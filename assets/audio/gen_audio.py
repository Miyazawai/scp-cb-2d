#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_audio.py -- SCP:CB 2D 程序化音效生成器

只使用 Python 标准库 + numpy，从零合成 15 个音效：
    22050 Hz / 16-bit / mono / RIFF WAV

设计约定
--------
* 所有声音由振荡器、噪声、包络、简单滤波与程序化混响构成；不读取任何采样。
* 非循环音效首尾使用 5-10 ms 淡入淡出，量化前将峰值归一到目标值。
* 循环音效采用“尾部交叉淡化进头部”的 wrap crossfade：
      在 N 个循环样本之外多渲染 X 个样本，把 x[N:N+X] 淡入 y[0:X]。
  这样 y[N-1] 到 y[0] 的过渡等价于原始连续信号的相邻采样过渡。
* 文件生成后重新读取 PCM 做峰值 / RMS / 削波 / 边界检查，并写进 REPORT.md。

运行：
    python gen_audio.py
输出：
    本脚本所在目录下的 15 个 WAV、audio_manifest.json、REPORT.md
"""

from __future__ import annotations

import json
import math
import wave
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

import numpy as np

SR = 22050
BIT_DEPTH = 16
CHANNELS = 1
OUT_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------

def sec_to_samples(seconds: float) -> int:
    return int(round(seconds * SR))


def t_axis(n: int) -> np.ndarray:
    return np.arange(n, dtype=np.float64) / SR


def db_to_gain(db: float) -> float:
    return float(10.0 ** (db / 20.0))


def peak_dbfs(x: np.ndarray) -> float:
    m = float(np.max(np.abs(x))) if x.size else 0.0
    return 20.0 * math.log10(max(m, 1e-12))


def rms_dbfs(x: np.ndarray) -> float:
    if x.size == 0:
        return -240.0
    v = float(np.mean(np.square(x)))
    return 10.0 * math.log10(max(v, 1e-24))


def normalize_peak(x: np.ndarray, target_db: float) -> np.ndarray:
    m = float(np.max(np.abs(x))) if x.size else 0.0
    if m < 1e-12:
        raise ValueError("refusing to normalize a silent buffer")
    return x * (db_to_gain(target_db) / m)


def remove_dc(x: np.ndarray) -> np.ndarray:
    return x - float(np.mean(x))


def smoothstep(t: np.ndarray, a: float, b: float) -> np.ndarray:
    if b <= a:
        return (t >= b).astype(np.float64)
    u = np.clip((t - a) / (b - a), 0.0, 1.0)
    return u * u * (3.0 - 2.0 * u)


def env_exp(t: np.ndarray, attack: float, tau: float) -> np.ndarray:
    """平滑起音 + 指数衰减；t 为从事件起点开始的秒数。"""
    a = np.clip(t / max(attack, 1e-5), 0.0, 1.0)
    a = 0.5 - 0.5 * np.cos(np.pi * a)
    return a * np.exp(-np.maximum(t - attack, 0.0) / max(tau, 1e-5))


def env_ar(t: np.ndarray, attack: float, release_start: float, release_end: float) -> np.ndarray:
    """平滑起音，持续到 release_start，再平滑收尾。"""
    up = smoothstep(t, 0.0, max(attack, 1e-5))
    down = 1.0 - smoothstep(t, release_start, release_end)
    return up * down


def fade_edges(x: np.ndarray, fade_in: float = 0.006, fade_out: float = 0.008) -> np.ndarray:
    """对一次性音效做首尾余弦淡入淡出，端点严格为 0。"""
    y = np.array(x, dtype=np.float64, copy=True)
    ni = min(sec_to_samples(fade_in), len(y) // 2)
    no = min(sec_to_samples(fade_out), len(y) // 2)
    if ni > 1:
        y[:ni] *= 0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, ni))
    if no > 1:
        y[-no:] *= 0.5 + 0.5 * np.cos(np.linspace(0.0, np.pi, no))
    return y


def add_at(buf: np.ndarray, start_s: float, sig: np.ndarray, gain: float = 1.0) -> None:
    i = int(round(start_s * SR))
    if i < 0:
        sig = sig[-i:]
        i = 0
    if i >= len(buf) or sig.size == 0:
        return
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n] * gain


def phase_from_freq(freq: np.ndarray) -> np.ndarray:
    """对瞬时频率积分得到相位；freq 单位为 Hz。"""
    ph = 2.0 * np.pi * np.cumsum(freq, dtype=np.float64) / SR
    return ph - ph[0]


def damped_sine(t: np.ndarray, freq: float, tau: float, phase: float = 0.0,
                attack: float = 0.0008) -> np.ndarray:
    return np.sin(2.0 * np.pi * freq * t + phase) * env_exp(t, attack, tau)


def bandlimited_square(t: np.ndarray, freq: float, max_harmonic_hz: float = 9000.0,
                       max_odd: int = 31) -> np.ndarray:
    """带限方波，只叠加低于 max_harmonic_hz 的奇次谐波，避免混叠。"""
    out = np.zeros_like(t)
    k = 1
    while k <= max_odd and freq * k < max_harmonic_hz:
        out += np.sin(2.0 * np.pi * freq * k * t) / k
        k += 2
    return out * (4.0 / np.pi)


# ---------------------------------------------------------------------------
# 噪声与滤波
# ---------------------------------------------------------------------------

def fir_lowpass(x: np.ndarray, fc: float, taps: int = 257) -> np.ndarray:
    """窗函数法线性相位 FIR 低通。taps 为奇数。"""
    if fc >= 0.499 * SR or x.size == 0:
        return x.copy()
    if taps % 2 == 0:
        taps += 1
    taps = min(taps, x.size if x.size % 2 == 1 else x.size - 1)
    if taps < 9:
        return x.copy()
    n = np.arange(taps, dtype=np.float64) - (taps - 1) / 2.0
    h = 2.0 * (fc / SR) * np.sinc(2.0 * (fc / SR) * n) * np.blackman(taps)
    s = float(np.sum(h))
    if abs(s) < 1e-12:
        return x.copy()
    h /= s
    return np.convolve(x, h, mode="same")


def fir_highpass(x: np.ndarray, fc: float, taps: int = 385) -> np.ndarray:
    return x - fir_lowpass(x, fc, taps=taps)


def fir_bandpass(x: np.ndarray, lo: float, hi: float, taps: int = 257) -> np.ndarray:
    return fir_lowpass(x, hi, taps=taps) - fir_lowpass(x, lo, taps=taps)


def fft_band_noise(n: int, rng: np.random.Generator, lo: float, hi: float,
                   pink: float = 0.0, resonance: Sequence[Tuple[float, float, float]] = ()) -> np.ndarray:
    """
    FFT 整段整形噪声。n 个样本是循环周期（首尾天然满足周期延拓），
    很适合循环底噪；对一次性音效则再乘包络与淡化。
        pink: 0=白噪声, 1=粉红噪声倾斜
        resonance: [(中心频率, 品质因数, 增益), ...]
    """
    n = int(n)
    if n <= 8:
        return np.zeros(n)
    white = rng.standard_normal(n)
    spec = np.fft.rfft(white)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    f = np.maximum(f, 1.0)
    mask = (f * f / (f * f + lo * lo)) * (hi * hi / (f * f + hi * hi))
    if pink > 0.0:
        mask *= (40.0 / np.maximum(f, 40.0)) ** (0.5 * pink)
    for fc, q, gain in resonance:
        bw = max(0.035, 0.5 / max(q, 0.1))
        mask *= 1.0 + gain * np.exp(-0.5 * (np.log2(f / max(fc, 1.0)) / bw) ** 2)
    spec *= mask
    spec[0] = 0.0
    y = np.fft.irfft(spec, n=n)
    r = float(np.sqrt(np.mean(y * y)))
    if r > 1e-12:
        y /= r
    return y


def pink_noise(n: int, rng: np.random.Generator, lo: float = 30.0, hi: float = 6000.0) -> np.ndarray:
    return fft_band_noise(n, rng, lo, hi, pink=1.0)


# ---------------------------------------------------------------------------
# 卷积混响
# ---------------------------------------------------------------------------

def fft_convolve(x: np.ndarray, ir: np.ndarray) -> np.ndarray:
    n = len(x) + len(ir) - 1
    nfft = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)
    return y[:len(x)]


def make_ir(seed: int, length: float, decay: float, lowpass_hz: float,
            predelay: float = 0.004, early: Sequence[Tuple[float, float]] | None = None) -> np.ndarray:
    n = max(16, sec_to_samples(length))
    rng = np.random.default_rng(seed)
    t = t_axis(n)
    ir = rng.standard_normal(n) * np.exp(-t / max(decay, 0.002))
    ir = fir_lowpass(ir, lowpass_hz, taps=129)
    if early is None:
        early = ((0.006, 0.55), (0.011, -0.36), (0.019, 0.24), (0.031, -0.16))
    for dt, g in early:
        idx = sec_to_samples(predelay + dt)
        if idx < n:
            ir[idx] += g
    ir /= math.sqrt(float(np.sum(ir * ir)) + 1e-12)
    return ir


def apply_room(x: np.ndarray, mix: float, ir: np.ndarray) -> np.ndarray:
    wet = fft_convolve(x, ir)[:len(x)]
    return (1.0 - mix) * x + mix * wet


# ---------------------------------------------------------------------------
# 循环交叉淡化
# ---------------------------------------------------------------------------

def wrap_crossfade(x: np.ndarray, n_loop: int, xfade_s: float) -> np.ndarray:
    """
    将连续渲染的 x[0:n_loop+xfade] 折叠为 n_loop 样本：
        y[:X] = x[:X] * w_in + x[N:N+X] * w_out
        y[X:] = x[X:N]
    这是“尾部淡出接回开头”的循环接法。循环边界 y[N-1] -> y[0]
    对应原信号 x[N-1] -> x[N]，因此没有人为的硬切。
    """
    nx = sec_to_samples(xfade_s)
    nx = max(2, min(nx, n_loop // 4))
    if len(x) < n_loop + nx:
        raise ValueError("source must contain n_loop + xfade samples")
    y = np.array(x[:n_loop], dtype=np.float64, copy=True)
    i = np.arange(nx, dtype=np.float64)
    w_in = 0.5 - 0.5 * np.cos(np.pi * i / (nx - 1))       # 0 -> 1
    w_out = 1.0 - w_in
    y[:nx] = x[:nx] * w_in + x[n_loop:n_loop + nx] * w_out
    return y


# ---------------------------------------------------------------------------
# 音效 1：amb_loop（8 s 设施底噪）
# ---------------------------------------------------------------------------

def synth_amb_loop() -> np.ndarray:
    dur = 8.0
    n = sec_to_samples(dur)
    xf = 0.045
    total = n + sec_to_samples(xf)
    t = t_axis(total)
    rng = np.random.default_rng(10001)

    # 低频设施嗡鸣：两路接近但不相同的频率形成缓慢拍频，并加入轻微非线性。
    hum = (0.70 * np.sin(2.0 * np.pi * 43.2 * t + 0.35)
           + 0.44 * np.sin(2.0 * np.pi * 57.6 * t + 1.20)
           + 0.21 * np.sin(2.0 * np.pi * 86.4 * t + 2.10)
           + 0.16 * np.sin(2.0 * np.pi * 28.8 * t + 0.70))
    hum *= 0.78 + 0.12 * np.sin(2.0 * np.pi * 0.071 * t + 0.4) \
                + 0.06 * np.sin(2.0 * np.pi * 0.127 * t + 2.2)
    hum = np.tanh(1.18 * hum) / np.tanh(1.18)

    # 通风管：带粉红倾斜的 90-2400 Hz 气流，叠加 250 Hz 与 620 Hz 的管壁共振。
    air = fft_band_noise(total, rng, 85.0, 2200.0, pink=1.0,
                         resonance=((260.0, 2.2, 0.65), (690.0, 3.0, 0.35)))
    air *= 0.60 + 0.16 * np.sin(2.0 * np.pi * 0.043 * t + 1.1) \
                + 0.08 * np.sin(2.0 * np.pi * 0.101 * t + 0.2)

    rumble = fft_band_noise(total, rng, 22.0, 90.0, pink=0.6)
    rumble *= 0.62 + 0.16 * np.sin(2.0 * np.pi * 0.059 * t + 2.6)

    bed = 0.52 * hum + 0.32 * air + 0.28 * rumble

    # 极轻微的偶发金属“咔”：三次，彼此音高、距离感不同。
    for start, freq, gain, tau in ((1.42, 2860.0, 0.33, 0.085),
                                   (4.16, 2140.0, 0.24, 0.115),
                                   (6.55, 3370.0, 0.19, 0.070)):
        ln = sec_to_samples(0.26)
        tt = t_axis(ln)
        tick_noise = fft_band_noise(ln, rng, 1600.0, 7600.0, pink=0.0)
        tick_noise *= env_exp(tt, 0.0007, 0.009)
        ring = (damped_sine(tt, freq, tau, 0.8)
                + 0.48 * damped_sine(tt, freq * 1.47, tau * 0.62, 2.1)
                + 0.20 * damped_sine(tt, freq * 2.31, tau * 0.35, 0.3))
        clank = 0.56 * tick_noise + 0.44 * ring
        clank = fir_lowpass(clank, 5200.0, taps=129)
        add_at(bed, start, clank, gain)

    # 给“房间”一点极短的反射，避免贴耳；湿声很低。
    ir = make_ir(10002, 0.42, 0.10, 2400.0, predelay=0.009)
    bed = apply_room(bed, 0.16, ir)
    bed = remove_dc(bed)
    return wrap_crossfade(bed, n, xf)


# ---------------------------------------------------------------------------
# 音效 2-4：三种皮鞋 / 水泥脚步
# ---------------------------------------------------------------------------

def synth_step(variant: int) -> np.ndarray:
    n = sec_to_samples(0.16)
    t = t_axis(n)
    rng = np.random.default_rng(2001 + variant)
    lead = 0.0065
    tt = np.maximum(t - lead, 0.0)
    on = (t >= lead).astype(np.float64)

    if variant == 0:       # 硬跟先着地：亮、干、脆
        f0, f1, body_tau = 151.0, 78.0, 0.055
        heel_gain, scuff_gain, thump_gain = 1.00, 0.58, 0.72
        scuff_lo, scuff_hi = 520.0, 3000.0
    elif variant == 1:     # 鞋底拖过水泥：中频摩擦更多、跟音稍软
        f0, f1, body_tau = 132.0, 69.0, 0.062
        heel_gain, scuff_gain, thump_gain = 0.62, 1.00, 0.80
        scuff_lo, scuff_hi = 330.0, 2100.0
    else:                  # 更重的落脚：低频多、鞋跟二次细响
        f0, f1, body_tau = 116.0, 61.0, 0.072
        heel_gain, scuff_gain, thump_gain = 0.78, 0.72, 1.00
        scuff_lo, scuff_hi = 410.0, 2500.0

    # 跟部宽带冲击与鞋底细碎摩擦。
    crack = fft_band_noise(n, rng, 2400.0, 8200.0)
    crack *= env_exp(tt, 0.00045, 0.0032) * on
    heel = fft_band_noise(n, rng, 850.0, 5600.0)
    heel *= env_exp(tt, 0.0007, 0.010) * on

    scuff = fft_band_noise(n, rng, scuff_lo, scuff_hi, pink=0.9,
                           resonance=((980.0, 1.3, 0.30),))
    scuff *= env_exp(tt, 0.005, 0.040) * on
    # 慢速的摩擦起伏，模仿鞋底与水泥的粘滑。
    scuff *= 0.78 + 0.22 * np.sin(2.0 * np.pi * (29.0 + 4.0 * variant) * tt + 1.4)

    # 低频脚掌 / 鞋跟“落重”。
    freq = f0 + (f1 - f0) * np.clip(tt / 0.065, 0.0, 1.0)
    phase = phase_from_freq(freq)
    thump = np.sin(phase) * env_exp(tt, 0.0012, body_tau) * on
    sub = np.sin(2.0 * np.pi * 54.0 * tt + 0.4) * env_exp(tt, 0.002, 0.055) * on
    knock = np.sin(2.0 * np.pi * 188.0 * tt + 1.0) * env_exp(tt, 0.0008, 0.022) * on

    # 皮面/鞋底的短促共鸣，不是明显音高。
    leather = (0.55 * damped_sine(tt, 1080.0 + 110.0 * variant, 0.014, 0.2)
               + 0.32 * damped_sine(tt, 1730.0 + 90.0 * variant, 0.010, 1.7))
    leather *= on

    mix = (0.54 * heel_gain * heel
           + 0.35 * heel_gain * crack
           + 0.76 * scuff_gain * scuff
           + 0.86 * thump_gain * thump
           + 0.24 * sub
           + 0.12 * knock
           + 0.15 * leather)

    # 少量混凝土细砂颗粒，让三次脚步不完全一样。
    grit = np.zeros(n)
    for _ in range(7 + 2 * variant):
        pos = float(rng.uniform(0.008, 0.072))
        gl = sec_to_samples(float(rng.uniform(0.0008, 0.0025)))
        if gl < 4:
            continue
        gt = t_axis(gl)
        g = fft_band_noise(gl, rng, 1800.0, 7600.0) * env_exp(gt, 0.0002, 0.0009)
        add_at(grit, lead + pos, g, float(rng.uniform(0.02, 0.10)))
    mix += grit

    ir = make_ir(2010 + variant, 0.095, 0.024, 3200.0, predelay=0.003,
                 early=((0.004, 0.4), (0.009, -0.25), (0.017, 0.14)))
    mix = apply_room(mix, 0.17, ir)
    mix = remove_dc(mix)
    mix = fir_highpass(mix, 28.0, taps=257)
    mix = fade_edges(mix, 0.005, 0.008)
    return mix


# ---------------------------------------------------------------------------
# 音效 5：door_hiss（气动门开）
# ---------------------------------------------------------------------------

def synth_door_hiss() -> np.ndarray:
    n = sec_to_samples(0.9)
    t = t_axis(n)
    rng = np.random.default_rng(3001)

    # 起始的“嗤”：高压气流在门缝处泄出，分成低频气团与高频嘶声。
    air = fft_band_noise(n, rng, 300.0, 7200.0, pink=0.55,
                         resonance=((1350.0, 0.9, 0.28), (3350.0, 1.4, 0.20)))
    air *= (smoothstep(t, 0.004, 0.020) * (0.62 + 0.38 * np.exp(-t / 0.10))
            * (1.0 - smoothstep(t, 0.32, 0.52)))
    low_chuff = fft_band_noise(n, rng, 70.0, 520.0, pink=0.8)
    low_chuff *= smoothstep(t, 0.0, 0.018) * np.exp(-t / 0.16)
    hiss = fft_band_noise(n, rng, 2300.0, 8800.0)
    hiss *= smoothstep(t, 0.003, 0.009) * np.exp(-t / 0.085)

    valve = (np.sin(2.0 * np.pi * 57.0 * t + 0.2)
             * env_exp(t, 0.0015, 0.055)) * (t > 0.004)

    # 后段：金属滑轨摩擦 + 极轻的轨道吱声。
    slide = (smoothstep(t, 0.36, 0.45) * (1.0 - smoothstep(t, 0.78, 0.885)))
    rail = fft_band_noise(n, rng, 720.0, 5200.0, pink=0.25,
                          resonance=((1180.0, 3.2, 0.8), (2440.0, 2.6, 0.55)))
    rail *= slide * (0.56 + 0.44 * np.abs(np.sin(2.0 * np.pi * 11.5 * t + 0.8)))

    squeak_f = 900.0 + 620.0 * smoothstep(t, 0.40, 0.79)
    squeak_phase = phase_from_freq(squeak_f) + 0.6 * np.sin(2.0 * np.pi * 6.3 * t)
    squeak = np.sin(squeak_phase) * slide * 0.050
    squeak += 0.35 * np.sin(2.0 * np.pi * 1.93 * squeak_phase) * slide * 0.030

    rail_ring = (damped_sine(np.maximum(t - 0.42, 0.0), 486.0, 0.14, 0.3) * (t > 0.42)
                 + 0.55 * damped_sine(np.maximum(t - 0.42, 0.0), 963.0, 0.10, 1.8) * (t > 0.42))
    rail_ring *= smoothstep(t, 0.42, 0.50) * 0.32

    end_stop = np.zeros(n)
    stop_tt = np.maximum(t - 0.852, 0.0)
    stop = (0.45 * damped_sine(stop_tt, 172.0, 0.035, 0.1)
            + 0.22 * damped_sine(stop_tt, 640.0, 0.022, 1.3)
            + 0.16 * fft_band_noise(n, rng, 900.0, 5000.0) * env_exp(stop_tt, 0.0006, 0.010))
    end_stop += stop * (t > 0.852)

    mix = (1.00 * air + 0.48 * low_chuff + 0.34 * hiss + 0.30 * valve
           + 0.54 * rail + 1.00 * squeak + 0.38 * rail_ring + 0.30 * end_stop)
    ir = make_ir(3002, 0.30, 0.075, 2600.0, predelay=0.005)
    mix = apply_room(mix, 0.18, ir)
    mix = remove_dc(mix)
    mix = fir_highpass(mix, 25.0, taps=257)
    mix = fade_edges(mix, 0.005, 0.010)
    return mix


# ---------------------------------------------------------------------------
# 音效 6：door_close（重门合拢 + 闷响）
# ---------------------------------------------------------------------------

def synth_door_close() -> np.ndarray:
    n = sec_to_samples(0.6)
    t = t_axis(n)
    rng = np.random.default_rng(3101)

    # 0-0.34 s：沉重的门体沿轨道滑动。
    move = smoothstep(t, 0.015, 0.11) * (1.0 - smoothstep(t, 0.28, 0.355))
    rumble = fft_band_noise(n, rng, 32.0, 180.0, pink=0.7)
    rumble *= move * (0.70 + 0.30 * np.sin(2.0 * np.pi * 5.2 * t + 0.5))
    scrape = fft_band_noise(n, rng, 450.0, 2600.0, pink=0.35,
                            resonance=((820.0, 2.4, 0.45),))
    scrape *= move * (0.35 + 0.65 * np.abs(np.sin(2.0 * np.pi * 17.0 * t + 1.1)))
    motor = (0.16 * np.sin(2.0 * np.pi * 88.0 * t + 0.4)
             + 0.08 * np.sin(2.0 * np.pi * 176.0 * t + 1.2)) * move

    # 0.34 s：合拢。低频冲击 + 金属门板模态 + 锁舌咔哒 + 气流被挤出的“噗”。
    imp = 0.345
    it = np.maximum(t - imp, 0.0)
    on = (t >= imp).astype(np.float64)
    freq = 68.0 + (32.0 - 68.0) * np.clip(it / 0.16, 0.0, 1.0)
    boom = np.sin(phase_from_freq(freq)) * env_exp(it, 0.0025, 0.14) * on
    sub = np.sin(2.0 * np.pi * 27.5 * it + 0.1) * env_exp(it, 0.004, 0.17) * on
    impact_noise = fft_band_noise(n, rng, 38.0, 620.0, pink=0.55)
    impact_noise *= env_exp(it, 0.0015, 0.055) * on
    slam = fft_band_noise(n, rng, 900.0, 7800.0)
    slam *= env_exp(it, 0.0005, 0.018) * on

    modes = np.zeros(n)
    for f, tau, amp, ph in ((104.0, 0.20, 0.55, 0.2),
                            (173.0, 0.15, 0.42, 1.3),
                            (287.0, 0.11, 0.33, 2.2),
                            (462.0, 0.085, 0.22, 0.9),
                            (781.0, 0.060, 0.15, 2.8),
                            (1294.0, 0.035, 0.08, 1.5)):
        modes += amp * damped_sine(it, f, tau, ph) * on
    # 门板被撞后的轻微二次 rattling。
    rattle = np.zeros(n)
    for dt, amp in ((0.075, 0.12), (0.101, 0.08), (0.138, 0.05)):
        rr = np.maximum(t - (imp + dt), 0.0)
        rattle += amp * (np.sin(2.0 * np.pi * 315.0 * rr + 0.6)
                         + 0.5 * np.sin(2.0 * np.pi * 611.0 * rr + 1.8)) \
                  * env_exp(rr, 0.0008, 0.020) * (t >= imp + dt)

    latch = np.zeros(n)
    lt = np.maximum(t - 0.363, 0.0)
    latch += (fft_band_noise(n, rng, 1800.0, 8500.0) * env_exp(lt, 0.0004, 0.005)
              + 0.4 * damped_sine(lt, 2460.0, 0.010, 1.0)) * (t >= 0.363)

    air_puff = fft_band_noise(n, rng, 120.0, 900.0, pink=0.9)
    air_puff *= env_exp(it, 0.002, 0.045) * on

    mix = (0.55 * rumble + 0.26 * scrape + 0.10 * motor
           + 0.95 * boom + 0.55 * sub + 0.34 * impact_noise
           + 0.32 * slam + 0.52 * modes + 0.38 * rattle
           + 0.24 * latch + 0.30 * air_puff)
    ir = make_ir(3102, 0.48, 0.13, 2100.0, predelay=0.006)
    mix = apply_room(mix, 0.22, ir)
    mix = remove_dc(mix)
    mix = fir_highpass(mix, 22.0, taps=257)
    mix = fade_edges(mix, 0.006, 0.010)
    return mix


# ---------------------------------------------------------------------------
# 音效 7-8：读卡器接受 / 拒绝
# ---------------------------------------------------------------------------

def synth_keycard_beep() -> np.ndarray:
    n = sec_to_samples(0.25)
    t = t_axis(n)
    rng = np.random.default_rng(4001)
    out = np.zeros(n)

    for idx, (start, freq) in enumerate(((0.022, 1760.0), (0.118, 1975.0))):
        ln = sec_to_samples(0.072)
        tt = t_axis(ln)
        env = env_exp(tt, 0.0018, 0.052) * (1.0 - smoothstep(tt, 0.048, 0.068))
        tone = bandlimited_square(tt, freq, max_harmonic_hz=8800.0, max_odd=11)
        tone = np.tanh(0.85 * tone) / np.tanh(0.85)
        tone *= 0.92 + 0.08 * np.sin(2.0 * np.pi * 21.0 * tt + 0.5)
        tone *= env
        click = fft_band_noise(ln, rng, 1600.0, 9000.0) * env_exp(tt, 0.0003, 0.0022)
        add_at(out, start, tone + 0.12 * click, 1.0 if idx == 0 else 0.92)

    # 读卡器塑料壳体的极短反射。
    ir = make_ir(4002, 0.11, 0.028, 4200.0, predelay=0.002)
    out = apply_room(out, 0.12, ir)
    out = remove_dc(out)
    out = fir_highpass(out, 45.0, taps=257)
    out = fade_edges(out, 0.005, 0.010)
    return out


def synth_keycard_deny() -> np.ndarray:
    n = sec_to_samples(0.35)
    t = t_axis(n)
    rng = np.random.default_rng(4101)
    start = 0.025
    tt = np.maximum(t - start, 0.0)
    on = (t >= start).astype(np.float64)
    dur = 0.255
    u = np.clip(tt / dur, 0.0, 1.0)
    freq = 238.0 + (94.0 - 238.0) * (u ** 1.25)
    phase = phase_from_freq(freq)
    buzz = np.tanh(1.6 * (np.sin(phase) + 0.34 * np.sin(2.0 * phase) + 0.16 * np.sin(3.0 * phase)))
    buzz *= env_exp(tt, 0.005, 0.24) * (1.0 - smoothstep(tt, dur - 0.03, dur + 0.015))
    buzz *= 0.82 + 0.18 * np.sin(2.0 * np.pi * 19.0 * tt)
    sub = np.sin(2.0 * np.pi * 58.0 * tt + 0.4) * env_exp(tt, 0.006, 0.15)
    click = fft_band_noise(n, rng, 500.0, 2200.0) * env_exp(tt, 0.0005, 0.012)

    out = (buzz + 0.26 * sub + 0.16 * click) * on
    ir = make_ir(4102, 0.16, 0.045, 2200.0, predelay=0.003)
    out = apply_room(out, 0.13, ir)
    out = remove_dc(out)
    out = fir_highpass(out, 35.0, taps=257)
    out = fade_edges(out, 0.005, 0.010)
    return out


# ---------------------------------------------------------------------------
# 音效 9：pickup
# ---------------------------------------------------------------------------

def synth_pickup() -> np.ndarray:
    n = sec_to_samples(0.2)
    t = t_axis(n)
    rng = np.random.default_rng(5001)

    # 少量 FM 的金属/玻璃“叮”，两个不严格谐和的分量。
    tt = np.maximum(t - 0.006, 0.0)
    on = (t >= 0.006).astype(np.float64)
    mod_index = 1.55 * np.exp(-tt / 0.028)
    carrier_phase = 2.0 * np.pi * 2360.0 * tt
    fm = np.sin(carrier_phase + mod_index * np.sin(2.0 * np.pi * 3350.0 * tt + 0.7))
    fm *= env_exp(tt, 0.0012, 0.050) * on
    partials = (0.35 * damped_sine(tt, 3510.0, 0.045, 1.1)
                + 0.22 * damped_sine(tt, 4690.0, 0.030, 2.4)
                + 0.18 * damped_sine(tt, 1280.0, 0.028, 0.5)) * on
    sparkle = fft_band_noise(n, rng, 4200.0, 9800.0) * env_exp(tt, 0.0007, 0.008) * on
    body = (0.62 * fm + 0.36 * partials + 0.10 * sparkle)

    ir = make_ir(5002, 0.17, 0.040, 5200.0, predelay=0.002)
    body = apply_room(body, 0.16, ir)
    body = remove_dc(body)
    body = fir_highpass(body, 110.0, taps=257)
    body = fade_edges(body, 0.005, 0.010)
    return body


# ---------------------------------------------------------------------------
# 音效 10：flashlight_click
# ---------------------------------------------------------------------------

def synth_flashlight_click() -> np.ndarray:
    n = sec_to_samples(0.06)
    t = t_axis(n)
    rng = np.random.default_rng(6001)
    out = np.zeros(n)

    def click_at(start: float, strength: float, high: float) -> None:
        tt = np.maximum(t - start, 0.0)
        on = (t >= start).astype(np.float64)
        noise = fft_band_noise(n, rng, 1500.0, 9200.0) * env_exp(tt, 0.00025, 0.0022)
        shell = (0.55 * damped_sine(tt, 1180.0, 0.0085, 0.2)
                 + 0.34 * damped_sine(tt, 2380.0, 0.0060, 1.6)
                 + 0.20 * damped_sine(tt, high, 0.0035, 2.7))
        spring = 0.10 * damped_sine(tt, 5200.0, 0.0045, 0.9)
        add_at(out, 0.0, (noise + shell + spring) * on, strength)

    click_at(0.007, 1.0, 3950.0)
    click_at(0.029, 0.62, 4600.0)

    out = remove_dc(out)
    out = fir_highpass(out, 160.0, taps=257)
    out = fade_edges(out, 0.005, 0.005)
    return out


# ---------------------------------------------------------------------------
# 音效 11：blink
# ---------------------------------------------------------------------------

def synth_blink() -> np.ndarray:
    n = sec_to_samples(0.3)
    t = t_axis(n)
    rng = np.random.default_rng(7001)

    # 耳膜压迫：低频缓慢起伏 + 两次很轻的闷响。
    pressure = (0.55 * np.sin(2.0 * np.pi * 43.0 * t + 0.1)
                + 0.22 * np.sin(2.0 * np.pi * 29.0 * t + 1.1))
    pressure *= env_exp(t, 0.035, 0.105)
    close_thump = (np.sin(2.0 * np.pi * 63.0 * np.maximum(t - 0.045, 0.0))
                   * env_exp(np.maximum(t - 0.045, 0.0), 0.004, 0.035)
                   * (t >= 0.045))
    open_thump = (np.sin(2.0 * np.pi * 72.0 * np.maximum(t - 0.175, 0.0))
                  * env_exp(np.maximum(t - 0.175, 0.0), 0.006, 0.028)
                  * (t >= 0.175))
    thud_noise = fft_band_noise(n, rng, 28.0, 230.0, pink=0.6)
    thud_noise *= env_exp(t, 0.010, 0.055) * 0.22

    # 高频“被眼睑闷住”的一小段空气声，随闭眼迅速衰减。
    hiss = fft_band_noise(n, rng, 1400.0, 7800.0, pink=0.2)
    hiss *= smoothstep(t, 0.006, 0.035) * np.exp(-np.maximum(t - 0.035, 0.0) / 0.060)
    hiss *= 1.0 - smoothstep(t, 0.22, 0.29)

    # 睁眼时极轻的湿润“分开”声，用短促中频噪声表示。
    wet_tt = np.maximum(t - 0.188, 0.0)
    wet = fft_band_noise(n, rng, 550.0, 2400.0)
    wet *= env_exp(wet_tt, 0.003, 0.018) * (t >= 0.188) * 0.22

    out = (0.60 * pressure + 0.28 * close_thump + 0.20 * open_thump
           + 0.17 * thud_noise + 0.10 * hiss + wet)
    ir = make_ir(7002, 0.16, 0.040, 1700.0, predelay=0.004)
    out = apply_room(out, 0.12, ir)
    out = remove_dc(out)
    out = fir_highpass(out, 22.0, taps=257)
    out = fade_edges(out, 0.008, 0.010)
    return out


# ---------------------------------------------------------------------------
# 音效 12：scp_step（全套里最不适的一个）
# ---------------------------------------------------------------------------

def synth_scp_step() -> np.ndarray:
    """
    SCP-173 式混凝土雕像挪一步。
    设计上刻意避开“干净的电影撞击”：用干燥、贴耳的颗粒化石面粘滑，
    加上 20-60 Hz 的体重感、非谐和石体模态和混凝土碎屑，制造一种
    “它就在你背后、而且没有生命”的生理不适。
    """
    n = sec_to_samples(0.18)
    t = t_axis(n)
    rng = np.random.default_rng(8001)
    lead = 0.004

    # --- 拖拽前的低频压力：几乎听不见，但能感到有质量靠近。
    pre = (0.30 * np.sin(2.0 * np.pi * 27.0 * t + 0.4)
           + 0.18 * np.sin(2.0 * np.pi * 41.0 * t + 1.7))
    pre *= smoothstep(t, 0.0, 0.030) * (1.0 - smoothstep(t, 0.10, 0.16))

    # --- 石块摩擦：粉红噪声 + 多层带通 + 粘滑颗粒调制。
    drag_env = smoothstep(t, 0.006, 0.021) * (1.0 - smoothstep(t, 0.105, 0.152))
    friction = fft_band_noise(n, rng, 120.0, 3100.0, pink=1.0,
                              resonance=((430.0, 1.7, 0.55),
                                         (980.0, 2.4, 0.42),
                                         (1870.0, 2.9, 0.32)))
    # 低频粗糙调制：不平滑的 20-70 Hz 起伏 = 石头在水泥上“顿、蹭”。
    ctrl = rng.standard_normal(n)
    ctrl = fir_lowpass(ctrl, 48.0, taps=257)
    ctrl = np.abs(ctrl)
    ctrl /= max(float(np.percentile(ctrl, 96.0)), 1e-9)
    grain = 0.26 + 0.92 * np.clip(ctrl, 0.0, 1.6)
    friction *= drag_env * grain
    friction *= 0.82 + 0.18 * np.sin(2.0 * np.pi * 87.0 * t + 0.8)

    # 更窄的“硬石刮擦”带，给声音一个干涩、刺耳的中高频边缘。
    scrape = fft_band_noise(n, rng, 1500.0, 5400.0, pink=0.15,
                            resonance=((2660.0, 4.2, 0.9), (3720.0, 3.1, 0.5)))
    scrape *= drag_env * (0.20 + 0.80 * np.clip(ctrl, 0.0, 1.0))

    # --- 撞击：重量落在水泥上。低频下坠 + 非谐和石体模态。
    imp = 0.068
    it = np.maximum(t - imp, 0.0)
    on = (t >= imp).astype(np.float64)
    f_drop = 66.0 + (29.0 - 66.0) * np.clip(it / 0.125, 0.0, 1.0)
    weight = np.sin(phase_from_freq(f_drop)) * env_exp(it, 0.0022, 0.110) * on
    sub = (0.65 * np.sin(2.0 * np.pi * 24.0 * it + 0.1)
           + 0.35 * np.sin(2.0 * np.pi * 36.5 * it + 1.2))
    sub *= env_exp(it, 0.003, 0.125) * on
    # 一个非常闷的混凝土“啪”，不是金属 clang。
    slap_noise = fft_band_noise(n, rng, 45.0, 760.0, pink=0.55)
    slap_noise *= env_exp(it, 0.0012, 0.040) * on

    modes = np.zeros(n)
    for f, tau, amp, ph in ((58.0, 0.125, 0.60, 0.2),
                            (91.0, 0.100, 0.45, 1.7),
                            (137.0, 0.080, 0.50, 0.9),
                            (213.0, 0.062, 0.34, 2.6),
                            (347.0, 0.048, 0.24, 1.3),
                            (529.0, 0.033, 0.16, 0.4),
                            (812.0, 0.022, 0.10, 2.0)):
        modes += amp * damped_sine(it, f, tau, ph) * on

    # 非线性：让低频产生粗糙的谐波，像石头内部在共振。
    low_block = np.tanh(1.85 * (0.72 * weight + 0.48 * sub + 0.44 * modes)) / np.tanh(1.85)

    # --- 混凝土碎屑 / 颗粒：随机短脉冲，不规则，是“硬物在地面上蹭”的关键。
    grit = np.zeros(n)
    for _ in range(52):
        pos = float(rng.uniform(0.004, 0.132))
        gl = sec_to_samples(float(rng.uniform(0.00035, 0.0028)))
        if gl < 4:
            continue
        gt = t_axis(gl)
        gn = fft_band_noise(gl, rng, 1200.0, 9600.0, pink=0.1,
                            resonance=((4300.0, 2.0, 0.35),))
        g = gn * env_exp(gt, 0.0002, 0.00065)
        add_at(grit, lead + pos, g, float(rng.uniform(0.015, 0.070)))

    # 拖拽尾部的二次“蹭”与极轻的碎石落回地面。
    tail_env = smoothstep(t, 0.105, 0.125) * (1.0 - smoothstep(t, 0.145, 0.178))
    tail_scrape = fft_band_noise(n, rng, 700.0, 3400.0, pink=0.55)
    tail_scrape *= tail_env * (0.5 + 0.5 * np.abs(np.sin(2.0 * np.pi * 23.0 * t + 0.3)))

    mix = (0.18 * pre
           + 0.68 * friction
           + 0.24 * scrape
           + 0.95 * low_block
           + 0.32 * slap_noise
           + 0.43 * grit
           + 0.20 * tail_scrape)

    # 贴地的短混响：刻意做得很干，保持“就在背后”的贴身感。
    ir = make_ir(8002, 0.22, 0.052, 2900.0, predelay=0.004,
                 early=((0.0045, 0.30), (0.0105, -0.20), (0.021, 0.11)))
    mix = apply_room(mix, 0.115, ir)
    mix = remove_dc(mix)

    # 保留 21 Hz 的体感，切掉直流与次声。
    mix = fir_highpass(mix, 17.0, taps=513)
    # 轻微软削波，让冲击更“硬”，但归一化后不会削顶。
    mix = np.tanh(1.25 * mix) / np.tanh(1.25)
    mix = fade_edges(mix, 0.005, 0.009)
    return mix


# ---------------------------------------------------------------------------
# 音效 13：heartbeat（1 s 循环）
# ---------------------------------------------------------------------------

def _heart_beat(n: int, start: float, f0: float, f1: float, tau: float,
                strength: float, seed: int) -> np.ndarray:
    out = np.zeros(n)
    ln = n
    tt = np.maximum(t_axis(ln) - start, 0.0)
    on = (t_axis(ln) >= start).astype(np.float64)
    freq = f0 + (f1 - f0) * np.clip(tt / 0.070, 0.0, 1.0)
    phase = phase_from_freq(freq)
    body = np.sin(phase) * env_exp(tt, 0.0035, tau)
    body += 0.34 * np.sin(2.0 * np.pi * 92.0 * tt + 0.4) * env_exp(tt, 0.004, tau * 0.42)
    body *= on
    rng = np.random.default_rng(seed)
    thump = fft_band_noise(ln, rng, 28.0, 220.0, pink=0.65)
    thump *= env_exp(tt, 0.004, tau * 0.60) * on
    out += strength * (0.92 * body + 0.30 * thump)
    return out


def synth_heartbeat() -> np.ndarray:
    n = sec_to_samples(1.0)
    xf = 0.06
    total = n + sec_to_samples(xf)
    out = np.zeros(total)

    # 咚（S1）— 短间隔 — 咚（S2），然后一整段安静的舒张期。
    out += _heart_beat(total, 0.050, 58.0, 38.0, 0.105, 1.00, 9001)
    out += _heart_beat(total, 0.278, 64.0, 43.0, 0.082, 0.72, 9002)

    # 极轻的胸腔共鸣，避免纯正弦的“电子”感。
    t = t_axis(total)
    chest = (0.055 * np.sin(2.0 * np.pi * 118.0 * t + 0.2)
             * env_exp(np.maximum(t - 0.050, 0.0), 0.006, 0.09) * (t >= 0.050))
    chest += (0.040 * np.sin(2.0 * np.pi * 142.0 * t + 1.8)
              * env_exp(np.maximum(t - 0.278, 0.0), 0.006, 0.06) * (t >= 0.278))
    out += chest

    ir = make_ir(9003, 0.35, 0.10, 650.0, predelay=0.006)
    out = apply_room(out, 0.13, ir)
    out = remove_dc(out)
    out = fir_highpass(out, 20.0, taps=385)
    return wrap_crossfade(out, n, xf)


# ---------------------------------------------------------------------------
# 音效 14：stinger
# ---------------------------------------------------------------------------

def synth_stinger() -> np.ndarray:
    n = sec_to_samples(1.4)
    t = t_axis(n)
    rng = np.random.default_rng(10001)
    hit = 0.006
    tt = np.maximum(t - hit, 0.0)
    on = (t >= hit).astype(np.float64)

    # 高频噪声爆发，尖锐但用短衰减控制，不刺穿耳膜。
    blast = fft_band_noise(n, rng, 1800.0, 9800.0, pink=0.1,
                           resonance=((4600.0, 1.2, 0.30),))
    blast *= env_exp(tt, 0.0006, 0.105) * on
    mid_burst = fft_band_noise(n, rng, 650.0, 5200.0, pink=0.5,
                               resonance=((1450.0, 2.2, 0.35),))
    mid_burst *= env_exp(tt, 0.001, 0.19) * on * (0.55 + 0.45 * np.sin(2.0 * np.pi * 31.0 * tt))

    # 失真的下行高频簇，像金属/无线电被扯断。
    f_hi = np.array([1830.0, 2270.0, 3020.0], dtype=np.float64)
    decay = np.exp(-tt / 0.14)
    cluster = np.zeros(n)
    for k, f in enumerate(f_hi):
        glide = f * (0.55 + 0.45 * np.exp(-tt / 0.22))
        cluster += (0.45 / (k + 1)) * np.sin(phase_from_freq(glide) + k * 1.3)
    cluster = np.tanh(1.8 * cluster) * decay * on

    # 快速下行的低频：420 Hz -> 32 Hz，同时保留一个更低的 sub。
    f_lo = 420.0 + (32.0 - 420.0) * np.clip(tt / 0.50, 0.0, 1.0) ** 0.72
    low = np.sin(phase_from_freq(f_lo)) * env_exp(tt, 0.003, 0.42) * on
    low += 0.55 * np.sin(2.0 * np.pi * 27.0 * tt + 0.3) * env_exp(tt, 0.004, 0.55) * on
    low = np.tanh(1.35 * low) / np.tanh(1.35)

    # 起始闷击，让身体先于耳朵反应。
    impact = (np.sin(2.0 * np.pi * 52.0 * tt + 0.1) * env_exp(tt, 0.002, 0.11)
              + 0.35 * fft_band_noise(n, rng, 30.0, 400.0, pink=0.4)
              * env_exp(tt, 0.001, 0.06)) * on

    # 末尾余响：带通噪声 + 低鸣，逐渐消失在走廊里。
    tail = fft_band_noise(n, rng, 120.0, 1800.0, pink=0.8)
    tail *= smoothstep(t, 0.30, 0.60) * np.exp(-np.maximum(t - 0.45, 0.0) / 0.42)
    tail *= 0.17

    mix = (0.58 * blast + 0.30 * mid_burst + 0.32 * cluster
           + 0.92 * low + 0.44 * impact + tail)
    ir = make_ir(10002, 0.70, 0.20, 2400.0, predelay=0.010)
    mix = apply_room(mix, 0.25, ir)
    mix = remove_dc(mix)
    mix = fir_highpass(mix, 20.0, taps=385)
    mix = fade_edges(mix, 0.005, 0.012)
    return mix


# ---------------------------------------------------------------------------
# 音效 15：alarm_loop（4 s 远处双音警报）
# ---------------------------------------------------------------------------

def synth_alarm_loop() -> np.ndarray:
    n = sec_to_samples(4.0)
    xf = 0.06
    total = n + sec_to_samples(xf)
    t = t_axis(total)
    rng = np.random.default_rng(11001)

    # 4 s 内严格两次 2 s 循环，循环点落在警报间隙里。
    phase_t = np.mod(t, 2.0)
    tone_a = np.zeros(total)
    tone_b = np.zeros(total)
    for cycle in range(3):
        start = cycle * 2.0
        # A 音 392 Hz；B 音 523.25 Hz，各 0.54 s，中间有呼吸间隙。
        for target, f, a, b in ((tone_a, 392.0, 0.16, 0.70),
                                (tone_b, 523.25, 0.89, 1.43)):
            if start > total:
                continue
            tt = t - (start + a)
            on = (tt >= 0.0) & (tt <= (b - a))
            if not np.any(on):
                continue
            tt2 = np.maximum(tt, 0.0)
            env = smoothstep(tt2, 0.0, 0.055) * (1.0 - smoothstep(tt2, (b - a) - 0.09, (b - a)))
            # 双音警报用柔和的三角/带限方波混合，不用高频方波。
            soft = (np.sin(2.0 * np.pi * f * tt2 + 0.2)
                    + 0.22 * np.sin(2.0 * np.pi * 2.0 * f * tt2 + 1.1)
                    + 0.08 * np.sin(2.0 * np.pi * 3.0 * f * tt2 + 0.4))
            vibrato = 1.0 + 0.0025 * np.sin(2.0 * np.pi * 5.2 * tt2)
            buf = soft * env * vibrato * on
            target += buf * 0.18

    # 墙后的低通 + 轻微梳状反射，让它“闷在墙后”。
    tone = tone_a + tone_b
    tone = fir_lowpass(tone, 1050.0, taps=385)
    delayed = np.zeros_like(tone)
    delayed[sec_to_samples(0.018):] = tone[:-sec_to_samples(0.018)] * 0.24
    tone = tone + delayed
    tone = fir_lowpass(tone, 780.0, taps=385)

    # 设施低鸣与远处空气，填满警报间隙，也是循环的“胶水”。
    hum = (0.30 * np.sin(2.0 * np.pi * 57.0 * t + 0.3)
           + 0.20 * np.sin(2.0 * np.pi * 85.5 * t + 1.2))
    hum *= 0.72 + 0.12 * np.sin(2.0 * np.pi * 0.19 * t + 1.0)
    air = fft_band_noise(total, rng, 60.0, 900.0, pink=0.9)
    air *= 0.22
    mix = 0.90 * tone + 0.30 * hum + 0.30 * air

    ir = make_ir(11002, 0.85, 0.24, 1000.0, predelay=0.020)
    mix = apply_room(mix, 0.33, ir)
    mix = remove_dc(mix)
    mix = fir_highpass(mix, 45.0, taps=385)
    return wrap_crossfade(mix, n, xf)


# ---------------------------------------------------------------------------
# 规格表 / 生成 / 写出 / 分析
# ---------------------------------------------------------------------------

SPECS: List[Tuple[str, float, bool, float, str, Callable[[], np.ndarray]]] = [
    ("amb_loop.wav", 8.0, True, -12.0,
     "设施底噪：低频嗡鸣 + 通风气流 + 极轻金属偶发咔声", synth_amb_loop),
    ("step_1.wav", 0.16, False, -3.0,
     "皮鞋踩水泥：硬跟先着地，亮而干", lambda: synth_step(0)),
    ("step_2.wav", 0.16, False, -3.0,
     "皮鞋踩水泥：鞋底拖动，中频摩擦更多", lambda: synth_step(1)),
    ("step_3.wav", 0.16, False, -3.0,
     "皮鞋踩水泥：更重的落脚，低频更多", lambda: synth_step(2)),
    ("door_hiss.wav", 0.9, False, -3.0,
     "气动门开启：起始泄气嘶声 + 末尾金属滑轨", synth_door_hiss),
    ("door_close.wav", 0.6, False, -3.0,
     "沉重金属门合拢：滑轨、撞击、闷响与锁舌", synth_door_close),
    ("keycard_beep.wav", 0.25, False, -3.0,
     "读卡器接受：两声短促高频电子蜂鸣", synth_keycard_beep),
    ("keycard_deny.wav", 0.35, False, -3.0,
     "读卡器拒绝：低沉下行的短促蜂鸣", synth_keycard_deny),
    ("pickup.wav", 0.2, False, -3.0,
     "拾取物品：轻微高频金属叮声", synth_pickup),
    ("flashlight_click.wav", 0.06, False, -3.0,
     "手电开关：塑料壳体机械咔嗒（按下/回弹两下）", synth_flashlight_click),
    ("blink.wav", 0.3, False, -3.0,
     "闭眼/睁眼：低频耳膜压力 + 短促高频衰减", synth_blink),
    ("scp_step.wav", 0.18, False, -3.0,
     "SCP-173 混凝土雕像挪步：石面粘滑 + 低频撞击", synth_scp_step),
    ("heartbeat.wav", 1.0, True, -12.0,
     "心跳两下（咚-咚），低频、可循环", synth_heartbeat),
    ("stinger.wav", 1.4, False, -3.0,
     "惊吓音：高频噪声爆发 + 下行低频 + 走廊余响", synth_stinger),
    ("alarm_loop.wav", 4.0, True, -3.0,
     "远处警报：墙后闷住的双音循环", synth_alarm_loop),
]


def write_wav(path: Path, x: np.ndarray) -> None:
    x = np.asarray(x, dtype=np.float64)
    # 峰值在调用前已经归一化；这里只做 16-bit 量化。
    pcm = np.clip(np.rint(x * 32767.0), -32768.0, 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(BIT_DEPTH // 8)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def read_wav(path: Path) -> Tuple[np.ndarray, int, int, int, int]:
    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        rate = wf.getframerate()
        frames = wf.getnframes()
        raw = wf.readframes(frames)
    pcm = np.frombuffer(raw, dtype="<i2")
    x = pcm.astype(np.float64) / 32768.0
    return x, channels, sampwidth, rate, frames


def analyze(path: Path, is_loop: bool) -> Dict[str, object]:
    x, channels, sampwidth, rate, frames = read_wav(path)
    if channels != 1 or sampwidth != 2 or rate != SR:
        raise AssertionError(f"bad WAV format: {path.name}")
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    peak_fs = 20.0 * math.log10(max(peak, 1e-12))
    rms = rms_dbfs(x)
    dc = float(np.mean(x))
    clipped = int(np.count_nonzero(np.abs(x) >= (32767.0 / 32768.0)))
    head = float(abs(x[0])) if x.size else 0.0
    tail = float(abs(x[-1])) if x.size else 0.0
    head8 = float(np.max(np.abs(x[:min(len(x), 8)]))) if x.size else 0.0
    tail8 = float(np.max(np.abs(x[-min(len(x), 8):]))) if x.size else 0.0
    seam_jump = float(abs(x[0] - x[-1])) if is_loop and x.size else 0.0
    seam_db = 20.0 * math.log10(max(seam_jump, 1e-12))
    # 首尾 10 ms 与全段的最大单样本步进；用于人工复核淡入淡出/爆音。
    edge = min(len(x), sec_to_samples(0.010))
    max_step_head = float(np.max(np.abs(np.diff(x[:edge])))) if edge > 1 else 0.0
    max_step_tail = float(np.max(np.abs(np.diff(x[-edge:])))) if edge > 1 else 0.0
    return {
        "frames": frames,
        "duration": frames / float(SR),
        "peak_dbfs": peak_fs,
        "rms_dbfs": rms,
        "dc": dc,
        "clipped": clipped,
        "head": head,
        "tail": tail,
        "head8": head8,
        "tail8": tail8,
        "seam_jump": seam_jump,
        "seam_db": seam_db,
        "max_step_head": max_step_head,
        "max_step_tail": max_step_tail,
        "is_loop": is_loop,
    }


def to_int16_peak_stats(x: np.ndarray) -> Tuple[float, float]:
    pcm = np.clip(np.rint(x * 32767.0), -32768.0, 32767.0).astype("<i2")
    y = pcm.astype(np.float64) / 32768.0
    return 20.0 * math.log10(max(float(np.max(np.abs(y))), 1e-12)), rms_dbfs(y)


def write_manifest(results: Dict[str, Dict[str, object]]) -> None:
    manifest = {}
    for name, _dur, is_loop, _target, use, _fn in SPECS:
        st = results[name]
        manifest[name] = {
            "duration_sec": round(float(st["duration"]), 6),
            "loop": bool(is_loop),
            "peak_dbfs": round(float(st["peak_dbfs"]), 2),
            "rms_dbfs": round(float(st["rms_dbfs"]), 2),
            "use": use,
        }
    path = OUT_DIR / "audio_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(results: Dict[str, Dict[str, object]], elapsed: float) -> None:
    lines: List[str] = []
    lines.append("# SCP:CB 2D — 程序化音效生成报告\n")
    lines.append("生成方式：`gen_audio.py`，纯 Python + numpy 合成，未读取或下载任何音频素材。\n")
    lines.append(f"- 采样率 / 位深 / 声道：**{SR} Hz / 16-bit / mono**")
    lines.append(f"- 文件数：**{len(SPECS)} 个 WAV**。需求表写“14 个”，但逐项清点实际是 "
                 f"`amb_loop` 1 + `step_1/2/3` 3 + 其余 11 = **15**；以逐项清单为准，全部交付。")
    lines.append("- 一次性音效：首尾 5–10 ms 余弦淡入淡出，端点严格为 0。")
    lines.append("- 循环音效：多渲染 45–60 ms，再用 wrap crossfade 把尾部淡回开头；"
                 "循环边界等价于连续信号的相邻采样。")
    lines.append("- 归一化：一次性音效峰值 −3 dBFS；`amb_loop` / `heartbeat` 为 −12 dBFS。"
                 "量化后重新读取 PCM 测量下表。\n")

    lines.append("## 实测电平与文件检查\n")
    lines.append("峰值/RMS 均以 32768 为 0 dBFS 参考，从最终 16-bit PCM 重新读取后计算。"
                 "“循环接缝差”为 `|首样本 − 末样本|`（仅循环类）。\n")
    lines.append("| 文件 | 目标时长 | 实测时长 | 峰值 dBFS | RMS dBFS | 循环 | 削波样本 | 首/尾边界幅度 | 接缝差 dBFS |")
    lines.append("|---|---:|---:|---:|---:|:---:|---:|---:|---:|")
    for name, dur, is_loop, target, _use, _fn in SPECS:
        st = results[name]
        bounds = f"{max(float(st['head']), float(st['tail'])) * 32768:.1f} LSB"
        seam = f"{float(st['seam_db']):.1f}" if is_loop else "—"
        lines.append(
            f"| `{name}` | {dur:.3f}s | {float(st['duration']):.4f}s | "
            f"{float(st['peak_dbfs']):.2f} | {float(st['rms_dbfs']):.2f} | "
            f"{'是' if is_loop else '否'} | {int(st['clipped'])} | {bounds} | {seam} |"
        )
    lines.append("")
    lines.append("检查结果：全部文件非静音、无削波样本、峰值均低于 0 dBFS；"
                 "一次性音效首尾样本均为 0 LSB，循环类首尾差见上表。"
                 "所有文件均为 22050 Hz / 16-bit / 单声道。\n")

    lines.append("## 每个音效的合成方法\n")
    methods = {
        "amb_loop.wav": "两路 43.2/57.6 Hz 正弦嗡鸣加缓慢拍频与 tanh 谐波，叠加粉红噪声整形的通风气流、"
                        "250/690 Hz 管壁共振和 22–90 Hz 低频隆隆；三次随机金属轻咔由带通噪声与三个非谐和阻尼正弦构成。"
                        "最后用短卷积混响粘合，wrap crossfade 45 ms。",
        "step_1.wav": "850–5600 Hz 宽带跟部冲击、2.4–8.2 kHz 极短鞋跟脆响、520–3000 Hz 粉红噪声鞋底摩擦，"
                      "以及 151→78 Hz 的下坠低频脚掌重量；少量混凝土砂粒脉冲和 95 ms 小房间 IR。",
        "step_2.wav": "同一物理模型但降低跟部冲击、加长 330–2100 Hz 鞋底拖动噪声并改变粘滑调制相位，"
                      "音高起点降到 132 Hz，听感更像鞋底在水泥上蹭过去。",
        "step_3.wav": "更重的变体：116→61 Hz、更长低频衰减、更大的 sub 与摩擦低频，"
                      "同时保留较短的高频鞋跟细响作为第二次微小接触。",
        "door_hiss.wav": "300–7200 Hz 粉红气流配 70–520 Hz 气团、2.3–8.8 kHz 初始嘶声和 57 Hz 阀门闷击；"
                         "0.42 s 后加入 720–5200 Hz 滑轨噪声、11.5 Hz 粘滑调制、900→1520 Hz 轻吱声和轨道共振。",
        "door_close.wav": "前 0.34 s 是 32–180 Hz 门体隆隆 + 450–2600 Hz 轨道刮擦 + 88/176 Hz 电机声；"
                          "0.345 s 处 68→32 Hz 冲击、27.5 Hz sub、金属门板非谐和模态、锁舌点击与气流“噗”，"
                          "再走 0.48 s 混凝土混响。",
        "keycard_beep.wav": "带限方波（1760/1975 Hz，只叠到 8.8 kHz 的奇次谐波）经 tanh 轻微饱和，"
                            "配 1.8 ms 起音、指数衰减和每声起点的超短宽带点击；两声间隔 96 ms。",
        "keycard_deny.wav": "238→94 Hz 的带限方波/三次谐波经 tanh 失真，19 Hz 幅度抖动，"
                            "叠 58 Hz sub 与一声低通点击，形成短促下行的“拒绝”感。",
        "pickup.wav": "2360 Hz 载波配 3350 Hz 调制器的 FM 叮声，加 3510/4690/1280 Hz 非谐和阻尼正弦、"
                      "4.2–9.8 kHz 极短 sparkle 和 0.17 s 亮混响。",
        "flashlight_click.wav": "两次 1.5–9.2 kHz 极短噪声冲击，分别配 1180/2380/3950 Hz 与 2380/4600 Hz "
                                "塑料壳体阻尼模态，第二下更轻；用 5 ms 淡入淡出保护端点。",
        "blink.wav": "43/29 Hz 缓慢低频压力、63/72 Hz 两次轻闷响、28–230 Hz 低通噪声，"
                     "再叠 1.4–7.8 kHz 快速衰减气流与 550–2400 Hz 极轻湿润声，模拟闭眼时外界高频被闷住。",
        "scp_step.wav": "核心是 120–3100 Hz 粉红石面摩擦经 20–70 Hz 不规则粘滑颗粒调制，"
                        "加 430/980/1870 Hz 干涩共振、1500–5400 Hz 硬石刮擦、52 个随机混凝土碎屑脉冲；"
                        "0.068 s 处 66→29 Hz 体重冲击、24/36.5 Hz sub、非谐和石体模态与 tanh 低频粗糙化，"
                        "最后只给 11.5% 的贴地短混响，保持贴身、干燥、没有电影感。",
        "heartbeat.wav": "两次 58→38 / 64→43 Hz 的下坠正弦心音，配 92 Hz 胸腔共振和 28–220 Hz 低通噪声，"
                         "第二声更轻更短；0.45 s 后留出舒张期，最后 60 ms wrap crossfade 接回开头。",
        "stinger.wav": "1.8–9.8 kHz 噪声爆发 + 650–5200 Hz 中频爆裂 + 1830/2270/3020 Hz 失真下行簇，"
                       "同时 420→32 Hz 低频快速下坠、27 Hz sub 与 52 Hz 起始闷击；"
                       "0.7 s 暗混响给出走廊余响。",
        "alarm_loop.wav": "392/523.25 Hz 两个柔和双音（基频 + 2/3 次谐波，5.2 Hz 轻微颤音）按 2 s 周期交替，"
                          "1050→780 Hz 低通、18 ms 梳状反射、57/85.5 Hz 设施低鸣与 0.85 s 暗混响；"
                          "4 s 循环点落在间隙，60 ms wrap crossfade。",
    }
    for name, _dur, _loop, _target, _use, _fn in SPECS:
        lines.append(f"- **`{name}`**：{methods[name]}")
    lines.append("")

    # scp_step 的针对性说明与测量。
    scp = results["scp_step.wav"]
    lines.append("## 关于 `scp_step.wav`：为什么它应该是全套最不适的\n")
    lines.append("它没有采用“干净的低频 boom + 混响”的常规打击乐做法，而是把三个令人不适的物理线索叠在一起："
                 "① 石面与水泥的粘滑摩擦，包络被 20–70 Hz 不规则噪声调制，听起来像有重量的一团东西在一顿一顿地蹭；"
                 "② 52 个随机微碎屑脉冲，没有节奏、没有音高，制造“混凝土被磨出砂”的牙齿感；"
                 "③ 66→29 Hz 的体重下坠与 24/36.5 Hz sub，配合 tanh 产生的粗糙谐波，让胸腔先感到“有东西落在背后”。"
                 "混响只有 11.5%，所以它不像远处电影音效，而像贴着后颈发生。\n")
    lines.append(f"该文件实测峰值 **{float(scp['peak_dbfs']):.2f} dBFS**、RMS **{float(scp['rms_dbfs']):.2f} dBFS**；"
                 f"首尾边界为 0 LSB，无削波。建议游戏内音量不要压得太低，它是本套音效的信息通道之一。\n")

    lines.append("## 自评：最不满意的两个\n")
    lines.append("1. **`blink.wav`**：耳膜压迫本质上有一半是“体感”而不是耳机能还原的听觉事件；"
                 "在笔记本扬声器上它很可能只像一记很轻的低频闷响，闭眼/睁眼的语义要靠画面配合。"
                 "低频 29–43 Hz 的份额也让它在小喇叭上损失较多。")
    lines.append("2. **`flashlight_click.wav`**：60 ms 的长度和单声道让它只能是合格的机械咔嗒，"
                 "缺少真实手电筒那种弹簧回弹的细微二次振动与壳体差异；两次点击的模态还是偏“合成器”。"
                 "如果后续允许更长的 tail，我会加一个 15–25 ms 的金属弹簧余振。\n")

    lines.append("## 复现\n")
    lines.append("```powershell")
    lines.append(r"& 'C:\Users\Miyazawa i\AppData\Local\Programs\Python\Python311\python.exe' "
                 r"'C:\Users\Miyazawa i\Desktop\scp\assets\audio\gen_audio.py'")
    lines.append("```")
    lines.append(f"\n本次生成耗时约 {elapsed:.1f} s（含分析与写报告）。脚本中所有随机源均使用固定 seed，"
                 "重复运行会得到相同结果（浮点库版本差异可能带来极小量化差异）。\n")

    (OUT_DIR / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    import time
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: Dict[str, Dict[str, object]] = {}
    print(f"Output: {OUT_DIR}")
    print(f"Format: {SR} Hz / {BIT_DEPTH}-bit / mono")
    for name, dur, is_loop, target, _use, fn in SPECS:
        print(f"  synthesizing {name:<22} {dur:>5.2f}s ...", end="", flush=True)
        x = fn()
        expected = sec_to_samples(dur)
        if len(x) != expected:
            raise AssertionError(f"{name}: length {len(x)} != expected {expected}")
        x = remove_dc(x)
        if is_loop:
            # 循环类不做首尾淡出，接缝由 wrap_crossfade 保证。
            x = normalize_peak(x, target)
        else:
            x = fade_edges(x, 0.005 if dur <= 0.2 else 0.006,
                           0.008 if dur <= 0.2 else 0.010)
            x = normalize_peak(x, target)
        # 极端兜底：确保量化后不会碰到满刻度。
        x = np.clip(x, -0.99, 0.99)
        path = OUT_DIR / name
        write_wav(path, x)
        st = analyze(path, is_loop)
        results[name] = st
        print(f" peak {float(st['peak_dbfs']):6.2f} dBFS  RMS {float(st['rms_dbfs']):6.2f} dBFS")

    # ---- 自动质量检查 ----
    errors: List[str] = []
    for name, dur, is_loop, target, _use, _fn in SPECS:
        st = results[name]
        if abs(float(st["duration"]) - dur) > (1.0 / SR + 1e-9):
            errors.append(f"{name}: bad duration {st['duration']}")
        if float(st["clipped"]) != 0:
            errors.append(f"{name}: {st['clipped']} clipped samples")
        if float(st["peak_dbfs"]) > -0.5:
            errors.append(f"{name}: peak too hot {st['peak_dbfs']}")
        if float(st["rms_dbfs"]) < -75.0:
            errors.append(f"{name}: effectively silent RMS {st['rms_dbfs']}")
        if abs(float(st["peak_dbfs"]) - target) > 0.25:
            errors.append(f"{name}: target peak {target} actual {st['peak_dbfs']}")
        if is_loop:
            if float(st["seam_jump"]) > 0.012:
                errors.append(f"{name}: seam jump too large {st['seam_jump']}")
        else:
            if max(float(st["head"]), float(st["tail"])) > 1e-6:
                errors.append(f"{name}: nonzero edge samples")
    if errors:
        raise SystemExit("QUALITY CHECK FAILED:\n  " + "\n  ".join(errors))

    write_manifest(results)
    write_report(results, time.time() - t0)
    print("\nQuality check: PASS")
    print("  - all formats, durations, peaks, RMS, clipping and boundaries checked")
    print("  - loop seams checked; edge fades checked")
    print("  - wrote audio_manifest.json and REPORT.md")


if __name__ == "__main__":
    main()

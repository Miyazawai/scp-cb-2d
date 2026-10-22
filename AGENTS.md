# SCP:CB 2D — agent notes

把 SCP – Containment Breach 做成**像素俯视 2D** 的免费同人游戏。Godot 4 / GDScript。

动手之前先读：

- `CONTEXT.md` —— 这个项目的术语表。输出里提到领域概念时用表里的词，别用 `_Avoid_` 里的同义词。
- `docs/adr/` —— 四条硬决策（俯视 + 光照遮蔽、Godot、永不做战斗、三幕 + 回程）。和 ADR 冲突时显式说出来，不要默默覆盖。
- `docs/design/game-design.md` —— 剧情、四幕结构、beat 表、结局、内容预算。

## 环境

- Godot 4.7.2 标准版（非 mono）：`D:\software\Godot\4.7.2\Godot_v4.7.2-stable_win64.exe`
- 直接跑：`Godot_v4.7.2-stable_win64.exe --path .`
- 无窗口自检：`--headless -- --validate`（关卡数据）、`-- --selftest`（连通性）、`-- --audit`（素材就位）
- 截图：`-- --shot` / `--shot2` / `--shot3` / `--start`，会存 `demo_shot*.png` 后自动退出
- 所有中文文档写完后跑 `python tools/check_encoding.py`，`BAD` 或 `DECODE-FAIL` 一律当失败

## 结构

- `levels/act1.json` —— 关卡数据。加内容 = 加 JSON 块，不要去写死坐标。
- `scripts/main.gd` —— 关卡构建、流程、交互、HUD、存档
- `scripts/player.gd` —— 移动、手电、眨眼、电量、体力、"看见"判定
- `scripts/scp173.gd` —— 凝视规则（瞬移步）
- `scripts/ui.gd` / `scripts/i18n.gd` —— 界面与中英词条（中文默认，L 切换）
- `assets/art`、`assets/audio` —— 全部由脚本生成，可复跑；缺图时会自动降级成程序绘制

## 硬规则

1. **不做战斗**。没有血条、伤害、成长。玩家的手段只有移动、躲藏、开关灯、跑。
2. **"看见" = 手电光锥照到 ∧ 睁眼 ∧ 无遮挡**。环境光不算。
3. **死亡必须可归因**，只有天灾事件（106）允许"不讲理"。
4. 界面文案一律走 `i18n.gd`，中文为默认语言。

## Agent skills

### Issue tracker

Issues live in this repo's GitHub Issues (`gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary, label strings equal to role names. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

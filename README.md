# SCP:CB 2D

把《SCP – Containment Breach》的体验做成**像素俯视 2D** 的免费同人游戏。开源、非商业。

![demo](docs/images/demo.png)

> 状态：**可玩 demo（垂直切片）**。只有一处手工搭建的设施区段，用于验证核心机制是否成立：黑暗里的手电、看不见就动的东西、会耗尽的眼睛。

## 现在这个 demo 里有什么

| 机制 | 实现 |
|---|---|
| 黑暗与光照 | 全场熄灭，只有顶灯光斑与手电锥形光；墙体真实遮挡光线 |
| 手电电量 | 最核心的资源，耗尽后你只能靠顶灯的余光活着 |
| "看见"判定 | **锥内 ∧ 被照亮 ∧ 眼睛睁开** 三者同时成立，才算看见 |
| SCP-173 | 只要没被看见就以恒定速度走向你，被看见就完全冻结；接触即死 |
| 眨眼 | 22 秒强制眨眼 0.35 秒，期间全黑；可以提前按空格主动眨，把闭眼时机握在自己手里 |
| 门禁 | 1 级钥匙卡 → 开启走廊尽头的区域门 |
| 逃出 | 走到绿色逃生区即通关 |

还没有的：随机地图、多个 SCP、存档、声音、剧情。它们都在路线图里（见下）。

## 操作

| 键 | 动作 |
|---|---|
| `WASD` / 方向键 | 移动 |
| 鼠标 | 转动手电方向（**逃跑时可以把光留在身后**） |
| `Shift` | 冲刺（更快耗尽手电） |
| `空格` | 主动眨眼 |
| `F` | 开关手电 |
| `R` | 重开 |
| `Esc` | 退出 |

## 运行

需要 **Godot 4.7**（标准版，不需要 .NET 版）。

```powershell
# 本机已装好的路径
D:\software\Godot\4.7.2\Godot_v4.7.2-stable_win64.exe --path "C:\Users\Miyazawa i\Desktop\scp"
```

也可以在本目录双击 `play.cmd`。或者用 Godot 编辑器打开 `project.godot`，按 F5。

画面是 480×270 内部分辨率、16px tile、整数倍放大到 1440×810。

## 目录

```
project.godot          引擎配置（480×270、最近邻过滤）
main.tscn              唯一场景，节点由脚本生成
scripts/main.gd        关卡搭建、门禁、HUD、游戏流程
scripts/player.gd      移动、手电、眨眼、电量、"看见"判定
scripts/scp173.gd      SCP-173 的凝视规则
scripts/keycard.gd     钥匙卡
tools/check_encoding.py  中文文档编码自检
CONTEXT.md             术语表（这个项目里的词各指什么）
docs/adr/              硬决策记录
docs/research/         原作系统与地图生成的逆向调研、素材来源登记
art/_poc/              像素素材产线的可行性探针（程序化生成的占位美术）
```

## 设计上的四条硬约束

写在 `docs/adr/` 里，任何新提案都要先过这几关：

1. [俯视 2D + 光照遮蔽作为一等机制](docs/adr/0001-top-down-2d-with-light-occlusion.md)
2. [引擎用 Godot 4](docs/adr/0002-godot-4-gdscript.md)
3. [永不做战斗系统](docs/adr/0003-no-combat.md)
4. 承重系统只有五个：眨眼凝视、随机设施、钥匙卡权限攀升、黑暗与电量、SCP-106 的天灾追击

## 路线图

- [x] 垂直切片：一处区段、173、手电、眨眼、门禁、逃生
- [ ] 用 2D 重写设施生成（参考 `docs/research/map-generation-spec.md` 里的蛇形走廊 + 四邻接定型算法）
- [ ] 声音作为信息通道：脚步、腐蚀声、石材摩擦声，配极简方向提示
- [ ] SCP-106 与天灾事件
- [ ] 难度档位与存档终端
- [ ] 十个 SCP 的 2D 机制
- [ ] 三区推进与回程

## 许可

- **代码**：MIT（见 `LICENSE`）
- **美术 / 文本 / 设计文档**：CC BY-SA 4.0（衍生自 SCP 基金会内容，见 `NOTICE.md`）
- 未使用原作任何代码与素材；未使用 SCP-173 的原型图像。

本项目是免费同人作品，与 SCP 基金会 wiki 的贡献者共享同一套世界观。SCP 基金会内容以 CC BY-SA 3.0 发布：https://scp-wiki.wikidot.com/licensing-guide

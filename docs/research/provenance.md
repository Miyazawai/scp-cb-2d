# 调研素材来源登记（provenance）

登记时间：2026-10-22 18:54–18:59 +08:00（本机时间，Asia/Shanghai）。
所有 .bb 文件均为 **SCP – Containment Breach v1.3.11** 的 Blitz3D 源码，仓库 `Regalis11/scpcb`（master 分支），
仓库 README 声明「游戏与源码均以 CC BY-SA 3.0 发布」。文件仅作只读分析，未修改、未移动。

## 一、源码文件（下载于 C:\Users\Miyazawa i\Desktop\scp\）

| 本地文件 | 原始 URL | 下载时间 | 对应页面 / 作品 | 用途 |
|---|---|---|---|---|
| MapSystem.bb | https://raw.githubusercontent.com/Regalis11/scpcb/master/MapSystem.bb | 2026-10-22 18:54:35 | SCP – Containment Breach（原作，v1.3.11 源码） | 地图生成 `CreateMap()`、房型常量、chunk 系统 |
| UpdateEvents.bb | https://raw.githubusercontent.com/Regalis11/scpcb/master/UpdateEvents.bb | 2026-10-22 18:55:50 | 同上 | 随机事件（如 `682roar`）、blackout 音效、房间脚本 |
| Main.bb | https://raw.githubusercontent.com/Regalis11/scpcb/master/Main.bb | 2026-10-22 18:55:52 | 同上 | blink timer / stamina、`GenerateSeedNumber()`、MTF 公告 |
| NPCs.bb | https://raw.githubusercontent.com/Regalis11/scpcb/master/NPCs.bb | 2026-10-22 18:55:53 | 同上 | NPC 行为（MTF、SCP 实体） |

仓库首页（许可与说明）：https://github.com/Regalis11/scpcb
源码目录页：https://github.com/Regalis11/scpcb/tree/master

## 二、图片素材（C:\Users\Miyazawa i\Desktop\scp\img\）

| 本地文件 | 原始 URL | 下载时间 | 所属页面 / 作品 | 实际内容 |
|---|---|---|---|---|
| permafrost.png | https://img.itch.zone/aW1nLzI2NTkxNTEwLnBuZw==/original/a6Brn1.png | 2026-10-22 18:55:13 | https://leoswitcher.itch.io/scp-permafrost （SCP: Permafrost，Leo，GameMaker） | 该 itch 页的封面图（cover），非游戏内截图 |
| wasd.gif | https://img.itch.zone/aW1nLzI3OTA5Njg2LmdpZg==/original/xKydZZ.gif | 2026-10-22 18:55:13 | https://wasd-game-studio.itch.io/scp-containment-breach-2d （SCP - Containment Breach - 2D，W.A.S.D） | 页面顶部 banner（SCP 标志 + 噪点），非玩法画面 |
| wasd2.gif | https://img.itch.zone/aW1nLzI3OTA5NTY4LmdpZg==/original/dvc5XK.gif | 2026-10-22 18:55:20 | 同上 | 页面正文的 logo 动画（"SECURE. CONTAIN. PROTECT."），非玩法画面 |

注意：这三张图都**不是 gameplay 截图**，无法用来判断视角或玩法；引用时请勿当作实机画面。
若需要实机画面，应回到对应 itch 页面取 screenshot 区，或抓取作者发布的视频。

## 三、文字来源（简报中的链接）

- Wikipedia：SCP – Containment Breach — https://en.wikipedia.org/wiki/SCP_%E2%80%93_Containment_Breach
- Speedrun.com 指南（结局条件）— https://www.speedrun.com/scpcb/guides/tblm6
- rooms.ini（房间模板表）— https://github.com/Regalis11/scpcb/blob/master/Data/rooms.ini
- SCP Wiki 授权指南 — https://scp-wiki.wikidot.com/licensing-guide
- 05Command：移除 SCP-173 图片讨论 — https://05command.wikidot.com/forum/t-14468375/
- itch.io 页面：wasd-game-studio / yellowstarstudio / gamerj7564 / leoswitcher / deepnight
- Steam：Nuclear Blaze — https://store.steampowered.com/app/1662480/Nuclear_Blaze/

## 四、授权提示

- SCP Wiki 文本：CC BY-SA 3.0，衍生作须署名并以同协议发布。
- SCP:CB 代码与素材：CC BY-SA 3.0（SCP-173 相关除外）。
- SCP-173 原型雕塑 Untitled 2004（Izumi Kato）不在 CC 内，禁止商用相关图像。
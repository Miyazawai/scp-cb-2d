# SCP – Containment Breach 与 2D 同人调研简报

**版本**：v1.3.11（2018-08-19）终版，Blitz3D，Joonas "Regalis" Rikkonen，2012 首发。

## 1 核心循环与胜负

D-9341（Class-D）在 SCP-173 实验事故后遇收容失效，无战斗力，须穿越 LCZ→HCZ→EZ 从 Gate A/B 逃出（[wiki](https://en.wikipedia.org/wiki/SCP_%E2%80%93_Containment_Breach)）。事故起因是 Chaos Insurgency 双面间谍释放 106、并把设施控制权交给 079（同上）。难度 Safe/Euclid/Keter 只改存档：随时 / 检查点 / 禁存档＋永久死亡（同上）。4 结局：Gate A 两条——关 remote door control 后被 MTF 扣留并获 SCP 编号，或未重收容 SCP-106 时趁乱逃出、被 Chaos Insurgency 带走；Gate B 两条——启动核弹、682 存活，或关核弹后被 Cloud Nine 处决（同上）。四条均需 EZ 的 electrical center（[guide](https://www.speedrun.com/scpcb/guides/tblm6)）。

## 2 系统

探索/随机地图：每局按 seed 重排（wiki）。门禁：1–5 级 keycard、密码门、气闸（wiki）。物品/背包：格数有限，含手电、电池、防毒面具、急救包与 SCP 物件（wiki）。blink meter：自然耗尽、须强制眨眼，闭眼时 173 可动（wiki）。体力：Shift 冲刺，耗尽硬直（[Main.bb](https://github.com/Regalis11/scpcb/blob/master/Main.bb)）。173：无人注视时移动，贴身秒杀（wiki）。106：触碰入 pocket dimension，须自寻出口，可重收容（wiki、guide）。096：看到面部即追杀（wiki）。049/079/895/966/372：接触即死的处决者、可对话的门禁 AI、监控画面致幻、需夜视才可见的隐形猎手、只在余光中出现的尾随者（[rooms.ini](https://github.com/Regalis11/scpcb/blob/master/Data/rooms.ini)）。MTF Nine-Tailed Fox：定时入场，先广播后交火，并播报 173 的收容状态（wiki、Main.bb）。停电/警报/广播：blackout、Tesla gate、MTF 公告（rooms.ini、[events](https://github.com/Regalis11/scpcb/blob/master/UpdateEvents.bb)）。文档/终端：lore 兼路线提示，部分直接给出 106、895 的应对法（wiki）。解谜：electrical center、Alpha/Omega 核弹井、Tesla gate 走廊；“温室”未证实（原作对应 SCP-860 森林）。随机事件：682 咆哮；server room、lockroom 实为固定房脚本/定时气闸（events）。

## 3 地图生成

三区 LCZ/HCZ/EZ 按纵向三分，跨界格标 checkpoint（[MapSystem.bb](https://github.com/Regalis11/scpcb/blob/master/MapSystem.bb)）。粗网格蛇形开主走廊：横段 10–15 格、竖段 3–4 格、每廊 4–5 条支路（同上）。按四邻接数定房型：1=room1、直线 2=room2、拐角 2=room2C、3=room3、4=room4；每区不足 5 个 room1 或没有 room4/room2C 时强制改造（同上）。模板在 rooms.ini 定义 shape、zone1–5、commonness（0–100 权重，0 表示脚本固定放置）、large、tesla（rooms.ini）。房间 props（灯、聚光灯、soundemitter、screen、waypoint、道具）由 .rmesh 的 point entity 与 FillRoom 生成（同上）。特殊房按房型列表百分比槽位插入（roompj 10%、914 30%、049 40%），故必现而位置不同（MapSystem.bb）。seed 为字符串，哈希后 SeedRnd，同 seed 同图；基础设施无区块重生成，仅 1499 维度用 chunk 循环（Main.bb）。

## 4 承重墙判断

承重墙：① 眨眼/凝视——“看”是资源；② 无战斗力，只能逃/躲；③ 程序化设施＋keycard＝权限攀升；④ 稀缺存档。依据：删①失去专属动词，删②变射击，删③凝视无法组织成旅程，删④死亡失重。可替换：SCP 名单（173/106 除外）、背包格数、体力、Tesla gate、广播、结局数量、核弹演出——只调风味与节奏。对 2D 改编，把“注视”落成面向/视野锥或摄像头切换，是保留承重墙的最低成本方案（判断）。

## 5 2D / 像素同人

1. **SCP - Containment Breach - 2D**（W.A.S.D，itch）：2D 横向重制，pre-Alpha，仅 8 个 SCP、无存档；个人规模，样本太少、口碑未证实（[itch](https://wasd-game-studio.itch.io/scp-containment-breach-2d)）。
2. **SCP:CB: Python Edition Remastered**（Yellow Star，pygame）：8-bit 重制，2025 起更新，仅 LCZ 完成；无评分数据（[itch](https://yellowstarstudio.itch.io/scp-containment-breach-python-edition)）。
3. **SCP: 2D**（Gamerj7564，TurboWarp）：Scratch 系 2D，含地图生成与 4 难度，一人约一年完成（[itch](https://gamerj7564.itch.io/scp-2d)）。
4. **SCP: Permafrost**（Leo，GameMaker）：俯视像素 souls-like，重战斗与数值，开发中；5.0 分但仅 1 条评分（[itch](https://leoswitcher.itch.io/scp-permafrost)）。
5. **Nuclear Blaze**（Deepnight，Steam）：横版像素消防，$9.99，96% 好评（780 评），商业完成度最高（[Steam](https://store.steampowered.com/app/1662480/Nuclear_Blaze/)）。

## 6 版权

SCP Wiki 文本 CC BY-SA 3.0：须署名并以同协议发布（[licensing](https://scp-wiki.wikidot.com/licensing-guide)）。原作代码/素材同为 CC BY-SA 3.0，唯 173 例外（wiki、[repo](https://github.com/Regalis11/scpcb)）。173 原型 Untitled 2004（Izumi Kato）非 CC，Wiki 已撤图并禁售相关商品（[O5](https://05command.wikidot.com/forum/t-14468375/)）。同人惯例：免费＋署名，或去 SCP 化（Nuclear Blaze 即如此）；商业化多为灰色地带。2026-02 社区 Preservation Project 在 CC BY-SA 下把原版搬上 Steam（wiki）。

## 事实清单

1. v1.3.11（2018-08-19）终版，Blitz3D。
2. 4 结局＝Gate A×2＋Gate B×2，均需 electrical center。
3. 难度只改存档；Keter 永久死亡。
4. 地图＝3 区＋蛇形走廊＋邻接定房型＋commonness＋seed。
5. 特殊房按百分比槽位插入，必现而位置随机。
6. 承重墙＝凝视＋无战斗力＋权限攀升＋稀缺存档。
7. 2D 同人多停在“仅 LCZ”或“无结局”。
8. 173 图像是硬红线；安全商业化＝去 SCP 化。
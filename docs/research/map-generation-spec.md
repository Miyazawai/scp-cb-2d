# SCP:CB 设施生成技术规格（MapSystem.bb 逆向）

**总结论**：设施主图 = `MapTemp` 网格上的蛇形走廊 + 四邻接定型 + 加权模板；`GenForestGrid` 只做 SCP-860 森林（`MapSystem.bb:2153-2157`），chunk 只做 SCP-1499（`MapSystem.bb:8314`），均不参与设施。未标文件名者为 `MapSystem.bb`。

## 1. `CreateMap()` 主流程

`CreateMap()`（`MapSystem.bb:7023`）内没有独立的“走廊连接/灯光/NPC/chunk”阶段。

| # | 步骤 | 输入 → 输出 | 依据 |
|---|---|---|---|
| 1 | 设 `I_Zone\Transition` 为 13/7，`SeedRnd` | 种子 → RNG | 7026-7037 |
| 2 | 蛇形主走廊：横段 10–15 格、竖段 3–4 格、每层 4–5 条支路 | 空网格 → 0/1/255 | 7043-7113 |
| 3 | 四邻接定型并按区分型计数 | `MapTemp` → 1..4 | 7120-7146 |
| 4 | 每区补 ≥5 个 ROOM1，强制 ≥1 个 ROOM4、≥1 个 ROOM2C | 计数 → 新 `MapTemp` | 7149-7356 |
| 5 | 建 `MapRoom$`，按百分比槽位写命名房 | 计数 → 房名表 | 7358-7453 |
| 6 | 逐格实例化：255→checkpoint，度 1/2/2C/3/4→`CreateRoom` 并旋转 | `MapTemp` → `Rooms` | 7455-7584 |
| 7 | 重叠修正、压平网格、邻格建门、建 `Adjacent[4]` | 房间 → 门与邻接图 | 7586-7767 |

灯光/道具由 `FillRoom` 按房名生成（2046、5506-5528）；waypoint 由 `InitWayPoints` 在 `CreateMap` 后建立（`Main.bb:8396-8400`），NPC 在 `InitNewGame`（`Main.bb:8404`）。

## 2. 森林网格 `GenForestGrid`

常量在 820-827。索引为 `(gridsize-1-y)*gridsize+x`，数组 y 向下、逻辑 y 向上（906）。它**不是从中心扩散**：从底部门格 `door2_pos` 出发（903-906）向上走一条主路径，`center=5` 只用于偏离钳制（866-875）。

- **主行走**：`dir=1` 时每步 40% 偏成左/右（912-914）；横向偏离达 `|x-center|>=3` 即掉头（870-871、916-917）。
- **回归**：横走时 27% 或已越界则强制 `dir=1`；刚转纵向时连走两格，避免 2×2 粗线（925-936）。
- **收尾**：到 `pathy>=6` 后直冲到 8，再沿顶行横走到 `door1_pos`（944-959）。
- **分叉**：`new_y` 由 -3 每次 +4、条件 `<4`，`gridsize=10` 时**只尝试一行**（964-966）；65% 触发（969），在最左/最右路径旁开洞；分支只活 2 步（995-997），每步 18% 死亡、25% 横走否则上移，邻接已有路径或 `temp_y>=8` 即停（1000-1024），最后 -1/-2 改回 1（1029-1040）。

伪代码：

```
door1,door2 = rand(3,7)
x=door2; y=1; dir=1                  # 1=逻辑向上
while y < 6:
  if dir==1:
    if rand(100)<=40: dir = 0 or 2   # 偏离
    dir = clamp_turn(dir,x,center=5,maxdev=3)
    step(dir)
  else:
    dir = clamp_turn(dir,x,5,3)
    if 越界 or rand(100)<=27: dir=1  # 回归
    step(dir); if dir==1: step(dir)  # 连走两格
  grid[y][x]=1
while y<8: step(1); grid[y][x]=1     # 冲顶
while x!=door1: step(side); grid[y][x]=1
for row in [1]:                      # 仅一次
  if rand(100)<=65:
    在 row 最左/最右路径旁开洞，横移 2 格
    for life in 1..2:
      if rand(100)<=18: break        # 死亡
      25% 横移 else y+1
      邻接已有路径则停
把 -1/-2 改回 1
```

## 3. 房间形状与模板匹配

`ROOM1..ROOM4`（1606）按出口数定义：ROOM1 死路 1 口、ROOM2 直线 2 口、ROOM2C 拐角 2 口、ROOM3 三岔 3 口、ROOM4 十字 4 口。朝向：ROOM1 朝唯一出口，ROOM2/2C/3 分别对齐直线、拐角、三岔开口，ROOM4 无朝向。四邻接定型（7128-7143），建门时由 shape+angle 白名单确认（7668-7717）；朝向由 `TurnEntity` 决定（7489-7556）。

`CreateRoom`（2023）先按 `name$` 匹配命名房（2032-2056）；否则收集 `zone[i]=zone` 且 `Shape=roomshape` 的 `Commonness` 权重，用 `Rand(temp)` 轮盘抽取（2058-2097）。无匹配时落空返回（2099）。

## 4. 分区

`ZONEAMOUNT=3`（1749），`GetZone(y)=Min(Floor((MapWidth-y)/MapWidth*3),2)`（7802-7804）。因 `MapWidth=MapHeight`（1750），等价于按 y 三分：y 大→0，y 小→2；`CreateMap` 内部却用 1/2/3（7463-7468），两套编号。

约束：模板 `zone1..zone5` 限定可出现的区（1681-1683、2061-2065）；每区至少 5 个 ROOM1、1 个 ROOM4、1 个 ROOM2C（7149-7356）；跨区格标 255→checkpoint（7099-7103、7472-7477）；zone 2 的通用门是重型门 `big=2`（7662、7691）；门等级取 zone（7691）。`I_Zone\Transition` 13/7 为门与玩家分区阈值（7026-7027、7652-7658、5564-5570），与 `GetZone` 不一致。

## 5. 模板加载

`LoadRoomTemplates("Data\rooms.ini")` 在文件加载期执行（1746）。格式为 INI 段 `[房名]`，可读键：`mesh path`、`shape`、`zone1..zone5`、`commonness`（0-100 权重）、`large`、`disabledecals`、`usevolumelighting`、`disableoverlapcheck`（1660-1689）。

尺寸**不在 ini**：由 `CalculateRoomTemplateExtents` 取包围盒（1718、8544-8556）。门、灯、道具也主要不在 ini：`.rmesh` 内嵌 point entity（574-674），`.b3d` 由 `LoadWorld` 按 `classname` 解析（54-210）；钥匙卡在 `FillRoom` 按房名写死（2102 起）。工作区无 `rooms.ini`，字段值未能核对。

## 6. 重叠检测与修正

`CalculateRoomExtents` 把模板 AABB 经 `TFormVector` 转到世界、收缩 0.05 并纠正 min/max（8558-8588）；`CheckRoomOverlap` 做三轴分离检测（8590-8595）。`PreventRoomOverlap`：跳过 start/checkpoint → 不交叠即返回 → ROOM2 试转 180° → 不行则与同 zone 同 shape 房互换位置/朝向并复查，失败回滚，仍失败只写日志且**不删房间**（8597-8732）。`DisableOverlapCheck` 默认 `True`（1631），须 ini 设 0 才启用（1689、8598）。

## 7. 门与钥匙卡

`CreateMap` 的通用连通门只传 `dopen` 和 `big`，未传 keycard（7691、7721），房与房之间的门默认无卡。钥匙卡等级是 `CreateDoor` 第 9 参数 `keycard`（`Main.bb:1866`），在 `FillRoom` 逐扇硬编码，如 1 级（2149-2150）、3 级（2499）、4 级（2549）；密码门走 `code$`（2144-2145 的 `"ABCD"`）。结论：**不在模板里，也不随机**，是按房名固定的常量；`rooms.ini` 无此字段（1660-1689）。

## 8. 寻路

`FindPath`（5999）是 **A\***：先清空所有 waypoint 状态（6019-6024）；起点取最近点（350，不可见 ×3，6038-6058），终点半径 400（6070-6083）；开放表线性扫描最小 F（6105-6113），5 邻接松弛（6120-6148）；H 为 XZ 曼哈顿距离（6135），MTF 对“无门边”+0.5（6126-6128）；成功后回溯 parent，最多 20 点（6174-6183）。瑕疵：6141 行 `Fcost` 用父节点 G 而非新 G。

图构建：每扇门一个 waypoint（5861-5897），模板内嵌 waypoint（595-605、127-135）；两点距离 <7、同房或任一端是门、且 `EntityVisible` 时双向连边，每点最多 5 条（5911-5963）。

## 9. chunk 流式加载

只服务 SCP-1499：`CreateChunkParts` 读 `Data\1499chunks.INI` 预拷贝部件（8214-8261）；`CreateChunk` 以 40 单位复制物体和地板（8274-8312）；`UpdateChunks` 以玩家 40 格坐标为中心生成 7×7（±120）chunk，超距删除，并按上限增删 `NPCtype1499`（8314-8416）。调用点在 1499 事件（`UpdateEvents.bb:8974`）与读档（`Main.bb:8607-8616`）。**设施主图无 chunk**。

## 10. 迁移判断

### A. 可直接迁移到 2D 俯视 tile

| 机制 | 理由 |
|---|---|
| 蛇形主走廊（7043-7113） | 纯 x/y 置位。 |
| 四邻接定房型（7120-7146） | 2D 邻域计数。 |
| zone 按 y 三分（7802-7804） | 一维分段。 |
| shape+commonness（2058-2097） | 权重与维度无关。 |
| 命名房槽位（7771-7800） | 纯数组占位。 |
| A\* + waypoint（5999-6192） | 2D 曼哈顿更简单。 |
| 门/钥匙卡（`Main.bb:1866`） | 门=边上的对象。 |
| AABB 重叠（8558-8732） | 2D 退化为矩形相交。 |

### B. 因 3D 存在、必须在 2D 重写

| 机制 | 理由 |
|---|---|
| `PlaceForest` 瓦片（1045-1311） | 12 单位 tile 与高度是 3D 资产。 |
| 世界坐标 `x*8/z*8`（7466、7488） | 8 米格距要换像素 tile。 |
| `TFormVector` 包围盒（8565-8574） | 依赖 3D 变换矩阵。 |
| 门框/双开门/按钮（`Main.bb:1873-1969`） | 2D 只需门格与状态。 |
| 灯/光锥（138-174、8514-8542） | 俯视应以视野/光照贴图替代。 |
| `EntityVisible` 连边（5938-5940） | 3D 射线加高度。 |
| Chunk 流式加载（8274-8416） | 为 3D 无限奔跑设计。 |
| 音效/triggerbox（175-186、530-570） | 3D 空间化与体触发。 |


**未能确定**：`cobble_chance` 取值（971，源码未定义）；`rooms.ini` 内容；`CalculateRoomExtents` 默认是否生效。

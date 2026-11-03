# 案卷 `lightsout3` —— Lights Out 翻转机制 · 3×3 确定性变体

引擎 **explicit** 口径（状态置换 + 逐元素按钮改名声明）的第二份真实系统
案卷，也是本法庭第二个非平凡真对称正控：完整 8 元素棋盘群 **D4** 以逐元素
按钮映射放行——与 `mini2048` 同群、不同机理（Toggle 代数，而非合并滑动）。

一键复现全部案卷：
`python -X utf8 cases/lightsout3/make_lightsout3.py --check`（字节自证 + 穷举
对称自证，退出码 0）。

## 模型

Lights Out 谜题（Tiger Electronics 掌机，1995 年公开发售；规则公开）的
确定性翻转核心。每条生成规则都在
`model.json → meta.rules_with_citations` 里引一手出处；两条规则源是：

- Wikipedia [《Lights Out (game)》](https://en.wikipedia.org/wiki/Lights_Out_(game))
  Gameplay 段："Pressing any of the lights will toggle it and the four
  adjacent lights."（按任一灯会翻转它与相邻四盏）；"The goal of the puzzle
  is to switch all the lights off, preferably in as few button presses as
  possible."（目标是熄灭全部灯）；Strategy 段："the order in which the
  lights are pressed does not matter, as the result will be the same"
  （按键顺序无关）；"pressing a light twice is equivalent to not pressing it
  at all"（按两次等于没按）。
- [Jaap's Puzzle Page "Lights Out"](https://www.jaapsch.net/puzzles/lights.htm)
  （Wikipedia 为该游戏引用的规则页）："By pressing a button, its light and
  those of the (non-diagonally) adjacent buttons will change (switch on if
  it was off, and vice versa)."（按下按钮，它与非斜向相邻按钮的灯状态翻转）。

- 512 态 = 2^9（9 盏灯 × 1 bit，bit i = 灯 i，1=亮 / 0=灭）。**512 个全是
  真态——本案没有填充态**：3×3 翻转矩阵在 GF(2) 上秩为 9（生成器每次运行
  都断言），故全灭态出发可达全部配置；每态 9 个后继两两不同（零自环——
  每个翻转掩码都含自己的按钮位），且任意两态的整行互不相同。对比
  `mini2048`：256 态中 175 个是填充态。
- 9 动作 = 9 个棋盘按钮，按位置编号（按钮 a 坐在灯 a 上）。九个翻转掩码
  是一手数据，记录在 `meta.toggle_masks`。
- 奖励全零**是设计如此**：原版游戏无计分（`meta.rules_with_citations`
  R6）；胜利条件——9 灯全灭（态 0）——作为终局性质记录在
  `meta.win_condition`（"获胜后设备并不锁定"），不折算成逐边奖励（与
  `tcp`/`dhcp`/`imap` 的全零奖励同一约定）。因此本案的裁决完全落在转移层。
- 变体边界（见 `meta.transcription_notes`）：3×3 棋盘（Tiger 原版是 5×5
  ——"The game consists of a 5 by 5 grid of lights"；3×3 脉络经 Merlin
  再版 Magic Square——"exactly the same as the standard Lights Out … a 3x3
  Lights out"，Jaap's 页——与 Lights Out Cube 的 3×3 面）；开局随机布灯
  未收录。

## 棋盘对称群与 explicit 口径

3×3 棋盘的对称群是 D4（8 阶）。真棋盘对称会**连同格子一起挪按钮**：棋盘
顺时针转 90° 后，原来的左上按钮就是现在的右上按钮。每个群元素 π 的按钮
改名 ρ(π) 是**被 forced 的**，且 π ↦ ρ(π) 构成群同态。`make_lightsout3.py`
在**全部 9! = 362 880 个按钮排列**上穷举推导每个 D4 元素的 ρ(π)（每元素
恰有一个合法映射——每次运行都断言），并对全部 64 个有序对断言同态律。
已验证的映射表（按钮 0..8 按行主序，0=左上，4=中心，8=右下）：

| 元素 | 内容映射（格） | forced 按钮映射（按钮 0..8） |
|---|---|---|
| 恒等 | [0,1,2,3,4,5,6,7,8] | [0,1,2,3,4,5,6,7,8] |
| 顺时针旋转90° | [2,5,8,1,4,7,0,3,6] | [2,5,8,1,4,7,0,3,6] |
| 旋转180° | [8,7,6,5,4,3,2,1,0] | [8,7,6,5,4,3,2,1,0] |
| 逆时针旋转90° | [6,3,0,7,4,1,8,5,2] | [6,3,0,7,4,1,8,5,2] |
| 上下翻转 | [6,7,8,3,4,5,0,1,2] | [6,7,8,3,4,5,0,1,2] |
| 左右翻转 | [2,1,0,5,4,3,8,7,6] | [2,1,0,5,4,3,8,7,6] |
| 主对角转置 | [0,3,6,1,4,7,2,5,8] | [0,3,6,1,4,7,2,5,8] |
| 反对角转置 | [8,5,2,7,4,1,6,3,0] | [8,5,2,7,4,1,6,3,0] |

（位置按钮系统里内容映射与按钮映射重合：灯挪了，十字也跟着挪，翻转挪后
十字的按钮就是挪后的按钮。）

## 补集正控与"无填充态"偏离

因为翻转是 XOR，**全盘取反映射** π(s) = 511 ⊕ s 与每一次按键可交换、且
不改动任何按钮名——是 *fixed* 口径（按钮钉死）下的真对称。

对 `mini2048` 范式的偏离，如实记录：本案的平凡正控**不是**填充态对换，
因为本案没有填充态可换（翻转矩阵秩 9——见上）。补集映射扮演的是
`mini2048` 里 pads 对换的同一种角色：一个被放行的 fixed 口径对称，把
口径争议与模型良构性隔离开。2026-11-04 案卷工程裁决：忠实转录优先于
凑正控形式。

结构性观察（生成器每次运行都断言）：补集与 **D4 的每一个元素**可交换，
所以棋盘群与补集生成直积 **D4 × C2**（16 阶）——以 `g5_d4_x_c2` 入卷，
是本案卷最大的一群。几何对称与 Toggle 代数对称在此相互独立且乘积仍是对
称；模型的全部自同构清单更大，任何群文件都不冒充它。

生成器还断言：只翻上排的镜像（结构上像镜像、却不是棋盘对称）**没有任何**
按钮改名可救——假控读数预先登记，只是不为它单花一个群文件（拒答一侧由
g2 覆盖）。

## 判决（live，2026-11-04）

三方庭审（`python -X utf8 -m symmetry_court arbitrate`，判决书
`verdicts/lightsout3.verdict.json`；判语汇总：4 × `semantics_duality`、
1 × `agree`；口径内配对全部一致）：

| 群 | 声明 | 阶 | 引擎判决（声明口径） | 读数 | 轨道（压缩） |
|---|---|---|---|---|---|
| `g1_rot90_map` | explicit，逐元素 action_maps | 4 | **pass**（exit 0，worst_tv 0.0，homomorphism full） | 旋转 + 按钮改名是真对称 | 140（3.657×） |
| `g2_rot90_nomap` | fixed（按钮钉死） | 4 | reject（exit 1，worst_tv 1.0） | 朴素主张确实为假——3/4 元素不达标 | 140（3.657×） |
| `g3_complement` | fixed，正控 | 2 | **pass**（exit 0，worst_tv 0.0） | 补集与每次按键可交换 | 256（2.000×） |
| `g4_d4_full` | explicit，逐元素 action_maps | 8 | **pass**（exit 0，worst_tv 0.0，homomorphism full） | 主正控：完整 D4 放行 | 102（5.020×） |
| `g5_d4_x_c2` | explicit，逐元素 action_maps | 16 | **pass**（exit 0，worst_tv 0.0，homomorphism full） | D4 × C2 放行——几何 ⊗ Toggle 代数 | 51（10.039×） |

引擎 live 收据（`python -X utf8 -m wuxing_gua check`，cwd=`vendored/`，
explicit 群不加 `--strict`；`receipts/check.<群>.json`，两个 fixed 声明群
另有 `--strict` 双证）与生成器自己的轨道计数完全一致：140 / 256 / 102 / 51。

三列读法：本模型 9 动作 = 9 bit，法庭盖章的 relabel 框架解析为 bitstring
判官——它从状态置换自身推导动作改名（按钮即位位），该推导恰好重合于被
forced 的逐元素按钮映射，所以 relabel 列与 explicit 收据同判（对比
`mini2048`：4 动作 < 8 bit 时同一框架是结构性失配）。fixed 列钉死按钮，
拒绝所有改按钮名的群（g1/g2/g4/g5）——起决定作用的是口径，不是置换。
networkx 列如实镜像这一分裂（D4 群结构 yes / 带标签 no；补集两者皆 yes）。
512 态超出陪审团自同构枚举的规模护栏（跳过并如实记录）；O(E) 直接边集
检查是主判定。

## 文件

- `make_lightsout3.py` —— 确定性生成器；`--check` 重跑对称自证（9! 穷举
  映射推导、同态律、补集可交换性、秩 9 无填充态证明）并验证全部 7 个文件
  字节一致。
- `model.json`、`expected.json`、`groups/g1…g5.json` —— 案卷本体。
- `receipts/check.<群>.json` —— 引擎 live 收据（声明口径），每群一份；
  `receipts/check.g2_rot90_nomap.strict.json` 与
  `receipts/check.g3_complement.strict.json` —— 两个 fixed 声明群的
  `--strict` 双证。
- 法庭判决书：`verdicts/lightsout3.verdict.json`（三方庭审）。

# 案卷 `sliding2x3` —— 滑块谜题滑动机制，2×3 确定性变体

引擎 **explicit** 动作口径的第三份案卷（状态置换 + 逐元素声明的方向改名），
也是本法庭第三个非平凡真对称正控：完整的 4 元素矩形对称群 **V4 = C2 × C2**
按逐元素 action_maps 放行——案卷上第三种群结构，不同于 `mini2048` 与
`lightsout3` 的 D4（8 阶）及 `lightsout3` 的 D4 × C2（16 阶）：2×3 棋盘是
非正方形矩形，不存在 90° 旋转（生成器穷举 720 个格子双射对邻接图逐一机器
验证）。本案同时把 **pads 正控**带回 explicit 口径案卷：本转录含 304 个真
实填充态（`lightsout3` 一个都没有——它的偏离注记如实记录了该缺口；
`mini2048` 本就同时具有 explicit 口径与真实填充态及其 pads 正控，本案在 V4
群结构上再次配齐这一对）。

重新生成一切：
`python -X utf8 cases/sliding2x3/make_sliding2x3.py --check`（字节一致 +
穷举对称自证，退出码 0）。

## 模型

滑块谜题家族（编号 n-puzzle 成员——15 puzzle / 8 puzzle；Klotski 华容道是
滑块类同源；规则公开）的确定性滑动核心。每条生成规则都在
`model.json → meta.rules_with_citations` 引其原始出处；两条规则来源：

- Wikipedia，["15 puzzle"](https://en.wikipedia.org/wiki/15_puzzle)，导语：
  *"Tiles in the same row or column of the open position can be moved by
  sliding them horizontally or vertically, respectively."*（与空位同行或同
  列的块可以通过水平或垂直滑动来移动）；*"The goal of the puzzle is to
  place the tiles in numerical order (from left to right, top to bottom)."*
  （谜题目标是将数字块按从左到右、从上到下的顺序排列）——可解性节：
  *"Johnson & Story (1879) used a parity argument to show that half of the
  starting positions for the n puzzle are impossible to resolve"*（一半起始
  局面无论走多少步都无解）；*"on boards of size m × n, where m and n are
  both larger than or equal to 2, all even permutations are solvable"*（在
  m、n 均 ≥ 2 的 m×n 棋盘上所有偶排列均可解）。
- Wikipedia，["Sliding puzzle"](https://en.wikipedia.org/wiki/Sliding_puzzle)，
  导语：*"a combination puzzle that challenges a player to slide (frequently
  flat) pieces along certain routes (usually on a board) to establish a
  certain end-configuration"*；*"a sliding block puzzle prohibits lifting any
  pieces off the board"*（滑块谜题禁止把任何块拿出棋盘）——并将 Klotski 列
  入滑块谜题的例子。

- 1024 状态 = 2^10。5 个数字块 + 1 个空位的 6! = 720 个排列是真态（状态 =
  排列的字典序秩；格子 0..5 行主序，值 0 = 空位）；秩 720..1023 是未使用的
  编码空间 = **304 个填充态**（全动作自环、奖励 0——与
  `tcp`/`dhcp`/`imap`/`mini2048` 同一填充惯例）。滑动只重排列块，重排列仍
  是 (0..5) 的排列，所以真态只达真态（生成器每次运行断言）。
- 4 动作 = 滑动方向，编号 0=up、1=down、2=left、3=right。方向名指**滑动的
  块**的运动（一块朝该方向滑入相邻空位），所以空位朝相反方向移动一步——
  记录在 `meta.action_names` 与规则 R1（原始资料不给动作编号，编号是本转录
  自己的约定）。边清点（可从 `meta.edge_rule_tags` 机数）：1680 条滑动边
  （S）、1200 条无块可滑方向的空转自环（I——该方向没有块可滑，什么都不变，
  与 `mini2048` 的不可用方向自环同一惯例）、1216 条填充自环（P = 304 × 4）。
- 奖励全零属**设计**：谜题无计分（规则 R4）；胜利条件——数字块按序、空位
  在末：排列 (1,2,3,4,5,0) = 状态 153——作为目标性质记录在
  `meta.win_condition`，不是逐边奖励（与 `tcp`/`dhcp`/`imap`/`lightsout3`
  同一全零惯例）。裁决因此完全落在转移层。
- 奇偶性记录、**不修复**（规则 R5）：滑动把 720 个真态分成两个各含 360 态
  的不变类（Johnson & Story 1879）；两个类都是本模型的真态，从目标态出发
  的 BFS 恰达 360 态（生成器每次运行断言）。类分裂是状态空间的性质，不编
  码为不可达填充。
- 变体边界（规则 R6）：2×3 棋盘——n-puzzle 的正典是 4×4 十五谜题（"15
  square tiles numbered 1 to 15 in a frame that is 4 tile positions high
  and 4 tile positions wide"）；8 puzzle 在 3×3 上玩同一规则（"8 tiles in
  a 3×3 frame"）；m, n ≥ 2 的 m×n 家族由 Johnson & Story 定理覆盖；初始打
  乱随机性不收录（规则 R7）。

## 棋盘对称与 explicit 口径

2×3 棋盘的对称群是 Klein 四元群 **V4 = C2 × C2**（4 阶）：恒等、左右镜像
（`hflip`）、上下镜像（`vflip`）、180° 旋转（`rot180`）。真棋盘对称带着格
子一起改方向名：棋盘左右镜像后，"一块向左滑"变成"一块向右滑"。对每个群
元素 π，方向改名 ρ(π) 是**被迫的**（forced），且 π ↦ ρ(π) 是群同态。
`make_sliding2x3.py` 对每个 V4 元素在**全部 4! = 24 个方向排列**上穷举搜索
（每元素恰一个有效映射——每次运行断言），并在全部 16 个有序对上断言同态
律。已验证的表（方向编号 0=up、1=down、2=left、3=right）：

| 元素 | 内容映射（格子） | 被迫的方向映射（0..3） |
|---|---|---|
| id | [0,1,2,3,4,5] | [0,1,2,3] |
| hflip | [2,1,0,5,4,3] | [0,1,3,2]（left ↔ right） |
| vflip | [3,4,5,0,1,2] | [1,0,2,3]（up ↔ down） |
| rot180 | [5,4,3,2,1,0] | [1,0,3,2]（up ↔ down 且 left ↔ right） |

生成器还断言：2×3 棋盘的完整几何对称群**恰为 V4**——穷举全部 720 个格子
双射，恰有 4 个保持邻接图（非正方形矩形不存在 90° 旋转）；两个非棋盘对称
的假变换（循环列移位、顶行左交换）**不承认任何**方向改名——假控读数预登
记，不花群文件（g2 覆盖案卷的拒答侧）。

## pads 正控与如实的定位

状态编码需要 2^10 = 1024 个槽位装 720 个真排列，304 个未用秩是填充态（全
动作自环、奖励 0）。其中两个（状态 720 与 1023）行为形状相同——全动作单个
自环、奖励 0——所以它们的对换是钉死方向口径下的真对称，立案为 `g3_pads`
（fixed，预期放行）。

案卷工程期间如实记录定位（2026-11-04）：pads 正控在 `lightsout3`（全无填充
态——翻转矩阵秩 9，其偏离注记记录了该缺口，裁决：忠实转录优先于凑正控形
式）之后在本案卷回归。`mini2048` 本就将 explicit 口径与真实填充态及 pads
正控（其 `g6`）配对；本案在第三种群结构（V4）上再次配对。V4 元素对填充区
逐点不动——未使用的秩不是棋盘排布（记录在 `meta.transcription_notes`）——
所以每个全状态轨道数 = 真态轨道数 + 304 个填充单点。

## 判词（live，2026-11-04）

三方庭审（`python -X utf8 -m symmetry_court arbitrate`，回执
`verdicts/sliding2x3.verdict.json`；判语汇总：4 × `disagree`——与
`mini2048` 同一诊断分裂：法庭盖章的 relabel 框架解析为 bitstring 判据，与
只看结构列相左；fixed 列配对全部一致）：

| 群 | 声明 | 阶 | 引擎判词（声明口径） | 读法 | 轨道（压缩） |
|---|---|---|---|---|---|
| `g1_hflip_map` | explicit，逐元素 action_maps | 2 | **pass**（exit 0，worst_tv 0.0，同态 full） | hflip + 改名方向是真对称 | 664（1.542×） |
| `g2_hflip_nomap` | fixed（方向钉死） | 2 | reject（exit 1，worst_tv 1.0） | 朴素主张确实为假 | 664（1.542×） |
| `g3_pads` | fixed，正控 | 2 | **pass**（exit 0，worst_tv 0.0） | 两个填充行不引用任何方向 | 1023（1.001×） |
| `g4_v4_full` | explicit，逐元素 action_maps | 4 | **pass**（exit 0，worst_tv 0.0，同态 full） | 主正控：全 V4 放行 | 484（2.116×） |

Live 引擎收据（自 `vendored/` 跑 `python -X utf8 -m wuxing_gua check`，
explicit 群不带 `--strict`；`receipts/check.<group>.json`，两个 fixed 群另
有 `--strict` 双份）与生成器自己的轨道数完全一致：664 / 1023 / 484。

三列读法：在 4 动作/10 位的本模型上，法庭盖章的 relabel 框架解析为
bitstring 判据（动作当翻位读）——与方向键系统结构性错位，所以 relabel 列
对四群一律拒答，录为诊断列（对比 `lightsout3`：9 动作 = 9 位时 bitstring
推导恰与逐元素按钮映射重合；与 `mini2048` 同形）。fixed 列钉死方向，拒绝
所有改名方向群（g1/g2/g4）、放行 pads 对换（g3）——起决定作用的是口径，
不是置换。networkx 两列镜像分裂（镜像群结构是/标签否；pads 对换双双是）。
1024 态超出陪审团自同构枚举的规模护栏（跳过并如实记录）；O(E) 直接边集检
查是主判定。逐格对账在钉死口径下为 g2 数出 1440 个被改写的 (状态 × 事件)
行为格（`verdicts/comparison.sliding2x3.json`，`broken_real_cells_fixed`）
——朴素臂会放行它，闸门拦下。

## 文件

- `make_sliding2x3.py` —— 确定性生成器；`--check` 重跑对称自证（穷举 4!
  映射推导、同态律、完整几何群 = V4 证明、假控、pads/奇偶检查）并验证全部
  6 个文件字节一致。
- `model.json`、`expected.json`、`groups/g1…g4.json` —— 案卷本体。
- `receipts/check.<group>.json` —— live 引擎收据（声明口径），每群一份；
  `receipts/check.g2_hflip_nomap.strict.json` 与
  `receipts/check.g3_pads.strict.json` —— 两个 fixed 群的 `--strict` 双份。
- 法庭回执：`verdicts/sliding2x3.verdict.json`（三方庭审）。

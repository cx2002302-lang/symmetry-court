# 案卷 `hanoi3` —— 汉诺塔移动机制，3 盘确定性变体

引擎 **explicit** 动作口径的第四份案卷（状态置换 + 逐元素声明的动作改名），
也是本法庭第四个非平凡真对称正控：完整的柱重标群 **S3**（6 阶）按逐元素
action_maps 放行——案卷上第四种群结构，不同于 `mini2048` 与 `lightsout3`
的 D4（8 阶）、`lightsout3` 的 D4 × C2（16 阶）及 `sliding2x3` 的 V4（4
阶），且是第一个非交换群。本案同时是案卷中**第一个『动作 = 有序对』语义
的入口**：动作不是有名字的方向或按钮，而是有序柱对 (X, Y)——"取 X 柱顶
盘放到 Y 柱"——所以柱重标把动作按有序对 (X, Y) ↦ (πX, πY) 一起改名。
pads 正控在本案卷继续在列：本转录含 5 个真实填充态（`lightsout3` 一个都
没有；`mini2048` 与 `sliding2x3` 本就同时配齐 explicit 口径与 pads 正控）。

重新生成一切：
`python -X utf8 cases/hanoi3/make_hanoi3.py --check`（字节一致 + 穷举对称
自证，退出码 0）。

## 模型

汉诺塔（规则公开）的确定性移动核心。每条生成规则都在
`model.json → meta.rules_with_citations` 引其原始出处；规则来源：

- Wikipedia，["Tower of Hanoi"](https://en.wikipedia.org/wiki/Tower_of_Hanoi)，
  导语：*"a mathematical game or puzzle consisting of three rods and a
  number of disks of various diameters, which can slide onto any rod"*（由
  三根柱和若干直径不同的圆盘组成，圆盘可滑套到任一柱上）；规则：*"Only
  one disk may be moved at a time."*（每次只能移动一个盘）、*"Each move
  consists of taking the upper disk from one of the stacks and placing it
  on top of another stack or on an empty rod."*（每次移动 = 从某叠顶端取盘
  放到另一叠顶或空柱上）、*"No disk may be placed on top of a disk that is
  smaller than it."*（大盘不得压小盘）；目标：*"The objective of the puzzle
  is to move the entire stack to one of the other rods"*（把整叠移到另一
  柱）；最少步数：*"With three disks, the puzzle can be solved in seven
  moves. The minimum number of moves required to solve a Tower of Hanoi
  puzzle is 2ⁿ − 1"*（三盘七步，最少步数 2ⁿ−1）；图节：*"For a puzzle with
  n disks, there are 3ⁿ nodes in the graph"*（n 盘图有 3ⁿ 个节点）及
  *"every node has three edges to other nodes, except the three corner
  nodes, which have two"*（每点三边，唯三个角点两边）；对称性：*"the
  problem is symmetric for permutations of the names of the pegs (symmetric
  group S3)"*（问题对柱名的置换对称，即对称群 S3）。

- 32 态 = 2⁵。3³ = 27 个盘到柱的指派是真态（state = 三进制数 p0 + 3·p1 +
  9·p2：盘 0/1/2 所在柱号，盘 0 = 最小盘 = 最低位三进制位；柱 A=0、B=1、
  C=2）；秩 27..31 是未用编码空间 = **5 个填充态**（每个动作自环、奖励 0
  ——与 `tcp`/`dhcp`/`imap`/`mini2048`/`sliding2x3` 同一填充约定）。移动
  只是把盘在柱间重排，所以真态只达真态（生成器逐次断言）。
- 6 个动作 = 六个**有序柱对**，索引 0=`A->B`、1=`A->C`、2=`B->A`、3=`B->C`、
  4=`C->A`、5=`C->B`（原谜题没有编号；索引是本转录自己的约定，记录在
  `meta.action_names`）。有序对 (X, Y) 合法当且仅当 X 柱非空且 Y 柱为空或
  Y 柱顶盘更大（规则 R1–R2）；不可用的对记为无操作自环、奖励 0（规则 R3
  ——与 `mini2048` 的不可用方向自环同一约定）。边普查（可从
  `meta.edge_rule_tags` 机器数出）：78 条合法移动边（M）、84 条不可用对
  自环（I）、30 条填充自环（P = 5 × 6）。
- 对源文图描述的移动普查（每次运行机器断言）：每个真态恰有 **3** 个合法
  有序对，唯三个角态（全盘同柱：态 0、13、26）恰有 **2** 个——即
  Wikipedia 的 *"every node has three edges to other nodes, except the
  three corner nodes, which have two."*
- 连通性与最优性（每次运行机器断言）：从目标态 BFS 可达全部 27 个真态；
  从标准起点（全盘在 A 柱，态 0）到目标（全盘在 C 柱，态 26）的 BFS 距离
  恰为 **7 = 2³ − 1**（*"With three disks, the puzzle can be solved in
  seven moves"*）。
- 奖励全零**属游戏设计**：原谜题无计分（规则 R4）；完成条件——整叠在 C
  柱（态 26）——作为目标性质记录在 `meta.win_condition`，不是逐边奖励
  （与 `tcp`/`dhcp`/`imap`/`lightsout3`/`sliding2x3` 同一全零约定）。裁决
  因此完全在转移层进行。
- 变体边界（规则 R6）：3 盘实例——原谜题是"若干个盘"的参数化谜题，玩具
  版常见 7 到 9 盘；所引规则句除 7 步最小值外均与盘数无关，而 7 正是 2ⁿ−1
  律在 n = 3 的取值。

## 柱对称与 explicit 口径

柱名除了自身恒等没有别的内容，所以三根柱的任何重标都精确保持移动机制：
柱重标群就是全对称群 **S3**（6 阶：恒等、A↔B / A↔C / B↔C 三个对换、
A→B→C→A / A→C→B→A 两个轮换）。真柱对称把有序对动作名跟着柱一起改：交换
柱 A 与 B，把移动 `A->B` 变成移动 `B->A`。对每个群元素 π，动作改名 ρ(π)
是**被迫的**——ρ(π) 把每个有序对 (X, Y) 映为 (πX, πY)——且 π ↦ ρ(π) 满
足群同态律。`make_hanoi3.py` 对 S3 的每个元素**穷举全部 6! = 720 个有序
对排列**推导 ρ（每元素恰一个合法映射——每次运行断言），并在 S3 全部
**36 个有序对**上断言同态律（另加每个 2 阶子群的 4 个）。验证表（动作
索引如上）：

| 元素 | 柱映射 π | 被迫的有序对映射 ρ (0..5) |
|---|---|---|
| id | (0,1,2) | [0,1,2,3,4,5] |
| swap_ab | (1,0,2) | [2,3,0,1,5,4]（A→B ↔ B→A，A→C ↔ B→C，C→A ↔ C→B） |
| swap_ac | (2,1,0) | [5,4,3,2,1,0]（每对随 A↔C 互换反转） |
| swap_bc | (0,2,1) | [1,0,4,5,2,3]（A→B ↔ A→C，B→A ↔ C→A，B→C ↔ C→B） |
| rot_abc | (1,2,0) | [3,2,5,4,0,1]（每对的两柱沿 A→B→C→A 前进） |
| rot_acb | (2,0,1) | [4,5,1,0,3,2]（每对的两柱沿 A→C→B→A 前进） |

生成器另外断言：两个不是柱重标的假状态映射——把盘 0 与盘 1 的柱号互换、
把盘 0→1→2→0 轮换——**任何**动作改名都不成立（盘的大小属于盘的恒等而非
位置）：假控读数预注册，不花群文件（g2 已覆盖案卷的拒答一侧）。六个动作
在真态上两两可分辨（断言在案），这正是每个 ρ 被唯一迫出的原因。

## pads 正控

状态编码需要 2⁵ = 32 个槽位放 27 个真排列，5 个未用秩是填充态（每个动作
自环、奖励 0）。其中两个（态 27 与 31）行为形状相同——每个动作都是单自
环、奖励 0——所以对换是钉死口径下的真对称，立为 `g4_pads`（fixed，预期
放行）。定位：pads 正控在 `mini2048` 的 g6、`sliding2x3` 的 g3 之后于本
案卷继续（`lightsout3` 无填充态；其偏离注记是该缺口的如实记录）。

## 判决（live，2026-11-07）

三方庭审（`python -X utf8 -m symmetry_court arbitrate`，收据
`verdicts/hanoi3.verdict.json`；判语：3 × `semantics_duality` +
1 × `agree`；fixed 列配对全部一致）：

| 群 | 声明 | 阶 | 引擎判决（声明口径） | 读数 | 轨道（压缩） |
|---|---|---|---|---|---|
| `g1_swap_ab_map` | explicit，逐元素 action_maps | 2 | **放行**（exit 0，worst_tv 0.0，同态律 full） | swap_ab + 改名有序对是真对称 | 19（1.684×） |
| `g2_swap_nomap` | fixed（有序对钉死） | 2 | 拒答（exit 1，worst_tv 1.0） | 朴素主张在该口径下确实为假 | 19（1.684×） |
| `g4_pads` | fixed，正控 | 2 | **放行**（exit 0，worst_tv 0.0） | 两个填充行不引用任何柱 | 31（1.032×） |
| `g3_s3_full` | explicit，逐元素 action_maps | 6 | **放行**（exit 0，worst_tv 0.0，同态律 full） | 主正控：全 S3 放行 | 10（3.200×） |

引擎 live 收据（自 `vendored/` 跑 `python -X utf8 -m wuxing_gua check`，
explicit 群不带 `--strict`；`receipts/check.<群>.json`，两个 fixed 声明群
另有 `--strict` 双份）与生成器自己的轨道计数完全一致：19 / 31 / 10
（Burnside 交叉验证：g1 真态轨道 (27+1)/2 = 14——A↔B 对换只固定全盘在未
换柱 C 上的那一个态——另加 5 个填充单点；g3 真态轨道 (27+3)/6 = 5，大小
3,6,6,6,6，另加 5 个填充单点）。

三列读法：在这个 6 动作/5 比特模型上，法庭盖章的 relabel 框架解析为
**generalized** 判官（六个动作无法按 5 比特状态的位翻转索引，位串读法根
本无从谈起），它从状态置换本身推导动作改名——该推导与被迫的逐元素有序
对映射重合，所以 relabel 列**与 explicit 收据同步放行**（对照
`mini2048`/`sliding2x3`：同一框架解析为位串判官、作为诊断列拒答；对照
`lightsout3`：9 动作 = 9 比特使位串推导与逐元素按钮映射重合）。fixed 列
钉死有序对，拒答所有改名对群（g1/g2/g3）、放行填充对换（g4）——起决定
作用的是口径，不是置换。networkx 列与该分裂镜像（换柱群 structure yes /
labeled no；pads 对换两列皆 yes）；32 态下陪审团的自同构集交叉核验**在
法庭规模护栏内实际运行**，枚举出 **720 个结构自同构**（= 6 个真态 S3 重
标 × 5! 填充排列）对 **120 个带标签自同构**（= 5! 填充排列 × 真态恒等）
——对"带标签真态空间的自同构群恰为柱重标群 S3"的独立机器验证。逐格台账
给 g2 在钉死口径下数出 **122** 个被改写的 (状态 × 事件) 行为格
（`verdicts/comparison.hanoi3.json`，`broken_real_cells_fixed`）——朴素
结构臂放行它，闸门拒答（本案卷第 5 个有害朴素放行，继 TCP 孪生对与三个
键/方向钉死的旋转、镜像之后）。

## 文件

- `make_hanoi3.py` —— 确定性生成器；`--check` 重跑对称自证（穷举 6! 映射
  推导、36 有序对同态律、两个假盘映射对照、移动普查、填充/连通/最优性检
  查）并核验全部 6 个文件字节一致。
- `model.json`、`expected.json`、`groups/g1…g4.json` —— 案卷本体。
- `receipts/check.<群>.json` —— 引擎 live 收据（声明口径），每群一份；
  `receipts/check.g2_swap_nomap.strict.json` 与
  `receipts/check.g4_pads.strict.json` —— fixed 声明群的 `--strict` 双份。
- 法庭收据：`verdicts/hanoi3.verdict.json`（三方庭审）。

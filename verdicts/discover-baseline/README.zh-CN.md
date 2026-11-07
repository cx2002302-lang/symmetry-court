# discover 对账基线（草稿）

供案卷第四个 CLI 能力 `discover` 做对账用的机器可读预期事实。discover 运行后
写出 `verdicts/discover.<case>.json`；对账步骤将该输出与本目录的基线逐项核对。

基线是对账中**独立**的一方，来源只有三类：

- 五个并入案（`hadoop-mr-task`、`k8s-pod-lifecycle`、`raft-etcd`、
  `tls13-handshake`、`usb2-device-states`）取 **field-trial 盲测项目的
  sealed 真值**——sha256 钉在该项目的 `sealed/_W3_manifest.json` 里，生成器
  每次运行都重验；
- 全部十二案的**法庭收据**（`cases/<case>/expected.json` 的 fixed 行与
  networkx labeled 列）；
- 对模型（`cases/<case>/model.json`）的**直接机器检查**。

不读任何 discover 输出。文件里的每个数字，要么逐字来自文件内注明的来源，
要么由生成器（`tools/make_discover_baseline.py`）从这些来源机器推导。

## 诚实边界

`discover` 只在 **fixed 口径**（事件名钉死）下发现候选状态对称。动作改名类
对称（`explicit` / `relabel` 口径）仍由**案卷作者显式声明**——机器不猜
"哪种一样"，本基线也不把它们记作 discover 的目标。对真实案卷的预期：
pads（填充类）对称可自动发现；claim（假双生）不应被发现；真实的 fixed 口径
群（若有）应被发现。fixed 行 pass 的声明组必须**包含于**发现群；fixed 行
reject 的声明组**不得被完整包含**。

## 每份文件记录什么

`discover.<case>.expected.json`，每案一份：

- `sources`——每个数字的出处；
- `model_facts`——态/动作/边数与**均匀孤立自由类**：每个动作格恰为
  `[(1.0, self, 0.0)]`、且无来自他态的入边、无去往他态的出边的态。对该类
  的任意置换都是 fixed 口径自同构（`Sym(class) <= Aut`），且该类在每个
  自同构下不变，群阶在分割两侧相乘；
- `fixed_automorphism_expectation`——预期群阶（有 sealed 或机器证书时给
  精确值，否则给下界）、补集刚性证书、1-WL 细化预期、枚举上限
  （默认 2000）处的预期行为、预期状态轨道数；
- `declared_groups`——每个群文件诸元素的轮换式、逐元素对 fixed 判据的
  机器验证、收据的 fixed 行、收录预期；
- `reconciliation_checks`——对账步骤应跑的具名检查。

## 预期总表（中英两版数字一致）

| 案 | 态数 | 自由类 | `|Aut_fixed|` 精确 | 下界 | 触上限(2000) | 1-WL 离散 | 轨道数 |
|---|---|---|---|---|---|---|---|
| `tcp` | 16 | 5 | 120 | 120 | 否 | 否 | 12 |
| `dhcp` | 16 | 8 | 40320 | 40320 | 是 | 否 | 9 |
| `imap` | 8 | 4 | 24 | 24 | 否 | 否 | 5 |
| `mini2048` | 256 | 183（其中 8 个真态） | — | 183! | 是 | 否 | 补集刚性时 74 |
| `lightsout3` | 512 | 0 | 512（`C2^9`） | 512 | 否 | 否 | 1 |
| `sliding2x3` | 1024 | 304 | — | 304! | 是 | 否 | 补集刚性时 721 |
| `hanoi3` | 32 | 5 | — | 120 | 否 | 否 | 补集刚性时 28 |
| `raft-etcd` | 4 | 0 | 1 | 1 | 否 | 是 | 4 |
| `k8s-pod-lifecycle` | 8 | 3 | 6 | 6 | 否 | 否 | 6 |
| `hadoop-mr-task` | 8 | 1 | 1 | 1 | 否 | 是 | 8 |
| `tls13-handshake` | 32 | 15 | 1307674368000（= 15!） | 1307674368000 | 是 | 否 | 18 |
| `usb2-device-states` | 8 | 2 | 2 | 2 | 否 | 否 | 7 |

精确值的来源：五个并入案带 sealed 群阶；`tcp`、`dhcp`、`imap` 由自由类
加补集刚性证书钉死；`lightsout3` 由平移群证书钉死（见下）。其余三案
（`hanoi3`、`mini2048`、`sliding2x3`）只记自由类下界——其补集存在把一轮
签名打并列的 structure-only 影子，补集因子由 discover 的细化与枚举裁决。

## 三个值得点名的模型事实

- **`mini2048` 的自由类是 183，不是 175。** 八个*真态*在 fixed 口径下表现
  如填充态：空盘，以及七张仅有的合并都被该案数值上限禁止的死牌面。八态
  全部行均匀孤立、零入边（穷举机检）。这不翻转任何已记录裁决——它把
  "填充等价"的故事延伸进了真态，发现群应当反映这一点。
- **`lightsout3` 没有填充态，但 `|Aut_fixed| = 512`。** 全部 4608 格都是
  单条 `(1.0, s xor mask_a, 0.0)` 行，九个切换掩码在 GF(2) 上秩为 9，于是
  任何 fixed 自同构 `pi` 满足 `pi(s xor mask_a) = pi(s) xor mask_a`，自身
  必为平移——`Aut_fixed` 恰为平移群 `C2^9`，作用只有一个 512 态的轨道。
  512 个平移已穷举验证。声明的 `g3_complement`（全灯翻转）只是该群的一
  个元素；此处 WL 上界很松（全体态被平移打成并列），钉住群阶靠枚举而非
  细化。
- **`k8s-pod-lifecycle` 是"枚举+细化双轨"设计的论证。** sealed 真值自己的
  均匀行启发式报出 5 态类（`k_factorial` 120），但真自由类是 3（阶 6）：
  另外两个均匀行态是被入边锚定的真吸收态。只靠行启发式会过预测——这正
  是设计强制枚举与带标签颜色细化并用、而不是单用其一的原因。

## 再生成 / 校验

```
python -X utf8 tools/make_discover_baseline.py            # （重）写 12 份文件
python -X utf8 tools/make_discover_baseline.py --check    # 字节同一校验
```

`--check` 在十二份文件重生成字节相同时退出码 0，有漂移退出 1。
`--sealed-dir` 覆盖 field-trial 盲测项目 `sealed` 目录的位置（默认取本仓库
的同级目录）。生成器每次运行都重验 sealed 文件对该项目 sealed 清单的
sha256，不符即拒绝产出。

## 对账检查

每案的 discover 输出应满足：

1. **群阶**——发现阶（精确值，或上限触顶时的下界加 WL 上界）与
   `order_exact` / `order_lower_bound` 一致；
2. **收录**——fixed-pass 声明组包含于发现群；fixed-reject 声明组不被完整
   包含；
3. **轨道**——自由类构成单一轨道；群阶精确时轨道数与预期一致；
4. **离散性**——细化报告与 `wl_refinement_expected_discrete` 一致
   （`hadoop-mr-task` 与 `raft-etcd` 是仅有的两个离散案；
   `hadoop-mr-task` 的 sealed 真值即 |Aut| = 1 的锚点）；
5. **上限**——触顶标志与每案记录的预期一致。

## 状态

草稿，先于 discover CLI 落地写成。基线不含任何计时主张；其全部检查都是
对模型与群文件的直接验证。JSON 文件只以仓库相对路径引用来源。

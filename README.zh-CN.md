# 对称法庭 Symmetry Court

[![CI: court selftest](https://img.shields.io/badge/court-selftest_pass-brightgreen)](https://github.com/cx2002302-lang/symmetry-court#quick-start) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Engine: wuxing-gua@04cf0b6](https://img.shields.io/badge/engine-wuxing--gua%4004cf0b6-grey)](NOTICE)

**给状态机的对称性主张开庭。** 一条主张、三位裁判、两套写明的口径、一份人人可复跑的判决书。—— English: [README.md](README.md)

---

## 认识这对双胞胎

翻开 TCP 标准——RFC 9293 §3.3.2 Figure 5——看关闭过程的两大分支。靠近末尾有两个状态，`CLOSING` 和 `FIN-WAIT-2`，画出来几乎是一对双胞胎：各自一条进门、一条出门，两条出门都通向同一个下一站；而且把其中一条出门送出去的事件，恰好是把另一条送进门的事件。把图上的事件标签擦掉，交换这两个状态，整张图严丝合缝地叠回自己身上。

但把标签读回来。`FIN-WAIT-2` 的出门事件是 **对方挂断了电话**（`rcv FIN`）；`CLOSING` 的出门事件是 **对方确认了我们的挂断请求**（`rcv ACK of FIN`）。这是两条不同关闭路径上的两个不同时刻——内部状态怎么改名，都变不成同一个事件。

转折来了。我们拿这对状态的交换去问一个对称性判据引擎："这次交换保不保行为？"它答 **pass**。我们又拿同一个问题去问一个独立的图计算库——这次把事件标签按住不许动——它答 **不行，恒等是唯一的对称**。两个答案都对。因为它们答的是 **两个不同的问题**："事件名可以跟着状态一起改名吗"和"事件名必须钉在原地吗"。引擎的默认口径默认前者，规范文本要求后者——而在问题被写下来之前，工具和陪审团谁也没说自己答的是哪一问。

**这就是这个仓库存在的理由。** 对称法庭把一条关于状态机的对称性主张，交给三位裁判，在 **两套写明名字的口径** 下各跑一遍，每一列都落进判决书文件，然后明说三方一致还是分歧。裁判意见不合时——双胞胎案正是不合——分歧本身就是发现，公开记录，不做和稀泥处理。

旗舰案例的完整叙事在 [docs/twin-trial.md](docs/twin-trial.md)。

## 三方仲裁是什么

对每一案里的每条对称性主张（一个"被告群"），法庭跑三列：

| 列 | 谁 | 答什么 |
|---|---|---|
| `wuxing-gua@relabel` | 内嵌判据引擎，relabel 口径 | **事件名可以跟着状态一起改名**时，交换是否成立 |
| `wuxing-gua@fixed` | 同一引擎，fixed 口径（`--strict`） | **事件名必须钉在原地**时，交换是否成立 |
| `networkx@labeled` | 独立陪审团（networkx），标签固定 | 同一个图问题，由另一套独立代码算 |

另有一列透明备查：陪审团的"只看结构"答案（标签擦掉版），记录在案卷的 expected / verdict 文件里。

三位裁判刻意互相独立：引擎是字节级原样内嵌的零依赖包，陪审团是另一套基于 networkx 的独立实现。任何一边有 bug，都藏不住——只会表现为列间分歧。每份判决都带一句明确的 agree/disagree 判语；`selftest` 把每份判决逐字段对 expected 记录重放，判决书偏离回执时不可能静默过关。

要点不是某一列"赢"，而是每一列 **默认的口径都被写明了**——双胞胎案暴露的缺口，缺的正是这个。

## 五分钟快速上手

```bash
git clone https://github.com/cx2002302-lang/symmetry-court.git
cd symmetry-court

# 唯一要装的：陪审团的依赖（引擎本身零依赖）
python -X utf8 -m pip install networkx

python -X utf8 -m symmetry_court list        # 看案卷
python -X utf8 -m symmetry_court arbitrate   # 开庭——每案出一张判决表
python -X utf8 -m symmetry_court compare     # 闸门价值对比——朴素合并 vs 过闸，逐群损害台账，口径按群声明分派（v2 起；见 docs/闸门价值对比.html）
python -X utf8 -m symmetry_court selftest    # 全案重放对 expected（退出码 0 = 全绿）
```

（`python -X utf8` 是本项目在 Windows 上的固定写法；其他平台上 `python3 -X utf8` 行为一致。）

arbitrate 会在控制台打印判决表，并把完整庭审记录写进 `verdicts/<case>.verdict.json`。selftest 是门禁：退出码 `0` 表示仓里每份判决仍与 expected 记录逐字段一致。

compare 自 v2 起按各群声明分派口径：声明 `explicit` 的群原样跑（不加 `--strict`），声明 `fixed` 或无声明的群维持 `--strict`（2026-11-04 起声明口径含逐元素 `action_maps` 形态）。11 案 41 群台账中，闸门每次放行都零破坏（判据性质）。`mini2048` 案（2048 合并机制 2×2 变体，D4）是 explicit 口径的第一个真实系统案卷：其『该放』已由案卷生成器穷举断言（逐元素映射唯一 + 群同态律）；2026-11-03 发现的引擎单映射局限已于 2026-11-04 由上游修复（逐元素 `action_maps`，装载时校验同态律）并重 vendored，g1/g3/g4 按声明口径实跑放行。`lightsout3` 案（Lights Out 翻转机制 3×3 变体，D4——2026-11-04 入卷）是该口径的第二份真实系统案卷，也是本法庭第二个非平凡真对称正控：与 `mini2048` 同群、不同机理（Toggle 代数，而非合并滑动）。`sliding2x3` 案（滑块谜题滑动机制 2×3 变体，V4——2026-11-04 入卷）是该口径的第三份真实系统案卷，也是本法庭第三个非平凡真对称正控：第三种群结构（非正方形矩形上的 Klein 四元群，机器验证为完整几何群），且 pads 正控随 explicit 口径回归（304 个真实填充态，接在 `lightsout3` 无填充态案之后）。台账闸门放行现为 17、全程零破坏；四处真陷阱（TCP 孪生 6 格、三案方向/按钮钉死旋转与镜像 740 + 12288 + 1440 格）全部拦下（见 [docs/闸门价值对比.html](docs/闸门价值对比.html)、[cases/mini2048/README.zh-CN.md](cases/mini2048/README.zh-CN.md)、[cases/lightsout3/README.zh-CN.md](cases/lightsout3/README.zh-CN.md) 与 [cases/sliding2x3/README.zh-CN.md](cases/sliding2x3/README.zh-CN.md)）。

### 怎么读判决

每个被告群、每种口径一行：

- **exit code** —— 引擎约定：`0` 放行，`1` 拒答，`2` 样本不足（仅采样模式；本法庭用不到），`3` 输入或内部错误；
- **verdict** —— 在该列写明口径下的 pass / reject；
- **`worst_tv`** —— 本次检验量到的最大失配（改名前后行为的总变差）；
- **`judge`** —— 引擎实际用的是哪套内部判据，便于追溯；
- **agree/disagree** —— 法庭对"三列对这名被告说的是不是同一个故事"的一句话判语。

**pass 永远只表示**：*在写明的那套口径下，结构上可以互换*。它不等于"可以放心压缩"。口径要你自己挑，挑法见下一节。

## 案卷

案卷现有 11 宗案件：5 案收编自 field-trial 盲测项目（模型/群文件/生成器/README 字节级复制；判词已与 field-trial 的 sealed 真值逐案对账，15/15 群一致，见各案 `expected.json` 的 provenance），6 案为本仓转录（`tcp`、`dhcp`、`imap`、`mini2048`、`lightsout3`、`sliding2x3`）。回执：对 `cases/` 目录跑 `python -X utf8 -m symmetry_court list`。下表每个数字都有仓内指名的回执文件背书——没有一个数来自记忆。

| 案件 | 协议 | 出处 | 状态数 | 孪生对 | relabel | fixed | networkx（带标签） |
|---|---|---|---|---|---|---|---|
| `tcp` | TCP 连接状态机 | RFC 9293 §3.3.2 Figure 5 | 16 状态、20 条转移、12 种事件 | CLOSING ↔ FIN-WAIT-2 | pass（exit 0，worst_tv 0.0） | reject（exit 1，worst_tv 1.0） | 非对称——仅恒等（只看结构：是） |
| `dhcp` | DHCP 客户端状态机 | RFC 2131 §4.4 Figure 5 | 16 状态（8 协议态 + 8 补位）、18 条转移、15 种事件 | RENEWING ↔ REBINDING（转录裁定：不可互换） | reject（exit 1，worst_tv 1.0） | reject（exit 1，worst_tv 1.0） | 非对称（结构与带标签口径皆非） |
| `imap` | IMAP4rev1 连接状态机 | RFC 3501 §3 + §6（正文规范，无 drawn 图） | 8 状态（4 协议态 + 4 补位）、11 条转移、6 种事件 | AUTHENTICATED ↔ SELECTED（SELECT/CLOSE 双向环） | reject（exit 1，worst_tv 1.0） | reject（exit 1，worst_tv 1.0） | 非对称（结构与带标签口径皆非） |
| `raft-etcd` | etcd/raft 单节点角色状态机 | etcd-io/raft `raft.go` @ `c51f010c851e`（StateType，raft.go:49-56） | 4 状态（4 协议态 + 0 补位）、12 条跨态迁移、14 种事件 | Candidate ↔ PreCandidate | reject（exit 1，worst_tv 1.0） | reject（exit 1，worst_tv 1.0） | 非对称（结构与带标签口径皆非） |
| `hadoop-mr-task` | Hadoop MRv2 Task 状态机 | apache/hadoop trunk @ `e66f40daf3cc`（`TaskStateInternal.java`:19-23） | 8 状态（7 协议态 + 1 补位）、18 条跨态分支、9 种事件 | FAILED ↔ KILLED | reject（exit 1，worst_tv 0.75） | reject（exit 1，worst_tv 1.0） | 非对称（结构与带标签口径皆非） |
| `k8s-pod-lifecycle` | Kubernetes Pod 生命周期（PodPhase） | kubernetes.io 官方文档 Pod Lifecycle 页 | 8 状态（5 协议态 + 3 补位）、13 条跨态分支、7 种事件 | Succeeded ↔ Failed | reject（exit 1，worst_tv 1.0） | reject（exit 1，worst_tv 1.0） | 非对称（结构与带标签口径皆非） |
| `tls13-handshake` | TLS 1.3 握手状态机（client + server） | RFC 8446 Appendix A（§A.1/§A.2） | 32 状态（17 协议态 + 15 补位）、22 条跨态分支、18 种事件 | c_WAIT_CERT ↔ c_WAIT_CV | reject（exit 1，worst_tv 1.0） | reject（exit 1，worst_tv 1.0） | 非对称（结构与带标签口径皆非） |
| `usb2-device-states` | USB 2.0 设备可见状态机 | USB 2.0 规范 §9.1（Figure 9-1 / Table 9-1） | 8 状态（6 协议态 + 2 补位）、14 条跨态分支、8 种事件 | Default ↔ Address | reject（exit 1，worst_tv 1.0） | reject（exit 1，worst_tv 1.0） | 非对称（结构与带标签口径皆非） |
| `mini2048` | 2048 合并机制（2×2 确定性变体） | gabrielecirulli/2048 `js/game_manager.js`（`move()` L130-191，方向编号 L131），Wikipedia Gameplay 互证 | 256 状态（81 真态 + 175 补位）、4 个方向键、计分奖励 | rot90+改名方向键（explicit）对 同一旋转+键钉死（fixed）——起决定作用的是口径，不是置换 | reject（exit 1，worst_tv 1.0；bitstring 诊断列——见注） | reject（exit 1，worst_tv 1.0） | explicit 口径逐元素映射自 2026-11-04 起放行 rot90/翻转/D4（70/136/55 轨道）；键钉死口径仍非对称（只看结构：是） |
| `lightsout3` | Lights Out 翻转机制（3×3 确定性变体） | Wikipedia "Lights Out (game)"（Gameplay/Strategy 原句）+ Jaap's Puzzle Page（Wikipedia 引用的规则页）；3×3 记为变体边界（Tiger 原版 5×5） | 512 状态（全真态、无补位）、9 个按钮、奖励全零（原版无计分） | rot90+改名按钮（explicit）对 同一旋转+按钮钉死（fixed）——与 `mini2048` 同群、不同机理（Toggle 代数） | pass（exit 0，worst_tv 0.0；bitstring 判官从置换推导的改名与逐元素按钮映射重合——见注） | reject（exit 1，worst_tv 1.0） | explicit 口径逐元素映射放行 rot90/D4/D4×C2（140/102/51 轨道），fixed 补集正控放行（256 轨道）；按钮钉死旋转仍非对称（只看结构：是） |
| `sliding2x3` | 滑块谜题滑动机制（2×3 确定性变体，n-puzzle 家族；Klotski 华容道为滑块类同源） | Wikipedia "15 puzzle"（导语 + 可解性原句）+ Wikipedia "Sliding puzzle"（导语原句）；2×3 记为变体边界（正典 n-puzzle 为 4×4；8 puzzle 为 3×3） | 1024 状态（720 真排列 + 304 补位）、4 个滑动方向、奖励全零（谜题无计分） | hflip+改名方向（explicit）对 同一镜像+方向钉死（fixed）——第三种群结构：非正方形矩形上的 V4（不存在 90° 旋转） | reject（exit 1，worst_tv 1.0；bitstring 诊断列——见注） | reject（exit 1，worst_tv 1.0） | explicit 口径逐元素映射放行 hflip/V4（664/484 轨道），fixed pads 正控放行（1023 轨道）；方向钉死镜像仍非对称（只看结构：是） |

`tcp` 行的注：状态数含 5 个补位哑态（引擎位串约定所需，16 态中 11 个为协议态）；案卷里其余两名被告——一个无聊换位、一个荒谬换位——在两套口径下都被拒（`cases/tcp/expected.json` 中 4/4 行 reject），这是"判官不是橡皮图章"在记录里的样子。底本转录里的一条边在逐边复核后被删除（`SYN-SENT` 上的 `CLOSE`：Figure 5 没有画这条箭头，且 §3.10.4 写明"删除 TCB"）；更正记录在模型元数据的转录注记里。`dhcp` 行的判决是数据说了算，不是感觉：两个续租状态共用同一完成标签 `DHCPACK/Record lease`，但连 relabel 口径都拒绝这次换位——因为 `REBINDING` 没有回到 `RENEWING` 的边。`imap` 行转录自 RFC 3501 的正文（其 §3 无图）；每条边都引用写明它的原句。TCP 没有回报概念，该案奖励层按设计全零，全部结论来自转移层（`dhcp`、`imap` 同）。

`raft-etcd`…`usb2-device-states` 五行收编自 field-trial 盲测项目（字节级复制；本仓回执 = `cases/<案>/expected.json` + `verdicts/<案>.verdict.json`；networkx 两列与 field-trial 的 sealed 真值逐案对账一致——15/15 群，sealed 文件与其 `_W3_manifest.json` 的 sha256 可回核）。`k8s-pod-lifecycle`、`tls13-handshake`、`usb2-device-states` 三案各含一个 pads 正对照（填充态对换：两口径 pass、networkx 结构/带标签皆同，`expected.json` 中 TRUE）；`hadoop-mr-task` 的第三群是对照群（RUNNING ↔ KILL_WAIT，拒）；`raft-etcd` 的第三群是 relabel 声明对照（同一置换、relabel 读法，仍拒）。`hadoop-mr-task` 行 relabel 列 worst_tv=0.75：FAILED/KILLED 对换只破坏部分真实格——数据实录，非笔误。`tls13-handshake` 随案 README 称跨态分支 20（按格计：client 9 + server 11）；按结果分支计（与本表其余各行同口径）为 22（client 10 + server 12，`model.json` 实算可复核）——本表取 22。

`mini2048` 行的注：引擎 **explicit** 口径（逐动作声明映射——棋盘对称会连格带方向键一起改名）的第一个真实系统样本，也是本仓库第一个被复现的引擎发现现场（2026-11-03）：vendored 判官的 explicit 层当时把**一个**声明的 `action_map` 用于闭包群的**每一个**元素（**含恒等元**），于是在任何"动作两两可分辨"的模型上，恒等元强制映射为恒等，任何非平凡的"动作改名"对称都不可能被放行。本案的 rot90/翻转/D4 群在逐元素映射语义下是真对称（由案卷生成器穷举推导并机器断言）。**2026-11-04 已修复兑现**：上游逐元素 `action_maps` 修复（装载时校验同态律）重 vendored，群文件改声明逐元素映射，explicit 口径收据（`cases/mini2048/receipts/`，引擎不带 `--strict`）实跑 **pass**、`homomorphism_checked: full`——g1/g3/g4 以 70/136/55 轨道放行（压缩 3.657×/1.882×/4.655×）；g2/g5 维持拒答、g6 维持放行，恒等映射对照在 legacy 单映射下照旧拒答（deprecated，行为不变）。本表 relabel/fixed 两列未翻案。同一模型上填充态对换照常放行（exit 0）；本表 relabel 列是法庭盖章的 relabel 框架，在 4 动作/8 位模型上解析为位串判据（动作当翻位读）——与方向键系统结构性错位，如实录为诊断列。完整诊断（含已验证的 8 元素映射表）：[cases/mini2048/README.zh-CN.md](cases/mini2048/README.zh-CN.md)。

`lightsout3` 行的注（2026-11-04 入卷）：Lights Out 谜题（Tiger Electronics 掌机，1995 年公开发售）确定性翻转核心的 3×3 转录——每条生成规则都在 `model.json → meta.rules_with_citations` 引 Wikipedia Gameplay/Strategy 原句与 Jaap's Puzzle Page；3×3 棋盘本身记为变体边界（原版 5×5；3×3 脉络经 Merlin 再版 Magic Square 与 Lights Out Cube 的 3×3 面）。512 个状态全是真态——3×3 翻转矩阵在 GF(2) 上秩 9（生成器断言），无补位态、零自环、任意两态整行互异。奖励全零属设计（原版无计分）；胜利条件（9 灯全灭）作为终局性质记录在 `meta.win_condition`，裁决完全落在转移层。被告群：g1（rot90 + 逐元素按钮映射，explicit）与 g4（全 D4，本法庭第二个非平凡真对称正控）按声明口径放行（140 / 102 轨道，3.657× / 5.020×）；g5——直积 D4 × C2（16 元素，51 轨道，10.039×）——因全盘取反与 D4 每个元素可交换（生成器逐元素断言）而放行。g2（同一旋转、按钮钉死）被拒：朴素臂会放行它，逐格对账在按钮钉死口径下数出 12288 个被改写的 (状态 × 事件) 行为格。g3——全盘取反，fixed——是平凡正控；偏离如实记录：本案没有填充态可换，补集映射扮演 `mini2048` 里 pads 对换的同一种角色（2026-11-04 案卷工程裁决：忠实转录优先于凑正控形式）。本表 relabel 列是法庭盖章的 relabel 框架，解析为 bitstring 判官——在 9 动作 = 9 位的本模型上，它从状态置换自身推导动作改名，该推导恰好重合于被 forced 的逐元素按钮映射，所以这一列与 explicit 收据同判（对比 `mini2048`：4 动作 < 8 位时同一框架是结构性错位）。512 态超出陪审团自同构枚举的规模护栏（跳过并如实记录）；O(E) 直接边集检查是主判定。案卷全文（含已验证的 8 元素映射表）：[cases/lightsout3/README.zh-CN.md](cases/lightsout3/README.zh-CN.md)。

`sliding2x3` 行的注（2026-11-04 入卷）：滑块谜题家族（编号 n-puzzle 成员——15 puzzle / 8 puzzle；Klotski 华容道为滑块类同源，列于滑块谜题例子中但本案不转录：其不等尺寸多格块需要另一种状态空间）确定性滑动核心的 2×3 转录（5 个数字块 + 1 空位）——每条生成规则都在 `model.json → meta.rules_with_citations` 引 Wikipedia 15-puzzle 导语/可解性原句与 Sliding-puzzle 导语；2×3 棋盘记为变体边界（正典 n-puzzle 为 4×4；"the 8 puzzle, which has 8 tiles in a 3×3 frame"）。1024 状态 = 2^10：6! = 720 个排列是真态（状态 = 排列的字典序秩）；秩 720..1023 是未使用编码空间——**304 个填充态**（全动作自环、奖励 0），真态与真实填充并存，pads 正控因此成立。奖励全零属设计（谜题无计分）；胜利条件（数字块按序、空位在末——排列 (1,2,3,4,5,0)，状态 153）作为目标性质记录在 `meta.win_condition`。Johnson & Story 奇偶分裂（一半起始局面无解）记录、不修复：两个类都是真态，从目标态出发的 BFS 恰达 360（生成器断言）。被告群：g1（hflip + 逐元素方向映射，explicit）与 g4（全 V4 = C2 × C2，本法庭第三个非平凡真对称正控）按声明口径放行（664 / 484 轨道，1.542× / 2.116×）。V4 经机器验证为棋盘的**完整**几何群（穷举 720 个格子双射，恰 4 个保持邻接图）——第三种群结构，不同于两案 D4。g2（同一镜像、方向钉死）被拒：朴素臂会放行它，逐格对账在钉死口径下数出 1440 个被改写的 (状态 × 事件) 行为格。g3——填充态 720 与 1023 的对换，fixed——是平凡正控；pads 对换在 `lightsout3` 无填充态案之后于本案卷回归（定位注记记录在案卷 README：`mini2048` 本就配对 explicit 口径与真实填充态及 pads 正控；本案在 V4 上再次配对）。本表 relabel 列是法庭盖章的 relabel 框架，解析为 bitstring 判官——在 4 动作 < 10 位的本模型上动作被当翻位读，与方向键系统结构性错位，录为诊断列（与 `mini2048` 同形）。1024 态超出陪审团自同构枚举的规模护栏（跳过并如实记录）；O(E) 直接边集检查是主判定。案卷全文（含已验证的 4 元素映射表）：[cases/sliding2x3/README.zh-CN.md](cases/sliding2x3/README.zh-CN.md)。

## 『两种一样』——三问自判

整份案卷压在一个区分上：当判据说"这次改名保行为"，它对你的 **动作（事件）名** 已经做了假设。

1. **你的系统里，动作到底是什么？** 从外部到来的事件（包、消息、超时——名字写在对方也能引用的规范里）：**fixed** 地界。绑在状态坐标上的指令（"翻开关 a"）：**relabel** 地界。
2. **状态改名后，动作名必须跟着改吗？** 改名后若日志、规范、线上含义要继续诚实，动作名必须跟着状态一起重写：**relabel**。若动作名指的是任何内部改名都碰不到的外部事实：**fixed**。
3. **悄悄重写事件名会弄坏什么公开的东西吗？** 若一次把 `rcv FIN` 悄悄写成 `rcv ACK of FIN` 的压缩会让你的规范撒谎：**fixed**。

拿不准就两套都跑（法庭向来如此），把分歧当发现读。长版指引——含两个能手算复核的最小例子——在 [docs/which-identical.md](docs/which-identical.md)。

## 边界诚实

- **discover 守卫事件类系统。** 引擎的找群器（`discover`）是在 relabel 家族判据下提候选群的——它为坐标绑定制系统而造。在事件驱动状态机上，discover 的提案只当线索、不当结论：任何压缩之前，先按 fixed 口径重审一遍。法庭的 check 列做的正是这次重审。
- **平凡群是协议自己的性质。** 若只找到恒等这一个对称，不是判据失职：它说明协议自己的事件结构已经把每个状态钉死了。带着事件标签读的 TCP 恰好就是这种系统——值得知道，不是缺陷。
- **标准里的图常常只是示意。** TCP Figure 5 省略了"任意状态收到 RST"的转移（图注 Note 3 自己写明）；这些边 **不收录**，缺失记录在案卷元数据里，而不是靠编造补齐。
- **pass ≠ 业务放行。** 每份判决书里的每个 pass，都只在对应该列写明的那套口径下成立。双胞胎在 relabel 列的 pass 是真的——而恰恰是那套口径下合并它们，机器就不再是 TCP。

## 参与贡献

新增案例是这里的主贡献方式：选一部公开标准，逐边转录、逐边注出处，起草被告群（含一名你预期败诉的），开庭，落 expected 记录，用确定性生成器封卷。六步流程与守则见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 致谢与来源

- **wuxing_gua 判据引擎** —— 字节级原样内嵌、零修改；钉死的源码版本与来源记录在 [NOTICE](NOTICE)。引擎为同作者自有代码，自带 MIT 许可；零依赖（纯标准库）。
- **networkx** —— 独立陪审团，仅用于仲裁臂（BSD 许可；引擎不依赖它）。
- **RFC 9293**（传输控制协议）—— `tcp` 案出处，转录自 §3.3.2 Figure 5。
- **RFC 2131**（动态主机配置协议）—— `dhcp` 案出处，转录自 §4.4 Figure 5。
- **RFC 3501**（互联网消息访问协议 IMAP4rev1）—— `imap` 案出处，转录自 §3（状态）与 §6（分状态命令）。
- **etcd-io/raft**（`raft.go`，钉定 `c51f010c851e`）—— `raft-etcd` 案出处，转录自 StateType 枚举与 step 函数族（raft.go:49-56 等）。
- **apache/hadoop**（trunk @ `e66f40daf3cc`）—— `hadoop-mr-task` 案出处，转录自 `TaskStateInternal.java` 的状态机工厂。
- **Kubernetes 官方文档**（Pod Lifecycle 页）—— `k8s-pod-lifecycle` 案出处，逐边引官方原句。
- **RFC 8446**（TLS 1.3）—— `tls13-handshake` 案出处，转录自 Appendix A（§A.1/§A.2），§4 为规范锚点。
- **USB 2.0 规范**（USB-IF，§9.1）—— `usb2-device-states` 案出处，转录自 Figure 9-1 与 Table 9-1。
- **Wikipedia "Lights Out (game)"** 与 **Jaap's Puzzle Page "Lights Out"** —— `lightsout3` 案出处，转录自 Gameplay/Strategy 原句，3×3 棋盘尺寸记为变体边界。
- **field-trial 盲测项目** —— 上述 5 案的转录与两轮盲测验证来源；sealed 真值对账记录在各案 `expected.json` 的 provenance 里。

定位口径，明说：在我们检索过的范围内，没有见到这个组合的对标——公开标准的状态机、在两套写明名字的等变口径下受审、配独立陪审团与可复跑判决书。若你知道对标在哪里，我们真心想听：开个 issue。

- 判决引擎为 [wuxing-gua](https://github.com/cx2002302-lang/wuxing-gua)——本法庭所实例化的上游项目；以 04cf0b6 版字节级内嵌（见 [NOTICE](NOTICE)）。
- 图解版成果一页看懂在上游主仓：[docs/成果介绍-图解版.html](https://github.com/cx2002302-lang/wuxing-gua/blob/main/docs/成果介绍-图解版.html)（[wuxing-gua](https://github.com/cx2002302-lang/wuxing-gua) 仓）——页内每个数字与本法庭回执（`verdicts/comparison.*.json`）对账一致。

## 许可

MIT——见 [LICENSE](LICENSE)。内嵌引擎保留其自身 MIT 许可条款，记录在 [NOTICE](NOTICE)。

# 新鲜 clone 走查——外部用户视角实跑 quick start

*2026-11-07。把本仓新鲜 `git clone` 到项目外临时目录，由一次独立执行逐行
照 README quick start 实跑，并把全部输出与仓内已提交收据对账。**结论：9/9
条走查命令行为与文档相符（其中一条暴露旗标陷阱，记于 §6）；selftest 重放
450/450 个契约字段；三份重生成收据共对账 4581 个叶子字段，4578 一致、3 处
差异——三处均为运行元数据，实质字段零漂移。**以下每个数字都由本次走查的
命令记录或本仓收据文件支撑——无一来自记忆。临时 clone 已在走查后删除；
原始控制台日志留存于仓外。*

实测环境：Windows、Python 3.12.10、networkx 3.6.1（环境中已装——见 §6
F2）。clone 命令：`git clone <本仓> <临时目录>`；clone 的 HEAD 与本仓一致
（`631b7e8`，"discover: labeled VF2 automorphism discovery subcommand + 12-case
truth reconciliation"），开跑前 `git status --porcelain` 为空。说明：走查
当时源检出工作树对若干 `verdicts/*` 有未提交的本地改动；按定义新鲜 clone
只反映最后一次提交——这正是外部用户拿到的状态，因此全文以已提交收据为
对账基准（§5）。

## 1. 步骤与命令

在 clone 内按序执行九条命令：

| # | 命令 | 退出码 | 耗时（量级） | 结果 |
|---|---|---|---|---|
| 1 | `git clone <repo> <temp dir>` | 0 | 秒级 | clone 位于 `631b7e8`，树干净 |
| 2 | `python -X utf8 -m pip install networkx` | 0 | 秒级 | `Requirement already satisfied`（3.6.1） |
| 3 | `python -X utf8 -m symmetry_court list` | 0 | 一秒内 | 案卷：12 案，全 `expected=yes verdict=yes` |
| 4 | `python -X utf8 -m symmetry_court selftest` | 0 | 个位数分钟（低段） | `SELFTEST PASS（重放契约字段 450 个）` |
| 5 | `python -X utf8 -m symmetry_court arbitrate --case tcp` | 0 | 一秒内 | **静默空转**——见 §6 F1 |
| 6 | `python -X utf8 -m symmetry_court arbitrate --only tcp` | 0 | 秒级 | 庭审表格 + 收据落盘 |
| 7 | `python -X utf8 -m symmetry_court discover --case tcp` | 0 | 一秒内 | 发现摘要 + 收据落盘 |
| 8 | `python -X utf8 -m symmetry_court arbitrate --help` | 0 | 一秒内 | 可见 `--only NAME`（旗标发现路径） |
| 9 | `python -X utf8 -m symmetry_court discover --case no-such-case` | 3 | 一秒内 | stderr `未找到案件 'no-such-case'`——大声拒绝 |

（控制台打印的本机绝对路径在下文摘录中裁去；原始日志保留原样。）

`list` 输出案卷部分：12 个子目录——`dhcp`（16 态/15 动作，4 群）、
`hadoop-mr-task`（8/9，3）、`hanoi3`（32/6，4）、`imap`（8/6，3）、
`k8s-pod-lifecycle`（8/7，3）、`lightsout3`（512/9，5）、`mini2048`
（256/4，6）、`raft-etcd`（4/14，3）、`sliding2x3`（1024/4，4）、`tcp`
（16/12，4）、`tls13-handshake`（32/18，3）、`usb2-device-states`（8/8，3）
——每行均 `expected=yes verdict=yes`；烟测案卷 1 案；引擎 vendored：在位。

## 2. 门禁：selftest

```
[vendored] OK：NOTICE 清单 30 文件逐一重算 sha256 一致，无清单外文件
[engine] OK：wuxing_gua 1.0.0（cwd=vendored/，PYTHONDONTWRITEBYTECODE=1）
...
SELFTEST PASS（重放契约字段 450 个）
```

逐案重放的契约字段数（每案同时通过「仓内收据 vs expected」核对）：

| 案件 | 字段 | 案件 | 字段 |
|---|---|---|---|
| `dhcp` | 40 | `raft-etcd` | 30 |
| `hadoop-mr-task` | 30 | `sliding2x3` | 40 |
| `hanoi3` | 40 | `tcp` | 40 |
| `imap` | 30 | `tls13-handshake` | 30 |
| `k8s-pod-lifecycle` | 30 | `usb2-device-states` | 30 |
| `lightsout3` | 50 | `mini2048` | 60 |

合计 450——对 expected 记录零漂移，且这是在一份走查者从未改写过的树上。

## 3. 庭审：一案三判官

命令 #5（本轮起初按 `discover --case` 的类比顺手敲出的命令）产出：

```
案卷 tcp：0 案受审
无案件可审（0 cases）——正式案卷以 cases/ 为准；烟测可用 --cases-dir smoke
EXIT=0
```

——一案未审却退出码 0：argparse 把 `--case` 前缀匹配到了 `--cases-dir`，
工具去找名为 `tcp` 的案卷目录去了（§6 F1）。正确的单案形式是 `--only`：

```
开庭 case: tcp
群 group | wuxing-gua@relabel | wuxing-gua@fixed | nx@structure | nx@labeled | 一致性判语 ruling
absurd   | reject tv=1        | reject tv=1      | no           | no         | 两口径一致:reject
other    | reject tv=1        | reject tv=1      | no           | no         | 两口径一致:reject
pads     | pass tv=0          | pass tv=0        | yes          | yes        | 两口径一致:pass
swap     | pass tv=0          | reject tv=1      | yes          | no         | 口径二义:relabel=pass/fixed=reject; nx 分列支持; 按声明(fixed)终判=reject
  判语汇总 ruling codes: {"agree": 3, "semantics_duality": 1} | 口径内配对全部一致: True
  判决书已写出: <clone>/verdicts/tcp.verdict.json
审判结束：全部 1 案均开庭并写出判决书。
```

这正是 README 旗舰行的现场重放：双生子（`swap`）在 relabel 口径下 pass、
fixed 口径下 reject，networkx 陪审同向分列；补位置换（`pads`）双口径
pass；两个对照被告（`absurd`、`other`）双口径 reject——判官不是橡皮图章。

## 4. 发现臂：一案

```
discover case: tcp
  WL 细分: 12 块, 离散=False | 枚举: 120 个自同构, 触顶=False
  群阶: 120 | 轨道: 12 (exact)
  闸门臂(vendored check --strict, 候选阶 120): pass
  对账 expected: 4 群一致=True
  冒烟双方向: pads 发现=True | swap 不发现=True
  判决书已写出: verdicts/discover.tcp.json (+ candidate 群文件，均可重放)
发现结束：全部 1 案已发现并写出判决书与候选群文件。
```

与 README 对 `tcp` 的记载逐项一致：完整补位交换群，阶 120 = 5!，细分不离
散（12 块），12 条精确轨道，闸门臂 pass，4 群对账全部一致，双向冒烟契约
两侧成立（pads 群被发现的；形态双生子 `swap` 不被发现——枚举完成故为精
确缺席）。与命令 #5 的静默空转对照，命令 #9 显示 discover 对未知案名大声
拒绝：stderr 报错、退出码 3。

## 5. 对账——实跑输出 vs 已提交收据

三个层级，全部当场执行：

1. **clone 同一性。** clone HEAD = `631b7e8` = 本仓 HEAD；开跑前工作树
   干净（`git status --porcelain` 为空）。
2. **门禁重放。** selftest：450/450 契约字段 PASS（§2），含对仓内
   `verdicts/` 已提交收据的核对。
3. **逐叶 diff：实跑收据 vs 已提交收据**（命令 #6/#7 就地写出的收据，与
   同路径 `git show HEAD:` 版本逐一比较；每个叶子字段都计数，无任何排除）：

| 收据 | 叶子字段 | 一致 | 差异 |
|---|---|---|---|
| `verdicts/tcp.verdict.json` | 508 | 507 | 1 |
| `verdicts/discover.tcp.json` | 2147 | 2145 | 2 |
| `verdicts/discover.tcp.candidate.json` | 1926 | 1926 | 0 |
| **合计** | **4581** | **4578** | **3** |

三处差异叶子，原文照录：

- `tcp.verdict.json → generated_utc`：`2026-11-06T21:34:37Z`（已提交）vs
  `2026-11-07T02:17:30Z`（实跑）——落盘时间戳，按设计随运行而变。
- `discover.tcp.json → generated_utc`：同类。
- `discover.tcp.json → sealed_truth.reason`：已提交版铸于 12 案对账审计跑
  （传了 `--sealed-dir`）："no sealed truth file for this case in the
  provided sealed dir (tcp.truth.json)"；实跑 quick start 未传 sealed
  dir："no sealed dir provided (--sealed-dir); sealed reconciliation not
  run"。两侧均记录 `sealed_truth.checked: false`；不涉及任何数字字段。
  （该跑见 report/discover-audit.md。）

就地重生成的 candidate 群文件与已提交版**字节全等**（sha256 一致）。全部
命令跑完后，clone 内 `git status --porcelain` 恰好只显示两个被改写的已
跟踪文件——即命令 #6/#7 重写的两份收据——别无其他。

## 6. 摩擦点与观察

**F1——单案庭审旗标是个陷阱。** README quick start 只给全案形式
（`arbitrate`）；单案旗标 `--only NAME` 存在但只在 `--help` 里可见。带着
discover 章节的 `--case NAME` 习惯过来的用户会得到**退出码 0 的静默空转**：
argparse 把 `--case` 唯一前缀匹配到 `--cases-dir`，工具报
`案卷 tcp：0 案受审`（它去找名为 `tcp` 的案卷目录了）然后一无所为地成功
退出。对照之下 discover 对未知案名 exit 3 大声拒绝（命令 #9）。两条低成
本加固供维护者参考：在 quick start 里写明 `--only`；和/或 arbitrate 在
零案受审时退出非零（它已打印警告行——对脚本而言退出码才是陷阱）。

> **已修（2026-11-07）——F1 闭环。** 三条加固全部落地，陷阱本身被移除：
> （1）`arbitrate` 与 `selftest` 现在接受 `--case NAME`（精确单案名，行为与
> `discover --case` 一致）；（2）全部子命令零案受审一律响亮失败——未知案名
> 或空案卷写 stderr 说明并退出码 3，"0 案静默 exit 0" 不再可能（所有
> argparse 解析器改用 `allow_abbrev=False`，打错的旗标如 `--cas` 也一样
> 大声报错，未知旗标退出码统一为 3）；（3）`compare`/`discover` 对零案卷
> 同样拒绝。本报告命令 #5 的复跑：
> `python -X utf8 -m symmetry_court arbitrate --case tcp` → `案卷 …：1 案受审`、
> 完整判决表、判决书写出、退出码 0。零匹配形态（`arbitrate --case
> no-such-case`、`selftest --case no-such-case`，以及 arbitrate/selftest/
> compare/discover 各自指向空目录的 `--cases-dir`/`--root`）均写 stderr 并
> 退出码 3。改动后全量门禁复跑：`SELFTEST PASS（重放契约字段 450 个）`、
> 退出码 0——契约字段零漂移。

**F2——依赖安装步未在空环境中演练。** networkx 3.6.1 已在环境中，pip 报
`Requirement already satisfied`，从零下载路径本次未验证。已验证的是：README
关于 networkx 是唯一安装（引擎 vendored 且零依赖）的说法与 `pyproject.toml`
及 §2 的 vendored 重哈希行相符。

> **已解（2026-11-07）——F2 空环境演练完成。** 依赖安装步在项目外临时目录的
> 一次性 venv 中重跑（`python -X utf8 -m venv <temp>/venv`；全新解释器唯一的
> 包是 pip 25.0.1——无 networkx，别无他物），quick start 随后在本 HEAD
> （`9c074ce`，开跑前 `git status --porcelain` 为空）的新鲜 clone 内、仅用该
> venv 解释器重跑。命令序列全部退出码 0：`python -X utf8 -m pip install
> networkx` → `Successfully installed networkx-3.7`；随后为封死缓存捷径，
> 卸载后以 `python -X utf8 -m pip install --no-cache-dir networkx` 重装
> （缓存被禁后 pip 无本地 wheel 可退，跑的就是从零抓取本身）→ 退出码 0。
> 终态环境：networkx 3.7 + pip 25.0.1，别无他物。quick start 的单案序列随后
> 在 networkx 3.7 下实跑，全部退出码 0：`list`（12 案全 `expected=yes
> verdict=yes`；引擎 vendored 在位，selftest 内 NOTICE 清单重哈希通过）、
> `selftest`（`SELFTEST PASS（重放契约字段 450 个）`）、`arbitrate --case
> tcp`（1 案受审；双生子行为 relabel pass / fixed reject / nx 分列，与案卷
> 一致）、`discover --case tcp`（阶 120 = 5!、12 条精确轨道、闸门臂 pass、
> 4/4 expected 对账、冒烟双向成立）。与已提交收据逐叶对账（无任何排除）：
> 三份 `tcp` 收据共 4581 个叶子字段，4574 一致、7 处差异——两处
> `generated_utc` 时间戳、一处 `sealed_truth.reason` 调用说明、三处随运行
> 而变的计时字段（量级不变；精确值以各收据的 `timing_seconds` 为准），另有
> 一处新的如实观察：`tcp.verdict.json → tools.networkx` 已提交版记
> `3.6.1`、实跑版记 `3.7`——该字段记录的是真正参与运行的陪审库版本；陪审库
> 领先一个大版本，全部 verdict、tv、判语叶子仍逐叶一致。candidate 群文件
> 重生成字节全等（sha256 一致）。本次全程无一处 `Requirement already
> satisfied`：依赖步已在空环境中验证。

观察（非摩擦）：(a) 三份收据中唯一非确定性的叶子就是上面两个
`generated_utc` 与一处 `sealed_truth.reason` 字符串；(b) 本次走查实测耗时
量级——selftest 低段个位数分钟，单案 arbitrate 秒级，单案 discover 一秒
以内，分工序数字在各自收据的 `timing_seconds`；(c) 控制台会打印本机绝对
路径（`<clone>/cases`、`<clone>/verdicts/...`）——正常 CLI 行为，本报告
已裁去。

## 7. 结语

一个拿着新鲜 clone 的陌生人照 README quick start 走完，得到的是：一份如实
自报的 12 案案卷；一扇重放 450/450 契约字段的门禁；旗舰双生子的现场庭审
且表格与 README 行逐格相符；一次发现跑，其数字（阶 120、12 轨道、闸门
pass、4/4 对账、冒烟双方向）与已提交收据除一个时间戳、一处随调用而变的
说明文字外逐叶相符；以及一份字节全等重生的 candidate 群文件。途中唯一的
锐边是 §6 F1 的 `--only`/`--case` 旗标陷阱。临时 clone 已在本走查后删除；
本报告与其英文孪生是本次向仓库添加的仅有的两个文件，本次执行未 commit、
未 push。

英文版：[fresh-clone-walkthrough.md](fresh-clone-walkthrough.md)


---

## 增补（整合趟，2026-11-07）

本报告由发现臂走查趟对 HEAD `631b7e8` 写就，落盘时未提交。compare 波整合趟
随后在整合后的树上复核了报告中可就地复现的论断并原样提交本报告：
`arbitrate --case tcp` 静默空转（退出码 0）与 `discover --case no-such-case`
响亮拒答（退出码 3）均予复现；`selftest` 在整合树上重跑（`SELFTEST PASS`，
450/450 契约字段，退出码 0）。走查前后落地了三个整合提交，均不改变本走查的
方法与结论：`ffafeda`（仅计时戳的收据刷新）、`42c5ce8`（正确性锚点如实两分
——代码与收据同步移动，重生成收据与已提交收据仍除运行元数据外逐叶相符），
以及 compare 的发现臂整合（对账收据新增 `discovery_arm` 块与逐行
`discovery` 列，只读既有 `verdicts/discover.<case>.json` 收据、绝不重跑发现；
与这些收据逐字段交叉核验：2 离散 / 9 pads / 1 填充之外 / 4 触顶，假阳性指示
0）。

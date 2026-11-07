# Case `ppp-lcp` — PPP LCP option-negotiation automaton (RFC 1661 sec.4)

Second external blind-trial round (`field-trial2/`) complete case file.
External system: the PPP Link Control Protocol option-negotiation automaton,
one automaton as seen by one endpoint, transcribed from RFC 1661 (PPP, July
1994), section 4 "The Option Negotiation Automaton" — the complete sec.4.1
State Transition Table (both halves, all 16 event rows x 10 state columns),
the sec.4.1 preamble, the p/r/x footnotes, plus the sec.4.2 States and
sec.4.3 Events prose. RFC 1661 is a public Internet Standards Track
specification (STD 51); the primary-source text snapshot lives at
`dossier/sources/rfc1661.txt` (fetched from
`https://www.rfc-editor.org/rfc/rfc1661.txt`).

第二轮外部盲测（`field-trial2/`）完整案卷。外部系统：PPP 链路控制协议（LCP）
选项协商自动机（单自动机、单端点视角），转录自 RFC 1661（1994 年 7 月）§4
"选项协商自动机"——§4.1 状态转移表**全表两半**（16 事件行 × 10 状态列）+
§4.1 前言 + p/r/x 注脚 + §4.2 状态、§4.3 事件正文。RFC 1661 是公开的
Internet 标准轨道规范（STD 51）；一手文本快照在
`dossier/sources/rfc1661.txt`（取自 rfc-editor.org 官方 txt）。

---

## 1. What is in this directory | 本目录内容

| file | content | 内容 |
|------|---------|------|
| `model.json` | trans model: 16-slot input contract (4 bits), **10 real states + 6 padding states**, **16 events**, rewards all zero, goals empty. All **120 declared table cells** (every non-'-' cell of both table halves) carry their RFC citation — section, row, column, printed cell text, snapshot line number — in `meta.edges_with_citations`; the 40 '-' (illegal-transition) cells and every other deviation from the table are declared in `meta.transcription_notes` (7 entries). | trans 模型：16 槽输入契约（4 bit），**10 实态 + 6 填充态**，**16 事件**，reward 全零，goals 空。**120 个已声明表格**（两半表全部非 '-' 格）每格在 `meta.edges_with_citations` 带规范引证——条号、行、列、印刷 cell 原文、快照行号；40 个 '-'（非法转移）格与其它全部转录政策在 `meta.transcription_notes`（7 条）声明。 |
| `expected.json` | hand-derived expected rows for the 4 candidate groups, under both action-name calibers (`relabel` = diagnostic contrast reading, `fixed` = protocol-true reading), plus the independent networkx juror columns. Provenance states the rows were derived from the transcription cell by cell, then confirmed by a live arbitration run. | 4 个候选群的手推期望行，覆盖两种动作名口径（`relabel`=诊断对照口径，`fixed`=协议真读法），外加独立陪审 networkx 两列。provenance 写明：行由转录逐格手推、再经 live 仲裁确认。 |
| `groups/*.json` | 4 candidate groups, each order 2, each file declares `semantics: {"action": "fixed"}` (event names pinned). | 4 个候选群，均为 2 阶，每个文件声明 `semantics: {"action": "fixed"}`（事件名钉死）。 |
| `make_ppp_lcp.py` | deterministic generator: rewrites the 6 files above **byte-identically** on every run (nothing random, no clock, no locale dependence); `--check` verifies byte identity and exits non-zero on drift. | 确定性生成器：每次运行**字节同一**地重写上述 6 个文件（无随机、无时钟、无本地化依赖）；`--check` 校验字节同一，漂移即非零退出。 |

State/event inventory (RFC-printed table headers, snapshot txt:736 and
txt:781): Initial(0), Starting(1), Closed(2), Stopped(3), Closing(4),
Stopping(5), Req-Sent(6), Ack-Rcvd(7), Ack-Sent(8), Opened(9) — sec.4.2
prints the long forms Request-Sent (txt:931) and Ack-Received (txt:945);
slots 10..15 are padding (self-loop only). Events are the table's own row
labels: Up, Down, Open, Close, TO+, TO-, RCR+, RCR-, RCA, RCN, RTR, RTA,
RUC, RXJ+, RXJ-, RXR (16; RXR bundles Echo-Request/Echo-Reply/
Discard-Request into one event per the sec.4 preamble, txt:676-681).
Undeclared (state, event) pairs and the table's '-' cells self-loop with
reward 0 — the encoding policy follows the court's tcp and http2 cases.

状态/事件清单（RFC 表头印刷名，快照 txt:736 与 txt:781）：Initial(0)、
Starting(1)、Closed(2)、Stopped(3)、Closing(4)、Stopping(5)、Req-Sent(6)、
Ack-Rcvd(7)、Ack-Sent(8)、Opened(9)——§4.2 正文用全称 Request-Sent
（txt:931）与 Ack-Received（txt:945）；10..15 槽为填充（纯自环）。事件即表
格行标签：Up/Down/Open/Close/TO+/TO-/RCR+/RCR-/RCA/RCN/RTR/RTA/RUC/RXJ+/
RXJ-/RXR（16 个；RXR 按 §4 前言 txt:676-681 把 Echo-Request/Echo-Reply/
Discard-Request 三包并作一事件）。未声明的 (state, event) 对与表中 '-' 格
自环 r=0——编码政策沿用法庭 tcp 案与 http2 案。

---

## 2. The symmetry claim | 对称主张

**EN.** RFC 1661 describes the two "one-step-from-Open" states in
near-verbatim mirror sentences. sec.4.2 'Ack-Received' (snapshot txt:945-949):
"a Configure-Request has been sent and a Configure-Ack has been received.
The Restart timer is still running, since a Configure-Ack has not yet been
sent." sec.4.2 'Ack-Sent' (snapshot txt:951-956): "a Configure-Request and a
Configure-Ack have both been sent, but a Configure-Ack has not yet been
received. The Restart timer is running, since a Configure-Ack has not yet
been received." The twin reading — whoever still owes the Configure-Ack is
the mirror of whoever still waits for it — suggests swapping Ack-Rcvd and
Ack-Sent maps the negotiation race onto itself. In RFC 9113's stream machine
(the field-trial2 http2 case) this same role-mirror reading held at the
structure level and broke only on event names; the expectation here was the
same shape. The table says otherwise: the swap breaks earlier.

**中文。** RFC 1661 用近乎逐字的镜像句描写两个"距 Open 一步"的状态。
§4.2 'Ack-Received'（快照 txt:945-949）："a Configure-Request has been sent
and a Configure-Ack has been received. The Restart timer is still running,
since a Configure-Ack has not yet been sent."。§4.2 'Ack-Sent'（快照
txt:951-956）："a Configure-Request and a Configure-Ack have both been sent,
but a Configure-Ack has not yet been received. The Restart timer is
running..."。"孪生"读法——仍欠对方 Configure-Ack 的一方是仍在等待
Configure-Ack 一方的镜像——提示把 Ack-Rcvd 与 Ack-Sent 互换即可让协商竞态
映射到自身。在 RFC 9113 流状态机（field-trial2 的 http2 案）中，同款角色
镜像读法在结构层成立、只在事件命名层断裂；本案的预期也是同型。表格给出了
相反答案：互换断裂得更早。

---

## 3. Candidate groups and expected rows | 候选群与期望行

`expected.json` holds 4 groups × 2 calibers = **8 verdict rows** (plus the
networkx juror pair per group); the live gate counts **40 replay contract
fields** (10 per group). All rows below were hand-derived from the
transcription cell by cell and match the live runs field-for-field.

`expected.json` 含 4 群 × 2 口径 = **8 行判决期望**（另每群一组 networkx
陪审列）；门禁实测重放契约字段 **40 个**（每群 10 个）。以下各行由转录逐格
手推、后与 live 跑逐字段一致。

| group | construction | relabel | fixed | networkx (structure / labeled) |
|-------|--------------|---------|-------|--------------------------------|
| `ack-twins-swap` (**claim** 主张群) | swap (7↔8) | reject, worst_tv 1.0 | reject, 1.0 | false / false |
| `closing-stopping-swap` (control 对照) | swap (4↔5) alone | reject, 1.0 | reject, 1.0 | false / false |
| `closed-stopped-swap` (control 对照) | swap (2↔3) alone | reject, 1.0 | reject, 1.0 | false / false |
| `pads` (positive control 正对照) | swap (10↔11) | pass, 0.0 | pass, 0.0 | true / true |

The two controls are the RFC's own "counterpart" twins (sec.4.2: "The
Stopping state is the Open counterpart to the Closing state" txt:920; "The
Stopped state is the Open counterpart to the Closed state" txt:864) taken
one swap at a time — each fails on drain targets that differ across the pair
(Down to Initial txt:739 vs Starting txt:784; drains to Closed txt:744/752/
756 vs to Stopped; negotiation-entry edges exist only on the Stopped side
txt:746-747). The positive control shows the pipeline admits a genuine
symmetry under both readings when one exists (padding states 10 and 11 have
byte-identical rows).

两个对照群取自 RFC 自己的 "counterpart" 孪生句（§4.2："The Stopping state
is the Open counterpart to the Closing state" txt:920；"The Stopped state is
the Open counterpart to the Closed state" txt:864），每次只换一对——每对都
在"汇入目标不同"上失败（Down 分别到 Initial txt:739 与 Starting txt:784；
汇入 Closed txt:744/752/756 与汇入 Stopped；协商进入边只存在于 Stopped 侧
txt:746-747）。正对照证明当真对称存在时（填充态 10 与 11 行字节相同），
流水线在两种口径下都会放行。

---

## 4. Finding | 实测结论

The claim group `ack-twins-swap` rules **`agree: reject`** — both calibers
reject (relabel worst_tv 1.0, fixed worst_tv 1.0) and the independent
networkx juror splits **neither** (structure no, labeled no). This is a
different shape from the http2 case: the HTTP/2 endpoint-role mirror was
admitted at the structure level (relabel pass, worst_tv 0.0) and broke only
on pinned event names (`semantics_duality`), whereas the LCP Ack-twin swap
is rejected **before** the structure layer — among the 120 declared table
cells, Ack-Rcvd has 6 edges into Req-Sent and 4 self-loops while Ack-Sent
has 2 edges into Req-Sent and 8 self-loops (TO+ txt:788: Ack-Rcvd retreats
to Req-Sent `scr/6` while Ack-Sent retransmits in place `scr/8`; RCR+ txt:791:
Ack-Rcvd completes `sca,tlu/9` while Ack-Sent loops `sca/8`; RCA txt:793:
Ack-Rcvd's ack is a crossed-connection retreat `scr/6x` while Ack-Sent's
completes the link `irc,tlu/9`). The near-verbatim sec.4.2 mirror sentences
describe the two roles' symmetric *meaning*, not a symmetric *graph*: in the
negotiation race the two twins move in opposite directions (one is finishing,
one is still being waited on), and no relabeling of event names can repair a
6-vs-2 target-count mismatch. Measured answer to "under which caliber does
the symmetry claim hold": for the LCP Ack twins, under neither — the twin
reading is narrative, not structural.

主张群 `ack-twins-swap` 判 **`agree: reject`**——两种口径都拒绝（relabel
worst_tv 1.0、fixed worst_tv 1.0），独立陪审 networkx 在**任何口径**都不分
裂（结构 no、标签 no）。这与 http2 案不同型：HTTP/2 端点角色镜像在结构层被
承认（relabel pass，worst_tv 0.0）、只在事件名钉死时断裂（`semantics_
duality`）；而 LCP 的 Ack 孪生互换**在结构层之前**就被拒绝——120 个已声明
表格中，Ack-Rcvd 有 6 条边进入 Req-Sent、4 条自环，Ack-Sent 只有 2 条边进入
Req-Sent、8 条自环（TO+ txt:788：Ack-Rcvd 回退 Req-Sent `scr/6`，Ack-Sent
原地重发 `scr/8`；RCR+ txt:791：Ack-Rcvd 完成协商 `sca,tlu/9`，Ack-Sent
自环 `sca/8`；RCA txt:793：Ack-Rcvd 的 ack 是交叉连接回退 `scr/6x`，
Ack-Sent 的 ack 完成链路 `irc,tlu/9`）。§4.2 那两段近乎逐字的镜像句描写的是
两种角色的对称**语义**，不是对称的**图**：协商竞态中两个孪生态朝相反方向
运动（一个正在完成、一个仍被等待），6 对 2 的目标数失配无法靠事件重命名
修复。"对称主张在哪个口径下成立"的实测答案：对 LCP 的 Ack 孪生，哪个口径
都不成立——孪生读法是叙事性的，不是结构性的。

---

## 5. Reproduce | 复现

Run from the court checkout root (the `symmetry_court` package must be
importable and the vendored engine must sit at its pinned location — i.e.
run inside a checkout of the court repo with this workspace as a sibling
directory, exactly the layout used for the http2 case; judgment criteria
are used as-is, never modified):

在法庭仓检出根目录运行（`symmetry_court` 包需可导入、vendored 引擎需在钉定
位置——即在法庭仓检出内以本工作区为同级目录运行，与 http2 案同款布局；判据
按原样使用，绝不修改）：

```text
# 1) generator byte-identity | 生成器字节同一
python -X utf8 ../field-trial2/cases/ppp-lcp/make_ppp_lcp.py --check
#    observed: exit 0, byte-identity OK (6 files) | 实测：exit 0，6 文件字节同一

# 2) live three-way arbitration (writes the receipt) | live 三方仲裁（写收据）
python -X utf8 -m symmetry_court arbitrate --cases-dir ../field-trial2/cases --verdicts-dir ../field-trial2/verdicts --case ppp-lcp
#    observed: exit 0, ruling codes {"agree": 4} | 实测：exit 0，判语汇总 {"agree": 4}

# 3) live gate over the round-2 docket (replays both cases) | 二轮卷宗门禁（重放两案）
python -X utf8 -m symmetry_court selftest --cases-dir ../field-trial2/cases --verdicts-dir ../field-trial2/verdicts
#    observed: exit 0, SELFTEST PASS（重放契约字段 80 个）| 实测：exit 0，80 个契约字段

# 4) the court's own 12-case gate, unaffected | 法庭自有 12 案门禁不受影响
python -X utf8 -m symmetry_court selftest
#    observed: exit 0, SELFTEST PASS（重放契约字段 450 个）| 实测：exit 0，450 个契约字段
```

Regenerate the case files with `python -X utf8
../field-trial2/cases/ppp-lcp/make_ppp_lcp.py` (no `--check`).

去掉 `--check` 直接运行生成器即重写案卷文件。

---

## 6. Provenance, receipts, red lines | 出处、收据与红线

- Primary source: RFC 1661 official txt (snapshot `dossier/sources/
  rfc1661.txt`); every one of the 120 collected edges cites its table cell
  (section, row, column, printed cell text) with a snapshot line number
  (txt:738-758 upper half, txt:783-803 lower half); footnotes p/r/x anchor
  at txt:818/820/822 with their option discussions (txt:894-904,
  txt:1025-1041, txt:1124-1135); the twin-state prose anchors at
  txt:945-956; the counterpart sentences at txt:864 and txt:920. An
  independent snapshot cross-check parsed both table halves straight from
  the snapshot and compared all 160 cells (120 declared + 40 '-') against
  `model.json` target-by-target: PASS, 160/160.
- 一手来源：RFC 1661 官方 txt（快照 `dossier/sources/rfc1661.txt`）；120 条
  收录边每条引证其表格格（条号、行、列、印刷 cell 原文）并带快照行号
  （上半 txt:738-758，下半 txt:783-803）；注脚 p/r/x 锚在 txt:818/820/822，
  选项讨论锚在 txt:894-904、txt:1025-1041、txt:1124-1135；孪生状态正文锚在
  txt:945-956；counterpart 句在 txt:864 与 txt:920。另做了一次独立快照交叉
  复核：直接从快照解析两半表全部 160 格（120 声明 + 40 '-'），与 `model.json`
  逐 target 比对：PASS，160/160。
- Live receipts: `verdicts/ppp-lcp.verdict.json` (written by the arbitration
  run; `generated_utc` is a run-variable field — a re-run refreshes it
  timing-only). Gate stdout snapshots: `report/ppp_arbitrate_stdout.txt`,
  `report/ppp_make_check_stdout.txt`, `report/ppp_ft2_selftest_stdout.txt`,
  `report/ppp_court_selftest_stdout.txt` (paired `*_stderr.txt`, each 0
  bytes; every command ran pipe-free with the exit code read directly from
  the gate process, per the court's section-7 SOP).
- live 收据：`verdicts/ppp-lcp.verdict.json`（仲裁运行写出；`generated_utc`
  为运行变量字段——复跑仅按 timing-only 刷新）。门禁 stdout 快照：
  `report/ppp_arbitrate_stdout.txt`、`report/ppp_make_check_stdout.txt`、
  `report/ppp_ft2_selftest_stdout.txt`、`report/ppp_court_selftest_stdout.txt`
  （配对 `*_stderr.txt` 各 0 字节；所有命令无管道、退出码从门禁进程直读，
  按法庭 §7 SOP）。
- Red lines kept: the case participates only via `--cases-dir` /
  `--verdicts-dir`; the court's own docket files (its `cases/` and
  `verdicts/`) are untouched, and the 12-docket gate still replays **450
  contract fields** (exit 0, working tree clean before and after the run);
  judgment criteria and the vendored engine are used as-is. Numbers in this
  README are backed by the live runs and receipts named above, not by
  ad-hoc claims.
- 红线保持：本案只经 `--cases-dir` / `--verdicts-dir` 参审；法庭自有卷宗
  （其 `cases/` 与 `verdicts/`）零触碰，12 案门禁仍重放 **450 个契约字段**
  （exit 0，跑前后工作树 clean）；判据与 vendored 引擎按原样使用。本 README
  全部数字以上述 live 跑与收据为据。
---

## 7. Adoption into the official docket | 收编入庭（2026-11-08）

**EN.** On 2026-11-08 this case (RFC 1661 sec.4 negotiation automaton) was adopted into the court's
official docket as `cases/ppp-lcp` — the closing step of the field-trial2
blind-trial round 2. Facts of the adoption, all live-run backed in this
repository:

- Source: the field-trial2 round-2 complete case file. Byte-level copy
  verified: all 8 files sha256-identical at copy time, and the six
  oracle-input files (`model.json`, `expected.json`, the 4 group files)
  match the hashes recorded in `field-trial2/sealed/manifest.json`.
- Unsealing verdict (round-2 reconciliation,
  `field-trial2/report/reconciliation.md`): across the three adopted cases,
  12 candidate groups × 5 axes (fixed / relabel / binding /
  networkx-structure / networkx-labeled) = **60/60 AGREE**, false positives
  0, false negatives 0. The sealed truth was frozen write-once at
  2026-11-07T18:34:44Z, before the tool receipts were opened.
- Sealed truth: `field-trial2/sealed/ppp-lcp.truth.json` (sha256 listed in
  `field-trial2/sealed/manifest.json`). The `networkx` columns in
  `expected.json` are carried from this sealed truth and record the
  sourcing in `provenance.networkx_source`; this adoption run's live
  networkx jury reproduced the same two columns for all 4 groups.
- What adoption changed in this directory: `expected.json` provenance
  rewritten for the docket (engine rows re-observed live in this repository
  — values field-for-field identical to the round-2 records);
  `make_ppp_lcp.py`'s embedded expected provenance updated to match, so generator
  byte-identity still holds; this section appended. Sections 1–6 above are
  the round-2 record kept verbatim — they describe the blind-trial phase,
  when this case participated only via `--cases-dir` and the docket still
  counted 450 contract fields over 12 cases.
- Receipts (2026-11-08, in this repository): `python -X utf8 -m
  symmetry_court arbitrate --emit-expected-template --case ppp-lcp` → exit 0,
  stderr 0 bytes, ruling codes `{"agree": 4}`, receipt
  `verdicts/ppp-lcp.verdict.json`; `make_ppp_lcp.py --check` → exit 0 (byte-identity
  OK, 6 files); docket gate `python -X utf8 -m symmetry_court selftest` →
  exit 0, `SELFTEST PASS（重放契约字段 570 个）` over 15 cases (this case:
  40/40 contract fields PASS).

**中文。** 2026-11-08，本案（RFC 1661 sec.4 negotiation automaton）收编入法庭正式案卷，路径
`cases/ppp-lcp`——field-trial2 盲测二轮的收官一步。收编事实，全部在本仓
live-run 背书：

- 来源：field-trial2 二轮完整案卷。字节级复制已核验：8 个文件复制时
  sha256 逐一相同；六份 oracle 输入文件（`model.json`、`expected.json`、
  4 个群文件）与 `field-trial2/sealed/manifest.json` 记录的哈希一致。
- 开封判语（二轮对账，`field-trial2/report/reconciliation.md`）：三案合计
  12 个候选群 × 5 个轴（fixed / relabel / binding / networkx-structure /
  networkx-labeled）= **60/60 全 AGREE**，假阳 0、假阴 0。封存真值于
  2026-11-07T18:34:44Z 写一次冻结，先于工具收据开封。
- 封存真值：`field-trial2/sealed/ppp-lcp.truth.json`（sha256 见
  `field-trial2/sealed/manifest.json`）。`expected.json` 的 networkx 两列
  沿用该封存真值，来源已写入 `provenance.networkx_source`；本次收编运行的
  live networkx 陪审逐群复现了相同两列（4 群全同）。
- 收编在本目录内的改动：`expected.json` 的 provenance 按案卷口径重写
  （引擎行在本仓 live 重测——数值与二轮记录逐字段一致）；`make_ppp_lcp.py` 内嵌的
  expected provenance 同步更新，生成器字节同一保持；追加本节。以上 1–6 节
  为二轮原记录、一字未动——它们描述的是盲测阶段（本案当时只经
  `--cases-dir` 参审，全卷 12 案 450 契约字段）。
- 收据（2026-11-08，本仓）：`python -X utf8 -m symmetry_court arbitrate
  --emit-expected-template --case ppp-lcp` → exit 0、stderr 0 字节、判语
  `{"agree": 4}`、收据 `verdicts/ppp-lcp.verdict.json`；`make_ppp_lcp.py --check` →
  exit 0（byte-identity OK，6 文件）；全卷门禁 `python -X utf8 -m
  symmetry_court selftest` → exit 0、`SELFTEST PASS（重放契约字段 570 个）`、
  15 案（本案 40/40 契约字段 PASS）。

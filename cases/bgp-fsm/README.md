# Case `bgp-fsm` — BGP-4 peer finite state machine (RFC 4271 sec.8)

Second external blind-trial round (`field-trial2/`) complete case file —
the round's third. External system: the BGP-4 peer finite state machine, one
FSM as seen by one endpoint for one configured peer, transcribed from
RFC 4271 (A Border Gateway Protocol 4 (BGP-4), January 2006), section 8
"BGP Finite State Machine (FSM)" — the event list of sec.8.1.1-8.1.5
(Events 1-28, numbering per sec.8.2.1.4) plus the per-state paragraphs of
sec.8.2.2. RFC 4271 is a public Internet Standards Track specification; the
primary-source text snapshot lives at `dossier/sources/rfc4271.txt` (fetched
from `https://www.rfc-editor.org/rfc/rfc4271.txt`).

第二轮外部盲测（`field-trial2/`）完整案卷——本轮第三案。外部系统：BGP-4
对等体有限状态机（单端点、单配置对等体视角的一份 FSM），转录自 RFC 4271
（2006 年 1 月）§8 "BGP Finite State Machine (FSM)"——§8.1.1-8.1.5 的事件
清单（Event 1-28，编号依 §8.2.1.4）+ §8.2.2 逐状态段落。RFC 4271 是公开的
Internet 标准轨道规范；一手文本快照在 `dossier/sources/rfc4271.txt`
（取自 rfc-editor.org 官方 txt）。

---

## 1. What is in this directory | 本目录内容

| file | content | 内容 |
|------|---------|------|
| `model.json` | trans model: 8-slot input contract (3 bits), **6 real states + 2 padding states**, **28 events**, rewards all zero, goals empty. All **99 collected edges** carry their RFC citation (clause reference + printed transition phrase + snapshot line range) in `meta.edges_with_citations`; every deviation from the prose is declared in `meta.transcription_notes` (12 entries, each marked NOT COLLECTED / KEPT with the RFC sentence quoted). | trans 模型：8 槽输入契约（3 bit），**6 实态 + 2 填充态**，**28 事件**，reward 全零，goals 空。**99 条已收录边**每条在 `meta.edges_with_citations` 带规范引证（条号 + 印刷迁移句 + 快照行段）；对散文的全部偏离在 `meta.transcription_notes`（12 条，逐条标注未收录/保留并引用原句）。 |
| `expected.json` | verdict rows for the 4 candidate groups under both action-name calibers (`relabel` = diagnostic contrast reading, `fixed` = protocol-true reading) plus the independent networkx juror columns. Provenance states the rows were taken from the live arbitration run — no rows were pre-written: `model.json` and `groups/` were generated and arbitrated before this file existed. | 4 个候选群在两种动作名口径下的判决行（`relabel`=诊断对照口径，`fixed`=协议真读法），外加独立陪审 networkx 两列。provenance 写明：行取自 live 仲裁运行——无任何预写：本文件生成之前 `model.json` 与 `groups/` 已生成并开庭。 |
| `groups/*.json` | 4 candidate groups, each order 2, each file declares `semantics: {"action": "fixed"}` (event names pinned). | 4 个候选群，均为 2 阶，每个文件声明 `semantics: {"action": "fixed"}`（事件名钉死）。 |
| `make_bgp_fsm.py` | deterministic generator: rewrites the 6 files above **byte-identically** on every run (nothing random, no clock, no locale dependence); `--check` verifies byte identity and exits non-zero on drift. | 确定性生成器：每次运行**字节同一**地重写上述 6 个文件（无随机、无时钟、无本地化依赖）；`--check` 校验字节同一，漂移即非零退出。 |

State/event inventory: Idle(0), Connect(1), Active(2), OpenSent(3),
OpenConfirm(4), Established(5); slots 6..7 are padding (self-loop only).
Events = sec.8.1's printed names in RFC event-number order (Event N =
action index N-1): ManualStart, ManualStop, AutomaticStart,
ManualStart_with_PassiveTcpEstablishment, AutomaticStart_with_PassiveTcpEstablishment,
AutomaticStart_with_DampPeerOscillations, AutomaticStart_with_DampPeerOscillations_and_PassiveTcpEstablishment,
AutomaticStop, ConnectRetryTimer_Expires, HoldTimer_Expires,
KeepaliveTimer_Expires, DelayOpenTimer_Expires, IdleHoldTimer_Expires,
TcpConnection_Valid, Tcp_CR_Invalid, Tcp_CR_Acked, TcpConnectionConfirmed,
TcpConnectionFails, BGPOpen, BGPOpen_with_DelayOpenTimer_running (the RFC
prints "BGPOpen with DelayOpenTimer running"), BGPHeaderErr, BGPOpenMsgErr,
OpenCollisionDump, NotifMsgVerErr, NotifMsg, KeepAliveMsg, UpdateMsg,
UpdateMsgErr. Undeclared (state, event) pairs self-loop with reward 0 — the
encoding policy follows the court's tcp/http2/ppp cases.

状态/事件清单：Idle(0)、Connect(1)、Active(2)、OpenSent(3)、
OpenConfirm(4)、Established(5)；6..7 槽为填充（纯自环）。事件即 §8.1 的
印刷名、按 RFC 事件号排序（事件 N = 动作下标 N-1）：ManualStart …
UpdateMsgErr 共 28 个（Event 20 印刷形为 "BGPOpen with DelayOpenTimer
running"，模型写作 BGPOpen_with_DelayOpenTimer_running）。未声明的
(state, event) 对自环 r=0——编码政策沿用法庭 tcp/http2/ppp 案。

---

## 2. The symmetry claim | 对称主张

**EN.** The engineering reading that motivates the case: at the session
layer the two BGP speakers are peers — each runs the same FSM table, and
when two connections collide the winner is decided by an ordering (router
comparison, sec.6.8) that does not depend on which side dialed; sec.8.2.1.2:
"there may be two connections for one peer. After the connection collision
is resolved (see Section 6.8), the FSM for the connection that is closed
SHOULD be disposed" (snapshot txt:2879-2883). The case tests what that
peer-equivalence does and does not give away at the level of one FSM's
state set: can the internal state pairs — the TCP-acquisition pair
(Connect, Active), the session-live pair (OpenConfirm, Established), the
mid-negotiation pair (OpenSent, OpenConfirm) — be exchanged while every
arrow of sec.8.2.2's prose maps to an arrow?

**中文。** 本案的工程出发点：会话层上两个 BGP 发言人对等——各自运行同一份
FSM 表，两条连接相撞时按与拨号方向无关的序（router 比较，§6.8）裁决；
§8.2.1.2 原文："there may be two connections for one peer. After the
connection collision is resolved (see Section 6.8), the FSM for the
connection that is closed SHOULD be disposed"（快照 txt:2879-2883）。本案
实测的是这份对等性在单份 FSM 状态集层面给出什么、不给什么：内部状态对——
TCP 建连对（Connect, Active）、会话存活对（OpenConfirm, Established）、
协商中段对（OpenSent, OpenConfirm）——能否互换而让 §8.2.2 散文的每条箭头
映射到箭头？

---

## 3. Candidate groups and verdict rows | 候选群与判决行

`expected.json` holds 4 groups × 2 calibers = **8 verdict rows** (plus the
networkx juror pair per group); the live gate counts **40 replay contract
fields** (10 per group). The rows are the live run's own observed rows.

`expected.json` 含 4 群 × 2 口径 = **8 行判决**（另每群一组 networkx 陪审
列）；门禁实测重放契约字段 **40 个**（每群 10 个）。各行即 live 运行的
实测行。

| group | construction | relabel | fixed | networkx (structure / labeled) |
|-------|--------------|---------|-------|--------------------------------|
| `connect-active-swap` (**claim** 主张群) | swap (1↔2) | reject, worst_tv 1.0 | reject, 1.0 | false / false |
| `openconfirm-established-swap` (control 对照) | swap (4↔5) alone | reject, 1.0 | reject, 1.0 | false / false |
| `opensent-openconfirm-swap` (control 对照) | swap (3↔4) alone | reject, 1.0 | reject, 1.0 | false / false |
| `pads` (positive control 正对照) | swap (6↔7) | pass, 0.0 | pass, 0.0 | true / true |

Live ruling summary: `{"agree": 4}` — both engine calibers and the networkx
juror agree on every group, so no semantics duality appears in this case:
all three real-state swaps break at the structure level already, before
event names are pinned.

live 判语汇总：`{"agree": 4}`——两种引擎口径与 networkx 陪审对每群全体
一致，本案无语义二元性：三个实态互换全部在结构层即断，早于事件名钉死。

---

## 4. Finding | 实测结论

The claim group `connect-active-swap` rules **reject under both readings**.
Under the base transcription (optional session attributes at their defaults,
per sec.8.2.1.3) the two states' rows differ on a single event — Event 9
(ConnectRetryTimer_Expires): in Connect it "stays in the Connect state"
(txt:3052), in Active it "changes its state to Connect" (txt:3290) — and the
rest of the break is structural, not lexical: Idle feeds Connect through
Events 1/3 and Active through Events 4/5 (txt:2947-2962, txt:2975-2988), and
OpenSent's TcpConnectionFails exits to Active only (txt:3569-3579). Renaming
cannot repair it either: Connect declares three self-transitions (Events
9/14/15) where Active declares two (Events 14/15) — a 3-into-2 pigeonhole.
The measured answer to the peer-equivalence reading: Connect and Active are
complements (the side that dials and the side that listens), not
interchangeable states; the RFC encodes the complementarity in the optional
event split itself.

主张群 `connect-active-swap` 两口径均判 **reject**。在基础转录口径下
（可选会话属性取默认，依 §8.2.1.3），两态的行只在单一事件上不同——
Event 9（ConnectRetryTimer_Expires）：Connect "stays in the Connect state"
（txt:3052），Active "changes its state to Connect"（txt:3290）——其余断裂
都是结构性的而非词汇性的：Idle 经事件 1/3 进 Connect、经事件 4/5 进
Active（txt:2947-2962、txt:2975-2988），且 OpenSent 的
TcpConnectionFails 只去向 Active（txt:3569-3579）。改名也救不了：Connect
声明三条自迁移（事件 9/14/15）而 Active 只声明两条（事件 14/15）——3 进 2
的鸽笼。对等性读法的实测答案：Connect 与 Active 是互补者（拨号方与监听
方），不是可互换状态；RFC 把这份互补性写进了可选事件的拆分本身。

---

## 5. Reproduce | 复现

Run from the workspace root that contains `field-trial2/` (the court package
must be importable — the receipts below were produced from a checkout of the
court repo with this workspace as a sibling directory; judgment criteria are
used as-is, never modified):

在包含 `field-trial2/` 的工作区根目录运行（法庭包需可导入——下列收据出自
法庭仓检出、以本工作区为同级目录；判据按原样使用，绝不修改）：

```text
# 1) generator byte-identity | 生成器字节同一
python -X utf8 field-trial2/cases/bgp-fsm/make_bgp_fsm.py --check
#    observed: exit 0, byte-identity OK (6 files) | 实测：exit 0，6 文件字节同一

# 2) live three-way arbitration (writes the receipt) | live 三方仲裁（写收据）
python -X utf8 -m symmetry_court arbitrate --cases-dir ../field-trial2/cases --verdicts-dir ../field-trial2/verdicts --case bgp-fsm
#    observed: exit 0, ruling codes {"agree": 4}, stderr 0 bytes | 实测：exit 0，判语 {"agree": 4}，stderr 0 字节

# 3) live gate over the round's three cases | 三案门禁
python -X utf8 -m symmetry_court selftest --cases-dir ../field-trial2/cases --verdicts-dir ../field-trial2/verdicts
#    observed: exit 0, SELFTEST PASS（重放契约字段 120 个）
```

Regenerate the case files with `python -X utf8
field-trial2/cases/bgp-fsm/make_bgp_fsm.py` (no `--check`).

去掉 `--check` 直接运行生成器即重写案卷文件。

---

## 6. Provenance, receipts, red lines | 出处、收据与红线

- Primary source: RFC 4271 official txt (snapshot `dossier/sources/rfc4271.txt`, 5,827 lines; sec.8 starts at txt:2023, sec.8.2.2 at txt:2939); every collected edge cites its sec.8.2.2 paragraph and snapshot line range; the event list cites sec.8.1.1-8.1.5 (Event definition headers at txt:2375 through txt:2814).
- 一手来源：RFC 4271 官方 txt（快照 `dossier/sources/rfc4271.txt`，5,827 行；§8 起于 txt:2023，§8.2.2 起于 txt:2939）；每条已收录边引用其 §8.2.2 段落与快照行段；事件清单引用 §8.1.1-8.1.5（事件定义头 txt:2375 至 txt:2814）。
- Transcription policies are declared, not silent: base-attributes reading for the optional-attribute branches (12 transcription notes; attribute-conditional branches and the tracked/ignored pairs listed with their snapshot lines).
- 转录口径是声明出来的，不是默认的：可选属性分支取基础属性读法（12 条转录注记；属性条件分支与 tracked/ignored 对均列出快照行）。
- Live receipt: `verdicts/bgp-fsm.verdict.json` (written by the arbitration run; sha256 8e3ebebc81c0d473ecd6b43fb9d222ae4341c78d5d642b448e40c5a7d0871512; its `generated_utc` is a run-variable field). Gate stdout snapshots: `report/bgp2_arbitrate_stdout.txt`, `report/bgp2_ft2_selftest_stdout.txt`, `report/bgp2_court_selftest_stdout.txt`.
- live 收据：`verdicts/bgp-fsm.verdict.json`（仲裁运行写出；sha256 8e3ebebc…1512；其 `generated_utc` 为运行变量字段）。门禁 stdout 快照：`report/bgp2_arbitrate_stdout.txt`、`report/bgp2_ft2_selftest_stdout.txt`、`report/bgp2_court_selftest_stdout.txt`。
- Red lines kept: the case participates only via `--cases-dir` / `--verdicts-dir`; the court's own docket files (its `cases/` and `verdicts/`) are untouched, and the 12-docket gate still replays **450 contract fields** (observed this session, exit 0); judgment criteria and the vendored engine are used as-is; no verdict row was pre-written — `expected.json` was generated after the live run from the arbitration's own observed rows.
- 红线保持：本案只经 `--cases-dir` / `--verdicts-dir` 参审；法庭自有卷宗（其 `cases/` 与 `verdicts/`）零触碰，12 案门禁仍重放 **450 个契约字段**（本会话实测，exit 0）；判据与 vendored 引擎按原样使用；无任何预写判决行——`expected.json` 在 live 运行之后依仲裁实测行生成。
---

## 7. Adoption into the official docket | 收编入庭（2026-11-08）

**EN.** On 2026-11-08 this case (RFC 4271 sec.8 peer FSM) was adopted into the court's
official docket as `cases/bgp-fsm` — the closing step of the field-trial2
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
- Sealed truth: `field-trial2/sealed/bgp-fsm.truth.json` (sha256 listed in
  `field-trial2/sealed/manifest.json`). The `networkx` columns in
  `expected.json` are carried from this sealed truth and record the
  sourcing in `provenance.networkx_source`; this adoption run's live
  networkx jury reproduced the same two columns for all 4 groups.
- What adoption changed in this directory: `expected.json` provenance
  rewritten for the docket (engine rows re-observed live in this repository
  — values field-for-field identical to the round-2 records);
  `make_bgp_fsm.py`'s embedded expected provenance updated to match, so generator
  byte-identity still holds; this section appended. Sections 1–6 above are
  the round-2 record kept verbatim — they describe the blind-trial phase,
  when this case participated only via `--cases-dir` and the docket still
  counted 450 contract fields over 12 cases.
- Receipts (2026-11-08, in this repository): `python -X utf8 -m
  symmetry_court arbitrate --emit-expected-template --case bgp-fsm` → exit 0,
  stderr 0 bytes, ruling codes `{"agree": 4}`, receipt
  `verdicts/bgp-fsm.verdict.json`; `make_bgp_fsm.py --check` → exit 0 (byte-identity
  OK, 6 files); docket gate `python -X utf8 -m symmetry_court selftest` →
  exit 0, `SELFTEST PASS（重放契约字段 570 个）` over 15 cases (this case:
  40/40 contract fields PASS).

**中文。** 2026-11-08，本案（RFC 4271 sec.8 peer FSM）收编入法庭正式案卷，路径
`cases/bgp-fsm`——field-trial2 盲测二轮的收官一步。收编事实，全部在本仓
live-run 背书：

- 来源：field-trial2 二轮完整案卷。字节级复制已核验：8 个文件复制时
  sha256 逐一相同；六份 oracle 输入文件（`model.json`、`expected.json`、
  4 个群文件）与 `field-trial2/sealed/manifest.json` 记录的哈希一致。
- 开封判语（二轮对账，`field-trial2/report/reconciliation.md`）：三案合计
  12 个候选群 × 5 个轴（fixed / relabel / binding / networkx-structure /
  networkx-labeled）= **60/60 全 AGREE**，假阳 0、假阴 0。封存真值于
  2026-11-07T18:34:44Z 写一次冻结，先于工具收据开封。
- 封存真值：`field-trial2/sealed/bgp-fsm.truth.json`（sha256 见
  `field-trial2/sealed/manifest.json`）。`expected.json` 的 networkx 两列
  沿用该封存真值，来源已写入 `provenance.networkx_source`；本次收编运行的
  live networkx 陪审逐群复现了相同两列（4 群全同）。
- 收编在本目录内的改动：`expected.json` 的 provenance 按案卷口径重写
  （引擎行在本仓 live 重测——数值与二轮记录逐字段一致）；`make_bgp_fsm.py` 内嵌的
  expected provenance 同步更新，生成器字节同一保持；追加本节。以上 1–6 节
  为二轮原记录、一字未动——它们描述的是盲测阶段（本案当时只经
  `--cases-dir` 参审，全卷 12 案 450 契约字段）。
- 收据（2026-11-08，本仓）：`python -X utf8 -m symmetry_court arbitrate
  --emit-expected-template --case bgp-fsm` → exit 0、stderr 0 字节、判语
  `{"agree": 4}`、收据 `verdicts/bgp-fsm.verdict.json`；`make_bgp_fsm.py --check` →
  exit 0（byte-identity OK，6 文件）；全卷门禁 `python -X utf8 -m
  symmetry_court selftest` → exit 0、`SELFTEST PASS（重放契约字段 570 个）`、
  15 案（本案 40/40 契约字段 PASS）。

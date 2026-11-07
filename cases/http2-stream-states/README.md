# Case `http2-stream-states` — HTTP/2 stream state machine (RFC 9113 sec.5.1)

Second external blind-trial round (`field-trial2/`) complete case file.
External system: the HTTP/2 stream state machine, one stream as seen by one
endpoint, transcribed from RFC 9113 (HTTP/2, June 2022), section 5.1 "Stream
States" — Figure 2 plus the per-state bullet lists plus the END_STREAM
separate-event paragraph. RFC 9113 is a public Internet Standards Track
specification (it obsoletes RFC 7540); the primary-source text snapshot lives
at `dossier/sources/rfc9113.txt` (fetched from
`https://www.rfc-editor.org/rfc/rfc9113.txt`).

第二轮外部盲测（`field-trial2/`）完整案卷。外部系统：HTTP/2 流状态机（单条流、
单个端点视角），转录自 RFC 9113（2022 年 6 月）§5.1 "Stream States"——Figure 2
全文 + 逐状态 bullet + END_STREAM 按独立事件处理的条款。RFC 9113 是公开的
Internet 标准轨道规范（废止 RFC 7540）；一手文本快照在
`dossier/sources/rfc9113.txt`（取自 rfc-editor.org 官方 txt）。

---

## 1. What is in this directory | 本目录内容

| file | content | 内容 |
|------|---------|------|
| `model.json` | trans model: 16-slot input contract (4 bits), **7 real states + 9 padding states**, **8 events**, rewards all zero, goals empty. All **20 collected edges** carry their RFC citation in `meta.edges_with_citations`; every deviation from the figure is declared in `meta.transcription_notes` (6 entries, each marked NOT COLLECTED / KEPT with the RFC sentence quoted). | trans 模型：16 槽输入契约（4 bit），**7 实态 + 9 填充态**，**8 事件**，reward 全零，goals 空。**20 条已收录边**每条在 `meta.edges_with_citations` 带规范引证；对图的全部偏离在 `meta.transcription_notes`（6 条，逐条标注未收录/保留并引用原句）。 |
| `expected.json` | hand-derived expected rows for the 4 candidate groups, under both action-name calibers (`relabel` = diagnostic contrast reading, `fixed` = protocol-true reading), plus the independent networkx juror columns. Provenance states the rows were derived from the transcription, then confirmed by a live arbitration run. | 4 个候选群的手推期望行，覆盖两种动作名口径（`relabel`=诊断对照口径，`fixed`=协议真读法），外加独立陪审 networkx 两列。provenance 写明：行先由转录手推、再经 live 仲裁确认。 |
| `groups/*.json` | 4 candidate groups, each order 2, each file declares `semantics: {"action": "fixed"}` (event names pinned). | 4 个候选群，均为 2 阶，每个文件声明 `semantics: {"action": "fixed"}`（事件名钉死）。 |
| `make_http2.py` | deterministic generator: rewrites the 6 files above **byte-identically** on every run (nothing random, no clock, no locale dependence); `--check` verifies byte identity and exits non-zero on drift. | 确定性生成器：每次运行**字节同一**地重写上述 6 个文件（无随机、无时钟、无本地化依赖）；`--check` 校验字节同一，漂移即非零退出。 |

State/event inventory: idle(0), reserved (local)(1), reserved (remote)(2),
open(3), half-closed (local)(4), half-closed (remote)(5), closed(6); slots
7..15 are padding (self-loop only). Events = Figure 2's own legend
abbreviations: send/recv × PP (PUSH_PROMISE), H (HEADERS), ES (END_STREAM
flag), R (RST_STREAM). Undeclared (state, event) pairs self-loop with reward 0
— the encoding policy follows the court's tcp case (RFC 9293 transcription).

状态/事件清单：idle(0)、reserved (local)(1)、reserved (remote)(2)、open(3)、
half-closed (local)(4)、half-closed (remote)(5)、closed(6)；7..15 槽为填充
（纯自环）。事件即 Figure 2 图例缩写：send/recv × PP（PUSH_PROMISE）、H
（HEADERS）、ES（END_STREAM flag）、R（RST_STREAM）。未声明的 (state, event)
对自环 r=0——编码政策沿用法庭 tcp 案（RFC 9293 转录）。

---

## 2. The symmetry claim | 对称主张

**EN.** RFC 9113 defines the state machine once and lets both endpoints run it
subjectively — sec.5.1 (snapshot txt:709): "Both endpoints have a subjective
view of the state of a stream". Swapping the two endpoint roles (local ↔
remote) maps every arrow of Figure 2 to an arrow: reserved (local) ↔ reserved
(remote) and half-closed (local) ↔ half-closed (remote) are mirror twins — the
two reserved bullets say verbatim the same sentence "Either endpoint can send
a RST_STREAM frame to cause the stream to become closed" (snapshot txt:764 and
txt:783) — while idle, open and closed stay fixed. The mirror holds at the
structure level only: edge labels are frame events and they flip with the role
(send ↔ recv), so with event names pinned (the protocol-true reading) the swap
is not a symmetry. The two endpoint roles are complementary, not identical.

**中文。** RFC 9113 只定义一份状态机，让两端各自以主观视角使用——§5.1（快照
txt:709）："Both endpoints have a subjective view of the state of a stream"。
把两个端点角色互换（local↔remote），Figure 2 的每条箭头都映射到箭头：reserved
(local) ↔ reserved (remote)、half-closed (local) ↔ half-closed (remote) 互为
镜像——两个 reserved bullet 逐字写同一句 "Either endpoint can send a RST_STREAM
frame to cause the stream to become closed"（快照 txt:764 与 txt:783）——
idle/open/closed 不动。但镜像只到结构层：边上的标签是帧事件，随角色翻转
（send↔recv），钉住事件名（协议真读法）后互换不再是对称。两端角色是互补关系，
不是恒等关系。

---

## 3. Candidate groups and expected rows | 候选群与期望行

`expected.json` holds 4 groups × 2 calibers = **8 verdict rows** (plus the
networkx juror pair per group); the live gate counts **40 replay contract
fields** (10 per group). All rows below were hand-derived from the
transcription and match the live runs field-for-field.

`expected.json` 含 4 群 × 2 口径 = **8 行判决期望**（另每群一组 networkx 陪审
列）；门禁实测重放契约字段 **40 个**（每群 10 个）。以下各行先手推、后与 live
跑逐字段一致。

| group | construction | relabel | fixed | networkx (structure / labeled) |
|-------|--------------|---------|-------|--------------------------------|
| `endpoint-mirror` (**claim** 主张群) | swap (1↔2) AND (4↔5) | pass, worst_tv 0.0 | **reject, worst_tv 1.0** | true / false |
| `half-mirror-only` (control 对照) | swap (4↔5) alone | reject, 1.0 | reject, 1.0 | false / false |
| `reserved-swap-only` (control 对照) | swap (1↔2) alone | reject, 1.0 | reject, 1.0 | false / false |
| `pads` (positive control 正对照) | swap (7↔8) | pass, 0.0 | pass, 0.0 | true / true |

The two controls exist because each half of the mirror alone is not a symmetry
of the graph (removing either swap breaks edge pairing); the positive control
shows the pipeline admits a genuine symmetry under both readings when one
exists (padding states 7 and 8 have byte-identical rows).

设两个对照群的原因：镜像的任一半单独拿掉都不构成图的对称（缺任一互换即破坏边
配对）；正对照证明当真对称存在时（填充态 7 与 8 行字节相同），流水线在两种口径
下都会放行。

---

## 4. Finding | 实测结论

The claim group `endpoint-mirror` rules **`semantics_duality`**: the
endpoint-role mirror is admitted at the structure level (relabel pass,
worst_tv 0.0) and rejected with event names pinned (fixed reject, worst_tv
1.0); the independent networkx juror splits the same way (structure yes /
labeled no). Under the group's declared reading (`fixed`, the protocol-true
one) the final ruling is reject. That is the measured answer to "under which
caliber does the symmetry claim hold": the shared-diagram engineering reading
is structural, and the frame-event naming is exactly where it stops.

主张群 `endpoint-mirror` 判 **`semantics_duality`**：端点角色镜像在结构层被
承认（relabel pass，worst_tv 0.0），钉住事件名后被拒绝（fixed reject，
worst_tv 1.0）；独立陪审 networkx 同步分裂（结构 yes / 标签 no）。按群声明的
读法（`fixed`，协议真读法）终判 reject。这就是"对称主张在哪个口径下成立"的
实测答案：同图两端的工程读法只到结构层，帧事件命名正是它的边界。

---

## 5. Reproduce | 复现

Run from the workspace root that contains `field-trial2/` (the court package
must be importable — e.g. run inside a checkout of the court repo with this
workspace as a sibling directory, or put that checkout on `PYTHONPATH`;
judgment criteria are used as-is, never modified):

在包含 `field-trial2/` 的工作区根目录运行（法庭包需可导入——例如在法庭仓检出
内以本工作区为同级目录运行，或将该检出加入 `PYTHONPATH`；判据按原样使用，
绝不修改）：

```text
# 1) generator byte-identity | 生成器字节同一
python -X utf8 field-trial2/cases/http2-stream-states/make_http2.py --check
#    observed: exit 0, byte-identity OK (6 files) | 实测：exit 0，6 文件字节同一

# 2) live three-way arbitration (writes the receipt) | live 三方仲裁（写收据）
python -X utf8 -m symmetry_court arbitrate --cases-dir field-trial2/cases --verdicts-dir field-trial2/verdicts --case http2-stream-states
#    observed: exit 0, ruling codes {"agree": 3, "semantics_duality": 1}

# 3) live gate (replays the case, compares expected + saved receipt) | 门禁
python -X utf8 -m symmetry_court selftest --cases-dir field-trial2/cases --verdicts-dir field-trial2/verdicts
#    observed: exit 0, SELFTEST PASS（重放契约字段 40 个）
```

Regenerate the case files with `python -X utf8
field-trial2/cases/http2-stream-states/make_http2.py` (no `--check`).

去掉 `--check` 直接运行生成器即重写案卷文件。

---

## 6. Provenance, receipts, red lines | 出处、收据与红线

- Primary source: RFC 9113 official txt (snapshot `dossier/sources/rfc9113.txt`); quote anchors verified in the snapshot at txt:706 (END_STREAM separate-event rule), txt:709 (subjective view), txt:764 / txt:783 (verbatim reserved-bullet mirror pair).
- 一手来源：RFC 9113 官方 txt（快照 `dossier/sources/rfc9113.txt`）；引文锚点已在快照内核对——txt:706（END_STREAM 独立事件条款）、txt:709（主观视角）、txt:764 / txt:783（两 reserved bullet 逐字镜像对）。
- Live receipt: `verdicts/http2-stream-states.verdict.json` (written by the arbitration run; its `generated_utc` is a run-variable field — a re-run refreshes it timing-only, substance fields verified identical leaf-for-leaf across same-day re-runs). Gate stdout snapshots: `report/ft2_selftest_stdout.txt` and `report/m2_ft2_selftest_stdout.txt`.
- live 收据：`verdicts/http2-stream-states.verdict.json`（仲裁运行写出；其 `generated_utc` 为运行变量字段——复跑仅按 timing-only 刷新，实质字段经同日多次复跑逐叶核对一致）。门禁 stdout 快照：`report/ft2_selftest_stdout.txt` 与 `report/m2_ft2_selftest_stdout.txt`。
- Red lines kept: the case participates only via `--cases-dir` / `--verdicts-dir`; the court's own docket files (its `cases/` and `verdicts/`) are untouched, and the 12-docket gate still replays **450 contract fields**; judgment criteria and the vendored engine are used as-is. Numbers in this README are backed by the live runs and receipts named above, not by ad-hoc claims.
- 红线保持：本案只经 `--cases-dir` / `--verdicts-dir` 参审；法庭自有卷宗（其 `cases/` 与 `verdicts/`）零触碰，12 案门禁仍重放 **450 个契约字段**；判据与 vendored 引擎按原样使用。本 README 全部数字以上述 live 跑与收据为据。
---

## 7. Adoption into the official docket | 收编入庭（2026-11-08）

**EN.** On 2026-11-08 this case (RFC 9113 sec.5.1 stream state machine) was adopted into the court's
official docket as `cases/http2-stream-states` — the closing step of the field-trial2
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
- Sealed truth: `field-trial2/sealed/http2-stream-states.truth.json` (sha256 listed in
  `field-trial2/sealed/manifest.json`). The `networkx` columns in
  `expected.json` are carried from this sealed truth and record the
  sourcing in `provenance.networkx_source`; this adoption run's live
  networkx jury reproduced the same two columns for all 4 groups.
- What adoption changed in this directory: `expected.json` provenance
  rewritten for the docket (engine rows re-observed live in this repository
  — values field-for-field identical to the round-2 records);
  `make_http2.py`'s embedded expected provenance updated to match, so generator
  byte-identity still holds; this section appended. Sections 1–6 above are
  the round-2 record kept verbatim — they describe the blind-trial phase,
  when this case participated only via `--cases-dir` and the docket still
  counted 450 contract fields over 12 cases.
- Receipts (2026-11-08, in this repository): `python -X utf8 -m
  symmetry_court arbitrate --emit-expected-template --case http2-stream-states` → exit 0,
  stderr 0 bytes, ruling codes `{"agree": 3, "semantics_duality": 1}`, receipt
  `verdicts/http2-stream-states.verdict.json`; `make_http2.py --check` → exit 0 (byte-identity
  OK, 6 files); docket gate `python -X utf8 -m symmetry_court selftest` →
  exit 0, `SELFTEST PASS（重放契约字段 570 个）` over 15 cases (this case:
  40/40 contract fields PASS).

**中文。** 2026-11-08，本案（RFC 9113 sec.5.1 stream state machine）收编入法庭正式案卷，路径
`cases/http2-stream-states`——field-trial2 盲测二轮的收官一步。收编事实，全部在本仓
live-run 背书：

- 来源：field-trial2 二轮完整案卷。字节级复制已核验：8 个文件复制时
  sha256 逐一相同；六份 oracle 输入文件（`model.json`、`expected.json`、
  4 个群文件）与 `field-trial2/sealed/manifest.json` 记录的哈希一致。
- 开封判语（二轮对账，`field-trial2/report/reconciliation.md`）：三案合计
  12 个候选群 × 5 个轴（fixed / relabel / binding / networkx-structure /
  networkx-labeled）= **60/60 全 AGREE**，假阳 0、假阴 0。封存真值于
  2026-11-07T18:34:44Z 写一次冻结，先于工具收据开封。
- 封存真值：`field-trial2/sealed/http2-stream-states.truth.json`（sha256 见
  `field-trial2/sealed/manifest.json`）。`expected.json` 的 networkx 两列
  沿用该封存真值，来源已写入 `provenance.networkx_source`；本次收编运行的
  live networkx 陪审逐群复现了相同两列（4 群全同）。
- 收编在本目录内的改动：`expected.json` 的 provenance 按案卷口径重写
  （引擎行在本仓 live 重测——数值与二轮记录逐字段一致）；`make_http2.py` 内嵌的
  expected provenance 同步更新，生成器字节同一保持；追加本节。以上 1–6 节
  为二轮原记录、一字未动——它们描述的是盲测阶段（本案当时只经
  `--cases-dir` 参审，全卷 12 案 450 契约字段）。
- 收据（2026-11-08，本仓）：`python -X utf8 -m symmetry_court arbitrate
  --emit-expected-template --case http2-stream-states` → exit 0、stderr 0 字节、判语
  `{"agree": 3, "semantics_duality": 1}`、收据 `verdicts/http2-stream-states.verdict.json`；`make_http2.py --check` →
  exit 0（byte-identity OK，6 文件）；全卷门禁 `python -X utf8 -m
  symmetry_court selftest` → exit 0、`SELFTEST PASS（重放契约字段 570 个）`、
  15 案（本案 40/40 契约字段 PASS）。

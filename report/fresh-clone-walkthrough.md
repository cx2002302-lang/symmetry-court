# Fresh-clone walkthrough — an external user runs the quick start

*2026-11-07. A fresh `git clone` of this repository was taken into a temporary
directory outside the project, the README quick start was executed line by
line by an independent pass, and every output was reconciled against the
committed receipts. **Outcome: 9/9 walkthrough commands behaved as documented
(one of them exposed a flag trap, recorded in §6); selftest replayed 450/450
contract fields; 4581 leaf fields compared across three regenerated receipts,
4578 identical, 3 differing — all three run-metadata, zero substantive
drift.** Every number below is backed by the command transcript of this
walkthrough or by a receipt file in this repository — none comes from memory.
The temporary clone was removed after the walkthrough; the raw console logs
were retained outside the repository.*

Environment observed: Windows, Python 3.12.10, networkx 3.6.1 (already
present — see §6 F2). Clone command: `git clone <this repository> <temp dir>`;
the clone's HEAD matched this repository's HEAD, `631b7e8` ("discover: labeled
VF2 automorphism discovery subcommand + 12-case truth reconciliation"), and
`git status --porcelain` was empty before any run. Note: the source checkout
showed uncommitted local edits to several `verdicts/*` files at walkthrough
time; a fresh clone reflects the last commit by definition, which is exactly
the state an external user receives — so the committed receipts are the
reconciliation target throughout (§5).

## 1. Steps and commands

Nine commands were executed inside the clone, in this order:

| # | Command | Exit | Duration (magnitude) | Result |
|---|---|---|---|---|
| 1 | `git clone <repo> <temp dir>` | 0 | seconds | clone at `631b7e8`, clean tree |
| 2 | `python -X utf8 -m pip install networkx` | 0 | seconds | `Requirement already satisfied` (3.6.1) |
| 3 | `python -X utf8 -m symmetry_court list` | 0 | under a second | docket: 12 cases, all `expected=yes verdict=yes` |
| 4 | `python -X utf8 -m symmetry_court selftest` | 0 | low single-digit minutes | `SELFTEST PASS（重放契约字段 450 个）` |
| 5 | `python -X utf8 -m symmetry_court arbitrate --case tcp` | 0 | under a second | **silent no-op** — see §6 F1 |
| 6 | `python -X utf8 -m symmetry_court arbitrate --only tcp` | 0 | seconds | trial table + receipt written |
| 7 | `python -X utf8 -m symmetry_court discover --case tcp` | 0 | under a second | discovery brief + receipts written |
| 8 | `python -X utf8 -m symmetry_court arbitrate --help` | 0 | under a second | shows `--only NAME` (flag discovery path) |
| 9 | `python -X utf8 -m symmetry_court discover --case no-such-case` | 3 | under a second | stderr `未找到案件 'no-such-case'` — loud refusal |

(Absolute local paths printed by the console are trimmed in the excerpts
below; the raw logs keep them.)

`list` output, docket part: 12 subdirectories — `dhcp` (16 states / 15
actions, 4 groups), `hadoop-mr-task` (8/9, 3), `hanoi3` (32/6, 4), `imap`
(8/6, 3), `k8s-pod-lifecycle` (8/7, 3), `lightsout3` (512/9, 5), `mini2048`
(256/4, 6), `raft-etcd` (4/14, 3), `sliding2x3` (1024/4, 4), `tcp` (16/12, 4),
`tls13-handshake` (32/18, 3), `usb2-device-states` (8/8, 3) — every row
`expected=yes verdict=yes`; smoke docket 1 case; engine vendored: present.

## 2. The gate: selftest

```
[vendored] OK：NOTICE 清单 30 文件逐一重算 sha256 一致，无清单外文件
[engine] OK：wuxing_gua 1.0.0（cwd=vendored/，PYTHONDONTWRITEBYTECODE=1）
...
SELFTEST PASS（重放契约字段 450 个）
```

Per-case contract fields replayed (each case also PASSes the
saved-receipt-vs-expected check):

| case | fields | case | fields |
|---|---|---|---|
| `dhcp` | 40 | `raft-etcd` | 30 |
| `hadoop-mr-task` | 30 | `sliding2x3` | 40 |
| `hanoi3` | 40 | `tcp` | 40 |
| `imap` | 30 | `tls13-handshake` | 30 |
| `k8s-pod-lifecycle` | 30 | `usb2-device-states` | 30 |
| `lightsout3` | 50 | `mini2048` | 60 |

Sum: 450 — zero drift against the expected records, in a tree the writer of
this walkthrough never touched.

## 3. The trial: one case, three judges

Command #5 (the one this pass initially reached for, by analogy with
`discover --case`) produced:

```
案卷 tcp：0 案受审
无案件可审（0 cases）——正式案卷以 cases/ 为准；烟测可用 --cases-dir smoke
EXIT=0
```

— exit 0 having tried nothing: argparse prefix-matched `--case` onto
`--cases-dir`, making the tool look for a docket directory named `tcp`
(§6 F1). The correct single-case form is `--only`:

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

This is the README's flagship row, replayed live: the twins (`swap`) pass
under the relabel standard and reject under the fixed standard, with the
networkx jury split the same way; the padding swap (`pads`) passes under both;
the two control defendants (`absurd`, `other`) are rejected under both — the
judge is no rubber stamp.

## 4. The discovery arm: one case

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

Exactly the README's recorded readings for `tcp`: the full padding-swap group,
order 120 = 5!, refinement not discrete (12 blocks), 12 exact orbits, gate arm
pass, per-group reconciliation consistent for all 4 groups, and the two-sided
smoke contract both ways (the pads group is discovered; the shape-twin `swap`
is absent — an exact absence, since the enumeration completed). By contrast
with command #5's silent no-op, command #9 shows `discover` refuses an
unknown case name loudly: stderr message, exit 3.

## 5. Reconciliation — fresh run vs committed receipts

Three levels, all executed here:

1. **Clone identity.** Clone HEAD = `631b7e8` = this repository's HEAD;
   working tree clean before the runs (`git status --porcelain` empty).
2. **Gate replay.** selftest: 450/450 contract fields PASS (§2), including
   the saved-receipt checks against the committed `verdicts/` files.
3. **Leaf-by-leaf diff, fresh receipts vs committed receipts** (the receipts
   commands #6 and #7 wrote in place, compared against `git show HEAD:` of
   the same paths; every leaf field counted, nothing excluded):

| receipt | leaf fields | equal | differ |
|---|---|---|---|
| `verdicts/tcp.verdict.json` | 508 | 507 | 1 |
| `verdicts/discover.tcp.json` | 2147 | 2145 | 2 |
| `verdicts/discover.tcp.candidate.json` | 1926 | 1926 | 0 |
| **total** | **4581** | **4578** | **3** |

The three differing leaves, quoted verbatim:

- `tcp.verdict.json → generated_utc`: `2026-11-06T21:34:37Z` (committed) vs
  `2026-11-07T02:17:30Z` (fresh) — a write timestamp, run-variable by design.
- `discover.tcp.json → generated_utc`: same category.
- `discover.tcp.json → sealed_truth.reason`: committed minted during the
  12-case audit run (which passed `--sealed-dir`): "no sealed truth file for
  this case in the provided sealed dir (tcp.truth.json)"; fresh quick-start
  run passes no sealed dir: "no sealed dir provided (--sealed-dir); sealed
  reconciliation not run". Both record `sealed_truth.checked: false`; no
  numeric field is involved. (See report/discover-audit.md for that run.)

The candidate group file regenerated in place is **byte-identical** to the
committed one (sha256 match). After all runs, `git status --porcelain` in the
clone shows exactly two modified tracked files — the two receipts commands #6
and #7 rewrote — and nothing else.

## 6. Friction points and observations

**F1 — the single-case arbitration flag is a trap.** README's quick start
shows only the all-cases form (`arbitrate`); the single-case flag `--only NAME`
exists but appears only in `--help`. A user carrying over the `--case NAME`
idiom from the discover section gets a **silent no-op with exit 0**: argparse
uniquely prefix-matches `--case` onto `--cases-dir`, so the tool reports
`案卷 tcp：0 案受审` (it looked for a docket directory named `tcp`) and exits
successfully having done nothing. `discover`, by contrast, refuses an unknown
case with exit 3 (command #9). Two low-cost hardenings, for the maintainers'
consideration: document `--only` in the quick start, and/or have arbitrate
exit non-zero when zero cases were selected (it already prints a warning
line — the exit code is the trap for scripts).

**F2 — the dependency step was not exercised from an empty environment.**
networkx 3.6.1 was already installed, so pip reported
`Requirement already satisfied` and the from-scratch download path went
unverified here. What was verified: the README's claim that networkx is the
only install (the engine is vendored and zero-dependency) matches
`pyproject.toml` and the vendored re-hash line in §2.

Observations (not frictions): (a) the two `generated_utc` fields and the
`sealed_truth.reason` string above are the only non-deterministic leaves in
the three receipts; (b) timing magnitudes observed in this walkthrough —
selftest low single-digit minutes, single-case arbitrate seconds, single-case
discover under a second, per-stage numbers in each receipt's
`timing_seconds`; (c) the console prints absolute local paths
(`<clone>/cases`, `<clone>/verdicts/...`) — normal CLI behavior, trimmed in
this report.

## 7. Conclusion

A stranger with a fresh clone, following the README quick start, gets: a
12-case docket that lists itself truthfully; a gate that replays 450/450
contract fields; a live trial of the flagship twins whose table matches the
README row cell by cell; a discovery run whose numbers (order 120, 12 orbits,
gate pass, 4/4 reconciliation, both smoke directions) match the committed
receipt leaf-for-leaf apart from a timestamp and one invocation-dependent
note string; and a candidate group file that regenerates byte-identical. The
one sharp edge found on the way is the `--only`/`--case` flag trap in §6 F1.
The temporary clone was removed after this walkthrough; this report and its
Chinese twin were the only files added to the repository, and nothing was
committed or pushed by this pass.

中文版：[fresh-clone-walkthrough.zh-CN.md](fresh-clone-walkthrough.zh-CN.md)


---

## Addendum (integration pass, 2026-11-07)

This report was authored by the discovery-arm walkthrough pass against HEAD
`631b7e8` and handed off uncommitted. The compare-wave integration pass then
verified its spot-checkable claims on the integrated tree and committed the
report unchanged: `arbitrate --case tcp` silent no-op (exit 0) and `discover
--case no-such-case` loud refusal (exit 3) were both reproduced; `selftest`
was re-run on the integrated tree (`SELFTEST PASS`, 450/450 contract fields,
exit 0). Three integration commits landed around/after the walkthrough, none
of which alters the walkthrough's method or outcome: `ffafeda` (timing-only
receipts refresh), `42c5ce8` (honest two-way correctness anchors — code and
receipts move together, so the regenerated receipt still matches the
committed one leaf-for-leaf apart from run metadata), and the compare
discovery-arm integration (comparison receipts now also carry a
`discovery_arm` block and a per-row `discovery` column, read from the
existing `verdicts/discover.<case>.json` receipts with no discovery re-run;
cross-checked field-by-field against those receipts: 2 discrete / 9 pads /
1 beyond-padding / 4 capped, false-positive indicators 0).

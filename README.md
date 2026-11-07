# Symmetry Court

[![CI: court selftest](https://img.shields.io/badge/court-selftest_pass-brightgreen)](https://github.com/cx2002302-lang/symmetry-court#quick-start) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Engine: wuxing-gua@04cf0b6](https://img.shields.io/badge/engine-wuxing--gua%4004cf0b6-grey)](NOTICE)

**A courtroom for symmetry claims about state machines.** One claim, three
judges, two named standards, a verdict file anyone can replay. —
中文版：[README.zh-CN.md](README.zh-CN.md)

---

## Meet the twins

Open the TCP standard — RFC 9293, §3.3.2, Figure 5 — and look at the two
closing paths. Near the end sit two states, `CLOSING` and `FIN-WAIT-2`, drawn
as near-perfect twins: each has one entrance and one exit, both exits lead to
the same next state, and what sends one twin out is exactly what brought the
other in. Erase the event labels from the diagram and swapping the two states
maps the picture perfectly onto itself.

But read the labels. `FIN-WAIT-2` ends when **the peer hangs up on us**
(`rcv FIN`). `CLOSING` ends when **the peer confirms our hang-up request**
(`rcv ACK of FIN`). Two different moments of two different closing paths —
and no renaming of internal states can make them the same event.

Now the twist. We asked a symmetry-judging engine whether that state swap
preserves behaviour, and it answered **pass**. We asked an independent graph
library the same question while keeping event labels in place, and it
answered **no — identity is the only symmetry**. Both answers are correct.
They answer *different questions*: "may the event names be renamed along with
the states?" versus "may the event names stay put?". The engine's default
assumes the rename is allowed; the specification says it is not; neither the
tool nor the jury ever said which question it was answering — until the
question was written down.

**That is what this repository is for.** Symmetry Court takes a symmetry
claim about a state machine, puts it in front of three judges, runs it under
*both* named standards, records every column in a verdict file, and states
the agreement or disagreement out loud. When the judges disagree — as they do
on the twins — the disagreement is the finding, published, not smoothed over.

The full story of the flagship case is in [docs/twin-trial.md](docs/twin-trial.md).

## What three-party arbitration means

For every symmetry claim (a "defendant group") in a case, the court runs:

| column | who | what it answers |
|---|---|---|
| `wuxing-gua@relabel` | the vendored judge engine, relabel standard | the swap holds **if event names may be renamed along with the states** |
| `wuxing-gua@fixed` | the same engine, fixed standard (`--strict`) | the swap holds **only if event names stay put** |
| `networkx@labeled` | an independent jury (networkx), labels fixed | the same graph question, computed by separate code |

plus a transparency column: the jury's structure-only answer (labels erased),
recorded in the case's expected/verdict files.

The three judges are independent on purpose. The engine is a vendored,
byte-identical, zero-dependency package; the jury is separate code built on
networkx. A bug in either cannot hide behind the other — it shows up as a
column disagreement. Every verdict carries an explicit agree/disagree line,
and `selftest` replays each verdict field-by-field against the expected
records, so a verdict that drifted from its receipt cannot pass silently.

The point is not that one column "wins". The point is that the standard each
column assumes is **written down** — which is exactly what was missing when
the twins exposed the gap.

## Five-minute quick start


```bash
git clone https://github.com/cx2002302-lang/symmetry-court.git
cd symmetry-court

# the only install: the jury's dependency (the engine itself needs nothing)
python -X utf8 -m pip install networkx

python -X utf8 -m symmetry_court list        # see the docket
python -X utf8 -m symmetry_court arbitrate   # run the trial — a verdict table per case
python -X utf8 -m symmetry_court compare     # gate-value A/B: naive structural merge vs the gate, per-group damage ledger (caliber per group declaration since v2)
python -X utf8 -m symmetry_court discover    # fixed-caliber candidate discovery + gate arm (scoped — see its section below)
python -X utf8 -m symmetry_court selftest    # replay every verdict against expected (exit 0 = green)
```

(`python -X utf8` is the project's convention on Windows; elsewhere a plain
`python3 -X utf8` behaves the same.)

Arbitrate prints a verdict table to the console and writes the full trial
records to `verdicts/<case>.verdict.json`. Selftest is the gate: exit `0`
means every verdict in the repository still matches its expected record.

Since v2, compare dispatches the caliber per group declaration (groups
declaring `explicit` run as declared, without `--strict`; groups declaring
`fixed` or none run `--strict`; since 2026-11-04 this includes the
per-element `action_maps` form). Across the 12-case / 45-group ledger every
gate admission is zero-damage by construction. The `mini2048` case (2048
merge mechanics, 2×2 variant, D4) is the explicit caliber's first
real-system docket: its "should-admit" is machine-asserted by the case
generator (per-element map uniqueness plus the group homomorphism law);
the engine's single-global-action_map limitation found on 2026-11-03 was
fixed upstream on 2026-11-04 (per-element `action_maps`, homomorphism law
checked at load) and g1/g3/g4 now run and pass under their declared
caliber. The `lightsout3` case (Lights Out toggle mechanics, 3×3 variant,
D4 — 2026-11-04) is the second real-system docket of that caliber and the
court's second non-trivial positive control: same group as `mini2048`'s,
different mechanism (toggle algebra instead of merge-and-slide). The
`sliding2x3` case (sliding-puzzle move mechanics, 2×3 variant, V4 —
2026-11-04) is the third real-system docket of that caliber and the
court's third non-trivial positive control: a third group structure (the
Klein four-group on a non-square rectangle, machine-verified as the full
geometric group), and the pads positive control returns alongside the
explicit caliber (304 real padding states, after `lightsout3`'s no-padding
entry). The `hanoi3` case (Tower of Hanoi move mechanics, 3-disk variant,
S3 — 2026-11-07) is the fourth real-system docket of that caliber and the
court's fourth non-trivial positive control: a fourth group structure (the
full peg-relabel group S3, order 6, the first non-abelian one), and the
docket's first entry whose action semantics is an ordered pair of rods —
a relabeling renames the actions as ordered pairs (X, Y) ↦ (πX, πY).
Across the 12-case / 45-group ledger, the structure-only naive
arm would admit 25 groups, of which 5 are genuinely harmful — those 5 would
silently rewrite 14596 real behavior cells (TCP twins, 6 cells;
keys-pinned rotations and mirror, 740 + 12288 + 1440 cells; the
pairs-pinned rod swap of `hanoi3`, 122 cells) — and the gate
refuses exactly those 5. (The gate arm's 20 admissions carry zero damage,
but that zero is guaranteed by construction, not independent evidence: by
the criterion's definition a pass requires `worst_tv <= 1e-9` on every
cell — receipt `gate_admitted_broken_is_zero_by_definition`;
`compare.py:326` comments it as "zero by criterion definition" — so the
zero is a consequence of the definition, not a separately measured
result. On the figure "5": it is `naive_harmful`, defined at
`compare.py:323` as `n_saved` — the count of harmful merges the gate
caught, not the total number of naive-admitted harmful groups; the
per-row detail keeps a separate contrast column `broken_real_cells_fixed`
(15 of the naive-admitted rows have `>0`).) See
[docs/闸门价值对比.html](docs/闸门价值对比.html),
[cases/mini2048/README.md](cases/mini2048/README.md),
[cases/lightsout3/README.md](cases/lightsout3/README.md),
[cases/sliding2x3/README.md](cases/sliding2x3/README.md) and
[cases/hanoi3/README.md](cases/hanoi3/README.md). Since 2026-11-07, compare
also reads each case's existing discovery receipt
(`verdicts/discover.<case>.json`; the discover module is not imported and
nothing is re-discovered) and carries the discovery arm into the same
ledger: per-case conclusion (2 discrete identity groups / 9 pads
discoveries / 1 beyond-padding fixed group, the 4 capped cases flagged;
discovered order, or lower bound with orbit LB/UB), with false-positive
indicators totaling 0 — the four capabilities close one loop: `discover`
proposes, `arbitrate` judges, `compare` prices, `selftest` replays.

### How to read a verdict

Each defendant group gets one row per standard:

- **exit code** — engine convention: `0` pass, `1` reject, `2` sample
  shortfall (sampling mode only; not used by the court), `3` input or
  internal error;
- **verdict** — pass/reject, under the column's named standard;
- **`worst_tv`** — the largest mismatch the check measured (total variation
  between the renamed and the original behaviour);
- **`judge`** — which internal judge the engine actually used, for
  traceability;
- **agree/disagree** — the court's one-line statement of whether the three
  columns tell the same story about this defendant, and why.

A **pass always means**: *structurally interchangeable under the named
standard*. It is not a blessing to compress. Picking the standard is your
call, and the next section is the checklist for it.

## The docket

The docket holds 12 cases: five incorporated from the field-trial blind-test
project (model/groups/generator/README copied byte-identical; their verdicts
reconcile group-by-group with field-trial's sealed truth, 15/15 groups — see
each case's `expected.json` provenance) and seven transcribed in this
repository (`tcp`, `dhcp`, `imap`, `mini2048`, `lightsout3`,
`sliding2x3`, `hanoi3`). Receipt:
`python -X utf8 -m symmetry_court list` over `cases/`. Every number below is
backed by the named receipt file in this repository — no number here comes
from memory.

| Case | Protocol | Source | States | Twin pair | relabel | fixed | networkx (labeled) |
|---|---|---|---|---|---|---|---|
| `tcp` | TCP connection state machine | RFC 9293 §3.3.2 Figure 5 | 16 states, 20 transitions, 12 events | CLOSING ↔ FIN-WAIT-2 | pass (exit 0, worst_tv 0.0) | reject (exit 1, worst_tv 1.0) | not a symmetry — identity only (structure-only: yes) |
| `dhcp` | DHCP client state machine | RFC 2131 §4.4 Figure 5 | 16 states (8 protocol + 8 padding), 18 transitions, 15 events | RENEWING ↔ REBINDING (decided by the transcription: not interchangeable) | reject (exit 1, worst_tv 1.0) | reject (exit 1, worst_tv 1.0) | not a symmetry (structure and labeled) |
| `imap` | IMAP4rev1 connection state machine | RFC 3501 §3 + §6 (prose spec, no drawn figure) | 8 states (4 protocol + 4 padding), 11 transitions, 6 events | AUTHENTICATED ↔ SELECTED (the SELECT/CLOSE 2-cycle) | reject (exit 1, worst_tv 1.0) | reject (exit 1, worst_tv 1.0) | not a symmetry (structure and labeled) |
| `raft-etcd` | etcd/raft single-node role state machine | etcd-io/raft `raft.go` @ `c51f010c851e` (StateType, raft.go:49-56) | 4 states (4 protocol + 0 padding), 12 cross-state transitions, 14 events | Candidate ↔ PreCandidate | reject (exit 1, worst_tv 1.0) | reject (exit 1, worst_tv 1.0) | not a symmetry (structure and labeled) |
| `hadoop-mr-task` | Hadoop MRv2 Task state machine | apache/hadoop trunk @ `e66f40daf3cc` (`TaskStateInternal.java`:19-23) | 8 states (7 protocol + 1 padding), 18 cross-state branches, 9 events | FAILED ↔ KILLED | reject (exit 1, worst_tv 0.75) | reject (exit 1, worst_tv 1.0) | not a symmetry (structure and labeled) |
| `k8s-pod-lifecycle` | Kubernetes Pod lifecycle (PodPhase) | kubernetes.io docs, Pod Lifecycle page | 8 states (5 protocol + 3 padding), 13 cross-state branches, 7 events | Succeeded ↔ Failed | reject (exit 1, worst_tv 1.0) | reject (exit 1, worst_tv 1.0) | not a symmetry (structure and labeled) |
| `tls13-handshake` | TLS 1.3 handshake state machine (client + server) | RFC 8446 Appendix A (§A.1/§A.2) | 32 states (17 protocol + 15 padding), 22 cross-state branches, 18 events | c_WAIT_CERT ↔ c_WAIT_CV | reject (exit 1, worst_tv 1.0) | reject (exit 1, worst_tv 1.0) | not a symmetry (structure and labeled) |
| `usb2-device-states` | USB 2.0 device visible state machine | USB 2.0 spec §9.1 (Figure 9-1 / Table 9-1) | 8 states (6 protocol + 2 padding), 14 cross-state branches, 8 events | Default ↔ Address | reject (exit 1, worst_tv 1.0) | reject (exit 1, worst_tv 1.0) | not a symmetry (structure and labeled) |
| `mini2048` | 2048 merge mechanics (2×2 deterministic variant) | gabrielecirulli/2048 `js/game_manager.js` (`move()` L130-191, direction numbering L131), corroborated by Wikipedia Gameplay | 256 states (81 real + 175 padding), 4 direction keys, score rewards | rot90 with renamed keys (explicit) vs the same rotation with keys pinned (fixed) — the caliber, not the permutation, decides | reject (exit 1, worst_tv 1.0; bitstring diagnostic — see note) | reject (exit 1, worst_tv 1.0) | explicit caliber with per-element maps admits rot90/flip/D4 since 2026-11-04 (70/136/55 orbits); keys-pinned reading stays a non-symmetry (structure-only: yes) |
| `lightsout3` | Lights Out toggle mechanics (3×3 deterministic variant) | Wikipedia "Lights Out (game)" (Gameplay + Strategy sentences) + Jaap's Puzzle Page (the rules page Wikipedia cites); 3×3 recorded as a variant boundary (the Tiger original is 5×5) | 512 states (all real, no padding), 9 buttons, rewards all zero (the source game has no score) | rot90 with renamed buttons (explicit) vs the same rotation with buttons pinned (fixed) — same group as `mini2048`, different mechanism (toggle algebra) | pass (exit 0, worst_tv 0.0; the bitstring judge's π-derived renaming coincides with the per-element button maps — see note) | reject (exit 1, worst_tv 1.0) | explicit caliber with per-element maps admits rot90/D4/D4×C2 (140/102/51 orbits), the fixed complement control passes (256 orbits); the keys-pinned rotation stays a non-symmetry (structure-only: yes) |
| `sliding2x3` | Sliding-puzzle move mechanics (2×3 deterministic variant, n-puzzle family; Klotski is the sliding-block cognate) | Wikipedia "15 puzzle" (lead + Solvability sentences) + Wikipedia "Sliding puzzle" (lead sentences); 2×3 recorded as a variant boundary (the canonical n-puzzle is 4×4; the 8 puzzle is 3×3) | 1024 states (720 real arrangements + 304 padding), 4 slide directions, rewards all zero (the puzzle has no score) | hflip with renamed directions (explicit) vs the same mirror with directions pinned (fixed) — a third group structure: V4 on a non-square rectangle (no 90° rotation exists) | reject (exit 1, worst_tv 1.0; bitstring diagnostic — see note) | reject (exit 1, worst_tv 1.0) | explicit caliber with per-element maps admits hflip/V4 (664/484 orbits), the fixed pads control passes (1023 orbits); the directions-pinned mirror stays a non-symmetry (structure-only: yes) |
| `hanoi3` | Tower of Hanoi move mechanics (3-disk deterministic variant) | Wikipedia "Tower of Hanoi" (lead rules + objective + minimum-moves + graph + S3-symmetry sentences); 3 disks recorded as a variant boundary (the source takes "a number of disks"; toy versions commonly 7–9) | 32 states (27 real arrangements + 5 padding), 6 ordered rod-pair actions, rewards all zero (the puzzle has no score) | A↔B rod swap with renamed ordered pairs (explicit) vs the same swap with pairs pinned (fixed) — a fourth group structure: the full peg-relabel group S3 (order 6, first non-abelian), and the docket's first ordered-pair action semantics | pass (exit 0, worst_tv 0.0; the relabel frame resolves to the generalized judge, which derives the renaming from the state permutation — see note) | reject (exit 1, worst_tv 1.0) | explicit caliber with per-element maps admits swap_ab/S3 (19/10 orbits), the fixed pads control passes (31 orbits); the pairs-pinned swap stays a non-symmetry (structure-only: yes) |

Notes on the `tcp` row: the state count includes 5 padding states required by
the engine's bit-string convention (16 total, 11 protocol states); the
remaining defendants in the case — a pointless swap and an absurd one — are
rejected under both standards (4/4 rows reject in `cases/tcp/expected.json`),
which is how the record shows the judge is not a rubber stamp. One edge in the
predecessor transcription was removed after edge-by-edge re-verification
(`SYN-SENT` on `CLOSE`: Figure 5 draws no such arrow and §3.10.4 says "delete
the TCB"); the correction is recorded in the model's transcription notes. The
`dhcp` row's verdict is data, not vibes: the two lease-renewal states share
the identical `DHCPACK/Record lease` completion label, yet even the relabel
reading rejects the swap, because `REBINDING` has no edge back to `RENEWING`.
The `imap` row is transcribed from RFC 3501's prose (its §3 has no figure);
every edge cites the sentence that states it. TCP defines no payoff, so the
case's reward layer is all zeros by design and every conclusion comes from
the transition layer (same for `dhcp` and `imap`).

Notes on the five incorporated rows (`raft-etcd` … `usb2-device-states`):
they come from the field-trial blind-test project, copied byte-identical
(this repo's receipts: `cases/<case>/expected.json` +
`verdicts/<case>.verdict.json`; the networkx columns reconcile
group-by-group with field-trial's sealed truth — `sealed/<case>.truth.json`,
sha256 pinned in that project's `sealed/_W3_manifest.json` — 15/15 groups
agree). `k8s-pod-lifecycle`, `tls13-handshake` and `usb2-device-states` each
carry a pads positive control (a padding-state swap: pass under both
standards, structure and labeled both yes — TRUE in
`cases/<case>/expected.json`); `hadoop-mr-task`'s third group is a control
(RUNNING ↔ KILL_WAIT, rejected); `raft-etcd`'s third group is the
relabel-declaration contrast (same permutation, relabel reading — still
rejected). The `hadoop-mr-task` row's relabel column shows worst_tv=0.75:
the FAILED/KILLED swap breaks only some of the real cells — recorded as the
data says, not a typo. The `tls13-handshake` case README (the hand-written
doc shipped with the case) says 20 cross-state branches (a per-cell count:
client 9 + server 11); counted per outcome branch — the same caliber as the
other rows — it is 22 (client 10 + server 12, recomputable from
`model.json`); this table uses the model-derived 22.

Notes on the `mini2048` row: the first real-system exercise of the engine's
**explicit** caliber (a declared per-action renaming — a board symmetry
renames the direction keys with the cells), and the source of this
repository's first reproduced engine finding (2026-11-03): the vendored
judge's explicit layer *then* applied one declared `action_map` to every
closed-group element *including the identity*, so on any model with
pairwise-distinguishable actions the identity element forced the identity
map and no non-trivial renamed-action symmetry could be admitted. The
rot90/flip/D4 groups here are true symmetries under per-element maps
(derived exhaustively and machine-asserted by the case generator).
**Resolved 2026-11-04**: the upstream per-element `action_maps` fix
(homomorphism law checked at load) was re-vendored, the group files declare
the per-element maps, and the explicit-caliber receipts
(`cases/mini2048/receipts/`, engine run without `--strict`) read **pass**
with `homomorphism_checked: full` — g1/g3/g4 admitted at 70/136/55 orbits
(compression 3.657×/1.882×/4.655×); g2/g5 stay rejected, g6 stays admitted,
and the identity-map control still rejects under the legacy single map
(deprecated, behavior unchanged). The relabel/fixed table columns did not
flip. The pads swap passes on the same model (exit 0), and the table's
relabel column for this case is the court-stamped relabel frame, which
resolves to the bitstring judge (actions-read-as-bit-flips) on a
4-action/8-bit model — a structural mismatch recorded as the diagnostic
column. Full diagnosis with the verified 8-element map table:
[cases/mini2048/README.md](cases/mini2048/README.md).

Notes on the `lightsout3` row (2026-11-04): the deterministic toggle core of
the Lights Out puzzle (Tiger Electronics handheld, 1995) transcribed at 3×3
— every generating rule cites Wikipedia's Gameplay/Strategy sentences and
Jaap's Puzzle Page in `model.json → meta.rules_with_citations`; the 3×3
board itself is a recorded variant boundary (the original is 5×5; the 3×3
lineage runs through Merlin's reissued Magic Square and the Lights Out
Cube's 3×3 faces). All 512 states are real — the 9×9 toggle matrix over
GF(2) has rank 9 (generator-asserted), so there are no padding states, no
self-loops, and no two states share a row. Rewards are all zero by design
(the source game has no score); the win condition (all lamps off) is a
terminal property recorded in `meta.win_condition`, so the adjudication
runs entirely on the transition layer. The defendant groups: g1 (rot90 +
per-element button maps, explicit) and g4 (full D4, the second non-trivial
positive control of this court) pass under their declared caliber (140 and
102 orbits, 3.657× and 5.020×), as does g5 — the direct product D4 × C2
(16 elements, 51 orbits, 10.039×), admitted because the all-lamps
complement commutes with every D4 element (generator-asserted). g2 (the
same rotation, buttons pinned) is refused: the naive structure-only arm
admits it, and the cell-by-cell ledger counts 12288 broken (state × event)
cells under the pinned reading. g3 — the all-lamps complement, fixed — is
the trivial positive control; deviation recorded honestly: this case has
no padding states to swap, so the complement map plays the role
`mini2048`'s pads swap plays there (ruled 2026-11-04: faithful
transcription outranks control-form symmetry). The relabel column here is
the court-stamped relabel frame resolving to the bitstring judge, which on
this 9-action/9-bit model derives the action renaming from the state
permutation itself — that derivation coincides with the forced per-element
button maps, so the column passes in step with the explicit receipts
(contrast `mini2048`, where 4 actions on 8 bits made the same frame a
structural mismatch). At 512 states the jury's automorphism-set
cross-check is skipped by the court's scale guard; the O(E) direct
edge-set check is the primary. Case write-up with the verified 8-element
map table: [cases/lightsout3/README.md](cases/lightsout3/README.md).

Notes on the `sliding2x3` row (2026-11-04): the deterministic slide core of
the sliding-puzzle family — the numbered n-puzzle member (15 puzzle / 8
puzzle; Klotski is the sliding-block cognate, listed among the sliding-puzzle
examples but not transcribed here: its unequal multi-cell pieces would need a
different state space) — transcribed at 2×3 (5 numbered tiles + 1 open
position); every generating rule cites Wikipedia's 15-puzzle lead/Solvability
sentences and the Sliding-puzzle lead in `model.json →
meta.rules_with_citations`; the 2×3 board is a recorded variant boundary (the
canonical n-puzzle is 4×4; "the 8 puzzle, which has 8 tiles in a 3×3 frame").
1024 states = 2^10: the 6! = 720 arrangements are the real states (state =
lexicographic rank of the arrangement); ranks 720..1023 are unused encoding
space — **304 padding states** (every action self-loops, reward 0), so real
states sit alongside real padding for the docket's pads control. Rewards are
all zero by design (the puzzle has no score); the win condition (tiles in
numerical order, open position last — arrangement (1,2,3,4,5,0), state 153)
is a goal property in `meta.win_condition`. The Johnson & Story parity split
(half of the starting positions unsolvable) is recorded, not repaired: both
classes are real states and BFS from the goal reaches exactly 360
(generator-asserted). The defendant groups: g1 (hflip + per-element direction
maps, explicit) and g4 (full V4 = C2 × C2, the third non-trivial positive
control of this court) pass under their declared caliber (664 and 484 orbits,
1.542× and 2.116×). V4 is machine-verified as the board's FULL geometric
group (all 720 cell bijections enumerated; exactly 4 preserve the adjacency
graph) — a third group structure, distinct from the D4 cases. g2 (the same
mirror, directions pinned) is refused: the naive structure-only arm admits
it, and the cell-by-cell ledger counts 1440 broken (state × event) cells
under the pinned reading. g3 — the swap of padding states 720 and 1023,
fixed — is the trivial positive control; the pads swap returns on this
docket after `lightsout3`'s no-padding entry (placement note recorded in the
case README: `mini2048` already pairs the explicit caliber with real padding
states and a pads control; this case pairs them again on V4). The relabel
column here is the court-stamped relabel frame resolving to the bitstring
judge, which on this 4-action/10-bit model reads actions as bit flips — a
structural mismatch recorded as the diagnostic column (same shape as
`mini2048`). At 1024 states the jury's automorphism-set cross-check is
skipped by the court's scale guard; the O(E) direct edge-set check is the
primary. Case write-up with the verified 4-element map table:
[cases/sliding2x3/README.md](cases/sliding2x3/README.md).

Notes on the `hanoi3` row (2026-11-07): the deterministic move core of the
Tower of Hanoi transcribed at 3 disks / 3 rods (A, B, C); every generating
rule cites Wikipedia's Tower-of-Hanoi lead/rules/objective/minimum-moves/
graph sentences in `model.json → meta.rules_with_citations`; the 3-disk
size is a recorded variant boundary (the source takes "a number of disks";
toy versions commonly have around 7 to 9). 32 states = 2⁵: the 3³ = 27
disk-to-rod assignments are the real states (state = the base-3 numeral
p0 + 3·p1 + 9·p2); ranks 27..31 are unused encoding space — **5 padding
states** (every action self-loops, reward 0), so the pads control continues
on this docket (after `mini2048`'s g6 and `sliding2x3`'s g3). Rewards are
all zero by design (the puzzle has no score); the win condition (the entire
stack on rod C, state 26) is a goal property in `meta.win_condition`, and
the model machine-asserts the source's arithmetic on every run: every real
state has exactly 3 legal ordered pairs except the three corner states,
which have 2 ("every node has three edges to other nodes, except the three
corner nodes, which have two"); BFS from the goal reaches all 27 real
states; the start-to-goal distance is exactly 7 = 2³ − 1 ("With three
disks, the puzzle can be solved in seven moves"). The actions are the six
**ordered rod pairs** (X, Y) — the docket's first entry whose action
semantics is an ordered pair rather than a named direction or button — so a
peg relabeling renames the actions with the rods: (X, Y) ↦ (πX, πY). The
defendant groups: g1 (the A↔B swap + per-element ordered-pair maps,
explicit) and g3 (the FULL peg-relabel group S3 = C3 × C2, order 6 — the
fourth non-trivial positive control of this court, the first non-abelian
one) pass under their declared caliber (19 and 10 orbits, 1.684× and
3.200×; Burnside: g1 real orbits (27+1)/2 = 14 — only the all-on-rod-C
state survives the A↔B swap — plus 5 pad singletons; g3 real orbits
(27+3)/6 = 5, sizes 3,6,6,6,6, plus 5 pad singletons). The generator
machine-verifies S3 dynamically: every one of the 6 rod permutations has
exactly one forced ordered-pair renaming (exhaustive over all 6! = 720
action permutations) and the six (π, ρ(π)) pairs satisfy the homomorphism
law over all 36 ordered pairs; two fake state maps that are not peg
relabelings (a disk swap; a disk cycle) admit no renaming at all. g2 (the
same swap, pairs pinned) is refused: the naive structure-only arm admits
it, and the cell-by-cell ledger counts 122 broken (state × event) cells
under the pinned reading. g4 — the swap of padding states 27 and 31,
fixed — is the trivial positive control (31 orbits, 1.032×). The relabel
column here is the court-stamped relabel frame resolving to the
**generalized** judge (six actions cannot be indexed as bit flips of a
5-bit state), which derives the renaming from the state permutation itself
— coinciding with the forced per-element maps — so the column passes in
step with the explicit receipts (contrast `mini2048`/`sliding2x3`, where
the same frame resolves to the bitstring judge and rejects as a
diagnostic). At 32 states the jury's automorphism-set cross-check runs
under the court's scale guard and enumerates 720 structural automorphisms
(6 real-state S3 relabelings × 5! padding permutations) against 120
labeled ones (5! padding permutations × identity on the real states) — an
independent machine verification that the labeled real state space's
automorphism group is exactly the rod-relabel group S3. Case write-up with
the verified 6-element map table:
[cases/hanoi3/README.md](cases/hanoi3/README.md).

## Which "identical"? — three questions

The whole docket hangs on one distinction: when a judge says "this renaming
preserves behaviour", it has assumed something about your **action (event)
names**.

1. **What is an action in your system?** An event arriving from outside
   (packet, message, timeout — named in a spec another party could quote):
   **fixed** territory. An instruction bound to a state coordinate ("flip
   switch a"): **relabel** territory.
2. **If the states were renamed, must the action labels follow?** If your
   logs, specs, and wire meanings stay honest only when labels travel with
   the states: **relabel**. If labels name external facts no internal
   renaming can touch: **fixed**.
3. **Would silent event-name rewriting corrupt anything published?** If a
   compression that quietly rewrites `rcv FIN` into `rcv ACK of FIN` would
   make your spec lie: **fixed**.

Run both standards when unsure (the court always does), and read the
disagreement as a finding. The long version — the poker-table intro, the three
questions, three worked examples read straight off the case receipts, a
one-page claim-to-verdict chart, and a term glossary — is
[docs/which-identical.md](docs/which-identical.md).

## Candidate discovery — the fourth capability

`python -X utf8 -m symmetry_court discover [--case NAME] [--all] [--cap N]
[--sealed-dir DIR]`

The court can now propose candidates as well as judge them. The proposal step
is deliberately scoped, and the scope is the same distinction the whole
repository turns on:

- **What it discovers:** fixed-caliber candidates only. Each model's
  transition table becomes a directed multigraph whose edges carry
  `(action, prob, reward)` labels; networkx's VF2 matcher enumerates the
  label-preserving automorphisms, pruned by a 1-WL color refinement in which
  edge labels participate. Event names stay pinned throughout — this is the
  `wuxing-gua@fixed` / `networkx@labeled` reading of the docket, applied to
  proposal instead of judgment.
- **What it refuses to discover:** action-renaming (relabel/explicit)
  candidates. "Which kind of sameness applies" is the case author's
  declaration, not a machine guess — the repository's core argument applies
  to the proposal step too. The engine's own group-finder covers the relabel
  family; the court's discover deliberately does not.
- **Explosion guard, honest by construction:** a large filler class can make
  automorphism enumeration explode (the TLS 1.3 case carries 15 padding
  states; its full fixed automorphism group has order 15! ≈ 1.3 × 10¹²).
  Enumeration therefore runs under a hard cap (`--cap`, default 2000). When
  the cap is hit, the receipt says so and reports: the group order as a lower
  bound (≥ cap); the 1-WL blocks as the orbit upper bound (every true orbit
  sits inside one block); and the orbits of the enumerated permutations as
  the orbit lower bound (each block is a proven symmetric set). Discrete
  refinement ⇒ the identity group. A capped case never reports an exact
  number it did not earn.
- **Gate arm:** each discovery is written as a replayable group file
  (`verdicts/discover.<case>.candidate.json`, semantics `fixed`) and passed
  through the vendored engine's `check --strict` — the same judge via an
  independent code path. A discovery the engine rejects is recorded as a
  failure, not smoothed over.
- **Reconciliation:** every receipt (`verdicts/discover.<case>.json`) checks
  the discovery against the case's own expected records (per-group direct
  criterion `multiset(trans[π(s)][a]) == multiset{(p, π(t), r)}` plus
  enumeration membership) and, for the five incorporated field cases, against
  the field-trial sealed truth (pass `--sealed-dir`): exact order equality
  wherever the enumeration completed; structural consistency notes where it
  capped.

Readings from the live receipts (regenerate with
`python -X utf8 -m symmetry_court discover --all`): the `tcp` case discovers
the full padding-swap group — order 120 = 5!, five padding states mutually
interchangeable, 12 orbits, refinement not discrete — while the shape-twin
`swap` is absent from the enumerated set (an exact absence, since the
enumeration completed; the direct criterion rejects it independently). Both
directions of that two-sided smoke contract are recorded in the receipt's
`smoke` block. The four large-filler cases (`dhcp`, `tls13-handshake`,
`mini2048`, `sliding2x3`) hit the cap and report lower bounds only; the
sealed truth's 15! for tls13 exceeds any reachable cap, which is exactly the
honest outcome. `lightsout3` completes exactly at minutes-scale — its state
graph is vertex-transitive (1-WL cannot split it, and indeed its fixed
automorphism group is the 512-element translation group, a single orbit).
Timing magnitude: most cases and all cap cases finish within seconds;
exact per-stage numbers live in each receipt's `timing_seconds`. The
12-case truth reconciliation (outcome: **0 false positives**; the
reconciliation table, per-case conclusions and honesty notes) is recorded
in [report/discover-audit.md](report/discover-audit.md) (Chinese twin
[report/discover-audit.zh-CN.md](report/discover-audit.zh-CN.md)), checked
against the pre-registered expectations in `verdicts/discover-baseline/`.

## Honest boundaries

- **Two different "discovers" — know which one you are running.** The
  engine's group-finder (`wuxing_gua discover`) proposes candidates under the
  relabel family of judges — it was built for coordinate-bound systems. The
  court's own `symmetry_court discover` takes the opposite scoping:
  fixed-caliber candidates only (see the section above). On an event-driven
  machine, treat any proposal as a lead, not a verdict: re-judge it under the
  fixed standard before any compression. The court's gate arm runs exactly
  that re-judging on every candidate it discovers.
- **A trivial group is the protocol's own property.** If the only symmetry
  found is the identity, that is not the judge failing: it says the
  protocol's own event structure already pins every state. TCP, read with
  event labels, is exactly such a system — worth knowing, not a defect.
- **Standards figures are often summaries.** TCP's Figure 5 omits the
  "RST from any state" transitions (its own Note 3 says so); those edges are
  *not collected*, and the omission is recorded in the case metadata instead
  of silently repaired.
- **Pass ≠ business blessing.** Every pass in every verdict file is scoped to
  the standard named in its column. The twins' relabel-column pass is real —
  and it is exactly the reading under which merging them would stop the
  machine being TCP.

## Contributing

New cases are the main contribution: pick a public standard, transcribe
edge-by-edge with citations, draft defendant groups (including one you expect
to lose), run the trial, land expected records, freeze it behind a
deterministic generator. The six-step process with the ground rules is in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Acknowledgments & sources

- **wuxing_gua judge engine** — vendored byte-for-byte, zero modification;
  the pinned source revision and provenance are recorded in
  [NOTICE](NOTICE). The engine is the same authors' own code and carries its
  own MIT license; it is zero-dependency (pure standard library).
- **networkx** — the independent jury, used in the arbitration arm only
  (BSD-licensed; the engine does not depend on it).
- **RFC 9293** (Transmission Control Protocol) — source of the `tcp` case,
  transcribed from §3.3.2 Figure 5.
- **RFC 2131** (Dynamic Host Configuration Protocol) — source of the `dhcp`
  case, transcribed from §4.4 Figure 5.
- **RFC 3501** (Internet Message Access Protocol, IMAP4rev1) — source of the
  `imap` case, transcribed from §3 (states) and §6 (per-state commands).
- **etcd-io/raft** (`raft.go`, pinned `c51f010c851e`) — source of the
  `raft-etcd` case, transcribed from the StateType enum and the step-function
  family (raft.go:49-56 et al.).
- **apache/hadoop** (trunk @ `e66f40daf3cc`) — source of the `hadoop-mr-task`
  case, transcribed from the state-machine factory in `TaskStateInternal.java`.
- **Kubernetes official docs** (Pod Lifecycle page) — source of the
  `k8s-pod-lifecycle` case, every edge citing the official wording.
- **RFC 8446** (TLS 1.3) — source of the `tls13-handshake` case, transcribed
  from Appendix A (§A.1/§A.2) with §4 as the normative anchor.
- **USB 2.0 specification** (USB-IF, §9.1) — source of the
  `usb2-device-states` case, transcribed from Figure 9-1 and Table 9-1.
- **Wikipedia, "Lights Out (game)"** and **Jaap's Puzzle Page, "Lights
  Out"** — sources of the `lightsout3` case, transcribed from the Gameplay
  and Strategy sentences with the 3×3 board size recorded as a variant
  boundary.
- **Wikipedia, "15 puzzle"** and **Wikipedia, "Sliding puzzle"** — sources
  of the `sliding2x3` case, transcribed from the lead and Solvability
  sentences with the 2×3 board size recorded as a variant boundary (Klotski
  is the sliding-block cognate of the same family).
- **the field-trial blind-test project** — transcription and two-round blind
  verification for the five cases above; the sealed-truth reconciliation is
  recorded in each case's `expected.json` provenance.

On positioning, stated plainly: within the sources we searched, we have not
seen a counterpart for this exact combination — public-standard state
machines tried under two named equivariance standards, with an independent
jury and replayable verdict files. If you know of one, we would genuinely
like to hear about it: open an issue.

- The judge engine is [wuxing-gua](https://github.com/cx2002302-lang/wuxing-gua) — the upstream project this courtroom instantiates; vendored byte-exact at 04cf0b6 (see [NOTICE](NOTICE)).
- The self-judgment guide for the two standards: [docs/which-identical.md](docs/which-identical.md) — two kinds of "the same" in plain language (poker-table swaps vs the TCP twins), the three questions, three receipt-backed examples from the docket (`tcp` fixed / `lightsout3` relabel / `mini2048` explicit), a one-page declare→dispatch→verdict chart, and a term glossary.
- The one-page illustrated results tour lives upstream: [docs/成果介绍-图解版.html](https://github.com/cx2002302-lang/wuxing-gua/blob/main/docs/成果介绍-图解版.html) in the [wuxing-gua](https://github.com/cx2002302-lang/wuxing-gua) repository — every number on that page reconciles with this court's receipts (`verdicts/comparison.*.json`).

## License

MIT — see [LICENSE](LICENSE). The vendored engine keeps its own MIT license
terms, recorded in [NOTICE](NOTICE).

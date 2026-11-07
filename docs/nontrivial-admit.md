# The Non-trivial Admit — a true symmetry the tool could not (yet) say yes to

*The account of the `mini2048` case: the explicit caliber's first real-system
filing, the mirror image of the TCP twin trial, and the engine limitation
the filing surfaced. Written 2026-11-03; the crew chief's ruling on the
finding was "record as observed, fix upstream next wave" — every row below
is recorded as observed. **2026-11-04: the limitation was fixed upstream
(per-element `action_maps` with the homomorphism law checked at load) and
the engine re-vendored; g1/g3/g4 flipped to pass under their declared
per-element maps — the flip hooks of §7 are cashed, and the 2026-11-03
records below are kept as history (honest tradition: findings stay on the
record).**

Every number in this document is backed by a receipt file in this
repository — the case file `cases/mini2048/` (model, groups, generator,
per-group engine receipts under `cases/mini2048/receipts/`), the trial
record `verdicts/mini2048.verdict.json`, and the gate-value ledger
`verdicts/comparison.mini2048.json` — and the gate
(`python -X utf8 -m symmetry_court selftest`; 320 contract fields replayed
green on 2026-11-03, re-verified green after the 2026-11-04 flip) re-verifies
the match on every run.

---

## 1. One-sentence summary

The docket's first non-trivial true-symmetry candidate case (2048-mini, D4)
is on file; its "should-admit" is machine-asserted by the case generator
(per-element map uniqueness plus the group homomorphism law, verified over
all 24 action bijections). On 2026-11-03 the engine's explicit caliber
still applied one declared action map to every closed-group element
including the identity, so the group was structurally rejected at the tool
layer; on 2026-11-04 the upstream per-element `action_maps` fix landed and
was re-vendored, and **g1/g3/g4 now pass under their declared per-element
maps** (live receipts; g2/g5 stay rejected, g6 stays admitted).

## 2. The mirror: TCP and 2048 fail in opposite directions

The twin trial ([twin-trial.md](twin-trial.md)) is the story of a tool that
says **yes** when the specification says **no**: TCP's `CLOSING` and
`FIN-WAIT-2` are structural twins, so a structure-only reading admits the
swap — while the event names (`rcv FIN` vs `rcv ACK of FIN`) say the two
states are strangers. Same shape, different events: the right verdict is
**reject**, and only the fixed (keys-pinned) caliber delivers it.

`mini2048` is the same lesson with the sign flipped. The 2×2 board's D4
symmetry is written into the game itself: rotate the board and the direction
keys rename with the cells — press what used to be "up" and the game runs
on untouched. Structure says **yes**, the keys-pinned reading says **no**
(and wrongly so, for this system), and the reading that says **yes**
correctly — the one where the renaming is declared, per element — is the
explicit caliber. Same shape, events that must rename: the right verdict is
**admit**, and only the explicit caliber can even ask for it.

| | TCP twins | 2048 board (D4) |
|---|---|---|
| structure-only reading | admits (wrong for the spec) | admits — and here that is *right* |
| keys pinned (`fixed`) | rejects — correct | rejects — the naive-intuition claim (`g2`) |
| renaming declared (`explicit`) | admits (wrong for the spec; TCP's relabel-column pass) | **should admit — the true symmetry** (machine-asserted; tool-rejected for now, §5) |

A tool that asks only one of these questions is wrong in one direction on
TCP and in the other on 2048. That symmetry of failures is why the court
always names the caliber — and why this docket needed a real system where
the **admit** side is the true one. Until this wave it had none: every
admission in the 8-case ledger was a padding-state swap
(`comparison.summary.json`: gate admits 6 of 26 groups in the pre-2048
ledger, all pads).

## 3. Why the 2048 board's D4 is a true symmetry

The case transcribes the deterministic core of the original open-source
2048 ([gabrielecirulli/2048](https://github.com/gabrielecirulli/2048), MIT)
as a 2×2 variant: 256 states (81 real + 175 padding), 4 actions (the arrow
keys in the original's own numbering, `game_manager.js` L131), the 2048
score as reward (+4 for the only allowed merge, L167); random spawns are
not collected (recorded in `meta.transcription_notes`). A board symmetry
π (one of D4's 8 elements) pairs with exactly one direction-key renaming
ρ(π): rotating the board clockwise by 90° turns "up" into "right", and so
on for every element. The pairing is not a free choice — it is **forced**,
and π ↦ ρ(π) satisfies the group homomorphism law ρ(gh) = ρ(g)∘ρ(h).

The generator (`cases/mini2048/make_mini2048.py`) does not take this on
trust: it exhausts all 24 bijections of the 4-key action set, asserts that
exactly one ρ(π) works for each of the 8 group elements, and asserts the
homomorphism law — on every run (`--check`, exit 0). The verified table is
printed in `cases/mini2048/README.md` (e.g. rot90cw: content map
[1,3,0,2], forced key map [1,2,3,0]; flip_tb: [2,3,0,1] with [2,1,0,3]).

So "rotate the board and rename the keys" is not an analogy; it is a
machine-asserted equivariance claim about a transcribed real system. Under
per-element action maps, g1 (the C4 rotation subgroup), g3 (the vertical
flip, order 2) and g4 (the full D4) are true symmetries.

## 4. What each reading says about it (all receipt-backed)

With event names pinned (`fixed`), rotating the board while "up" must stay
"up" is genuinely false: the cell-by-cell ledger counts **740** real
( state × event ) cells whose behaviour changes
(`verdicts/comparison.mini2048.json`, group `g2_rot90_nomap`,
`broken_real_cells_fixed`). The engine rejects `g2` — *correctly for the
question that caliber asks*. The fake control (`g5`, a single-row "mirror"
for which even the generator asserts no ρ exists) is rejected under both
readings, with an additional reward-profile failure (26/96 orbit pairs,
`receipts/check.g5_row_mirror_fake.json`). The padding swap `g6` passes
under `fixed` (exit 0, worst_tv 0.0) — the positive control showing the
model itself is well-formed.

The structure-only arm (edge-set invariance, the naive proxy) admits all
four true/false rotation-flip claims alike — it cannot tell g1 from g2,
because the difference lives entirely in the event names. The networkx
jury agrees on the shape question (`structure_symmetry: true` for
g1–g4 in `cases/mini2048/expected.json`, labeled: false).

And the explicit-caliber ledger says this about the real candidates —
**2026-11-04 state (live, receipts re-run against the re-vendored engine;
each element reconciles under its own declared map)**:

| group | declared caliber, cell-by-cell damage | engine explicit verdict |
|---|---|---|
| `g1_rot90_map` (C4) | 0 cells | **pass** (exit 0, worst_tv 0.0) |
| `g3_flip_map` (order 2) | **0 cells** | **pass** (exit 0, worst_tv 0.0) |
| `g4_d4_full` (D4) | 0 cells | **pass** (exit 0, worst_tv 0.0) |

History (2026-11-03 receipts, kept): with the then-only single-map
format the ledger read g1 = 500 cells, g4 = 1240 cells — what happens when
the file's single declared map is applied to *every* element of the closed
group — and the engine rejected g1/g3/g4 (3/4, 1/2, 7/8 elements failing,
each on the identity). The per-element `action_maps` fix removed the
degeneration: each element is now judged with its own derived ρ(π), the
ledger reconciles at zero everywhere, and the verdicts flipped. The
fixed-caliber contrast is still recorded per row
(`broken_real_cells_fixed`: g1=740, g3=130, g4=1480).

Compression readings, now **live** (admitted groups): g4 (full D4)
**4.655×** (55 orbits), g1 (C4) **3.657×** (70 orbits), g3 **1.882×**
(136 orbits) — exactly the numbers the flip hooks of §7 projected;
g2 stays rejected (740-cell damage under its keys-pinned claim), g5
rejected, g6 admitted at 1.004× (255 orbits).

## 5. The wall (2026-11-03, resolved 2026-11-04): one action map per group file, identity included

The engine's explicit judge used to check every element π of the closed
group against **one** declared map ρ: for all s, a — `π(T(s,a))` must equal
`T(π(s), ρ(a))`. Closure (`close_group`) always includes the identity.
For the identity element the condition degenerates to
`dist(s,a) = dist(s, ρ(a))` for all s, a — which, on any model whose
actions are pairwise behaviourally distinguishable (one tile on the board
suffices here), forces ρ = identity. But a rotation's map is not the
identity. Contradiction: **no** declared map could let a non-trivial
renamed-action symmetry through. This is precisely why the explicit
caliber had zero real-system samples until this case — and why the upstream
fix (2026-11-04) declares the maps **per element** (`semantics.action_maps`,
a list parallel to `elements`, homomorphism law ρ(g∘h) = ρ(g)∘ρ(h) checked
at load: all ordered pairs up to 500 elements, `homomorphism_checked` =
`full` on every group in this case).

The two-sided control pinned the diagnosis to the identity element, not to
a mistaken map (`receipts/`; 2026-11-03 record, control re-run live on
2026-11-04 against the fixed engine with the same outcome — legacy
single-map behavior unchanged):

- `g1` declared with the rot90 map [1,2,3,0]: **reject**, 3/4 elements
  fail, `first_bad` = the identity element (index 0);
- the same group declared with the identity map [0,1,2,3]
  (`check.control_g1_identity_map.json`): **reject**, 3/4 fail,
  `first_bad` = the rot90 element (index 1).

Whichever map you declared, the element it didn't fit failed first — the
exact fingerprint of the single-global-map design, not of a transcription
error. (During that wave's doc review the same reject was reproduced with
an ad-hoc identity-only group filed against this model under a non-identity
map — 1/1 elements fail — consistent with the argument above; that ad-hoc
probe is not a repository receipt, the two-sided control above is.) Under
the per-element format this degeneration cannot arise: the identity element
carries the identity map (validated at load) and every other element its
own ρ.

## 6. What the explicit caliber is for — and what this case gives it

The point of the explicit caliber is to turn "renaming knowledge" from
prose into a machine-checkable declaration: instead of arguing about
whether "the keys rename with the board", the case file asserts the
declaration and the engine checks the claim cell-by-cell at zero
tolerance. What this case added was the **first real-system instance of
that declaration** — plus the discovery (2026-11-03) that the then-current
schema (one map per group file) could not carry the per-element
information a real symmetry group needs. compare v2
(`symmetry_court/compare.py`) already respected the declaration: explicit
groups run as declared (no `--strict`), their ledger is kept in the
declared caliber, and the fixed-caliber contrast is recorded per row — so
when the engine gained per-element maps (2026-11-04), the ledger flipped
with only a declaration-form recognition added to compare
(`declared_action_map_kind: per_element`, per-element damage ledger); the
engine stayed the sole judge.

## 7. The flip hooks — cashed 2026-11-04 (upstream per-element action_maps fix)

The 2026-11-03 hook read: "the fix belongs to the upstream engine
(per-element `action_maps`, or deriving ρ(π) from declared generator maps
and verifying the homomorphism law); `vendored/` stays byte-identical this
wave. After the fix and re-vendoring, the expected state of this docket
is: g1/g3/g4 flip to **pass** under their declared per-element maps
(readings 3.657× / 1.882× / 4.655×), g2 and g5 stay **rejected** (the
keys-pinned and fake claims are genuinely false), g6 stays **pass**."
(Original text preserved above verbatim in this paragraph.)

**Cashed, 2026-11-04**: upstream commit "explicit caliber per-element
action_maps + homomorphism law" re-vendored (NOTICE manifest re-hashed,
30/30 byte-identical), group files upgraded to `action_maps` (generator
`--check` byte-identity green), live re-run: g1/g3/g4 **pass** (orbits
70 / 136 / 55; compression 3.657× / 1.882× / 4.655×; worst_tv 0.0;
`homomorphism_checked: full`), g2/g5 **reject** unchanged, g6 **pass**
unchanged, control unchanged (reject). The W2 acceptance corpus
(`w37_acceptance/run_acceptance.py` against the fixed engine): 7/7 PASS.
The docket rows in `README.md` / `README.zh-CN.md` and
`docs/闸门价值对比.html` carry the same flip.

## 8. Reading the receipts

- `cases/mini2048/model.json` — the transcribed machine; `meta.rules_with_citations`
  anchors every generating rule to the original source (`game_manager.js`
  line anchors, corroborated by Wikipedia's Gameplay text);
  `meta.per_element_action_maps` holds the 8 verified (π, ρ(π)) pairs;
  `meta.known_issue` records the finding and its 2026-11-04 resolution.
- `cases/mini2048/groups/g1…g6.json` — the defendants; g1/g3/g4 declare
  `explicit` with per-element `action_maps` (since 2026-11-04; previously
  the legacy single generator map), g2/g5/g6 declare `fixed`.
- `cases/mini2048/receipts/check.<group>.json` — one live engine receipt
  per group (run without `--strict`), plus
  `check.control_g1_identity_map.json` (the two-sided control of §5) and,
  since 2026-11-04, `check.<group>.strict.json` for the three fixed-declared
  groups (the --strict caliber receipt).
- `cases/mini2048/expected.json` — the court columns (relabel/fixed/
  networkx) per group, with per-row notes recording which rows flipped
  (g1/g3/g4's explicit-caliber receipts, cashed 2026-11-04) and which did
  not.
- `verdicts/mini2048.verdict.json` — the full trial record;
  `verdicts/comparison.mini2048.json` — the gate-value ledger rows quoted
  in §4; `verdicts/comparison.summary.json` — the docket totals (at this
  document's writing 9 cases / 32 groups; since 2026-11-04 the ledger also
  carries `lightsout3` — 10 cases / 37 groups, see §9 —,
  `sliding2x3` — 11 cases / 41 groups, see §10 —, since 2026-11-07,
  `hanoi3` — 12 cases / 45 groups, see §11 — and, since 2026-11-08, the
  three blind-trial round-2 cases — 15 cases / 57 groups, see §13).
- `cases/mini2048/README.md` (+ `README.zh-CN.md`) — the case's own
  diagnostic write-up, including the verified 8-element map table.

Engine exit codes: `0` pass, `1` reject, `2` sample shortfall (not used
here), `3` input or internal error.

## 9. The second non-trivial admit: `lightsout3` (2026-11-04)

The explicit caliber's second real-system filing — same group as this
case's (the full 8-element board group D4), different mechanism. Where the
2048 board's symmetry lives in the slide-and-merge direction rules, the
Lights Out board's symmetry lives in **toggle algebra**: a press is an XOR
flip of a button and its orthogonal neighbors ("Pressing any of the lights
will toggle it and the four adjacent lights." — Wikipedia, "Lights Out
(game)"), so rotating the board and moving the buttons with it commutes
with every press. The case transcribes the 3×3 deterministic variant of
the Tiger Electronics handheld (1995) with citations to Wikipedia and
Jaap's Puzzle Page; 512 states, all real (the 9×9 toggle matrix over GF(2)
has rank 9 — asserted by the generator — so there are **no padding
states**), rewards all zero by design (the source game has no score).

What the case adds, receipt-backed (`cases/lightsout3/receipts/`,
`verdicts/lightsout3.verdict.json`, `verdicts/comparison.lightsout3.json`;
gate replay: 370 contract fields green, 2026-11-04):

- **g4_d4_full (D4, 8 elements) — pass** under its declared per-element
  maps, worst_tv 0.0, `homomorphism_checked: full`: the second
  non-trivial positive control, after this case's g4. **102 orbits**
  (compression 5.020×) — computed live, not projected.
- **g1_rot90_map (C4)** — pass, **140 orbits** (3.657×).
- **g5_d4_x_c2 (D4 × C2, 16 elements)** — pass, **51 orbits**
  (10.039×): the all-lamps complement map π(s) = 511 ⊕ s commutes with
  every D4 element (generator-asserted per element), so the board group
  and the complement generate their direct product — geometric symmetry
  and toggle-algebra symmetry are independent here.
- **g2_rot90_nomap (fixed)** — reject, as it should be: with buttons
  pinned the claim is genuinely false, and the cell-by-cell ledger counts
  **12288** broken (state × event) cells (`broken_real_cells_fixed`,
  three rotation elements × 4096 each) — the naive structure-only arm
  admits this merge; the gate refuses it.
- **g3_complement (fixed, positive control)** — pass, 256 orbits
  (2.000×). Deviation recorded honestly: the trivial positive control is
  **not** a padding-state swap — this case has no padding states to swap
  (rank-9 toggle matrix); the complement map plays the same role this
  case's `g6_pads` plays there. Ruled 2026-11-04 during case engineering:
  faithful transcription outranks control-form symmetry.

The generator (`cases/lightsout3/make_lightsout3.py`) scales this case's
method to 9 buttons: exhaustive search over **all 9! = 362 880 button
permutations** asserts exactly one ρ(π) per element plus the homomorphism
law on every run (`--check`, exit 0); it also pre-registers the fake
control reading (a top-row-only mirror admits no ρ at all) without spending
a group file on it.

## 10. The third non-trivial admit: `sliding2x3` (2026-11-04)

The explicit caliber's third real-system filing, and a third group
structure: the 2×3 sliding-puzzle board (the numbered n-puzzle family —
15 puzzle / 8 puzzle; Klotski is the sliding-block cognate) is a non-square
rectangle, so its full geometric symmetry group is the Klein four-group
**V4 = C2 × C2** (identity, left-right mirror, top-bottom mirror,
180-degree rotation) — no 90-degree rotation exists. The generator
machine-verifies V4 as exactly the full geometric group by enumerating all
720 cell bijections against the adjacency graph (exactly 4 survivors), so
the docket now holds three distinct admitted structures: D4 (mini2048,
lightsout3), D4 × C2 (lightsout3's g5), V4 (this case). Where 2048's
symmetry lives in slide-and-merge direction rules and Lights Out's in
toggle algebra, the sliding puzzle's symmetry lives in **adjacency**: one
rule — a tile slides one grid step into the adjacent open position
("Tiles in the same row or column of the open position can be moved by
sliding them horizontally or vertically, respectively." — Wikipedia,
"15 puzzle") — and a board mirror carries its forced direction renaming
(left ↔ right for hflip; up ↔ down for vflip; both for rot180).

The case transcribes the 2×3 deterministic variant with citations to
Wikipedia's 15-puzzle and Sliding-puzzle articles; 1024 states = 2^10, of
which the 6! = 720 arrangements are real (state = lexicographic rank) and
304 unused ranks are **real padding states** (every action self-loops,
reward 0). Rewards all zero by design (the puzzle has no score); the
Johnson & Story parity split is recorded, not repaired (both classes are
real states; BFS from the goal reaches exactly 360, generator-asserted).

What the case adds, receipt-backed (`cases/sliding2x3/receipts/`,
`verdicts/sliding2x3.verdict.json`, `verdicts/comparison.sliding2x3.json`;
gate replay: 410 contract fields green, 2026-11-04):

- **g4_v4_full (V4, 4 elements) — pass** under its declared per-element
  maps, worst_tv 0.0, `homomorphism_checked: full`: the third non-trivial
  positive control. **484 orbits** (compression 2.116×) — computed
  live, not projected (Burnside: (720+0+0+0)/4 real orbits of size 4 —
  no V4 element fixes a real arrangement, distinct tiles cannot mirror
  onto each other — plus 304 fixed padding singletons).
- **g1_hflip_map (order 2)** — pass, **664 orbits** (1.542×).
- **g3_pads (fixed, positive control)** — pass, 1023 orbits (1.001×):
  the pads swap **returns** on this docket after lightsout3's no-padding
  case. Placement recorded honestly: mini2048 already pairs the explicit
  caliber with real padding states and a pads control (its g6); this case
  pairs them again on the V4 structure.
- **g2_hflip_nomap (fixed)** — reject, as it should be: with directions
  pinned the claim is genuinely false, and the cell-by-cell ledger counts
  **1440** broken (state × event) cells (`broken_real_cells_fixed`) —
  the naive structure-only arm admits this merge; the gate refuses it.

The generator (`cases/sliding2x3/make_sliding2x3.py`) runs this case's
method at 4 actions: exhaustive search over **all 4! = 24 direction
permutations** asserts exactly one ρ(π) per element plus the
homomorphism law on every run (`--check`, exit 0); it also pre-registers
the fake control readings (a cyclic column shift and a top-row left swap
admit no ρ at all) without spending group files on them.

## 11. The fourth non-trivial admit: `hanoi3` (2026-11-07)

The explicit caliber's fourth real-system filing, a fourth group
structure, and the docket's first entry whose **action semantics is an
ordered pair**: a Tower of Hanoi action is not a named direction or button
but the ordered pair of rods (X, Y) — "take the upper disk of rod X, place
it on rod Y" ("Each move consists of taking the upper disk from one of the
stacks and placing it on top of another stack or on an empty rod." —
Wikipedia, "Tower of Hanoi"). Rod names carry no geometry beyond their
identity, so every relabeling of the three rods preserves the mechanics:
the peg-relabel group is the full symmetric group **S3** (order 6: identity,
3 transpositions, 2 three-cycles) — the first non-abelian structure
admitted on this docket, after D4 (mini2048, lightsout3), D4 × C2
(lightsout3's g5) and V4 (sliding2x3). The source itself states the
symmetry in solution terms: *"the problem is symmetric for permutations of
the names of the pegs (symmetric group S3)."* A relabeling renames the
actions as ordered pairs (X, Y) ↦ (πX, πY), the renaming is forced per
element, and π ↦ ρ(π) is a group homomorphism.

The case transcribes the 3-disk deterministic variant with citations to
Wikipedia's Tower-of-Hanoi article; 32 states = 2⁵, of which the 3³ = 27
disk-to-rod assignments are real (state = the base-3 numeral p0 + 3·p1 +
9·p2) and 5 unused ranks are **real padding states** (every action
self-loops, reward 0). Rewards all zero by design (the puzzle has no
score); the win condition (the entire stack on rod C, state 26) is a goal
property in `meta.win_condition`. The generator machine-asserts the
source's arithmetic on every run: every real state has exactly 3 legal
ordered pairs except the three corner states, which have 2 ("every node
has three edges to other nodes, except the three corner nodes, which have
two"); BFS from the goal reaches all 27 real states; the start-to-goal
distance is exactly 7 = 2³ − 1 ("With three disks, the puzzle can be
solved in seven moves").

What the case adds, receipt-backed (`cases/hanoi3/receipts/`,
`verdicts/hanoi3.verdict.json`, `verdicts/comparison.hanoi3.json`;
gate replay: 450 contract fields green, 2026-11-07):

- **g3_s3_full (S3, 6 elements) — pass** under its declared per-element
  maps, worst_tv 0.0, `homomorphism_checked: full`: the fourth non-trivial
  positive control. **10 orbits** (compression 3.200×) — computed live,
  not projected (Burnside over the real states: identity fixes 27, each
  transposition fixes the 1 all-on-the-unswapped-rod state, each rotation
  fixes nothing, so (27+3)/6 = 5 real orbits of sizes 3,6,6,6,6, plus 5
  fixed padding singletons).
- **g1_swap_ab_map (order 2)** — pass, **19 orbits** (1.684×): real
  orbits (27+1)/2 = 14, plus 5 pad singletons.
- **g4_pads (fixed, positive control)** — pass, 31 orbits (1.032×): the
  pads swap continues on this docket after `mini2048`'s g6 and
  `sliding2x3`'s g3.
- **g2_swap_nomap (fixed)** — reject, as it should be: with the ordered
  pairs pinned the claim is genuinely false, and the cell-by-cell ledger
  counts **122** broken (state × event) cells (`broken_real_cells_fixed`)
  — the naive structure-only arm admits this merge; the gate refuses it
  (the docket's fifth harmful naive admit).

The relabel column reads differently from the previous two puzzle cases:
at 6 actions on a 5-bit model the court-stamped relabel frame resolves to
the **generalized** judge (six actions cannot be indexed as bit flips of a
5-bit state, so no bitstring reading arises), which derives the action
renaming from the state permutation itself — coinciding with the forced
per-element ordered-pair maps — so the column passes in step with the
explicit receipts (contrast `mini2048`/`sliding2x3`, where the same frame
resolves to the bitstring judge and rejects as a diagnostic). At 32 states
the jury's automorphism-set cross-check runs under the court's scale
guard: **720 structural automorphisms** (6 real-state S3 relabelings × 5!
padding permutations) against **120 labeled** ones (5! padding
permutations × identity on the real states) — an independent machine
verification that the labeled real state space's automorphism group is
exactly the rod-relabel group S3.

The generator (`cases/hanoi3/make_hanoi3.py`) runs this case's method at
6 actions: exhaustive search over **all 6! = 720 ordered-pair
permutations** asserts exactly one ρ(π) per element plus the homomorphism
law over all **36 ordered pairs** of S3 on every run (`--check`, exit 0);
it also pre-registers the fake control readings (a rod-wise disk swap and
a disk cycle admit no ρ at all — sizes are attached to disk identity, not
positions) without spending group files on them, and cross-validates the
legal-move function against an independent stack-based implementation on
every (state, action) pair.

## 12. The automatic discovery arm — `discover`, the fourth capability (2026-11-07)

The court now proposes candidates as well as judging them, and the proposal
step is scoped by the same distinction this file turns on: **fixed-caliber
candidates only** (event names pinned — the model transition table becomes a
directed multigraph with `(action, prob, reward)` edge labels, networkx VF2
enumerates the label-preserving automorphisms, 1-WL edge-label refinement
prunes soundly, a hard cap of 2000 turns explosion into honest lower
bounds). Action-renaming (relabel/explicit) candidates — the declared
groups this file is about — remain the case author's declaration; the
machine does not guess them.

The full-docket run reconciled clean, case by case, against each case's
existing truth (per-case audit report:
[report/discover-audit.md](../report/discover-audit.md), Chinese twin
[report/discover-audit.zh-CN.md](../report/discover-audit.zh-CN.md);
pre-registered expectations in `verdicts/discover-baseline/`):

- **12/12 cases reconciled; 0 false positives** — all 8,786 enumerated
  permutations direct-checked against the sealed fixed criterion by an
  audit-side independent implementation, 0 violations;
- **7/7 set-level equalities** where the enumeration completed (four small
  incorporated cases equal to the sealed element sets; `tcp`/`imap`/
  `hanoi3` equal to the explicitly generated padding-class symmetric
  groups; `lightsout3` equal to the 512 XOR translations);
- **2 discrete cases** ⇒ identity groups (`hadoop-mr-task`, `raft-etcd`;
  the former is the docket's |Aut| = 1 anchor, sealed order equality);
- **9 cases auto-discover their pads class** (`tcp` 5! = 120, `dhcp`
  capped with the baseline certificate 8! = 40320, `imap` 4! = 24,
  `mini2048` capped with a 183-state free class — 175 padding states plus
  the 8 real absorbing dead boards this file's case carries,
  `sliding2x3` capped at 304, `hanoi3` 5! = 120, `k8s-pod-lifecycle`
  S3 of order 6, `tls13-handshake` capped on its 15 fillers,
  `usb2-device-states` 2);
- **1 case discovers a non-trivial fixed group beyond padding** —
  `lightsout3`, whose fixed automorphism group is exactly the
  512-element translation group C2^9 on the state space (a single orbit;
  the 1-WL refinement is one block because the graph is genuinely
  vertex-transitive — the exact order comes from enumeration);
- **4 capped cases** report lower bounds only (`dhcp`, `mini2048`,
  `sliding2x3`, `tls13-handshake` — the sealed 15! exceeds any reachable
  cap, which is the honest outcome);
- **44 declared groups consistent with their expected fixed rows** — every
  fixed-pass group admitted (or direct-criterion-proven at cap), every
  fixed-reject group independently rejected by the direct criterion; the
  tls13 partial enumeration fixes all 17 protocol states pointwise,
  matching the sealed isolated-filler decomposition.

The mirror image of this file's story holds on the discovery side too:
the explicit-caliber groups this file records (rot90 with renamed keys,
D4 with per-element button maps, V4, S3) were **not** discovered by the
machine under the fixed caliber — the direct criterion rejects each of
them there, which is the same fact the court's fixed column records. The
declaration does the work; the machine, on both arms, only ever verifies.

## 13. The blind-trial round 2: three externally transcribed cases join the docket (2026-11-08)

Where §9–§11 are positive controls authored in this repository, the
blind-test project's second round shipped three complete case files whose
transcription was finished before the tool receipts were opened:
`http2-stream-states` (RFC 9113 sec.5.1 stream states), `ppp-lcp` (RFC
1661 sec.4 option-negotiation automaton) and `bgp-fsm` (RFC 4271 sec.8
peer FSM). Each case was judged, sealed against an independent
fresh-implementation oracle (write-once, frozen 2026-11-07), then
unsealed and reconciled: **12 candidate groups × 5 axes (fixed / relabel
/ binding / networkx-structure / networkx-labeled) = 60/60 AGREE, 0 false
positives, 0 false negatives**, and the expected rows reconcile
field-for-field with the tool receipts (96 fields, 0 mismatches). On
2026-11-08 the three cases were adopted into the docket byte-identical
(`cases/http2-stream-states/`, `cases/ppp-lcp/`, `cases/bgp-fsm/`; each
case README carries an Adoption section), and the gate now replays **570
contract fields over 15 cases** (each new case contributes 40). The
networkx columns are carried from that round's sealed truth with the
sourcing recorded in each `expected.json` provenance.

What the three cases add to this file's story:

- **A `semantics_duality` ruling on a role-mirror reading:
  `http2-stream-states`.** The claim group `endpoint-mirror` swaps the
  two endpoint roles (reserved (local) ↔ reserved (remote), half-closed
  (local) ↔ half-closed (remote)) and passes the relabel column (exit 0,
  worst_tv 0.0; the witness renaming is the full send↔recv frame mirror:
  send PP ↔ recv PP, send H ↔ recv H, send ES ↔ recv ES, send R ↔ recv
  R) while the fixed column rejects (exit 1, worst_tv 1.0; first
  violating cell (idle, send PP): with names pinned, idle → reserved
  (local) does not move while the mirror demands reserved (remote)); the
  juror splits the same way (structure yes / labeled no). This is the
  same verdict shape the docket already records for `tcp`'s twins
  (relabel pass / fixed reject) — with the opposite polarity: here
  the shared-diagram reading is the one the source itself writes (RFC
  9113 sec.5.1: "Both endpoints have a subjective view of the state of a
  stream"), so the endpoint-role mirror is a real symmetry of the
  unlabeled diagram and the frame-event naming is exactly where it
  stops. The gate-value ledger counts 12 real cells under the pinned
  reading — the naive structure-only arm admits this merge, the gate
  refuses it (the docket's sixth harmful naive admit, after the five of
  §2/§9/§10/§11).
- **Two honest negatives: `ppp-lcp` and `bgp-fsm`.** Each case's prose
  describes its twin pair in near-verbatim mirror sentences (RFC 1661
  sec.4.2's Ack-Received/Ack-Sent pair; RFC 4271's Connect/Active, which
  "run the same machinery" in the prose pattern), and each transcription
  refutes the reading: all three defendants per case reject under BOTH
  calibers, with the first violating cell recorded in the sealed truth
  (`ppp-lcp` ack-twins: (Stopped, RCR+) — the RFC table cell
  `irc,scr,sca/8`, re-checked against that project's RFC snapshot at
  line 746; `bgp-fsm` connect-active: (Idle, ManualStart)). The
  structure-only arm refuses these swaps too — they fail at the edge-set
  level, before event names even matter (18/23/18 and 7/11/16 broken
  cells under the pinned reading) — while each case's pads control still
  passes (1.067× / 1.143×), showing the pipeline admits a genuine
  symmetry on the same models. "The prose says twins" is exactly the
  kind of claim a court should test rather than grant, and the record
  now holds two cases where the rhetoric says twin and the data says no.

Receipts: `cases/<case>/expected.json` (with provenance),
`verdicts/<case>.verdict.json`, `verdicts/comparison.<case>.json` (the
round-2 cases are all fixed-declared groups — no explicit-caliber rows);
the round-2 unsealing reconciliation is the blind-test project's
`report/reconciliation.md`; the sealed truth files and their sha256
manifest live in that project's `sealed/` directory (write-once, frozen
2026-11-07T18:34:44Z). The three cases carry no
`verdicts/discover.<case>.json` receipts, so compare's discovery arm
records them n/a — compare never runs discovery itself.

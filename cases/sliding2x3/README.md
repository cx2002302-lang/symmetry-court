# Case `sliding2x3` — sliding-puzzle move mechanics, 2×3 deterministic variant

The third docket for the engine's **explicit** action caliber (state
permutation + declared per-element direction renaming), and the court's third
non-trivial positive control: the full 4-element rectangle group
**V4 = C2 × C2**, admitted with per-element action maps — a third group
structure on the docket, distinct from `mini2048`'s and `lightsout3`'s D4
(order 8) and `lightsout3`'s D4 × C2 (order 16): the 2×3 board is a
non-square rectangle, so no 90-degree rotation exists (machine-verified by
enumerating all 720 cell bijections against the adjacency graph). It is also
the docket entry that brings the **pads positive control back** among the
explicit-caliber cases: this transcription has 304 real padding states
(`lightsout3` had none — its deviation note records that gap; `mini2048`
pairs the explicit caliber with real padding states and a pads control too,
this case pairs them again on the V4 structure).

Regenerate everything:
`python -X utf8 cases/sliding2x3/make_sliding2x3.py --check` (byte identity +
exhaustive symmetry self-certification, exit 0).

## The model

The deterministic slide core of the sliding-puzzle family (the numbered
n-puzzle member — 15 puzzle / 8 puzzle; Klotski is the sliding-block cognate;
rules public). Every generating rule cites its primary source in
`model.json → meta.rules_with_citations`; the two rule sources are:

- Wikipedia, ["15 puzzle"](https://en.wikipedia.org/wiki/15_puzzle), lead:
  *"Tiles in the same row or column of the open position can be moved by
  sliding them horizontally or vertically, respectively."*; *"The goal of the
  puzzle is to place the tiles in numerical order (from left to right, top to
  bottom)."* — and Solvability: *"Johnson & Story (1879) used a parity
  argument to show that half of the starting positions for the n puzzle are
  impossible to resolve"*, *"on boards of size m × n, where m and n are both
  larger than or equal to 2, all even permutations are solvable"*.
- Wikipedia, ["Sliding puzzle"](https://en.wikipedia.org/wiki/Sliding_puzzle),
  lead: *"a combination puzzle that challenges a player to slide (frequently
  flat) pieces along certain routes (usually on a board) to establish a
  certain end-configuration"*; *"a sliding block puzzle prohibits lifting any
  pieces off the board"* — with Klotski listed among the examples of sliding
  puzzles.

- 1024 states = 2^10. The 6! = 720 arrangements of 5 numbered tiles + 1 open
  position are the real states (state = lexicographic rank of the
  arrangement; cells 0..5 row-major, value 0 = the open position); ranks
  720..1023 are unused encoding space = **304 padding states** (every action
  self-loops, reward 0 — same padding convention as
  `tcp`/`dhcp`/`imap`/`mini2048`). A slide rearranges tiles, so real states
  only reach real states (generator-asserted).
- 4 actions = the slide directions, indexed 0=up, 1=down, 2=left, 3=right.
  The direction names the motion of the **sliding tile** (a tile slides in
  that direction into the adjacent open position), so the open position moves
  one step in the opposite direction — recorded in `meta.action_names` and
  rule R1 (the source names no action numbering; the indices are this
  transcription's own convention). Edge census (machine-countable from
  `meta.edge_rule_tags`): 1680 slide edges (S), 1200 unavailable-direction
  no-op self-loops (I — a direction with no tile to slide changes nothing,
  the same convention as `mini2048`'s unavailable-direction self-loops), 1216
  padding self-loops (P = 304 × 4).
- Rewards all zero **by design**: the puzzle has no score (rule R4); the win
  condition — tiles in numerical order, open position last: arrangement
  (1,2,3,4,5,0) = state 153 — is recorded in `meta.win_condition` as a goal
  property, not a per-edge reward (same all-zero convention as
  `tcp`/`dhcp`/`imap`/`lightsout3`). The adjudication therefore runs entirely
  on the transition layer.
- Parity recorded, **not repaired** (rule R5): moves split the 720 real
  states into two invariant classes of 360 each (Johnson & Story 1879); both
  classes are real states of this model, and a BFS from the goal reaches
  exactly 360 (generator-asserted on every run). The class split is a
  property of the state space, not encoded as unreachable padding.
- Variant boundary (rule R6): the 2×3 board — the canonical n-puzzle is the
  4×4 fifteen puzzle ("15 square tiles numbered 1 to 15 in a frame that is 4
  tile positions high and 4 tile positions wide"); the 8 puzzle plays the
  same rules on 3×3 ("8 tiles in a 3×3 frame"); the m×n family with m, n ≥ 2
  is covered by the Johnson & Story theorem; initial-scramble randomness is
  not collected (rule R7).

## The board symmetry and the explicit caliber

The 2×3 board's symmetry group is the Klein four-group **V4 = C2 × C2**
(order 4): identity, left-right mirror (`hflip`), top-bottom mirror
(`vflip`), 180-degree rotation (`rot180`). A true board symmetry moves the
direction names with the cells: mirroring the board left-right turns "a tile
slides left" into "a tile slides right". Per group element π the direction
renaming ρ(π) is *forced*, and the map π ↦ ρ(π) is a group homomorphism.
`make_sliding2x3.py` derives ρ(π) for every V4 element by **exhaustive search
over all 4! = 24 direction permutations** (exactly one valid map per element
— asserted on every run) and asserts the homomorphism law over all 16
ordered pairs. The verified table (directions indexed 0=up, 1=down, 2=left,
3=right):

| element | content map (cells) | forced direction map (0..3) |
|---|---|---|
| id | [0,1,2,3,4,5] | [0,1,2,3] |
| hflip | [2,1,0,5,4,3] | [0,1,3,2] (left ↔ right) |
| vflip | [3,4,5,0,1,2] | [1,0,2,3] (up ↔ down) |
| rot180 | [5,4,3,2,1,0] | [1,0,3,2] (up ↔ down, left ↔ right) |

Also asserted by the generator: the full geometric group of the 2×3 board is
**exactly V4** — all 720 cell bijections are enumerated and exactly 4
preserve the adjacency graph (no 90-degree rotation exists on a non-square
rectangle); two fake transforms that are not board symmetries (a cyclic
column shift, a top-row left swap) admit **no** direction renaming at all —
the fake-control reading is pre-registered even though no group file is
spent on it (g2 covers the reject side of the docket).

## The pads positive control and the honest placement

The state encoding needs 2^10 = 1024 slots for 720 real arrangements, so 304
unused ranks are padding states (every action self-loops, reward 0). Two of
them (states 720 and 1023) have the same behavior shape — every action a
single self-loop with reward 0 — so their swap is a genuine symmetry under
the pinned-direction reading, filed as `g3_pads` (fixed, expected pass).

Placement recorded honestly during case engineering (2026-11-04): the pads
positive control returns on this docket after `lightsout3`, which has no
padding states at all (rank-9 toggle matrix — its deviation note records
that gap, ruled: faithful transcription outranks control-form symmetry).
`mini2048` already pairs the explicit caliber with real padding states and a
pads control (its `g6`); this case pairs them again on a third group
structure (V4). The V4 elements fix the padding region pointwise — unused
ranks are not board configurations (recorded in `meta.transcription_notes`) —
so every full-state orbit count is the real-state orbit count plus the 304
pad singletons.

## Verdicts (live, 2026-11-04)

Three-way arbitration (`python -X utf8 -m symmetry_court arbitrate`, receipt
`verdicts/sliding2x3.verdict.json`; ruling codes: 4 × `disagree` — the same
diagnostic split as `mini2048`, where the court-stamped relabel frame
resolves to the bitstring judge and disagrees with the structure-only
column; all fixed-column pairs agree):

| group | declaration | order | engine verdict (declared caliber) | reading | orbits (compression) |
|---|---|---|---|---|---|
| `g1_hflip_map` | explicit, per-element action_maps | 2 | **pass** (exit 0, worst_tv 0.0, homomorphism full) | hflip + renamed directions is a true symmetry | 664 (1.542×) |
| `g2_hflip_nomap` | fixed (directions pinned) | 2 | reject (exit 1, worst_tv 1.0) | the naive claim is genuinely false | 664 (1.542×) |
| `g3_pads` | fixed, positive control | 2 | **pass** (exit 0, worst_tv 0.0) | the two padding rows reference no direction | 1023 (1.001×) |
| `g4_v4_full` | explicit, per-element action_maps | 4 | **pass** (exit 0, worst_tv 0.0, homomorphism full) | main positive control: full V4 admitted | 484 (2.116×) |

Live engine receipts (`python -X utf8 -m wuxing_gua check` from `vendored/`,
explicit groups without `--strict`; `receipts/check.<group>.json`, plus
`--strict` doubles for the two fixed-declared groups) match the generator's
own orbit counts exactly: 664 / 1023 / 484.

Reading of the three columns: on this 4-action/10-bit model the
court-stamped relabel frame resolves to the bitstring judge, which reads
actions as bit flips — a structural mismatch for a direction-key system, so
the relabel column rejects all four groups as a diagnostic (contrast
`lightsout3`, where 9 actions = 9 bits made the bitstring derivation
coincide with the per-element button maps; same shape as `mini2048`). The
fixed column pins the directions and rejects every renamed-direction group
(g1/g2/g4) while admitting the pads swap (g3) — the caliber, not the
permutation, decides. The networkx columns mirror the split (structure yes /
labeled no for the mirror groups; both yes for the pads swap). At 1024
states the jury's automorphism-set cross-check is skipped by the court's
scale guard; the O(E) direct edge-set check is the primary. The cell-by-cell
ledger counts 1440 broken (state × event) cells under the
pinned reading for g2 (`verdicts/comparison.sliding2x3.json`,
`broken_real_cells_fixed`) — the naive structure-only arm admits it; the gate
refuses it.

## Files

- `make_sliding2x3.py` — deterministic generator; `--check` re-runs the
  symmetry self-certification (exhaustive 4! map derivation, homomorphism
  law, full-geometric-group = V4 proof, fake controls, pads/parity checks)
  and verifies byte identity of all 6 files.
- `model.json`, `expected.json`, `groups/g1…g4.json` — the case.
- `receipts/check.<group>.json` — live engine receipts (declared caliber),
  one per group; `receipts/check.g2_hflip_nomap.strict.json` and
  `receipts/check.g3_pads.strict.json` — `--strict` doubles for the
  fixed-declared groups.
- Court receipt: `verdicts/sliding2x3.verdict.json` (three-way arbitration).

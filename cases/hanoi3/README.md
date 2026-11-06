# Case `hanoi3` — Tower of Hanoi move mechanics, 3-disk deterministic variant

The fourth docket for the engine's **explicit** action caliber (state
permutation + declared per-element action renaming), and the court's fourth
non-trivial positive control: the FULL peg-relabel group **S3** (order 6),
admitted with per-element action maps — a fourth group structure on the
docket, distinct from `mini2048`'s and `lightsout3`'s D4 (order 8),
`lightsout3`'s D4 × C2 (order 16) and `sliding2x3`'s V4 (order 4), and the
first non-abelian one. It is also the docket's **first entry whose action
semantics is an ordered pair**: an action is not a named direction or button
but the ordered pair of rods (X, Y) — "take the upper disk of rod X, place
it on rod Y" — so a peg relabeling renames the actions as ordered pairs
(X, Y) ↦ (πX, πY). The pads positive control continues on this docket: this
transcription has 5 real padding states (`lightsout3` had none; `mini2048`
and `sliding2x3` pair the explicit caliber with a pads control too).

Regenerate everything:
`python -X utf8 cases/hanoi3/make_hanoi3.py --check` (byte identity +
exhaustive symmetry self-certification, exit 0).

## The model

The deterministic move core of the Tower of Hanoi (rules public). Every
generating rule cites its primary source in
`model.json → meta.rules_with_citations`; the source is:

- Wikipedia, ["Tower of Hanoi"](https://en.wikipedia.org/wiki/Tower_of_Hanoi),
  lead: *"a mathematical game or puzzle consisting of three rods and a number
  of disks of various diameters, which can slide onto any rod"*; rules:
  *"Only one disk may be moved at a time."*, *"Each move consists of taking
  the upper disk from one of the stacks and placing it on top of another
  stack or on an empty rod."*, *"No disk may be placed on top of a disk that
  is smaller than it."*; objective: *"The objective of the puzzle is to move
  the entire stack to one of the other rods"*; minimum moves: *"With three
  disks, the puzzle can be solved in seven moves. The minimum number of moves
  required to solve a Tower of Hanoi puzzle is 2ⁿ − 1"*; graph section:
  *"For a puzzle with n disks, there are 3ⁿ nodes in the graph"* and *"every
  node has three edges to other nodes, except the three corner nodes, which
  have two"*; symmetry: *"the problem is symmetric for permutations of the
  names of the pegs (symmetric group S3). If a solution is known moving from
  peg A to peg C, then, by renaming the pegs, the same solution can be used
  for every other choice of starting and destination peg."*

- 32 states = 2⁵. The 3³ = 27 disk-to-rod assignments are the real states
  (state = the base-3 numeral p0 + 3·p1 + 9·p2: the rod of disk 0/1/2, disk
  0 = smallest = least significant trit; rods A=0, B=1, C=2); ranks 27..31
  are unused encoding space = **5 padding states** (every action self-loops,
  reward 0 — same padding convention as `tcp`/`dhcp`/`imap`/`mini2048`/
  `sliding2x3`). A move rearranges disks among rods, so real states only
  reach real states (generator-asserted).
- 6 actions = the six **ordered rod pairs**, indexed 0=`A->B`, 1=`A->C`,
  2=`B->A`, 3=`B->C`, 4=`C->A`, 5=`C->B` (the source names no numbering; the
  indices are this transcription's own convention, recorded in
  `meta.action_names`). The pair (X, Y) is legal exactly when rod X is
  non-empty and rod Y is empty or Y's upper disk is larger (rules R1–R2); an
  unavailable pair is a no-op self-loop with reward 0 (rule R3 — same
  convention as `mini2048`'s unavailable-direction self-loops). Edge census
  (machine-countable from `meta.edge_rule_tags`): 78 legal-move edges (M),
  84 unavailable-pair self-loops (I), 30 padding self-loops (P = 5 × 6).
- Move census against the source's graph description (machine-asserted on
  every run): every real state has exactly **3** legal ordered pairs, except
  the three corner states (all disks on one rod: 0, 13, 26) which have
  exactly **2** — Wikipedia's *"every node has three edges to other nodes,
  except the three corner nodes, which have two."*
- Connectivity and optimality (machine-asserted on every run): a BFS from
  the goal reaches all 27 real states; the BFS distance from the standard
  start (every disk on rod A, state 0) to the goal (every disk on rod C,
  state 26) is exactly **7 = 2³ − 1** (*"With three disks, the puzzle can be
  solved in seven moves"*).
- Rewards all zero **by design**: the puzzle has no score (rule R4); the win
  condition — the entire stack on rod C, state 26 — is recorded in
  `meta.win_condition` as a goal property, not a per-edge reward (same
  all-zero convention as `tcp`/`dhcp`/`imap`/`lightsout3`/`sliding2x3`). The
  adjudication therefore runs entirely on the transition layer.
- Variant boundary (rule R6): the 3-disk instance — the source puzzle takes
  "a number of disks" and toy versions commonly have around 7 to 9; every
  cited rule sentence is size-independent except the 7-move minimum, which
  is the 2ⁿ − 1 law evaluated at n = 3.

## The peg symmetry and the explicit caliber

The rod names carry no geometry beyond their identity, so every relabeling
of the three rods preserves the move mechanics: the peg-relabel group is the
full symmetric group **S3** (order 6: identity, swaps A↔B / A↔C / B↔C,
rotations A→B→C→A / A→C→B→A). A true peg symmetry moves the ordered-pair
action names with the rods: swapping rods A and B turns the move `A->B` into
the move `B->A`. Per group element π the action renaming ρ(π) is *forced* —
ρ(π) maps each ordered pair (X, Y) to (πX, πY) — and π ↦ ρ(π) is a group
homomorphism. `make_hanoi3.py` derives ρ(π) for every S3 element by
**exhaustive search over all 6! = 720 ordered-pair permutations** (exactly
one valid map per element — asserted on every run) and asserts the
homomorphism law over all **36 ordered pairs** of S3 (plus the 4 of each
order-2 subgroup). The verified table (actions indexed as above):

| element | rod map π | forced ordered-pair map ρ (0..5) |
|---|---|---|
| id | (0,1,2) | [0,1,2,3,4,5] |
| swap_ab | (1,0,2) | [2,3,0,1,5,4] (A→B ↔ B→A, A→C ↔ B→C, C→A ↔ C→B) |
| swap_ac | (2,1,0) | [5,4,3,2,1,0] (every pair reversed with the A↔C swap) |
| swap_bc | (0,2,1) | [1,0,4,5,2,3] (A→B ↔ A→C, B→A ↔ C→A, B→C ↔ C→B) |
| rot_abc | (1,2,0) | [3,2,5,4,0,1] (each pair's rods advanced A→B→C→A) |
| rot_acb | (2,0,1) | [4,5,1,0,3,2] (each pair's rods advanced A→C→B→A) |

Also asserted by the generator: two fake state maps that are not peg
relabelings — swapping disks 0 and 1 rod-wise, and cycling disks 0→1→2→0 —
admit **no** action renaming at all (disk sizes are attached to disk
identity, not positions): the fake-control reading is pre-registered even
though no group file is spent on it (g2 covers the reject side of the
docket). The six actions are pairwise distinguishable on real states
(asserted), which is what forces each ρ to be unique.

## The pads positive control

The state encoding needs 2⁵ = 32 slots for 27 real arrangements, so 5 unused
ranks are padding states (every action self-loops, reward 0). Two of them
(states 27 and 31) have the same behavior shape — every action a single
self-loop with reward 0 — so their swap is a genuine symmetry under the
pinned-pair reading, filed as `g4_pads` (fixed, expected pass). Placement:
the pads control continues on this docket after `mini2048`'s g6 and
`sliding2x3`'s g3 (`lightsout3` has no padding states; its deviation note is
the honest record of that gap).

## Verdicts (live, 2026-11-07)

Three-way arbitration (`python -X utf8 -m symmetry_court arbitrate`, receipt
`verdicts/hanoi3.verdict.json`; ruling codes: 3 × `semantics_duality` +
1 × `agree`; all fixed-column pairs agree):

| group | declaration | order | engine verdict (declared caliber) | reading | orbits (compression) |
|---|---|---|---|---|---|
| `g1_swap_ab_map` | explicit, per-element action_maps | 2 | **pass** (exit 0, worst_tv 0.0, homomorphism full) | swap_ab + renamed pairs is a true symmetry | 19 (1.684×) |
| `g2_swap_nomap` | fixed (pairs pinned) | 2 | reject (exit 1, worst_tv 1.0) | the naive claim is genuinely false | 19 (1.684×) |
| `g4_pads` | fixed, positive control | 2 | **pass** (exit 0, worst_tv 0.0) | the two padding rows reference no rod | 31 (1.032×) |
| `g3_s3_full` | explicit, per-element action_maps | 6 | **pass** (exit 0, worst_tv 0.0, homomorphism full) | main positive control: full S3 admitted | 10 (3.200×) |

Live engine receipts (`python -X utf8 -m wuxing_gua check` from `vendored/`,
explicit groups without `--strict`; `receipts/check.<group>.json`, plus
`--strict` doubles for the two fixed-declared groups) match the generator's
own orbit counts exactly: 19 / 31 / 10 (Burnside cross-checked: g1 real
orbits (27+1)/2 = 14 — only the all-on-rod-C state is fixed by the A↔B swap
— plus 5 pad singletons; g3 real orbits (27+3)/6 = 5, of sizes 3,6,6,6,6,
plus 5 pad singletons).

Reading of the three columns: on this 6-action/5-bit model the
court-stamped relabel frame resolves to the **generalized** judge (six
actions cannot be indexed as bit flips of a 5-bit state, so no bitstring
reading arises), which derives the action renaming from the state
permutation itself — that derivation coincides with the forced per-element
ordered-pair maps, so the relabel column **passes in step with the explicit
receipts** (contrast `mini2048`/`sliding2x3`, where the same frame resolves
to the bitstring judge and rejects as a diagnostic; contrast `lightsout3`,
where 9 actions = 9 bits made the bitstring derivation coincide with the
per-element button maps). The fixed column pins the ordered pairs and
rejects every renamed-pair group (g1/g2/g3) while admitting the pads swap
(g4) — the caliber, not the permutation, decides. The networkx columns
mirror the split (structure yes / labeled no for the peg-swap groups; both
yes for the pads swap); at 32 states the jury's automorphism-set cross-check
RUNS under the court's scale guard and enumerates **720 structural
automorphisms** (= 6 real-state S3 relabelings × 5! padding permutations)
against **120 labeled** ones (= 5! padding permutations × identity on the
real states) — an independent machine verification that the labeled real
state space's automorphism group is exactly the rod-relabel group S3. The
cell-by-cell ledger counts **122** broken (state × event) cells under the
pinned reading for g2 (`verdicts/comparison.hanoi3.json`,
`broken_real_cells_fixed`) — the naive structure-only arm admits it; the
gate refuses it (the fifth harmful naive admit of the docket, after TCP's
twins and the three keys/direction-pinned rotations and mirror).

## Files

- `make_hanoi3.py` — deterministic generator; `--check` re-runs the
  symmetry self-certification (exhaustive 6! map derivation, homomorphism
  law over all 36 ordered pairs, two fake disk-map controls, move census,
  pads/parity/optimality checks) and verifies byte identity of all 6 files.
- `model.json`, `expected.json`, `groups/g1…g4.json` — the case.
- `receipts/check.<group>.json` — live engine receipts (declared caliber),
  one per group; `receipts/check.g2_swap_nomap.strict.json` and
  `receipts/check.g4_pads.strict.json` — `--strict` doubles for the
  fixed-declared groups.
- Court receipt: `verdicts/hanoi3.verdict.json` (three-way arbitration).

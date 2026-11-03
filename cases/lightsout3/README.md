# Case `lightsout3` — Lights Out toggle mechanics, 3×3 deterministic variant

The second docket for the engine's **explicit** action caliber (state
permutation + declared per-element button renaming), and the court's second
non-trivial positive control: the full 8-element board group **D4**, admitted
with per-element button maps — same group as `mini2048`'s, different
mechanism (toggle algebra instead of merge-and-slide).

Regenerate everything:
`python -X utf8 cases/lightsout3/make_lightsout3.py --check` (byte identity +
exhaustive symmetry self-certification, exit 0).

## The model

The deterministic toggle core of the Lights Out puzzle (Tiger Electronics
handheld, 1995; rules public). Every generating rule cites its primary
source in `model.json → meta.rules_with_citations`; the two rule sources are:

- Wikipedia, ["Lights Out (game)"](https://en.wikipedia.org/wiki/Lights_Out_(game)),
  Gameplay: *"Pressing any of the lights will toggle it and the four adjacent
  lights."*; *"The goal of the puzzle is to switch all the lights off,
  preferably in as few button presses as possible."* — and Strategy:
  *"the order in which the lights are pressed does not matter, as the result
  will be the same"*, *"pressing a light twice is equivalent to not pressing
  it at all"*.
- [Jaap's Puzzle Page, "Lights Out"](https://www.jaapsch.net/puzzles/lights.htm)
  (the rules page Wikipedia cites for the game): *"By pressing a button, its
  light and those of the (non-diagonally) adjacent buttons will change
  (switch on if it was off, and vice versa)."*

- 512 states = 2^9 (9 lamps × 1 bit, bit i = lamp i, 1=on / 0=off). **All
  512 are real states — there are no padding states**: the 9×9 toggle matrix
  over GF(2) has rank 9 (asserted by the generator on every run), so every
  configuration is reachable from the all-off state; every state has 9
  distinct active successors (zero self-loops — each toggle mask contains
  its own button bit) and no two states share a row. Contrast `mini2048`,
  where 175 of 256 states are padding.
- 9 actions = the 9 board buttons, indexed by position (button a sits on
  lamp a). The nine toggle masks are primary data, recorded in
  `meta.toggle_masks`.
- Rewards all zero **by design**: the source game has no score
  (`meta.rules_with_citations` R6); the win condition — all nine lamps off
  (state 0) — is recorded in `meta.win_condition` as a terminal property
  ("the device does not lock on winning"), not as a per-edge reward (same
  all-zero convention as `tcp`/`dhcp`/`imap`). The adjudication therefore
  runs entirely on the transition layer.
- Variant boundaries, recorded in `meta.transcription_notes`: the 3×3 board
  (the Tiger original is 5×5 — "The game consists of a 5 by 5 grid of
  lights"; the 3×3 lineage runs through Merlin's reissued Magic Square —
  "exactly the same as the standard Lights Out … a 3x3 Lights out", Jaap's
  page — and the Lights Out Cube's 3×3 faces); initial-board randomization
  not collected.

## The board symmetry and the explicit caliber

The 3×3 board's symmetry group is D4 (order 8). A true board symmetry moves
the buttons with the cells: rotating the board clockwise turns the top-left
button into the top-right button. Per group element π the button renaming
ρ(π) is *forced*, and the map π ↦ ρ(π) is a group homomorphism.
`make_lightsout3.py` derives ρ(π) for every D4 element by **exhaustive
search over all 9! = 362 880 button permutations** (exactly one valid map
per element — asserted on every run) and asserts the homomorphism law over
all 64 ordered pairs. The verified table (buttons indexed 0..8 row-major,
0=top-left, 4=center, 8=bottom-right):

| element | content map (cells) | forced button map (buttons 0..8) |
|---|---|---|
| id | [0,1,2,3,4,5,6,7,8] | [0,1,2,3,4,5,6,7,8] |
| rot90cw | [2,5,8,1,4,7,0,3,6] | [2,5,8,1,4,7,0,3,6] |
| rot180 | [8,7,6,5,4,3,2,1,0] | [8,7,6,5,4,3,2,1,0] |
| rot90ccw | [6,3,0,7,4,1,8,5,2] | [6,3,0,7,4,1,8,5,2] |
| flip_tb | [6,7,8,3,4,5,0,1,2] | [6,7,8,3,4,5,0,1,2] |
| flip_lr | [2,1,0,5,4,3,8,7,6] | [2,1,0,5,4,3,8,7,6] |
| transpose | [0,3,6,1,4,7,2,5,8] | [0,3,6,1,4,7,2,5,8] |
| antitrans | [8,5,2,7,4,1,6,3,0] | [8,5,2,7,4,1,6,3,0] |

(For a position-button system the content map and the button map coincide:
moving the lamps moves the crosses, so the button that toggles the moved
cross is the moved button.)

## The complement control and the no-padding deviation

Because toggling is XOR, the **all-lamps complement map** π(s) = 511 ⊕ s
commutes with every button press and renames nothing — a genuine symmetry
under the *fixed* caliber (buttons pinned).

Deviation from the `mini2048` pattern, recorded honestly: the trivial
positive control here is **not** a padding-state swap, because this case has
no padding states to swap (rank-9 toggle matrix — see above). The complement
map plays the same role `mini2048`'s pads swap plays there: an admitted
fixed-caliber symmetry that isolates caliber questions from model
well-formedness. Ruled 2026-11-04 during case engineering: faithful
transcription outranks control-form symmetry.

Structural observation (machine-asserted on every run): the complement
commutes with **every** D4 element, so the board group and the complement
generate the direct product **D4 × C2** (order 16) — filed as
`g5_d4_x_c2`, the largest group on the docket. Geometric symmetry and
toggle-algebra symmetry are independent here and their product is a
symmetry; the model's full automorphism inventory is larger still and no
group file claims to be it.

Also asserted by the generator: a top-row-only mirror (a structural mirror
that is not a board symmetry) admits **no** button renaming at all — the
fake-control reading is pre-registered even though no group file is spent
on it (g2 covers the reject side of the docket).

## Verdicts (live, 2026-11-04)

Three-way arbitration (`python -X utf8 -m symmetry_court arbitrate`, receipt
`verdicts/lightsout3.verdict.json`; ruling codes: 4 × `semantics_duality`,
1 × `agree`; all consistent pairs true):

| group | declaration | order | engine verdict (declared caliber) | reading | orbits (compression) |
|---|---|---|---|---|---|
| `g1_rot90_map` | explicit, per-element action_maps | 4 | **pass** (exit 0, worst_tv 0.0, homomorphism full) | rot90 + renamed buttons is a true symmetry | 140 (3.657×) |
| `g2_rot90_nomap` | fixed (buttons pinned) | 4 | reject (exit 1, worst_tv 1.0) | the naive claim is genuinely false — 3/4 elements fail | 140 (3.657×) |
| `g3_complement` | fixed, positive control | 2 | **pass** (exit 0, worst_tv 0.0) | the complement commutes with every press | 256 (2.000×) |
| `g4_d4_full` | explicit, per-element action_maps | 8 | **pass** (exit 0, worst_tv 0.0, homomorphism full) | main positive control: full D4 admitted | 102 (5.020×) |
| `g5_d4_x_c2` | explicit, per-element action_maps | 16 | **pass** (exit 0, worst_tv 0.0, homomorphism full) | D4 × C2 admitted — geometric ⊗ toggle-algebra symmetry | 51 (10.039×) |

Live engine receipts (`python -X utf8 -m wuxing_gua check` from `vendored/`,
explicit groups without `--strict`; `receipts/check.<group>.json`, plus
`--strict` doubles for the two fixed-declared groups) match the generator's
own orbit counts exactly: 140 / 256 / 102 / 51.

Reading of the three columns: on this 9-action/9-bit model the court-stamped
relabel frame resolves to the bitstring judge, which derives the action
renaming from the state permutation itself (buttons are bit positions) —
that derivation coincides with the forced per-element button map, so the
relabel column passes in step with the explicit receipts (contrast
`mini2048`, where 4 actions on 8 bits made the same frame a structural
mismatch). The fixed column pins the buttons and rejects every renamed-
button group (g1/g2/g4/g5) — the caliber, not the permutation, decides.
The networkx columns mirror the split (structure yes / labeled no for the
D4 groups; both yes for the complement). At 512 states the jury's
automorphism-set cross-check is skipped by the court's scale guard; the
O(E) direct edge-set check is the primary.

## Files

- `make_lightsout3.py` — deterministic generator; `--check` re-runs the
  symmetry self-certification (exhaustive 9! map derivation, homomorphism
  law, complement commutation, rank-9 no-padding proof) and verifies byte
  identity of all 7 files.
- `model.json`, `expected.json`, `groups/g1…g5.json` — the case.
- `receipts/check.<group>.json` — live engine receipts (declared caliber),
  one per group; `receipts/check.g2_rot90_nomap.strict.json` and
  `receipts/check.g3_complement.strict.json` — `--strict` doubles for the
  fixed-declared groups.
- Court receipt: `verdicts/lightsout3.verdict.json` (three-way arbitration).

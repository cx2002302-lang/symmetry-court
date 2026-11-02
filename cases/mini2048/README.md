# Case `mini2048` — 2048 merge mechanics, 2×2 deterministic variant

The first real-system sample for the engine's **explicit** action caliber
(state permutation + declared direction-key renaming) — and the case that
surfaced the first reproducible engine defect of this repository.

Regenerate everything:
`python -X utf8 cases/mini2048/make_mini2048.py --check` (byte identity +
exhaustive symmetry self-certification, exit 0).

## The model

The deterministic core of the original open-source 2048
([gabrielecirulli/2048](https://github.com/gabrielecirulli/2048), MIT):
slide + merge, no random tile spawns (not collected — randomness is outside
the deterministic FSM semantics). Every generating rule cites its
first-hand source in `model.json → meta.rules_with_citations`
(`js/game_manager.js` line anchors: `move()` L130-191, direction numbering
"0: up, 1: right, 2: down, 3: left" L131, merge condition L156, merged
value L157, score L167, no-op moves L175-177/L182, random spawn L182-183 +
L68-76, game-over L184-187/L238-268), corroborated by Wikipedia's Gameplay
sentences.

- 256 states = 2^8 (4 cells × 2 bits; per-cell encoding 0=empty, 1=value 2,
  2=value 4, 3=unused). 81 real states + 175 unreachable padding states
  (every action self-loops, reward 0).
- 4 actions = the arrow keys in the original's own numbering.
- Rewards = the 2048 score: +4 for the only allowed merge (2+2 → 4), 0
  otherwise (`score += merged.value`, game_manager.js L167). Variant boundary:
  a move with two 2+2 merges awards +4 flat (original per-merge sum would be
  +8); transitions identical, no verdict depends on it.
- Variant boundaries, recorded in `meta.transcription_notes`: merge capped
  at 4 (two 4s never merge here — the original merges any equal pair);
  random spawns not collected; dead boards self-loop on every action
  (that is what the original's `move()` computes for a move that changes
  nothing).

## The board symmetry and the explicit caliber

The 2×2 board's symmetry group is D4 (order 8). A true board symmetry
renames the four direction keys along with the cells: rotating the board
clockwise turns the "up" key into the "right" key. Per group element π the
renaming ρ(π) is *forced*, and the map π ↦ ρ(π) is a group homomorphism.
`make_mini2048.py` derives ρ(π) for every D4 element by exhaustive search
over the 24 action bijections and asserts uniqueness plus the homomorphism
law on every run. The verified table:

| element | content map (cells) | forced action map (up,right,down,left) |
|---|---|---|
| id | [0,1,2,3] | [0,1,2,3] |
| rot90cw | [1,3,0,2] | [1,2,3,0] |
| rot180 | [3,2,1,0] | [2,3,0,1] |
| rot90ccw | [2,0,3,1] | [3,0,1,2] |
| flip_tb | [2,3,0,1] | [2,1,0,3] |
| flip_lr | [1,0,3,2] | [0,3,2,1] |
| transpose | [0,2,1,3] | [3,2,1,0] |
| antitrans | [3,1,2,0] | [1,0,3,2] |

## The finding (2026-11-03; crew-chief ruling: record as observed, fix upstream next wave)

The vendored engine's explicit judge
(`vendored/wuxing_gua/core_check.py` L249-267 `_equiv_error_explicit`, wired
at L317-354 `_check_transition`) applies **one** declared `action_map` to
**every** element of the closed group — including the identity, which
`close_group` (L114-135) always adds and the full-element check always
tests (order ≤ 5000 → `all_elements`).

For the identity element the explicit check degenerates to
`dist(s,a) = dist(s, ρ(a))` for all s, a. On this model (as on any system
whose actions are pairwise behaviorally distinguishable — one tile on the
board separates every direction pair) that forces ρ = id. But the rot90
element requires ρ = [1,2,3,0] ≠ id. Contradiction: **no** declared map can
make a non-trivial renamed-action symmetry pass. That is why the explicit
caliber had zero real-system samples.

Live evidence (engine run with the court's own invocation
`python -X utf8 -m wuxing_gua check` from `vendored/`, no `--strict`;
receipts in `receipts/`):

| group | declaration | order | engine verdict | signature | orbits (compression) |
|---|---|---|---|---|---|
| `g1_rot90_map` | explicit, map of rot90cw | 4 | reject | 3/4 elements fail, `first_bad` = **identity** element, tv 1.0; reward layer passes (n_bad 0) | 70 (3.657×) |
| `g2_rot90_nomap` | fixed (keys pinned) | 4 | reject — *correct* | `first_bad` = rot90 element | 70 (3.657×) |
| `g3_flip_map` | explicit, map of flip_tb | 2 | reject | 1/2 fails, `first_bad` = **identity** | 136 (1.882×) |
| `g4_d4_full` | explicit, full D4 | 8 | reject | 7/8 fail, `first_bad` = **identity** | 55 (4.655×) |
| `g5_row_mirror_fake` | fixed, control | 2 | reject — *correct* | top-row-only mirror is in no caliber a symmetry (generator asserts no ρ exists at all) | 160 (1.600×) |
| `g6_pads` | fixed, padding swap | 2 | **pass** (exit 0, worst_tv 0.0) | positive control: model well-formed | 255 (1.004×) |
| control: g1 with identity map | explicit, [0,1,2,3] | 4 | reject | `first_bad` = rot90 element — closes the "wrong map" alternative | 70 |

Reading of the signatures: g1 fails on its own identity element (and g4 on
7/8), while the only element that passes under a generator's map is that
generator itself — the exact fingerprint of the single-global-map design
limitation, not of a transcription error. `g6_pads` passing on the same
model rules out model-level breakage.

**Consequence.** g1/g3/g4 are true symmetries under per-element action maps
(derived and machine-asserted); the engine's explicit layer rejects them
because its group format cannot express per-element maps. Their
explicit-caliber receipts are expected to **flip to pass** after the
upstream fix (per-element ρ(π) with the homomorphism law
ρ(gh) = ρ(g)∘ρ(h)); `g2`/`g5` are expected to stay rejected (fixed caliber),
`g6` to stay admitted. The relabel/fixed rows in `expected.json` answer
other calibers and are not expected to flip — each carries a `note` saying
so. `expected.json → groups.*.note` and
`model.json → meta.known_issue` point here.

## Files

- `make_mini2048.py` — deterministic generator; `--check` re-runs the
  symmetry self-certification and verifies byte identity of all 8 files.
- `model.json`, `expected.json`, `groups/g1…g6.json` — the case.
- `receipts/check.<group>.json` — live engine receipts (no `--strict`),
  one per group; `receipts/check.control_g1_identity_map.json` + 
  `receipts/_control_g1_identity_map.group.json` — the identity-map control
  experiment (temporary group file, kept as evidence, not part of the case).
- Court receipt: `verdicts/mini2048.verdict.json` (three-way arbitration).

## Upstream handoff

The fix belongs to the upstream engine (next wave, not this repository and
not `vendored/`): accept per-element action maps (e.g. `action_maps` aligned
with `elements`, or derive ρ(π) from a declared generator map by
composition and verify the homomorphism law). `mini2048` then serves as the
regression positive control: g1/g3/g4 flip to pass, g2/g5 stay rejected,
g6 stays admitted.

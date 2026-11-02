# The Non-trivial Admit — a true symmetry the tool could not (yet) say yes to

*The account of the `mini2048` case: the explicit caliber's first real-system
filing, the mirror image of the TCP twin trial, and the engine limitation
the filing surfaced. Written 2026-11-03; the crew chief's ruling on the
finding was "record as observed, fix upstream next wave" — every row below
is recorded as observed.*

Every number in this document is backed by a receipt file in this
repository — the case file `cases/mini2048/` (model, groups, generator,
per-group engine receipts under `cases/mini2048/receipts/`), the trial
record `verdicts/mini2048.verdict.json`, and the gate-value ledger
`verdicts/comparison.mini2048.json` — and the gate
(`python -X utf8 -m symmetry_court selftest`; 320 contract fields replayed
green on 2026-11-03) re-verifies the match on every run.

---

## 1. One-sentence summary

The docket's first non-trivial true-symmetry candidate case (2048-mini, D4)
is on file; its "should-admit" is machine-asserted by the case generator
(per-element map uniqueness plus the group homomorphism law, verified over
all 24 action bijections), but the engine's explicit caliber applies one
declared action map to every closed-group element including the identity,
so the group is structurally rejected at the tool layer — a finding of this
wave, with the fix scheduled upstream and g1/g3/g4 expected to flip to
admit afterwards.

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

And the explicit-caliber ledger says this about the real candidates:

| group | declared caliber, cell-by-cell damage | engine explicit verdict |
|---|---|---|
| `g1_rot90_map` (C4) | 500 cells* | reject — 3/4 elements fail |
| `g3_flip_map` (order 2) | **0 cells** | reject — 1/2 elements fail |
| `g4_d4_full` (D4) | 1240 cells* | reject — 7/8 elements fail |

\* The 500/1240 are what happens when the file's single declared map is
applied to *every* element of the closed group: the group-file format
cannot express "each element carries its own renaming", so executing the
file as written would change that many cells. The generator-matched pair
for each element is a different story: the rot90 element itself passes the
engine's equivariance check under its own map (see §5), and `g3` — whose
group has a single non-identity element, so the file's map *is* the
element's map — reconciles at **zero** broken cells: a real-system,
non-trivial (order-2) renamed-action symmetry that the cell-by-cell ledger
finds perfectly harmless, rejected by the tool anyway.

Compression readings if these groups were admitted: g4 (full D4)
**4.655×** (55 orbits), g1/g2 (C4) **3.657×** (70), g3 **1.882×** (136) —
the numbers the flip in §7 would cash in.

## 5. The wall: one action map per group file, identity included

The engine's explicit judge
(`vendored/wuxing_gua/core_check.py`, `_equiv_error_explicit`, wired in
`_check_transition`) checks every element π of the closed group against
**one** declared map ρ: for all s, a — `π(T(s,a))` must equal
`T(π(s), ρ(a))`. Closure (`close_group`) always includes the identity.
For the identity element the condition degenerates to
`dist(s,a) = dist(s, ρ(a))` for all s, a — which, on any model whose
actions are pairwise behaviourally distinguishable (one tile on the board
suffices here), forces ρ = identity. But a rotation's map is not the
identity. Contradiction: **no** declared map can let a non-trivial
renamed-action symmetry through. This is precisely why the explicit
caliber had zero real-system samples until now.

The two-sided control pins the diagnosis to the identity element, not to a
mistaken map (`receipts/`):

- `g1` declared with the rot90 map [1,2,3,0]: **reject**, 3/4 elements
  fail, `first_bad` = the identity element (index 0);
- the same group declared with the identity map [0,1,2,3]
  (`check.control_g1_identity_map.json`): **reject**, 3/4 fail,
  `first_bad` = the rot90 element (index 1).

Whichever map you declare, the element it doesn't fit fails first — the
exact fingerprint of the single-global-map design, not of a transcription
error. (During this wave's doc review the same reject was reproduced with
an ad-hoc identity-only group filed against this model under a non-identity
map — 1/1 elements fail — consistent with the argument above; that ad-hoc
probe is not a repository receipt, the two-sided control above is.)

## 6. What the explicit caliber is for — and what this case gives it

The point of the explicit caliber is to turn "renaming knowledge" from
prose into a machine-checkable declaration: instead of arguing about
whether "the keys rename with the board", the case file asserts
`semantics: {action: "explicit", action_map: [...]}` and the engine checks
the claim cell-by-cell at zero tolerance. What this case adds is the
**first real-system instance of that declaration** — plus the discovery
that the current schema (one map per group file) cannot carry the
per-element information a real symmetry group needs. compare v2
(`symmetry_court/compare.py`) already respects the declaration: explicit
groups run as declared (no `--strict`), their ledger is kept in the
declared caliber, and the fixed-caliber contrast is recorded per row — so
the day the engine gains per-element maps, the ledger flips without any
tooling change.

## 7. The flip hooks (wave 37)

The fix belongs to the upstream engine (per-element `action_maps`, or
deriving ρ(π) from declared generator maps and verifying the homomorphism
law); `vendored/` stays byte-identical this wave. After the fix and
re-vendoring, the expected state of this docket is: g1/g3/g4 flip to
**pass** under their declared per-element maps (readings 3.657× / 1.882× /
4.655×), g2 and g5 stay **rejected** (the keys-pinned and fake claims are
genuinely false), g6 stays **pass**. The pages that carry this story —
`docs/闸门价值对比.html`, the docket rows in `README.md` /
`README.zh-CN.md`, and this file — each need a one-line flip, already
marked in place.

## 8. Reading the receipts

- `cases/mini2048/model.json` — the transcribed machine; `meta.rules_with_citations`
  anchors every generating rule to the original source (`game_manager.js`
  line anchors, corroborated by Wikipedia's Gameplay text);
  `meta.per_element_action_maps` holds the 8 verified (π, ρ(π)) pairs;
  `meta.known_issue` records this finding.
- `cases/mini2048/groups/g1…g6.json` — the defendants; g1/g3/g4 declare
  `explicit` with their generator's map, g2/g5/g6 declare `fixed`.
- `cases/mini2048/receipts/check.<group>.json` — one live engine receipt
  per group (run without `--strict`), plus
  `check.control_g1_identity_map.json` (the two-sided control of §5).
- `cases/mini2048/expected.json` — the court columns (relabel/fixed/
  networkx) per group, with per-row notes on which rows are expected to
  flip and which are not.
- `verdicts/mini2048.verdict.json` — the full trial record;
  `verdicts/comparison.mini2048.json` — the gate-value ledger rows quoted
  in §4; `verdicts/comparison.summary.json` — the 9-case / 32-group totals.
- `cases/mini2048/README.md` (+ `README.zh-CN.md`) — the case's own
  diagnostic write-up, including the verified 8-element map table.

Engine exit codes: `0` pass, `1` reject, `2` sample shortfall (not used
here), `3` input or internal error.

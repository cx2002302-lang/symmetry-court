# Discover reconciliation baselines (draft)

Machine-readable expected facts for reconciling the docket's fourth CLI
capability, `discover`, against each case's existing truth. When discover
runs, it writes `verdicts/discover.<case>.json`; the reconciliation step
compares that output against the baseline in this directory.

These baselines are the **independent** side of the reconciliation. They are
derived from:

- the **sealed truth** of the field-trial blind-test project for the five
  incorporated cases (`hadoop-mr-task`, `k8s-pod-lifecycle`, `raft-etcd`,
  `tls13-handshake`, `usb2-device-states`) — sha256 pinned in that project's
  `sealed/_W3_manifest.json`, re-verified by the generator on every run;
- the **court receipts** (`cases/<case>/expected.json`, fixed rows and
  networkx labeled columns) for all twelve cases;
- **direct machine checks on the models** (`cases/<case>/model.json`).

No discover output is read. Every number in these files is either copied
from a source named in the file or machine-derived from such sources by the
generator (`tools/make_discover_baseline.py`).

## Honesty boundary

`discover` discovers candidate state symmetries only under the **fixed
caliber** (event names pinned). Action-renaming symmetries — the `explicit`
and `relabel` calibers — stay **author-declared**: the machine does not guess
"which sameness", and this baseline does not record them as discover targets.
Expected outcome on the real docket: padding-class symmetries are discovered
automatically; claim symmetries (false twins) are not discovered; any true
fixed-caliber group should be discovered. A declared group whose fixed row
passes must be **contained** in the discovered group; a declared group whose
fixed row rejects must **not be fully contained**.

## What each file records

`discover.<case>.expected.json`, one per case:

- `sources` — where every number comes from;
- `model_facts` — state/action/edge counts and the **uniform isolated free
  class**: states whose every action cell is exactly `[(1.0, self, 0.0)]`
  with no in-edge from any other state and no out-edge to any other state.
  Any permutation of this class is a fixed-caliber automorphism
  (`Sym(class) <= Aut`), the class is invariant under every automorphism,
  and group orders multiply across the split;
- `fixed_automorphism_expectation` — the expected group order (exact when
  sealed or machine-certified, otherwise a lower bound), a complement
  rigidity certificate, the expected 1-WL refinement behavior, the expected
  behavior at the discover enumeration cap (default 2000), and the expected
  state-orbit count;
- `declared_groups` — every group file's elements in cycle notation, each
  element machine-verified against the fixed criterion, the receipt's fixed
  row, and the admission expectation;
- `reconciliation_checks` — the named checks the reconcile step should run.

## Expectation table (numbers identical in both language versions)

| Case | States | Free class | `|Aut_fixed|` exact | Lower bound | Cap 2000 hit | 1-WL discrete | Orbits |
|---|---|---|---|---|---|---|---|
| `tcp` | 16 | 5 | 120 | 120 | no | no | 12 |
| `dhcp` | 16 | 8 | 40320 | 40320 | yes | no | 9 |
| `imap` | 8 | 4 | 24 | 24 | no | no | 5 |
| `mini2048` | 256 | 183 (8 of them real) | — | 183! | yes | no | 74 if complement rigid |
| `lightsout3` | 512 | 0 | 512 (`C2^9`) | 512 | no | no | 1 |
| `sliding2x3` | 1024 | 304 | — | 304! | yes | no | 721 if complement rigid |
| `hanoi3` | 32 | 5 | — | 120 | no | no | 28 if complement rigid |
| `raft-etcd` | 4 | 0 | 1 | 1 | no | yes | 4 |
| `k8s-pod-lifecycle` | 8 | 3 | 6 | 6 | no | no | 6 |
| `hadoop-mr-task` | 8 | 1 | 1 | 1 | no | yes | 8 |
| `tls13-handshake` | 32 | 15 | 1307674368000 (= 15!) | 1307674368000 | yes | no | 18 |
| `usb2-device-states` | 8 | 2 | 2 | 2 | no | no | 7 |

Exactness sources: the five incorporated cases carry the sealed group order;
`tcp`, `dhcp` and `imap` are pinned by the complement rigidity certificate on
top of their free class; `lightsout3` is pinned by its translation-group
certificate (below). The remaining three (`hanoi3`, `mini2048`,
`sliding2x3`) record the free-class lower bound only — their complements
have structure-only shadows that tie one-round signatures, so the discover
refinement and enumeration decide their complement factor.

## Three model facts worth calling out

- **`mini2048`'s free class is 183, not 175.** Eight *real* states behave as
  padding under the fixed criterion: the empty board and seven boards whose
  only merges are forbidden by the case's value cap. All eight have uniform
  isolated rows and zero in-edges (machine-checked exhaustively). This flips
  no recorded verdict — it extends the padding-equivalence story into real
  states, and the discovered group should reflect it.
- **`lightsout3` has no padding, yet `|Aut_fixed| = 512`.** All 4608 cells
  are single `(1.0, s xor mask_a, 0.0)` rows and the nine toggle masks have
  GF(2) rank 9, so any fixed automorphism `pi` satisfies
  `pi(s xor mask_a) = pi(s) xor mask_a` and is itself a translation —
  `Aut_fixed` is exactly the translation group `C2^9`, acting with one orbit
  of 512 states. All 512 translations were verified exhaustively. The
  declared `g3_complement` (the all-lamps flip) is one element of this
  group; the WL upper bound is loose here (all states are
  translation-tied), so enumeration — not refinement — pins the order.
- **`k8s-pod-lifecycle` is the argument for the dual-track design.** The
  sealed truth's own uniform-row heuristic reports a 5-state class
  (`k_factorial` 120), but the true free class is 3 (order 6): the other two
  uniform-row states are real absorbing states anchored by in-edges. A row
  heuristic alone overpredicts; this is why the design mandates enumeration
  plus labeled color refinement rather than either alone.

## Regenerate / check

```
python -X utf8 tools/make_discover_baseline.py            # (re)write the 12 files
python -X utf8 tools/make_discover_baseline.py --check    # byte-identity check
```

`--check` exits 0 when the twelve files regenerate byte-identical, 1 on
drift. `--sealed-dir` overrides the location of the field-trial blind-test
project's `sealed` directory (default: the sibling directory next to this
repository). The generator re-verifies the sealed files' sha256 against that
project's sealed manifest on every run and refuses to emit on mismatch.

## Reconciliation checks

For each case, the discover output should satisfy:

1. **order** — the discovered order (exact, or cap lower bound plus WL upper
   bound) is consistent with `order_exact` / `order_lower_bound`;
2. **admission** — every fixed-pass declared group is contained in the
   discovered group; every fixed-reject declared group is not fully
   contained;
3. **orbits** — the free class forms a single orbit; the orbit count is
   consistent with the expectation when the order is exact;
4. **discreteness** — the refinement report matches
   `wl_refinement_expected_discrete` (`hadoop-mr-task` and `raft-etcd` are
   the two discrete cases; `hadoop-mr-task`'s sealed truth is the
   |Aut| = 1 anchor);
5. **cap** — the cap-hit flag matches the expectation recorded per case.

## Status

Draft, written before the discover CLI lands. The baselines carry no timing
claims; all their checks are direct verifications over the model and group
files. The JSON files reference sources by repository-relative paths only.

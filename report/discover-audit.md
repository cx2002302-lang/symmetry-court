# Discover audit — the 12-case truth reconciliation

*2026-11-07. The `discover` capability (fixed-caliber candidate discovery)
ran over the full docket and its output was reconciled, case by case, against
each case's existing truth. **Outcome: 12/12 cases reconciled, 0 false
positives, 0 expectation mismatches.** Every number below is backed by a
receipt file in this repository or by the machine checks described in
§2 — none comes from memory.*

## 1. What was reconciled, against what

Two independent sides meet in this audit:

- **Side A — the discovery run.** `python -X utf8 -m symmetry_court
  discover --all --sealed-dir <field-trial blind-test project>/sealed`
  (exit 0). Per case it writes `verdicts/discover.<case>.json` (WL
  refinement, capped-or-exact enumeration, orbits, gate arm, per-group
  reconciliation, sealed-truth reconciliation) plus a replayable candidate
  group file `verdicts/discover.<case>.candidate.json` (semantics `fixed`),
  which the vendored engine's `check --strict` verifies as the gate arm.
- **Side B — this audit.** For every case the enumeration was re-run
  in-process (same cap 2000) to recover the *full* enumerated permutation
  set, and:
  1. **false-positive check** — every enumerated permutation was verified
     against the sealed fixed criterion
     `multiset(trans[π(s)][a]) == multiset{(p, π(t), r) : (p,t,r) ∈ trans[s][a]}`
     by an implementation written on the audit side (not the discover
     module's own);
  2. **set-level equality** — where the true group is pinned, the
     enumerated set was compared as a *set* against the expected group
     (sealed `fixed_aut_elements` for the four small incorporated cases;
     explicitly generated `Sym(free class)` for `tcp`/`imap`/`hanoi3`;
     the 512 translations `x ↦ x ⊕ v` for `lightsout3`);
  3. **declared-group admission** — every group file's elements against the
     expected.json fixed rows (direct criterion + enumeration membership);
  4. **receipt cross-check** — the stored receipts match the fresh run
     (order, truncation flag, WL blocks, orbit counts) 12/12;
  5. **baseline consistency** — the outcome was checked against the
     pre-registered expectations in `verdicts/discover-baseline/`
     (written before this run; see that directory's README for the
     honesty boundary of the baseline itself).

## 2. Reconciliation table

Orbit bounds at capped cases are printed `LB/UB`: the orbits of the
enumerated-permutation subgroup (each block a proven symmetric set) and the
1-WL blocks (each true orbit sits inside one block). `set=` is the audit's
set-level check for completed enumerations.

| Case | States | 1-WL blocks (discrete) | Enumerated | Capped | Order | Orbits | Gate arm | Sealed | set= |
|---|---|---|---|---|---|---|---|---|---|
| `tcp` | 16 | 12 (no) | 120 | no | **120** | 12 exact | pass | — | `Sym(5)` ✓ |
| `dhcp` | 16 | 9 (no) | 2000 | yes | ≥2000 (baseline certificate: 8! = 40320) | 10/9 | pass | — | ⊆ `Sym(8)` ✓ |
| `imap` | 8 | 5 (no) | 24 | no | **24** | 5 exact | pass | — | `Sym(4)` ✓ |
| `mini2048` | 256 | 62 (no) | 2000 | yes | ≥2000 | 242/62 | pass | — | 0 violations ✓ |
| `lightsout3` | 512 | 1 (no — vertex-transitive) | 512 | no | **512** | 1 exact | pass | — | 512 translations ✓ |
| `sliding2x3` | 1024 | 7 (no) | 2000 | yes | ≥2000 | 1018/7 | pass | — | 0 violations ✓ |
| `hanoi3` | 32 | 28 (no) | 120 | no | **120** | 28 exact | pass | — | `Sym(5)` ✓ |
| `raft-etcd` | 4 | 4 (**yes**) | 1 | no | **1** | 4 exact | pass | order equal ✓ | sealed elements ✓ |
| `k8s-pod-lifecycle` | 8 | 6 (no) | 6 | no | **6** | 6 exact | pass | order equal ✓ | sealed elements ✓ |
| `hadoop-mr-task` | 8 | 8 (**yes**) | 1 | no | **1** | 8 exact | pass | order equal ✓ | sealed elements ✓ |
| `tls13-handshake` | 32 | 18 (no) | 2000 | yes | ≥2000 (sealed: 15!) | 26/18 | pass | structural (capped) ✓ | 0 violations ✓ |
| `usb2-device-states` | 8 | 7 (no) | 2 | no | **2** | 7 exact | pass | order equal ✓ | sealed elements ✓ |

Totals: **8,786 enumerated permutations direct-checked, 0 violations**;
**7/7 set-level equalities hold**; **44 declared groups consistent with
their expected fixed rows**; **5/5 sealed reconciliations consistent** (four
exact order equalities, one capped with structural consistency — every one
of tls13's 2000 enumerated permutations fixes all 17 protocol states
pointwise, exactly the sealed isolated-filler decomposition); **12/12
receipts match fresh re-runs**.

## 3. One-line conclusion per case

- **`tcp`** — not discrete; **discovers the pads group** (the full 5!
  padding-swap group, 12 orbits); exact order 120; two-sided smoke contract
  holds (pads discovered / shape-twin `swap` provably absent, both
  directions recorded in the receipt's `smoke` block).
- **`dhcp`** — **capped** (≥2000; the baseline certificate pins the true
  order at 8! = 40320); discovers the pads class (8 uniform isolated
  padding states); 1-WL gives 9 blocks; orbit count bounded in [9, 10].
- **`imap`** — not discrete; **discovers pads** (exact 24 = 4!, 5 orbits).
- **`mini2048`** — **capped**; discovers the 183-state free class (175
  padding states *plus the 8 real absorbing dead boards* — the baseline
  expectation, confirmed live); 1-WL 62 blocks; orbits bounded in
  [62, 242]; the declared explicit-caliber groups are each rejected by the
  direct criterion under the fixed caliber (decisive regardless of the
  cap), and the declared pads swap is proven by the direct criterion —
  its absence from the partial enumeration is honestly recorded as
  inconclusive at cap.
- **`lightsout3`** — not discrete *because the truth is*: the state graph
  is vertex-transitive, and the discovered group is exactly the 512-element
  translation group `C2^9` (single orbit) — set-equal to the baseline's
  machine certificate, independently re-derived here by VF2.
- **`sliding2x3`** — **capped**; discovers the pads class (304 states);
  1-WL 7 blocks; orbits bounded in [7, 1018].
- **`hanoi3`** — not discrete; **discovers pads**; exact order 120 = 5!,
  set-equal to `Sym({27..31})`, 28 orbits — the baseline's conditional
  expectation (≥120, 28 orbits if the complement is rigid) is confirmed by
  the completed enumeration.
- **`raft-etcd`** — **discrete ⇒ identity group** (order 1); sealed order
  equality; the only content is 4 singleton orbits.
- **`k8s-pod-lifecycle`** — not discrete; **discovers pads** (S3 of order 6
  on the three free fillers); sealed order equality (the sealed truth's own
  row heuristic overpredicts 120 vs the true 6 — recorded in the baseline).
- **`hadoop-mr-task`** — **discrete ⇒ identity group** (order 1); sealed
  order equality; the |Aut| = 1 anchor of the docket.
- **`tls13-handshake`** — **capped** (the sealed 15! exceeds any reachable
  cap — the honest outcome); discovers the 15-filler pads class; all 2000
  enumerated permutations fix the 17 protocol states pointwise (0
  violations — structural agreement with the sealed decomposition); orbit
  count bounded in [18, 26] with the 1-WL upper bound matching the sealed
  decomposition's 18 orbits.
- **`usb2-device-states`** — not discrete; **discovers pads** (exact 2);
  sealed order equality.

Distribution: **2 discrete identity groups** (`hadoop-mr-task`,
`raft-etcd`); **9 cases discover their pads class** (`tcp`, `dhcp`, `imap`,
`mini2048`, `sliding2x3`, `hanoi3`, `k8s-pod-lifecycle`,
`tls13-handshake`, `usb2-device-states`); **1 case discovers a non-trivial
fixed group beyond padding** (`lightsout3`, the translation group);
**4 capped** (`dhcp`, `mini2048`, `sliding2x3`, `tls13-handshake`);
**0 false positives** — no case discovered a symmetry its truth does not
contain.

## 4. Honesty notes (recorded, not smoothed over)

- A capped case never reports an exact order: `dhcp`, `mini2048`,
  `sliding2x3`, `tls13-handshake` report lower bounds plus WL orbit upper
  bounds. Where an exact number is on record anyway (the baseline
  certificates, the sealed truth), the two sides are consistent.
- At cap, membership of a declared group in the enumerated set is recorded
  as inconclusive; the direct criterion is the decisive evidence in both
  directions (this is visible verbatim in the `mini2048` receipt).
- The sealed comparison for `tls13-handshake` records `order_matches: null`
  at cap (no contradiction is derivable) together with the structural
  consistency note — it does not pretend to a comparison it cannot make.
- The `lightsout3` 1-WL refinement is a single block spanning all 512
  states — a true reflection of the vertex-transitive translation group,
  not a tool failure; the exact order comes from enumeration, which the
  receipt's `timing_seconds` records at minutes scale for this one case
  (all other cases and all capped cases finish within seconds).

## 5. Reproduce

```
python -X utf8 -m symmetry_court discover --all --sealed-dir ../field-trial/sealed
python -X utf8 tools/make_discover_baseline.py --check     # baseline byte-identity
python -X utf8 -m symmetry_court selftest                  # 450 contract fields, exit 0
```

The candidate group files replay independently through the vendored engine:
`python -X utf8 -m wuxing_gua check --trans <case>/model.json --group
verdicts/discover.<case>.candidate.json --strict` (cwd `vendored/`).

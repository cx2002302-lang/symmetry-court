# Which "identical" do you mean?

A self-judgment guide for the two symmetry standards used in Symmetry Court.

**Who this is for.** You ran the court (or any equivariance judge) on your own
state machine, two columns disagreed, and now you want to know which column
describes *your* system — without reading a line of the judge's code.

**The whole issue in one sentence.** When a judge says "this renaming preserves
the system's behaviour", it has silently assumed something about your *action
names* — and there are two common assumptions, which give opposite answers on
the same machine.

---

## 1. Two kinds of "the same" — a poker table and a pair of twins

**The poker table.** Take two cards of the same rank from your hand — say the
queen of hearts and the queen of spades — and swap them. Nothing changes: every
rule that scores the hand reads only the rank, and both cards carry a queen.
The suit rides along, unseen, and may as well have been swapped with them.
"Identical" here means *interchangeable under the rules* — the rules never
consult the label that distinguishes the two cards, so the label is free to
travel. That is the spirit of the **relabel** reading: if everything the rules
measure survives the swap, the names may be renamed along with it.

**The TCP twins.** Open the TCP standard — RFC 9293, §3.3.2, Figure 5 — near
the end of the closing paths sit two states, `CLOSING` and `FIN-WAIT-2`, drawn
as near-perfect twins: one entrance and one exit each, both exits leading to
the same next state. Erase the event labels from the diagram and swapping the
two states maps the picture perfectly onto itself — they look exactly like the
two queens. But read the labels. One twin's exit is **the peer hung up on us**
(`rcv FIN`); the other's is **the peer confirmed our hang-up request**
(`rcv ACK of FIN`). These are not positions on a board — they are two different
facts about the world outside the machine, decided by the peer, named in a
specification another party quotes. A swap that quietly exchanges the two
events does not preserve TCP; it rewrites history and hopes nobody reads the
log. That is the **fixed** reading: event names name external facts, so they
stay put.

Same shape, opposite verdicts — because "the same" answers to two different
questions: *may the labels travel?* versus *are the labels nailed down?* The
rest of this page is how to tell, for your system, which question you are
actually asking.

---

## 2. The two definitions

Both definitions ask the same thing: does the state renaming `π` preserve the
transition table? They differ only in what happens to the action (event) name.

**fixed** — the action name must survive unchanged:

```text
π( T(s, a) )  =  T( π(s), a )          for every state s and action a
```

**relabel** — the action may be renamed along with the states (an action `b`
must exist at the renamed state; it does not have to be `a`):

```text
π( T(s, a) )  =  T( π(s), b )          for some action b, per (s, a)
```

Under `relabel`, a swap of two states is allowed to also swap the meanings of
events. Under `fixed`, events are nailed to the world outside the machine and
cannot be renamed at all.

Neither is "the strict one" and "the loose one" in any moral sense. They answer
different questions, and each is correct for one large class of systems — and
wrong for the other. (The docket also carries a third, **explicit** form: a
declared per-action renaming, §4 example C.)

---

## 3. The three questions

Ask them in order; the standard falls out.

**Q1 — Is an action bound to a state coordinate, or is it an external event?**

- An **event that arrives from outside** — a packet, a message, a timeout, a
  signal — something your specification or interop document names and another
  party could send: you are in **fixed** territory. TCP's `rcv FIN` is the
  canonical example: the peer decides when it arrives, and no renaming of
  TCP's internal states changes what a FIN is.
- An **instruction indexed by a state coordinate** — "flip switch a", "press
  button k", "toggle lamp j" — where the action's identity is bound to a
  position inside the state: you are in **relabel** territory. If you rename
  the switches, the instruction manual must be renamed with them, or every
  button label points at the wrong device.

**Q2 — If the states were renamed, should the action labels follow?**

Imagine a compression tool renames your states. Then look at your logs, your
spec text, your on-the-wire meanings:

- If the action labels **must be rewritten too** for all of that text to stay
  honest — the labels were coordinates, and coordinates travel with the map:
  **relabel**.
- If the action labels **must stay put** (they name external facts that no
  internal renaming can touch): **fixed**.

**Q3 — After the merge, who gets hurt?**

- If a compression that silently rewrites `rcv FIN` into `rcv ACK of FIN`
  would make your specification, your protocol analyzer, or your interop
  tests lie — the victims are everyone who consumes the published record:
  **fixed**.
- If your "actions" appear in no external contract (they are internal knobs of
  a simulation, a game, a scheduling model), nobody outside can be lied to,
  and the merge damage is measurable cell-by-cell on the transition table
  alone: **relabel** is not merely tolerable; it is the semantically correct
  reading.

Run both standards when unsure — the court always does — and read the
disagreement as a finding about your system, not as a malfunction.

---

## 4. Three minimal examples, read off the case files

All numbers below are read from receipt files in this repository —
`cases/<case>/expected.json` (the court's expected-verdict records, replayed
field-by-field by `selftest`), `verdicts/*.verdict.json` (the trial records),
and `verdicts/comparison.<case>.json` (the gate-value ledger). No number here
comes from memory.

### Example A — events: the TCP twins (fixed is the honest standard)

The claim (`cases/tcp/groups/swap.json`, 2 elements, declared
`semantics.action = fixed`): swap `FIN-WAIT-2` and `CLOSING` — the twin pair
of RFC 9293 §3.3.2 Figure 5. The model: 16 states (5 of them padding), 12
events (`verdicts/comparison.tcp.json`, summary). The receipts:

| receipt field | relabel frame (contrast copy) | fixed frame (the declaration) |
|---|---|---|
| exit | 0 | 1 |
| verdict | pass | reject |
| worst_tv | 0.0 | 1.0 |
| judge | generalized | strict |

Sources: `cases/tcp/expected.json`, row `swap`; `verdicts/tcp.verdict.json`,
`groups.swap`. The independent jury splits the same way the two standards do:
structure-only yes, event-labeled **no** — with event labels kept, the labeled
automorphism set over the non-padding states is the identity alone
(`verdicts/tcp.verdict.json`, `groups.swap.networkx`).

The relabel column's "pass" is exactly the two queens feeling: swap the states,
let the event names travel with them, and the picture closes. The fixed
column's "reject" is what reading the labels costs: under the pinned reading,
merging the twins would silently rewrite **6 of the case's 192 real
(state × event) cells** (`verdicts/comparison.tcp.json`, row `swap.json`,
`broken_real_cells_fixed`). Who gets hurt (Q3): every consumer of the TCP
spec — the merge turns "the peer hung up" into "the peer confirmed our
hang-up". The declared standard is fixed, and fixed binds: **reject** is the
verdict of record. This is the false-acceptance direction — relabel is the
wrong standard for a protocol, and it says pass.

### Example B — switches: the Lights Out board (relabel is the honest standard)

The claim (`cases/lightsout3/expected.json`, row `g1_rot90_map`): rotate the
3×3 board 90° clockwise and move the buttons with it — each button *is* a lamp
position, a state coordinate, so the true symmetry carries its own button
renaming. The model: 512 states, 9 buttons, rewards all zero
(`verdicts/comparison.lightsout3.json`, summary). The receipts:

| receipt field | relabel frame | fixed frame (buttons pinned) |
|---|---|---|
| exit | 0 | 1 |
| verdict | pass | reject |
| worst_tv | 0.0 | 1.0 |
| judge | bitstring | strict |

Sources: `cases/lightsout3/expected.json`, row `g1_rot90_map`. On this
9-action/9-bit model the relabel frame resolves to the bitstring judge, whose
renaming derived from the state permutation coincides with the declared
per-element button maps — so the relabel column passes in step with the
declared-caliber receipts (`cases/lightsout3/README.md` has the map table).
The ledger prices the two readings: merging under the **pinned** reading would
rewrite **12288** real (state × event) cells; under the **declared** reading,
**0** — and if the group is true, its 140 orbits over 512 states give a
compression reading of 3.657× (`verdicts/comparison.lightsout3.json`, row
`g1_rot90_map.json`: `broken_real_cells_fixed`, `broken_real_cells_declared`,
`would_be_orbits_if_merged`, `compression_if_true`). This is the
false-rejection direction — for a switch board, the fixed standard rejects a
swap any engineer knows is harmless, because "press button k" was fed to it
with the k's left in the old positions.

*(Contrast, same frame: `mini2048`'s relabel column reads **reject** as a
recorded diagnostic — there 4 direction keys cannot honestly be read as bit
flips of an 8-bit state, so the derivation misses. Same frame, two
resolutions; the declared caliber is what makes either readable.)*

### Example C — declared renames: the mini2048 direction keys (explicit)

The claim (`cases/mini2048/groups/g1_rot90_map.json`): rotate the 2×2 board
90° clockwise and rename the direction keys with the cells — the group file
*declares* the renaming per element (`semantics.action = explicit`, four
elements with `action_maps` `[[0,1,2,3], [1,2,3,0], [3,0,1,2], [2,3,0,1]]`:
the identity keeps every key, the rotation maps up→right→down→left→up, and so
on). The model: 256 states, 4 direction keys
(`verdicts/comparison.mini2048.json`, summary). The receipts, on three
readings of the same permutation:

| reading | receipt | result |
|---|---|---|
| declared explicit caliber | `cases/mini2048/receipts/check.g1_rot90_map.json` | **pass**, exit 0, `homomorphism_checked: full` |
| same rotation, keys pinned (`g2_rot90_nomap`, fixed) | `cases/mini2048/expected.json`, row `g2_rot90_nomap` | **reject**, exit 1, worst_tv 1.0 |
| court's relabel frame on this 4-action/8-bit model | `cases/mini2048/expected.json`, row `g1_rot90_map` | reject — recorded diagnostic, not expected to flip |

The ledger agrees with the declared reading: 740 real cells break under the
pinned reading, 0 under the declared one, 70 orbits over 256 states,
compression 3.657× (`verdicts/comparison.mini2048.json`, rows
`g1_rot90_map.json` / `g2_rot90_nomap.json`). The teaching point is the
permutation's sameness: the board rotation is *one* permutation, and it is
simultaneously a true symmetry (under the declared renames) and not a symmetry
at all (keys pinned). **The caliber, not the permutation, decides** — which is
why the court makes you declare it, and why the declared form carries its own
homomorphism check (the renamings must compose exactly as the group elements
compose).

---

## 5. Which standard, which system

| your system | actions are… | standard |
|---|---|---|
| protocol / interop state machine (TCP, DHCP, SMTP, TLS…) | external events, named in a public spec | **fixed** |
| switch board / milestone bits / puzzle coordinates | instructions bound to a state position | **relabel** |
| puzzle keys that genuinely travel with a declared board symmetry | renames you can write down per element | **explicit** |
| simulation with internal knobs | internal controls, no external contract | **relabel** |
| anything with both kinds mixed | — | run **both**; read the disagreement as a finding |

That last row is the honest one. Mixed systems exist, and for them no single
standard is "the answer" — the disagreement between the two columns is the
diagnostic.

---

## 6. From claim to verdict — the court on one page

```text
              your state machine + your symmetry claim
                                  |
    [0] SELF-JUDGE  (the three questions, §3)
          Q1  actions: state coordinates or external events?
          Q2  if the states rename, do the labels follow?
          Q3  after a merge, who gets hurt?
                                  |
                                  v
    [1] DECLARE    cases/<case>/groups/<g>.json
          "semantics": {"action": "fixed" | "relabel" | "explicit" (+ maps)}
          -- you declare; the machine never guesses
             (the discovery arm stays fixed-only for the same reason)
                                  |
                                  v
    [2] DISPATCH   the court runs BOTH standards on the same permutation
          +--------------------------------------------------+
          | wuxing-gua@relabel : b may be renamed with π     |
          | wuxing-gua@fixed   : b = a, event names pinned   |
          | networkx jury      : structure-only / labeled    |
          +--------------------------------------------------+
                                  |
                                  v
    [3] VERDICT    verdicts/<case>.verdict.json
          three columns + one agree/disagree line per defendant
          |-- standards agree  --> ruling "两口径一致" (agree)
          |-- standards differ --> ruling "口径二义" (semantics_duality):
          |        the DECLARED standard binds; the other column is the
          |        diagnostic -- and the disagreement is the finding
          '-- a column errs ----> recorded in the verdict, never smoothed
                                  |
                                  v
    [4] REPLAY     selftest re-runs every case and compares every contract
                   field against cases/<case>/expected.json
                   (the docket's gate line: 450 contract fields)
```

Two things the chart is doing on purpose. The declaration step (1) is where
§3's three questions get cashed: nothing downstream will guess the standard
for you. And the dispatch step (2) always runs *both* standards — even when
the declaration is unambiguous — so the column you did not choose is still on
the record as a diagnostic (that is exactly the pass sitting next to the
twins' reject in example A).

---

## 7. The court's terms, one line each

- **state** — one configuration the machine can be in; the docket's models
  encode states as bit-strings (TCP: 16 states, 5 of them padding fillers).
- **action / event** — the lever available in a state; externally an event a
  spec names (`rcv FIN`), internally a coordinate (`press button k`).
- **transition** — one table cell: (state, action) → its outcomes, each with
  probability, next state, and reward.
- **symmetry claim / defendant group** — a set of state permutations claimed
  to preserve behaviour, filed as `groups/<name>.json` and put on trial.
- **semantics declaration** — the group file's answer to "which identical?":
  `fixed`, `relabel`, or `explicit` (with the renames written out per
  element).
- **relabel** — π may rename actions along with states (§2, the traveling
  formula).
- **fixed** — event names pinned; π must work with the very same action names
  (§2, the pinned formula).
- **explicit** — a declared per-action renaming, one map per group element,
  the declaration itself part of the claim (example C).
- **homomorphism law** — the declared renamings must compose exactly as the
  group elements compose; the engine checks it at load (the mini2048 receipt
  records `homomorphism_checked: full`).
- **padding state** — an unreachable filler state the bit-string convention
  requires to reach a power of two (TCP carries 5; the engine's pad-aware
  mode knows to set them aside).
- **orbit** — the class of states a group merges into one; the rot90 group on
  mini2048 gives 70 orbits over 256 states.
- **worst_tv** — the largest mismatch the check measured (total variation
  between renamed and original behaviour); a pass requires it ≤ 1e-9 on every
  cell.
- **exit code** — the engine's three-valued honesty: 0 pass, 1 reject, 3
  input/internal error (2 = sample shortfall exists upstream but is not used
  by the court).
- **ruling code** — the court's per-defendant agree/disagree line: `agree`
  when the standards tell one story, `semantics_duality` when the column split
  is the caliber's doing (the twins' ruling).
- **contract field** — one replayable leaf of an expected record (exit,
  verdict, worst_tv, judge, and the networkx pair); the gate replays 450 of
  them across the docket on every run.

---

## 8. Further reading (all in this repository)

- The court's front door: [README.md](../README.md) — the docket table with
  every case's columns, and the quick start.
- The twins' full story: [twin-trial.md](twin-trial.md) — how the flagship
  case exposed the unnamed-standard gap that this page exists to close.
- The explicit caliber in practice: [nontrivial-admit.md](nontrivial-admit.md)
  — the mini2048 finding, and what admitting a declared rename costs.
- The three example cases as filed: [cases/tcp/](../cases/tcp/) (model,
  groups, expected records), [cases/lightsout3/](../cases/lightsout3/) and
  [cases/mini2048/](../cases/mini2048/) (plus their case READMEs with the
  verified per-element map tables).
- Adding your own case: [CONTRIBUTING.md](../CONTRIBUTING.md) — the six-step
  process; step 4 is where you write the semantics declaration this page is
  about.

---

## 9. Small print

- A "pass" always means: *structurally interchangeable under the named
  standard*. It is not a blessing to compress. You still have to pick the
  standard on purpose, with Q1–Q3.
- If the only symmetry a judge finds is the identity, that is not the judge
  failing. An automorphism group of size one says the system's own event
  structure already pins every state — a property of the protocol, worth
  knowing, not a defect to fix.
- The zero-damage of an admitted group is a property of the criterion, not a
  separately measured result: a pass *is* the statement that no cell moves
  (worst_tv ≤ 1e-9 on every cell). The evidence that the gate earns its keep
  lives in the damage ledger of the naive arm it refused
  (`verdicts/comparison.<case>.json`).

# Symmetry Court

[![CI: court selftest](https://img.shields.io/badge/court-selftest_pass-brightgreen)](https://github.com/cx2002302-lang/symmetry-court#quick-start) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Engine: wuxing-gua@e1b1fa8](https://img.shields.io/badge/engine-wuxing--gua%40e1b1fa8-grey)](NOTICE)

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
python -X utf8 -m symmetry_court selftest    # replay every verdict against expected (exit 0 = green)
```

(`python -X utf8` is the project's convention on Windows; elsewhere a plain
`python3 -X utf8` behaves the same.)

Arbitrate prints a verdict table to the console and writes the full trial
records to `verdicts/<case>.verdict.json`. Selftest is the gate: exit `0`
means every verdict in the repository still matches its expected record.

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

The docket holds 3 cases (receipt: `python -X utf8 -m symmetry_court list`
over `cases/`). Every number below is backed by the named receipt file in this
repository — no number here comes from memory.

| Case | Protocol | Source | States | Twin pair | relabel | fixed | networkx (labeled) |
|---|---|---|---|---|---|---|---|
| `tcp` | TCP connection state machine | RFC 9293 §3.3.2 Figure 5 | 16 states, 20 transitions, 12 events | CLOSING ↔ FIN-WAIT-2 | pass (exit 0, worst_tv 0.0) | reject (exit 1, worst_tv 1.0) | not a symmetry — identity only (structure-only: yes) |
| `dhcp` | DHCP client state machine | RFC 2131 §4.4 Figure 5 | 16 states (8 protocol + 8 padding), 18 transitions, 15 events | RENEWING ↔ REBINDING (decided by the transcription: not interchangeable) | reject (exit 1, worst_tv 1.0) | reject (exit 1, worst_tv 1.0) | not a symmetry (structure and labeled) |
| `imap` | IMAP4rev1 connection state machine | RFC 3501 §3 + §6 (prose spec, no drawn figure) | 8 states (4 protocol + 4 padding), 11 transitions, 6 events | AUTHENTICATED ↔ SELECTED (the SELECT/CLOSE 2-cycle) | reject (exit 1, worst_tv 1.0) | reject (exit 1, worst_tv 1.0) | not a symmetry (structure and labeled) |

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
disagreement as a finding. The long version, with two hand-checkable worked
examples, is [docs/which-identical.md](docs/which-identical.md).

## Honest boundaries

- **`discover` guards event-class systems.** The engine's group-finder
  (`discover`) proposes candidate groups under the relabel family of judges —
  it was built for coordinate-bound systems. On an event-driven machine,
  treat discover's proposals as leads, not verdicts: re-judge them under the
  fixed standard before any compression. The court's check columns exist
  precisely for that re-judging.
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

On positioning, stated plainly: within the sources we searched, we have not
seen a counterpart for this exact combination — public-standard state
machines tried under two named equivariance standards, with an independent
jury and replayable verdict files. If you know of one, we would genuinely
like to hear about it: open an issue.

- The judge engine is [wuxing-gua](https://github.com/cx2002302-lang/wuxing-gua) — the upstream project this courtroom instantiates; vendored byte-exact at e1b1fa8 (see [NOTICE](NOTICE)).

## License

MIT — see [LICENSE](LICENSE). The vendored engine keeps its own MIT license
terms, recorded in [NOTICE](NOTICE).

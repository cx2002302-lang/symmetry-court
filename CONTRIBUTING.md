# Contributing to Symmetry Court

The unit of contribution here is a **case**: one state machine transcribed from a
public standard, the symmetry claims put on trial against it, and the expected
verdicts that let anyone replay the trial. Everything else — the engine, the
jury, the verdict format — already exists; a new case only adds evidence.

Two ground rules before the steps:

- **The engine is frozen.** `vendored/` is a byte-identical copy of the
  wuxing_gua judge engine (see `NOTICE`). If you believe the engine is wrong,
  record the disagreement as a finding — never patch the vendored copy.
- **Numbers come from runs.** Every expected verdict, exit code, and count in a
  case file or in the READMEs must be backed by an actual run recorded in the
  repository (`cases/<name>/expected.json`, `verdicts/*.verdict.json`). Never
  write a number from memory.

## Adding a case — the six-step process

### 1. Pick a source you can cite to the clause

A case must come from a publicly checkable standard or specification — an RFC,
an ISO/IEEE/ITU document, anything a stranger can open and read. Note the exact
section and figure/table number (for example: RFC 9293 §3.3.2, Figure 5). If
you cannot pin the location, stop: no citation, no case. If you cannot confirm
the source within a fixed time budget, record that honestly (e.g. "no
qualifying source confirmed") instead of stretching a weaker one.

### 2. Transcribe edge-by-edge, cite every edge

Copy each transition (from-state, event, to-state) into the transcription, and
attach its clause reference. Transcription must not change semantics — if the
diagram and the prose disagree, transcribe what the standard actually says and
note the tension. If an edge is ambiguous, or the standard itself declares the
diagram incomplete (TCP's Figure 5, for instance, is a summary that omits the
"RST from any state" transitions), **leave that edge out and record it under
`meta.transcription_notes` as not collected**. An honest partial transcript
beats a plausible invented one.

### 3. Encode `model.json`

Write the model in the wuxing_gua trans format: `n_bits`, `n_actions`,
`n_states`, the transition table with **action (event) names**, rewards, goals,
plus `meta.source_system`, `meta.source_citation`, and human-readable
`state_names` / action names. Make every encoding decision explicit:

- padding states (the engine's bit-string convention may require padding up to
  a power of two — TCP needed 5 unreachable padding states to reach 16);
- rewards (if the standard defines no payoff, say so and set them to zero —
  the reward layer then carries no information, and every conclusion in the
  case comes from the transition layer alone).

### 4. Draft the defendants

One `groups/*.json` per symmetry claim, each with:

- `meta.claim` — the claimed symmetry in one plain sentence a non-mathematician
  can check ("swapping state X and state Y maps every transition onto a
  transition");
- a `semantics` declaration — for event-driven machines this is `fixed` (event
  names frozen). Do not leave the standard implicit: an undeclared semantics
  lets the engine guess one from the model's shape;
- include at least one group you **expect to be rejected**. A court that only
  hears winning claims is not a court; the rejected defendants are what show
  the judge is not a rubber stamp.

### 5. Run the trial, land `expected.json`

Run the engine under **both** standards (relabel and fixed) for every group,
and the networkx jury both ways (structure-only, and with event labels held
fixed). Record one row per group per standard in `cases/<name>/expected.json`:
`exit` / `verdict` / `worst_tv` / `judge`, plus the jury columns
(`structure_symmetry`, `labeled_symmetry`). These numbers must come from the
runs you just did — if a run disagrees with your intuition, the run wins and
your intuition gets rewritten.

### 6. Freeze it

- Write `make_<name>.py`, a deterministic generator for every file in the case
  directory, with a `--check` mode that re-generates and verifies
  byte-identity (see the generator style in the upstream engine's examples).
- Add the case to the case tables in **both** `README.md` and
  `README.zh-CN.md`, with the same numbers in both languages.
- Add the case's provenance to `NOTICE` if the source is new.
- Run `python -X utf8 -m symmetry_court selftest` from the repository root —
  it replays every verdict against its expected file and must exit 0.

## House rules

- Banned in all text, both languages: superlative-claim vocabulary — any
  wording asserting the work has no precedent, no equal, or arrives before all
  others (the bilingual list in the project charter). Positioning statements
  use the scoped form: *"within the sources we searched, we have not seen a
  counterpart for this combination."*
- No personal names, intranet hostnames, or private project names anywhere.
- Documentation is bilingual with parity: `README.md` (English) and
  `README.zh-CN.md` (Chinese) carry the same sections and the same numbers.
- Windows note: run everything as `python -X utf8 ...`.

If a step above conflicts with something you find in the repository, stop and
open an issue describing the conflict — the recorded receipts win over any
prose, including this file.

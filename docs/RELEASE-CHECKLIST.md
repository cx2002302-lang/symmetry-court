# Release Checklist — Symmetry Court v0.1.0

Every checked box below was executed on 2026-10-31 against this exact tree;
the command and its observed result are written next to it, so the checklist
itself is replayable. Unchecked boxes belong to the repository owner at push
time.

## 1. Gate (must be green before any push)

- [x] Full replay, official docket:
      `python -X utf8 -m symmetry_court selftest` → exit 0,
      `SELFTEST PASS（重放契约字段 110 个）` — 40 fields (dhcp) + 30 (imap)
      + 40 (tcp), all expected rows and saved verdict receipts field-by-field
      identical.
- [x] Full arbitration, official docket:
      `python -X utf8 -m symmetry_court arbitrate` → exit 0, all 3 cases
      tried, verdict files written to `verdicts/` (committed).
- [x] Smoke docket:
      `python -X utf8 -m symmetry_court arbitrate --cases-dir smoke` → exit 0;
      `python -X utf8 -m symmetry_court selftest --cases-dir smoke` → exit 0
      (40 fields).
- [x] Deterministic generators:
      `python -X utf8 smoke/tcp_smoke/make_tcp_smoke.py --check` →
      `byte-identity OK: 6 files`;
      `python -X utf8 cases/tcp/make_tcp.py --check` → byte-identity OK
      (model, expected, 4 groups).
- [x] One-command run: `run.bat` covers steps 1–6 above in order and exits 0.

## 2. Vendored engine integrity (charter: not one byte changed)

- [x] `vendored/` re-hashed file-by-file against the pinned source tree at
      commit `e1b1fa86b04cba2bd0001134bf3c33255a748d39` (source repo's
      `publish/` subdirectory, working tree clean): 30/30 identical
      (11 engine + 19 src), 0 mismatches, 0 missing, 0 extra files.
- [x] The gate re-verifies this on every run:
      `[vendored] OK：NOTICE 清单 30 文件逐一重算 sha256 一致，无清单外文件`.
- [x] Provenance, version pin, and manifest recorded in [NOTICE](../NOTICE).

## 3. Red lines (charter)

- [x] **Numbers are receipt-backed.** Every figure in both READMEs and in
      `docs/twin-trial.md` traces to `cases/*/expected.json`,
      `cases/*/model.json`, or `verdicts/*.verdict.json` — verified one by
      one on this date (states/transitions/events counts, exit codes,
      `worst_tv`, the tcp automorphism counts 2/240/1/120, the 4/4 rejected
      control rows). Spot-check set: 10 figures, all matched.
- [x] **Banned vocabulary absent (both languages).** Grepped every tracked
      file for first/novel/首创/state-of-the-art/unprecedented/no prior
      work/前所未有/首个/首次/开创/空前/独一无二: zero novelty claims in
      authored text. Positioning uses the scoped form ("within the sources
      we searched, we have not seen a counterpart for this exact
      combination"). Remaining unscoped novelty-claim hits: zero; residual literal-token
      hits are scoped, receipt-backed statements inside authored text, plus
      the byte-frozen vendored tree (e.g. the variable name `first_row` in the
      engine's circulant-matrix helper; 上游校准环境标签 SYS-1/SYS-2/SYS-3A
      in upstream research modules) — inherited verbatim from the pinned
      upstream release tree, which its own release scan (upstream
      `RELEASE-CHECK.md`) had already cleared for those categories; charter
      "not one byte changed" forbids editing them here.
- [x] **Desensitization.** Grepped tracked files against the six-category
      scan list — person names, internal codenames, project handles, local
      toolchain names, machine paths (both drive-root and user-profile
      forms), and the upstream project's own name variants — zero hits in
      authored text. Verdict records sanitize paths at write time
      (`symmetry_court/trial.py` `_sanitize`). `_rfc_scratch/` (local RFC
      texts used for verification) is `.gitignore`d and not committed.
- [x] **Case sources are public standards, cited per edge.** tcp ← RFC 9293
      §3.3.2 Figure 5 + Notes (each edge cites its clause; uncertain edges
      recorded as *not collected*); dhcp ← RFC 2131 §4.4 Figure 5; imap ←
      RFC 3501 §3 + §6. Citations spot-verified against the RFC texts.
- [x] **Bilingual parity.** README.md ↔ README.zh-CN.md: 9 sections, same
      order, same docket table, same numbers (one benign rendering
      difference: "the SELECT/CLOSE 2-cycle" ↔ "SELECT/CLOSE 双向环").
- [x] **Jury, not gatekeeper.** networkx is used in the arbitration arm only
      (`symmetry_court/trial.py`); the engine itself remains
      zero-dependency; the gate is `selftest`.

## 4. Packaging

- [x] `pyproject.toml` (name `symmetry-court`, version 0.1.0, requires
      Python ≥ 3.12, dependency: networkx; console script `symmetry-court`).
- [x] `LICENSE` (MIT, "Symmetry Court contributors"); vendored engine keeps
      its own MIT terms, recorded in [NOTICE](../NOTICE).
- [x] `README.md` (English, primary) + `README.zh-CN.md` (Chinese), cross-
      linked at the top.
- [x] `CONTRIBUTING.md` (six-step case process, house rules),
      `docs/twin-trial.md` (flagship narrative),
      `docs/which-identical.md` (standards-choice guide), `run.bat`
      (one-command gate), `.gitignore` / `.gitattributes` (byte-exact
      checkout).
- [x] Badge slot left as a placeholder for the owner to fill at release:
      `<!-- badges: placeholder — owner/repo filled at release -->`
      (README.md line 3; README.zh-CN.md line 3), plus the
      `https://github.com/cx2002302-lang/symmetry-court.git` clone URL in both
      quick starts.

## 5. Owner actions at push time (unchecked by design)

- [ ] Create the remote repository and push (the local repo is
      self-contained; no remote is configured here by policy).
- [x] Replace `cx2002302-lang` in both READMEs (clone URL) and fill the badge line — done at release (d1e8a67+badge commit)
      with the real owner/repo slug.
- [ ] Re-run `run.bat` after the badge edits and commit any resulting
      no-op diff confirmation.
- [ ] Tag the release (suggested: `v0.1.0`).

## 6. Wave addendum — 2026-11-03 (integration close-out, docket 9 cases / 32 groups)

- [x] 2026-11-03: full replay green — `python -X utf8 -m symmetry_court selftest` → exit 0, `SELFTEST PASS（重放契约字段 320 个）` (9 cases, incl. `mini2048` 60 fields); `arbitrate` → 9/9 verdicts written; `compare` (v2, caliber per group declaration) → 9 cases / 32 groups, 闸门价值一致性 PASS (gate admits 7, all zero-damage; old-8 per-case receipts zero-drift modulo gate seconds); smoke docket 40 fields PASS + `make_tcp_smoke.py --check` byte-identity OK; vendored 30/30 NOTICE sha256 unchanged; banned-vocabulary / internal-name greps clean in authored text (`docs/nontrivial-admit.md` records the `mini2048` finding: explicit caliber's first real-system sample, engine rejects pending upstream per-element-map fix).

## 7. Gate re-run SOP addendum — 2026-11-07 (selftest exit-1 anomaly, three clean re-runs, 12 cases / 450 fields)

Incident on record: a closure-gate run of `python -X utf8 -m symmetry_court
selftest` was logged with exit code 1 while its captured stdout was truncated
(no `FAIL` line visible); a later manual re-run with direct exit capture
exited 0 and the audit passed, leaving an unexplained contradiction.
Disposition on 2026-11-07, this tree: three consecutive clean re-runs, each an
isolated invocation with no pipe anywhere in the command line, stdout/stderr
redirected to files, `$?` read directly from the gate process —

- [x] run 1 → exit 0, 205 s wall, `SELFTEST PASS（重放契约字段 450 个）`, stderr 0 bytes
- [x] run 2 → exit 0, 206 s wall, `SELFTEST PASS（重放契约字段 450 个）`, stderr 0 bytes
- [x] run 3 → exit 0, 206 s wall, `SELFTEST PASS（重放契约字段 450 个）`, stderr 0 bytes

All three replayed all 12 cases field-by-field (40+30+40+30+30+50+60+30+40+
40+30+30 = 450 contract fields), verified 30/30 NOTICE sha256 entries, engine
version OK, and left the working tree untouched (receipt comparison is
read-only). Classification: the exit-1 record is not reproducible and is most
consistent with a capture artifact of the gate harness (piped invocation /
truncated log), not with a defect in the gate itself. The original record's
exact command line was not preserved, so a one-off transient cannot be fully
excluded from the surviving evidence; the protocol below makes any recurrence
diagnosable on the spot. No code change was needed or made — judgment
criteria untouched; `run.bat` audited and already clean (direct
`|| goto :fail` per step, no pipes).

### Gate re-run SOP (binding for every future gate run)

1. **Never take `$?` after a pipe.** In `cmd | tee f` or `cmd | tail …`, `$?`
   is the last pipeline element's status, not the gate's. Redirect instead:
   `python -X utf8 -m symmetry_court selftest > gate_stdout.txt 2> gate_stderr.txt`
   then read `$?` directly.
2. **Capture full stdout and stderr to files; never head/truncate them.**
   Failure details (`FAIL：…` lines, failing group/arm/field, per-case
   `[replay] case …` headers) are interleaved through the output and the
   summary is at the end; a head-only capture is what made the incident
   record undiagnosable.
3. **Record per run, verbatim:** exit code, wall time, the final summary line
   (`SELFTEST PASS/FAIL（重放契约字段 N 个）`), stderr byte count.
4. **On a non-zero exit, archive `gate_stdout.txt`/`gate_stderr.txt` before
   any re-run**, then read the failing branch (the `[replay] case X` header
   above the failure) and the failing cell (`group Y arm Z.field: expected …,
   replay …`).
5. **One exit-0 re-run does not close an exit-1 record.** Three consecutive
   clean runs are required; any non-zero among the three = real flake →
   root-cause before any gate claim.

Exit-code triage map (grounded in the current tree):

- exit 1, `FAIL：<N>/<M> 个契约字段不一致` → replay vs expected mismatch; the
  named `group Y arm Z.field` line identifies the cell. Live-flake cause to
  check by the clock: an engine arm subprocess timed out (per-arm limit
  300 s, `ENGINE_TIMEOUT_DEFAULT` in `symmetry_court/trial.py`; on timeout
  the arm record gets `engine timeout after 300s` and a null `verdict`, so
  the contract fields print as `expected 0, replay None`) — typical under
  heavy concurrent machine load. Fix direction: archive per-arm timings and
  evolve the `--timeout` value with a written precedent here; never edit
  `vendored/`.
- exit 1, `[engine] FAIL` → the engine `--version` probe failed (60 s probe
  timeout in `symmetry_court/trial.py` `_tools_block`).
- exit 1, `saved verdict file STALE/unreadable` → the committed receipt in
  `verdicts/` diverges from `expected.json` (re-mint with `arbitrate`), or
  was being rewritten concurrently while the gate read it — schedule gate
  runs so no second writer touches the repo at the same time.
- exit 1, `[vendored] FAIL` → NOTICE sha256 mismatch, missing file, or an
  extra non-`.pyc` file under `vendored/` (`vendor_check` in
  `symmetry_court/selftest.py`). Charter: stop and investigate, never patch
  vendored files in place.
- exit 1, `FAIL：重放失败/重放异常` → case-dir integrity (model.json or
  group files missing/unreadable) — static, not load-dependent.
- exit 3 → usage-level failure (0 cases tried / unknown case name); distinct
  from 1; a 0-case gate run never passes silently.
- There is no total wall-clock limit inside selftest; only per-engine-call
  timeouts apply. Observed full-replay wall time at a quiet load on the
  reference machine: 205–206 s (the three runs above).

Reference invocation (clean-protocol form):

    python -X utf8 -m symmetry_court selftest > gate_stdout.txt 2> gate_stderr.txt
    echo "exit=$?"

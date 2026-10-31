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
      combination"). Remaining literal-token hits live only inside the
      byte-frozen vendored tree (e.g. the variable name `first_row` in the
      engine's circulant-matrix helper; 上游校准环境标签 SYS-1/SYS-2/SYS-3A
      in upstream research modules) — inherited verbatim from the pinned
      upstream release tree, which its own release scan (upstream
      `RELEASE-CHECK.md`) had already cleared for those categories; charter
      "not one byte changed" forbids editing them here.
- [x] **Desensitization.** Grepped tracked files for person names, machine
      paths (`D:/`, `C:\Users`), and internal project identifiers
      (老徐/qywx/GameWXXX/team_battle/64卦/ZCode/AgentHome/WorkBuddy): zero
      hits in authored text. Verdict records sanitize paths at write time
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

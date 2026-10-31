# -*- coding: utf-8 -*-
"""
make_imap.py -- deterministic generator for the IMAP case: the four-state
connection state machine of IMAP4rev1 (RFC 3501), transcribed from the RFC
text for this repository.

Writes, byte-identical on every re-run (nothing random, no clock, no locale
dependence), next to this script:

  model.json                the trans model: 4 real states + 4 padding
                            states (2^3 input contract), 6 events, rewards
                            all zero
  groups/auth_selected.json defendant A: swap AUTHENTICATED <-> SELECTED --
                            the two states are joined by the mutually
                            inverse SELECT / CLOSE edges (a 2-cycle) and
                            both have LOGOUT exits: looks swap-friendly
  groups/notauth_auth.json  defendant B: swap NOT-AUTHENTICATED <-->
                            AUTHENTICATED (control lookalike)
  groups/pads.json          positive control: swap of two padding states

Transcription authority: RFC 3501 has NO drawn state diagram -- section 3
("State and Flow Diagram") specifies the four states in prose. The edge set
here is the flow reconstruction from section 3's entry conditions, section
6's per-state command lists, and the transition sentences of sections 6.4.2
(CLOSE) and 7.1.4 (PREAUTH). Every edge carries its quoting citation in
model.json (meta.edges_with_citations). Honest-transcription notes are in
meta.transcription_notes (greeting modeled as an event; STARTTLS excluded
by the RFC's own words; BAD/NO never change state).

State numbering: NOT-AUTHENTICATED=0, AUTHENTICATED=1, SELECTED=2, LOGOUT=3;
padding states 4..7.

Usage:
  python -X utf8 cases/imap/make_imap.py            # write all four files
  python -X utf8 cases/imap/make_imap.py --out DIR  # write into DIR
  python -X utf8 cases/imap/make_imap.py --check    # verify bytes, exit 0/1
"""
import argparse
import json
import os
import sys

STATES = ["NOT-AUTHENTICATED", "AUTHENTICATED", "SELECTED", "LOGOUT"]

C_ANY = "RFC 3501 sec.6.1 ('The following commands are valid in any state: CAPABILITY, NOOP, and LOGOUT.'); sec.3.4 ('entered as a result of a client request (via the LOGOUT command)')"
C_BYE = "RFC 3501 sec.3.4 ('or by unilateral action on the part of either the client or server'); sec.7.1.5 (BYE response)"

# (from, event, to, citation). Order fixes the action indices.
EDGES = [
    ("NOT-AUTHENTICATED", "AUTHENTICATE or LOGIN (OK)", "AUTHENTICATED",
     "RFC 3501 sec.6.2 ('In the not authenticated state, the AUTHENTICATE "
     "or LOGIN command establishes authentication and enters the "
     "authenticated state.'); sec.3.2 ('entered when ... acceptable "
     "authentication credentials have been provided')"),
    ("NOT-AUTHENTICATED", "PREAUTH greeting", "AUTHENTICATED",
     "RFC 3501 sec.3.1 (not authenticated state 'is entered when a "
     "connection starts unless the connection has been pre-authenticated'); "
     "sec.7.1.4 ('The PREAUTH response ... indicates that the connection "
     "has already been authenticated by external means; thus no LOGIN "
     "command is needed')"),
    ("AUTHENTICATED", "SELECT or EXAMINE (OK)", "SELECTED",
     "RFC 3501 sec.6.3 ('the following commands are valid in the "
     "authenticated state: SELECT, EXAMINE, ...'); sec.3.3 ('This state is "
     "entered when a mailbox has been successfully selected')"),
    ("SELECTED", "SELECT or EXAMINE (OK)", "SELECTED",
     "RFC 3501 sec.6.4.2 ('Even if a mailbox is selected, a SELECT, "
     "EXAMINE, or LOGOUT command MAY be issued without previously issuing "
     "a CLOSE command. The SELECT, EXAMINE, and LOGOUT commands implicitly "
     "close the currently selected mailbox') -- re-select stays selected"),
    ("SELECTED", "CLOSE (OK)", "AUTHENTICATED",
     "RFC 3501 sec.6.4.2 ('Result: OK - close completed, now in "
     "authenticated state' / 'returns to the authenticated state from the "
     "selected state'); sec.3.2 ('after a successful CLOSE command')"),
    ("NOT-AUTHENTICATED", "LOGOUT", "LOGOUT", C_ANY),
    ("AUTHENTICATED", "LOGOUT", "LOGOUT", C_ANY),
    ("SELECTED", "LOGOUT", "LOGOUT",
     "RFC 3501 sec.6.1 + sec.6.4.2 (implicit close) + sec.3.4"),
    ("NOT-AUTHENTICATED", "unilateral close (BYE)", "LOGOUT", C_BYE),
    ("AUTHENTICATED", "unilateral close (BYE)", "LOGOUT", C_BYE),
    ("SELECTED", "unilateral close (BYE)", "LOGOUT", C_BYE),
]

EVENTS = []
for _, ev, _, _ in EDGES:
    if ev not in EVENTS:
        EVENTS.append(ev)

N_BITS = 3
N_STATES = 1 << N_BITS          # 8 = 4 real + 4 padding
REAL_STATES = list(range(4))

TRANSCRIPTION_NOTES = [
    "no drawn diagram: RFC 3501 section 3 specifies the four states in "
    "prose only (despite the heading 'State and Flow Diagram' there is no "
    "figure). The edge set is the flow reconstruction from section 3's "
    "entry conditions, section 6's per-state command lists, and the "
    "transition sentences of sec.6.4.2 (CLOSE) and sec.7.1.4 (PREAUTH); "
    "every edge carries its quoting citation.",
    "modeling choice: the greeting is treated as an event received in the "
    "initial state -- a PREAUTH greeting moves the freshly started "
    "connection from not-authenticated to authenticated (edge 2 of "
    "EDGES). RFC wording quoted in that edge's citation.",
    "not collected: STARTTLS (sec.6.2.1: it 'does not establish "
    "authentication or enter the authenticated state' -- no state "
    "transition); command failures (sec.6 intro: 'A rejected command (BAD "
    "response) never changes the state of the connection'); a failed "
    "SELECT ('after an error in selecting a mailbox' the connection is in "
    "authenticated state, sec.3.2 -- no transition); CAPABILITY/NOOP and "
    "the mailbox-management commands (self-loops in every state; the "
    "encoding already maps undeclared events to self-loops, so they are "
    "not declared as actions); the autologout timer (sec.5.4) is subsumed "
    "under the unilateral-close (BYE) edges.",
    "encoding: states 4..7 are unreachable padding to reach 2^3 (engine "
    "input contract); any (state, event) pair not listed in EDGES "
    "self-loops with reward 0; rewards are all zero because IMAP defines "
    "no payoff; goals is empty.",
    "twin note: AUTHENTICATED and SELECTED are joined by the mutually "
    "inverse edges SELECT (forward) and CLOSE (back) -- a 2-cycle that "
    "looks swap-friendly; both also have LOGOUT exits. Whether the swap is "
    "a symmetry is a question for the data -- see groups/auth_selected.json.",
    "provenance: transcribed fresh from RFC 3501 text (fetched from "
    "rfc-editor.org on 2026-10-31) for this repository; no base model was "
    "copied.",
]

# ------------------------------------------------- expected verdict table
# Observed on 2026-10-31 from a live three-way arbitration run
# (`python -X utf8 -m symmetry_court arbitrate --emit-expected-template`;
# receipt: verdicts/imap.verdict.json). The gate
# (`python -X utf8 -m symmetry_court selftest`) replays every case and
# compares these pinned rows field-by-field against a fresh run.
EXPECTED_ROWS = {
    "auth_selected": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "generalized"},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": False, "labeled_symmetry": False},
    },
    "notauth_auth": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "generalized"},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": False, "labeled_symmetry": False},
    },
    "pads": {
        "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                    "judge": "generalized"},
        "fixed": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": True},
    },
}


def build_expected():
    groups = {}
    for name, g in build_groups().items():
        key = os.path.splitext(name)[0]
        groups[key] = {
            "claim": g["meta"]["claim"],
            "relabel": dict(EXPECTED_ROWS[key]["relabel"]),
            "fixed": dict(EXPECTED_ROWS[key]["fixed"]),
            "networkx": dict(EXPECTED_ROWS[key]["networkx"]),
        }
    return {
        "case": "imap",
        "provenance": {
            "recorded": ("2026-10-31, observed from a live three-way "
                         "arbitration run (`python -X utf8 -m symmetry_court "
                         "arbitrate --emit-expected-template`); the receipt "
                         "is verdicts/imap.verdict.json; the gate "
                         "(`python -X utf8 -m symmetry_court selftest`) "
                         "replays the case and compares these rows "
                         "field-by-field"),
            "reading_guide": ("relabel row = actions may be renamed along "
                              "with states (diagnostic contrast reading for "
                              "an event-class model); fixed row = event "
                              "names pinned (the protocol-true reading, "
                              "declared in each group file); networkx "
                              "columns = independent juror"),
        },
        "groups": groups,
    }


# ---------------------------------------------------------------- builders
def build_trans():
    idx = {name: i for i, name in enumerate(STATES)}
    delta = {}
    for u, ev, v, _ in EDGES:
        delta[(idx[u], ev)] = idx[v]
    trans = []
    for s in range(N_STATES):
        row = []
        for ev in EVENTS:
            if s in REAL_STATES and (s, ev) in delta:
                row.append([[1.0, delta[(s, ev)], 0.0]])
            else:
                row.append([[1.0, s, 0.0]])   # undeclared event -> self-loop
        trans.append(row)
    return trans


def build_model():
    return {
        "n_bits": N_BITS,
        "n_actions": len(EVENTS),
        "n_states": N_STATES,
        "goals": [],
        "meta": {
            "source_system": ("IMAP4rev1 connection state machine, "
                              "transcribed from RFC 3501 section 3 (states "
                              "and entry conditions) and section 6 "
                              "(per-state commands), cross-checked against "
                              "sections 6.4.2 and 7.1.4. RFC 3501 is a "
                              "public standard (proposed standard, March "
                              "2003)."),
            "variant": "imap-rfc3501-connection",
            "source_citation": ("RFC 3501 (March 2003), sections 3, 3.1-3.4, "
                                "6.1, 6.2, 6.3, 6.4, 6.4.2, 7.1.4, 7.1.5. "
                                "Per-edge citations in "
                                "meta.edges_with_citations."),
            "state_names": STATES,
            "action_names": EVENTS,
            "real_states": REAL_STATES,
            "semantics_class": ("event: the actions are protocol commands "
                                "or greeting/teardown events named by the "
                                "RFC; their names are part of the behavior "
                                "and do not follow state renamings -- "
                                "candidate groups in groups/ declare "
                                "semantics \"fixed\". The relabel rows in "
                                "expected.json are the diagnostic contrast "
                                "reading, not the protocol-true one."),
            "encoding": ("states 4..7 = unreachable padding (self-loop "
                         "only); undeclared (state, event) pairs self-loop "
                         "with reward 0"),
            "reward_rule": ("rewards all zero: IMAP defines no payoff; the "
                            "reward layer carries no information, all "
                            "conclusions come from the transition layer"),
            "edges_with_citations": [
                {"from": u, "event": ev, "to": v, "citation": c}
                for u, ev, v, c in EDGES
            ],
            "transcription_notes": TRANSCRIPTION_NOTES,
            "regenerate": "python -X utf8 cases/imap/make_imap.py",
        },
        "trans": build_trans(),
    }


def _swap(a, b):
    perm = list(range(N_STATES))
    perm[a], perm[b] = perm[b], perm[a]
    return perm


def _group(elements_swaps, meta):
    return {
        "n_states": N_STATES,
        "elements": [list(range(N_STATES))] + [_swap(a, b) for a, b in elements_swaps],
        "semantics": {"action": "fixed"},
        "meta": meta,
    }


def build_groups():
    idx = {name: i for i, name in enumerate(STATES)}
    na, au, se = idx["NOT-AUTHENTICATED"], idx["AUTHENTICATED"], idx["SELECTED"]
    pad_a, pad_b = 4, 5
    regen = "python -X utf8 cases/imap/make_imap.py"

    return {
        "auth_selected.json": _group(
            [(au, se)],
            {
                "claim": ("defendant A: AUTHENTICATED and SELECTED are joined "
                          "by two mutually inverse edges (SELECT forward, "
                          "CLOSE back) and both have LOGOUT exits, so the "
                          "two 'inside the session' states could be swapped "
                          "and compressed"),
                "construction": ("order-2 group swapping AUTHENTICATED <-> "
                                 "SELECTED (states %d <-> %d)" % (au, se)),
                "why_it_looks_legal": ("the SELECT/CLOSE pair forms a 2-cycle "
                                       "between exactly these two states, "
                                       "and both leave to LOGOUT the same "
                                       "way; on the unlabeled graph the swap "
                                       "maps each arrow to an arrow"),
                "why_it_is_not_a_symmetry": ("the login edge has no mirror: "
                                             "NOT-AUTHENTICATED enters "
                                             "AUTHENTICATED (by "
                                             "AUTHENTICATE/LOGIN or PREAUTH "
                                             "greeting) but nothing enters "
                                             "SELECTED from "
                                             "NOT-AUTHENTICATED; and SELECT "
                                             "is a self-loop once already "
                                             "SELECTED (sec.6.4.2) while "
                                             "AUTHENTICATED has no such "
                                             "self-loop on that event"),
                "semantics_note": ("event-class model: semantics declared "
                                   "\"fixed\"; the relabel row in "
                                   "expected.json is the diagnostic contrast "
                                   "reading"),
                "regenerate": regen,
            }),
        "notauth_auth.json": _group(
            [(na, au)],
            {
                "claim": ("defendant B (control lookalike): NOT-AUTHENTICATED "
                          "and AUTHENTICATED are one command apart, so they "
                          "could be swapped"),
                "construction": ("order-2 group swapping NOT-AUTHENTICATED "
                                 "<-> AUTHENTICATED (states %d <-> %d)"
                                 % (na, au)),
                "why_it_looks_legal": ("the two states sit adjacent in the "
                                       "flow and one command separates them"),
                "why_it_is_not_a_symmetry": ("NOT-AUTHENTICATED has no "
                                             "incoming edges at all (it is "
                                             "the diagram's entry point, "
                                             "sec.3.1) while AUTHENTICATED "
                                             "is entered from two states; "
                                             "and 'it is not possible to "
                                             "re-enter not authenticated "
                                             "state' (sec.6.2) -- no edge "
                                             "ever returns"),
                "semantics_note": ("event-class model: semantics declared "
                                   "\"fixed\""),
                "regenerate": regen,
            }),
        "pads.json": _group(
            [(pad_a, pad_b)],
            {
                "claim": ("positive control: padding states %d and %d have "
                          "byte-identical rows (every event self-loops, "
                          "reward 0), so the swap is a genuine symmetry under "
                          "BOTH readings and should be admitted everywhere"
                          % (pad_a, pad_b)),
                "construction": ("order-2 group swapping padding states %d "
                                 "<-> %d" % (pad_a, pad_b)),
                "why_it_looks_legal": ("the two padding rows are identical, "
                                       "so the swap is equivariant with event "
                                       "names pinned"),
                "why_it_is_a_symmetry": ("padding rows reference no event; "
                                         "the swap maps every arrow to itself "
                                         "under both readings"),
                "semantics_note": ("event-class model: semantics declared "
                                   "\"fixed\" and admitted anyway -- this is "
                                   "the fixed positive control"),
                "regenerate": regen,
            }),
    }


# ---------------------------------------------------------------- main
def _dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


def payloads():
    ps = {"model.json": _dump(build_model()),
          "expected.json": _dump(build_expected())}
    for name, g in build_groups().items():
        ps["groups/" + name] = _dump(g)
    return ps


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=here,
                    help="target directory (default: this script's directory)")
    ap.add_argument("--check", action="store_true",
                    help="do not write; verify the committed files are "
                         "byte-identical to a fresh regeneration")
    args = ap.parse_args(argv)

    ps = payloads()
    if args.check:
        bad = []
        for name, blob in sorted(ps.items()):
            p = os.path.join(here, name)
            with open(p, "r", encoding="utf-8", newline="") as f:
                current = f.read()
            if current != blob:
                bad.append(name)
        if bad:
            sys.stderr.write("byte-identity FAILED: %s\n" % ", ".join(bad))
            return 1
        sys.stdout.write("byte-identity OK: %s\n" % ", ".join(sorted(ps)))
        return 0

    os.makedirs(args.out, exist_ok=True)
    os.makedirs(os.path.join(args.out, "groups"), exist_ok=True)
    for name, blob in sorted(ps.items()):
        p = os.path.join(args.out, name)
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(blob)
        sys.stdout.write("wrote %s (%d bytes)\n"
                         % (p, len(blob.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())

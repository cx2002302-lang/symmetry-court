# -*- coding: utf-8 -*-
"""
make_tcp.py -- deterministic generator for the flagship case: the TCP
connection state machine, transcribed from RFC 9293.

Writes, byte-identical on every re-run (nothing random, no clock, no locale
dependence), next to this script:

  model.json            the trans model: 11 real states + 5 padding states
                        (2^4 input contract), 12 events, rewards all zero
  groups/swap.json      defendant A: swap CLOSING <-> FIN-WAIT-2 (order 2)
  groups/other.json     defendant B: swap FIN-WAIT-1 <-> SYN-RECEIVED
  groups/absurd.json    defendant C: swap CLOSED <-> ESTABLISHED (control)
  groups/pads.json      positive control: swap of two padding states

Transcription authority: RFC 9293 section 3.3.2 Figure 5 ("TCP Connection
State Diagram") plus its Notes 1-3, cross-checked against section 3.10.4
(CLOSE Call). Every edge carries its citation in model.json
(meta.edges_with_citations). The transcription was re-verified edge-by-edge
against the RFC text (this is the A2 transcription duty); the corrections
against the base material are recorded in meta.transcription_notes:

  1. REMOVED  SYN-SENT --CLOSE--> FIN-WAIT-1: Figure 5 draws no such arrow
     (the only arrows entering FIN-WAIT-1 come from SYN-RECEIVED and
     ESTABLISHED), and section 3.10.4 (CLOSE Call, SYN-SENT STATE) says
     "Delete the TCB and return \"error: closing\" responses..." -- no
     FIN-WAIT-1 transition. The base material contained this edge; it most
     likely traces to older RFC 793-style drawings. Not transcribed.
  2. KEPT, re-cited  FIN-WAIT-1 --rcv FIN (and our FIN acked)--> TIME-WAIT:
     NOT drawn in Figure 5; section 3.3.2 Note 2 states it ("The figure
     omits a transition from FIN-WAIT-1 to TIME-WAIT if a FIN is received
     and the local FIN is also acknowledged."). Cited to Note 2, not to the
     figure. The event label "rcv FIN+FIN acked" is the base material's
     shorthand for Note 2's wording, not an RFC-printed string.
  3. NOT COLLECTED  the any-state RST transitions (Note 3): the RFC itself
     omits them from the figure "for legibility"; only the drawn
     SYN-RECEIVED --rcv RST--> LISTEN edge (conditional on passive OPEN,
     Note 1) is included.

The states/events/encoding policy of the base material (a predecessor
transcription of the same figure; provenance in NOTICE) is preserved:
state numbering 0..10, event indices 0..11, padding states 11..15
self-loop, undeclared
(state, event) pairs self-loop with reward 0, rewards all zero (TCP defines
no payoff), goals empty.

Usage:
  python -X utf8 cases/tcp/make_tcp.py            # write all five files
  python -X utf8 cases/tcp/make_tcp.py --out DIR  # write into DIR
  python -X utf8 cases/tcp/make_tcp.py --check    # verify bytes, exit 0/1
"""
import argparse
import json
import os
import sys

# ---------------------------------------------------------------- data
STATES = ["CLOSED", "LISTEN", "SYN-SENT", "SYN-RECEIVED", "ESTABLISHED",
          "FIN-WAIT-1", "FIN-WAIT-2", "CLOSE-WAIT", "CLOSING", "LAST-ACK",
          "TIME-WAIT"]

FIG5 = "RFC 9293 sec.3.3.2 Figure 5"
NOTE1 = "RFC 9293 sec.3.3.2 Figure 5 + Note 1"
NOTE2 = "RFC 9293 sec.3.3.2 Note 2 (stated in the note; deliberately omitted from the Figure 5 drawing)"

# (from, event, to, citation) -- order fixes the action indices (first
# occurrence). Re-verified edge-by-edge against the RFC 9293 text.
EDGES = [
    ("CLOSED", "active OPEN", "SYN-SENT", FIG5),
    ("CLOSED", "passive OPEN", "LISTEN", FIG5),
    ("LISTEN", "rcv SYN", "SYN-RECEIVED", FIG5),
    ("LISTEN", "SEND", "SYN-SENT", FIG5),
    ("LISTEN", "CLOSE", "CLOSED", FIG5),
    ("SYN-SENT", "rcv SYN,ACK", "ESTABLISHED", FIG5),
    ("SYN-SENT", "rcv SYN", "SYN-RECEIVED", FIG5),
    ("SYN-RECEIVED", "rcv ACK of SYN", "ESTABLISHED", FIG5),
    ("SYN-RECEIVED", "rcv RST", "LISTEN", NOTE1),
    ("SYN-RECEIVED", "CLOSE", "FIN-WAIT-1", FIG5),
    ("ESTABLISHED", "CLOSE", "FIN-WAIT-1", FIG5),
    ("ESTABLISHED", "rcv FIN", "CLOSE-WAIT", FIG5),
    ("FIN-WAIT-1", "rcv ACK of FIN", "FIN-WAIT-2", FIG5),
    ("FIN-WAIT-1", "rcv FIN", "CLOSING", FIG5),
    ("FIN-WAIT-1", "rcv FIN+FIN acked", "TIME-WAIT", NOTE2),
    ("FIN-WAIT-2", "rcv FIN", "TIME-WAIT", FIG5),
    ("CLOSE-WAIT", "CLOSE", "LAST-ACK", FIG5),
    ("CLOSING", "rcv ACK of FIN", "TIME-WAIT", FIG5),
    ("LAST-ACK", "rcv ACK of FIN", "CLOSED", FIG5),
    ("TIME-WAIT", "timeout 2MSL", "CLOSED", FIG5),
]

EVENTS = []
for _, ev, _, _ in EDGES:
    if ev not in EVENTS:
        EVENTS.append(ev)

N_BITS = 4
N_STATES = 1 << N_BITS          # 16 = 11 real + 5 padding
REAL_STATES = list(range(11))   # 0..10 are protocol states; 11..15 padding

TRANSCRIPTION_NOTES = [
    "removed vs base material: the edge SYN-SENT --CLOSE--> FIN-WAIT-1 in "
    "the predecessor transcription of this figure (see NOTICE) is NOT "
    "transcribed here: RFC 9293 Figure 5 draws no arrow from SYN-SENT into "
    "FIN-WAIT-1 (only SYN-RECEIVED and ESTABLISHED arrows enter FIN-WAIT-1), "
    "and sec.3.10.4 CLOSE Call, SYN-SENT STATE, says 'Delete the TCB and "
    "return \"error: closing\" responses to any queued SENDs, or RECEIVEs.' "
    "-- i.e. no transition to FIN-WAIT-1. Likely carried over from older "
    "RFC 793-style drawings.",
    "kept with changed citation: FIN-WAIT-1 --rcv FIN+FIN acked--> TIME-WAIT "
    "does not appear in the Figure 5 drawing; it is stated in sec.3.3.2 "
    "Note 2 ('The figure omits a transition from FIN-WAIT-1 to TIME-WAIT if "
    "a FIN is received and the local FIN is also acknowledged.') and is "
    "transcribed from Note 2. The event label 'rcv FIN+FIN acked' is the "
    "base material's shorthand for that wording, not an RFC-printed string.",
    "not collected (per the RFC's own omission): Note 3's any-state RST "
    "transitions (sending a RST goes to TIME-WAIT; receiving a RST goes to "
    "LISTEN or CLOSED) are omitted from Figure 5 'for legibility' and are "
    "not transcribed as model edges; only the drawn "
    "SYN-RECEIVED --rcv RST--> LISTEN edge (Note 1, conditional on having "
    "reached SYN-RECEIVED after a passive OPEN) is included.",
    "scope warning, quoted from the RFC: 'NOTA BENE: This diagram is only a "
    "summary and must not be taken as the total specification.' The model "
    "transcribes the diagram plus its Notes, not the full normative state "
    "machine of sections 3.5/3.10.",
    "encoding: states 11..15 are unreachable padding to reach 2^4 (engine "
    "input contract, same rule as the real 512/16,384-state cases); any "
    "(state, event) pair not listed in EDGES self-loops with reward 0 "
    "(undeclared event = no state change); rewards are all zero because TCP "
    "defines no payoff; goals is empty.",
    "names: the figure abbreviates state names (ESTAB, SYN RCVD, FIN "
    "WAIT-1, FINWAIT-2, CLOSE WAIT); this transcription uses the canonical "
    "state names, per RFC 9293's own remark that 'Some state names are "
    "abbreviated or hyphenated differently in the diagram from how they "
    "appear elsewhere in the document.'",
    "base material: a predecessor transcription of the same figure was used "
    "as the starting point (provenance and version pin in NOTICE); state "
    "numbering and event indices preserved; the SYN-SENT CLOSE edge removed "
    "(note 1); every edge re-verified against the RFC text on 2026-10-31.",
]

# ------------------------------------------------- expected verdict table
# Observed on 2026-10-31 from a live three-way arbitration run
# (`python -X utf8 -m symmetry_court arbitrate --emit-expected-template`;
# receipt: verdicts/tcp.verdict.json). The gate
# (`python -X utf8 -m symmetry_court selftest`) replays every case and
# compares these pinned rows field-by-field against a fresh run.
EXPECTED_ROWS = {
    "absurd": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "generalized"},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": False, "labeled_symmetry": False},
    },
    "other": {
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
    "swap": {
        "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                    "judge": "generalized"},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
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
        "case": "tcp",
        "provenance": {
            "recorded": ("2026-10-31, observed from a live three-way "
                         "arbitration run (`python -X utf8 -m symmetry_court "
                         "arbitrate --emit-expected-template`); the receipt "
                         "is verdicts/tcp.verdict.json; the gate "
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
            "source_system": ("TCP connection state machine (client-or-server "
                              "endpoint), transcribed from RFC 9293 section "
                              "3.3.2 Figure 5 and its Notes, cross-checked "
                              "against section 3.10.4 (CLOSE Call). RFC 9293 "
                              "is a public standard (STD 7)."),
            "variant": "tcp-rfc9293",
            "source_citation": ("RFC 9293 (November 2022), section 3.3.2, "
                                "Figure 5 'TCP Connection State Diagram' + "
                                "Notes 1-3; sections 3.5 and 3.10.4 used for "
                                "cross-checks. Per-edge citations in "
                                "meta.edges_with_citations."),
            "state_names": STATES,
            "action_names": EVENTS,
            "real_states": REAL_STATES,
            "semantics_class": ("event: the actions are protocol events "
                                "(arriving segments, calls, timers); their "
                                "names are part of the behavior and do not "
                                "follow state renamings -- candidate groups "
                                "in groups/ declare semantics \"fixed\". The "
                                "relabel rows in expected.json are the "
                                "diagnostic contrast reading, not the "
                                "protocol-true one."),
            "encoding": ("states 11..15 = unreachable padding (self-loop "
                         "only); undeclared (state, event) pairs self-loop "
                         "with reward 0"),
            "reward_rule": ("rewards all zero: TCP defines no payoff; the "
                            "reward layer carries no information, all "
                            "conclusions come from the transition layer"),
            "edges_with_citations": [
                {"from": u, "event": ev, "to": v, "citation": c}
                for u, ev, v, c in EDGES
            ],
            "transcription_notes": TRANSCRIPTION_NOTES,
            "regenerate": "python -X utf8 cases/tcp/make_tcp.py",
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
    fw2, cw, cls = idx["FIN-WAIT-2"], idx["CLOSE-WAIT"], idx["CLOSING"]
    fw1, sr = idx["FIN-WAIT-1"], idx["SYN-RECEIVED"]
    closed, est = idx["CLOSED"], idx["ESTABLISHED"]
    pad_a, pad_b = 11, 12
    regen = "python -X utf8 cases/tcp/make_tcp.py"

    return {
        "swap.json": _group(
            [(cls, fw2)],
            {
                "claim": ("defendant A: FIN-WAIT-2 (waiting for the peer's FIN) "
                          "and CLOSING (waiting for the peer's ACK of our FIN) "
                          "are drawn as shape-twins -- one outgoing edge each, "
                          "both into TIME-WAIT -- so the two termination paths "
                          "could be swapped and compressed into one"),
                "construction": ("order-2 group swapping CLOSING <-> FIN-WAIT-2 "
                                 "(states %d <-> %d), the only nontrivial "
                                 "structure-level automorphism of the "
                                 "unlabeled RFC 9293 Figure 5 graph"
                                 % (cls, fw2)),
                "why_it_looks_legal": ("both states have exactly one outgoing "
                                       "edge and it leads to TIME-WAIT in "
                                       "both; on the unlabeled graph the swap "
                                       "maps arrows to arrows"),
                "why_it_is_not_a_symmetry": ("the outgoing events differ: "
                                             "FIN-WAIT-2 leaves on 'rcv FIN', "
                                             "CLOSING leaves on 'rcv ACK of "
                                             "FIN' -- merging 'the peer sent "
                                             "FIN' with 'the peer acknowledged "
                                             "our FIN' is a protocol error "
                                             "(TV 1.0 on the completion edges "
                                             "under the fixed reading)"),
                "semantics_note": ("event-class model: semantics declared "
                                   "\"fixed\" (event names pinned); the "
                                   "relabel row in expected.json is the "
                                   "diagnostic contrast reading"),
                "regenerate": regen,
            }),
        "other.json": _group(
            [(fw1, sr)],
            {
                "claim": ("defendant B: FIN-WAIT-1 and SYN-RECEIVED are both "
                          "middle states with three outgoing edges, so they "
                          "could be swapped"),
                "construction": ("order-2 group swapping FIN-WAIT-1 <-> "
                                 "SYN-RECEIVED (states %d <-> %d)" % (fw1, sr)),
                "why_it_looks_legal": ("coarse shape similarity: both are "
                                       "mid-handshake/teardown states with "
                                       "three outgoing edges in the figure"),
                "why_it_is_not_a_symmetry": ("their edge targets differ "
                                             "(FIN-WAIT-1 leaves toward "
                                             "FIN-WAIT-2/CLOSING/TIME-WAIT; "
                                             "SYN-RECEIVED toward "
                                             "ESTABLISHED/LISTEN/FIN-WAIT-1): "
                                             "no relabeling of events can "
                                             "reconcile the two successor "
                                             "sets"),
                "semantics_note": ("event-class model: semantics declared "
                                   "\"fixed\""),
                "regenerate": regen,
            }),
        "absurd.json": _group(
            [(closed, est)],
            {
                "claim": ("defendant C (control): CLOSED and ESTABLISHED -- a "
                          "connection's starting state and its main working "
                          "state -- could be swapped"),
                "construction": ("order-2 group swapping CLOSED <-> "
                                 "ESTABLISHED (states %d <-> %d)"
                                 % (closed, est)),
                "why_it_looks_legal": ("nothing -- this defendant exists as "
                                       "the obviously-refused control: a "
                                       "sanity check that all three parties "
                                       "(wuxing-gua relabel, wuxing-gua "
                                       "fixed, networkx) refuse together"),
                "why_it_is_not_a_symmetry": ("CLOSED has 2 outgoing edges, "
                                             "ESTABLISHED has 2, but their "
                                             "in/out neighborhoods are "
                                             "entirely different (CLOSED is "
                                             "entered from LISTEN/LAST-ACK/"
                                             "TIME-WAIT; ESTABLISHED from "
                                             "SYN-SENT/SYN-RECEIVED); degree "
                                             "signatures already differ"),
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
        sys.stdout.write("byte-identity OK: %s\n"
                         % ", ".join(sorted(ps)))
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

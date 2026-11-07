# -*- coding: utf-8 -*-
"""
make_http2.py -- deterministic generator for the field-trial2 case: the
HTTP/2 stream state machine, transcribed from RFC 9113.

Writes, byte-identical on every re-run (nothing random, no clock, no locale
dependence), next to this script:

  model.json            the trans model: 7 real states + 9 padding states
                        (2^4 input contract), 8 events, rewards all zero
  expected.json         hand-derived expected rows (live-run confirmed; see
                        provenance.recorded)
  groups/endpoint-mirror.json     defendant A: endpoint-role mirror (claim)
  groups/half-mirror-only.json    defendant B: half-closed swap alone
  groups/reserved-swap-only.json  defendant C: reserved swap alone
  groups/pads.json                positive control: padding-state swap

Transcription authority: RFC 9113 (HTTP/2, June 2022) section 5.1 "Stream
States", Figure 2 plus the per-state bullet lists. Every edge carries its
citation in model.json (meta.edges_with_citations). Deviations from the
figure are recorded in meta.transcription_notes.

The encoding policy follows the court's flagship tcp case (RFC 9293
transcription): undeclared (state, event) pairs self-loop with reward 0,
padding states self-loop everything, rewards all zero (HTTP/2 defines no
payoff at the stream-state layer), goals empty.

States (RFC-printed names): idle, reserved (local), reserved (remote), open,
half-closed (local), half-closed (remote), closed -- indices 0..6. Slots
7..15 are padding. Events are the Figure 2 legend abbreviations, RFC-printed:
send/recv x {PP, H, ES, R} (PP = PUSH_PROMISE, H = HEADERS, ES = END_STREAM
flag, R = RST_STREAM).

Usage:
  python -X utf8 make_http2.py            # write all files
  python -X utf8 make_http2.py --out DIR  # write into DIR
  python -X utf8 make_http2.py --check    # verify bytes, exit 0/1
"""
import argparse
import json
import os
import sys

# ---------------------------------------------------------------- data
STATES = ["idle", "reserved (local)", "reserved (remote)", "open",
          "half-closed (local)", "half-closed (remote)", "closed"]

F = "RFC 9113 sec.5.1 Figure 2"
IB = "RFC 9113 sec.5.1 'idle' bullet list"
RLB = "RFC 9113 sec.5.1 'reserved (local)' bullet list"
RRB = "RFC 9113 sec.5.1 'reserved (remote)' bullet list"
OB = "RFC 9113 sec.5.1 'open' bullet list"
HLB = "RFC 9113 sec.5.1 'half-closed (local)' bullet list"
HRB = "RFC 9113 sec.5.1 'half-closed (remote)' bullet list"

# (from, event, to, citation) -- order fixes the event indices (an event's
# index is set by its earliest occurrence), the same policy as the tcp case.
# Re-verified edge-by-edge against the RFC 9113 sec.5.1 text and Figure 2.
EDGES = [
    ("idle", "send PP", "reserved (local)", F + " + " + IB),
    ("idle", "recv PP", "reserved (remote)", F + " + " + IB),
    ("idle", "send H", "open", F + " + " + IB),
    ("idle", "recv H", "open", F + " + " + IB),
    ("reserved (local)", "send H", "half-closed (remote)", F + " + " + RLB),
    ("reserved (local)", "send R", "closed", F + " + " + RLB),
    ("reserved (local)", "recv R", "closed", F),
    ("reserved (remote)", "recv H", "half-closed (local)", F + " + " + RRB),
    ("reserved (remote)", "send R", "closed", F + " + " + RRB),
    ("reserved (remote)", "recv R", "closed", F),
    ("open", "send ES", "half-closed (local)", F + " + " + OB),
    ("open", "recv ES", "half-closed (remote)", F + " + " + OB),
    ("open", "send R", "closed", F + " + " + OB),
    ("open", "recv R", "closed", F),
    ("half-closed (local)", "recv ES", "closed", F + " + " + HLB),
    ("half-closed (local)", "send R", "closed", F + " + " + HLB),
    ("half-closed (local)", "recv R", "closed", F + " + " + HLB),
    ("half-closed (remote)", "send ES", "closed", F + " + " + HRB),
    ("half-closed (remote)", "send R", "closed", F + " + " + HRB),
    ("half-closed (remote)", "recv R", "closed", F + " + " + HRB),
]

# earliest-occurrence order over EDGES: send PP, recv PP, send H, recv H,
# send R, recv R, send ES, recv ES
EVENTS = ["send PP", "recv PP", "send H", "recv H",
          "send R", "recv R", "send ES", "recv ES"]

N_BITS = 4
N_STATES = 1 << N_BITS          # 16 slots
REAL_STATES = list(range(7))    # 0..6 real; 7..15 padding
PAD_STATES = list(range(7, 16))

TRANSCRIPTION_NOTES = [
    ("NOT COLLECTED  idle -> closed via a higher-valued intervening stream "
     "identifier: sec.5.1 'idle' bullet says 'Opening a stream with a "
     "higher-valued stream identifier causes the stream to transition "
     "immediately to a closed state; note that this transition is not shown "
     "in the diagram.' The RFC itself omits it from Figure 2; not "
     "transcribed (same policy as the tcp case's treatment of the any-state "
     "RST note)."),
    ("KEPT via the separate-event rule: 'For the purpose of state "
     "transitions, the END_STREAM flag is processed as a separate event to "
     "the frame that bears it; a HEADERS frame with the END_STREAM flag set "
     "can cause two state transitions.' (sec.5.1, right after Figure 2). "
     "Hence 'send ES' / 'recv ES' are standalone events and a HEADERS frame "
     "with ES chains two edges (e.g. idle --send H--> open --send ES--> "
     "half-closed (local))."),
    ("NOT COLLECTED (no state transition): PRIORITY and WINDOW_UPDATE frames "
     "may be received in reserved (local), reserved (remote) and the "
     "half-closed states, and PRIORITY on closed streams, without any state "
     "transition (the per-state frame-type lists); CONTINUATION frames 'do "
     "not result in state transitions' (sec.5.1 note after Figure 2). No "
     "edges for them."),
    ("NOT COLLECTED (connection-level error exits): receiving any frame "
     "other than HEADERS or PRIORITY on an idle stream (and the per-state "
     "frame-type bans) is a CONNECTION error of type PROTOCOL_ERROR "
     "(sec.5.1), not a stream-state transition; the connection-error path "
     "is outside this case's scope."),
    ("NOT COLLECTED: closed-state late-frame handling (sec.5.1 'closed': "
     "minimal processing and discard; WINDOW_UPDATE or RST_STREAM may arrive "
     "for a short period after closing) causes no transition out of closed; "
     "Figure 2 draws no outgoing arrow from closed and none is transcribed."),
    ("KEPT, re-scoped: 'Receiving a PUSH_PROMISE frame also causes the "
     "promised stream to become \"reserved (remote)\", even when the "
     "PUSH_PROMISE frame is received on a closed stream.' (sec.5.1 "
     "'closed'). The re-reserved stream is the PROMISED (idle) stream, a "
     "different stream; its idle --recv PP--> reserved (remote) edge is "
     "already collected. No extra edge for the closed stream itself."),
]

REGEN = "python -X utf8 field-trial2/cases/http2-stream-states/make_http2.py"


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
            "source_system": ("HTTP/2 stream state machine (one stream as "
                              "seen by one endpoint), transcribed from "
                              "RFC 9113 section 5.1 Figure 2 and the "
                              "per-state bullet lists. RFC 9113 is a public "
                              "standard (Internet Standards Track "
                              "technical specification; obsoletes "
                              "RFC 7540)."),
            "variant": "http2-rfc9113",
            "source_citation": ("RFC 9113 (June 2022), section 5.1 'Stream "
                                "States', Figure 2 + per-state bullet "
                                "lists + the END_STREAM separate-event "
                                "paragraph. Per-edge citations in "
                                "meta.edges_with_citations."),
            "state_names": STATES,
            "action_names": EVENTS,
            "real_states": REAL_STATES,
            "semantics_class": ("event: the actions are protocol frame "
                                "events (with the figure's own PP/H/ES/R "
                                "abbreviations); their names are part of "
                                "the behavior and do not follow state "
                                "renamings -- candidate groups in groups/ "
                                "declare semantics \"fixed\". The relabel "
                                "rows in expected.json are the diagnostic "
                                "contrast reading, not the protocol-true "
                                "one."),
            "encoding": ("states 7..15 = unreachable padding (self-loop "
                         "only); undeclared (state, event) pairs self-loop "
                         "with reward 0"),
            "reward_rule": ("rewards all zero: the stream-state layer "
                            "defines no payoff; the reward layer carries "
                            "no information, all conclusions come from the "
                            "transition layer"),
            "edges_with_citations": [
                {"from": u, "event": ev, "to": v, "citation": c}
                for u, ev, v, c in EDGES
            ],
            "transcription_notes": TRANSCRIPTION_NOTES,
            "regenerate": REGEN,
        },
        "trans": build_trans(),
    }


# ---------------------------------------------------------------- groups
def _swap(a, b):
    perm = list(range(N_STATES))
    perm[a], perm[b] = perm[b], perm[a]
    return perm


def _group(elements_perms, meta):
    return {
        "n_states": N_STATES,
        "elements": [list(range(N_STATES))] + elements_perms,
        "semantics": {"action": "fixed"},
        "meta": meta,
    }


def endpoint_mirror_perm():
    # local <-> remote: reserved (local) 1 <-> reserved (remote) 2,
    # half-closed (local) 4 <-> half-closed (remote) 5;
    # idle 0, open 3, closed 6 and pads 7..15 fixed.
    perm = list(range(N_STATES))
    perm[1], perm[2] = 2, 1
    perm[4], perm[5] = 5, 4
    return perm


def build_groups():
    regen = REGEN
    return {
        "endpoint-mirror.json": _group(
            [endpoint_mirror_perm()],
            {
                "claim": ("defendant A (claim): the stream state graph is "
                          "endpoint-role symmetric -- swapping the two "
                          "endpoint roles (local <-> remote) maps every "
                          "arrow to an arrow: reserved (local) <-> reserved "
                          "(remote) (server-push reservation twins), "
                          "half-closed (local) <-> half-closed (remote), "
                          "with idle, open and closed fixed. The RFC writes "
                          "the two reserved states and the two half-closed "
                          "states as mirror bullet lists, and the RST "
                          "escape says verbatim 'Either endpoint can send a "
                          "RST_STREAM frame' in both reserved states."),
                "construction": ("order-2 group: swap reserved (local) <-> "
                                 "reserved (remote) (states 1 <-> 2) AND "
                                 "half-closed (local) <-> half-closed "
                                 "(remote) (states 4 <-> 5)"),
                "why_it_looks_legal": ("on the unlabeled graph every edge "
                                       "maps to an edge: idle->res(l)/res(r) "
                                       "are twins, res(l)->hc(r) mirrors "
                                       "res(r)->hc(l), open->hc(l)/hc(r) are "
                                       "twins, and every ->closed edge has "
                                       "its twin"),
                "why_it_is_not_a_symmetry": ("the labels move with the "
                                             "roles: 'send PP' on "
                                             "idle->reserved (local) becomes "
                                             "'recv PP' on idle->reserved "
                                             "(remote); likewise send H/recv "
                                             "H, send ES/recv ES and send "
                                             "R/recv R differ on most edges, "
                                             "so with event names pinned the "
                                             "swap fails -- the two roles "
                                             "are complementary, not "
                                             "identical"),
                "engineering_anchor": ("the RFC defines the state machine "
                                       "once and lets both endpoints use it "
                                       "subjectively: 'Both endpoints have "
                                       "a subjective view of the state of a "
                                       "stream' (sec.5.1); the mirror "
                                       "reading is exactly how one shared "
                                       "diagram serves both sides"),
                "semantics_note": ("event-class model: semantics declared "
                                   "\"fixed\" (protocol-true reading); the "
                                   "relabel row is the diagnostic contrast "
                                   "reading"),
                "regenerate": regen,
            }),
        "half-mirror-only.json": _group(
            [_swap(4, 5)],
            {
                "claim": ("defendant B: half-closed (local) and half-closed "
                          "(remote) are shape-twins (both drain to closed "
                          "on three events), so maybe they can be swapped "
                          "while keeping reserved (local)/(remote) fixed"),
                "construction": ("order-2 group swapping half-closed (local) "
                                 "<-> half-closed (remote) (states 4 <-> 5) "
                                 "only"),
                "why_it_looks_legal": ("both half-closed states have exactly "
                                       "the same row shape: three outgoing "
                                       "edges, all into closed"),
                "why_it_is_not_a_symmetry": ("their IN-edges differ: "
                                             "reserved (remote) --recv H--> "
                                             "half-closed (local) exists, "
                                             "but reserved (remote) -> "
                                             "half-closed (remote) does not; "
                                             "the swap would need "
                                             "reserved (remote) -> "
                                             "half-closed (remote), which no "
                                             "edge provides (same for "
                                             "reserved (local) -> "
                                             "half-closed (local))"),
                "semantics_note": ("control: expected to fail BOTH readings "
                                   "(structure itself breaks)"),
                "regenerate": regen,
            }),
        "reserved-swap-only.json": _group(
            [_swap(1, 2)],
            {
                "claim": ("defendant C: reserved (local) and reserved "
                          "(remote) are server-push twins (both released by "
                          "RST from either endpoint), so maybe they can be "
                          "swapped while keeping the half-closed pair "
                          "fixed"),
                "construction": ("order-2 group swapping reserved (local) "
                                 "<-> reserved (remote) (states 1 <-> 2) "
                                 "only"),
                "why_it_looks_legal": ("both reserved states have two "
                                       "outgoing targets: their half-closed "
                                       "successor and closed"),
                "why_it_is_not_a_symmetry": ("the swap sends "
                                             "reserved (local) --send H--> "
                                             "half-closed (remote) to "
                                             "reserved (remote) --send H--> "
                                             "half-closed (remote), which "
                                             "does not exist (reserved "
                                             "(remote) opens only by "
                                             "RECVING a HEADERS frame into "
                                             "half-closed (local)); the "
                                             "reserved pair cannot move "
                                             "without the half-closed pair"),
                "semantics_note": ("control: expected to fail BOTH readings "
                                   "(structure itself breaks)"),
                "regenerate": regen,
            }),
        "pads.json": _group(
            [_swap(7, 8)],
            {
                "claim": ("positive control: padding states 7 and 8 have "
                          "byte-identical rows (every event self-loops, "
                          "reward 0), so the swap is a genuine symmetry "
                          "under BOTH readings and should be admitted "
                          "everywhere"),
                "construction": ("order-2 group swapping padding states 7 "
                                 "<-> 8"),
                "why_it_looks_legal": ("the two padding rows are identical, "
                                       "so the swap is equivariant with "
                                       "event names pinned"),
                "why_it_is_a_symmetry": ("padding rows reference no event; "
                                         "the swap maps every arrow to "
                                         "itself under both readings"),
                "semantics_note": ("event-class model: semantics declared "
                                   "\"fixed\" and admitted anyway -- this "
                                   "is the fixed positive control"),
                "regenerate": regen,
            }),
    }


# ---------------------------------------------------------------- expected
EXPECTED_ROWS = {
    "endpoint-mirror": {
        "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                    "judge": "generalized"},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
    },
    "half-mirror-only": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "generalized"},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": False, "labeled_symmetry": False},
    },
    "reserved-swap-only": {
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
        "case": "http2-stream-states",
        "provenance": {
            "recorded": (
                "2026-11-08 adoption into the official docket: the case bundle was "
                "copied byte-identical from the field-trial2 blind-trial round-2 case "
                "directory (8/8 files sha256-equal at copy time; oracle-input hashes "
                "match field-trial2/sealed/manifest.json), then the rows below were "
                "re-observed live in this repository via `python -X utf8 -m "
                "symmetry_court arbitrate --emit-expected-template --case "
                "http2-stream-states` -- relabel/fixed are this run's measured rows, "
                "field-for-field identical to the round-2 records; the receipt is "
                "verdicts/http2-stream-states.verdict.json; the gate (`python -X utf8 "
                "-m symmetry_court selftest`) replays the case and compares these "
                "rows field-by-field"),
            "reading_guide": (
                "relabel row = actions may be renamed along with states (diagnostic "
                "contrast reading for an event-class model); fixed row = event names "
                "pinned (the protocol-true reading, declared in each group file); "
                "networkx columns = independent juror"),
            "networkx_source": (
                "networkx columns are carried from the field-trial2 sealed truth "
                "(field-trial2/sealed/http2-stream-states.truth.json, independent "
                "oracle w2-independent-oracle, write-once after sealing "
                "2026-11-07T18:34:44Z, sha256 listed in "
                "field-trial2/sealed/manifest.json); the round-2 unsealing "
                "reconciliation matched the tool on 60/60 checks (12 candidate groups "
                "x 5 axes: fixed / relabel / binding / networkx-structure / "
                "networkx-labeled; false positives 0, false negatives 0; report: "
                "field-trial2/report/reconciliation.md), and this adoption run's live "
                "networkx jury reproduced the same two columns for all 4 groups"),
        },
        "groups": groups,
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

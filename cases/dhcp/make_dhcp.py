# -*- coding: utf-8 -*-
"""
make_dhcp.py -- deterministic generator for the DHCP case: the client
state-transition diagram of RFC 2131, transcribed fresh from the RFC text
for this repository.

Writes, byte-identical on every re-run (nothing random, no clock, no locale
dependence), next to this script:

  model.json                the trans model: 8 real states + 8 padding
                            states (2^4 input contract), 15 events, rewards
                            all zero
  groups/renew_rebind.json  defendant A: swap RENEWING <-> REBINDING -- the
                            protocol's own conceptual twin pair
  groups/reboot_rebind.json defendant B: swap REBOOTING <-> REBINDING -- the
                            sneaky one: same degree signature, different
                            in-neighborhoods (looks like, is not)
  groups/init_start.json    defendant C: swap INIT <-> INIT-REBOOT (control)
  groups/pads.json          positive control: swap of two padding states

Transcription authority: RFC 2131 section 4.4, Figure 5 ("State-transition
diagram for DHCP clients"), cross-checked against sections 3.1, 3.2 and
4.4.1-4.4.5, which name the states explicitly. Every edge carries its
citation in model.json (meta.edges_with_citations). Transcription honesty
rules applied (see meta.transcription_notes):

  - where the 1997 hand-drawn ASCII routing is ambiguous, the edge endpoint
    is pinned by the prose (the prose names the states explicitly); the
    figure label is kept verbatim as the event name
  - one edge is taken from prose although the figure does not draw it
    (REQUESTING --DHCPNAK--> INIT, sec.3.1 step 5), marked as such
  - retransmission timeouts (sec.4.1) and the RFC's "silently discarded"
    stray-message rules are NOT declared as actions: in this encoding an
    undeclared event self-loops with reward 0, which is behaviorally the
    same thing; only the two discard self-loops the figure actually draws
    (REQUESTING, BOUND) are declared
  - DHCPINFORM is not in Figure 5 by the RFC's own remark (sec.4.4 intro)
    and is not transcribed

State numbering: INIT=0, SELECTING=1, REQUESTING=2, BOUND=3, RENEWING=4,
REBINDING=5, INIT-REBOOT=6, REBOOTING=7; padding states 8..15.

Usage:
  python -X utf8 cases/dhcp/make_dhcp.py            # write all five files
  python -X utf8 cases/dhcp/make_dhcp.py --out DIR  # write into DIR
  python -X utf8 cases/dhcp/make_dhcp.py --check    # verify bytes, exit 0/1
"""
import argparse
import json
import os
import sys

STATES = ["INIT", "SELECTING", "REQUESTING", "BOUND", "RENEWING", "REBINDING",
          "INIT-REBOOT", "REBOOTING"]

FIG5 = "RFC 2131 sec.4.4 Figure 5"
F5_S441 = "RFC 2131 sec.4.4 Figure 5; sec.4.4.1"
F5_S445 = "RFC 2131 sec.4.4 Figure 5; sec.4.4.5"
F5_S31 = "RFC 2131 sec.4.4 Figure 5 (label); sec.3.1 step 5 + sec.3.2"
F5_S32 = "RFC 2131 sec.4.4 Figure 5; sec.3.2 + sec.4.4.2"

# (from, event, to, citation). The event string is the figure label verbatim
# (event part "/" action part). Order fixes the action indices.
EDGES = [
    ("INIT", "-/Send DHCPDISCOVER", "SELECTING",
     "RFC 2131 sec.4.4 Figure 5 (label '-/Send DHCPDISCOVER'); sec.4.4.1 "
     "('The client begins in INIT state and forms a DHCPDISCOVER message ... "
     "then broadcasts the DHCPDISCOVER')"),
    ("SELECTING", "DHCPOFFER/Collect replies", "SELECTING",
     "RFC 2131 sec.4.4 Figure 5 (self-loop); sec.4.4.1 ('The client collects "
     "DHCPOFFER messages over a period of time')"),
    ("SELECTING", "Select offer/send DHCPREQUEST", "REQUESTING",
     "RFC 2131 sec.4.4 Figure 5; sec.4.4.1 ('selects one DHCPOFFER message "
     "... and sends that address in the \"server identifier\" field of a "
     "DHCPREQUEST broadcast message')"),
    ("SELECTING", "DHCPACK (not accept.)/Send DHCPDECLINE", "INIT",
     "RFC 2131 sec.4.4 Figure 5 (label); sec.3.1 step 5 ('the client MUST "
     "send a DHCPDECLINE message to the server and restarts the "
     "configuration process'); sec.3.2 ('This action corresponds to the "
     "client moving to the INIT state in the DHCP state diagram')"),
    ("REQUESTING", "DHCPNAK/Restart configuration", "INIT",
     "RFC 2131 sec.3.1 step 5 ('If the client receives a DHCPNAK message, "
     "the client restarts the configuration process.'); NOT drawn in "
     "Figure 5 -- transcribed from prose, label is prose-derived"),
    ("REQUESTING", "DHCPACK/Record lease, set timers T1, T2", "BOUND",
     "RFC 2131 sec.4.4 Figure 5; sec.4.4.1 ('Once the DHCPACK message from "
     "the server arrives, the client is initialized and moves to BOUND "
     "state.')"),
    ("REQUESTING", "DHCPOFFER/Discard", "REQUESTING",
     "RFC 2131 sec.4.4 Figure 5 (lower-left discard self-loop)"),
    ("BOUND", "DHCPOFFER, DHCPACK, DHCPNAK/Discard", "BOUND",
     "RFC 2131 sec.4.4 Figure 5 (self-loop); sec.4.4.1 ('Any arriving "
     "DHCPACK messages must be silently discarded.')"),
    ("BOUND", "T1 expires/Send DHCPREQUEST to leasing server", "RENEWING",
     "RFC 2131 sec.4.4 Figure 5; sec.4.4.5 ('At time T1 the client moves to "
     "RENEWING state and sends (via unicast) a DHCPREQUEST message')"),
    ("RENEWING", "DHCPACK/Record lease, set timers T1, T2", "BOUND",
     "RFC 2131 sec.4.4 Figure 5; sec.4.4.5 ('When the client receives a "
     "DHCPACK from the server ... returns to BOUND state')"),
    ("RENEWING", "T2 expires/Broadcast DHCPREQUEST", "REBINDING",
     "RFC 2131 sec.4.4 Figure 5; sec.4.4.5 ('If no DHCPACK arrives before "
     "time T2, the client moves to REBINDING state and sends (via broadcast) "
     "a DHCPREQUEST message')"),
    ("RENEWING", "DHCPNAK/Halt network", "INIT",
     "RFC 2131 sec.4.4 Figure 5 (right-hand rail); sec.4.4.5 ('If the lease "
     "expires before the client receives a DHCPACK, the client moves to "
     "INIT state'); sec.3.1 (DHCPNAK restarts the configuration process)"),
    ("REBINDING", "DHCPACK/Record lease, set timers T1, T2", "BOUND",
     "RFC 2131 sec.4.4 Figure 5 (second 'DHCPACK/Record lease' label on the "
     "REBINDING-to-BOUND path); sec.4.4.5 (REBINDING awaits a DHCPACK like "
     "RENEWING)"),
    ("REBINDING", "DHCPNAK, Lease expired/Halt network", "INIT",
     "RFC 2131 sec.4.4 Figure 5 (label above REBINDING + right-side rail "
     "into INIT); sec.4.4.5 ('If the lease expires before the client "
     "receives a DHCPACK, the client moves to INIT state' -- stated for "
     "both RENEWING and REBINDING)"),
    ("INIT-REBOOT", "-/Send DHCPREQUEST", "REBOOTING",
     "RFC 2131 sec.4.4 Figure 5; sec.4.4.2 ('The client begins in "
     "INIT-REBOOT state and sends a DHCPREQUEST message')"),
    ("REBOOTING", "DHCPACK/Record lease, set timers T1, T2", "BOUND",
     "RFC 2131 sec.4.4 Figure 5; sec.4.4.2 ('Once a DHCPACK message with an "
     "'xid' field matching that in the client's DHCPREQUEST message arrives "
     "from any server, the client is initialized and moves to BOUND state')"),
    ("REBOOTING", "DHCPNAK/Discard offer", "INIT",
     "RFC 2131 sec.4.4 Figure 5; sec.3.2 ('If the client receives a DHCPNAK "
     "message, it cannot reuse its remembered network address ... moving to "
     "the INIT state in the DHCP state diagram'); sec.4.4.2"),
    ("INIT-REBOOT", "DHCPNAK/Restart", "INIT",
     "RFC 2131 sec.4.4 Figure 5 (label 'DHCPNAK/Restart'); sec.3.2 (NAK "
     "corresponds to 'the client moving to the INIT state in the DHCP state "
     "diagram')"),
]

EVENTS = []
for _, ev, _, _ in EDGES:
    if ev not in EVENTS:
        EVENTS.append(ev)

N_BITS = 4
N_STATES = 1 << N_BITS          # 16 = 8 real + 8 padding
REAL_STATES = list(range(8))

TRANSCRIPTION_NOTES = [
    "figure routing: RFC 2131's Figure 5 is a hand-drawn 1997 ASCII diagram; "
    "the exact routing of a few rails is ambiguous at pixel level (the two "
    "right-side rails into INIT labeled 'DHCPNAK/Halt network'; the discard "
    "self-loops). Where the drawing is ambiguous the edge endpoint is pinned "
    "by the section 3.1/3.2/4.4.x prose, which names the states explicitly; "
    "the figure label is kept verbatim as the event name.",
    "prose-only edge: REQUESTING --DHCPNAK/Restart configuration--> INIT is "
    "stated in sec.3.1 step 5 but is not drawn in Figure 5; it is "
    "transcribed from prose and its label is prose-derived, not a "
    "figure-printed string. The twin edge INIT-REBOOT --DHCPNAK/Restart--> "
    "INIT IS drawn (and stated in sec.3.2).",
    "right-side pair note: the figure prints 'DHCPNAK/Halt network' beside "
    "the far-right rail (from RENEWING) and 'DHCPNAK, Lease expired/Halt "
    "network' above REBINDING; sec.4.4.5 states the lease-expiry-to-INIT "
    "rule for BOTH RENEWING and REBINDING ('In both RENEWING and REBINDING "
    "states...' sec.4.4.5; 'If the lease expires before the client receives "
    "a DHCPACK, the client moves to INIT state'), so both INIT-transitions "
    "are RFC-supported regardless of which label is read onto which rail.",
    "not collected: retransmission timeouts (sec.4.1 -- retransmits are "
    "self-loops with no state change; the encoding already maps undeclared "
    "events to self-loops, so they are not declared as actions); the "
    "'silently discarded' stray-message rules of sec.4.4.1 beyond the two "
    "discard self-loops the figure actually draws (REQUESTING "
    "'DHCPOFFER/Discard', BOUND 'DHCPOFFER, DHCPACK, DHCPNAK/Discard'); "
    "DHCPINFORM (the RFC itself remarks 'The DHCPINFORM message is not shown "
    "in figure 5', sec.4.4 intro).",
    "encoding: states 8..15 are unreachable padding to reach 2^4 (engine "
    "input contract); any (state, event) pair not listed in EDGES self-loops "
    "with reward 0 (undeclared event = no state change); rewards are all "
    "zero because DHCP defines no payoff; goals is empty.",
    "twin pair: RENEWING and REBINDING are the RFC's own conceptual twins "
    "(sec.4.4.5: both send DHCPREQUEST to extend the lease, differing in "
    "unicast vs broadcast and in T1 vs T2). Whether they are interchangeable "
    "as STATES is a question for the data -- see groups/renew_rebind.json "
    "and the case README. The twin edges they DO share verbatim: both leave "
    "on the identical label 'DHCPACK/Record lease, set timers T1, T2'.",
    "provenance: transcribed fresh from RFC 2131 text (fetched from "
    "rfc-editor.org on 2026-10-31) for this repository; no base model was "
    "copied.",
]

# ------------------------------------------------- expected verdict table
# Observed on 2026-10-31 from a live three-way arbitration run
# (`python -X utf8 -m symmetry_court arbitrate --emit-expected-template`;
# receipt: verdicts/dhcp.verdict.json). The gate
# (`python -X utf8 -m symmetry_court selftest`) replays every case and
# compares these pinned rows field-by-field against a fresh run.
EXPECTED_ROWS = {
    "init_start": {
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
    "reboot_rebind": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "generalized"},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": False, "labeled_symmetry": False},
    },
    "renew_rebind": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "generalized"},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": False, "labeled_symmetry": False},
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
        "case": "dhcp",
        "provenance": {
            "recorded": ("2026-10-31, observed from a live three-way "
                         "arbitration run (`python -X utf8 -m symmetry_court "
                         "arbitrate --emit-expected-template`); the receipt "
                         "is verdicts/dhcp.verdict.json; the gate "
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
            "source_system": ("DHCP client state-transition diagram, "
                              "transcribed from RFC 2131 section 4.4 Figure 5, "
                              "cross-checked against sections 3.1, 3.2 and "
                              "4.4.1-4.4.5. RFC 2131 is a public standard "
                              "(proposed standard, March 1997)."),
            "variant": "dhcp-rfc2131-client",
            "source_citation": ("RFC 2131 (March 1997), section 4.4, "
                                "Figure 5 'State-transition diagram for DHCP "
                                "clients'; sections 3.1, 3.2, 4.4.1-4.4.5 for "
                                "cross-checks. Per-edge citations in "
                                "meta.edges_with_citations."),
            "state_names": STATES,
            "action_names": EVENTS,
            "real_states": REAL_STATES,
            "semantics_class": ("event: the actions are protocol messages or "
                                "timer events named by the figure labels; "
                                "their names are part of the behavior and do "
                                "not follow state renamings -- candidate "
                                "groups in groups/ declare semantics "
                                "\"fixed\". The relabel rows in "
                                "expected.json are the diagnostic contrast "
                                "reading, not the protocol-true one."),
            "encoding": ("states 8..15 = unreachable padding (self-loop "
                         "only); undeclared (state, event) pairs self-loop "
                         "with reward 0"),
            "reward_rule": ("rewards all zero: DHCP defines no payoff; the "
                            "reward layer carries no information, all "
                            "conclusions come from the transition layer"),
            "edges_with_citations": [
                {"from": u, "event": ev, "to": v, "citation": c}
                for u, ev, v, c in EDGES
            ],
            "transcription_notes": TRANSCRIPTION_NOTES,
            "regenerate": "python -X utf8 cases/dhcp/make_dhcp.py",
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
    renew, rebind = idx["RENEWING"], idx["REBINDING"]
    reboot = idx["REBOOTING"]
    init, init_reboot = idx["INIT"], idx["INIT-REBOOT"]
    pad_a, pad_b = 8, 9
    regen = "python -X utf8 cases/dhcp/make_dhcp.py"

    return {
        "renew_rebind.json": _group(
            [(renew, rebind)],
            {
                "claim": ("defendant A: RENEWING and REBINDING are the "
                          "protocol's own twin pair -- both are lease-"
                          "extension waiting rooms that send DHCPREQUEST and "
                          "leave on the identical 'DHCPACK/Record lease' "
                          "label -- so they could be swapped and compressed "
                          "into one state"),
                "construction": ("order-2 group swapping RENEWING <-> "
                                 "REBINDING (states %d <-> %d)"
                                 % (renew, rebind)),
                "why_it_looks_legal": ("sec.4.4.5 describes them as the same "
                                       "activity differing only in unicast "
                                       "vs broadcast; both leave on the "
                                       "identical event label "
                                       "'DHCPACK/Record lease, set timers "
                                       "T1, T2' toward BOUND"),
                "why_it_is_not_a_symmetry": ("RENEWING has a third outgoing "
                                             "edge (T2 expires/Broadcast "
                                             "DHCPREQUEST -> REBINDING) that "
                                             "REBINDING lacks, and REBINDING "
                                             "cannot reach RENEWING; their "
                                             "event sets differ (DHCPNAK vs "
                                             "'DHCPNAK, Lease expired' "
                                             "labels, T2 broadcast vs no "
                                             "T2)"),
                "semantics_note": ("event-class model: semantics declared "
                                   "\"fixed\"; the relabel row in "
                                   "expected.json is the diagnostic contrast "
                                   "reading"),
                "regenerate": regen,
            }),
        "reboot_rebind.json": _group(
            [(reboot, rebind)],
            {
                "claim": ("defendant B: REBOOTING and REBINDING have the same "
                          "graph shape -- exactly one in-neighbor, two "
                          "outgoing edges, both toward BOUND and INIT -- so "
                          "they could be swapped"),
                "construction": ("order-2 group swapping REBOOTING <-> "
                                 "REBINDING (states %d <-> %d)"
                                 % (reboot, rebind)),
                "why_it_looks_legal": ("degree signatures match exactly: one "
                                       "in-neighbor each (INIT-REBOOT vs "
                                       "RENEWING), and both leave toward "
                                       "{BOUND, INIT}"),
                "why_it_is_not_a_symmetry": ("the in-neighborhoods are "
                                             "themselves non-interchangeable "
                                             "(INIT-REBOOT has 2 outgoing "
                                             "edges and no incoming ones; "
                                             "RENEWING has 3 outgoing and 1 "
                                             "incoming), and the event labels "
                                             "differ ('DHCPNAK/Discard offer' "
                                             "vs 'DHCPNAK, Lease expired/"
                                             "Halt network')"),
                "semantics_note": ("event-class model: semantics declared "
                                   "\"fixed\""),
                "regenerate": regen,
            }),
        "init_start.json": _group(
            [(init, init_reboot)],
            {
                "claim": ("defendant C (control): INIT and INIT-REBOOT are "
                          "both starting states of the diagram, so they could "
                          "be swapped"),
                "construction": ("order-2 group swapping INIT <-> INIT-REBOOT "
                                 "(states %d <-> %d)" % (init, init_reboot)),
                "why_it_looks_legal": ("both are the diagram's entry points "
                                       "(fresh start vs reboot with known "
                                       "address)"),
                "why_it_is_not_a_symmetry": ("INIT receives 5 incoming edges "
                                             "from four different states plus "
                                             "the DECLINE edge, INIT-REBOOT "
                                             "receives none; INIT leaves on "
                                             "'-/Send DHCPDISCOVER', "
                                             "INIT-REBOOT on '-/Send "
                                             "DHCPREQUEST' and "
                                             "'DHCPNAK/Restart'"),
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

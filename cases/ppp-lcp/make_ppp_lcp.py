# -*- coding: utf-8 -*-
"""
make_ppp_lcp.py -- deterministic generator for the field-trial2 case: the
PPP Link Control Protocol option-negotiation automaton, transcribed from
RFC 1661.

Writes, byte-identical on every re-run (nothing random, no clock, no locale
dependence), next to this script:

  model.json                     the trans model: 10 real states + 6 padding
                                 states (2^4 input contract), 16 events,
                                 rewards all zero
  expected.json                  hand-derived expected rows (live-run
                                 confirmed; see provenance.recorded)
  groups/ack-twins-swap.json     defendant A: Ack-Rcvd <-> Ack-Sent twin swap
                                 (claim)
  groups/closing-stopping-swap.json  defendant B: Closing <-> Stopping alone
  groups/closed-stopped-swap.json    defendant C: Closed <-> Stopped alone
  groups/pads.json               positive control: padding-state swap

Transcription authority: RFC 1661 (Point-to-Point Protocol, July 1994)
section 4 "The Option Negotiation Automaton": the sec.4.1 State Transition
Table (both halves), plus the sec.4.1 preamble, the footnote definitions and
the sec.4.2/4.3 prose that the footnotes point to. EVERY declared cell of the
table (all 120 of them, both halves, all 16 event rows x 10 state columns)
is transcribed cell for cell; each collected edge carries its section
citation, the printed cell text, and the snapshot line number in
meta.edges_with_citations. Deviations/policies are declared in
meta.transcription_notes.

The encoding policy follows the court's tcp and http2 cases: undeclared
(state, event) pairs -- here also the table's '-' illegal-transition cells --
self-loop with reward 0, padding states self-loop everything, rewards all
zero (the negotiation automaton defines no payoff), goals empty.

States (RFC-printed table headers, snapshot txt:736 and txt:781): Initial(0),
Starting(1), Closed(2), Stopped(3), Closing(4), Stopping(5), Req-Sent(6),
Ack-Rcvd(7), Ack-Sent(8), Opened(9). Slots 10..15 are padding. (sec.4.2
prints the long forms Request-Sent / Ack-Received for states 6 and 7.)
Events are the table's own row labels, RFC-printed: Up, Down, Open, Close,
TO+, TO-, RCR+, RCR-, RCA, RCN, RTR, RTA, RUC, RXJ+, RXJ-, RXR.

Usage:
  python -X utf8 make_ppp_lcp.py            # write all files
  python -X utf8 make_ppp_lcp.py --out DIR  # write into DIR
  python -X utf8 make_ppp_lcp.py --check    # verify bytes, exit 0/1
"""
import argparse
import json
import os
import sys

# ---------------------------------------------------------------- data
STATES = ["Initial", "Starting", "Closed", "Stopped", "Closing", "Stopping",
          "Req-Sent", "Ack-Rcvd", "Ack-Sent", "Opened"]

N_BITS = 4
N_STATES = 1 << N_BITS          # 16 slots
REAL_STATES = list(range(10))   # 0..9 real; 10..15 padding
PAD_STATES = list(range(10, 16))

EVENTS = ["Up", "Down", "Open", "Close", "TO+", "TO-",
          "RCR+", "RCR-", "RCA", "RCN", "RTR", "RTA", "RUC", "RXJ+", "RXJ-",
          "RXR"]


def _cell(row, col, cell_text, line, extra=""):
    c = ("RFC 1661 sec.4.1 State Transition Table, %s row, %s column: '%s' "
         "(snapshot txt:%d)" % (row, col, cell_text, line))
    if extra:
        c += " " + extra
    return c


_P = ("+ footnote p: Passive option (snapshot txt:818; sec.4.2 'Stopped' "
      "Implementation Option txt:894-904)")
_R = ("+ footnote r: Restart option (snapshot txt:820; sec.4.3 'Open' "
      "Implementation Option txt:1025-1041)")
_X = ("+ footnote x: crossed connection (snapshot txt:822; sec.4.3 'RCA' "
      "Implementation Note txt:1124-1135)")

# (from, event, to, citation) -- one entry per DECLARED table cell, both
# table halves, in row-then-column order (snapshot txt:738-758 upper half,
# txt:783-803 lower half). The printed cell text is quoted verbatim in each
# citation; state indices follow the RFC's own printed column numbers.
# Re-verified cell by cell against the snapshot during transcription.
EDGES = [
    # ---- Up (txt:738 upper, txt:783 lower: '-' for states 2..9)
    (0, "Up", 2, _cell("Up", "Initial", "2", 738)),
    (1, "Up", 6, _cell("Up", "Starting", "irc,scr/6", 738)),
    # ---- Down (txt:739, txt:784)
    (2, "Down", 0, _cell("Down", "Closed", "0", 739)),
    (3, "Down", 1, _cell("Down", "Stopped", "tls/1", 739)),
    (4, "Down", 0, _cell("Down", "Closing", "0", 739)),
    (5, "Down", 1, _cell("Down", "Stopping", "1", 739)),
    (6, "Down", 1, _cell("Down", "Req-Sent", "1", 784)),
    (7, "Down", 1, _cell("Down", "Ack-Rcvd", "1", 784)),
    (8, "Down", 1, _cell("Down", "Ack-Sent", "1", 784)),
    (9, "Down", 1, _cell("Down", "Opened", "tld/1", 784)),
    # ---- Open (txt:740, txt:785)
    (0, "Open", 1, _cell("Open", "Initial", "tls/1", 740)),
    (1, "Open", 1, _cell("Open", "Starting", "1", 740)),
    (2, "Open", 6, _cell("Open", "Closed", "irc,scr/6", 740)),
    (3, "Open", 3, _cell("Open", "Stopped", "3r", 740, _R)),
    (4, "Open", 5, _cell("Open", "Closing", "5r", 740, _R)),
    (5, "Open", 5, _cell("Open", "Stopping", "5r", 740, _R)),
    (6, "Open", 6, _cell("Open", "Req-Sent", "6", 785)),
    (7, "Open", 7, _cell("Open", "Ack-Rcvd", "7", 785)),
    (8, "Open", 8, _cell("Open", "Ack-Sent", "8", 785)),
    (9, "Open", 9, _cell("Open", "Opened", "9r", 785, _R)),
    # ---- Close (txt:741, txt:786)
    (0, "Close", 0, _cell("Close", "Initial", "0", 741)),
    (1, "Close", 0, _cell("Close", "Starting", "tlf/0", 741)),
    (2, "Close", 2, _cell("Close", "Closed", "2", 741)),
    (3, "Close", 2, _cell("Close", "Stopped", "2", 741)),
    (4, "Close", 4, _cell("Close", "Closing", "4", 741)),
    (5, "Close", 4, _cell("Close", "Stopping", "4", 741)),
    (6, "Close", 4, _cell("Close", "Req-Sent", "irc,str/4", 786)),
    (7, "Close", 4, _cell("Close", "Ack-Rcvd", "irc,str/4", 786)),
    (8, "Close", 4, _cell("Close", "Ack-Sent", "irc,str/4", 786)),
    (9, "Close", 4, _cell("Close", "Opened", "tld,irc,str/4", 786)),
    # ---- TO+ (txt:743, txt:788)
    (4, "TO+", 4, _cell("TO+", "Closing", "str/4", 743)),
    (5, "TO+", 5, _cell("TO+", "Stopping", "str/5", 743)),
    (6, "TO+", 6, _cell("TO+", "Req-Sent", "scr/6", 788)),
    (7, "TO+", 6, _cell("TO+", "Ack-Rcvd", "scr/6", 788)),
    (8, "TO+", 8, _cell("TO+", "Ack-Sent", "scr/8", 788)),
    # ---- TO- (txt:744, txt:789)
    (4, "TO-", 2, _cell("TO-", "Closing", "tlf/2", 744)),
    (5, "TO-", 3, _cell("TO-", "Stopping", "tlf/3", 744)),
    (6, "TO-", 3, _cell("TO-", "Req-Sent", "tlf/3p", 789, _P)),
    (7, "TO-", 3, _cell("TO-", "Ack-Rcvd", "tlf/3p", 789, _P)),
    (8, "TO-", 3, _cell("TO-", "Ack-Sent", "tlf/3p", 789, _P)),
    # ---- RCR+ (txt:746, txt:791)
    (2, "RCR+", 2, _cell("RCR+", "Closed", "sta/2", 746)),
    (3, "RCR+", 8, _cell("RCR+", "Stopped", "irc,scr,sca/8", 746)),
    (4, "RCR+", 4, _cell("RCR+", "Closing", "4", 746)),
    (5, "RCR+", 5, _cell("RCR+", "Stopping", "5", 746)),
    (6, "RCR+", 8, _cell("RCR+", "Req-Sent", "sca/8", 791)),
    (7, "RCR+", 9, _cell("RCR+", "Ack-Rcvd", "sca,tlu/9", 791)),
    (8, "RCR+", 8, _cell("RCR+", "Ack-Sent", "sca/8", 791)),
    (9, "RCR+", 8, _cell("RCR+", "Opened", "tld,scr,sca/8", 791)),
    # ---- RCR- (txt:747, txt:792)
    (2, "RCR-", 2, _cell("RCR-", "Closed", "sta/2", 747)),
    (3, "RCR-", 6, _cell("RCR-", "Stopped", "irc,scr,scn/6", 747)),
    (4, "RCR-", 4, _cell("RCR-", "Closing", "4", 747)),
    (5, "RCR-", 5, _cell("RCR-", "Stopping", "5", 747)),
    (6, "RCR-", 6, _cell("RCR-", "Req-Sent", "scn/6", 792)),
    (7, "RCR-", 7, _cell("RCR-", "Ack-Rcvd", "scn/7", 792)),
    (8, "RCR-", 6, _cell("RCR-", "Ack-Sent", "scn/6", 792)),
    (9, "RCR-", 6, _cell("RCR-", "Opened", "tld,scr,scn/6", 792)),
    # ---- RCA (txt:748, txt:793)
    (2, "RCA", 2, _cell("RCA", "Closed", "sta/2", 748)),
    (3, "RCA", 3, _cell("RCA", "Stopped", "sta/3", 748)),
    (4, "RCA", 4, _cell("RCA", "Closing", "4", 748)),
    (5, "RCA", 5, _cell("RCA", "Stopping", "5", 748)),
    (6, "RCA", 7, _cell("RCA", "Req-Sent", "irc/7", 793)),
    (7, "RCA", 6, _cell("RCA", "Ack-Rcvd", "scr/6x", 793, _X)),
    (8, "RCA", 9, _cell("RCA", "Ack-Sent", "irc,tlu/9", 793)),
    (9, "RCA", 6, _cell("RCA", "Opened", "tld,scr/6x", 793, _X)),
    # ---- RCN (txt:749, txt:794)
    (2, "RCN", 2, _cell("RCN", "Closed", "sta/2", 749)),
    (3, "RCN", 3, _cell("RCN", "Stopped", "sta/3", 749)),
    (4, "RCN", 4, _cell("RCN", "Closing", "4", 749)),
    (5, "RCN", 5, _cell("RCN", "Stopping", "5", 749)),
    (6, "RCN", 6, _cell("RCN", "Req-Sent", "irc,scr/6", 794)),
    (7, "RCN", 6, _cell("RCN", "Ack-Rcvd", "scr/6x", 794, _X)),
    (8, "RCN", 8, _cell("RCN", "Ack-Sent", "irc,scr/8", 794)),
    (9, "RCN", 6, _cell("RCN", "Opened", "tld,scr/6x", 794, _X)),
    # ---- RTR (txt:751, txt:796)
    (2, "RTR", 2, _cell("RTR", "Closed", "sta/2", 751)),
    (3, "RTR", 3, _cell("RTR", "Stopped", "sta/3", 751)),
    (4, "RTR", 4, _cell("RTR", "Closing", "sta/4", 751)),
    (5, "RTR", 5, _cell("RTR", "Stopping", "sta/5", 751)),
    (6, "RTR", 6, _cell("RTR", "Req-Sent", "sta/6", 796)),
    (7, "RTR", 6, _cell("RTR", "Ack-Rcvd", "sta/6", 796)),
    (8, "RTR", 6, _cell("RTR", "Ack-Sent", "sta/6", 796)),
    (9, "RTR", 5, _cell("RTR", "Opened", "tld,zrc,sta/5", 796)),
    # ---- RTA (txt:752, txt:797)
    (2, "RTA", 2, _cell("RTA", "Closed", "2", 752)),
    (3, "RTA", 3, _cell("RTA", "Stopped", "3", 752)),
    (4, "RTA", 2, _cell("RTA", "Closing", "tlf/2", 752)),
    (5, "RTA", 3, _cell("RTA", "Stopping", "tlf/3", 752)),
    (6, "RTA", 6, _cell("RTA", "Req-Sent", "6", 797)),
    (7, "RTA", 6, _cell("RTA", "Ack-Rcvd", "6", 797)),
    (8, "RTA", 8, _cell("RTA", "Ack-Sent", "8", 797)),
    (9, "RTA", 6, _cell("RTA", "Opened", "tld,scr/6", 797)),
    # ---- RUC (txt:754, txt:799)
    (2, "RUC", 2, _cell("RUC", "Closed", "scj/2", 754)),
    (3, "RUC", 3, _cell("RUC", "Stopped", "scj/3", 754)),
    (4, "RUC", 4, _cell("RUC", "Closing", "scj/4", 754)),
    (5, "RUC", 5, _cell("RUC", "Stopping", "scj/5", 754)),
    (6, "RUC", 6, _cell("RUC", "Req-Sent", "scj/6", 799)),
    (7, "RUC", 7, _cell("RUC", "Ack-Rcvd", "scj/7", 799)),
    (8, "RUC", 8, _cell("RUC", "Ack-Sent", "scj/8", 799)),
    (9, "RUC", 9, _cell("RUC", "Opened", "scj/9", 799)),
    # ---- RXJ+ (txt:755, txt:800)
    (2, "RXJ+", 2, _cell("RXJ+", "Closed", "2", 755)),
    (3, "RXJ+", 3, _cell("RXJ+", "Stopped", "3", 755)),
    (4, "RXJ+", 4, _cell("RXJ+", "Closing", "4", 755)),
    (5, "RXJ+", 5, _cell("RXJ+", "Stopping", "5", 755)),
    (6, "RXJ+", 6, _cell("RXJ+", "Req-Sent", "6", 800)),
    (7, "RXJ+", 6, _cell("RXJ+", "Ack-Rcvd", "6", 800)),
    (8, "RXJ+", 8, _cell("RXJ+", "Ack-Sent", "8", 800)),
    (9, "RXJ+", 9, _cell("RXJ+", "Opened", "9", 800)),
    # ---- RXJ- (txt:756, txt:801)
    (2, "RXJ-", 2, _cell("RXJ-", "Closed", "tlf/2", 756)),
    (3, "RXJ-", 3, _cell("RXJ-", "Stopped", "tlf/3", 756)),
    (4, "RXJ-", 2, _cell("RXJ-", "Closing", "tlf/2", 756)),
    (5, "RXJ-", 3, _cell("RXJ-", "Stopping", "tlf/3", 756)),
    (6, "RXJ-", 3, _cell("RXJ-", "Req-Sent", "tlf/3", 801)),
    (7, "RXJ-", 3, _cell("RXJ-", "Ack-Rcvd", "tlf/3", 801)),
    (8, "RXJ-", 3, _cell("RXJ-", "Ack-Sent", "tlf/3", 801)),
    (9, "RXJ-", 5, _cell("RXJ-", "Opened", "tld,irc,str/5", 801)),
    # ---- RXR (txt:758, txt:803)
    (2, "RXR", 2, _cell("RXR", "Closed", "2", 758)),
    (3, "RXR", 3, _cell("RXR", "Stopped", "3", 758)),
    (4, "RXR", 4, _cell("RXR", "Closing", "4", 758)),
    (5, "RXR", 5, _cell("RXR", "Stopping", "5", 758)),
    (6, "RXR", 6, _cell("RXR", "Req-Sent", "6", 803)),
    (7, "RXR", 7, _cell("RXR", "Ack-Rcvd", "7", 803)),
    (8, "RXR", 8, _cell("RXR", "Ack-Sent", "8", 803)),
    (9, "RXR", 9, _cell("RXR", "Opened", "ser/9", 803)),
]

TRANSCRIPTION_NOTES = [
    ("KEPT (one event, three packets): RXR bundles Receive-Echo-Request / "
     "Receive-Echo-Reply / Receive-Discard-Request into a single event: the "
     "sec.4 preamble says these packet classes 'are not differentiated in "
     "the automaton descriptions ... they always cause the same "
     "transitions' (snapshot txt:676-681); the table has one RXR row "
     "(txt:758 / txt:803); sec.4.3 defines it (txt:1201-1207)."),
    ("KEPT (actions not modeled): each table cell is action/new-state "
     "(sec.4.1 preamble txt:726-729). The transcription keeps the "
     "transition target; the action lists (tlu/tld/tls/tlf, irc/zrc, "
     "scr/sca/scn, str/sta, scj, ser) are not part of the model layer -- "
     "the model encodes (state, event) -> state only, the same "
     "transition-layer-only policy as the tcp and http2 cases. The printed "
     "cell text stays visible in every edge citation."),
    ("NOT COLLECTED ('-' cells): the dash marks an illegal transition "
     "(sec.4.1 preamble txt:730-732); 40 of the 160 cells are '-' (Up x "
     "states 2..5 txt:738 and x states 6..9 txt:783, Down x Initial/"
     "Starting txt:739, TO+ and TO- x states 0..3 txt:743-744 and x Opened "
     "txt:788-789, the four receive rows x Initial/Starting txt:746-749 and "
     "RTR/RTA/RUC/RXJ+/RXJ-/RXR x Initial/Starting, Up already counted). "
     "They encode 'this event does not occur here' and collapse to the "
     "same self-loop as undeclared pairs (reward 0), per the tcp/http2 "
     "encoding policy."),
    ("KEPT (declared self-transitions): 67 of the 120 declared cells carry "
     "a new state equal to the source state (e.g. Open in Starting is "
     "plain '1' txt:740, Close in Initial is '0' txt:741, TO+ in Closing "
     "is 'str/4' txt:743, RTA in Req-Sent is '6' txt:797, RUC in Opened is "
     "'scj/9' txt:799). All are transcribed as ordinary edges (from == "
     "to) so the collected edge set mirrors the table cell for cell; in "
     "the trans matrix they coincide numerically with self-loops."),
    ("NOT COLLECTED (footnote semantics): the table's footnote letters "
     "p/r/x (txt:818/820/822) annotate implementation options -- Passive, "
     "Restart, crossed connection -- that change actions or reading, not "
     "the new-state column. The letters are quoted in the affected edges' "
     "citations and the option discussions are anchored (p: txt:894-904, "
     "r: txt:1025-1041, x: txt:1124-1135)."),
    ("NOT COLLECTED (cross-layer propagation): This-Layer-Up/Down actions "
     "signal NCP automata (sec.4.3 'Up' txt:979-986, 'Down' "
     "txt:1004-1006); that inter-automaton signaling is outside this "
     "case's scope (one LCP automaton, one endpoint)."),
    ("KEPT (state naming): state_names use the printed table-header "
     "abbreviations Req-Sent / Ack-Rcvd / Ack-Sent (txt:736, txt:781); "
     "sec.4.2 prints the long forms Request-Sent (txt:931) and "
     "Ack-Received (txt:945)."),
]

REGEN = "python -X utf8 field-trial2/cases/ppp-lcp/make_ppp_lcp.py"


# ---------------------------------------------------------------- builders
def build_trans():
    idx = {name: i for i, name in enumerate(STATES)}
    delta = {}
    for u, ev, v, _ in EDGES:
        key = (u, EVENTS.index(ev))
        if key in delta and delta[key] != v:
            raise ValueError("table conflict at %s" % (key,))
        delta[key] = v
    trans = []
    for s in range(N_STATES):
        row = []
        for ei in range(len(EVENTS)):
            if s in REAL_STATES and (s, ei) in delta:
                row.append([[1.0, delta[(s, ei)], 0.0]])
            else:
                row.append([[1.0, s, 0.0]])   # undeclared / '-' -> self-loop
        trans.append(row)
    return trans


def build_model():
    return {
        "n_bits": N_BITS,
        "n_actions": len(EVENTS),
        "n_states": N_STATES,
        "goals": [],
        "meta": {
            "source_system": ("PPP Link Control Protocol option-negotiation "
                              "automaton (one automaton as seen by one "
                              "endpoint), transcribed from RFC 1661 section "
                              "4 and its sec.4.1 State Transition Table. "
                              "RFC 1661 is a public standard (Internet "
                              "Standards Track; STD 51)."),
            "variant": "ppp-lcp-rfc1661",
            "source_citation": ("RFC 1661 (July 1994), section 4 'The "
                                "Option Negotiation Automaton', sec.4.1 "
                                "State Transition Table (both halves, all "
                                "16 event rows x 10 state columns) + "
                                "footnotes p/r/x + sec.4.2 States + sec.4.3 "
                                "Events. Per-edge citations with snapshot "
                                "line numbers in meta.edges_with_citations."),
            "state_names": STATES,
            "action_names": EVENTS,
            "real_states": REAL_STATES,
            "semantics_class": ("event: the actions are protocol events "
                                "(the table's own row labels Up/Down/Open/"
                                "Close/TO+/-/RCR+/-/RCA/RCN/RTR/RTA/RUC/"
                                "RXJ+/-/RXR); their names are part of the "
                                "behavior and do not follow state renamings "
                                "-- candidate groups in groups/ declare "
                                "semantics \"fixed\". The relabel rows in "
                                "expected.json are the diagnostic contrast "
                                "reading, not the protocol-true one."),
            "encoding": ("states 10..15 = unreachable padding (self-loop "
                         "only); undeclared (state, event) pairs and the "
                         "table's '-' illegal-transition cells self-loop "
                         "with reward 0"),
            "reward_rule": ("rewards all zero: the negotiation automaton "
                            "defines no payoff; the reward layer carries no "
                            "information, all conclusions come from the "
                            "transition layer"),
            "edges_with_citations": [
                {"from": STATES[u], "event": ev, "to": STATES[v],
                 "citation": c}
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


def build_groups():
    regen = REGEN
    return {
        "ack-twins-swap.json": _group(
            [_swap(7, 8)],
            {
                "claim": ("defendant A (claim): the negotiation automaton "
                          "is initiator/responder symmetric at the Ack "
                          "twins -- Ack-Rcvd and Ack-Sent are the two "
                          "one-step-from-Open states, and sec.4.2 describes "
                          "them in near-verbatim mirror sentences: "
                          "'Ack-Received': 'a Configure-Request has been "
                          "sent and a Configure-Ack has been received. The "
                          "Restart timer is still running, since a "
                          "Configure-Ack has not yet been sent' "
                          "(snapshot txt:945-949) vs 'Ack-Sent': 'a "
                          "Configure-Request and a Configure-Ack have both "
                          "been sent, but a Configure-Ack has not yet been "
                          "received. The Restart timer is running' "
                          "(snapshot txt:951-956) -- so swapping states "
                          "7 <-> 8 with every other state fixed should map "
                          "the negotiation race onto itself."),
                "construction": ("order-2 group swapping Ack-Rcvd <-> "
                                 "Ack-Sent (states 7 <-> 8); all other "
                                 "states fixed"),
                "why_it_looks_legal": ("both twins sit between Req-Sent and "
                                       "Opened with the Restart timer "
                                       "running, both drain to Stopped on "
                                       "TO-/RXJ- (txt:789, txt:801) and to "
                                       "Closing on Close (txt:786), and "
                                       "both fall to Starting on Down "
                                       "(txt:784) -- the sec.4.2 sentences "
                                       "are mirror-written"),
                "why_it_is_not_a_symmetry": ("the table breaks the swap "
                                             "even before event names are "
                                             "pinned: among declared cells "
                                             "Ack-Rcvd has 6 edges into "
                                             "Req-Sent (TO+ txt:788, RCA "
                                             "txt:793, RCN txt:794, RTR "
                                             "txt:796, RTA txt:797, RXJ+ "
                                             "txt:800) and 4 self-loops "
                                             "(Open txt:785, RCR- txt:792, "
                                             "RUC txt:799, RXR txt:803), "
                                             "while Ack-Sent has 2 edges "
                                             "into Req-Sent (RCR- txt:792, "
                                             "RTR txt:796) and 8 "
                                             "self-loops (Open, TO+, RCR+, "
                                             "RCN, RTA, RUC, RXJ+, RXR -- "
                                             "txt:785-803); a swap cannot "
                                             "map 6-to-Req-Sent onto "
                                             "2-to-Req-Sent. The direction "
                                             "of completion also flips: "
                                             "Ack-Rcvd finishes on RCR+ "
                                             "(sca,tlu/9 txt:791) while "
                                             "Ack-Sent finishes on RCA "
                                             "(irc,tlu/9 txt:793)"),
                "engineering_anchor": ("the twin reading is how one shared "
                                       "table serves both negotiation "
                                       "roles: whoever still owes the "
                                       "Configure-Ack is the mirror of "
                                       "whoever still waits for it "
                                       "(sec.4.2 txt:945-956); the RFC "
                                       "itself flags the crossed case as "
                                       "an anomaly, not a symmetry "
                                       "(footnote x, txt:822)"),
                "semantics_note": ("event-class model: semantics declared "
                                   "\"fixed\" (protocol-true reading); the "
                                   "relabel row is the diagnostic contrast "
                                   "reading"),
                "regenerate": regen,
            }),
        "closing-stopping-swap.json": _group(
            [_swap(4, 5)],
            {
                "claim": ("defendant B: Closing and Stopping are the "
                          "termination twins -- in both, a "
                          "Terminate-Request has been sent and the Restart "
                          "timer is running while waiting for a "
                          "Terminate-Ack, and sec.4.2 says 'The Stopping "
                          "state is the Open counterpart to the Closing "
                          "state' (snapshot txt:918-929, counterpart "
                          "sentence at txt:920; 'Closing' at txt:906-916), "
                          "so maybe states 4 <-> 5 can be swapped alone"),
                "construction": ("order-2 group swapping Closing <-> "
                                 "Stopping (states 4 <-> 5) only"),
                "why_it_looks_legal": ("both have the same TO+ retransmit "
                                       "self-loop (str/4 vs str/5, "
                                       "txt:743) and both are Closed/"
                                       "Stopped's waiting rooms"),
                "why_it_is_not_a_symmetry": ("their drains land on "
                                             "different shores: Closing's "
                                             "Down goes to Initial (txt:739) "
                                             "while Stopping's Down goes to "
                                             "Starting (txt:784); Closing's "
                                             "TO-/RTA/RXJ- drain to Closed "
                                             "(txt:744, txt:752, txt:756) "
                                             "while Stopping's drain to "
                                             "Stopped -- the swap would "
                                             "need Closing->Starting and "
                                             "Closing->Stopped edges, which "
                                             "no cell provides"),
                "semantics_note": ("control: expected to fail BOTH readings "
                                   "(structure itself breaks)"),
                "regenerate": regen,
            }),
        "closed-stopped-swap.json": _group(
            [_swap(2, 3)],
            {
                "claim": ("defendant C: Closed and Stopped are the quiet "
                          "twins -- in neither is a negotiation in flight, "
                          "in neither does the Restart timer run, and both "
                          "answer an unwanted Configure-Request with a "
                          "Terminate-Ack (sec.4.2 'Closed' txt:853-860, "
                          "'Stopped' txt:862-872; txt:864 'The Stopped "
                          "state is the Open counterpart to the Closed "
                          "state'), so maybe states 2 <-> 3 can be swapped "
                          "alone"),
                "construction": ("order-2 group swapping Closed <-> "
                                 "Stopped (states 2 <-> 3) only"),
                "why_it_looks_legal": ("both quiet states self-loop on "
                                       "RTA/RUC/RXJ+/RXR (txt:752, "
                                       "txt:754-758) and both keep "
                                       "RCR-style noise inside themselves "
                                       "with sta actions"),
                "why_it_is_not_a_symmetry": ("only Stopped can advance a "
                                             "negotiation: Stopped's RCR+ "
                                             "enters Ack-Sent (irc,scr,"
                                             "sca/8 txt:746) and its RCR- "
                                             "enters Req-Sent (irc,scr,"
                                             "scn/6 txt:747), while "
                                             "Closed's RCR+/RCR- self-loop "
                                             "with sta/2 (txt:746-747); "
                                             "and Closed's Open starts a "
                                             "negotiation into Req-Sent "
                                             "(irc,scr/6 txt:740) while "
                                             "Stopped's Open loops in "
                                             "place (3r txt:740) -- the "
                                             "swap would need Closed->"
                                             "Ack-Sent and Stopped->"
                                             "Req-Sent-via-Open edges, "
                                             "which no cell provides"),
                "semantics_note": ("control: expected to fail BOTH readings "
                                   "(structure itself breaks)"),
                "regenerate": regen,
            }),
        "pads.json": _group(
            [_swap(10, 11)],
            {
                "claim": ("positive control: padding states 10 and 11 have "
                          "byte-identical rows (every event self-loops, "
                          "reward 0), so the swap is a genuine symmetry "
                          "under BOTH readings and should be admitted "
                          "everywhere"),
                "construction": ("order-2 group swapping padding states 10 "
                                 "<-> 11"),
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
    "ack-twins-swap": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "generalized"},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": False, "labeled_symmetry": False},
    },
    "closing-stopping-swap": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "generalized"},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": False, "labeled_symmetry": False},
    },
    "closed-stopped-swap": {
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
        "case": "ppp-lcp",
        "provenance": {
            "recorded": (
                "2026-11-08 adoption into the official docket: the case bundle was "
                "copied byte-identical from the field-trial2 blind-trial round-2 case "
                "directory (8/8 files sha256-equal at copy time; oracle-input hashes "
                "match field-trial2/sealed/manifest.json), then the rows below were "
                "re-observed live in this repository via `python -X utf8 -m "
                "symmetry_court arbitrate --emit-expected-template --case ppp-lcp` -- "
                "relabel/fixed are this run's measured rows, field-for-field "
                "identical to the round-2 records; the receipt is "
                "verdicts/ppp-lcp.verdict.json; the gate (`python -X utf8 -m "
                "symmetry_court selftest`) replays the case and compares these rows "
                "field-by-field"),
            "reading_guide": (
                "relabel row = actions may be renamed along with states (diagnostic "
                "contrast reading for an event-class model); fixed row = event names "
                "pinned (the protocol-true reading, declared in each group file); "
                "networkx columns = independent juror"),
            "networkx_source": (
                "networkx columns are carried from the field-trial2 sealed truth "
                "(field-trial2/sealed/ppp-lcp.truth.json, independent oracle "
                "w2-independent-oracle, write-once after sealing "
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

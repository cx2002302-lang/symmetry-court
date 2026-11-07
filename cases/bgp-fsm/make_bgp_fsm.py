# -*- coding: utf-8 -*-
"""
make_bgp_fsm.py -- deterministic generator for the field-trial2 case: the
BGP-4 peer finite state machine, transcribed from RFC 4271 section 8.

Writes, byte-identical on every re-run (nothing random, no clock, no locale
dependence), next to this script:

  model.json                     the trans model: 6 real states + 2 padding
                                 states (2^3 input contract), 28 events,
                                 rewards all zero
  expected.json                  verdict rows taken from the live arbitration
                                 run (no rows pre-written; see
                                 provenance.recorded)
  groups/connect-active-swap.json     defendant A: Connect <-> Active swap
                                      (claim)
  groups/openconfirm-established-swap.json  defendant B: OpenConfirm <->
                                      Established alone (control)
  groups/opensent-openconfirm-swap.json     defendant C: OpenSent <->
                                      OpenConfirm alone (control)
  groups/pads.json               positive control: padding-state swap

Transcription authority: RFC 4271 (A Border Gateway Protocol 4 (BGP-4),
January 2006) section 8 "BGP Finite State Machine (FSM)": the event list of
sec.8.1.1-8.1.5 (Events 1-28, numbering per sec.8.2.1.4) plus the per-state
paragraphs of sec.8.2.2. EVERY (state, event) pair that the sec.8.2.2 prose
assigns an outcome -- a state change, an explicit "stays/remains", or an
explicit catch-all enumeration -- is transcribed as one edge carrying its
clause reference, the printed transition phrase, and the snapshot line range
in meta.edges_with_citations. Deviations/policies are declared in
meta.transcription_notes.

The encoding policy follows the court's tcp/http2/ppp cases: undeclared
(state, event) pairs self-loop with reward 0, padding states self-loop
everything, rewards all zero (the BGP FSM defines no payoff), goals empty.

States (sec.8.2.2's own paragraph order, snapshot txt:2941, txt:3010,
txt:3255, txt:3495, txt:3708, txt:3932): Idle(0), Connect(1), Active(2),
OpenSent(3), OpenConfirm(4), Established(5). Slots 6..7 are padding.
Events are sec.8.1's printed names in RFC event-number order (Event N =
action index N-1): ManualStart, ManualStop, AutomaticStart,
ManualStart_with_PassiveTcpEstablishment, ... , UpdateMsgErr.

Usage:
  python -X utf8 make_bgp_fsm.py            # write all files
  python -X utf8 make_bgp_fsm.py --out DIR  # write into DIR
  python -X utf8 make_bgp_fsm.py --check    # verify bytes, exit 0/1
"""
import argparse
import json
import os
import sys

# ---------------------------------------------------------------- data
STATES = ["Idle", "Connect", "Active", "OpenSent", "OpenConfirm",
          "Established"]

N_BITS = 3
N_STATES = 1 << N_BITS          # 8 slots
REAL_STATES = list(range(6))    # 0..5 real; 6..7 padding
PAD_STATES = list(range(6, 8))

EVENTS = [
    "ManualStart",                                      # Event 1  (txt:2375)
    "ManualStop",                                       # Event 2  (txt:2387)
    "AutomaticStart",                                   # Event 3  (txt:2398)
    "ManualStart_with_PassiveTcpEstablishment",         # Event 4  (txt:2425)
    "AutomaticStart_with_PassiveTcpEstablishment",      # Event 5  (txt:2442)
    "AutomaticStart_with_DampPeerOscillations",         # Event 6  (txt:2471)
    "AutomaticStart_with_DampPeerOscillations_and_PassiveTcpEstablishment",
                                                        # Event 7  (txt:2490)
    "AutomaticStop",                                    # Event 8  (txt:2511)
    "ConnectRetryTimer_Expires",                        # Event 9  (txt:2535)
    "HoldTimer_Expires",                                # Event 10 (txt:2542)
    "KeepaliveTimer_Expires",                           # Event 11 (txt:2548)
    "DelayOpenTimer_Expires",                           # Event 12 (txt:2554)
    "IdleHoldTimer_Expires",                            # Event 13 (txt:2567)
    "TcpConnection_Valid",                              # Event 14 (txt:2603)
    "Tcp_CR_Invalid",                                   # Event 15 (txt:2625)
    "Tcp_CR_Acked",                                     # Event 16 (txt:2652)
    "TcpConnectionConfirmed",                           # Event 17 (txt:2662)
    "TcpConnectionFails",                               # Event 18 (txt:2674)
    "BGPOpen",                                          # Event 19 (txt:2697)
    "BGPOpen_with_DelayOpenTimer_running",              # Event 20 (txt:2710)
    "BGPHeaderErr",                                     # Event 21 (txt:2724)
    "BGPOpenMsgErr",                                    # Event 22 (txt:2731)
    "OpenCollisionDump",                                # Event 23 (txt:2738)
    "NotifMsgVerErr",                                   # Event 24 (txt:2774)
    "NotifMsg",                                         # Event 25 (txt:2781)
    "KeepAliveMsg",                                     # Event 26 (txt:2789)
    "UpdateMsg",                                        # Event 27 (txt:2807)
    "UpdateMsgErr",                                     # Event 28 (txt:2814)
]

# RFC-printed state headers (sec.8.2.2) used in the citations.
_STATE_RFC = ["Idle state", "Connect State", "Active State", "OpenSent",
              "OpenConfirm State", "Established State"]


def _c(s, ref, quote, lines, extra=""):
    c = ("RFC 4271 sec.8.2.2 '%s', %s: '%s' (snapshot txt:%s)"
         % (_STATE_RFC[s], ref, quote, lines))
    if extra:
        c += " " + extra
    return c


# (from, rfc_event_number, to, citation) -- one entry per (state, event)
# pair the sec.8.2.2 prose assigns an outcome, state by state, events in
# ascending RFC numbering. Event N = action index N-1. The transition
# phrase is quoted from the snapshot; line ranges were re-verified against
# dossier/sources/rfc4271.txt during transcription.
EDGES = [
    # ---- Idle state (snapshot txt:2941-3008)
    (0, 1, 1, _c(0, "'In response to a ManualStart event (Event 1) or an "
                  "AutomaticStart event (Event 3)' paragraph",
                  "changes its state to Connect", "2947-2962")),
    (0, 3, 1, _c(0, "'In response to a ManualStart event (Event 1) or an "
                  "AutomaticStart event (Event 3)' paragraph",
                  "changes its state to Connect", "2947-2962")),
    (0, 4, 2, _c(0, "'In response to a ManualStart_with_PassiveTcpEstablishment"
                  " event (Event 4) or AutomaticStart_with_PassiveTcpEstablishment"
                  " event (Event 5)' paragraph",
                  "changes its state to Active", "2975-2988")),
    (0, 5, 2, _c(0, "'In response to a ManualStart_with_PassiveTcpEstablishment"
                  " event (Event 4) or AutomaticStart_with_PassiveTcpEstablishment"
                  " event (Event 5)' paragraph",
                  "changes its state to Active", "2975-2988")),
    # ---- Connect State (snapshot txt:3010-3244)
    (1, 2, 0, _c(1, "'In response to a ManualStop event (Event 2)' paragraph",
                 "changes its state to Idle", "3017-3036")),
    (1, 9, 1, _c(1, "'In response to the ConnectRetryTimer_Expires event "
                  "(Event 9)' paragraph", "stays in the Connect state",
                 "3038-3052")),
    (1, 12, 3, _c(1, "'If the DelayOpenTimer_Expires event (Event 12) occurs "
                  "in the Connect state' paragraph",
                  "changes its state to OpenSent", "3054-3061")),
    (1, 14, 1, _c(1, "'If the BGP FSM receives a TcpConnection_Valid event "
                  "(Event 14)' paragraph",
                  "the connection remains in the Connect state", "3063-3065")),
    (1, 15, 1, _c(1, "'If the BGP FSM receives a Tcp_CR_Invalid event "
                  "(Event 15)' paragraph",
                  "remains in the Connect state", "3067-3069")),
    (1, 16, 3, _c(1, "'If the TCP connection succeeds (Event 16 or Event 17)' "
                  "paragraph, DelayOpen=FALSE branch",
                  "changes its state to OpenSent", "3089-3100",
                  "[the DelayOpen=TRUE branch 'stays in the Connect state' "
                  "(txt:3071-3087) is attribute-conditional, NOT COLLECTED "
                  "-- see transcription_notes]")),
    (1, 17, 3, _c(1, "'If the TCP connection succeeds (Event 16 or Event 17)' "
                  "paragraph, DelayOpen=FALSE branch",
                  "changes its state to OpenSent", "3089-3100",
                  "[the DelayOpen=TRUE branch 'stays in the Connect state' "
                  "(txt:3071-3087) is attribute-conditional, NOT COLLECTED "
                  "-- see transcription_notes]")),
    (1, 18, 0, _c(1, "'If the TCP connection fails (Event 18)' paragraph, "
                  "DelayOpenTimer-not-running branch",
                  "changes its state to Idle", "3117-3125",
                  "[the DelayOpenTimer-running branch 'changes its state to "
                  "Active' (txt:3104-3115) is attribute-conditional, NOT "
                  "COLLECTED -- see transcription_notes]")),
    (1, 20, 4, _c(1, "'If an OPEN message is received while the DelayOpenTimer "
                  "is running (Event 20)' paragraph",
                  "changes its state to OpenConfirm", "3127-3161")),
    (1, 21, 0, _c(1, "'If BGP message header checking (Event 21) or OPEN "
                  "message checking detects an error (Event 22)' paragraph",
                  "changes its state to Idle", "3167-3186")),
    (1, 22, 0, _c(1, "'If BGP message header checking (Event 21) or OPEN "
                  "message checking detects an error (Event 22)' paragraph",
                  "changes its state to Idle", "3167-3186")),
    (1, 24, 0, _c(1, "'If a NOTIFICATION message is received with a version "
                  "error (Event 24)' paragraph",
                  "changes its state to Idle", "3188-3224",
                  "[both DelayOpenTimer branches land on Idle]")),
    # Connect catch-all (Events 8, 10-11, 13, 19, 23, 25-28)
    (1, 8, 0, _c(1, "catch-all 'In response to any other events (Events 8, "
                 "10-11, 13, 19, 23, 25-28)' paragraph",
                 "changes its state to Idle", "3226-3244")),
    (1, 10, 0, _c(1, "catch-all 'In response to any other events (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3226-3244")),
    (1, 11, 0, _c(1, "catch-all 'In response to any other events (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3226-3244")),
    (1, 13, 0, _c(1, "catch-all 'In response to any other events (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3226-3244")),
    (1, 19, 0, _c(1, "catch-all 'In response to any other events (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3226-3244")),
    (1, 23, 0, _c(1, "catch-all 'In response to any other events (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3226-3244")),
    (1, 25, 0, _c(1, "catch-all 'In response to any other events (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3226-3244")),
    (1, 26, 0, _c(1, "catch-all 'In response to any other events (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3226-3244")),
    (1, 27, 0, _c(1, "catch-all 'In response to any other events (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3226-3244")),
    (1, 28, 0, _c(1, "catch-all 'In response to any other events (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3226-3244")),
    # ---- Active State (snapshot txt:3255-3493)
    (2, 2, 0, _c(2, "'In response to a ManualStop event (Event 2)' paragraph",
                 "changes its state to Idle", "3262-3278")),
    (2, 9, 1, _c(2, "'In response to a ConnectRetryTimer_Expires event "
                 "(Event 9)' paragraph", "changes its state to Connect",
                 "3280-3290")),
    (2, 12, 3, _c(2, "'If the local system receives a DelayOpenTimer_Expires "
                  "event (Event 12)' paragraph",
                  "changes its state to OpenSent", "3292-3313")),
    (2, 14, 2, _c(2, "'If the local system receives a TcpConnection_Valid "
                  "event (Event 14)' paragraph",
                  "stays in the Active state", "3318-3320")),
    (2, 15, 2, _c(2, "'If the local system receives a Tcp_CR_Invalid event "
                  "(Event 15)' paragraph",
                  "stays in the Active State", "3322-3324")),
    (2, 16, 3, _c(2, "'In response to the success of a TCP connection (Event "
                  "16 or Event 17)' paragraph, DelayOpen=FALSE branch",
                  "changes its state to OpenSent", "3340-3350",
                  "[the DelayOpen=TRUE branch 'stays in the Active state' "
                  "(txt:3330-3338) is attribute-conditional, NOT COLLECTED "
                  "-- see transcription_notes]")),
    (2, 17, 3, _c(2, "'In response to the success of a TCP connection (Event "
                  "16 or Event 17)' paragraph, DelayOpen=FALSE branch",
                  "changes its state to OpenSent", "3340-3350",
                  "[the DelayOpen=TRUE branch 'stays in the Active state' "
                  "(txt:3330-3338) is attribute-conditional, NOT COLLECTED "
                  "-- see transcription_notes]")),
    (2, 18, 0, _c(2, "'If the local system receives a TcpConnectionFails "
                  "event (Event 18)' paragraph (no DelayOpenTimer branch in "
                  "this state's prose)",
                  "changes its state to Idle", "3355-3376")),
    (2, 20, 4, _c(2, "'If an OPEN message is received and the DelayOpenTimer "
                  "is running (Event 20)' paragraph",
                  "changes its state to OpenConfirm", "3378-3404")),
    (2, 21, 0, _c(2, "'If BGP message header checking (Event 21) or OPEN "
                  "message checking detects an error (Event 22)' paragraph",
                  "changes its state to Idle", "3410-3438")),
    (2, 22, 0, _c(2, "'If BGP message header checking (Event 21) or OPEN "
                  "message checking detects an error (Event 22)' paragraph",
                  "changes its state to Idle", "3410-3438")),
    (2, 24, 0, _c(2, "'If a NOTIFICATION message is received with a version "
                  "error (Event 24)' paragraph",
                  "changes its state to Idle", "3440-3468",
                  "[both DelayOpenTimer branches land on Idle]")),
    # Active catch-all (Events 8, 10-11, 13, 19, 23, 25-28)
    (2, 8, 0, _c(2, "catch-all 'In response to any other event (Events 8, "
                 "10-11, 13, 19, 23, 25-28)' paragraph",
                 "changes its state to Idle", "3479-3493")),
    (2, 10, 0, _c(2, "catch-all 'In response to any other event (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3479-3493")),
    (2, 11, 0, _c(2, "catch-all 'In response to any other event (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3479-3493")),
    (2, 13, 0, _c(2, "catch-all 'In response to any other event (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3479-3493")),
    (2, 19, 0, _c(2, "catch-all 'In response to any other event (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3479-3493")),
    (2, 23, 0, _c(2, "catch-all 'In response to any other event (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3479-3493")),
    (2, 25, 0, _c(2, "catch-all 'In response to any other event (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3479-3493")),
    (2, 26, 0, _c(2, "catch-all 'In response to any other event (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3479-3493")),
    (2, 27, 0, _c(2, "catch-all 'In response to any other event (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3479-3493")),
    (2, 28, 0, _c(2, "catch-all 'In response to any other event (Events 8, "
                  "10-11, 13, 19, 23, 25-28)' paragraph",
                  "changes its state to Idle", "3479-3493")),
    # ---- OpenSent (snapshot txt:3495-3706)
    (3, 2, 0, _c(3, "'If a ManualStop event (Event 2) is issued in the "
                 "OpenSent state' paragraph",
                 "changes its state to Idle", "3502-3515")),
    (3, 8, 0, _c(3, "'If an AutomaticStop event (Event 8) is issued in the "
                 "OpenSent state' paragraph",
                 "changes its state to Idle", "3517-3540")),
    (3, 10, 0, _c(3, "'If the HoldTimer_Expires (Event 10)' paragraph",
                  "changes its state to Idle", "3542-3558")),
    (3, 18, 2, _c(3, "'If a TcpConnectionFails event (Event 18) is received' "
                  "paragraph", "changes its state to Active", "3569-3579")),
    (3, 19, 4, _c(3, "'If there are no errors in the OPEN message (Event 19)' "
                  "paragraph", "changes its state to OpenConfirm",
                  "3591-3606")),
    (3, 21, 0, _c(3, "'If the BGP message header checking (Event 21) or OPEN "
                  "message checking detects an error (Event 22)' paragraph",
                  "changes its state to Idle", "3615-3632")),
    (3, 22, 0, _c(3, "'If the BGP message header checking (Event 21) or OPEN "
                  "message checking detects an error (Event 22)' paragraph",
                  "changes its state to Idle", "3615-3632")),
    (3, 23, 0, _c(3, "'If such an event [OpenCollisionDump (Event 23)] is "
                  "received in the OpenSent state' paragraph",
                  "changes its state to Idle", "3651-3669")),
    (3, 24, 0, _c(3, "'If a NOTIFICATION message is received with a version "
                  "error (Event 24)' paragraph",
                  "changes its state to Idle", "3671-3680")),
    # OpenSent catch-all (Events 9, 11-13, 20, 25-28)
    (3, 9, 0, _c(3, "catch-all 'In response to any other event (Events 9, "
                 "11-13, 20, 25-28)' paragraph",
                 "changes its state to Idle", "3682-3706")),
    (3, 11, 0, _c(3, "catch-all 'In response to any other event (Events 9, "
                  "11-13, 20, 25-28)' paragraph",
                  "changes its state to Idle", "3682-3706")),
    (3, 12, 0, _c(3, "catch-all 'In response to any other event (Events 9, "
                  "11-13, 20, 25-28)' paragraph",
                  "changes its state to Idle", "3682-3706")),
    (3, 13, 0, _c(3, "catch-all 'In response to any other event (Events 9, "
                  "11-13, 20, 25-28)' paragraph",
                  "changes its state to Idle", "3682-3706")),
    (3, 20, 0, _c(3, "catch-all 'In response to any other event (Events 9, "
                  "11-13, 20, 25-28)' paragraph",
                  "changes its state to Idle", "3682-3706")),
    (3, 25, 0, _c(3, "catch-all 'In response to any other event (Events 9, "
                  "11-13, 20, 25-28)' paragraph",
                  "changes its state to Idle", "3682-3706")),
    (3, 26, 0, _c(3, "catch-all 'In response to any other event (Events 9, "
                  "11-13, 20, 25-28)' paragraph",
                  "changes its state to Idle", "3682-3706")),
    (3, 27, 0, _c(3, "catch-all 'In response to any other event (Events 9, "
                  "11-13, 20, 25-28)' paragraph",
                  "changes its state to Idle", "3682-3706")),
    (3, 28, 0, _c(3, "catch-all 'In response to any other event (Events 9, "
                  "11-13, 20, 25-28)' paragraph",
                  "changes its state to Idle", "3682-3706")),
    # ---- OpenConfirm State (snapshot txt:3708-3930)
    (4, 2, 0, _c(4, "'In response to a ManualStop event (Event 2) initiated "
                 "by the operator' paragraph",
                 "changes its state to Idle", "3715-3728")),
    (4, 8, 0, _c(4, "'In response to the AutomaticStop event initiated by "
                 "the system (Event 8)' paragraph",
                 "changes its state to Idle", "3730-3746")),
    (4, 10, 0, _c(4, "'If the HoldTimer_Expires event (Event 10) occurs "
                  "before a KEEPALIVE message is received' paragraph",
                  "changes its state to Idle", "3748-3773")),
    (4, 11, 4, _c(4, "'If the local system receives a KeepaliveTimer_Expires "
                  "event (Event 11)' paragraph",
                  "remains in the OpenConfirmed state", "3775-3782",
                  "[the RFC's printed spelling 'OpenConfirmed']")),
    (4, 18, 0, _c(4, "'If the local system receives a TcpConnectionFails "
                  "event (Event 18) from the underlying TCP or a "
                  "NOTIFICATION message (Event 25)' paragraph",
                  "changes its state to Idle", "3792-3815")),
    (4, 25, 0, _c(4, "'If the local system receives a TcpConnectionFails "
                  "event (Event 18) from the underlying TCP or a "
                  "NOTIFICATION message (Event 25)' paragraph",
                  "changes its state to Idle", "3792-3815")),
    (4, 24, 0, _c(4, "'If the local system receives a NOTIFICATION message "
                  "with a version error (NotifMsgVerErr (Event 24))' "
                  "paragraph", "changes its state to Idle", "3817-3826")),
    (4, 19, 0, _c(4, "'If the local system receives a valid OPEN message "
                  "(BGPOpen (Event 19))' paragraph, connection-collision-drop "
                  "branch", "changes its state to Idle", "3828-3846",
                  "[the no-collision case carries no declared transition -- "
                  "see transcription_notes]")),
    (4, 21, 0, _c(4, "'If the BGP message header checking (BGPHeaderErr "
                  "(Event 21)) or OPEN message checking detects an error "
                  "(BGPOpenMsgErr (Event 22))' paragraph",
                  "changes its state to Idle", "3848-3874")),
    (4, 22, 0, _c(4, "'If the BGP message header checking (BGPHeaderErr "
                  "(Event 21)) or OPEN message checking detects an error "
                  "(BGPOpenMsgErr (Event 22))' paragraph",
                  "changes its state to Idle", "3848-3874")),
    (4, 23, 0, _c(4, "'When the local system receives an OpenCollisionDump "
                  "event (Event 23)' paragraph",
                  "changes its state to Idle", "3876-3896")),
    (4, 26, 5, _c(4, "'If the local system receives a KEEPALIVE message "
                  "(KeepAliveMsg (Event 26))' paragraph",
                  "changes its state to Established", "3898-3903")),
    # OpenConfirm catch-all (Events 9, 12-13, 20, 27-28)
    (4, 9, 0, _c(4, "catch-all 'In response to any other event (Events 9, "
                 "12-13, 20, 27-28)' paragraph",
                 "changes its state to Idle", "3905-3930")),
    (4, 12, 0, _c(4, "catch-all 'In response to any other event (Events 9, "
                  "12-13, 20, 27-28)' paragraph",
                  "changes its state to Idle", "3905-3930")),
    (4, 13, 0, _c(4, "catch-all 'In response to any other event (Events 9, "
                  "12-13, 20, 27-28)' paragraph",
                  "changes its state to Idle", "3905-3930")),
    (4, 20, 0, _c(4, "catch-all 'In response to any other event (Events 9, "
                  "12-13, 20, 27-28)' paragraph",
                  "changes its state to Idle", "3905-3930")),
    (4, 27, 0, _c(4, "catch-all 'In response to any other event (Events 9, "
                  "12-13, 20, 27-28)' paragraph",
                  "changes its state to Idle", "3905-3930")),
    (4, 28, 0, _c(4, "catch-all 'In response to any other event (Events 9, "
                  "12-13, 20, 27-28)' paragraph",
                  "changes its state to Idle", "3905-3930")),
    # ---- Established State (snapshot txt:3932-4160)
    (5, 2, 0, _c(5, "'In response to a ManualStop event (initiated by an "
                 "operator) (Event 2)' paragraph",
                 "changes its state to Idle", "3940-3955")),
    (5, 8, 0, _c(5, "'In response to an AutomaticStop event (Event 8)' "
                 "paragraph", "changes its state to Idle", "3957-3974")),
    (5, 10, 0, _c(5, "'If the HoldTimer_Expires event occurs (Event 10)' "
                  "paragraph", "changes its state to Idle", "3988-4005")),
    (5, 18, 0, _c(5, "'If the local system receives a NOTIFICATION message "
                  "(Event 24 or Event 25) or a TcpConnectionFails (Event 18) "
                  "from the underlying TCP' paragraph",
                  "changes its state to Idle", "4064-4078")),
    (5, 24, 0, _c(5, "'If the local system receives a NOTIFICATION message "
                  "(Event 24 or Event 25) or a TcpConnectionFails (Event 18) "
                  "from the underlying TCP' paragraph",
                  "changes its state to Idle", "4064-4078")),
    (5, 25, 0, _c(5, "'If the local system receives a NOTIFICATION message "
                  "(Event 24 or Event 25) or a TcpConnectionFails (Event 18) "
                  "from the underlying TCP' paragraph",
                  "changes its state to Idle", "4064-4078")),
    (5, 26, 5, _c(5, "'If the local system receives a KEEPALIVE message "
                  "(Event 26)' paragraph",
                  "remains in the Established state", "4095-4101")),
    (5, 27, 5, _c(5, "'If the local system receives an UPDATE message "
                  "(Event 27)' paragraph",
                  "remains in the Established state", "4103-4111")),
    (5, 28, 0, _c(5, "'If the local system receives an UPDATE message, and "
                  "the UPDATE message error handling procedure (see Section "
                  "6.3) detects an error (Event 28)' paragraph",
                  "changes its state to Idle", "4113-4132")),
    # Established catch-all (Events 9, 12-13, 20-22)
    (5, 9, 0, _c(5, "catch-all 'In response to any other event (Events 9, "
                 "12-13, 20-22)' paragraph",
                 "changes its state to Idle", "4134-4160")),
    (5, 12, 0, _c(5, "catch-all 'In response to any other event (Events 9, "
                  "12-13, 20-22)' paragraph",
                  "changes its state to Idle", "4134-4160")),
    (5, 13, 0, _c(5, "catch-all 'In response to any other event (Events 9, "
                  "12-13, 20-22)' paragraph",
                  "changes its state to Idle", "4134-4160")),
    (5, 20, 0, _c(5, "catch-all 'In response to any other event (Events 9, "
                  "12-13, 20-22)' paragraph",
                  "changes its state to Idle", "4134-4160")),
    (5, 21, 0, _c(5, "catch-all 'In response to any other event (Events 9, "
                  "12-13, 20-22)' paragraph",
                  "changes its state to Idle", "4134-4160")),
    (5, 22, 0, _c(5, "catch-all 'In response to any other event (Events 9, "
                  "12-13, 20-22)' paragraph",
                  "changes its state to Idle", "4134-4160")),
]

TRANSCRIPTION_NOTES = [
    ("KEPT (one FSM per connection): the model transcribes ONE endpoint's "
     "automaton -- sec.8.2.1: 'BGP MUST maintain a separate FSM for each "
     "configured peer' (snapshot txt:2825); the two-peer collision "
     "resolution of sec.6.8 is a cross-connection procedure, not a state of "
     "one FSM, and the model does not merge two peers into one machine."),
    ("KEPT (base-attributes policy): the sec.8.2.2 prose branches on the "
     "optional session attributes of sec.8.1.1; the transcription takes the "
     "base configuration (DelayOpen=FALSE, PassiveTcpEstablishment=FALSE, "
     "DampPeerOscillations=FALSE, SendNOTIFICATIONwithoutOPEN=FALSE, "
     "CollisionDetectEstablishedState=FALSE), the parameterization sec.8.2.1.3 "
     "itself sketches: 'If an Optional Session attribute cannot be set to "
     "TRUE, the events supporting that set of options do not have to be "
     "supported' (txt:2885-2895). Events that are separate numbered events "
     "(4, 5, 12, 13, 20) are transcribed at their own declared outcomes even "
     "though they presuppose an attribute -- the RFC numbers them as events "
     "in their own right (sec.8.2.1.4, txt:2923-2928)."),
    ("NOT COLLECTED (attribute-conditional branches, one per paragraph "
     "branch): Connect Events 16/17 DelayOpen=TRUE branch 'stays in the "
     "Connect state' (txt:3071-3087); Connect Event 18 DelayOpenTimer-running "
     "branch 'changes its state to Active' (txt:3104-3115); Active Events "
     "16/17 DelayOpen=TRUE branch 'stays in the Active state' "
     "(txt:3330-3338); Established Events 19/23 CollisionDetectEstablishedState "
     "branch (txt:4039-4062) -- base reading: 'Normally, a Detect Collision "
     "will be ignored in the Established state' (sec.8.1.5 Event 23 "
     "attribute status, txt:2319-2325). Each collected edge's citation names "
     "its branch."),
    ("NOT COLLECTED (Idle damping group): Events 6, 7 and 13 in Idle -- "
     "'If the DampPeerOscillations attribute is set to TRUE, the following "
     "three additional events may occur within the Idle state' ... 'The "
     "method of preventing persistent peer oscillation is outside the scope "
     "of this document' (txt:2993-3005): no transition is declared, so the "
     "pairs collapse to the policy self-loop (reward 0)."),
    ("NOT COLLECTED (explicit no-change / ignored): Idle Events 2 and 8 "
     "'are ignored in the Idle state' (txt:2964-2965) and the Idle catch-all "
     "'Any other event (Events 9-12, 15-28) received in the Idle state does "
     "not cause change in the state of the local system' (txt:3007-3008); "
     "the start events (Events 1, 3-7) 'are ignored' in Connect (txt:3015), "
     "Active (txt:3260), OpenSent (txt:3499-3500), OpenConfirm "
     "(txt:3712-3713) and Established (txt:3937-3938). All collapse to the "
     "same self-loop as undeclared pairs, per the tcp/http2/ppp encoding "
     "policy."),
    ("NOT COLLECTED (tracked/ignored, no declared transition): OpenSent "
     "Events 14/16/17 'This second TCP connection is tracked per Connection "
     "Collision processing (Section 6.8) until an OPEN message is received' "
     "(txt:3560-3564) and Event 15 'is ignored' (txt:3566-3567); OpenConfirm "
     "Events 14/16/17 'needs to track the second connection' "
     "(txt:3784-3787) and Event 15 'will ignore the second connection "
     "attempt' (txt:3789-3790); Established Event 14 'will cause the second "
     "connection to be tracked' (txt:4019-4020), Event 15 'will be ignored' "
     "(txt:4022-4023), Events 16/17 'SHALL be tracked until it sends an "
     "OPEN message' (txt:4025-4027). No state-change sentence appears in "
     "any of these paragraphs."),
    ("NOT COLLECTED (no transition phrase): Established Event 11's paragraph "
     "declares actions only -- 'sends a KEEPALIVE message, and restarts its "
     "KeepaliveTimer, unless the negotiated HoldTime value is zero' "
     "(txt:4007-4013) -- with no state-change sentence, in contrast to "
     "OpenConfirm Event 11 which says 'remains in the OpenConfirmed state' "
     "(txt:3782). Transcribed as undeclared (policy self-loop)."),
    ("KEPT (conditional branch, protocol-internal condition): OpenConfirm "
     "Event 19's paragraph declares only the collision-drop branch 'changes "
     "its state to Idle' (txt:3828-3846); the no-collision case carries no "
     "declared transition. The declared branch is transcribed and the "
     "condition is named in the edge's citation -- collision handling is "
     "core sec.6.8 machinery, not an optional session attribute, so this "
     "branch is in base scope."),
    ("KEPT (event naming and numbering): event names are sec.8.1's printed "
     "names in RFC event-number order; the action index = event number - 1. "
     "Event 20 is printed 'BGPOpen with DelayOpenTimer running' (txt:2710) "
     "and appears in the model as 'BGPOpen_with_DelayOpenTimer_running'; "
     "Event 7's header wraps across two snapshot lines (txt:2490-2491) and "
     "the model uses the unwrapped form. The numbering 1-28 is the RFC's own "
     "(sec.8.2.1.4, txt:2923-2928)."),
    ("KEPT (state naming and order): the six state names follow sec.8.2.2's "
     "own paragraph order Idle / Connect / Active / OpenSent / OpenConfirm / "
     "Established (headers at txt:2941, txt:3010, txt:3255, txt:3495, "
     "txt:3708, txt:3932); slots 6-7 are padding. OpenConfirm Event 11's "
     "prose spells the state 'OpenConfirmed' (txt:3782) -- the model keeps "
     "the header spelling 'OpenConfirm' (txt:3708)."),
    ("KEPT (actions not modeled): every transition paragraph's action "
     "bullets (send NOTIFICATION/KEEPALIVE/OPEN, restart timers, release "
     "resources, ConnectRetryCounter updates, damping hooks) are not part "
     "of the model layer -- the model encodes (state, event) -> state only, "
     "the same transition-layer-only policy as the tcp/http2/ppp cases; the "
     "printed transition phrase stays visible in every edge citation."),
    ("KEPT (declared self-transitions): self-transitions the prose states "
     "explicitly are transcribed as ordinary edges (from == to): Connect "
     "Events 9/14/15 (txt:3052, txt:3063-3069), Active Events 14/15 "
     "(txt:3318-3324), OpenConfirm Event 11 (txt:3775-3782), Established "
     "Events 26/27 (txt:4095-4111); in the trans matrix they coincide "
     "numerically with the policy self-loops."),
]

REGEN = "python -X utf8 field-trial2/cases/bgp-fsm/make_bgp_fsm.py"


# ---------------------------------------------------------------- builders
def build_trans():
    delta = {}
    for u, ev, v, _ in EDGES:
        key = (u, ev - 1)          # RFC event number -> action index
        if key in delta and delta[key] != v:
            raise ValueError("prose conflict at state %d, Event %d"
                             % (u, ev))
        delta[key] = v
    trans = []
    for s in range(N_STATES):
        row = []
        for a in range(len(EVENTS)):
            if s in REAL_STATES and (s, a) in delta:
                row.append([[1.0, delta[(s, a)], 0.0]])
            else:
                row.append([[1.0, s, 0.0]])   # undeclared -> self-loop
        trans.append(row)
    return trans


def build_model():
    return {
        "n_bits": N_BITS,
        "n_actions": len(EVENTS),
        "n_states": N_STATES,
        "goals": [],
        "meta": {
            "source_system": ("BGP-4 peer finite state machine (one FSM as "
                              "seen by one endpoint for one configured "
                              "peer), transcribed from RFC 4271 section 8. "
                              "RFC 4271 is a public standard (Internet "
                              "Standards Track; the BGP-4 specification)."),
            "variant": "bgp-fsm-rfc4271",
            "source_citation": ("RFC 4271 (January 2006), section 8 'BGP "
                                "Finite State Machine (FSM)': the event "
                                "list of sec.8.1.1-8.1.5 (Events 1-28, "
                                "numbering per sec.8.2.1.4) plus the "
                                "per-state paragraphs of sec.8.2.2. "
                                "Per-edge citations with snapshot line "
                                "ranges in meta.edges_with_citations."),
            "state_names": STATES,
            "action_names": EVENTS,
            "real_states": REAL_STATES,
            "semantics_class": ("event: the actions are protocol events "
                                "(sec.8.1's own event names, administrative "
                                "/ timer / TCP / message classes); their "
                                "names are part of the behavior and do not "
                                "follow state renamings -- candidate groups "
                                "in groups/ declare semantics \"fixed\". "
                                "The relabel rows in expected.json are the "
                                "diagnostic contrast reading, not the "
                                "protocol-true one."),
            "encoding": ("states 6..7 = unreachable padding (self-loop "
                         "only); undeclared (state, event) pairs self-loop "
                         "with reward 0"),
            "reward_rule": ("rewards all zero: the BGP FSM defines no "
                            "payoff; the reward layer carries no "
                            "information, all conclusions come from the "
                            "transition layer"),
            "edges_with_citations": [
                {"from": STATES[u], "event": EVENTS[ev - 1],
                 "rfc_event_number": ev, "to": STATES[v], "citation": c}
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
        "connect-active-swap.json": _group(
            [_swap(1, 2)],
            {
                "claim": ("defendant A (claim): the two TCP-acquisition "
                          "states are twins -- Connect is 'waiting for the "
                          "TCP connection to be completed' (snapshot "
                          "txt:3012-3013) and Active is 'trying to acquire "
                          "a peer by listening for, and accepting, a TCP "
                          "connection' (txt:3257-3258) -- and they run the "
                          "same machinery: both drop to Idle on ManualStop "
                          "(txt:3017-3036 / txt:3262-3278), both enter "
                          "OpenSent on DelayOpenTimer expiry and on TCP "
                          "success (txt:3054-3061 + txt:3089-3100 / "
                          "txt:3292-3313 + txt:3340-3350), both reach "
                          "OpenConfirm on a delayed OPEN (Event 20; "
                          "txt:3127-3161 / txt:3378-3404), both sink to "
                          "Idle on TcpConnectionFails (txt:3117-3125 / "
                          "txt:3355-3376) -- so swapping states 1 <-> 2 "
                          "should map the connection-establishment half of "
                          "the FSM onto itself."),
                "construction": ("order-2 group swapping Connect <-> Active "
                                 "(states 1 <-> 2); all other states fixed"),
                "why_it_looks_legal": ("sec.8.2.1.1 says the roles converge: "
                                       "'When a BGP speaker is configured as "
                                       "active, it may end up on either the "
                                       "active or passive side of the "
                                       "connection that eventually gets "
                                       "established. Once the TCP connection "
                                       "is completed, it doesn't matter which "
                                       "end was active and which was passive' "
                                       "(snapshot txt:2870-2874); the two "
                                       "state paragraphs are near-parallel "
                                       "prose, and the TCP-failure exits both "
                                       "read 'changes its state to Idle'"),
                "why_it_is_not_a_symmetry": ("the swap fails on named edges: "
                                             "(a) the start fan-in is "
                                             "attribute-linked -- Idle "
                                             "reaches Connect through Events "
                                             "1/3 (txt:2947-2962) and Active "
                                             "through Events 4/5 "
                                             "(txt:2975-2988), so the swap "
                                             "demands Idle --Event 1--> "
                                             "Active, which no paragraph "
                                             "declares; (b) OpenSent's "
                                             "TcpConnectionFails (Event 18) "
                                             "exits to Active only "
                                             "(txt:3569-3579) -- the swap "
                                             "demands a mirror exit to "
                                             "Connect, which does not exist; "
                                             "(c) the retry-restart rows "
                                             "point differently -- in "
                                             "Connect, Event 9 'stays in the "
                                             "Connect state' (txt:3052), in "
                                             "Active it 'changes its state to "
                                             "Connect' (txt:3290), so the "
                                             "swap demands Active --Event 9--> "
                                             "Active; (d) renaming cannot "
                                             "repair (c): Connect declares "
                                             "three self-transitions under "
                                             "Events 9/14/15 (txt:3052, "
                                             "txt:3063-3069) while Active "
                                             "declares only two, under "
                                             "Events 14/15 (txt:3318-3324) -- "
                                             "any action renaming would have "
                                             "to send three distinct Connect "
                                             "self-transitions onto Active's "
                                             "two self-transition events, a "
                                             "pigeonhole with no solution"),
                "engineering_anchor": ("the active/passive distinction is a "
                                       "TCP-layer role, not a second "
                                       "machine: sec.8.2.1 defines "
                                       "outgoing/incoming connections "
                                       "(txt:2828-2832) and the difference "
                                       "ends at 'which side of the TCP "
                                       "connection has port number 179' "
                                       "(txt:2874-2875); the FSM keeps the "
                                       "two states distinct exactly because "
                                       "the listening side never dials -- "
                                       "the optional-event split (Events 1/3 "
                                       "vs 4/5) is the RFC's own "
                                       "machine-readable form of that "
                                       "distinction"),
                "semantics_note": ("event-class model: semantics declared "
                                   "\"fixed\" (protocol-true reading); the "
                                   "relabel row is the diagnostic contrast "
                                   "reading"),
                "regenerate": regen,
            }),
        "openconfirm-established-swap.json": _group(
            [_swap(4, 5)],
            {
                "claim": ("defendant B: OpenConfirm and Established are the "
                          "two session-live states -- both answer ManualStop, "
                          "AutomaticStop and HoldTimer expiry with a "
                          "NOTIFICATION and a drop to Idle (txt:3715-3746, "
                          "txt:3748-3773 / txt:3940-3974, txt:3988-4005), "
                          "both keep the session alive on their periodic "
                          "machinery (OpenConfirm 'remains in the "
                          "OpenConfirmed state' on Event 11, txt:3775-3782; "
                          "Established 'remains in the Established state' on "
                          "Events 26/27, txt:4095-4111), and both sink to "
                          "Idle on NOTIFICATION or TCP failure (txt:3792-3826 "
                          "/ txt:4064-4078) -- so maybe states 4 <-> 5 can "
                          "be swapped alone"),
                "construction": ("order-2 group swapping OpenConfirm <-> "
                                 "Established (states 4 <-> 5) only"),
                "why_it_looks_legal": ("both states hold a live session with "
                                       "the same drain-to-Idle skeleton and "
                                       "the same NOTIFICATION handling; on "
                                       "the unlabeled graph both also "
                                       "self-loop on their periodic events"),
                "why_it_is_not_a_symmetry": ("OpenConfirm exists to leave "
                                             "itself on Event 26: 'If the "
                                             "local system receives a "
                                             "KEEPALIVE message (KeepAliveMsg "
                                             "(Event 26)) ... changes its "
                                             "state to Established' "
                                             "(txt:3898-3903), while "
                                             "Established's Event 26 'remains "
                                             "in the Established state' "
                                             "(txt:4095-4101) -- the swap "
                                             "demands Established --Event "
                                             "26--> OpenConfirm, which no "
                                             "paragraph declares; "
                                             "Established additionally "
                                             "self-loops on UPDATE (Event 27, "
                                             "txt:4103-4111) where "
                                             "OpenConfirm's FSM-error "
                                             "catch-all sends Event 27 to "
                                             "Idle (txt:3905-3930); and the "
                                             "in-edges differ -- Established "
                                             "is entered only through "
                                             "OpenConfirm's Event 26, while "
                                             "OpenConfirm is entered from "
                                             "OpenSent's Event 19 "
                                             "(txt:3591-3606) and from "
                                             "Connect/Active's Event 20 "
                                             "(txt:3127-3161, txt:3378-3404)"),
                "semantics_note": ("control group: the transcription says "
                                   "the swap breaks at the structure level "
                                   "(the Event 26 target differs); the "
                                   "verdict rows live in expected.json and "
                                   "come from the arbitration run, not from "
                                   "this note"),
                "regenerate": regen,
            }),
        "opensent-openconfirm-swap.json": _group(
            [_swap(3, 4)],
            {
                "claim": ("defendant C: OpenSent and OpenConfirm are the "
                          "two mid-negotiation states -- OpenSent 'waits for "
                          "an OPEN message from its peer' (txt:3497) and "
                          "OpenConfirm 'waits for a KEEPALIVE or "
                          "NOTIFICATION message' (txt:3710); both drain to "
                          "Idle on the administrative and hold-time events "
                          "in the same prose pattern ('changes its state to "
                          "Idle' per paragraph, txt:3502-3558 / "
                          "txt:3715-3773) -- so maybe states 3 <-> 4 can be "
                          "swapped alone"),
                "construction": ("order-2 group swapping OpenSent <-> "
                                 "OpenConfirm (states 3 <-> 4) only"),
                "why_it_looks_legal": ("both states sit between the OPEN "
                                       "exchange and session establishment, "
                                       "both are entered from the "
                                       "TCP-acquisition half, and both carry "
                                       "the same paragraph skeleton of "
                                       "NOTIFICATION-plus-Idle drains"),
                "why_it_is_not_a_symmetry": ("their completion edges point "
                                             "at different shores: OpenSent's "
                                             "Event 19 (BGPOpen) advances to "
                                             "OpenConfirm (txt:3591-3606) "
                                             "while OpenConfirm's Event 19 "
                                             "drops to Idle (collision "
                                             "branch, txt:3828-3846); "
                                             "OpenSent's Event 18 "
                                             "(TcpConnectionFails) escapes "
                                             "to Active (txt:3569-3579) "
                                             "while OpenConfirm's Event 18 "
                                             "drops to Idle (txt:3792-3815); "
                                             "and OpenConfirm's Event 26 "
                                             "advances to Established "
                                             "(txt:3898-3903) while "
                                             "OpenSent's Event 26 lands in "
                                             "the FSM-error catch-all --> "
                                             "Idle (txt:3682-3706) -- the "
                                             "swap also demands an OpenSent "
                                             "--Event 26--> Established edge "
                                             "and an OpenConfirm --Event "
                                             "19--> OpenConfirm edge, "
                                             "neither of which any paragraph "
                                             "declares"),
                "semantics_note": ("control group: the transcription says "
                                   "the swap breaks at the structure level "
                                   "(Events 18/19/26 targets differ); the "
                                   "verdict rows live in expected.json and "
                                   "come from the arbitration run, not from "
                                   "this note"),
                "regenerate": regen,
            }),
        "pads.json": _group(
            [_swap(6, 7)],
            {
                "claim": ("positive control: padding states 6 and 7 have "
                          "byte-identical rows (every event self-loops, "
                          "reward 0), so the swap is a genuine symmetry "
                          "under BOTH readings and should be admitted "
                          "everywhere"),
                "construction": ("order-2 group swapping padding states 6 "
                                 "<-> 7"),
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
# Verdict rows are NOT pre-written: the rows below are the live arbitration
# run's own observed rows (arbitrate --emit-expected-template, court
# checkout root, 2026-11-08; receipt field-trial2/verdicts/bgp-fsm.verdict.
# json, sha256 8e3ebebc...1512, stderr 0 bytes, exit 0, ruling codes
# {"agree": 4}). model.json and groups/ were generated and heard before
# expected.json existed.
EXPECTED_ROWS = {
    "connect-active-swap": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "generalized"},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": False, "labeled_symmetry": False},
    },
    "openconfirm-established-swap": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "generalized"},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": False, "labeled_symmetry": False},
    },
    "opensent-openconfirm-swap": {
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
    if EXPECTED_ROWS is None:
        return None
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
        "case": "bgp-fsm",
        "provenance": {
            "recorded": (
                "2026-11-08 adoption into the official docket: the case bundle was "
                "copied byte-identical from the field-trial2 blind-trial round-2 case "
                "directory (8/8 files sha256-equal at copy time; oracle-input hashes "
                "match field-trial2/sealed/manifest.json), then the rows below were "
                "re-observed live in this repository via `python -X utf8 -m "
                "symmetry_court arbitrate --emit-expected-template --case bgp-fsm` -- "
                "relabel/fixed are this run's measured rows, field-for-field "
                "identical to the round-2 records; the receipt is "
                "verdicts/bgp-fsm.verdict.json; the gate (`python -X utf8 -m "
                "symmetry_court selftest`) replays the case and compares these rows "
                "field-by-field"),
            "reading_guide": (
                "relabel row = actions may be renamed along with states (diagnostic "
                "contrast reading for an event-class model); fixed row = event names "
                "pinned (the protocol-true reading, declared in each group file); "
                "networkx columns = independent juror"),
            "networkx_source": (
                "networkx columns are carried from the field-trial2 sealed truth "
                "(field-trial2/sealed/bgp-fsm.truth.json, independent oracle "
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
    ps = {"model.json": _dump(build_model())}
    expected = build_expected()
    if expected is not None:
        ps["expected.json"] = _dump(expected)
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

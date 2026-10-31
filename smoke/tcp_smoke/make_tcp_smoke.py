# -*- coding: utf-8 -*-
"""
make_tcp_smoke.py -- deterministic generator for the smoke case tcp_smoke

This is the court's SMOKE docket: the RFC 9293 TCP trial as a pre-recorded
replica, used to exercise the whole arbitrate/selftest pipeline when the
official cases/ docket is still being transcribed. The official docket is
cases/ (case-engineering territory); this directory is court-side and
self-contained.

Writes five files next to this script (byte-identical on every re-run; no
clock, no locale, no randomness):

  model.json            the TCP state machine model -- byte-identical to the
                        upstream wuxing-gua sample transcription of RFC 9293
                        section 3.3.2 Figure 5 (11 real states + 5 padding,
                        12 events, rewards all zero). Upstream serialization
                        preserved exactly: indent=1, CRLF line endings, no
                        trailing newline. Its embedded meta.regenerate points
                        at the upstream script that produced the original --
                        kept as historical truth, not as this repo's command.
  groups/swap.json      the twin swap CLOSING <-> FIN-WAIT-2 (defendant that
                        splits the standards: relabel passes it, fixed and
                        the labeled jury refuse it)
  groups/other.json     the pointless swap FIN-WAIT-1 <-> SYN-RECEIVED
  groups/absurd.json    the absurd swap CLOSED <-> ESTABLISHED
  groups/identity.json  the trivial group (control defendant)
  expected.json         the expected verdict table, recorded from an actual
                        court run (live-run backed; numbers baked as constants
                        below, byte-pinned by --check)

Every group file declares semantics {"action": "fixed"} (event-class=fixed:
TCP's actions are external protocol events) and carries a plain-language
meta.claim.

Usage:

  python -X utf8 smoke/tcp_smoke/make_tcp_smoke.py            # write all files
  python -X utf8 smoke/tcp_smoke/make_tcp_smoke.py --check    # verify bytes

`--check` regenerates everything in memory and compares against the committed
copies, exiting 0 when byte-identical.
"""
import argparse
import json
import os
import sys

N_STATES = 16          # 11 real + 5 padding, to reach 2**4
GOAL_PAD = range(11, 16)

# RFC 9293 section 3.3.2 Figure 5 -- 11 named states, 21 transitions, 12
# events. Same transcription as the upstream sample (states 0..10 in figure
# order; 11..15 unreachable padding, self-loop only; rewards all zero because
# TCP defines no payoff).
STATES = ["CLOSED", "LISTEN", "SYN-SENT", "SYN-RECEIVED", "ESTABLISHED",
          "FIN-WAIT-1", "FIN-WAIT-2", "CLOSE-WAIT", "CLOSING", "LAST-ACK",
          "TIME-WAIT"]

EDGES = [
    ("CLOSED", "SYN-SENT", "active OPEN"),
    ("CLOSED", "LISTEN", "passive OPEN"),
    ("LISTEN", "SYN-RECEIVED", "rcv SYN"),
    ("LISTEN", "SYN-SENT", "SEND"),
    ("LISTEN", "CLOSED", "CLOSE"),
    ("SYN-SENT", "ESTABLISHED", "rcv SYN,ACK"),
    ("SYN-SENT", "SYN-RECEIVED", "rcv SYN"),
    ("SYN-SENT", "FIN-WAIT-1", "CLOSE"),
    ("SYN-RECEIVED", "ESTABLISHED", "rcv ACK of SYN"),
    ("SYN-RECEIVED", "LISTEN", "rcv RST"),
    ("SYN-RECEIVED", "FIN-WAIT-1", "CLOSE"),
    ("ESTABLISHED", "FIN-WAIT-1", "CLOSE"),
    ("ESTABLISHED", "CLOSE-WAIT", "rcv FIN"),
    ("FIN-WAIT-1", "FIN-WAIT-2", "rcv ACK of FIN"),
    ("FIN-WAIT-1", "CLOSING", "rcv FIN"),
    ("FIN-WAIT-1", "TIME-WAIT", "rcv FIN+FIN acked"),
    ("FIN-WAIT-2", "TIME-WAIT", "rcv FIN"),
    ("CLOSE-WAIT", "LAST-ACK", "CLOSE"),
    ("CLOSING", "TIME-WAIT", "rcv ACK of FIN"),
    ("LAST-ACK", "CLOSED", "rcv ACK of FIN"),
    ("TIME-WAIT", "CLOSED", "timeout 2MSL"),
]

EVENTS = []
for _u, _v, e in EDGES:
    if e not in EVENTS:
        EVENTS.append(e)

UPSTREAM_MODEL_SHA256 = ("375de3448889bde411545649890ca7ee8af053fa0d54397bec"
                         "3bf2d417dcc1e8")


def build_model():
    """The upstream tcp_case model dict, field order included (for byte identity)."""
    idx = {name: i for i, name in enumerate(STATES)}
    delta = {}
    for u, v, ev in EDGES:
        delta[(idx[u], ev)] = idx[v]

    trans = []
    for s in range(N_STATES):
        row = []
        for ev in EVENTS:
            if s in GOAL_PAD:
                row.append([[1.0, s, 0.0]])
            elif (s, ev) in delta:
                row.append([[1.0, delta[(s, ev)], 0.0]])
            else:
                row.append([[1.0, s, 0.0]])   # undeclared = illegal, self-loop
        trans.append(row)

    return {
        "n_bits": 4,
        "n_actions": len(EVENTS),
        "n_states": N_STATES,
        "goals": [],
        "meta": {
            "source_system": ("TCP connection state machine, transcribed from "
                              "RFC 9293 "
                              "section 3.3.2 Figure 5 (public standard). 11 real states + "
                              "5 padding states; rewards are all zero because TCP defines "
                              "no payoff"),
            "variant": "tcp-rfc9293",
            "state_names": STATES,
            "action_names": EVENTS,
            "padding": "states 11..15 are unreachable padding (self-loop only)",
            "regenerate": "python tcp_three_way.py",
        },
        "trans": trans,
    }


def _swap(a, b):
    perm = list(range(N_STATES))
    perm[a], perm[b] = perm[b], perm[a]
    return perm


CLOSED, FIN_WAIT_2, CLOSING = 0, 6, 8
FIN_WAIT_1, SYN_RECEIVED = 5, 3
ESTABLISHED = 4

SEMANTICS_FIXED = {
    "action": "fixed",
    "note": ("event-class=fixed: TCP's actions are external protocol events; "
             "their names are part of the published behavior and do not "
             "follow state renamings"),
}
_PROV = ("group elements identical to the upstream tcp_case sample "
         "(RFC 9293 section 3.3.2 Figure 5 base material), re-encoded with "
         "an explicit semantics declaration and a plain-language claim")


def build_group_swap():
    return {
        "n_states": N_STATES,
        "elements": [list(range(N_STATES)), _swap(CLOSING, FIN_WAIT_2)],
        "semantics": SEMANTICS_FIXED,
        "meta": {
            "construction": ("swap CLOSING <-> FIN-WAIT-2, the only "
                             "structure-level automorphism networkx found"),
            "claim": ("swapping CLOSING (state 8) and FIN-WAIT-2 (state 6) "
                      "maps every transition onto a transition"),
            "why_it_splits": ("the two states are structural twins (one in, "
                              "one out, both exits into TIME-WAIT) but their "
                              "exit events differ: rcv FIN vs rcv ACK of FIN"),
            "provenance": _PROV,
        },
    }


def build_group_other():
    return {
        "n_states": N_STATES,
        "elements": [list(range(N_STATES)), _swap(FIN_WAIT_1, SYN_RECEIVED)],
        "semantics": SEMANTICS_FIXED,
        "meta": {
            "construction": "swap FIN-WAIT-1 <-> SYN-RECEIVED",
            "claim": ("swapping FIN-WAIT-1 (state 5) and SYN-RECEIVED "
                      "(state 3) maps every transition onto a transition"),
            "provenance": _PROV,
        },
    }


def build_group_absurd():
    return {
        "n_states": N_STATES,
        "elements": [list(range(N_STATES)), _swap(CLOSED, ESTABLISHED)],
        "semantics": SEMANTICS_FIXED,
        "meta": {
            "construction": ("swap CLOSED <-> ESTABLISHED (different degrees, "
                             "should be refused)"),
            "claim": ("swapping CLOSED (state 0) and ESTABLISHED (state 4) "
                      "maps every transition onto a transition"),
            "provenance": _PROV,
        },
    }


def build_group_identity():
    return {
        "n_states": N_STATES,
        "elements": [list(range(N_STATES))],
        "semantics": SEMANTICS_FIXED,
        "meta": {
            "construction": "the trivial group (identity only)",
            "claim": ("renaming nothing is a symmetry (control defendant: "
                      "every standard and every judge must admit it)"),
            "provenance": "court-side control group, not from the upstream sample",
        },
    }


# ---------------------------------------------------------------------------
# Expected verdict table -- RECORDED FROM AN ACTUAL COURT RUN, not from
# memory. Baked as constants so --check can pin the file byte-exactly.
# Source run: `python -X utf8 -m symmetry_court arbitrate --cases-dir smoke
#             --emit-expected-template`, 2026-10-31 (see verdicts/tcp_smoke.
#             verdict.json for the full trial record of the same run).
# ---------------------------------------------------------------------------
EXPECTED_RUN_UTC = "2026-10-31T03:09:47Z"

EXPECTED = {
    "case": "tcp_smoke",
    "provenance": {
        "recorded_from_live_run": EXPECTED_RUN_UTC,
        "how": ("expected rows are the observed rows of an actual court run "
                "(arbitrate --cases-dir smoke --emit-expected-template, run "
                "2026-10-31T03:09:47Z) baked into make_tcp_smoke.py as "
                "constants; --check pins them byte-exactly. Full trial record "
                "of the same run: verdicts/tcp_smoke.verdict.json"),
        "engine": "vendored wuxing_gua 1.0.0 (see NOTICE)",
        "jury": "networkx (independent implementation; not imported from the "
                "upstream tcp_three_way.py)",
    },
    "groups": {
        "swap": {
            "claim": build_group_swap()["meta"]["claim"],
            "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                        "judge": "generalized"},
            "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                      "judge": "strict"},
            "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
        },
        "other": {
            "claim": build_group_other()["meta"]["claim"],
            "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                        "judge": "generalized"},
            "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                      "judge": "strict"},
            "networkx": {"structure_symmetry": False, "labeled_symmetry": False},
        },
        "absurd": {
            "claim": build_group_absurd()["meta"]["claim"],
            "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                        "judge": "generalized"},
            "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                      "judge": "strict"},
            "networkx": {"structure_symmetry": False, "labeled_symmetry": False},
        },
        "identity": {
            "claim": build_group_identity()["meta"]["claim"],
            "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                        "judge": "generalized"},
            "fixed": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                      "judge": "strict"},
            "networkx": {"structure_symmetry": True, "labeled_symmetry": True},
        },
    },
}


def build_expected():
    exp = json.loads(json.dumps(EXPECTED))  # deep copy
    exp["provenance"]["recorded_from_live_run"] = EXPECTED_RUN_UTC
    return exp


def _dump_lf(obj):
    """My files: LF line endings, trailing newline (repo-side convention)."""
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


def _dump_upstream(obj):
    """Upstream byte-compat: indent=1, CRLF line endings, no trailing newline."""
    return json.dumps(obj, ensure_ascii=False, indent=1).replace("\n", "\r\n")


def payloads():
    return {
        "model.json": _dump_upstream(build_model()),
        os.path.join("groups", "swap.json"): _dump_lf(build_group_swap()),
        os.path.join("groups", "other.json"): _dump_lf(build_group_other()),
        os.path.join("groups", "absurd.json"): _dump_lf(build_group_absurd()),
        os.path.join("groups", "identity.json"): _dump_lf(build_group_identity()),
        "expected.json": _dump_lf(build_expected()),
    }


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=here,
                    help="target directory (default: this script's directory)")
    ap.add_argument("--check", action="store_true",
                    help="do not write; verify the committed files are "
                         "byte-identical to a fresh generation")
    args = ap.parse_args(argv)

    blobs = payloads()
    if args.check:
        bad = []
        for name, blob in sorted(blobs.items()):
            p = os.path.join(args.out, name)
            with open(p, "r", encoding="utf-8", newline="") as f:
                current = f.read()
            if current != blob:
                bad.append(name)
        if bad:
            sys.stderr.write("byte-identity FAILED: %s\n" % ", ".join(bad))
            return 1
        sys.stdout.write("byte-identity OK: %d files (%s)\n"
                         % (len(blobs),
                            ", ".join(sorted(os.path.basename(p) for p in blobs))))
        return 0

    os.makedirs(os.path.join(args.out, "groups"), exist_ok=True)
    for name, blob in sorted(blobs.items()):
        p = os.path.join(args.out, name)
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(blob)
        sys.stdout.write("wrote %s (%d bytes)\n" % (p, len(blob.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())

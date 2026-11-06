# -*- coding: utf-8 -*-
"""
make_hanoi3.py -- deterministic generator for the hanoi3 case: the Tower of
Hanoi move mechanics at 3 disks / 3 pegs (rules public), built as the fourth
docket for the engine's *explicit* action caliber (state permutation +
declared per-element action renaming) and the fourth non-trivial positive
control: the FULL peg-relabel group S3 (order 6), admitted with per-element
action maps. It is also the docket's first entry whose action space has
ORDERED-PAIR semantics: an action is not a named direction or button but the
ordered pair of rods (X, Y) = "take the upper disk of rod X, place it on rod
Y", so a peg relabeling renames the actions as ordered pairs
(X, Y) |-> (piX, piY).

Writes, byte-identical on every re-run (nothing random, no clock, no locale
dependence), next to this script:

  model.json                     the trans model: 32 states = 2^5 (the
                                 3^3 = 27 disk-to-rod arrangements are the
                                 real states; ranks 27..31 are unused
                                 encoding space = 5 padding states), 6
                                 ordered peg-pair actions, rewards all zero
                                 by design (the source puzzle has no score;
                                 the win condition is recorded in meta)
  groups/g1_swap_ab_map.json     defendant A: the A<->B peg swap with the
                                 ordered pairs renamed with the rods
                                 (explicit + per-element action_maps)
  groups/g2_swap_nomap.json      defendant B: the same swap with the ordered
                                 pairs PINNED (fixed) -- the naive-intuition
                                 claim
  groups/g3_s3_full.json         main positive control: the FULL peg-relabel
                                 group S3 = C3 x C2 (order 6: identity, 3
                                 transpositions, 2 rotations), each element
                                 carrying its own ordered-pair renaming
                                 (explicit + per-element action_maps)
  groups/g4_pads.json            positive control: swap of two padding
                                 states (fixed, expected pass)
  expected.json                  pinned verdict rows, observed live

Transcription authority (primary source, public):
  - Wikipedia, "Tower of Hanoi" (en.wikipedia.org/wiki/Tower_of_Hanoi):
    lead ("a mathematical game or puzzle consisting of three rods and a
    number of disks of various diameters, which can slide onto any rod");
    rules ("Only one disk may be moved at a time."; "Each move consists of
    taking the upper disk from one of the stacks and placing it on top of
    another stack or on an empty rod."; "No disk may be placed on top of a
    disk that is smaller than it."); objective ("The objective of the puzzle
    is to move the entire stack to one of the other rods"); minimum moves
    ("With three disks, the puzzle can be solved in seven moves. The minimum
    number of moves required to solve a Tower of Hanoi puzzle is 2^n - 1");
    state graph ("For a puzzle with n disks, there are 3^n nodes in the
    graph" and "every node has three edges to other nodes, except the three
    corner nodes, which have two"); symmetry ("the problem is symmetric for
    permutations of the names of the pegs (symmetric group S3). If a
    solution is known moving from peg A to peg C, then, by renaming the
    pegs, the same solution can be used for every other choice of starting
    and destination peg.").

Variant boundaries (recorded, not hidden -- see TRANSCRIPTION_NOTES):
  1. 3 disks: the source puzzle is parameterized by the number of disks
     ("a number of disks"; toy versions commonly have around 7 to 9); the
     3-disk instance keeps the full rule set, the full S3 peg symmetry and
     the minimal non-trivial state space 3^3 = 27 (recorded as a variant
     boundary, rule R6).
  2. No score: the puzzle has no numeric payoff, so the reward layer is all
     zero by design and the win condition (the entire stack on one rod) is
     recorded in meta.win_condition as a goal property, not a per-edge
     reward (same all-zero convention as tcp/dhcp/imap/lightsout3/
     sliding2x3).

The explicit caliber and this case: a peg symmetry moves the ordered-pair
action names with the rods (renaming the pegs A<->B turns the move "A->B"
into the move "B->A"). Per group element pi the action renaming rho(pi) is
forced -- rho(pi) maps the ordered pair (X, Y) to (piX, piY) -- and
pi |-> rho(pi) is a group homomorphism. The engine's group format accepts
semantics.action_maps: one action renaming (bijection) per group element,
parallel to elements, homomorphism-law checked at load -- each explicit
group file here declares the per-element maps of its own elements
(exhaustively derived and asserted by this generator on every run over all
6! = 720 ordered-pair permutations); model.meta.per_element_action_maps
holds the full derivation table.

Why S3: the peg names A, B, C carry no geometry beyond their identity, so
every relabeling of the three rods preserves the move mechanics exactly --
the peg-relabel group is the full symmetric group S3 (order 6 = |S3|:
identity, 3 transpositions, 2 three-cycles). Wikipedia states the symmetry
in solution terms (see the citation above); this generator machine-verifies
it dynamically: for every one of the 6 peg permutations, the induced state
permutation commutes with the move table under exactly one ordered-pair
renaming (exhaustive over 720), and the six (pi, rho(pi)) pairs satisfy the
homomorphism law over all 36 ordered pairs. This is a fourth group
structure on the docket, distinct from mini2048's and lightsout3's D4
(order 8), lightsout3's D4 x C2 (order 16) and sliding2x3's V4 (order 4) --
and the first admitted group that is non-abelian of order 6.

Why the pads positive control exists here: the state encoding needs
n_states = 2^5 = 32 slots for 3^3 = 27 real arrangements, so 5 unused ranks
are padding states (every action self-loops with reward 0 -- the same
padding convention as tcp/dhcp/imap/mini2048/sliding2x3). Two padding
states therefore have the same behavior shape and their swap is a genuine
fixed-caliber symmetry (g4_pads) -- the pads positive control continues its
run of explicit-caliber dockets (mini2048's g6, sliding2x3's g3).

Usage:
  python -X utf8 cases/hanoi3/make_hanoi3.py            # write all files
  python -X utf8 cases/hanoi3/make_hanoi3.py --out DIR  # write into DIR
  python -X utf8 cases/hanoi3/make_hanoi3.py --check    # verify bytes +
                                                        # re-run the
                                                        # symmetry self-
                                                        # certification
"""
import argparse
import itertools
import json
import os
import sys

# ---------------------------------------------------------------- encoding
# Rods A, B, C indexed 0, 1, 2. A configuration is the 3-tuple of rod ids,
# one per disk: disk 0 = smallest, disk 2 = largest (the Wikipedia recursive
# solution numbers disks from 0 = smallest). State = the base-3 numeral
# p0 + 3*p1 + 9*p2 (disk 0 = least significant trit); 3^3 = 27 real states.
# n_bits = 5 (2^5 = 32 >= 27); ranks 27..31 are unused encoding space =
# 5 padding states.
N_DISKS = 3
N_PEGS = 3
N_REAL = 27                                              # 3^3
N_BITS = 5
N_STATES = 1 << N_BITS                                   # 32
N_PADS = N_STATES - N_REAL                               # 5
N_ACTIONS = 6

# Actions = ordered rod pairs (X, Y): take the upper disk of rod X and place
# it on rod Y (Wikipedia rule 2). Ordered pairs are the action semantics --
# source and target are bound to rod identity, so a peg relabeling carries
# the pairs with the rods. Recorded in meta.action_names / rules R1; action
# indices are this transcription's own convention (the source names no
# numbering), not a court choice.
ACTION_PAIRS = [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]
ACTION_NAMES = ["A->B", "A->C", "B->A", "B->C", "C->A", "C->B"]
_PAIR_INDEX = {pair: i for i, pair in enumerate(ACTION_PAIRS)}

WIKI = 'Wikipedia "Tower of Hanoi" (en.wikipedia.org/wiki/Tower_of_Hanoi), '

RULES = [
    {"id": "R1-one-disk-upper-disk",
     "rule": ("one move takes the UPPER disk from one of the stacks and "
              "places it on top of another stack or on an empty rod; only "
              "one disk may be moved at a time. An action is the ordered "
              "rod pair (X, Y): take rod X's upper disk, place it on rod "
              "Y -- the six ordered pairs of three rods are the six "
              "actions"),
     "citation": (WIKI + "rules: 'Only one disk may be moved at a time.'; "
                  "'Each move consists of taking the upper disk from one "
                  "of the stacks and placing it on top of another stack or "
                  "on an empty rod.'")},
    {"id": "R2-no-smaller-under-larger",
     "rule": ("no disk may be placed on top of a disk that is smaller than "
              "it: the ordered pair (X, Y) is legal exactly when rod X is "
              "non-empty and rod Y is empty or Y's upper disk is larger "
              "than X's upper disk (the upper disk of a rod is its "
              "smallest disk)"),
     "citation": (WIKI + "rule: 'No disk may be placed on top of a disk "
                  "that is smaller than it.'")},
    {"id": "R3-illegal-move-noop",
     "rule": ("an ordered pair with an empty source rod or a smaller target "
              "top disk is unavailable: the move changes nothing (recorded "
              "as a no-op self-loop with reward 0, same convention as "
              "mini2048's unavailable-direction self-loops and "
              "sliding2x3's rule R2)"),
     "citation": (WIKI + "the rules constrain what MAY be moved (R1, R2); "
                  "this model keeps all six ordered pairs as actions so the "
                  "action set is rod-relabeling covariant, and records an "
                  "unavailable pair as a self-loop -- the same not-collected "
                  "move convention as the other puzzle dockets")},
    {"id": "R4-no-score-goal-rod",
     "rule": ("the puzzle has no score; the reward layer is all zero by "
              "design and the win condition (the entire stack moved to one "
              "of the other rods, here rod C: every disk on rod 2) is "
              "recorded in meta.win_condition, not as a per-edge reward"),
     "citation": (WIKI + "objective: 'The objective of the puzzle is to "
                  "move the entire stack to one of the other rods'; the "
                  "article describes no scoring -- recorded, not turned "
                  "into a reward; same all-zero reward convention as the "
                  "tcp/dhcp/imap/lightsout3/sliding2x3 cases")},
    {"id": "R5-state-space-27-connected",
     "rule": ("the 3-disk puzzle's full configuration space is the 3^3 = 27 "
              "disk-to-rod assignments, all of them real states of this "
              "model (no arrangement is excluded); the move graph over "
              "them is connected -- a BFS from the goal reaches all 27 "
              "(machine-asserted on every run)"),
     "citation": (WIKI + "graph section: 'For a puzzle with n disks, there "
                  "are 3^n nodes in the graph' (3^3 = 27 nodes for three "
                  "disks); the article's graph construction builds one "
                  "connected Sierpinski-triangle figure over all nodes")},
    {"id": "R6-3-disks-VARIANT",
     "rule": ("VARIANT BOUNDARY: this case is the 3-disk instance; the "
              "source puzzle is parameterized by the number of disks ('a "
              "number of disks of various diameters'; 'The puzzle can be "
              "played with any number of disks, although many toy versions "
              "have around 7 to 9 of them'). Every cited rule sentence is "
              "disk-count-independent except the 7-move minimum, which is "
              "the 2^n - 1 law evaluated at n = 3"),
     "citation": (WIKI + "'With three disks, the puzzle can be solved in "
                  "seven moves. The minimum number of moves required to "
                  "solve a Tower of Hanoi puzzle is 2^n - 1, where n is "
                  "the number of disks.'; 'The puzzle can be played with "
                  "any number of disks, although many toy versions have "
                  "around 7 to 9 of them.'")},
    {"id": "R7-deterministic",
     "rule": ("play itself is deterministic: a legal ordered pair moves "
              "exactly the one upper disk of the source rod, with no "
              "randomness; the physical puzzle's starting stack is the "
              "only free choice and it is NOT collected (outside the "
              "deterministic FSM semantics)"),
     "citation": (WIKI + "consequence of R1/R2 as stated (each move is "
                  "'taking the upper disk from one of the stacks'); same "
                  "not-collected discipline as mini2048's random-spawn "
                  "rule and sliding2x3's rule R7")},
    {"id": "R8-peg-relabel-symmetry",
     "rule": ("the puzzle's own symmetry: renaming the rods preserves the "
              "mechanics -- the peg-relabel group is the symmetric group "
              "S3 (order 6: identity, 3 transpositions, 2 three-cycles), "
              "and a relabeling pi renames each ordered-pair action "
              "(X, Y) to (piX, piY)"),
     "citation": (WIKI + "'First, observe that the problem is symmetric "
                  "for permutations of the names of the pegs (symmetric "
                  "group S3). If a solution is known moving from peg A to "
                  "peg C, then, by renaming the pegs, the same solution "
                  "can be used for every other choice of starting and "
                  "destination peg.'")},
]

TRANSCRIPTION_NOTES = [
    "scope: 3 disks, 3 rods (A, B, C indexed 0, 1, 2), 6 ordered rod-pair "
    "actions; the deterministic move mechanics of the Tower of Hanoi "
    "(rules R1-R2) with the starting stack NOT collected (rule R7) -- the "
    "model is the full 27-configuration transition system.",
    "VARIANT BOUNDARY (rule R6): the 3-disk instance; the source puzzle "
    "takes 'a number of disks' and toy versions commonly have around 7 to "
    "9; every cited rule sentence is size-independent except the 7-move "
    "minimum (the 2^n - 1 law at n = 3, machine-asserted on every run as "
    "the BFS distance from the standard start to the goal).",
    "actions: six ordered rod pairs indexed 0=A->B, 1=A->C, 2=B->A, 3=B->C, "
    "4=C->A, 5=C->B -- the FIRST docket entry whose action semantics is an "
    "ordered pair (source rod, target rod) rather than a named direction "
    "(mini2048's arrow keys, sliding2x3's slide directions) or a button "
    "(lightsout3). A rod relabeling renames the pairs with the rods: "
    "(X, Y) -> (piX, piY) -- the renaming is forced, and pi |-> rho(pi) is "
    "the group homomorphism the engine checks at load.",
    "encoding: state = 5 bits = the base-3 numeral p0 + 3*p1 + 9*p2 (peg "
    "of disk 0/1/2, disk 0 = smallest = least significant trit; rods "
    "A=0, B=1, C=2). 3^3 = 27 real states; ranks 27..31 are unused "
    "encoding space = 5 padding states (every action self-loops with "
    "reward 0 -- same padding convention as tcp/dhcp/imap/mini2048/"
    "sliding2x3). A move rearranges disks among rods, so a real state "
    "only reaches real states (machine-asserted on every run).",
    "illegal moves: an ordered pair whose source rod is empty or whose "
    "target rod's upper disk is smaller is unavailable and is recorded as "
    "a no-op self-loop with reward 0 (rule R3 -- same convention as "
    "mini2048's unavailable-direction self-loops). Machine-checked "
    "against the source's graph description: every real state has exactly "
    "3 legal ordered pairs, except the three corner states (all disks on "
    "one rod) which have exactly 2 ('every node has three edges to other "
    "nodes, except the three corner nodes, which have two' -- Wikipedia).",
    "rewards: all zero by design (rule R4) -- the puzzle has no score; "
    "the win condition (the entire stack on rod C: state (2,2,2), index "
    "26) is recorded in meta.win_condition as a goal property and the "
    "puzzle does not lock on it, so it is an ordinary state of the "
    "transition system and goals=[] in this model. The adjudication "
    "therefore runs entirely on the transition layer (same all-zero "
    "convention as tcp/dhcp/imap/lightsout3/sliding2x3).",
    "optimality recorded (rule R6): the BFS distance from the standard "
    "start (every disk on rod A, state 0) to the goal (every disk on rod "
    "C, state 26) is exactly 7 = 2^3 - 1 ('With three disks, the puzzle "
    "can be solved in seven moves' -- Wikipedia), machine-asserted on "
    "every run.",
    "explicit caliber note: a peg symmetry renames the ordered-pair "
    "actions element-by-element (renaming the rods A<->B turns 'A->B' "
    "into 'B->A' and 'A->C' into 'B->C'); rho(identity)=id while "
    "rho(swap)!=id, so no single action_map can serve a whole closed "
    "group. Each explicit group file here declares semantics.action_maps "
    "(one bijection per element, parallel to elements, homomorphism-law "
    "checked at load); meta.per_element_action_maps holds the full "
    "derivation (exhaustively derived over all 6! = 720 ordered-pair "
    "permutations, unique per element, asserted on every run, homomorphism "
    "law over all 36 ordered pairs of S3).",
    "why S3: the rod names carry no geometry beyond their identity, so "
    "every relabeling of the three rods preserves the mechanics -- the "
    "peg-relabel group is the full symmetric group S3 of order 6 "
    "(identity, 3 transpositions, 2 three-cycles), machine-verified "
    "dynamically: all 6 elements have exactly one forced ordered-pair "
    "renaming each and satisfy the homomorphism law. A fourth group "
    "structure on the docket (D4, D4 x C2, V4, now S3) and the first "
    "non-abelian one; also the docket's first true group whose action "
    "space is ordered pairs.",
    "padding positive control: 5 real padding states exist (the unused "
    "ranks 27..31), so the pads swap continues on this docket after "
    "mini2048's g6 and sliding2x3's g3 (lightsout3 has no padding states; "
    "its deviation note is the honest record of that gap).",
    "regenerate: python -X utf8 cases/hanoi3/make_hanoi3.py",
]

# ---------------------------------------------------------------- encoding
POW3 = [1, 3, 9]


def decode(s):
    """Real state index -> (peg of disk 0, peg of disk 1, peg of disk 2)."""
    assert 0 <= s < N_REAL
    return (s % 3, (s // 3) % 3, (s // 9) % 3)


def encode(pos):
    """(peg per disk) -> real state index."""
    assert len(pos) == N_DISKS
    for p in pos:
        assert 0 <= p < N_PEGS
    return pos[0] + 3 * pos[1] + 9 * pos[2]


def is_pad(s):
    return s >= N_REAL


GOAL_POS = (2, 2, 2)          # the entire stack on rod C
GOAL_STATE = encode(GOAL_POS)  # 26
START_POS = (0, 0, 0)          # the standard start: every disk on rod A
START_STATE = encode(START_POS)  # 0


# ---------------------------------------------------------------- move rule
# Primary implementation: works on the disk->rod map (the state encoding
# itself). The upper disk of a rod is its smallest disk (smallest index on
# that rod, since smaller disks are never under larger ones).
def move(s, a):
    """Deterministic ordered-pair move -> (successor state, reward, tag).

    Tag: 'M' a legal move (R1 + R2), 'I' the ordered pair is unavailable
    (no-op self-loop, R3), 'P' padding self-loop.
    Returns the rule tags so every edge's generating rules are recorded
    (meta.edge_rule_tags).
    """
    if is_pad(s):
        return s, 0.0, "P"
    pos = decode(s)
    x, y = ACTION_PAIRS[a]
    top_x = None
    for d in range(N_DISKS):
        if pos[d] == x:
            top_x = d                      # smallest disk on rod x
            break
    if top_x is None:
        return s, 0.0, "I"                 # nothing to move from rod x
    top_y = None
    for d in range(N_DISKS):
        if pos[d] == y:
            top_y = d
            break
    if top_y is not None and top_y < top_x:
        return s, 0.0, "I"                 # target top smaller than mover
    nxt = list(pos)
    nxt[top_x] = y
    return encode(nxt), 0.0, "M"


# Independent implementation: works on rod->stack lists (pop/push on
# explicit stacks), a different data path from the disk->rod digit rewrite
# above. Cross-validated against move() on every (state, action) pair.
def move_stacks(s, a):
    if is_pad(s):
        return s, 0.0, "P"
    pos = decode(s)
    stacks = [[], [], []]
    for d in range(N_DISKS - 1, -1, -1):   # push largest first
        stacks[pos[d]].append(d)           # stack top = stacks[p][-1]
    x, y = ACTION_PAIRS[a]
    if not stacks[x]:
        return s, 0.0, "I"
    d = stacks[x][-1]                      # upper disk of rod x
    if stacks[y] and stacks[y][-1] < d:
        return s, 0.0, "I"
    stacks[x].pop()
    stacks[y].append(d)
    npos = [None] * N_DISKS
    for p in range(N_PEGS):
        for e in stacks[p]:
            npos[e] = p
    return encode(npos), 0.0, "M"


def build_trans():
    """32 x 6 deterministic rows + the per-edge rule-tag table."""
    trans = []
    tags = []
    for s in range(N_STATES):
        row = []
        tag = ""
        for a in range(N_ACTIONS):
            t, r, _tag = move(s, a)
            row.append([[1.0, t, r]])
            tag += _tag
        trans.append(row)
        tags.append(tag)
    return trans, tags


def bfs_all(start):
    """BFS over real states from start -> (reachable count, distances)."""
    dist = {start: 0}
    frontier = [start]
    while frontier:
        nxt = []
        for s in frontier:
            for a in range(N_ACTIONS):
                t, _r, tag = move(s, a)
                if tag != "I" and t not in dist:
                    dist[t] = dist[s] + 1
                    nxt.append(t)
        frontier = nxt
    return len(dist), dist


# ---------------------------------------------------------------- symmetry
# Peg relabelings as rod maps sigma: old rod -> new rod. The six elements
# of S3 on rods (A, B, C) = (0, 1, 2).
PEG_PERMS = [
    ("id",       (0, 1, 2)),
    ("swap_ab",  (1, 0, 2)),
    ("swap_ac",  (2, 1, 0)),
    ("swap_bc",  (0, 2, 1)),
    ("rot_abc",  (1, 2, 0)),   # A->B->C->A
    ("rot_acb",  (2, 0, 1)),   # A->C->B->A
]


def state_perm_of(sigma):
    """Rod map sigma -> state permutation pi: pi(s) relabels every disk's
    rod through sigma on real states; the padding region is fixed pointwise
    (unused ranks are not rod assignments -- recorded in
    meta.transcription_notes)."""
    pi = []
    for s in range(N_STATES):
        if is_pad(s):
            pi.append(s)
            continue
        pos = decode(s)
        pi.append(encode((sigma[pos[0]], sigma[pos[1]], sigma[pos[2]])))
    return pi


def rename_actions(sigma):
    """The forced ordered-pair renaming under rod map sigma:
    (X, Y) -> (sigma[X], sigma[Y]), expressed in action-index space."""
    out = []
    for a in range(N_ACTIONS):
        x, y = ACTION_PAIRS[a]
        out.append(_PAIR_INDEX[(sigma[x], sigma[y])])
    return out


_MAP_CACHE = {}


def derive_action_map(pi):
    """Exhaustive search over ALL 6! = 720 ordered-pair permutations for
    rho with, for ALL states s and actions a:
        move(pi(s), rho[a]) == pi(move(s, a))            (transition layer)
        reward(pi(s), rho[a]) == reward(move(s, a))      (trivially true:
                                                          rewards all zero,
                                                          checked separately)
    Returns the list of valid rhos (asserted by callers to have length
    exactly 1, or 0 for non-symmetries). Memoized per permutation. This is
    the author-side derivation of the per-element ordered-pair renaming;
    the engine's verdicts remain the court's judges."""
    key = tuple(pi)
    if key in _MAP_CACHE:
        return _MAP_CACHE[key]
    found = []
    for rho in itertools.permutations(range(N_ACTIONS)):
        ok = True
        for s in range(N_STATES):
            ps = pi[s]
            for a in range(N_ACTIONS):
                t, _r, _tag = move(s, a)
                t2, _r2, _tag2 = move(ps, rho[a])
                if t2 != pi[t]:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            found.append(list(rho))
    _MAP_CACHE[key] = found
    return found


def derive_unique_map(pi, expect=True):
    """derive_action_map + loud uniqueness assertion (exactly one rho), or
    exactly zero when expect=False (non-symmetry controls)."""
    found = derive_action_map(pi)
    if expect:
        assert len(found) == 1, "action map not unique: %r" % (found,)
        return found[0]
    assert len(found) == 0, "expected no action map, found %r" % (found,)
    return None


def compose_maps(rho_outer, rho_inner):
    """rho after rho: a -> rho_outer[rho_inner[a]]."""
    return [rho_outer[rho_inner[a]] for a in range(N_ACTIONS)]


def orbits(elements):
    """Full-state orbit count (the padding states are fixed pointwise by
    every peg permutation, so each pad is its own orbit)."""
    parent = list(range(N_STATES))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in elements:
        for s in range(N_STATES):
            ra, rb = find(s), find(e[s])
            if ra != rb:
                parent[ra] = rb
    return len({find(x) for x in range(N_STATES)})


def real_orbits(elements):
    """Orbit count restricted to the 27 real states."""
    parent = list(range(N_REAL))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in elements:
        for s in range(N_REAL):
            ra, rb = find(s), find(e[s])
            if ra != rb:
                parent[ra] = rb
    return len({find(x) for x in range(N_REAL)})


def orbit_sizes(elements):
    """Multiset of full-state orbit sizes (Burnside cross-check support)."""
    seen = set()
    sizes = []
    for s in range(N_STATES):
        if s in seen:
            continue
        orb = set()
        for e in elements:
            orb.add(e[s])
        seen |= orb
        sizes.append(len(orb))
    return sorted(sizes)


# ---------------------------------------------------------------- closure
def _closure(seeds):
    """Closure of state-permutation seeds (identity included)."""
    ident = tuple(range(N_STATES))
    seen = {ident}
    frontier = [ident]
    while frontier:
        nxt = []
        for g in frontier:
            for h in seeds:
                c = tuple(h[x] for x in g)
                if c not in seen:
                    seen.add(c)
                    nxt.append(c)
        frontier = nxt
    return sorted(list(x) for x in seen)


def _swap_states(a, b):
    pi = list(range(N_STATES))
    pi[a], pi[b] = pi[b], pi[a]
    return pi


# ---------------------------------------------------------------- derivation
def derive_symmetry_table():
    """Per-element ordered-pair maps for the whole S3 + the homomorphism
    and fake-control checks.

    Returns dict name -> {"sigma": sigma, "state_perm": pi,
                          "action_map": rho}.
    Asserts (loud, on every run):
      1. every one of the 6 peg permutations has exactly one rho
         (exhaustive over 6! = 720 ordered-pair permutations);
      2. rho(id) = id and rho(swap_ab) != id (non-triviality);
      3. the homomorphism law rho(sigma2 o sigma1) == rho(sigma2) o
         rho(sigma1) for all 36 ordered pairs of S3 (and the 4 of any
         order-2 subgroup, checked on the closed group files below);
      4. the S3 closure of {swap_ab, rot_abc} has exactly 6 distinct
         elements (a group: closed, contains inverses);
      5. the padding region (5 states) is fixed pointwise by every
         element and real states never reach padding states;
      6. two fake state maps that are not peg relabelings (a swap of
         disks 0 and 1; a cyclic rotation of disks 0->1->2->0) admit NO
         rho at all -- sizes are attached to disk identity, not positions;
      7. the six actions are pairwise distinguishable on real states
         (supporting data for uniqueness: for any two ordered pairs some
         real state tells them apart);
      8. the move census agrees with the source's graph description:
         exactly 3 legal ordered pairs on every real state except the
         three corner states (all disks on one rod), which have exactly 2.
    """
    table = {}
    for name, sigma in PEG_PERMS:
        pi = state_perm_of(sigma)
        table[name] = {"sigma": list(sigma), "state_perm": pi,
                       "action_map": derive_unique_map(pi)}
    # 2. identity / non-triviality
    assert table["id"]["action_map"] == list(range(N_ACTIONS))
    assert table["swap_ab"]["action_map"] != list(range(N_ACTIONS))
    # the forced renaming of swap_ab renames the pairs through the rods
    assert table["swap_ab"]["action_map"] == rename_actions((1, 0, 2))
    assert table["rot_abc"]["action_map"] == rename_actions((1, 2, 0))
    # 3. homomorphism over all 36 ordered pairs of S3
    for (n1, _s1) in PEG_PERMS:
        for (n2, _s2) in PEG_PERMS:
            want = compose_maps(table[n2]["action_map"],
                                table[n1]["action_map"])
            got = derive_unique_map(
                state_perm_of(tuple(
                    table[n2]["sigma"][table[n1]["sigma"][p]]
                    for p in range(N_PEGS))))
            assert got == want, ("homomorphism broken", n1, n2, got, want)
    # 4. S3 closure: 6 distinct elements
    s3 = _closure([table["swap_ab"]["state_perm"],
                   table["rot_abc"]["state_perm"]])
    assert len(s3) == 6
    assert sorted(tuple(p) for p in s3) == sorted(
        tuple(table[n]["state_perm"]) for n, _s in PEG_PERMS)
    # 5. pads fixed pointwise; real states reach only real states
    for name in table:
        for s in range(N_REAL, N_STATES):
            assert table[name]["state_perm"][s] == s, (name, s)
    trans, _tags = build_trans()
    for s in range(N_REAL):
        for a in range(N_ACTIONS):
            assert not is_pad(trans[s][a][0][1]), (s, a)
    # 6. fake state maps admit no renaming at all
    fake_disk01 = []                      # swap disks 0 and 1 rod-wise
    for s in range(N_STATES):
        if is_pad(s):
            fake_disk01.append(s)
            continue
        p0, p1, p2 = decode(s)
        fake_disk01.append(encode((p1, p0, p2)))
    fake_cycle = []                       # disks 0->1->2->0
    for s in range(N_STATES):
        if is_pad(s):
            fake_cycle.append(s)
            continue
        p0, p1, p2 = decode(s)
        fake_cycle.append(encode((p2, p0, p1)))
    derive_unique_map(fake_disk01, expect=False)
    derive_unique_map(fake_cycle, expect=False)
    # 7. the six actions are pairwise distinguishable on real states
    for a in range(N_ACTIONS):
        for b in range(a + 1, N_ACTIONS):
            distinct = any(move(s, a)[0] != move(s, b)[0]
                           or move(s, a)[2] != move(s, b)[2]
                           for s in range(N_REAL))
            assert distinct, ("actions not distinguishable", a, b)
    # 8. move census: 3 legal pairs per state, 2 on the three corners
    for s in range(N_REAL):
        legal = sum(1 for a in range(N_ACTIONS) if move(s, a)[2] == "M")
        corner = len(set(decode(s))) == 1
        assert legal == (2 if corner else 3), (s, legal, corner)
    return table


def _per_element_action_maps(sym, elements):
    """Closed-group elements (state permutations, file order) -> the list of
    per-element action maps parallel to elements, looked up from the derived
    table. Raises (loud) on any element outside the table. This is the list
    the group files declare as semantics.action_maps; the identity element
    necessarily maps to the identity renaming."""
    by_perm = {tuple(e["state_perm"]): list(e["action_map"])
               for e in sym.values()}
    maps = []
    for e in elements:
        key = tuple(e)
        if key not in by_perm:
            raise AssertionError("group element outside the derived table")
        maps.append(by_perm[key])
    ident = tuple(range(N_STATES))
    for e, m in zip(elements, maps):
        if tuple(e) == ident:
            assert m == list(range(N_ACTIONS))
    return maps


# ---------------------------------------------------------------- groups
PAD_A, PAD_B = 27, 31      # two of the 5 padding states (unused ranks)


def build_groups(sym):
    swap_pi = sym["swap_ab"]["state_perm"]
    rot_pi = sym["rot_abc"]["state_perm"]
    g1 = _closure([swap_pi])
    assert len(g1) == 2
    g3 = _closure([swap_pi, rot_pi])
    assert len(g3) == 6
    assert is_pad(PAD_A) and is_pad(PAD_B)
    g4 = _closure([_swap_states(PAD_A, PAD_B)])
    assert len(g4) == 2
    # g2 is the controlled contrast to g1: identical elements, fixed caliber
    regen = "python -X utf8 cases/hanoi3/make_hanoi3.py"

    return {
        "g1_swap_ab_map.json": {
            "n_states": N_STATES,
            "elements": g1,
            "semantics": {"action": "explicit",
                          "action_maps": _per_element_action_maps(sym, g1)},
            "meta": {
                "claim": ("defendant A: swapping rods A and B and renaming "
                          "the ordered-pair actions with the rods ('the "
                          "move A->B' becomes 'the move B->A', every pair "
                          "renamed (X,Y) -> (piX,piY)) preserves the puzzle "
                          "exactly -- ordered pairs are bound to rod "
                          "identity, so the true symmetry carries its own "
                          "action renaming; declared under the explicit "
                          "caliber with per-element action maps"),
                "construction": ("order-2 group {id, swap_ab} as state "
                                 "permutations; semantics.action_maps = the "
                                 "per-element derived renamings, one "
                                 "bijection per element, parallel to "
                                 "elements (meta.per_element_action_maps "
                                 "holds the full derivation table; "
                                 "rho(identity)=id; the homomorphism law "
                                 "is asserted by this generator and "
                                 "re-checked by the engine at load)"),
                "why_it_is_a_symmetry": ("the move rule is defined through "
                                         "rod identity alone (upper disk of "
                                         "the source rod, larger-or-empty "
                                         "target); swapping the rods and "
                                         "renaming the ordered pairs "
                                         "commutes with every move on "
                                         "every one of the 32 states "
                                         "(asserted exhaustively by the "
                                         "generator over all 6! = 720 "
                                         "ordered-pair permutations, "
                                         "exactly one valid map per "
                                         "element)"),
                "caliber_note": ("explicit declaration: the ordered-pair "
                                 "names are bound to rod identity ('take "
                                 "rod A's upper disk to rod B'), so they "
                                 "travel with the rod swap"),
                "regenerate": regen,
            },
        },
        "g2_swap_nomap.json": {
            "n_states": N_STATES,
            "elements": g1,
            "semantics": {"action": "fixed"},
            "meta": {
                "claim": ("defendant B: the same A<->B rod swap with the "
                          "ordered pairs PINNED (the move A->B must stay "
                          "the move A->B) -- the naive-intuition claim that "
                          "'the tower looks the same with the rods "
                          "relabeled', filed deliberately under the fixed "
                          "caliber to show it is the ordered-pair "
                          "renaming, not the state permutation, that makes "
                          "defendant A true"),
                "construction": ("identical elements to g1_swap_ab_map "
                                 "(order-2 swap group); semantics declared "
                                 "fixed"),
                "why_it_is_not_a_symmetry": ("with the ordered pairs "
                                             "pinned, the relabeled tower "
                                             "answers the move A->B with a "
                                             "move between unswapped rods: "
                                             "on the standard start (all "
                                             "disks on A) the pinned "
                                             "reading moves disk 0 from "
                                             "rod A to rod B while the "
                                             "swapped world requires it "
                                             "from rod B to rod A, so the "
                                             "deterministic successors "
                                             "differ (TV 1.0 on the real "
                                             "states' broken cells)"),
                "caliber_note": ("fixed declaration: this defendant is the "
                                 "controlled contrast to g1 -- same "
                                 "permutation, opposite action caliber"),
                "regenerate": regen,
            },
        },
        "g4_pads.json": {
            "n_states": N_STATES,
            "elements": g4,
            "semantics": {"action": "fixed"},
            "meta": {
                "claim": ("positive control: padding states %d and %d have "
                          "the same behavior shape (every action a single "
                          "self-loop, reward 0), so the swap is a genuine "
                          "symmetry under the pinned-pair reading and "
                          "should be admitted everywhere"
                          % (PAD_A, PAD_B)),
                "construction": ("order-2 group swapping padding states %d "
                                 "<-> %d (two of the 5 unused base-3 "
                                 "ranks 27..31)" % (PAD_A, PAD_B)),
                "why_it_is_a_symmetry": ("padding rows reference no rod; "
                                         "the swap maps every ordered pair "
                                         "to itself under both calibers"),
                "caliber_note": ("isolates the explicit-caliber dispute "
                                 "from model well-formedness: the engine "
                                 "admits this fixed symmetry on the same "
                                 "model; the pads control continues on "
                                 "this docket after mini2048's g6 and "
                                 "sliding2x3's g3 (lightsout3 has no "
                                 "padding states at all)"),
                "regenerate": regen,
            },
        },
        "g3_s3_full.json": {
            "n_states": N_STATES,
            "elements": g3,
            "semantics": {"action": "explicit",
                          "action_maps": _per_element_action_maps(sym, g3)},
            "meta": {
                "claim": ("main positive control: the FULL peg-relabel "
                          "group S3 = C3 x C2 (order 6: identity, swaps "
                          "A<->B / A<->C / B<->C, rotations A->B->C->A / "
                          "A->C->B->A), each element carrying its own "
                          "ordered-pair renaming (X,Y) -> (piX,piY) -- "
                          "the fourth non-trivial positive control of this "
                          "court, after mini2048's D4, lightsout3's D4 and "
                          "sliding2x3's V4, the first non-abelian one, and "
                          "the docket's first entry whose action space is "
                          "ordered rod pairs"),
                "construction": ("closure of {swap_ab, rot_abc} = 6 "
                                 "elements = S3; semantics.action_maps = "
                                 "the per-element derived renamings, one "
                                 "bijection per element, parallel to "
                                 "elements (all six maps exhaustively "
                                 "derived over the 6! = 720 ordered-pair "
                                 "permutations and asserted in "
                                 "meta.per_element_action_maps; "
                                 "rho(identity)=id; homomorphism law "
                                 "asserted over all 36 ordered pairs by "
                                 "this generator and re-checked by the "
                                 "engine at load)"),
                "why_it_is_a_symmetry": ("S3 is the rods' own relabeling "
                                         "group and the move rule is "
                                         "rod-covariant by construction "
                                         "(upper disk of the source rod, "
                                         "larger-or-empty target -- the "
                                         "source states the symmetry: 'the "
                                         "problem is symmetric for "
                                         "permutations of the names of "
                                         "the pegs (symmetric group S3)')"),
                "caliber_note": ("admitted under the explicit caliber with "
                                 "per-element action_maps; compression "
                                 "reading: orbits of S3 on the 32 states "
                                 "(Burnside over the 27 real states: "
                                 "identity fixes 27, each transposition "
                                 "fixes the 1 all-on-the-unswapped-rod "
                                 "state, each rotation fixes nothing, so "
                                 "(27+3)/6 = 5 real-state orbits -- sizes "
                                 "3,6,6,6,6 -- plus 5 fixed padding "
                                 "singletons), live count in "
                                 "receipts/check.g3_s3_full.json"),
                "regenerate": regen,
            },
        },
    }


# ---------------------------------------------------------------- model
def build_model(sym, tags):
    per_elem = {}
    for name in sym:
        per_elem[name] = {
            "sigma": sym[name]["sigma"],
            "action_map": sym[name]["action_map"],
        }
    n_reachable, dist = bfs_all(GOAL_STATE)
    edge_census = {"M": 0, "I": 0, "P": 0}
    for tag in tags:
        for ch in tag:
            edge_census[ch] += 1
    return {
        "n_bits": N_BITS,
        "n_actions": N_ACTIONS,
        "n_states": N_STATES,
        "goals": [],
        "meta": {
            "source_system": (
                "Tower of Hanoi (3 disks, 3 rods; rules public), "
                "transcribed as the deterministic 3-disk variant: 3^3 = 27 "
                "disk-to-rod arrangements, 6 ordered rod-pair actions, no "
                "randomness collected, no score"),
            "variant": "hanoi3-3disk-deterministic",
            "source_citation": (
                'Wikipedia "Tower of Hanoi" (en.wikipedia.org/wiki/'
                'Tower_of_Hanoi): lead ("a mathematical game or puzzle '
                'consisting of three rods and a number of disks of various '
                'diameters, which can slide onto any rod"), rules ("Only '
                'one disk may be moved at a time."; "Each move consists of '
                'taking the upper disk from one of the stacks and placing '
                'it on top of another stack or on an empty rod."; "No disk '
                'may be placed on top of a disk that is smaller than '
                'it."), objective ("The objective of the puzzle is to move '
                'the entire stack to one of the other rods"), minimum '
                'moves ("With three disks, the puzzle can be solved in '
                'seven moves. The minimum number of moves required to '
                'solve a Tower of Hanoi puzzle is 2^n - 1"), graph section '
                '("For a puzzle with n disks, there are 3^n nodes in the '
                'graph"; "every node has three edges to other nodes, '
                'except the three corner nodes, which have two"), symmetry '
                '("the problem is symmetric for permutations of the names '
                'of the pegs (symmetric group S3)"). Per-rule citations in '
                'meta.rules_with_citations; per-edge generating rules in '
                'meta.edge_rule_tags.'),
            "state_names": None,
            "action_names": ACTION_NAMES,
            "state_encoding": (
                "state = 5 bits = the base-3 numeral p0 + 3*p1 + 9*p2 (peg "
                "of disk 0/1/2, disk 0 = smallest = least significant "
                "trit; rods A=0, B=1, C=2). 3^3 = 27 real states; ranks "
                "27..31 are unused encoding space = 5 padding states "
                "(every action self-loops, reward 0 -- same padding "
                "convention as tcp/dhcp/imap/mini2048/sliding2x3); a move "
                "rearranges disks among rods, so real states only reach "
                "real states"),
            "real_states_count": N_REAL,
            "padding_states_count": N_PADS,
            "goal_state": GOAL_STATE,
            "start_state": START_STATE,
            "reachable_from_goal": n_reachable,
            "semantics_class": (
                "ordered-pair: the six actions are ordered rod pairs "
                "(source rod, target rod) bound to rod identity -- the "
                "docket's first entry with pair-semantics actions (contrast "
                "mini2048's arrow keys, lightsout3's buttons, sliding2x3's "
                "directions); a rod relabeling renames the pairs with the "
                "rods (X,Y) -> (piX,piY), so true peg symmetries are "
                "explicit-caliber claims with per-element ordered-pair "
                "renamings; the fixed reading (pairs pinned) is the naive "
                "contrast"),
            "reward_rule": (
                "all zero by design: the puzzle has no score (see "
                "meta.rules_with_citations R4); the win condition is "
                "recorded in meta.win_condition, not as a per-edge reward "
                "(same all-zero convention as tcp/dhcp/imap/lightsout3/"
                "sliding2x3)"),
            "win_condition": (
                "the entire stack on rod C: every disk on rod 2, state "
                "(2,2,2) = index %d -- 'The objective of the puzzle is to "
                "move the entire stack to one of the other rods' (Wikipedia "
                "lead); the standard start (every disk on rod A, state 0) "
                "reaches it in exactly %d moves ('With three disks, the "
                "puzzle can be solved in seven moves' -- Wikipedia; "
                "machine-asserted BFS distance); the puzzle does not lock "
                "on the goal, so it is an ordinary state of the transition "
                "system and goals=[] in this model" % (GOAL_STATE,
                                                        dist[GOAL_STATE])),
            "rules_with_citations": RULES,
            "edge_rule_tags": {
                "layout": (
                    "edge_rule_tags.values[s] is a 6-character string, "
                    "character a in {M,I,P} = the generating rule of edge "
                    "(s, action a); M=a legal ordered-pair move (R1+R2), "
                    "I=unavailable pair (no-op self-loop, R3), P=padding "
                    "self-loop. Census: %d M edges (3 per real state, 2 on "
                    "the three corner states where all disks share a rod "
                    "-- the source's graph description), %d I edges, %d P "
                    "edges (5 padding states x 6 actions)"
                    % (edge_census["M"], edge_census["I"],
                       edge_census["P"])),
                "values": tags,
            },
            "move_census": {
                "legal_M_edges": edge_census["M"],
                "illegal_I_edges": edge_census["I"],
                "padding_P_edges": edge_census["P"],
                "corner_states": [START_STATE,
                                  encode((1, 1, 1)),
                                  GOAL_STATE],
                "note": ("every real state has exactly 3 legal ordered "
                         "pairs except the three corner states (all disks "
                         "on one rod), which have exactly 2 -- Wikipedia's "
                         "graph description 'every node has three edges to "
                         "other nodes, except the three corner nodes, "
                         "which have two', machine-asserted on every run"),
            },
            "per_element_action_maps": per_elem,
            "transcription_notes": TRANSCRIPTION_NOTES,
            "regenerate": "python -X utf8 cases/hanoi3/make_hanoi3.py",
        },
        "trans": _TRANS,
    }


# ------------------------------------------------- expected verdict table
# Observed from a live three-way arbitration run
# (`python -X utf8 -m symmetry_court arbitrate --emit-expected-template`;
# receipt: verdicts/hanoi3.verdict.json). The gate
# (`python -X utf8 -m symmetry_court selftest`) replays every case and
# compares these pinned rows field-by-field against a fresh run.
# Pinned 2026-11-07 from the live run; on this 6-action/5-bit model the
# court-stamped relabel frame resolves to the GENERALIZED judge (six
# actions cannot be indexed as bit flips of a 5-bit state, so no bitstring
# reading arises), which derives the action renaming from the state
# permutation itself -- that derivation coincides with the forced
# per-element ordered-pair maps, so the relabel column passes in step with
# the explicit receipts (contrast mini2048/sliding2x3, where the same
# frame resolves to the bitstring judge and rejects as a diagnostic).
_RELABEL_NOTE = ("court-stamped relabel frame resolves to the generalized "
                 "judge on this 6-action/5-bit model (six actions cannot "
                 "be indexed as bit flips of a 5-bit state, so no "
                 "bitstring reading arises); the generalized judge derives "
                 "the action renaming from the state permutation itself, "
                 "which coincides with the forced per-element ordered-pair "
                 "maps, so the column passes in step with the explicit "
                 "receipts (contrast mini2048/sliding2x3, where the same "
                 "frame resolves to the bitstring judge and rejects as a "
                 "diagnostic)")
_FIXED_NOTE_G2 = ("ordered pairs pinned (--strict): under this caliber the "
                  "rod-swap claim is genuinely false, so this row does not "
                  "flip; the group's explicit-caliber verdict (receipts/) "
                  "is the admitted reading")
_FIXED_NOTE_G4 = ("ordered pairs pinned (fixed declaration): the padding "
                  "rows are byte-identical and reference no rod, so the "
                  "pinned reading is the true reading for this control")

_EXPECTED_NOTE_EXPLICIT = ("the explicit declaration is adjudicated by the "
    "vendored engine directly (receipts/check.%s.json, engine run without "
    "--strict: pass, worst_tv 0.0, homomorphism_checked full) and by the "
    "compare subcommand's declared-caliber gate arm; the relabel column "
    "here resolves to the generalized judge, which derives the action "
    "renaming from the state permutation itself -- on this model that "
    "derivation coincides with the forced per-element ordered-pair maps, "
    "so the column passes in step with the explicit receipts (contrast "
    "mini2048/sliding2x3, where the same frame resolves to the bitstring "
    "judge and rejects as a diagnostic; contrast lightsout3, where 9 "
    "actions = 9 bits made the bitstring derivation coincide with the "
    "per-element button maps); the fixed column is the pairs-pinned "
    "contrast")
_EXPECTED_NOTE_G2 = ("ordered pairs pinned: the rod-swap claim is genuinely "
    "false under this caliber (TV 1.0 -- the relabeled tower answers the "
    "move A->B with a move between unswapped rods, 1/2 elements failing); "
    "the relabel column passes here because the generalized judge derives "
    "the renaming from the state permutation -- the caliber, not the "
    "permutation, decides (compare mini2048's g1/g2 pair, where the "
    "bitstring judge rejected both)")
_EXPECTED_NOTE_G4 = ("fixed-caliber positive control: the two padding rows "
    "are the same behavior shape (every action a single self-loop with "
    "reward 0) and reference no rod, so the pinned reading is the true "
    "reading; this case has 5 real padding states (unused base-3 ranks "
    "27..31), so the pads swap continues on the docket (see the group "
    "file's note)")

EXPECTED_ROWS = {
    "g1_swap_ab_map": {
        "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                    "judge": "generalized", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
        "note": _EXPECTED_NOTE_EXPLICIT % "g1_swap_ab_map",
    },
    "g2_swap_nomap": {
        "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                    "judge": "generalized", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict", "note": _EXPECTED_NOTE_G2},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
    },
    "g4_pads": {
        "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                    "judge": "generalized", "note": _RELABEL_NOTE},
        "fixed": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                  "judge": "strict", "note": _EXPECTED_NOTE_G4},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": True},
    },
    "g3_s3_full": {
        "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                    "judge": "generalized", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
        "note": _EXPECTED_NOTE_EXPLICIT % "g3_s3_full",
    },
}


def build_expected():
    assert EXPECTED_ROWS is not None, \
        "expected rows not pinned yet: run the live arbitration and paste " \
        "the observed template into EXPECTED_ROWS"
    groups = {}
    for name, g in build_groups(_SYM).items():
        key = os.path.splitext(name)[0]
        groups[key] = {
            "claim": g["meta"]["claim"],
            "relabel": dict(EXPECTED_ROWS[key]["relabel"]),
            "fixed": dict(EXPECTED_ROWS[key]["fixed"]),
            "networkx": dict(EXPECTED_ROWS[key]["networkx"]),
        }
        note = EXPECTED_ROWS[key].get("note")
        if note:
            groups[key]["note"] = note
    return {
        "case": "hanoi3",
        "provenance": {
            "recorded": ("2026-11-07, observed from a live three-way "
                         "arbitration run "
                         "(`python -X utf8 -m symmetry_court arbitrate "
                         "--emit-expected-template`); the receipt is "
                         "verdicts/hanoi3.verdict.json; the gate "
                         "(`python -X utf8 -m symmetry_court selftest`) "
                         "replays the case and compares these rows "
                         "field-by-field"),
            "reading_guide": ("relabel row = engine's relabel frame "
                              "(court-stamped copy; on this 6-action/5-bit "
                              "model that frame resolves to the generalized "
                              "judge -- six actions cannot be indexed as "
                              "bit flips of a 5-bit state -- which derives "
                              "the action renaming from the state "
                              "permutation, coinciding with the forced "
                              "per-element ordered-pair maps, so the column "
                              "passes in step with the explicit receipts); "
                              "fixed row = ordered pairs pinned (--strict); "
                              "the explicit declarations of g1/g3 are "
                              "adjudicated by the vendored engine directly "
                              "(receipts in receipts/) and by the compare "
                              "subcommand's declared-caliber gate arm; "
                              "networkx columns = independent juror (at 32 "
                              "states the automorphism-set cross-check "
                              "runs under the court's scale guard, and the "
                              "O(E) direct edge-set check remains the "
                              "primary)"),
        },
        "groups": groups,
    }


# ---------------------------------------------------------------- main
def _dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


_SYM = derive_symmetry_table()
_TRANS, _TAGS = build_trans()


def payloads():
    ps = {"model.json": _dump(build_model(_SYM, _TAGS))}
    if EXPECTED_ROWS is None:
        sys.stderr.write("expected.json NOT written yet (rows not pinned): "
                         "run the live arbitration "
                         "(`python -X utf8 -m symmetry_court arbitrate "
                         "--emit-expected-template --only hanoi3`) and "
                         "paste the observed rows into EXPECTED_ROWS\n")
    else:
        ps["expected.json"] = _dump(build_expected())
    for name, g in build_groups(_SYM).items():
        ps["groups/" + name] = _dump(g)
    return ps


def self_certify(sym):
    """Author-side certification, re-run on every invocation:
    1. the S3 table: unique per-element ordered-pair maps (exhaustive over
       6! = 720), homomorphism law over all 36 ordered pairs, fake controls
       (all asserted inside derive_symmetry_table, re-invoked here);
    2. the move dynamics: deterministic single-successor rows, all-zero
       rewards, real states only reach real states, the move census (3
       legal pairs per real state, 2 on the three corners), exactly 5
       padding rows (all-action self-loops), reachable-from-goal = 27,
       BFS distance start->goal = 7 = 2^3 - 1;
    3. the declared group files: elements match the derived permutations
       and closures, declared action maps match the derived maps, and the
       engine's homomorphism convention holds on every declared pair
       (36 ordered pairs for S3, 4 for the order-2 groups);
    4. orbit counts (the compression readings the receipts should show):
       Burnside cross-checked (g1: (27+1)/2 = 14 real orbits + 5 pad
       singletons = 19; g3: (27+3)/6 = 5 real orbits of sizes 3,6,6,6,6
       + 5 = 10; g4: 31).
    Any failure raises (loud)."""
    sym = derive_symmetry_table()
    trans, tags = build_trans()
    n_pad_rows = 0
    for s in range(N_STATES):
        row_tags = tags[s]
        if is_pad(s):
            n_pad_rows += 1
            for a in range(N_ACTIONS):
                outs = trans[s][a]
                assert len(outs) == 1 and outs[0][0] == 1.0
                assert outs[0][1] == s and outs[0][2] == 0.0
                assert row_tags[a] == "P"
        else:
            assert any(t == "M" for t in row_tags), ("dead real row", s)
            for a in range(N_ACTIONS):
                outs = trans[s][a]
                assert len(outs) == 1 and outs[0][0] == 1.0
                t, r, _tag = move(s, a)
                t2, r2, tag2 = move_stacks(s, a)
                assert (t, r) == (t2, r2), ("stack cross-check", s, a)
                assert outs[0][1] == t and outs[0][2] == r
                assert r == 0.0                             # rule R4
                if row_tags[a] == "M":
                    assert t != s                           # a move moves
                else:
                    assert row_tags[a] == "I" and t == s
    assert n_pad_rows == N_PADS
    n_reach, dist = bfs_all(GOAL_STATE)
    assert n_reach == N_REAL == 27
    assert dist[START_STATE] == 7 == 2 ** N_DISKS - 1        # rule R6
    groups = build_groups(sym)
    ident = list(range(N_STATES))
    for fname, g in groups.items():
        sem = g["semantics"]
        if sem["action"] == "explicit":
            amaps = sem["action_maps"]
            assert len(amaps) == len(g["elements"])
            for m in amaps:
                assert sorted(m) == list(range(N_ACTIONS))
        assert g["n_states"] == N_STATES
        for e in g["elements"]:
            assert len(e) == N_STATES and sorted(e) == list(range(N_STATES))
    # g1 elements == swap_ab closure; g2 identical to g1 (controlled
    # contrast); g4 = pads swap closure; g3 = full S3 closure
    assert groups["g1_swap_ab_map.json"]["elements"] == \
        _closure([sym["swap_ab"]["state_perm"]])
    assert groups["g2_swap_nomap.json"]["elements"] == \
        groups["g1_swap_ab_map.json"]["elements"]
    assert groups["g4_pads.json"]["elements"] == \
        _closure([_swap_states(PAD_A, PAD_B)])
    assert groups["g3_s3_full.json"]["elements"] == \
        _closure([sym["swap_ab"]["state_perm"],
                  sym["rot_abc"]["state_perm"]])
    assert len(groups["g3_s3_full.json"]["elements"]) == 6
    # per-element declared maps: exactly the derived rho of each element,
    # and the engine's homomorphism convention holds on every declared pair
    # ((g o h)[s] = g[h[s]]  =>  rho(g o h) == rho_g o rho_h)
    by_perm = {tuple(e["state_perm"]): list(e["action_map"])
               for e in sym.values()}
    n_pairs_checked = 0
    for key in ("g1_swap_ab_map.json", "g3_s3_full.json"):
        els = groups[key]["elements"]
        mps = groups[key]["semantics"]["action_maps"]
        assert mps == [by_perm[tuple(e)] for e in els], key
        assert any(tuple(e) == tuple(ident) for e in els)
        for e, m in zip(els, mps):
            if tuple(e) == tuple(ident):
                assert m == list(range(N_ACTIONS))
        table = {tuple(e): m for e, m in zip(els, mps)}
        for eg, mg in table.items():
            for eh, mh in table.items():
                comp = tuple(eg[x] for x in eh)
                assert table[comp] == [mg[mh[a]] for a in range(N_ACTIONS)], \
                    (key, comp)
                n_pairs_checked += 1
    # S3's contribution to the ordered-pair audit is 36 pairs (6 x 6)
    assert n_pairs_checked == 36 + 4
    # pads swap: the two swapped rows are the same behavior shape -- every
    # action a single self-loop with reward 0 (each looping to its own
    # index, which is exactly what makes the swap equivariant)
    a, b = PAD_A, PAD_B
    for a2 in range(N_ACTIONS):
        assert trans[a][a2] == [[1.0, a, 0.0]]
        assert trans[b][a2] == [[1.0, b, 0.0]]
    n_orbits = {"g1": orbits(groups["g1_swap_ab_map.json"]["elements"]),
                "g2": orbits(groups["g2_swap_nomap.json"]["elements"]),
                "g3": orbits(groups["g3_s3_full.json"]["elements"]),
                "g4": orbits(groups["g4_pads.json"]["elements"])}
    # Burnside cross-checks
    #   g1 (order 2): Fix(swap_ab) on real states = the 1 state with every
    #     disk on the unswapped rod C -> (27+1)/2 = 14 real orbits + 5 pads
    #   g3 (S3): identity fixes 27, each transposition fixes 1, each
    #     rotation fixes 0 -> (27+3)/6 = 5 real orbits (sizes 3,6,6,6,6)
    #     + 5 pads
    #   g4: 32 states, one transposition -> 31
    assert n_orbits["g1"] == (N_REAL + 1) // 2 + N_PADS == 19
    assert n_orbits["g3"] == (N_REAL + 3 * 1 + 2 * 0) // 6 + N_PADS == 10
    assert orbit_sizes(groups["g3_s3_full.json"]["elements"]) == \
        [1, 1, 1, 1, 1, 3, 6, 6, 6, 6]
    assert n_orbits["g4"] == N_STATES - 1 == 31
    assert n_orbits["g1"] == n_orbits["g2"]
    assert real_orbits(groups["g1_swap_ab_map.json"]["elements"]) == 14
    assert real_orbits(groups["g3_s3_full.json"]["elements"]) == 5
    assert real_orbits(groups["g4_pads.json"]["elements"]) == N_REAL
    return sym, n_orbits


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=here,
                    help="target directory (default: this script's directory)")
    ap.add_argument("--check", action="store_true",
                    help="do not write; verify the committed files are "
                         "byte-identical to a fresh regeneration and re-run "
                         "the symmetry self-certification")
    args = ap.parse_args(argv)

    sym, n_orbits = self_certify(_SYM)
    sys.stderr.write(
        "self-certification OK: 6/6 S3 elements have unique per-element "
        "ordered-pair maps (exhaustive over 6! = 720 permutations; "
        "homomorphism law verified over all 36 ordered pairs of S3 plus "
        "the 4 of the order-2 groups; two fake state maps admit no map; "
        "pads fixed pointwise, real states reach only real states; move "
        "census 78 M / 84 I / 30 P; reachable from goal = 27, start->goal "
        "BFS distance = 7 = 2^3 - 1; all-state orbits g1=%d g2=%d g3=%d "
        "g4=%d (real-state orbits 14/14/5/27)\n"
        % (n_orbits["g1"], n_orbits["g2"], n_orbits["g3"], n_orbits["g4"]))

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

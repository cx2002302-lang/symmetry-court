# -*- coding: utf-8 -*-
"""
make_sliding2x3.py -- deterministic generator for the sliding2x3 case: the
2x3 deterministic transcription of the sliding-puzzle move mechanics (the
n-puzzle family: 15 puzzle / 8 puzzle; Klotski is the sliding-block cognate;
rules public), built as the third docket for the engine's *explicit* action
caliber (state permutation + declared per-element direction renaming) and
the third non-trivial positive control (the full 4-element rectangle group
V4, admitted with per-element action maps).

Writes, byte-identical on every re-run (nothing random, no clock, no locale
dependence), next to this script:

  model.json                     the trans model: 1024 states = 2^10 (the
                                 6! = 720 arrangements are the real states;
                                 ranks 720..1023 are unused encoding space =
                                 304 padding states), 4 slide directions,
                                 rewards all zero by design (the source game
                                 has no score; the win condition is recorded
                                 in meta)
  groups/g1_hflip_map.json       defendant A: left-right board mirror +
                                 renamed directions (explicit+action_maps,
                                 per-element)
  groups/g2_hflip_nomap.json     defendant B: same mirror, directions pinned
                                 (fixed) -- the naive-intuition claim
  groups/g3_pads.json            positive control: swap of two padding
                                 states (fixed, expected pass) -- this case
                                 HAS real padding states (304), so the pads
                                 swap returns after lightsout3's pads-less
                                 docket entry
  groups/g4_v4_full.json         main positive control: the full 4-element
                                 rectangle group V4 = C2 x C2 (explicit +
                                 action_maps, per-element)
  expected.json                  pinned verdict rows, observed live

Transcription authority (primary sources, public):
  - Wikipedia, "15 puzzle" (en.wikipedia.org/wiki/15_puzzle): "Tiles in the
    same row or column of the open position can be moved by sliding them
    horizontally or vertically, respectively."; "The goal of the puzzle is
    to place the tiles in numerical order (from left to right, top to
    bottom)."; "the 8 puzzle, which has 8 tiles in a 3x3 frame" (the n-
    puzzle naming); Johnson & Story (1879) parity: "half of the starting
    positions for the n puzzle are impossible to resolve"; "on boards of
    size m x n, where m and n are both larger than or equal to 2, all even
    permutations are solvable".
  - Wikipedia, "Sliding puzzle" (en.wikipedia.org/wiki/Sliding_puzzle):
    "a combination puzzle that challenges a player to slide (frequently
    flat) pieces along certain routes (usually on a board) to establish a
    certain end-configuration"; "a sliding block puzzle prohibits lifting
    any pieces off the board"; lists Klotski among the examples of sliding
    puzzles (the block-puzzle cognate of the numbered n-puzzle family).

Variant boundaries (recorded, not hidden -- see TRANSCRIPTION_NOTES):
  1. 2x3 board, 5 tiles + open position: the canonical n-puzzle is the 4x4
     15 puzzle ("15 square tiles ... in a frame that is 4 tile positions
     high and 4 tile positions wide"); the 8 puzzle plays the same rules on
     3x3 ("8 tiles in a 3x3 frame"); 2x3 is the smallest rectangular member
     of the same m x n family covered by Johnson & Story's m, n >= 2
     theorem. Every cited rule sentence is size-independent except the
     board size itself, which is recorded as a variant boundary (rule R6).
  2. Initial-scramble randomization is NOT collected: the model is the full
     720-configuration transition system; the starting setup is outside the
     deterministic FSM semantics (same discipline as mini2048's
     random-spawn rule).
  3. No score: the puzzle has no numeric payoff, so the reward layer is all
     zero by design and the win condition (tiles in numerical order) is
     recorded in meta.win_condition as a goal property, not a per-edge
     reward (same all-zero convention as tcp/dhcp/imap/lightsout3).

The explicit caliber and this case: a board symmetry moves the direction
names with the cells (mirroring the board left-right turns "a tile slides
left" into "a tile slides right"). Per group element pi the direction
renaming rho(pi) is forced, and pi |-> rho(pi) is a group homomorphism.
Since 2026-11-04 the engine's group format accepts semantics.action_maps:
one action renaming (bijection) per group element, parallel to elements,
homomorphism-law checked at load -- each explicit group file here declares
the per-element maps of its own elements (exhaustively derived and asserted
by this generator on every run over all 4! = 24 direction permutations);
model.meta.per_element_action_maps holds the full derivation table.

Why V4 (and not D4): the 2x3 board is a rectangle that is not a square, so
its geometric symmetry group has order 4 -- {id, left-right mirror,
top-bottom mirror, 180-degree rotation} = the Klein four-group V4 = C2 x C2
(no 90-degree rotation exists on a non-square board). This is a third
group structure on the docket, distinct from mini2048's and lightsout3's D4
(order 8) and lightsout3's D4 x C2 (order 16). The generator machine-verifies
that V4 is exactly the full geometric group of this board: all 6! = 720
cell bijections are enumerated and exactly 4 preserve the 2x3 adjacency
graph (asserted on every run).

Why the pads positive control exists here: the state encoding needs
n_states = 2^10 = 1024 slots for 6! = 720 real arrangements, so 304 unused
ranks are padding states (every action self-loops with reward 0 -- the same
padding convention as tcp/dhcp/imap/mini2048). Two padding states therefore
have the same behavior shape (every action a single self-loop with reward
0) and their swap is a genuine fixed-caliber symmetry
(g3_pads) -- the pads positive control returns on this docket after
lightsout3, which has no padding states at all (its deviation note is the
honest record of that gap; ruled 2026-11-04: faithful transcription
outranks control-form symmetry). Placement note recorded during case
engineering: mini2048 pairs the explicit caliber with real padding states
and a pads control (its g6) on the same docket; sliding2x3 pairs them again
on a third group structure (V4), and it is the pads control's return after
lightsout3's no-padding case.

Usage:
  python -X utf8 cases/sliding2x3/make_sliding2x3.py            # write all files
  python -X utf8 cases/sliding2x3/make_sliding2x3.py --out DIR  # write into DIR
  python -X utf8 cases/sliding2x3/make_sliding2x3.py --check    # verify bytes +
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
# Cell index i = 3*row + col on a 2x3 grid, (x, y) = (column, row), x
# rightward, y downward: 0=top-left, 1=top-center, 2=top-right,
# 3=bottom-left, 4=bottom-center, 5=bottom-right. A configuration is the
# 6-tuple of tile ids in cells 0..5, values {0..5} pairwise distinct with
# 0 = the open position and 1..5 = the numbered tiles: 6! = 720 real states.
# State = the lexicographic rank of the configuration among the 720
# permutations of (0,1,2,3,4,5); n_bits = 10 (2^10 = 1024 >= 720); ranks
# 720..1023 are unused encoding space = 304 padding states.
CELL_XY = [(x, y) for y in range(2) for x in range(3)]   # index -> (x, y)
XY_CELL = {xy: i for i, xy in enumerate(CELL_XY)}
N_CELLS = 6
N_TILES = 5
N_REAL = 720                                             # 6!
N_BITS = 10
N_STATES = 1 << N_BITS                                   # 1024
N_PADS = N_STATES - N_REAL                               # 304
N_ACTIONS = 4

# Actions = slide directions, indexed 0=up, 1=down, 2=left, 3=right. The
# direction names the motion of the SLIDING TILE (the public wording: a
# tile slides into the adjacent open position), so the open position moves
# one step in the OPPOSITE direction: action "up" = the tile below the open
# position slides up into it = the open position moves down. Recorded in
# meta.action_names / rules R1; action indices are this transcription's own
# convention (the source names no numbering), not a court choice.
ACTION_NAMES = ["up", "down", "left", "right"]

# Open-position displacement per action (dx, dy): the open position moves
# OPPOSITE to the tile's slide direction.
BLANK_DELTA = {0: (0, 1), 1: (0, -1), 2: (1, 0), 3: (-1, 0)}

WIKI15 = 'Wikipedia "15 puzzle" (en.wikipedia.org/wiki/15_puzzle), '
WIKISL = 'Wikipedia "Sliding puzzle" (en.wikipedia.org/wiki/Sliding_puzzle), '

RULES = [
    {"id": "R1-slide-into-open-position",
     "rule": ("one move = one numbered tile slides one grid step into the "
              "adjacent open position (the open position moves one step in "
              "the opposite direction); a tile is eligible when it sits in "
              "the same row or column as the open position and adjacent to "
              "it -- the four slide directions are the four actions"),
     "citation": (WIKI15 + "'Tiles in the same row or column of the open "
                  "position can be moved by sliding them horizontally or "
                  "vertically, respectively.' (the eligible tiles are the "
                  "ones aligned with the open position; one move slides the "
                  "adjacent one one step -- multi-tile push shorthands are "
                  "not collected); " + WIKISL + "'a combination puzzle that "
                  "challenges a player to slide (frequently flat) pieces "
                  "along certain routes (usually on a board) to establish a "
                  "certain end-configuration.'")},
    {"id": "R2-no-lifting-one-step",
     "rule": ("pieces never leave the board and never jump: only the tile "
              "orthogonally adjacent to the open position can slide, and a "
              "direction with no tile to slide changes nothing (the move is "
              "unavailable; recorded as a no-op self-loop with reward 0, "
              "same convention as mini2048's unavailable-direction "
              "self-loops)"),
     "citation": (WIKISL + "'Unlike tour puzzles, a sliding block puzzle "
                  "prohibits lifting any pieces off the board.'; the one-"
                  "step adjacency follows from R1's 'the open position' "
                  "wording (only the adjacent tile can slide into it in a "
                  "single move)")},
    {"id": "R3-goal-numerical-order",
     "rule": ("the goal configuration is the tiles in numerical order from "
              "left to right, top to bottom, with the open position last "
              "(bottom-right): the arrangement (1,2,3,4,5,0) -- recorded in "
              "meta.win_condition as a goal property"),
     "citation": (WIKI15 + "'The goal of the puzzle is to place the tiles "
                  "in numerical order (from left to right, top to "
                  "bottom).'")},
    {"id": "R4-no-score",
     "rule": ("the puzzle has no score; the reward layer is all zero by "
              "design and the win condition is recorded in "
              "meta.win_condition, not as a per-edge reward"),
     "citation": (WIKI15 + "the article defines the goal as a configuration "
                  "(R3) and describes no scoring; its solver content "
                  "('Commonly used heuristics for this problem include "
                  "counting the number of misplaced tiles and finding the "
                  "sum of the taxicab distances between each block and its "
                  "position in the goal configuration') is solver advice, "
                  "not a game payoff -- recorded, not turned into a reward; "
                  "same all-zero reward convention as the tcp/dhcp/imap/"
                  "lightsout3 cases")},
    {"id": "R5-parity-invariant-recorded",
     "rule": ("RECORDED, NOT REPAIRED: moves partition the 6! = 720 "
              "configurations into two parity classes of 360 each (only "
              "half of the starting positions are solvable from a given "
              "goal); the model transcribes the FULL 720-configuration "
              "transition system -- both classes are real states and the "
              "class split is a property of the state space, machine-"
              "asserted by a BFS from the goal (360 reachable), not encoded "
              "as unreachable padding"),
     "citation": (WIKI15 + "'Johnson & Story (1879) used a parity argument "
                  "to show that half of the starting positions for the n "
                  "puzzle are impossible to resolve, no matter how many "
                  "moves are made.'; 'on boards of size m x n, where m and "
                  "n are both larger than or equal to 2, all even "
                  "permutations are solvable'")},
    {"id": "R6-board-2x3-VARIANT",
     "rule": ("VARIANT BOUNDARY: this case is the 2x3 board (5 tiles + open "
              "position); the canonical n-puzzle is the 4x4 fifteen puzzle, "
              "the 8 puzzle plays the same rules on 3x3"),
     "citation": (WIKI15 + "'It has 15 square tiles numbered 1 to 15 in a "
                  "frame that is 4 tile positions high and 4 tile positions "
                  "wide, with one unoccupied position.'; 'Similar names are "
                  "used for different sized variants of the 15 puzzle, such "
                  "as the 8 puzzle, which has 8 tiles in a 3x3 frame.'; the "
                  "m x n family with m, n >= 2 is covered by the Johnson & "
                  "Story solvability theorem quoted in R5; Klotski (listed "
                  "among the examples of sliding puzzles) is the sliding-"
                  "block cognate of this family")},
    {"id": "R7-deterministic",
     "rule": ("play itself is deterministic: a slide always moves exactly "
              "the one adjacent tile, with no randomness; the physical "
              "puzzle's initial scramble is the only stochastic step and it "
              "is NOT collected (outside the deterministic FSM semantics)"),
     "citation": ("consequence of R1 as stated by " + WIKISL + "and " +
                  WIKI15 + " (a slide moves exactly one tile; nothing else "
                  "happens); same not-collected discipline as mini2048's "
                  "random-spawn rule")},
    {"id": "R8-family",
     "rule": ("family placement: the numbered uniform-tile n-puzzle member "
              "of the sliding-puzzle family; Klotski is the unequal-block "
              "cognate and is NOT transcribed here (its multi-cell pieces "
              "would need a different state space)"),
     "citation": (WIKISL + "'A sliding puzzle, sliding block puzzle, or "
                  "sliding tile puzzle is a combination puzzle ...' with "
                  "'Fifteen puzzle' and 'Klotski' listed among its examples "
                  "of sliding puzzles; " + WIKI15 + "for the numbered "
                  "uniform-tile member")},
]

TRANSCRIPTION_NOTES = [
    "scope: 2x3 board, 5 numbered tiles + 1 open position, 4 slide "
    "directions; the deterministic slide mechanics of the n-puzzle family "
    "(rule R1) with the initial scramble NOT collected (rule R7) -- "
    "randomness is not part of the deterministic FSM semantics, per the "
    "court's not-collected discipline (same pattern as mini2048's "
    "random-spawn rule).",
    "VARIANT BOUNDARY (rule R6): the 2x3 board; the canonical n-puzzle is "
    "the 4x4 fifteen puzzle and the 8 puzzle plays on 3x3 ('Similar names "
    "are used for different sized variants of the 15 puzzle, such as the 8 "
    "puzzle, which has 8 tiles in a 3x3 frame', Wikipedia). Every cited "
    "rule sentence is size-independent except the board size; the m x n "
    "family with m, n >= 2 is covered by Johnson & Story's solvability "
    "theorem; Klotski is the sliding-block cognate, not transcribed here.",
    "actions: four slide directions indexed 0=up, 1=down, 2=left, 3=right; "
    "the direction names the motion of the sliding TILE (a tile slides in "
    "that direction into the adjacent open position), so the open position "
    "moves one step in the opposite direction. The source names no action "
    "numbering; the indices are this transcription's own convention, "
    "recorded here and in meta.action_names.",
    "encoding: state = 10 bits = the lexicographic rank of the "
    "configuration among the 6! = 720 permutations of (0..5) (cells 0..5 "
    "row-major; value 0 = the open position, 1..5 = the numbered tiles). "
    "Ranks 720..1023 are unused encoding space: 304 padding states, every "
    "action self-loops with reward 0 (same padding convention as "
    "tcp/dhcp/imap/mini2048). Real states only reach real states: a slide "
    "rearranges tiles, and a rearrangement of (0..5) is again a "
    "permutation of (0..5), so a slide never produces an unused rank "
    "(machine-asserted by this generator on every run).",
    "parity recorded, not repaired (rule R5): the 720 real states split "
    "into two move-invariant classes of 360 each (Johnson & Story 1879); "
    "both classes are real states of this model. BFS from the goal "
    "configuration reaches exactly 360 of them (machine-asserted on every "
    "run); the other 360 are the unsolvable-from-goal class, present and "
    "well-formed.",
    "rewards: all zero by design (rule R4) -- the puzzle has no score; the "
    "win condition (tiles in numerical order, open position last: "
    "arrangement (1,2,3,4,5,0)) is recorded in meta.win_condition as a "
    "goal property and the puzzle does not lock on it, so it is an "
    "ordinary state of the transition system and goals=[] in this model. "
    "The adjudication therefore runs entirely on the transition layer "
    "(same all-zero convention as tcp/dhcp/imap/lightsout3).",
    "explicit caliber note: a board symmetry renames the slide directions "
    "element-by-element (mirroring the board left-right turns 'a tile "
    "slides left' into 'a tile slides right'); rho(identity)=id while "
    "rho(hflip)!=id, so no single action_map can serve a whole closed "
    "group. Since 2026-11-04 the engine's group format accepts "
    "semantics.action_maps (one bijection per element, parallel to "
    "elements, homomorphism-law checked at load); each explicit group file "
    "here declares the per-element maps of its own elements, and "
    "meta.per_element_action_maps holds the full derivation (exhaustively "
    "derived over all 4! = 24 direction permutations, unique per element, "
    "asserted on every run).",
    "why V4: the 2x3 board is a non-square rectangle, so its geometric "
    "symmetry group is the Klein four-group V4 = C2 x C2 of order 4 "
    "(identity, left-right mirror, top-bottom mirror, 180-degree "
    "rotation) -- no 90-degree rotation exists. The generator enumerates "
    "all 720 cell bijections against the 2x3 adjacency graph and machine-"
    "asserts exactly 4 survivors (the V4 content maps): a third group "
    "structure on the docket, distinct from mini2048's and lightsout3's "
    "D4 (order 8) and lightsout3's D4 x C2 (order 16).",
    "padding positive control: 304 real padding states exist (the unused "
    "ranks), so the pads swap of mini2048's g6 returns here as g3_pads "
    "after lightsout3's pads-less docket entry (lightsout3 has no padding "
    "states at all; its deviation note, ruled 2026-11-04: faithful "
    "transcription outranks control-form symmetry, is the honest record of "
    "that gap). Placement note: mini2048 pairs the explicit caliber with "
    "real padding states and a pads control on the same docket; this case "
    "pairs them again on a third group structure (V4).",
    "regenerate: python -X utf8 cases/sliding2x3/make_sliding2x3.py",
]

# ---------------------------------------------------------------- encoding
FACT = [1, 1, 2, 6, 24, 120]


def rank_of(arr):
    """Lexicographic rank of a 6-permutation of (0..5) among all 720."""
    avail = [0, 1, 2, 3, 4, 5]
    r = 0
    for i, v in enumerate(arr):
        idx = avail.index(v)
        r += idx * FACT[N_CELLS - 1 - i]
        avail.pop(idx)
    return r


def unrank(r):
    """Inverse of rank_of (r in [0, 720))."""
    avail = [0, 1, 2, 3, 4, 5]
    arr = []
    for i in range(N_CELLS):
        f = FACT[N_CELLS - 1 - i]
        idx, r = divmod(r, f)
        arr.append(avail.pop(idx))
    assert r == 0
    return tuple(arr)


GOAL_ARRANGEMENT = (1, 2, 3, 4, 5, 0)
GOAL_STATE = rank_of(GOAL_ARRANGEMENT)


def decode(s):
    """Real state index -> configuration tuple (tile per cell, 0=open)."""
    assert 0 <= s < N_REAL
    return unrank(s)


def encode(arr):
    """Configuration tuple -> real state index (arr must be a permutation)."""
    assert sorted(arr) == list(range(N_CELLS))
    return rank_of(arr)


def is_pad(s):
    return s >= N_REAL


# ---------------------------------------------------------------- move rule
def move(s, a):
    """Deterministic slide -> (successor state, reward, tag).

    Tag: 'S' a tile slid into the open position (R1), 'I' the direction has
    no tile to slide (no-op self-loop, R2), 'P' padding self-loop.
    Returns the rule tags so every edge's generating rules are recorded
    (meta.edge_rule_tags).
    """
    if is_pad(s):
        return s, 0.0, "P"
    arr = list(decode(s))
    b = arr.index(0)
    bx, by = CELL_XY[b]
    dx, dy = BLANK_DELTA[a]          # the open position moves opposite the tile
    tx, ty = bx + dx, by + dy
    if not (0 <= tx < 3 and 0 <= ty < 2):
        return s, 0.0, "I"           # no tile to slide in this direction
    t = XY_CELL[(tx, ty)]
    arr[b], arr[t] = arr[t], 0       # the tile slides into the old open cell
    return encode(arr), 0.0, "S"


def build_trans():
    """1024 x 4 deterministic rows + the per-edge rule-tag table."""
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


# ---------------------------------------------------------------- symmetries
def cell_map_of(fn):
    """(x,y)->(x',y') board transform -> content map d: content of cell c
    moves to cell d[c]."""
    d = []
    for (x, y) in CELL_XY:
        d.append(XY_CELL[fn(x, y)])
    return d


def state_perm_of(d):
    """Content map d -> state permutation pi: pi(s)[d[c]] = s[c] on real
    states (rank encoding); the padding region is fixed pointwise (unused
    ranks are not board configurations -- recorded in
    meta.transcription_notes)."""
    pi = []
    for s in range(N_STATES):
        if is_pad(s):
            pi.append(s)
            continue
        arr = decode(s)
        new = [0] * N_CELLS
        for c in range(N_CELLS):
            new[d[c]] = arr[c]
        pi.append(encode(new))
    return pi


def compose_d(d2, d1):
    """Content maps: apply d1, then d2 on top."""
    return [d2[d1[c]] for c in range(N_CELLS)]


# The rectangle symmetries as (x, y) transforms (V4 on the 2x3 grid).
V4_TRANSFORMS = [
    ("id",     lambda x, y: (x, y)),
    ("hflip",  lambda x, y: (2 - x, y)),   # left-right mirror
    ("vflip",  lambda x, y: (x, 1 - y)),   # top-bottom mirror
    ("rot180", lambda x, y: (2 - x, 1 - y)),
]

ADJACENCY = [(0, 1), (1, 2), (3, 4), (4, 5), (0, 3), (1, 4), (2, 5)]


def board_automorphisms():
    """All cell bijections preserving the 2x3 adjacency graph (machine
    check that the full geometric group is exactly V4)."""
    out = []
    for perm in itertools.permutations(range(N_CELLS)):
        edges = {(perm[a], perm[b]) for (a, b) in ADJACENCY}
        edges |= {(b, a) for (a, b) in edges}
        if edges == {(a, b) for (a, b) in ADJACENCY} | \
                {(b, a) for (a, b) in ADJACENCY}:
            out.append(list(perm))
    return out


_MAP_CACHE = {}


def derive_action_map(pi):
    """Exhaustive search over ALL 4! = 24 direction permutations for rho
    with, for ALL states s and actions a:
        move(pi(s), rho[a]) == pi(move(s, a))            (transition layer)
        reward(pi(s), rho[a]) == reward(move(s, a))      (trivially true:
                                                          rewards all zero,
                                                          checked separately)
    Returns the list of valid rhos (asserted by callers to have length
    exactly 1, or 0 for non-symmetries). Memoized per permutation. This is
    the author-side derivation of the per-element direction renaming; the
    engine's verdicts remain the court's judges."""
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
    """Orbit count restricted to the 720 real states (the pads are fixed
    pointwise, so full-state orbits = real orbits + 304 singletons)."""
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


def reachable_from_goal():
    """BFS over real states from the goal configuration (parity-class
    size, rule R5: machine-asserted 360 = half of 720)."""
    seen = {GOAL_STATE}
    frontier = [GOAL_STATE]
    while frontier:
        nxt = []
        for s in frontier:
            for a in range(N_ACTIONS):
                t, _r, tag = move(s, a)
                if tag != "I" and t not in seen:
                    seen.add(t)
                    nxt.append(t)
        frontier = nxt
    return len(seen)


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
    """Per-element direction maps for the whole V4 + the homomorphism and
    fake-control checks.

    Returns dict name -> {"content_map": d, "state_perm": pi,
                          "action_map": rho}.
    Asserts (loud, on every run):
      1. the full geometric group of the 2x3 board is exactly V4: the 720
         cell bijections preserve the adjacency graph for exactly the four
         V4 content maps (a third group structure on the docket -- no 90
         degree rotation exists on a non-square rectangle);
      2. every V4 element has exactly one rho (exhaustive over 4! = 24);
      3. rho(id) = id and rho(hflip) != id (non-triviality);
      4. the homomorphism law rho(d2 o d1) == rho(d2) o rho(d1) for all 16
         ordered pairs;
      5. the padding region (304 states) is fixed pointwise by every
         element and real states never reach padding states;
      6. two fake transforms that are not board symmetries (a cyclic
         column shift; a top-row left swap) admit NO rho at all;
      7. the four actions are pairwise distinguishable (supporting data
         for uniqueness: for any two directions some real state tells them
         apart).
    """
    # 1. the full geometric group is exactly V4
    autos = board_automorphisms()
    v4_maps = {tuple(cell_map_of(fn)) for _n, fn in V4_TRANSFORMS}
    assert len(autos) == 4 and {tuple(a) for a in autos} == v4_maps, \
        "the 2x3 board's full geometric group is not V4: %r" % (autos,)
    table = {}
    for name, fn in V4_TRANSFORMS:
        d = cell_map_of(fn)
        pi = state_perm_of(d)
        table[name] = {"content_map": d, "state_perm": pi,
                       "action_map": derive_unique_map(pi)}
    # 3. identity / non-triviality
    assert table["id"]["action_map"] == list(range(N_ACTIONS))
    assert table["hflip"]["action_map"] != list(range(N_ACTIONS))
    # 4. homomorphism: rho(d2 o d1) == rho(d2) o rho(d1)   (apply d1 then d2)
    for (n1, f1) in V4_TRANSFORMS:
        for (n2, f2) in V4_TRANSFORMS:
            comp = compose_d(table[n2]["content_map"], table[n1]["content_map"])
            assert comp == cell_map_of(lambda x, y, f1=f1, f2=f2: f2(*f1(x, y))), \
                (n1, n2)
            want = compose_maps(table[n2]["action_map"], table[n1]["action_map"])
            got = derive_unique_map(state_perm_of(comp))
            assert got == want, ("homomorphism broken", n1, n2, got, want)
    # 5. pads fixed pointwise; real states reach only real states
    for name in table:
        for s in range(N_REAL, N_STATES):
            assert table[name]["state_perm"][s] == s, (name, s)
    trans, _tags = build_trans()
    for s in range(N_REAL):
        for a in range(N_ACTIONS):
            assert not is_pad(trans[s][a][0][1]), (s, a)
    # 6. fake transforms admit no renaming at all
    fake_shift = [XY_CELL[((x + 1) % 3, y)] for (x, y) in CELL_XY]
    fake_rowswap = [1, 0, 2, 3, 4, 5]          # swap cells 0<->1 only
    derive_unique_map(state_perm_of(fake_shift), expect=False)
    derive_unique_map(state_perm_of(fake_rowswap), expect=False)
    # 7. the four actions are pairwise distinguishable on real states
    for a in range(N_ACTIONS):
        for b in range(a + 1, N_ACTIONS):
            distinct = any(move(s, a)[0] != move(s, b)[0]
                           or move(s, a)[2] != move(s, b)[2]
                           for s in range(N_REAL))
            assert distinct, ("actions not distinguishable", a, b)
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
PAD_A, PAD_B = 720, 1023   # two of the 304 padding states (unused ranks)


def build_groups(sym):
    hflip_pi = sym["hflip"]["state_perm"]
    vflip_pi = sym["vflip"]["state_perm"]
    g1 = _closure([hflip_pi])
    assert len(g1) == 2
    g4 = _closure([hflip_pi, vflip_pi])
    assert len(g4) == 4
    assert is_pad(PAD_A) and is_pad(PAD_B)
    g3 = _closure([_swap_states(PAD_A, PAD_B)])
    assert len(g3) == 2
    # g2 is the controlled contrast to g1: identical elements, fixed caliber
    regen = "python -X utf8 cases/sliding2x3/make_sliding2x3.py"

    return {
        "g1_hflip_map.json": {
            "n_states": N_STATES,
            "elements": g1,
            "semantics": {"action": "explicit",
                          "action_maps": _per_element_action_maps(sym, g1)},
            "meta": {
                "claim": ("defendant A: mirroring the 2x3 board left-right "
                          "and renaming the slide directions with it ('a "
                          "tile slides left' becomes 'a tile slides right', "
                          "up/down unchanged) preserves the puzzle exactly "
                          "-- directions are bound to board coordinates, so "
                          "the true symmetry carries its own direction "
                          "renaming; declared under the explicit caliber "
                          "with per-element action maps"),
                "construction": ("order-2 group {id, hflip} as state "
                                 "permutations; semantics.action_maps = the "
                                 "per-element derived renamings, one "
                                 "bijection per element, parallel to "
                                 "elements (meta.per_element_action_maps "
                                 "holds the full derivation table; "
                                 "rho(identity)=id; the homomorphism law is "
                                 "asserted by this generator and re-checked "
                                 "by the engine at load)"),
                "why_it_is_a_symmetry": ("the slide rule is defined through "
                                         "the same adjacency shape (rule R1) "
                                         "in every direction; mirroring the "
                                         "board and renaming the directions "
                                         "commutes with every slide on "
                                         "every one of the 1024 states "
                                         "(asserted exhaustively by the "
                                         "generator over all 4! = 24 "
                                         "direction permutations, exactly "
                                         "one valid map per element)"),
                "caliber_note": ("explicit declaration: the direction names "
                                 "are bound to board coordinates ('a tile "
                                 "slides left'), so they travel with the "
                                 "mirror"),
                "regenerate": regen,
            },
        },
        "g2_hflip_nomap.json": {
            "n_states": N_STATES,
            "elements": g1,
            "semantics": {"action": "fixed"},
            "meta": {
                "claim": ("defendant B: the same left-right mirror with the "
                          "directions PINNED (a slide left must stay a slide "
                          "left) -- the naive-intuition claim that 'the "
                          "board looks the same mirrored', filed "
                          "deliberately under the fixed caliber to show it "
                          "is the direction renaming, not the state "
                          "permutation, that makes defendant A true"),
                "construction": ("identical elements to g1_hflip_map "
                                 "(order-2 mirror group); semantics "
                                 "declared fixed"),
                "why_it_is_not_a_symmetry": ("with the directions pinned, "
                                             "the mirrored board answers the "
                                             "left slide with the right "
                                             "neighbor: on the goal state "
                                             "the pinned reading swaps the "
                                             "role of the left and right "
                                             "columns, so the deterministic "
                                             "successors differ (TV 1.0 on "
                                             "every real state's slide "
                                             "edges)"),
                "caliber_note": ("fixed declaration: this defendant is the "
                                 "controlled contrast to g1 -- same "
                                 "permutation, opposite action caliber"),
                "regenerate": regen,
            },
        },
        "g3_pads.json": {
            "n_states": N_STATES,
            "elements": g3,
            "semantics": {"action": "fixed"},
            "meta": {
                "claim": ("positive control: padding states %d and %d have "
                          "the same behavior shape (every action a single "
                          "self-loop, "
                          "reward 0), so the swap is a genuine symmetry "
                          "under the pinned-direction reading and should be "
                          "admitted everywhere" % (PAD_A, PAD_B)),
                "construction": ("order-2 group swapping padding states %d "
                                 "<-> %d (two of the 304 unused lexicographic "
                                 "ranks 720..1023)" % (PAD_A, PAD_B)),
                "why_it_is_a_symmetry": ("padding rows reference no "
                                         "direction; the swap maps every "
                                         "slide to itself under both "
                                         "calibers"),
                "caliber_note": ("isolates the explicit-caliber dispute "
                                 "from model well-formedness: the engine "
                                 "admits this fixed symmetry on the same "
                                 "model; the pads control returns on this "
                                 "docket after lightsout3 (which has no "
                                 "padding states at all) -- mini2048 pairs "
                                 "the explicit caliber with real padding "
                                 "states and a pads control too, this case "
                                 "pairs them again on a third group "
                                 "structure (V4)"),
                "regenerate": regen,
            },
        },
        "g4_v4_full.json": {
            "n_states": N_STATES,
            "elements": g4,
            "semantics": {"action": "explicit",
                          "action_maps": _per_element_action_maps(sym, g4)},
            "meta": {
                "claim": ("main positive control: the FULL 4-element "
                          "rectangle symmetry group V4 = C2 x C2 (identity, "
                          "left-right mirror, top-bottom mirror, 180-degree "
                          "rotation), each element carrying its own "
                          "direction renaming -- the third non-trivial "
                          "positive control of this court, after mini2048's "
                          "D4 and lightsout3's D4, and a third group "
                          "structure (the board is a non-square rectangle: "
                          "no 90-degree rotation exists, machine-verified "
                          "by enumerating all 720 cell bijections against "
                          "the adjacency graph)"),
                "construction": ("closure of {hflip, vflip} = 4 elements = "
                                 "V4; semantics.action_maps = the "
                                 "per-element derived renamings, one "
                                 "bijection per element, parallel to "
                                 "elements (all four maps exhaustively "
                                 "derived over the 4! = 24 direction "
                                 "permutations and asserted in "
                                 "meta.per_element_action_maps; "
                                 "rho(identity)=id; homomorphism law "
                                 "asserted by this generator and re-checked "
                                 "by the engine at load)"),
                "why_it_is_a_symmetry": ("V4 is the rectangle's own "
                                         "symmetry group and the slide rule "
                                         "is direction-symmetric by "
                                         "construction (one adjacency rule, "
                                         "four directions)"),
                "caliber_note": ("admitted under the explicit caliber with "
                                 "per-element action_maps; compression "
                                 "reading: orbits of V4 on the 1024 states "
                                 "(Burnside: 484 = (720+0+0+0)/4 real-state "
                                 "orbits of size 4 + 304 fixed padding "
                                 "singletons), live count in "
                                 "receipts/check.g4_v4_full.json"),
                "regenerate": regen,
            },
        },
    }


# ---------------------------------------------------------------- model
def build_model(sym, tags):
    per_elem = {}
    for name in sym:
        per_elem[name] = {
            "content_map": sym[name]["content_map"],
            "action_map": sym[name]["action_map"],
        }
    return {
        "n_bits": N_BITS,
        "n_actions": N_ACTIONS,
        "n_states": N_STATES,
        "goals": [],
        "meta": {
            "source_system": (
                "Sliding puzzle / n-puzzle family (15 puzzle; Klotski is "
                "the sliding-block cognate; rules public), transcribed as "
                "the 2x3 deterministic variant: 5 numbered tiles + 1 open "
                "position, 4 slide directions, no randomness collected, no "
                "score"),
            "variant": "sliding2x3-n-puzzle-deterministic",
            "source_citation": (
                'Wikipedia "15 puzzle" (en.wikipedia.org/wiki/15_puzzle): '
                'lead ("Tiles in the same row or column of the open '
                'position can be moved by sliding them horizontally or '
                'vertically, respectively."; "The goal of the puzzle is to '
                'place the tiles in numerical order (from left to right, '
                'top to bottom)."; "the 8 puzzle, which has 8 tiles in a '
                '3x3 frame"), Solvability section ("Johnson & Story (1879) '
                'used a parity argument to show that half of the starting '
                'positions for the n puzzle are impossible to resolve"; "on '
                'boards of size m x n, where m and n are both larger than '
                'or equal to 2, all even permutations are solvable"); '
                'Wikipedia "Sliding puzzle" (en.wikipedia.org/wiki/'
                'Sliding_puzzle): lead ("a combination puzzle that '
                'challenges a player to slide (frequently flat) pieces '
                'along certain routes (usually on a board) to establish a '
                'certain end-configuration"; "a sliding block puzzle '
                'prohibits lifting any pieces off the board"), with Klotski '
                "listed among the examples of sliding puzzles. Per-rule "
                "citations in meta.rules_with_citations; per-edge "
                "generating rules in meta.edge_rule_tags."),
            "state_names": None,
            "action_names": ACTION_NAMES,
            "state_encoding": (
                "state = 10 bits = the lexicographic rank of the "
                "configuration among the 6! = 720 permutations of (0..5); "
                "cells 0..5 row-major (0=top-left ... 5=bottom-right), tile "
                "value 0 = the open position, 1..5 = the numbered tiles; "
                "ranks 720..1023 are unused encoding space = 304 padding "
                "states (every action self-loops, reward 0 -- same padding "
                "convention as tcp/dhcp/imap/mini2048); a slide never "
                "produces an unused rank, so real states only reach real "
                "states"),
            "real_states_count": N_REAL,
            "padding_states_count": N_PADS,
            "goal_state": GOAL_STATE,
            "reachable_from_goal": reachable_from_goal(),
            "semantics_class": (
                "direction-key: the four actions are slide directions bound "
                "to board coordinates (a tile slides in the named "
                "direction); a board symmetry renames the directions with "
                "the cells, so true board symmetries are explicit-caliber "
                "claims with per-element direction renamings; the fixed "
                "reading (directions pinned) is the naive contrast"),
            "reward_rule": (
                "all zero by design: the puzzle has no score (see "
                "meta.rules_with_citations R4); the win condition is "
                "recorded in meta.win_condition, not as a per-edge reward "
                "(same all-zero convention as tcp/dhcp/imap/lightsout3)"),
            "win_condition": (
                "tiles in numerical order from left to right, top to "
                "bottom, open position last (bottom-right): the "
                "arrangement (1,2,3,4,5,0), state index %d -- 'The goal of "
                "the puzzle is to place the tiles in numerical order (from "
                "left to right, top to bottom)' (Wikipedia 15 puzzle lead); "
                "the puzzle does not lock on the goal, so it is an ordinary "
                "state of the transition system and goals=[] in this model"
                % GOAL_STATE),
            "rules_with_citations": RULES,
            "edge_rule_tags": {
                "layout": (
                    "edge_rule_tags.values[s] is a 4-character string, "
                    "character a in {S,I,P} = the generating rule of edge "
                    "(s, action a); S=a tile slid into the open position "
                    "(R1), I=no tile to slide in this direction (no-op "
                    "self-loop, R2), P=padding self-loop. Every real edge "
                    "of this model is generated by R1 (the slide) or is an "
                    "R2 unavailable-direction no-op; the 304 padding states "
                    "self-loop on all four actions (P)"),
                "values": tags,
            },
            "per_element_action_maps": per_elem,
            "transcription_notes": TRANSCRIPTION_NOTES,
            "regenerate": "python -X utf8 cases/sliding2x3/make_sliding2x3.py",
        },
        "trans": _TRANS,
    }


# ------------------------------------------------- expected verdict table
# Observed from a live three-way arbitration run
# (`python -X utf8 -m symmetry_court arbitrate --emit-expected-template`;
# receipt: verdicts/sliding2x3.verdict.json). The gate
# (`python -X utf8 -m symmetry_court selftest`) replays every case and
# compares these pinned rows field-by-field against a fresh run.
_RELABEL_NOTE = ("court-stamped relabel frame resolves to the bitstring "
                 "judge on this 4-action/10-bit model (n_actions <= n_bits), "
                 "which reads actions as bit flips -- a structural mismatch "
                 "for a direction-key system; diagnostic column, not "
                 "expected to flip")
_FIXED_NOTE_G2 = ("directions pinned (--strict): under this caliber the "
                  "mirror claim is genuinely false, so this row does not "
                  "flip; the group's explicit-caliber verdict (receipts/) "
                  "is the admitted reading")
_FIXED_NOTE_G3 = ("directions pinned (fixed declaration): the padding rows "
                  "are byte-identical and reference no direction, so the "
                  "pinned reading is the true reading for this control")

_EXPECTED_NOTE_EXPLICIT = ("the explicit declaration is adjudicated by the "
    "vendored engine directly (receipts/check.%s.json, engine run without "
    "--strict: pass, worst_tv 0.0, homomorphism_checked full) and by the "
    "compare subcommand's declared-caliber gate arm; the relabel column "
    "here resolves to the bitstring judge, which reads actions as bit "
    "flips on this 4-action/10-bit model -- a structural mismatch for a "
    "direction-key system (same shape as mini2048, contrast lightsout3 "
    "where 9 actions = 9 bits made the bitstring derivation coincide with "
    "the per-element button maps); the fixed column is the "
    "directions-pinned contrast")
_EXPECTED_NOTE_G2 = ("directions pinned: the mirror claim is genuinely false "
    "under this caliber (TV 1.0 -- the mirrored board answers the left "
    "slide with the right neighbor); the relabel column passes for no "
    "group on this model because the bitstring judge reads actions as bit "
    "flips -- the caliber, not the permutation, decides (same structure "
    "as mini2048's g1/g2 pair)")
_EXPECTED_NOTE_G3 = ("fixed-caliber positive control: the two padding rows "
    "are the same behavior shape (every action a single self-loop with "
    "reward 0) and reference "
    "no direction, so the pinned reading is the true reading; this case "
    "has 304 real padding states (unused lexicographic ranks), so the "
    "pads swap returns as the trivial control after lightsout3's "
    "no-padding case (see the group file's note)")

EXPECTED_ROWS = {
    "g1_hflip_map": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
        "note": _EXPECTED_NOTE_EXPLICIT % "g1_hflip_map",
    },
    "g2_hflip_nomap": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict", "note": _EXPECTED_NOTE_G2},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
    },
    "g3_pads": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                  "judge": "strict", "note": _EXPECTED_NOTE_G3},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": True},
    },
    "g4_v4_full": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
        "note": _EXPECTED_NOTE_EXPLICIT % "g4_v4_full",
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
        "case": "sliding2x3",
        "provenance": {
            "recorded": ("2026-11-04, observed from a live three-way "
                         "arbitration run "
                         "(`python -X utf8 -m symmetry_court arbitrate "
                         "--emit-expected-template`); the receipt is "
                         "verdicts/sliding2x3.verdict.json; the gate "
                         "(`python -X utf8 -m symmetry_court selftest`) "
                         "replays the case and compares these rows "
                         "field-by-field"),
            "reading_guide": ("relabel row = engine's relabel frame "
                              "(court-stamped copy; on this 4-action/10-bit "
                              "model that frame resolves to the bitstring "
                              "judge, which reads actions as bit flips -- a "
                              "structural mismatch for a direction-key "
                              "system, recorded as the diagnostic column); "
                              "fixed row = directions pinned (--strict); the "
                              "explicit declarations of g1/g4 are "
                              "adjudicated by the vendored engine directly "
                              "(receipts in receipts/) and by the compare "
                              "subcommand's declared-caliber gate arm; "
                              "networkx columns = independent juror (the "
                              "automorphism-set cross-check is skipped at "
                              "1024 states per the court's scale guard, the "
                              "O(E) direct edge-set check is the primary)"),
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
                         "--emit-expected-template --only sliding2x3`) and "
                         "paste the observed rows into EXPECTED_ROWS\n")
    else:
        ps["expected.json"] = _dump(build_expected())
    for name, g in build_groups(_SYM).items():
        ps["groups/" + name] = _dump(g)
    return ps


def self_certify(sym):
    """Author-side certification, re-run on every invocation:
    1. the V4 table: unique per-element maps (exhaustive over 4! = 24),
       homomorphism law, full-geometric-group check, fake controls (all
       asserted inside derive_symmetry_table, re-invoked here);
    2. the slide dynamics: deterministic single-successor rows, all-zero
       rewards, real states only reach real states, every real state has at
       least one slide edge, exactly 304 padding rows (all-action
       self-loops), reachable-from-goal = 360 (parity, rule R5);
    3. the declared group files: elements match the derived permutations
       and closures, declared action maps match the derived maps, and the
       engine's homomorphism convention holds on every declared pair;
    4. orbit counts (the compression readings the receipts should show):
       Burnside cross-checked (g1: (720+0)/2 + 304; g4: (720+0+0+0)/4 +
       304 -- no V4 element fixes a real configuration because distinct
       tiles cannot mirror onto each other).
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
            assert any(t != "I" for t in row_tags), ("dead real row", s)
            for a in range(N_ACTIONS):
                outs = trans[s][a]
                assert len(outs) == 1 and outs[0][0] == 1.0
                t, r, _tag = move(s, a)
                assert outs[0][1] == t and outs[0][2] == r
                assert r == 0.0                             # rule R4
                if row_tags[a] == "S":
                    assert t != s                           # a slide moves
                else:
                    assert row_tags[a] == "I" and t == s
    assert n_pad_rows == N_PADS
    assert reachable_from_goal() == N_REAL // 2 == 360
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
    # g1 elements == hflip closure; g2 identical to g1 (controlled contrast);
    # g3 = pads swap closure; g4 = V4 closure
    assert groups["g1_hflip_map.json"]["elements"] == \
        _closure([sym["hflip"]["state_perm"]])
    assert groups["g2_hflip_nomap.json"]["elements"] == \
        groups["g1_hflip_map.json"]["elements"]
    assert groups["g3_pads.json"]["elements"] == \
        _closure([_swap_states(PAD_A, PAD_B)])
    assert groups["g4_v4_full.json"]["elements"] == \
        _closure([sym["hflip"]["state_perm"],
                  sym["vflip"]["state_perm"]])
    assert len(groups["g4_v4_full.json"]["elements"]) == 4
    # per-element declared maps: exactly the derived rho of each element,
    # and the engine's homomorphism convention holds on every declared pair
    # ((g o h)[s] = g[h[s]]  =>  rho(g o h) == rho_g o rho_h)
    by_perm = {tuple(e["state_perm"]): list(e["action_map"])
               for e in sym.values()}
    for key in ("g1_hflip_map.json", "g4_v4_full.json"):
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
    # pads swap: the two swapped rows are the same behavior shape -- every
    # action a single self-loop with reward 0 (each looping to its own
    # index, which is exactly what makes the swap equivariant)
    a, b = PAD_A, PAD_B
    for a2 in range(N_ACTIONS):
        assert trans[a][a2] == [[1.0, a, 0.0]]
        assert trans[b][a2] == [[1.0, b, 0.0]]
    n_orbits = {"g1": orbits(groups["g1_hflip_map.json"]["elements"]),
                "g2": orbits(groups["g2_hflip_nomap.json"]["elements"]),
                "g3": orbits(groups["g3_pads.json"]["elements"]),
                "g4": orbits(groups["g4_v4_full.json"]["elements"])}
    # Burnside cross-check (no V4 element fixes a real configuration)
    assert n_orbits["g1"] == (N_REAL + 0) // 2 + N_PADS == 664
    assert n_orbits["g4"] == (N_REAL + 0 + 0 + 0) // 4 + N_PADS == 484
    assert n_orbits["g3"] == N_STATES - 1 == 1023
    assert n_orbits["g1"] == n_orbits["g2"]
    assert real_orbits(groups["g1_hflip_map.json"]["elements"]) == 360
    assert real_orbits(groups["g4_v4_full.json"]["elements"]) == 180
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
        "self-certification OK: 4/4 V4 elements have unique per-element "
        "direction maps (exhaustive over 4! = 24 permutations; homomorphism "
        "law verified over all 16 pairs; full geometric group of the 2x3 "
        "board machine-verified = V4 exactly; two fake transforms admit no "
        "map; pads fixed pointwise, real states reach only real states; "
        "reachable from goal = 360 = half of 720 (parity, Johnson & Story); "
        "all-state orbits g1=%d g2=%d g3=%d g4=%d (real-state orbits "
        "360/360/720/180)\n"
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

# -*- coding: utf-8 -*-
"""
make_lightsout3.py -- deterministic generator for the lightsout3 case: the
3x3 deterministic transcription of the Lights Out toggle mechanics (Tiger
Electronics handheld, 1995; rules public), built as the second docket for
the engine's *explicit* action caliber (state permutation + declared
per-element button renaming) and the second non-trivial positive control
(the full board group D4, admitted with per-element button maps).

Writes, byte-identical on every re-run (nothing random, no clock, no locale
dependence), next to this script:

  model.json                     the trans model: 512 states = 2^9 (9 lamps
                                 x 1 bit), 9 buttons, rewards all zero by
                                 design (the source game has no score; the
                                 win condition is recorded in meta)
  groups/g1_rot90_map.json       defendant A: 90-degree board rotation +
                                 renamed buttons (explicit+action_maps,
                                 per-element)
  groups/g2_rot90_nomap.json     defendant B: same rotation, buttons pinned
                                 (fixed) -- the naive-intuition claim
  groups/g3_complement.json      positive control: the all-lamps complement
                                 map (fixed, expected pass) -- see the
                                 deviation note below
  groups/g4_d4_full.json         main positive control: the full 8-element
                                 board group D4 (explicit+action_maps,
                                 per-element)
  groups/g5_d4_x_c2.json         the direct product D4 x C2 (16 elements,
                                 explicit+action_maps): the board group and
                                 the complement generate it because the
                                 complement commutes with every D4 element
  expected.json                  pinned verdict rows, observed live

Transcription authority (primary sources, public):
  - Wikipedia, "Lights Out (game)" (en.wikipedia.org/wiki/Lights_Out_(game)):
    "Pressing any of the lights will toggle it and the four adjacent lights."
    (Gameplay); "The goal of the puzzle is to switch all the lights off,
    preferably in as few button presses as possible." (Gameplay); Strategy:
    "the order in which the lights are pressed does not matter, as the result
    will be the same"; "pressing a light twice is equivalent to not pressing
    it at all".
  - Jaap's Puzzle Page, "Lights Out" (www.jaapsch.net/puzzles/lights.htm),
    the rules page Wikipedia itself cites for the game: "By pressing a
    button, its light and those of the (non-diagonally) adjacent buttons
    will change (switch on if it was off, and vice versa)."; "the order
    that the moves are performed is unimportant (i.e. the puzzle positions
    form an Abelian group)".

Variant boundaries (recorded, not hidden -- see TRANSCRIPTION_NOTES):
  1. 3x3 board: the Tiger original is 5x5 ("The game consists of a 5 by 5
     grid of lights"); the 3x3 board is the classic smaller variant of the
     same rules (Parker Brothers' Merlin ran similar rules on a 3 by 3 grid
     already in the 1970s, and the Lights Out Cube plays on six 3x3 faces;
     Jaap's page documents the reissued Merlin as "exactly the same as the
     standard Lights Out ... a 3x3 Lights out"). Every rule sentence cited
     here is size-independent except the grid size itself, which is recorded
     as a variant boundary (rule R7).
  2. Initial-board randomization ("a random number or a stored pattern of
     these lights is switched on") is NOT collected: the model is the full
     512-state transition system, initial setup is outside the deterministic
     FSM semantics (same discipline as mini2048's random-spawn rule).
  3. No score: the game has no numeric payoff, so the reward layer is all
     zero by design and the win condition (all lamps off) is recorded in
     meta.win_condition as a terminal property, not a per-edge reward (same
     all-zero convention as tcp/dhcp/imap).

The explicit caliber and this case: a board symmetry moves the buttons with
the cells (rotating the board clockwise turns the top-left button into the
top-right button). Per group element pi the button renaming rho(pi) is
forced, and pi |-> rho(pi) is a group homomorphism. Since 2026-11-04 the
engine's group format accepts semantics.action_maps: one action renaming
(bijection) per group element, parallel to elements, homomorphism-law
checked at load -- each explicit group file here declares the per-element
maps of its own elements (exhaustively derived and asserted by this
generator on every run); model.meta.per_element_action_maps holds the full
derivation table.

Why there is no padding-state swap here (deviation note, ruled 2026-11-04
during case engineering: faithful transcription outranks control-form
symmetry): on the 3x3 board the 9x9 toggle matrix over GF(2) has rank 9
(asserted by this generator on every run), so EVERY one of the 512
configurations is reachable from the all-off state, every state has 9
distinct active successors, and no two states share a row -- there are no
padding states and no self-loops, so the pads swap that serves as
mini2048's trivial positive control cannot be transcribed here. The trivial
positive control role is played instead by the ALL-LAMPS COMPLEMENT map
pi(s) = 511 XOR s: because toggling is XOR, complementing the whole board
commutes with every button press and keeps every button name, so it is a
genuine symmetry under the fixed caliber (buttons pinned) -- admitted as
g3_complement, and it commutes with every D4 element (asserted), so the
board group and the complement together generate the direct product
D4 x C2 (order 16), filed as g5_d4_x_c2.

Usage:
  python -X utf8 cases/lightsout3/make_lightsout3.py            # write all files
  python -X utf8 cases/lightsout3/make_lightsout3.py --out DIR  # write into DIR
  python -X utf8 cases/lightsout3/make_lightsout3.py --check    # verify bytes +
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
# Lamp/button index i = 3*row + col on a 3x3 grid, (x, y) = (column, row),
# x rightward, y downward: 0=top-left, 1=top-center, 2=top-right,
# 3=middle-left, 4=center, 5=middle-right, 6=bottom-left, 7=bottom-center,
# 8=bottom-right. State bit i = lamp i (1=on, 0=off) -> 2^9 = 512 states.
CELL_XY = [(x, y) for y in range(3) for x in range(3)]   # index -> (x, y)
XY_CELL = {xy: i for i, xy in enumerate(CELL_XY)}
N_CELLS = 9
N_BITS = 9
N_STATES = 1 << N_BITS                                   # 512
N_ACTIONS = 9

# Actions = the nine board buttons, indexed by the same row-major scheme as
# the lamps (button a sits on lamp a -- action indices are positional data).
ACTION_NAMES = ["top-left", "top-center", "top-right",
                "middle-left", "center", "middle-right",
                "bottom-left", "bottom-center", "bottom-right"]

WIKI = 'Wikipedia "Lights Out (game)", '
JAAP = 'Jaap\'s Puzzle Page "Lights Out" (www.jaapsch.net/puzzles/lights.htm), '

RULES = [
    {"id": "R1-toggle-cross",
     "rule": ("pressing a button toggles it and its orthogonal "
              "(non-diagonal) neighbors; on the 3x3 board a corner button "
              "toggles 3 lamps, an edge button 4, the center button 5 -- "
              "the toggle set is always the button itself plus its in-grid "
              "orthogonal neighbors (out-of-grid neighbors are ignored)"),
     "citation": (WIKI + "Gameplay: 'Pressing any of the lights will toggle "
                  "it and the four adjacent lights.' (the 5x5 wording; on "
                  "the 3x3 board the four adjacent DIRECTIONS shrink to the "
                  "in-grid ones); " + JAAP + "'By pressing a button, its "
                  "light and those of the (non-diagonally) adjacent buttons "
                  "will change (switch on if it was off, and vice versa).'")},
    {"id": "R2-win-all-off",
     "rule": ("the goal of the puzzle is to switch all the lights off; the "
              "all-off configuration (state 0) is the win condition"),
     "citation": (WIKI + "Gameplay: 'The goal of the puzzle is to switch "
                  "all the lights off, preferably in as few button presses "
                  "as possible.'; " + JAAP + "'Given a pattern of lights, "
                  "you have to switch them all off by pressing the correct "
                  "buttons.'")},
    {"id": "R3-order-invariance",
     "rule": ("the order in which buttons are pressed does not matter -- the "
              "resulting configuration depends only on WHICH buttons were "
              "pressed an odd number of times"),
     "citation": (WIKI + "Strategy: 'the order in which the lights are "
                  "pressed does not matter, as the result will be the "
                  "same'; " + JAAP + "'the order that the moves are "
                  "performed is unimportant (i.e. the puzzle positions form "
                  "an Abelian group)'")},
    {"id": "R4-double-press-idempotent",
     "rule": ("pressing the same button twice returns to the previous "
              "configuration, so no button ever needs to be pressed more "
              "than once (toggle algebra over GF(2))"),
     "citation": (WIKI + "Strategy: 'pressing a light twice is equivalent "
                  "to not pressing it at all'; " + JAAP + "'Since pressing "
                  "a button twice will not change anything, a button need "
                  "only be pressed at most once.'")},
    {"id": "R5-initial-randomness-not-collected",
     "rule": ("NOT COLLECTED: the starting board is set to a random pattern "
              "or a stored pattern; the model here is the full 512-state "
              "transition system and the initial setup is outside the "
              "deterministic FSM semantics"),
     "citation": (WIKI + "Gameplay: 'When the game starts, a random number "
                  "or a stored pattern of these lights is switched on.' -- "
                  "randomness is outside the deterministic FSM semantics; "
                  "recorded, not repaired")},
    {"id": "R6-no-score",
     "rule": ("the game has no score; 'as few button presses as possible' "
              "is advice about solutions, not a numeric payoff, so the "
              "reward layer is all zero by design"),
     "citation": (WIKI + "Gameplay: 'preferably in as few button presses as "
                  "possible' -- recorded, not turned into a reward; same "
                  "all-zero reward convention as the tcp/dhcp/imap cases")},
    {"id": "R7-board-3x3-VARIANT",
     "rule": ("VARIANT BOUNDARY: this case is the 3x3 board; the Tiger "
              "Electronics original is 5x5"),
     "citation": (WIKI + "'Lights Out is an electronic game released by "
                  "Tiger Electronics in 1995.'; 'The game consists of a 5 "
                  "by 5 grid of lights.'; the 3x3 board is the classic "
                  "smaller variant of the same rules: 'Merlin, a similar "
                  "electronic game, was released by Parker Brothers in the "
                  "1970s with similar rules on a 3 by 3 grid'; 'Lights Out "
                  "Cube (six 3x3 faces with effects across edges)'; "
                  + JAAP + "on the reissued Merlin: 'They are now exactly "
                  "the same as the standard Lights Out, i.e. each button "
                  "press changes its own light as well as the orthogonally "
                  "adjacent ones. It has simply become a 3x3 Lights out.'")},
    {"id": "R8-deterministic",
     "rule": ("play itself is deterministic: a press always toggles its "
              "cross exactly, with no randomness (the initial-board "
              "randomization of R5 is the only stochastic step, and it is "
              "not collected)"),
     "citation": ("consequence of R1 as stated by " + WIKI + "and " + JAAP +
                  " (a press changes exactly its cross; nothing else "
                  "happens)")},
]

TRANSCRIPTION_NOTES = [
    "scope: 3x3 board, 9 two-state lamps, 9 buttons; the deterministic "
    "toggle core of Lights Out (rule R1) with the initial-board "
    "randomization NOT collected (rule R5) -- randomness is not part of the "
    "deterministic FSM semantics, per the court's not-collected discipline "
    "(same pattern as mini2048's random-spawn rule).",
    "VARIANT BOUNDARY (rule R7): the 3x3 board; the Tiger original is 5x5. "
    "Every cited rule sentence is size-independent except the grid size; "
    "the 3x3 lineage runs through Merlin's reissued Magic Square ('exactly "
    "the same as the standard Lights Out ... a 3x3 Lights out', Jaap's "
    "page) and the Lights Out Cube's 3x3 faces.",
    "actions: the nine buttons indexed by board position 0..8 row-major "
    "(button a sits on lamp a) -- action indices are positional data, not a "
    "court choice.",
    "encoding: state = 9 bits = 9 lamps; bit i = lamp i, 1=on, 0=off. ALL "
    "512 bit patterns are valid configurations.",
    "no padding states: the 9x9 toggle matrix over GF(2) has rank 9 "
    "(asserted by this generator on every run), so every configuration is "
    "reachable from the all-off state; every state has 9 distinct active "
    "successors (zero self-loops: each toggle mask contains its own button "
    "bit) and no two states share a row. Contrast mini2048, where 175 of "
    "256 states are padding. Consequence: the trivial positive control "
    "here is NOT a padding swap -- see the complement note below.",
    "rewards: all zero by design (rule R6) -- the source game has no "
    "score; the win condition (all lamps off, state 0) is recorded in "
    "meta.win_condition as a terminal property and the device does not "
    "lock on winning, so state 0 is an ordinary state of the transition "
    "system. The adjudication therefore runs entirely on the transition "
    "layer (same all-zero convention as tcp/dhcp/imap).",
    "explicit caliber note: a board symmetry moves the buttons with the "
    "cells (rotating the board clockwise turns the top-left button into "
    "the top-right button); rho(identity)=id while rho(rot90)!=id, so no "
    "single action_map can serve a whole closed group. Since 2026-11-04 "
    "the engine's group format accepts semantics.action_maps (one "
    "bijection per element, parallel to elements, homomorphism-law checked "
    "at load); each explicit group file here declares the per-element maps "
    "of its own elements, and meta.per_element_action_maps holds the full "
    "derivation (exhaustively derived over all 9! = 362880 button "
    "permutations, unique per element, asserted on every run).",
    "complement positive control (deviation note, ruled 2026-11-04 during "
    "case engineering: faithful transcription outranks control-form "
    "symmetry): because toggling is XOR, complementing the whole board "
    "(pi(s) = 511 XOR s) commutes with every button press and keeps every "
    "button name, so it is a genuine symmetry under the fixed caliber; it "
    "plays the role mini2048's padding swap plays there (this case has no "
    "padding states to swap). Filed as g3_complement.",
    "structural observation (machine-asserted on every run): the complement "
    "map commutes with every element of the board group D4, so the group "
    "generated by the two is the direct product D4 x C2 of order 16 -- "
    "filed as g5_d4_x_c2. Geometric symmetry and toggle-algebra symmetry "
    "are independent here and their product is a symmetry; the model's "
    "full automorphism inventory is larger still and is NOT claimed by any "
    "group file (every group here is derived, closed, and machine-"
    "asserted; no group file claims to be the full automorphism group).",
    "regenerate: python -X utf8 cases/lightsout3/make_lightsout3.py",
]

# ---------------------------------------------------------------- toggle rule
def toggle_mask(a):
    """Button a toggles lamp a and its in-grid orthogonal neighbors (R1)."""
    x, y = CELL_XY[a]
    m = 0
    for (xx, yy) in ((x, y), (x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)):
        if 0 <= xx < 3 and 0 <= yy < 3:
            m |= 1 << XY_CELL[(xx, yy)]
    return m


MASKS = [toggle_mask(a) for a in range(N_ACTIONS)]
MASK_CELLS = [[i for i in range(N_CELLS) if MASKS[a] >> i & 1]
              for a in range(N_ACTIONS)]


def press(s, a):
    """Deterministic Lights Out press -> (successor state, reward, tag)."""
    return s ^ MASKS[a], 0.0, "T"


def build_trans():
    """512 x 9 deterministic rows + the per-edge rule-tag table (all T)."""
    trans = []
    tags = []
    for s in range(N_STATES):
        row = []
        for a in range(N_ACTIONS):
            t, r, _tag = press(s, a)
            row.append([[1.0, t, r]])
        trans.append(row)
        tags.append("T" * N_ACTIONS)
    return trans, tags


# ---------------------------------------------------------------- GF(2) rank
def toggle_matrix_rank():
    """Rank over GF(2) of the 9x9 matrix whose rows are the toggle masks."""
    rows = list(MASKS)
    rank = 0
    for bit in range(N_BITS - 1, -1, -1):
        piv = None
        for i in range(rank, len(rows)):
            if rows[i] >> bit & 1:
                piv = i
                break
        if piv is None:
            continue
        rows[rank], rows[piv] = rows[piv], rows[rank]
        for i in range(len(rows)):
            if i != rank and (rows[i] >> bit & 1):
                rows[i] ^= rows[rank]
        rank += 1
    return rank


# ---------------------------------------------------------------- symmetries
def cell_map_of(fn):
    """(x,y)->(x',y') board transform -> content map d: content of cell c
    moves to cell d[c]."""
    d = []
    for (x, y) in CELL_XY:
        d.append(XY_CELL[fn(x, y)])
    return d


def state_perm_of(d):
    """Content map d -> state permutation pi: pi(s)[d[c]] = s[c]."""
    pi = []
    for s in range(N_STATES):
        t = 0
        for c in range(N_CELLS):
            if s >> c & 1:
                t |= 1 << d[c]
        pi.append(t)
    return pi


def compose_d(d2, d1):
    """Content maps: apply d1, then d2 on top."""
    return [d2[d1[c]] for c in range(N_CELLS)]


# The eight board symmetries as (x, y) transforms (D4 on the 3x3 grid).
D4_TRANSFORMS = [
    ("id",         lambda x, y: (x, y)),
    ("rot90cw",    lambda x, y: (2 - y, x)),
    ("rot180",     lambda x, y: (2 - x, 2 - y)),
    ("rot90ccw",   lambda x, y: (y, 2 - x)),
    ("flip_tb",    lambda x, y: (x, 2 - y)),   # top-bottom mirror
    ("flip_lr",    lambda x, y: (2 - x, y)),   # left-right mirror
    ("transpose",  lambda x, y: (y, x)),
    ("antitrans",  lambda x, y: (2 - y, 2 - x)),
]


def complement_perm():
    """The all-lamps complement map pi(s) = 511 XOR s (an XOR-translation,
    not a content-map permutation): it commutes with every button press."""
    return [s ^ (N_STATES - 1) for s in range(N_STATES)]


_MAP_CACHE = {}


def derive_action_map(pi):
    """Exhaustive search over ALL 9! = 362880 button permutations for rho
    with, for ALL states s and actions a:
        press(pi(s), rho[a]) == pi(press(s, a))          (transition layer)
        reward(pi(s), rho[a]) == reward(press(s, a))     (trivially true:
                                                          rewards all zero,
                                                          checked separately)
    Returns the list of valid rhos (asserted by callers to have length
    exactly 1, or 0 for non-symmetries). Memoized per permutation. This is
    the author-side derivation of the per-element button renaming; the
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
                if (ps ^ MASKS[rho[a]]) != pi[s ^ MASKS[a]]:
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


# ---------------------------------------------------------------- derivation
def derive_symmetry_table():
    """Per-element button maps for the whole D4 + the complement + the
    homomorphism and commutation checks.

    Returns dict name -> {"content_map": d|None, "state_perm": pi,
    "action_map": rho, "kind": "board"|"xor-translation"}.
    Asserts (loud, on every run):
      1. the nine toggle masks are pairwise distinct and each contains its
         own button bit (uniqueness support: any valid rho must satisfy
         rho(a) = the button whose mask is pi(m_a) XOR pi(0), determined
         pointwise by the s=0 equations -- with distinct masks at most one
         rho exists; the exhaustive search then confirms existence);
      2. the toggle matrix over GF(2) has rank 9 (no padding states);
      3. every D4 element has exactly one rho (exhaustive over 9!);
      4. rho(id) = id and rho(rot90cw) != id (non-triviality);
      5. the homomorphism law rho(d2 o d1) == rho(d2) o rho(d1) for all 64
         ordered pairs;
      6. the complement has exactly one rho and it is the identity (buttons
         keep their names), and it commutes with every D4 element;
      7. the top-row-only mirror (a structural mirror that is not a board
         symmetry) admits NO rho at all.
    """
    # 1. masks pairwise distinct, self-containing
    assert all(MASKS[a] >> a & 1 for a in range(N_ACTIONS))
    assert len(set(MASKS)) == N_ACTIONS, "toggle masks not distinct"
    # 2. rank 9 -> no padding states
    assert toggle_matrix_rank() == N_BITS, "toggle matrix rank < 9"

    table = {}
    for name, fn in D4_TRANSFORMS:
        d = cell_map_of(fn)
        pi = state_perm_of(d)
        table[name] = {"content_map": d, "state_perm": pi,
                       "action_map": derive_unique_map(pi),
                       "kind": "board"}
    # 4. identity / non-triviality
    assert table["id"]["action_map"] == list(range(N_ACTIONS))
    assert table["rot90cw"]["action_map"] != list(range(N_ACTIONS))
    # 5. homomorphism: rho(d2 o d1) == rho(d2) o rho(d1)   (apply d1 then d2)
    for (n1, f1) in D4_TRANSFORMS:
        for (n2, f2) in D4_TRANSFORMS:
            comp = compose_d(table[n2]["content_map"], table[n1]["content_map"])
            assert comp == cell_map_of(lambda x, y, f1=f1, f2=f2: f2(*f1(x, y))), \
                (n1, n2)
            want = compose_maps(table[n2]["action_map"], table[n1]["action_map"])
            got = derive_unique_map(state_perm_of(comp))
            assert got == want, ("homomorphism broken", n1, n2, got, want)
    # 6. complement: unique rho = identity; commutes with every D4 element
    cpi = complement_perm()
    table["complement"] = {"content_map": None, "state_perm": cpi,
                           "action_map": derive_unique_map(cpi),
                           "kind": "xor-translation"}
    assert table["complement"]["action_map"] == list(range(N_ACTIONS))
    ident = list(range(N_STATES))
    for name, _fn in D4_TRANSFORMS:
        pd = table[name]["state_perm"]
        assert [cpi[pd[s]] for s in range(N_STATES)] == \
               [pd[cpi[s]] for s in range(N_STATES)], \
               ("complement does not commute with", name)
        assert pd != cpi, ("complement inside D4", name)
    # 7. the top-row-only mirror admits no renaming at all
    fake_d = [1, 0] + list(range(2, N_CELLS))   # swap cells 0<->1 only
    derive_unique_map(state_perm_of(fake_d), expect=False)
    return table


def _full_map_table(sym):
    """perm(tuple) -> action map, covering the D4 elements, the complement,
    AND the product elements complement o pi_d (whose map is rho(d): by the
    homomorphism law rho(c o d) = rho(c) o rho(d) = id o rho(d), since the
    complement's map is the identity). Used by the group builder and the
    self-certification alike."""
    by_perm = {}
    cpi = sym["complement"]["state_perm"]
    for name, entry in sym.items():
        by_perm[tuple(entry["state_perm"])] = list(entry["action_map"])
        if entry["kind"] == "board":
            prod = tuple(cpi[s] for s in entry["state_perm"])
            assert prod not in by_perm or \
                by_perm[prod] == list(entry["action_map"])
            by_perm[prod] = list(entry["action_map"])
    return by_perm


def _per_element_action_maps(sym, elements):
    """Closed-group elements (state permutations, file order) -> the list of
    per-element action maps parallel to elements, looked up from the full
    table (D4 x C2). Raises (loud) on any element outside the table. This
    is the list the group files declare as semantics.action_maps; the
    identity element necessarily maps to the identity renaming."""
    by_perm = _full_map_table(sym)
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
def build_groups(sym):
    rot_pi = sym["rot90cw"]["state_perm"]
    flip_pi = sym["flip_tb"]["state_perm"]
    comp_pi = sym["complement"]["state_perm"]
    g1 = _closure([rot_pi])
    assert len(g1) == 4
    d4 = _closure([rot_pi, flip_pi])
    assert len(d4) == 8
    g3 = _closure([comp_pi])
    assert len(g3) == 2
    g5 = _closure([rot_pi, flip_pi, comp_pi])
    assert len(g5) == 16
    # g2 is the controlled contrast to g1: identical elements, fixed caliber
    regen = "python -X utf8 cases/lightsout3/make_lightsout3.py"

    return {
        "g1_rot90_map.json": {
            "n_states": N_STATES,
            "elements": g1,
            "semantics": {"action": "explicit",
                          "action_maps": _per_element_action_maps(sym, g1)},
            "meta": {
                "claim": ("defendant A: rotating the 3x3 board 90 degrees "
                          "clockwise and moving the buttons with it (the "
                          "top-left button becomes the top-right button, "
                          "and so on around the rotation) preserves the "
                          "puzzle exactly -- buttons are bound to board "
                          "positions, so the true symmetry carries its own "
                          "button renaming; declared under the explicit "
                          "caliber with per-element action maps"),
                "construction": ("order-4 cyclic group {id, rot90cw, rot180, "
                                 "rot90ccw} as state permutations; "
                                 "semantics.action_maps = the per-element "
                                 "derived renamings, one bijection per "
                                 "element, parallel to elements "
                                 "(meta.per_element_action_maps holds the "
                                 "full derivation table; rho(identity)=id; "
                                 "the homomorphism law is asserted by this "
                                 "generator and re-checked by the engine at "
                                 "load)"),
                "why_it_is_a_symmetry": ("the toggle rule is defined through "
                                         "the same cross shape (rule R1) at "
                                         "every button; rotating the board "
                                         "and renaming the buttons commutes "
                                         "with every press on every one of "
                                         "the 512 states (asserted "
                                         "exhaustively by the generator "
                                         "over all 9! button permutations, "
                                         "exactly one valid map per "
                                         "element)"),
                "caliber_note": ("explicit declaration: the button names are "
                                 "bound to board positions ('the button at "
                                 "the top-left corner'), so they travel "
                                 "with the rotation"),
                "regenerate": regen,
            },
        },
        "g2_rot90_nomap.json": {
            "n_states": N_STATES,
            "elements": g1,
            "semantics": {"action": "fixed"},
            "meta": {
                "claim": ("defendant B: the same 90-degree rotation with the "
                          "buttons PINNED (the top-left button must stay the "
                          "top-left button) -- the naive-intuition claim "
                          "that 'the board looks the same rotated', filed "
                          "deliberately under the fixed caliber to show it "
                          "is the button renaming, not the state "
                          "permutation, that makes defendant A true"),
                "construction": ("identical elements to g1_rot90_map "
                                 "(order-4 rotation group); semantics "
                                 "declared fixed"),
                "why_it_is_not_a_symmetry": ("with the buttons pinned, the "
                                             "top-left button on the rotated "
                                             "board toggles a different "
                                             "cross than the top-left "
                                             "button on the original; the "
                                             "deterministic successors "
                                             "differ (TV 1.0 on every "
                                             "state, e.g. the all-off "
                                             "state: pressing the top-left "
                                             "button lights lamps {0,1,3} "
                                             "in the original but lamps "
                                             "{1,2,5} in the rotated "
                                             "reading)"),
                "caliber_note": ("fixed declaration: this defendant is the "
                                 "controlled contrast to g1 -- same "
                                 "permutation, opposite action caliber"),
                "regenerate": regen,
            },
        },
        "g3_complement.json": {
            "n_states": N_STATES,
            "elements": g3,
            "semantics": {"action": "fixed"},
            "meta": {
                "claim": ("positive control: the all-lamps complement map "
                          "pi(s) = 511 XOR s (every lamp flipped) commutes "
                          "with every button press because toggling is XOR, "
                          "so it is a genuine symmetry under the pinned-"
                          "button reading and should be admitted"),
                "construction": ("order-2 group {id, complement}; semantics "
                                 "declared fixed -- the complement is an "
                                 "XOR-translation of the lamp vector, not a "
                                 "board permutation, and keeps every button "
                                 "name (rho = identity)"),
                "why_it_is_a_symmetry": ("press(pi(s), a) = pi(s) XOR m_a = "
                                         "pi(s XOR m_a) = pi(press(s, a)) "
                                         "for every state and button "
                                         "(asserted exhaustively); rewards "
                                         "are all zero, so the reward layer "
                                         "is preserved trivially"),
                "caliber_note": ("deviation note (ruled 2026-11-04 during "
                                 "case engineering: faithful transcription "
                                 "outranks control-form symmetry): the "
                                 "trivial positive control here is NOT a "
                                 "padding-state swap -- this case HAS no "
                                 "padding states (toggle-matrix rank 9: "
                                 "all 512 configurations reachable, zero "
                                 "self-loops, all rows distinct, see "
                                 "model.meta.transcription_notes). The "
                                 "complement map plays the same role "
                                 "mini2048's pads swap plays there: an "
                                 "admitted fixed-caliber symmetry that "
                                 "isolates caliber questions from model "
                                 "well-formedness"),
                "regenerate": regen,
            },
        },
        "g4_d4_full.json": {
            "n_states": N_STATES,
            "elements": d4,
            "semantics": {"action": "explicit",
                          "action_maps": _per_element_action_maps(sym, d4)},
            "meta": {
                "claim": ("main positive control: the FULL 8-element board "
                          "symmetry group D4 (identity, three rotations, "
                          "four reflections), each element carrying its own "
                          "button renaming -- the second non-trivial "
                          "positive control of this court, after mini2048's "
                          "D4 and on a different mechanism (toggle algebra "
                          "instead of merge-and-slide)"),
                "construction": ("closure of {rot90cw, flip_tb} = 8 "
                                 "elements; semantics.action_maps = the "
                                 "per-element derived renamings, one "
                                 "bijection per element, parallel to "
                                 "elements (all eight maps exhaustively "
                                 "derived over the 9! button permutations "
                                 "and asserted in "
                                 "meta.per_element_action_maps; "
                                 "rho(identity)=id; homomorphism law "
                                 "asserted by this generator and re-checked "
                                 "by the engine at load)"),
                "why_it_is_a_symmetry": ("D4 is the square's own symmetry "
                                         "group and the toggle rule is "
                                         "direction-symmetric by "
                                         "construction (one cross rule, "
                                         "nine buttons)"),
                "caliber_note": ("admitted under the explicit caliber with "
                                 "per-element action_maps; compression "
                                 "reading: orbits of D4 on the 512 "
                                 "configurations (Burnside: 102 = "
                                 "(512+8+32+8+4x64)/8), live count in "
                                 "receipts/check.g4_d4_full.json"),
                "regenerate": regen,
            },
        },
        "g5_d4_x_c2.json": {
            "n_states": N_STATES,
            "elements": g5,
            "semantics": {"action": "explicit",
                          "action_maps": _per_element_action_maps(sym, g5)},
            "meta": {
                "claim": ("the direct product D4 x C2 (order 16): the board "
                          "group and the all-lamps complement generate it "
                          "because the complement commutes with every D4 "
                          "element (asserted by the generator); each "
                          "element (d, c^k) carries the button renaming of "
                          "its D4 partner d -- the complement itself "
                          "renames nothing"),
                "construction": ("closure of {rot90cw, flip_tb, complement} "
                                 "= 16 elements = D4 x C2; "
                                 "semantics.action_maps parallel to "
                                 "elements (rho(d, c^k) = rho(d), consistent "
                                 "with the homomorphism law because "
                                 "rho(complement)=id)"),
                "why_it_is_a_symmetry": ("geometric symmetry (D4) and "
                                         "toggle-algebra symmetry (the "
                                         "complement) are independent here "
                                         "and commute, so their product is "
                                         "a symmetry (asserted exhaustively "
                                         "per element)"),
                "caliber_note": ("admitted under the explicit caliber with "
                                 "per-element action_maps; the complement "
                                 "factor contributes no orbits on top of "
                                 "D4 x {complement-paired orbits}: the "
                                 "orbit count is the D4 orbit count halved "
                                 "when no D4 orbit is self-complementary "
                                 "(live count in "
                                 "receipts/check.g5_d4_x_c2.json)"),
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
            "kind": sym[name]["kind"],
        }
    return {
        "n_bits": N_BITS,
        "n_actions": N_ACTIONS,
        "n_states": N_STATES,
        "goals": [],
        "meta": {
            "source_system": (
                "Lights Out puzzle (Tiger Electronics handheld, 1995; "
                "toggle rule and all-off goal, rules public), transcribed "
                "as the 3x3 deterministic variant: 9 toggle buttons, no "
                "randomness collected, no score"),
            "variant": "lightsout3-3x3-deterministic",
            "source_citation": (
                'Wikipedia "Lights Out (game)" '
                "(en.wikipedia.org/wiki/Lights_Out_(game)): Gameplay "
                "('Pressing any of the lights will toggle it and the four "
                "adjacent lights.'; 'The goal of the puzzle is to switch "
                "all the lights off, preferably in as few button presses as "
                "possible.'), Strategy ('the order in which the lights are "
                "pressed does not matter, as the result will be the same'; "
                "'pressing a light twice is equivalent to not pressing it "
                "at all'); Jaap's Puzzle Page \"Lights Out\" "
                "(www.jaapsch.net/puzzles/lights.htm), the rules page "
                "Wikipedia cites for the game: 'By pressing a button, its "
                "light and those of the (non-diagonally) adjacent buttons "
                "will change (switch on if it was off, and vice versa).'; "
                "board-size variant boundary: Wikipedia ('The game consists "
                "of a 5 by 5 grid of lights'; Merlin 'with similar rules on "
                "a 3 by 3 grid'; 'Lights Out Cube (six 3x3 faces with "
                "effects across edges)'). Per-rule citations in "
                "meta.rules_with_citations; per-edge generating rules in "
                "meta.edge_rule_tags; the nine toggle masks in "
                "meta.toggle_masks."),
            "state_names": None,
            "action_names": ACTION_NAMES,
            "state_encoding": (
                "state = 9 bits = 9 lamps; lamp i = 3*row + col (row, col "
                "counted from the top-left), bit i = lamp i with 1=on, "
                "0=off; ALL 512 bit patterns are valid configurations "
                "(no padding states -- toggle-matrix rank 9, see "
                "meta.toggle_matrix_rank)"),
            "real_states_count": 512,
            "padding_states_count": 0,
            "toggle_matrix_rank": 9,
            "semantics_class": (
                "position-button: the nine actions are the nine board "
                "buttons at fixed positions; a board symmetry moves buttons "
                "with the cells, so true board symmetries are "
                "explicit-caliber claims with per-element button renamings; "
                "the fixed reading (buttons pinned) is the naive contrast. "
                "XOR-translations of the lamp vector (e.g. the all-lamps "
                "complement) keep every button name and hold under the "
                "fixed caliber"),
            "reward_rule": (
                "all zero by design: the source game has no score (see "
                "meta.rules_with_citations R6); the win condition is "
                "recorded in meta.win_condition, not as a per-edge reward "
                "(same all-zero convention as tcp/dhcp/imap)"),
            "win_condition": (
                "all nine lamps off (state 0) -- 'The goal of the puzzle is "
                "to switch all the lights off' (Wikipedia Gameplay); the "
                "device does not lock on winning, so state 0 is an ordinary "
                "state of the transition system and goals=[] in this model"),
            "rules_with_citations": RULES,
            "toggle_masks": {
                "layout": (
                    "toggle_masks.masks[a] = the bit mask (int) of the "
                    "lamps that button a toggles (bit i = lamp i); "
                    "toggle_masks.cells[a] = the same masks as cell-index "
                    "lists; button a always toggles lamp a itself (rule "
                    "R1)"),
                "masks": MASKS,
                "cells": MASK_CELLS,
            },
            "edge_rule_tags": {
                "layout": (
                    "edge_rule_tags.values[s] is a 9-character string, "
                    "character a = the generating rule of edge (s, action "
                    "a); T = the toggle rule R1. Every edge of this model "
                    "is generated by R1 (the toggle cross), so every "
                    "character is T; there are no padding self-loops and "
                    "no other generating rules"),
                "values": tags,
            },
            "per_element_action_maps": per_elem,
            "transcription_notes": TRANSCRIPTION_NOTES,
            "regenerate": "python -X utf8 cases/lightsout3/make_lightsout3.py",
        },
        "trans": _TRANS,
    }


# ------------------------------------------------- expected verdict table
# Observed from a live three-way arbitration run
# (`python -X utf8 -m symmetry_court arbitrate --emit-expected-template`;
# receipt: verdicts/lightsout3.verdict.json). The gate
# (`python -X utf8 -m symmetry_court selftest`) replays every case and
# compares these pinned rows field-by-field against a fresh run.
_RELABEL_NOTE = ("court-stamped relabel frame resolves to the bitstring "
                 "judge on this 9-action/9-bit model (n_actions <= n_bits), "
                 "which reads actions as bit flips -- a structural mismatch "
                 "for a position-button system; diagnostic column, not "
                 "expected to flip")
_FIXED_NOTE_G2 = ("buttons pinned (--strict): under this caliber the "
                  "rotation claim is genuinely false, so this row does not "
                  "flip; the group's explicit-caliber verdict (receipts/) "
                  "is the admitted reading")
_FIXED_NOTE_G3 = ("buttons pinned (fixed declaration): the complement "
                  "commutes with every press and renames nothing, so the "
                  "pinned reading is the true reading for this control")

_EXPECTED_NOTE_EXPLICIT = ("the explicit declaration is adjudicated by the "
    "vendored engine directly (receipts/check.%s.json, engine run without "
    "--strict: pass, worst_tv 0.0, homomorphism_checked full) and by the "
    "compare subcommand's declared-caliber gate arm; the relabel column "
    "here resolves to the bitstring judge, which on this 9-action/9-bit "
    "model derives the action renaming from the state permutation itself "
    "(buttons are bit positions), so the relabel column passes in step "
    "with the explicit reading (contrast mini2048, where 4 actions on 8 "
    "bits made the same frame a structural mismatch); the fixed column is "
    "the buttons-pinned contrast")
_EXPECTED_NOTE_G2 = ("buttons pinned: the rotation claim is genuinely false "
    "under this caliber (TV 1.0 -- e.g. the all-off state: the top-left "
    "button lights lamps {0,1,3} in the original but {1,2,5} in the "
    "rotated reading); the relabel column passes because the bitstring "
    "judge derives the action renaming from the permutation itself -- the "
    "caliber, not the permutation, decides (same structure as mini2048's "
    "g1/g2 pair)")
_EXPECTED_NOTE_G3 = ("fixed-caliber positive control: the complement "
    "commutes with every press and renames nothing, so the pinned reading "
    "is the true reading; this case has no padding states (toggle-matrix "
    "rank 9), so the trivial control is the complement map rather than a "
    "padding swap (see the group file's deviation note)")

EXPECTED_ROWS = {
    "g1_rot90_map": {
        "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
        "note": _EXPECTED_NOTE_EXPLICIT % "g1_rot90_map",
    },
    "g2_rot90_nomap": {
        "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict", "note": _EXPECTED_NOTE_G2},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
    },
    "g3_complement": {
        "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                  "judge": "strict", "note": _EXPECTED_NOTE_G3},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": True},
    },
    "g4_d4_full": {
        "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
        "note": _EXPECTED_NOTE_EXPLICIT % "g4_d4_full",
    },
    "g5_d4_x_c2": {
        "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
        "note": _EXPECTED_NOTE_EXPLICIT % "g5_d4_x_c2",
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
        "case": "lightsout3",
        "provenance": {
            "recorded": ("2026-11-04, observed from a live three-way "
                         "arbitration run "
                         "(`python -X utf8 -m symmetry_court arbitrate "
                         "--emit-expected-template`); the receipt is "
                         "verdicts/lightsout3.verdict.json; the gate "
                         "(`python -X utf8 -m symmetry_court selftest`) "
                         "replays the case and compares these rows "
                         "field-by-field"),
            "reading_guide": ("relabel row = engine's relabel frame "
                              "(court-stamped copy; on this 9-action/9-bit "
                              "model that frame resolves to the bitstring "
                              "judge, which reads actions as bit flips -- a "
                              "structural mismatch for a position-button "
                              "system, recorded as the diagnostic column); "
                              "fixed row = buttons pinned (--strict); the "
                              "explicit declarations of g1/g4/g5 are "
                              "adjudicated by the vendored engine directly "
                              "(receipts in receipts/) and by the compare "
                              "subcommand's declared-caliber gate arm; "
                              "networkx columns = independent juror (the "
                              "automorphism-set cross-check is skipped at "
                              "512 states per the court's scale guard, the "
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
                         "--emit-expected-template --only lightsout3`) and "
                         "paste the observed rows into EXPECTED_ROWS\n")
    else:
        ps["expected.json"] = _dump(build_expected())
    for name, g in build_groups(_SYM).items():
        ps["groups/" + name] = _dump(g)
    return ps


def self_certify(sym):
    """Author-side certification, re-run on every invocation:
    1. the D4 table + complement: unique per-element maps (exhaustive over
       9!), homomorphism law, complement commutation (all asserted inside
       derive_symmetry_table, re-invoked here);
    2. the toggle dynamics: deterministic single-successor rows, all-zero
       rewards, every press changes the state (no self-loops), the toggle
       matrix has rank 9 and every one of the 512 rows is distinct;
    3. the declared group files: elements match the derived permutations
       and closures, declared action maps match the derived maps, and the
       engine's homomorphism convention holds on every declared pair;
    4. orbit counts (the compression readings the receipts should show).
    Any failure raises (loud)."""
    sym = derive_symmetry_table()
    trans, tags = build_trans()
    for s in range(N_STATES):
        for a in range(N_ACTIONS):
            outs = trans[s][a]
            assert len(outs) == 1 and outs[0][0] == 1.0
            t, r, _tag = press(s, a)
            assert outs[0][1] == t and outs[0][2] == r
            assert t != s, ("self-loop", s, a)          # every press toggles
            assert r == 0.0                             # rule R6
    assert len({tuple(trans[s][a][0][1] for a in range(N_ACTIONS))
                for s in range(N_STATES)}) == N_STATES, "duplicate rows"
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
    # g1 elements == rot90 closure; g2 identical to g1 (controlled contrast);
    # g4 = D4; g3 = complement closure; g5 = D4 x C2 closure
    assert groups["g1_rot90_map.json"]["elements"] == \
        _closure([sym["rot90cw"]["state_perm"]])
    assert groups["g2_rot90_nomap.json"]["elements"] == \
        groups["g1_rot90_map.json"]["elements"]
    assert groups["g4_d4_full.json"]["elements"] == \
        _closure([sym["rot90cw"]["state_perm"],
                  sym["flip_tb"]["state_perm"]])
    assert len(groups["g4_d4_full.json"]["elements"]) == 8
    assert groups["g3_complement.json"]["elements"] == \
        _closure([sym["complement"]["state_perm"]])
    assert groups["g5_d4_x_c2.json"]["elements"] == \
        _closure([sym["rot90cw"]["state_perm"],
                  sym["flip_tb"]["state_perm"],
                  sym["complement"]["state_perm"]])
    assert len(groups["g5_d4_x_c2.json"]["elements"]) == 16
    # per-element declared maps: exactly the derived rho of each element,
    # and the engine's homomorphism convention holds on every declared pair
    # ((g o h)[s] = g[h[s]]  =>  rho(g o h) == rho_g o rho_h)
    by_perm = _full_map_table(sym)
    for key in ("g1_rot90_map.json", "g4_d4_full.json",
                "g5_d4_x_c2.json"):
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
    n_orbits = {"g1": orbits(groups["g1_rot90_map.json"]["elements"]),
                "g2": orbits(groups["g2_rot90_nomap.json"]["elements"]),
                "g3": orbits(groups["g3_complement.json"]["elements"]),
                "g4": orbits(groups["g4_d4_full.json"]["elements"]),
                "g5": orbits(groups["g5_d4_x_c2.json"]["elements"])}
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
        "self-certification OK: 8/8 D4 elements + the complement have "
        "unique per-element button maps (exhaustive over 9! = 362880 "
        "permutations; homomorphism law verified; complement commutes with "
        "every D4 element -> D4 x C2; top-row-only mirror admits no map; "
        "toggle-matrix rank 9 -> no padding states; orbits g1=%d g2=%d "
        "g3=%d g4=%d g5=%d\n"
        % (n_orbits["g1"], n_orbits["g2"], n_orbits["g3"], n_orbits["g4"],
           n_orbits["g5"]))

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

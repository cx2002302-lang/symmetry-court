# -*- coding: utf-8 -*-
"""
make_mini2048.py -- deterministic generator for the mini2048 case: a 2x2
deterministic transcription of the original 2048 merge mechanics, built as
the first real-system sample for the engine's *explicit* action caliber
(state permutation + declared direction-key renaming).

Writes, byte-identical on every re-run (nothing random, no clock, no locale
dependence), next to this script:

  model.json                       the trans model: 256 states = 2^8
                                   (4 cells x 2 bits), 4 actions
                                   (up/right/down/left, the original's own
                                   direction numbering), rewards = 2048 score
  groups/g1_rot90_map.json         defendant A: 90-degree board rotation +
                                   renamed direction keys (explicit+action_map)
  groups/g2_rot90_nomap.json       defendant B: same rotation, direction keys
                                   pinned (fixed) -- the naive-intuition claim
  groups/g3_flip_map.json          defendant C: top-bottom mirror + renamed
                                   keys (explicit+action_map)
  groups/g4_d4_full.json           defendant D: the full 8-element board
                                   symmetry group D4 (explicit+action_map)
  groups/g5_row_mirror_fake.json   control: top-row-only mirror (not a board
                                   symmetry) -- expected refuse
  groups/g6_pads.json              positive control: swap of two padding
                                   states (fixed, expected pass)
  expected.json                    pinned verdict rows, observed live

Transcription authority (first-hand, public):
  - gabrielecirulli/2048 (MIT), js/game_manager.js on master: move()
    (L130-191), getVector() (L193-204), buildTraversals() (L206-220),
    findFarthestPosition() (L222-236), movesAvailable() (L238-268),
    addRandomTile() (L68-76). File fetched from
    https://raw.githubusercontent.com/gabrielecirulli/2048/master/js/game_manager.js
  - Wikipedia, "2048 (video game)", Gameplay section (rules sentences quoted
    in meta.rules_with_citations).

Variant boundaries (recorded, not hidden -- see TRANSCRIPTION_NOTES):
  1. 2x2 grid, cell values {empty, 2, 4} only; merging is capped at 4 (2+2=4
     is the ceiling; two 4s slide without merging). The original merges any
     equal pair (game_manager.js L156-157 merges unconditionally on match);
     the cap is this case's deliberate truncation to keep the state space
     finite at 2^8 without an 8/16/... value ladder.
  2. Random tile spawns are NOT collected (game_manager.js L182-183 spawns
     only after a moved move; L69-76 picks value 2/4 at random): randomness
     is outside the deterministic FSM semantics this court transcribes.
  3. No game-over absorbing state: a dead board (no direction changes it)
     self-loops on every action with reward 0, which is exactly what the
     original's move() computes for a move that changes nothing (L175-177:
     moved stays false; L182: nothing happens).
  4. Padding: 175 of the 256 bit patterns contain the unused cell encoding 3;
     they are unreachable padding states (every action self-loops, reward 0),
     same convention as the tcp/dhcp/imap cases.

The explicit caliber and this case: a true board symmetry renames the four
direction keys along with the cells (rotating the board clockwise turns the
"up" key into the "right" key). Per group element pi the renaming rho(pi) is
forced; rho(identity)=id and rho(rot90)!=id, so a group file can only carry
the renaming of ONE chosen element (the engine's group format has a single
semantics.action_map). Each explicit group file here declares the map of its
named generator; model.meta carries the full per-element derivation table
(computed and asserted by this generator on every run).

Usage:
  python -X utf8 cases/mini2048/make_mini2048.py            # write all files
  python -X utf8 cases/mini2048/make_mini2048.py --out DIR  # write into DIR
  python -X utf8 cases/mini2048/make_mini2048.py --check    # verify bytes +
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
# Cell index c = 2*y + x on a 2x2 grid, (x, y) = (column, row) using the
# original source's coordinate convention (game_manager.js uses tile.x/tile.y
# with x rightward, y downward): 0=top-left, 1=top-right, 2=bottom-left,
# 3=bottom-right. State = sum_c enc_c << (2c) -> 4 cells x 2 bits = 2^8.
CELL_XY = [(0, 0), (1, 0), (0, 1), (1, 1)]          # index -> (x, y)
XY_CELL = {xy: i for i, xy in enumerate(CELL_XY)}
N_CELLS = 4
ENC_EMPTY, ENC_2, ENC_4, ENC_PAD = 0, 1, 2, 3       # per-cell 2-bit encoding
N_BITS = 8
N_STATES = 1 << N_BITS                              # 256
N_ACTIONS = 4

# Actions use the ORIGINAL source's own numbering (game_manager.js L131:
# "0: up, 1: right, 2: down, 3: left") and L194-204 getVector.
ACTION_NAMES = ["up", "right", "down", "left"]
VECTOR = {0: (0, -1), 1: (1, 0), 2: (0, 1), 3: (-1, 0)}   # L196-201

MERGE_REWARD = 4.0    # game_manager.js L167: score += merged.value; 2+2 -> 4
MERGE_CAP_ENC = ENC_4  # variant boundary: 2+2=4 is the merge ceiling

GM = "gabrielecirulli/2048 js/game_manager.js (MIT) L"
WIKI = 'Wikipedia "2048 (video game)", Gameplay: '

RULES = [
    {"id": "R1-slide",
     "rule": ("a move slides every tile as far as possible toward the chosen "
              "edge, stopped by another tile or the grid edge"),
     "citation": (GM + "152,172,222-236 (findFarthestPosition; moveTile to "
                  "positions.farthest); " + WIKI +
                  "'Tiles slide as far as possible in the chosen direction "
                  "until they are stopped by either another tile or the edge "
                  "of the grid.'")},
    {"id": "R2-merge-if-equal",
     "rule": ("two tiles of the same value that collide merge into one tile "
              "of the total value"),
     "citation": (GM + "156 (next.value === tile.value); 157 (tile.value * 2); "
                  + WIKI + "'If two tiles of the same number collide while "
                  "moving, they will merge into a tile with the total value "
                  "of the two tiles that collided.'")},
    {"id": "R3-merge-once",
     "rule": ("a tile created by a merge cannot merge again within the same "
              "move"),
     "citation": (GM + "155 ('Only one merger per row traversal?'); 156 "
                  "(!next.mergedFrom); 113-120 (prepareTiles clears "
                  "mergedFrom at move start); " + WIKI + "'The resulting "
                  "tile cannot merge with another tile again in the same "
                  "move.' (On a 2-cell line this guard is automatically "
                  "satisfied; cited because the transcribed rule is the "
                  "original's.)")},
    {"id": "R4-score",
     "rule": ("the score increases by the value of the merged tile"),
     "citation": (GM + "167 (self.score += merged.value); " + WIKI +
                  "'The user's score starts at zero, and is increased "
                  "whenever two tiles combine, by the value of the new "
                  "tile.'")},
    {"id": "R5-noop-move",
     "rule": ("a move that slides nothing and merges nothing leaves the "
              "board and the score unchanged"),
     "citation": (GM + "175-177 (moved stays false when no tile moved); "
                  "182-190 (if (moved) {...} -- nothing happens otherwise); "
                  "transcribed as a deterministic self-loop with reward 0")},
    {"id": "R6-direction-numbering",
     "rule": ("the four actions are the arrow keys, numbered 0: up, "
              "1: right, 2: down, 3: left"),
     "citation": (GM + "131 ('0: up, 1: right, 2: down, 3: left'); 194-204 "
                  "(getVector map)")},
    {"id": "R7-random-spawn-not-collected",
     "rule": ("NOT COLLECTED: after a moved move the original spawns a random "
              "tile (value 2 with probability 0.9, else 4) in a random empty "
              "cell"),
     "citation": (GM + "182-183 (if (moved) { this.addRandomTile(); ... }); "
                  "68-76 (addRandomTile: Math.random() < 0.9 ? 2 : 4); "
                  + WIKI + "'another such tile appears in a random empty "
                  "space after each turn.' -- randomness is outside the "
                  "deterministic FSM semantics; recorded, not repaired")},
    {"id": "R8-dead-board",
     "rule": ("a board where no direction changes anything self-loops on "
              "every action (no legal move changes the deterministic state)"),
     "citation": (GM + "184-187 (movesAvailable() false -> over=true); "
                  "238-268 (movesAvailable/tileMatchesAvailable); " + WIKI +
                  "'When the player has no legal moves (there are no empty "
                  "spaces and no adjacent tiles with the same value), the "
                  "game ends.' -- in the no-spawn variant deadness reduces "
                  "to: no direction changes the board")},
    {"id": "R9-merge-cap-VARIANT",
     "rule": ("VARIANT BOUNDARY: merging is capped at 4 -- only 2+2 merges "
              "(into 4); two 4s slide without merging"),
     "citation": ("the original has no cap (game_manager.js L156-157 merge "
                  "any equal pair, L170 only watches for 2048); the cap is "
                  "this case's deliberate 2x2 truncation, recorded in "
                  "meta.transcription_notes")},
]

TRANSCRIPTION_NOTES = [
    "scope: 2x2 board, cell values {empty, 2, 4}; the deterministic core of "
    "2048 (slide + merge) with the random tile spawn NOT collected (rule "
    "R7) -- randomness is not part of the deterministic FSM semantics, per "
    "the court's not-collected discipline (same pattern as the tcp case's "
    "any-state RST edges).",
    "VARIANT BOUNDARY (rule R9): the merge is capped at 4 (2+2 -> 4 only; "
    "two 4s never merge here). The original merges any equal pair "
    "(game_manager.js L156-157). Without the cap a 2x2 board still has a "
    "finite reachable set, but the 8/16/... value ladder would need wider "
    "cell encodings; the cap keeps the transcription inside 2 bits per cell "
    "and is applied identically in all four directions, so the board "
    "symmetry group is preserved.",
    "actions: indexed with the original's own numbering 0:up, 1:right, "
    "2:down, 3:left (game_manager.js L131) -- action indices are source "
    "data, not a court choice.",
    "encoding: state = 8 bits = 4 cells x 2 bits; per-cell encoding 0=empty, "
    "1=value 2, 2=value 4, 3=unused. The 175 states containing a cell with "
    "encoding 3 are unreachable padding: every action self-loops with "
    "reward 0 (same padding convention as tcp/dhcp/imap states 11..15). "
    "Moves never create encoding 3, so real states (81 of them) only reach "
    "real states.",
    "dead boards: a board that no direction changes self-loops on all four "
    "actions with reward 0 (rule R5/R8) -- this is the original's own "
    "behavior for a move that changes nothing, not a padding convention.",
    "rewards: the 2048 score (rule R4): +4 for the only allowed merge "
    "(2+2 -> 4), 0 otherwise. Unlike tcp/dhcp/imap (all-zero rewards) the "
    "reward layer here carries the game's payoff; the explicit/fixed "
    "contrast therefore also has a reward-profile reading.",
    "explicit caliber note: a board symmetry renames the direction keys "
    "element-by-element (rotating the board clockwise turns 'up' into "
    "'right'); rho(identity)=id while rho(rot90)!=id, so no single "
    "action_map can serve a whole closed group. The engine's group format "
    "carries ONE semantics.action_map; each explicit group file here "
    "declares the map of its named generator, and "
    "meta.per_element_action_maps holds the full derivation (computed and "
    "asserted by this generator on every run).",
    "regenerate: python -X utf8 cases/mini2048/make_mini2048.py",
]

# ---------------------------------------------------------------- board ops
def decode(s):
    return [(s >> (2 * c)) & 3 for c in range(N_CELLS)]


def encode(cells):
    v = 0
    for c, e in enumerate(cells):
        v |= e << (2 * c)
    return v


def is_pad(s):
    return any(e == ENC_PAD for e in decode(s))


# Lines per direction: pairs (u, v) of cell indices, u = the cell at the wall
# the tiles move toward, v = the cell behind it. Derived from the vector map
# (R6) so the four directions are the same rule, not four hand-coded rules.
def lines_for(direction):
    vx, vy = VECTOR[direction]
    out = []
    for x in range(2):
        for y in range(2):
            # a line starts at the wall cell: the cell with no neighbor
            # further along (x+vx, y+vy) inside the grid
            wx, wy = x + vx, y + vy
            if not (0 <= wx < 2 and 0 <= wy < 2):
                bx, by = x, y
                fx, fy = x - vx, y - vy
                out.append((XY_CELL[(bx, by)], XY_CELL[(fx, fy)]))
    return sorted(out)


LINES = {a: lines_for(a) for a in range(N_ACTIONS)}


def move(s, a):
    """Deterministic 2048 move -> (successor state, reward, tag).

    Tag: 'M' merged (R2/R3/R4), 'S' slid without merging (R1), 'N' no-op
    self-loop (R5), 'P' padding self-loop. Returns the rule tags so every
    edge's generating rules are recorded (meta.edge_rule_tags).
    """
    if is_pad(s):
        return s, 0.0, "P"
    cells = decode(s)
    new = list(cells)
    moved = False
    merged = False
    for (u, v) in LINES[a]:
        eu, ev = new[u], new[v]
        if eu == ENC_EMPTY and ev == ENC_EMPTY:
            continue                       # nothing to slide (R1: no tiles)
        if eu == ENC_EMPTY:
            new[u], new[v] = ev, ENC_EMPTY # slide to the wall (R1)
            moved = True
            continue
        if ev == ENC_EMPTY:
            continue                       # tile already at the wall
        if eu == ev and eu < MERGE_CAP_ENC:
            new[u], new[v] = eu + 1, ENC_EMPTY   # merge once (R2/R3), cap R9
            moved = True
            merged = True
            continue
        # eu != ev (or cap-blocked pair): no slide possible, no merge
    if not moved:
        return s, 0.0, "N"                 # R5: board and score unchanged
    reward = MERGE_REWARD if merged else 0.0   # R4
    return encode(new), reward, ("M" if merged else "S")


def build_trans():
    """256 x 4 deterministic rows + the per-edge rule-tag table."""
    trans = []
    tags = []
    for s in range(N_STATES):
        row = []
        srow_tags = []
        for a in range(N_ACTIONS):
            t, r, tag = move(s, a)
            row.append([[1.0, t, r]])
            srow_tags.append(tag)
        trans.append(row)
        tags.append("".join(srow_tags))
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
    """Content map d -> state permutation pi: pi(s)[d[c]] = s[c]."""
    pi = []
    for s in range(N_STATES):
        cells = decode(s)
        t_cells = [0] * N_CELLS
        for c in range(N_CELLS):
            t_cells[d[c]] = cells[c]
        pi.append(encode(t_cells))
    return pi


def compose_d(d2, d1):
    """Content maps: apply d1 first, then d2."""
    return [d2[d1[c]] for c in range(N_CELLS)]


# The eight board symmetries as (x, y) transforms (D4 on the 2x2 grid).
D4_TRANSFORMS = [
    ("id",         lambda x, y: (x, y)),
    ("rot90cw",    lambda x, y: (1 - y, x)),
    ("rot180",     lambda x, y: (1 - x, 1 - y)),
    ("rot90ccw",   lambda x, y: (y, 1 - x)),
    ("flip_tb",    lambda x, y: (x, 1 - y)),   # top-bottom mirror
    ("flip_lr",    lambda x, y: (1 - x, y)),   # left-right mirror
    ("transpose",  lambda x, y: (y, x)),
    ("antitrans",  lambda x, y: (1 - y, 1 - x)),
]


def succ_state(s, a):
    return move(s, a)[0]


def derive_action_map(pi):
    """Exhaustive search for rho with, for ALL states s and actions a:
    succ(pi(s), rho[a]) == pi(succ(s, a)).
    Returns the unique rho (action-index list) or None. This is the
    author-side derivation of the per-element direction-key renaming; the
    engine's verdicts remain the court's judges."""
    found = []
    for rho in itertools.permutations(range(N_ACTIONS)):
        ok = True
        for s in range(N_STATES):
            ps = pi[s]
            for a in range(N_ACTIONS):
                if succ_state(ps, rho[a]) != pi[succ_state(s, a)]:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            found.append(list(rho))
    if not found:
        return None
    assert len(found) == 1, "action map not unique: %r" % found
    return found[0]


def compose_maps(rho_outer, rho_inner):
    """rho after rho: a -> rho_outer[rho_inner[a]]."""
    return [rho_outer[rho_inner[a]] for a in range(N_ACTIONS)]


def derive_symmetry_table():
    """Per-element action maps for the whole D4 + the homomorphism check.

    Returns dict name -> {"content_map": d, "state_perm": pi, "action_map":
    rho or None}. Asserts: rho(id)==id; every D4 element has a unique rho;
    rho is a homomorphism on D4 (rho(d2 o d1) == rho(d2) o rho(d1)); the
    rot90 map differs from id (the non-triviality of the renamed-key
    reading); and the fake control map (top-row swap) admits NO rho at all.
    """
    table = {}
    for name, fn in D4_TRANSFORMS:
        d = cell_map_of(fn)
        pi = state_perm_of(d)
        table[name] = {"content_map": d, "state_perm": pi,
                       "action_map": derive_action_map(pi)}
    assert table["id"]["action_map"] == [0, 1, 2, 3]
    for name in table:
        assert table[name]["action_map"] is not None, name
    # homomorphism: rho(d2 o d1) == rho(d2) o rho(d1)   (apply d1 then d2)
    for (n1, f1) in D4_TRANSFORMS:
        for (n2, f2) in D4_TRANSFORMS:
            comp = compose_d(table[n2]["content_map"], table[n1]["content_map"])
            # comp must be the content map of the transform f2 o f1
            assert comp == cell_map_of(lambda x, y, f1=f1, f2=f2: f2(*f1(x, y))), \
                (n1, n2)
            want = compose_maps(table[n2]["action_map"], table[n1]["action_map"])
            got = derive_action_map(state_perm_of(comp))
            assert got == want, ("homomorphism broken", n1, n2, got, want)
    assert table["rot90cw"]["action_map"] != [0, 1, 2, 3]
    # the fake control: top-row-only swap is a symmetry under NO renaming
    fake = [1, 0, 2, 3]  # content of cell 0 <-> 1 (top row), bottom untouched
    assert derive_action_map(state_perm_of(fake)) is None
    return table


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


# ---------------------------------------------------------------- groups
def _perm_from_cell_map(d):
    return state_perm_of(d)


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


def build_groups(sym):
    rot_pi = sym["rot90cw"]["state_perm"]
    rot_map = sym["rot90cw"]["action_map"]
    flip_pi = sym["flip_tb"]["state_perm"]
    flip_map = sym["flip_tb"]["action_map"]
    d4 = _closure([rot_pi, flip_pi])
    assert len(d4) == 8, len(d4)
    g1 = _closure([rot_pi])
    assert len(g1) == 4
    g3 = _closure([flip_pi])
    assert len(g3) == 2
    fake_pi = state_perm_of([1, 0, 2, 3])
    g5 = _closure([fake_pi])
    pad_a, pad_b = 3, 11   # both contain a cell with encoding 3 -> padding
    assert is_pad(pad_a) and is_pad(pad_b)
    g6 = _closure([_swap_states(pad_a, pad_b)])
    regen = "python -X utf8 cases/mini2048/make_mini2048.py"

    return {
        "g1_rot90_map.json": {
            "n_states": N_STATES,
            "elements": g1,
            "semantics": {"action": "explicit", "action_map": list(rot_map)},
            "meta": {
                "claim": ("defendant A: rotating the board 90 degrees "
                          "clockwise and renaming the direction keys with it "
                          "(up->right->down->left->up) preserves the game "
                          "exactly -- the direction keys are bound to board "
                          "coordinates, so the true symmetry carries its own "
                          "key renaming; declared under the explicit caliber "
                          "with the rot90 generator's action map"),
                "construction": ("order-4 cyclic group {id, rot90cw, rot180, "
                                 "rot90ccw} as state permutations; "
                                 "semantics.action_map = the rot90cw "
                                 "generator's derived renaming %r "
                                 "(meta.per_element_action_maps holds all "
                                 "eight per-element maps; rho(identity)=id "
                                 "and rho(rot90)!=id, so a single map cannot "
                                 "serve the whole closed group -- this file "
                                 "declares the generator's)"
                                 % (rot_map,)),
                "why_it_is_a_symmetry": ("the move rule is defined through "
                                         "the same vector map (game_manager.js "
                                         "L194-204) for all four directions; "
                                         "rotating the board and renaming the "
                                         "keys commutes with slide+merge on "
                                         "every one of the 256 states "
                                         "(asserted exhaustively by the "
                                         "generator)"),
                "caliber_note": ("explicit declaration: the action names are "
                                 "bound to board coordinates ('the key that "
                                 "slides toward the top edge'), so they "
                                 "travel with the rotation"),
                "regenerate": regen,
            },
        },
        "g2_rot90_nomap.json": {
            "n_states": N_STATES,
            "elements": g1,
            "semantics": {"action": "fixed"},
            "meta": {
                "claim": ("defendant B: the same 90-degree rotation with the "
                          "direction keys PINNED (up must stay up) -- the "
                          "naive-intuition claim that 'the board looks the "
                          "same rotated', filed deliberately under the fixed "
                          "caliber to show it is the key renaming, not the "
                          "state permutation, that makes defendant A true"),
                "construction": ("identical elements to g1_rot90_map "
                                 "(order-4 rotation group); semantics "
                                 "declared fixed"),
                "why_it_is_not_a_symmetry": ("with the keys pinned, 'up' on "
                                             "the rotated board means sliding "
                                             "toward a different edge than "
                                             "'up' on the original; the "
                                             "deterministic successors differ "
                                             "(TV 1.0 on single-tile states, "
                                             "e.g. a tile on the top-right "
                                             "cell)"),
                "caliber_note": ("fixed declaration: this defendant is the "
                                 "controlled contrast to g1 -- same "
                                 "permutation, opposite action caliber"),
                "regenerate": regen,
            },
        },
        "g3_flip_map.json": {
            "n_states": N_STATES,
            "elements": g3,
            "semantics": {"action": "explicit", "action_map": list(flip_map)},
            "meta": {
                "claim": ("defendant C: mirroring the board top-bottom and "
                          "swapping the vertical keys with it (up<->down, "
                          "left/right unchanged) preserves the game -- the "
                          "second generator of the 8-element board group, "
                          "declared explicit with its derived action map"),
                "construction": ("order-2 group {id, flip_tb}; "
                                 "semantics.action_map = the flip_tb "
                                 "generator's derived renaming %r"
                                 % (flip_map,)),
                "why_it_is_a_symmetry": ("the vector map's y-component flips "
                                         "sign with the mirror while the "
                                         "x-component is untouched; "
                                         "slide+merge commutes with the "
                                         "mirrored keys on all 256 states "
                                         "(asserted exhaustively)"),
                "caliber_note": ("with g1 and g3 both admitted, the full D4 "
                                 "(g4) is generated: <rot90cw, flip_tb> = D4"),
                "regenerate": regen,
            },
        },
        "g4_d4_full.json": {
            "n_states": N_STATES,
            "elements": d4,
            "semantics": {"action": "explicit", "action_map": list(rot_map)},
            "meta": {
                "claim": ("defendant D: the FULL 8-element board symmetry "
                          "group D4 (identity, three rotations, four "
                          "reflections), each element carrying its own "
                          "direction-key renaming -- the complete "
                          "non-trivial positive control; if admitted, the "
                          "compression reading is the orbit count"),
                "construction": ("closure of {rot90cw, flip_tb} = 8 elements; "
                                 "semantics.action_map = the rot90cw "
                                 "generator's map %r (the file format holds "
                                 "one map; the per-element maps for all eight "
                                 "elements are derived and asserted in "
                                 "meta.per_element_action_maps -- "
                                 "rho(identity)=id, so a single non-trivial "
                                 "map cannot be equivariant for the identity "
                                 "element; see the explicit caliber note in "
                                 "model.meta.transcription_notes)"
                                 % (rot_map,)),
                "why_it_is_a_symmetry": ("D4 is the square's own symmetry "
                                         "group and the move rule is "
                                         "direction-symmetric by construction "
                                         "(one vector-driven rule, four "
                                         "directions)"),
                "caliber_note": ("compression reading if admitted: orbits of "
                                 "D4 on the 256 states (expected 55: 21 real "
                                 "+ 34 padding), i.e. 256 states collapse to "
                                 "55 classes"),
                "regenerate": regen,
            },
        },
        "g5_row_mirror_fake.json": {
            "n_states": N_STATES,
            "elements": g5,
            "semantics": {"action": "fixed"},
            "meta": {
                "claim": ("control: mirror the top row only (cells 0<->1 "
                          "swap, bottom row untouched) -- the board looks "
                          "locally mirror-symmetric but this map moves one "
                          "cell pair off the square's symmetry group; filed "
                          "under fixed and expected to be refused"),
                "construction": ("order-2 group swapping the two top-row "
                                 "cells' contents; NOT a member of D4 (D4's "
                                 "left-right mirror also swaps the bottom "
                                 "row)"),
                "why_it_is_not_a_symmetry": ("columns are broken: the up "
                                             "move acts on the two vertical "
                                             "columns, and swapping only the "
                                             "top cells changes which cells "
                                             "form a column; no action "
                                             "renaming can repair it (the "
                                             "generator asserts no rho exists "
                                             "for this map at all)"),
                "caliber_note": ("control defendant: naive structural "
                                 "inspection should also refuse this one "
                                 "(the edge sets already differ)"),
                "regenerate": regen,
            },
        },
        "g6_pads.json": {
            "n_states": N_STATES,
            "elements": g6,
            "semantics": {"action": "fixed"},
            "meta": {
                "claim": ("positive control: padding states %d and %d have "
                          "byte-identical rows (every action self-loops, "
                          "reward 0), so the swap is a genuine symmetry under "
                          "the pinned-key reading and should be admitted "
                          "everywhere" % (pad_a, pad_b)),
                "construction": ("order-2 group swapping padding states %d "
                                 "<-> %d (both contain the unused cell "
                                 "encoding 3)" % (pad_a, pad_b)),
                "why_it_is_a_symmetry": ("padding rows reference no direction; "
                                         "the swap maps every arrow to itself "
                                         "under both calibers"),
                "caliber_note": ("isolates the explicit-caliber dispute from "
                                 "model well-formedness: the engine admits "
                                 "this fixed symmetry on the same model"),
                "regenerate": regen,
            },
        },
    }


def _swap_states(a, b):
    pi = list(range(N_STATES))
    pi[a], pi[b] = pi[b], pi[a]
    return pi


# ---------------------------------------------------------------- model
def build_model(sym, tags):
    per_elem = {}
    for name, _fn in D4_TRANSFORMS:
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
            "source_system": ("2048 merge mechanics (original open-source "
                              "implementation gabrielecirulli/2048, MIT), "
                              "transcribed as a deterministic 2x2 variant: "
                              "slide + merge only, random tile spawns not "
                              "collected"),
            "variant": "mini2048-2x2-deterministic",
            "source_citation": (
                "gabrielecirulli/2048, js/game_manager.js on master (fetched "
                "from raw.githubusercontent.com/gabrielecirulli/2048): "
                "move() L130-191, getVector() L193-204, buildTraversals() "
                "L206-220, findFarthestPosition() L222-236, "
                "movesAvailable() L238-268, addRandomTile() L68-76; rules "
                "corroborated by Wikipedia '2048 (video game)', Gameplay "
                "section. Per-rule citations in meta.rules_with_citations; "
                "per-edge generating rules in meta.edge_rule_tags."),
            "state_names": None,
            "action_names": ACTION_NAMES,
            "state_encoding": (
                "state = 8 bits = 4 cells x 2 bits; cell c = 2*y + x with "
                "(x, y) = (column, row) in the source's convention -> cells "
                "0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right; "
                "per-cell encoding 0=empty, 1=value 2, 2=value 4, 3=unused "
                "(states containing a 3 in any cell = 175 padding states, "
                "every action self-loops reward 0); 81 real states"),
            "real_states_count": 81,
            "padding_states_count": 175,
            "semantics_class": (
                "direction-key: the four actions are the arrow keys bound to "
                "board coordinates (the original's own numbering 0:up, "
                "1:right, 2:down, 3:left, game_manager.js L131). A board "
                "symmetry renames the keys with the cells, so true "
                "symmetries here are explicit-caliber claims; the fixed "
                "reading (keys pinned) is the naive contrast"),
            "reward_rule": (
                "the 2048 score: +4 for a 2+2 -> 4 merge (game_manager.js "
                "L167 score += merged.value; the only merge allowed under "
                "the case's value cap), 0 for every other edge"),
            "rules_with_citations": RULES,
            "edge_rule_tags": {
                "layout": ("edge_rule_tags.values[s] is a 4-character string, "
                           "character a in {M,S,N,P} = the generating rule "
                           "of edge (s, action a); M=merged (R2/R3/R4), "
                           "S=slid without merging (R1), N=no-op self-loop "
                           "(R5), P=padding self-loop"),
                "values": tags,
            },
            "per_element_action_maps": per_elem,
            "known_issue": (
                "engine explicit-caliber limitation discovered by this case "
                "(2026-11-03, crew-chief ruling: record as observed, fix "
                "upstream next wave): the vendored judge's explicit layer "
                "applies ONE declared action_map to every closed group "
                "element including the identity, so on any model with "
                "behaviorally distinguishable actions the identity element "
                "forces the identity map and no non-trivial renamed-action "
                "symmetry can be admitted. g1/g3/g4 are true symmetries "
                "under per-element action maps (derivation asserted by the "
                "generator; table in meta.per_element_action_maps); their "
                "explicit-caliber rejects are expected to flip after the "
                "upstream fix. Diagnosis: cases/mini2048/README.md; live "
                "receipts: cases/mini2048/receipts/."),
            "transcription_notes": TRANSCRIPTION_NOTES,
            "regenerate": "python -X utf8 cases/mini2048/make_mini2048.py",
        },
        "trans": _TRANS,
    }


# ------------------------------------------------- expected verdict table
# Observed on 2026-11-03 from a live three-way arbitration run
# (`python -X utf8 -m symmetry_court arbitrate --emit-expected-template`;
# receipt: verdicts/mini2048.verdict.json). The gate
# (`python -X utf8 -m symmetry_court selftest`) replays every case and
# compares these pinned rows field-by-field against a fresh run.
#
# NOTE (explicit-caliber finding, crew-chief ruling 2026-11-03): the vendored
# engine's explicit judge applies ONE declared action_map to every closed
# group element including the identity, so no non-trivial renamed-action
# symmetry can be admitted (see README.md for the diagnosis). g1/g3/g4 are
# true symmetries under per-element action maps; their explicit-caliber
# verdicts (receipts/check.*.json, engine run WITHOUT --strict) are expected
# to flip from reject to pass after the upstream per-element fix. The
# relabel/fixed rows below answer different calibers and are not expected to
# flip; each carries its own note saying so.
_NOTE_FLIP = ("expected to flip after upstream per-element action-map fix "
              "(see cases/mini2048/README.md and "
              "receipts/check.%s.json): this group is a true symmetry under "
              "per-element action maps; the explicit-caliber reject is the "
              "engine's single-global-action_map limitation, not a "
              "transcription error")
_RELABEL_NOTE = ("court-stamped relabel frame resolves to the bitstring "
                 "judge on this 4-action/8-bit model (n_actions <= n_bits), "
                 "which reads actions as bit flips -- a structural mismatch "
                 "for a direction-key system; diagnostic column, not "
                 "expected to flip")
_FIXED_NOTE = ("direction keys pinned (--strict): under this caliber the "
               "claim is genuinely false, so this row is not expected to "
               "flip; the group's explicit-caliber verdict (receipts/) is "
               "the row that flips after the upstream fix")

EXPECTED_ROWS = {
    "g1_rot90_map": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict", "note": _FIXED_NOTE},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
    },
    "g2_rot90_nomap": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
    },
    "g3_flip_map": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict", "note": _FIXED_NOTE},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
    },
    "g4_d4_full": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict", "note": _FIXED_NOTE},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": False},
    },
    "g5_row_mirror_fake": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": False, "labeled_symmetry": False},
    },
    "g6_pads": {
        "relabel": {"exit": 1, "verdict": "reject", "worst_tv": 1.0,
                    "judge": "bitstring", "note": _RELABEL_NOTE},
        "fixed": {"exit": 0, "verdict": "pass", "worst_tv": 0.0,
                  "judge": "strict"},
        "networkx": {"structure_symmetry": True, "labeled_symmetry": True},
    },
}

_GROUPS_WITH_FLIP_HOOK = ("g1_rot90_map", "g3_flip_map", "g4_d4_full")


def build_expected():
    groups = {}
    for name, g in build_groups(_SYM).items():
        key = os.path.splitext(name)[0]
        groups[key] = {
            "claim": g["meta"]["claim"],
            "relabel": dict(EXPECTED_ROWS[key]["relabel"]),
            "fixed": dict(EXPECTED_ROWS[key]["fixed"]),
            "networkx": dict(EXPECTED_ROWS[key]["networkx"]),
        }
        if key in _GROUPS_WITH_FLIP_HOOK:
            groups[key]["note"] = _NOTE_FLIP % key
    return {
        "case": "mini2048",
        "provenance": {
            "recorded": ("2026-11-03, observed from a live three-way "
                         "arbitration run (`python -X utf8 -m symmetry_court "
                         "arbitrate --emit-expected-template`); the receipt "
                         "is verdicts/mini2048.verdict.json; the gate "
                         "(`python -X utf8 -m symmetry_court selftest`) "
                         "replays the case and compares these rows "
                         "field-by-field"),
            "reading_guide": ("relabel row = engine's relabel frame "
                              "(court-stamped copy; on this 4-action/8-bit "
                              "model that frame resolves to the bitstring "
                              "judge, which reads actions as bit flips -- a "
                              "structural mismatch for a direction-key "
                              "system, recorded as the diagnostic column); "
                              "fixed row = direction keys pinned (--strict); "
                              "the explicit declarations of g1/g3/g4 are "
                              "adjudicated by the vendored engine directly "
                              "(receipts in receipts/) and by the compare "
                              "subcommand's declared-caliber gate arm; "
                              "networkx columns = independent juror. The "
                              "note fields record the explicit-caliber "
                              "finding: g1/g3/g4 are true symmetries under "
                              "per-element action maps, rejected only by the "
                              "engine's single-global-action_map limitation "
                              "(README.md); the relabel/fixed rows answer "
                              "other calibers and are not expected to flip"),
        },
        "groups": groups,
    }


# ---------------------------------------------------------------- main
def _dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


_SYM = derive_symmetry_table()
_TRANS, _TAGS = build_trans()


def payloads():
    ps = {"model.json": _dump(build_model(_SYM, _TAGS)),
          "expected.json": _dump(build_expected())}
    for name, g in build_groups(_SYM).items():
        ps["groups/" + name] = _dump(g)
    return ps


def self_certify():
    """Author-side certification, re-run on every invocation:
    1. every D4 element has a unique per-element action map (and the
       homomorphism property holds);
    2. the fake control admits no map at all;
    3. the transcribed move conserves the value set (real states reach only
       real states) and is deterministic (single successor);
    4. the declared group files' elements match the derived permutations and
       the declared action maps match the derived generator maps.
    Any failure raises (loud)."""
    sym = derive_symmetry_table()
    trans, tags = build_trans()
    for s in range(N_STATES):
        for a in range(N_ACTIONS):
            outs = trans[s][a]
            assert len(outs) == 1 and outs[0][0] == 1.0
            t, r, tag = move(s, a)
            assert outs[0][1] == t and outs[0][2] == r
            if is_pad(s):
                assert tag == "P" and t == s and r == 0.0
            else:
                assert not is_pad(t), (s, a, t)
                assert r in (0.0, MERGE_REWARD)
    groups = build_groups(sym)
    for fname, g in groups.items():
        sem = g["semantics"]
        if sem["action"] == "explicit":
            amap = sem["action_map"]
            assert sorted(amap) == list(range(N_ACTIONS))
        assert g["n_states"] == N_STATES
        for e in g["elements"]:
            assert len(e) == N_STATES and sorted(e) == list(range(N_STATES))
    # g1 elements == rot90 closure; its declared map == derived rot90 map
    assert groups["g1_rot90_map.json"]["elements"] == \
        _closure([sym["rot90cw"]["state_perm"]])
    assert groups["g1_rot90_map.json"]["semantics"]["action_map"] == \
        sym["rot90cw"]["action_map"]
    assert groups["g3_flip_map.json"]["semantics"]["action_map"] == \
        sym["flip_tb"]["action_map"]
    assert groups["g4_d4_full.json"]["elements"] == \
        _closure([sym["rot90cw"]["state_perm"], sym["flip_tb"]["state_perm"]])
    assert len(groups["g4_d4_full.json"]["elements"]) == 8
    n_orbits = {"g1": orbits(groups["g1_rot90_map.json"]["elements"]),
                "g3": orbits(groups["g3_flip_map.json"]["elements"]),
                "g4": orbits(groups["g4_d4_full.json"]["elements"]),
                "g5": orbits(groups["g5_row_mirror_fake.json"]["elements"]),
                "g6": orbits(groups["g6_pads.json"]["elements"])}
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

    sym, n_orbits = self_certify()
    sys.stderr.write(
        "self-certification OK: 8/8 D4 elements have unique per-element "
        "action maps (homomorphism verified); fake control admits no map; "
        "orbits g1=%d g3=%d g4=%d g5=%d g6=%d\n"
        % (n_orbits["g1"], n_orbits["g3"], n_orbits["g4"], n_orbits["g5"],
           n_orbits["g6"]))

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

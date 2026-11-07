# -*- coding: utf-8 -*-
"""
discover.py —— 第四个法庭能力：fixed 口径候选对称群的自动发现

对案卷模型自动发现候选对称群（候选生成），随后过 vendored 引擎 check
验证（闸门臂），产出 verdicts/discover.<case>.json 与候选群文件。

口径边界（诚实声明，与 README 双语同步）：
  · 本能力只发现 fixed 口径（事件名钉死）的候选对称——把 model.trans 建成
    带边属性 (action, prob, reward) 的 MultiDiGraph，自同构枚举即「事件名
    原样对应」下的对称；
  · 动作改名类（relabel/explicit 口径）的候选不由机器发现——「哪种一样」
    必须由案卷作者显式声明（本项目的核心论点），机器不猜。

爆炸防护（硬约束）：
  · 自同构枚举带硬上限 AUTOMORPHISM_CAP（默认 2000）：触顶即停，据已枚举
    部分给出诚实下界（群阶 ≥ cap；轨道下界 = 已枚举置换生成子群的轨道，
    每个块都是「已证对称集合」）；
  · 同时算 1-WL 颜色细化（边标签参与，多重边按重数计入）给出轨道上界
    （每个真轨道必整块落在同一 WL 块内）；WL 离散（全部单点块）⇒ 恒等群；
  · 报告三样：轨道（精确，或 下界=已枚举子群轨道 / 上界=WL 块）、群阶
    （精确或 ≥cap）、细分是否离散。

正确性锚点（bring-up 实测，记录在判决书 provenance 里）：
  · 5 个 n≤8 的案（raft-etcd/usb2/hadoop/k8s/imap）上，本模块的 VF2 枚举
    与 S_n 暴力枚举逐元素集合全等，且与 field-trial 密封真值 fixed_aut_order
    逐一相等（1/2/1/6/24）；
  · WL 颜色的自同构不变性是 1-WL 的标准性质，作 node_match 剪枝无损
    （不丢任何自同构）——它只是剪枝，不是判据。

判据代码零改动红线：本模块不复实现任何引擎判据；闸门臂经 subprocess 调
vendored 引擎 check --strict（与 trial.run_engine_check 同一套机械）。
"""

import hashlib
import json
import os
import time

import networkx as nx
from networkx.algorithms.isomorphism import MultiDiGraphMatcher

from .trial import (ENGINE_TIMEOUT_DEFAULT, load_model, run_engine_check,
                    structural_pad_states)

# ---------------------------------------------------------------- 常量
# 枚举硬上限：触顶即停（诚实下界口径，禁假精确）。
AUTOMORPHISM_CAP_DEFAULT = 2000
# 触顶案闸门候选的闭包上限：候选 = 已枚举集的贪心闭子群（≤ 此上限）。
CLOSURE_CAP_DEFAULT = 256
# 枚举完整且阶 ≤ 此值时，闸门候选 = 完整枚举群（不再取闭子群）。
GATE_FULL_GROUP_CAP = 512
# 判决书里 elements 全列表的存储预算（元素数×状态数 ≤ 此值才全存；
# 触顶案一律只存生成集并注明 partial）。
ELEMENTS_NUMBERS_BUDGET = 100_000
# 逐元素直接判据（对账用）的规模上限：状态数超过此值跳过并如实注明。
DIRECT_CHECK_MAX_STATES = 1024

SEMANTICS_FIXED = "fixed"

_HONESTY_BOUNDARY = (
    "fixed-caliber (event names pinned) candidate discovery only; "
    "action-renaming (relabel/explicit) candidates remain the case author's "
    "explicit declaration - the machine does not guess which kind of sameness "
    "applies")

_METHOD_LINE = (
    "networkx MultiDiGraph VF2 automorphism enumeration with edge labels "
    "(action, prob, reward), pruned by 1-WL edge-label color refinement "
    "(sound: WL colors are automorphism-invariant); hard cap on enumeration")


# ---------------------------------------------------------------- 建图
def build_labeled_graph(model):
    """
    模型 → nx.MultiDiGraph（fixed 口径的事件图）。

    · 节点 = 全部 n_states 个状态（含哑填充态，一视同仁）；
    · trans[s][a] 的每个 outcome 条目 [p, u, r] 展开为一条多重边 s→u，
      边属性 (action, prob, reward) = (动作名, 概率, 奖励)——多条目展开为
      多重边，重数与标签共同进入判定；p≤0 的条目也建边（p 是标签的一部
      分，与密封真值 fixed 判据的全 multiset 口径一致；现存 12 案无 p≤0
      条目，此处口径选择以判据精确对齐为先）。
    """
    G = nx.MultiDiGraph()
    G.add_nodes_from(range(model["n_states"]))
    for s, row in enumerate(model["trans"]):
        for a, outcomes in enumerate(row):
            for oc in outcomes:
                G.add_edge(s, oc[1],
                           action=model["action_names"][a],
                           prob=float(oc[0]),
                           reward=float(oc[2]))
    return G


def _edge_key(d):
    return (d["action"], d["prob"], d["reward"])


def _edge_match(attrs1, attrs2):
    """多重边标签匹配：两侧平行边集合的 (action, prob, reward) 多重集相等。

    networkx 的 MultiDiGraphMatcher 把 {key: 属性dict} 整体交给 edge_match
    （见 networkx/algorithms/isomorphism/vf2userfunc.py 的文档），因此这里
    比较的是多重集而非单条边。
    """
    return sorted(_edge_key(d) for d in attrs1.values()) == \
           sorted(_edge_key(d) for d in attrs2.values())


# ---------------------------------------------------------------- 1-WL
def wl_refine(graph):
    """
    1-WL 颜色细化（边标签参与；有向多重图）。

    每轮新颜色 = hash(旧颜色, 入边多重集{(标签, 邻色)}, 出边多重集{(标签,
    邻色)})；自环同时计入入/出两个多重集；多重边按重数计入。迭代到划分
    不再变细为止。

    返回颜色划分 blocks（节点 id 列表的列表，每块升序）。它是轨道的集合
    上界口径：任何自同构 π 满足 color(π(s)) == color(s)（1-WL 标准性质），
    故每个真轨道必整块落在某一 WL 块内。

    注意局限（诚实边界）：1-WL 对点传递图（如 lightsout3 的状态图）无法
    细分（单一块）——这不是缺陷而是该图的真实对称性：其 fixed 自同构群
    确实点传递（512 个 XOR 平移）。
    """
    n = graph.number_of_nodes()
    edges_in = [[] for _ in range(n)]
    edges_out = [[] for _ in range(n)]
    for u, v, d in graph.edges(data=True):
        lab = _edge_key(d)
        edges_out[u].append((lab, v))
        edges_in[v].append((lab, u))
    colors = [0] * n

    def partition(cols):
        buckets = {}
        for i, c in enumerate(cols):
            buckets.setdefault(c, []).append(i)
        return {tuple(sorted(v)) for v in buckets.values()}

    prev = partition(colors)
    for _round in range(n):
        sig = [hashlib.sha256(repr((
            colors[v],
            sorted((lab, colors[u]) for (lab, u) in edges_in[v]),
            sorted((lab, colors[u]) for (lab, u) in edges_out[v]),
        )).encode("utf-8")).hexdigest()[:16] for v in range(n)]
        uniq = {}
        newc = [uniq.setdefault(s, len(uniq)) for s in sig]
        cur = partition(newc)
        if cur == prev:
            return sorted((list(b) for b in prev), key=lambda b: b[0])
        colors = newc
        prev = cur
    return sorted((list(b) for b in prev), key=lambda b: b[0])


def _colors_from_blocks(blocks, n):
    colors = [0] * n
    for ci, block in enumerate(blocks):
        for v in block:
            colors[v] = ci
    return colors


# ---------------------------------------------------------------- VF2 枚举
def vf2_automorphisms(graph, cap, wl_blocks=None, budget_s=None):
    """
    fixed 口径自同构枚举：MultiDiGraphMatcher(G, G).isomorphisms_iter()，
    硬上限 cap——枚举到 len(perms) >= cap 即停（触顶诚实记录，不假装枚完）。

    wl_blocks：1-WL 划分（可选）；给出时作为 node_match 剪枝（颜色不同的
    配对直接排除）。剪枝无损：WL 颜色自同构不变 ⇒ 不丢任何自同构。

    budget_s：可选墙钟预算（秒）；超过即停（与触顶同口径的诚实截断，
    stop_reason 注明）。默认 None = 无墙钟限制（只受 cap 约束）。

    返回 (perms, truncated, stop_reason)。
    枚举完整（truncated=False）⇒ perms 恰为全部 fixed 口径自同构（与
    S_n 暴力枚举逐元素全等的验证在案，见模块 docstring）。
    """
    n = graph.number_of_nodes()
    node_match = None
    if wl_blocks is not None:
        colors = _colors_from_blocks(wl_blocks, n)
        nx.set_node_attributes(graph, {i: colors[i] for i in range(n)}, "_wl")
        node_match = lambda x, y: x["_wl"] == y["_wl"]  # noqa: E731
    GM = MultiDiGraphMatcher(graph, graph,
                             edge_match=_edge_match, node_match=node_match)
    perms = []
    t0 = time.monotonic()
    for m in GM.isomorphisms_iter():
        perms.append(tuple(m[i] for i in range(n)))
        if len(perms) >= cap:
            return perms, True, ("hard cap reached (%d automorphisms "
                                 "enumerated; enumeration stopped, order is "
                                 "a lower bound)" % cap)
        if budget_s is not None and (time.monotonic() - t0) > budget_s:
            return perms, True, ("wall-clock budget %.0fs exceeded after %d "
                                 "automorphisms; enumeration stopped, order "
                                 "is a lower bound" % (budget_s, len(perms)))
    return perms, False, "search exhausted (all automorphisms enumerated)"


# ---------------------------------------------------------------- 轨道
def orbits_from_perms(perms, n):
    """
    给定置换集合，返回它们生成子群的轨道划分（union-find：每个置换把 i 与
    perm[i] 并入同类）。

    · perms = 完整枚举集 ⇒ 结果 = 全自同构群的精确轨道；
    · perms = 触顶部分枚举 ⇒ 结果是「已证对称集合」：同一块内的状态确实
      存在自同构链互相到达（块 ⊆ 某个真轨道），是轨道的集合下界。
    """
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for p in perms:
        for i in range(n):
            a, b = find(i), find(p[i])
            if a != b:
                parent[a] = b
    buckets = {}
    for i in range(n):
        buckets.setdefault(find(i), []).append(i)
    return sorted((sorted(v) for v in buckets.values()), key=lambda b: b[0])


# ---------------------------------------------------------------- 生成集/闭包
def greedy_generating_set(perms, n):
    """
    贪心生成集：按枚举顺序保留「能并出新轨道对」的置换（恒等不入选）。

    结果的生成子群与 perms 集合有相同的轨道划分（轨道判定对生成子群精确）；
    生成子群本身可能是 perms 张成群的子群（冗余度换速度，口径如实记录）。
    """
    ident = tuple(range(n))
    gens = []
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for p in perms:
        if p == ident:
            continue
        merged = False
        for i in range(n):
            a, b = find(i), find(p[i])
            if a != b:
                parent[a] = b
                merged = True
        if merged:
            gens.append(list(p))
    return gens


def close_under_composition(gens, n, cap):
    """
    轨道闭包算法：gens 张成群的闭包，元素数超过 cap 即停（返回 truncated）。
    返回 (sorted element list, truncated: bool)。truncated=False 时结果
    是真正的闭群。
    """
    ident = tuple(range(n))
    seen = {ident}
    worklist = [ident]
    gens_t = [tuple(g) for g in gens]
    while worklist:
        e = worklist.pop()
        for g in gens_t:
            for cand in (tuple(e[x] for x in g), tuple(g[x] for x in e)):
                if cand not in seen:
                    if len(seen) >= cap:
                        return sorted(list(x) for x in seen), True
                    seen.add(cand)
                    worklist.append(cand)
    return sorted(list(x) for x in seen), False


# ---------------------------------------------------------------- 直接判据
def element_is_fixed_aut(trans, pi):
    """
    逐元素 fixed 口径直接判据（O(n·A)，与 field-trial 密封真值同式）：
      multiset(trans[pi(s)][a]) == multiset{(p, pi(t), r) : (p,t,r) in trans[s][a]}
    事件名钉死：两侧比较都发生在同一动作下标 a 上（12 案动作名无重复，
    下标与名字一一对应；bring-up 已核实）。
    """
    n = len(trans)
    for s in range(n):
        row_src = trans[s]
        row_dst = trans[pi[s]]
        for a in range(len(row_src)):
            lhs = sorted((float(oc[0]), pi[oc[1]], float(oc[2]))
                         for oc in row_src[a])
            rhs = sorted((float(oc[0]), float(oc[1]), float(oc[2]))
                         for oc in row_dst[a])
            if lhs != rhs:
                return False
    return True


# ---------------------------------------------------------------- 数学核心
def discover_case(model, cap=AUTOMORPHISM_CAP_DEFAULT, budget_s=None):
    """
    一案的发现核心（纯数学部分）：三样输出 + 离散性判定。

    返回 dict：{"discovery": {...}, "timing_seconds": {...}}。dict 内含一个
    非序列化私有键 "_enumerated_set"（完整已枚举集合，供对账用），落盘前
    由 run_discover_case 剥离。
    """
    n = model["n_states"]
    timing = {}
    t0 = time.monotonic()
    graph = build_labeled_graph(model)
    n_edges = graph.number_of_edges()
    multi_entry_cells = sum(1 for row in model["trans"]
                            for outcomes in row if len(outcomes) > 1)
    timing["graph"] = round(time.monotonic() - t0, 6)

    t1 = time.monotonic()
    blocks = wl_refine(graph)
    discrete = len(blocks) == n
    timing["wl"] = round(time.monotonic() - t1, 6)

    t2 = time.monotonic()
    perms, truncated, stop_reason = vf2_automorphisms(
        graph, cap, wl_blocks=blocks, budget_s=budget_s)
    timing["vf2"] = round(time.monotonic() - t2, 6)
    count = len(perms)

    t3 = time.monotonic()
    # 轨道：完整枚举 = 精确；触顶 = 下界（已枚举子群轨道）+ 上界（WL 块）
    orbit_blocks = orbits_from_perms(perms, n)
    if truncated:
        orbits_status = "bounded"
        order = None
        order_claim = ("lower bound: at least %d automorphisms proven "
                       "(enumeration stopped at cap %d)" % (count, cap))
        orbit_note = ("truncated enumeration: lower_bound_blocks = orbits of "
                      "the enumerated-permutation subgroup (each block is a "
                      "proven symmetric set, contained in some true orbit); "
                      "upper_bound_blocks = 1-WL blocks (each true orbit is "
                      "contained in one block); the number of true orbits "
                      "lies between #upper_bound_blocks and "
                      "#lower_bound_blocks")
        lower_blocks = orbit_blocks
        upper_blocks = blocks
    else:
        orbits_status = "exact"
        order = count
        order_claim = ("exact: VF2 enumeration completed (%d automorphisms "
                       "= the full fixed-caliber automorphism group)" % count)
        orbit_note = ("enumeration completed: this is the orbit partition of "
                      "the full automorphism group")
        lower_blocks = None
        upper_blocks = None

    # 数学自检：任何轨道块必须整块落在单一 WL 块内（1-WL 不变性的必然），
    # 违反 = 实现错误，fail loud。
    colors = _colors_from_blocks(blocks, n)
    for block in orbit_blocks:
        if len({colors[v] for v in block}) != 1:
            raise AssertionError(
                "internal error: orbit block %r spans multiple WL colors "
                "(1-WL invariance violated)" % block)

    identity_group = (not truncated and count == 1) or discrete

    # elements 存储：完整且预算内才全存；触顶一律只存生成集（注明 partial）
    elements = None
    generators = greedy_generating_set(perms, n)
    if not truncated and count * n <= ELEMENTS_NUMBERS_BUDGET:
        elements = sorted(list(p) for p in perms)
        elements_storage = "full_enumeration"
    else:
        elements_storage = "generating_set"
    gens_note = None
    if truncated:
        gens_note = ("partial enumeration at cap %d: these generators "
                     "generate a subgroup of the enumerated set with the "
                     "same orbits as the enumerated set; the full group is "
                     "NOT claimed (order >= %d)" % (cap, cap))
    elif elements_storage == "generating_set":
        closure, closed_trunc = close_under_composition(
            generators, n, max(count, CLOSURE_CAP_DEFAULT))
        if not closed_trunc and len(closure) == count:
            gens_note = ("full group enumerated (order exact); element list "
                         "elided above the storage budget (%d x %d numbers); "
                         "these generators generate the exact full group "
                         "(closure equals the enumerated set)"
                         % (count, n))
        else:
            gens_note = ("full group enumerated (order exact); element list "
                         "elided above the storage budget (%d x %d numbers); "
                         "generators generate a subgroup with equal orbits "
                         "(closure not verified within budget)"
                         % (count, n))
    timing["orbits_and_generators"] = round(time.monotonic() - t3, 6)

    return {
        "discovery": {
            "semantics": SEMANTICS_FIXED,
            "method": _METHOD_LINE,
            "honesty_boundary": _HONESTY_BOUNDARY,
            "graph": {"nodes": n, "edges": n_edges,
                      "multi_entry_cells": multi_entry_cells},
            "cap": cap,
            "wl_refinement": {
                "n_blocks": len(blocks),
                "discrete": discrete,
                "blocks": [list(b) for b in blocks],
            },
            "enumeration": {
                "enumerated_count": count,
                "truncated": truncated,
                "stop_reason": stop_reason,
                "order": order,
                "order_claim": order_claim,
                "elements_storage": elements_storage,
                "elements": elements,
                "generators": generators,
                "n_generators": len(generators),
                "generators_note": gens_note,
            },
            "orbits": {
                "status": orbits_status,
                "n_orbits": len(orbit_blocks),
                "blocks": orbit_blocks,
                "lower_bound_blocks": lower_blocks,
                "upper_bound_blocks": upper_blocks,
                "note": orbit_note,
            },
            "discrete_wl": discrete,
            "identity_group": identity_group,
            "structural_pad_states": structural_pad_states(model),
            # 私有键：完整已枚举集合（对账用，落盘前剥离）
            "_enumerated_set": {p for p in perms},
        },
        "timing_seconds": timing,
    }


# ---------------------------------------------------------------- 闸门臂
def _candidate_group(model, discovery):
    """
    闸门候选群（semantics fixed，可独立重放）：
      · 枚举完整且阶 ≤ GATE_FULL_GROUP_CAP：候选 = 完整枚举群（就是全群，
        数学上闭）；
      · 否则：候选 = 已枚举集贪心生成元的闭子群（≤ CLOSURE_CAP_DEFAULT；
        超限则逐个退生成元重算，直到闭包完整 ≤ 上限）；
      · 单生成元闭包仍超限（循环群阶 > 上限）：退到恒等群兜底（恒真候选，
        闸门仍可重放，如实注明）。
    返回 (candidate dict, closure_truncated: bool)。
    """
    n = model["n_states"]
    enum = discovery["enumeration"]
    if not enum["truncated"] and enum["order"] is not None \
            and enum["order"] <= GATE_FULL_GROUP_CAP:
        if enum["elements"] is not None:
            elements = sorted(tuple(p) for p in enum["elements"])
        else:
            # 元素列表超出存储预算被省略：用生成集闭包重建全群
            closure, closed_trunc = close_under_composition(
                enum["generators"], n, max(enum["order"],
                                           CLOSURE_CAP_DEFAULT))
            if closed_trunc or len(closure) != enum["order"]:
                raise AssertionError(
                    "internal error: generator closure does not reproduce "
                    "the enumerated full group (%d vs %s)"
                    % (len(closure), enum["order"]))
            elements = sorted(closure)
        return {"kind": "full enumerated group (the exact fixed-caliber "
                        "automorphism group)",
                "order": len(elements),
                "closure_truncated": False,
                "elements": [list(e) for e in elements]}, False

    gens = [list(g) for g in enum["generators"]]
    closure, truncated = close_under_composition(gens, n, CLOSURE_CAP_DEFAULT)
    while truncated and len(gens) > 1:
        gens = gens[:-1]
        closure, truncated = close_under_composition(gens, n,
                                                     CLOSURE_CAP_DEFAULT)
    if truncated:
        # 单生成元闭包仍超限：恒等群兜底（诚实注明，不假装是更大的群）
        return {"kind": "identity-only fallback (even a single generator's "
                        "closure exceeded the cap; the gate verifies only "
                        "the identity element)",
                "order": 1, "closure_truncated": True,
                "elements": [list(range(n))]}, True
    kind = ("closed subgroup of the enumerated set (greedy generators, "
            "closure capped at %d)" % CLOSURE_CAP_DEFAULT)
    if enum["truncated"]:
        kind += (" -- partial discovery: this subgroup is a proven subset "
                 "of the true automorphism group, not the full group")
    return {"kind": kind, "order": len(closure),
            "closure_truncated": False,
            "elements": closure}, False


def write_candidate_file(path, case_name, candidate):
    """候选群文件落盘（semantics fixed + provenance meta）。"""
    doc = {
        "case": case_name,
        "semantics": {
            "action": SEMANTICS_FIXED,
            "note": ("machine-discovered candidate group under the fixed "
                     "standard (event names pinned); produced by "
                     "symmetry_court discover; the declared-caliber "
                     "contrast groups live in the case's own groups/ dir"),
        },
        "elements": candidate["elements"],
        "meta": {
            "claim": ("candidate symmetry group auto-discovered from the "
                      "model transition table (fixed caliber); verified by "
                      "the vendored engine check as the gate arm"),
            "discovered_by": _METHOD_LINE,
            "candidate_kind": candidate["kind"],
        },
    }
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    return doc


# ---------------------------------------------------------------- 对账
def _perm_label(p):
    """置换 → 环表示（人读得懂的对账证据）。"""
    n = len(p)
    seen = [False] * n
    cycles = []
    for i in range(n):
        if seen[i]:
            continue
        cyc = []
        j = i
        while not seen[j]:
            seen[j] = True
            cyc.append(j)
            j = p[j]
        if len(cyc) > 1:
            cycles.append("(%s)" % " ".join(str(x) for x in cyc))
    return "".join(cycles) if cycles else "id"


def _reconcile_all(cases_dir, model, case_dir, discovery):
    """expected.json（fixed 行 + nx labeled 列）与群文件逐元素直接判据对账。"""
    exp_path = os.path.join(case_dir, "expected.json")
    if not os.path.isfile(exp_path):
        return {"checked": False,
                "reason": "no expected.json in the case directory",
                "groups": [], "all_consistent": None}
    with open(exp_path, "r", encoding="utf-8") as f:
        expected = json.load(f)

    enum = discovery["enumeration"]
    n = model["n_states"]
    trans = model["trans"]
    enum_set = discovery.get("_enumerated_set")
    truncated = enum["truncated"]
    gens = {tuple(g) for g in enum["generators"]}

    groups_dir = os.path.join(case_dir, "groups")
    group_files = {}
    if os.path.isdir(groups_dir):
        for fn in sorted(os.listdir(groups_dir)):
            if fn.endswith(".json"):
                try:
                    with open(os.path.join(groups_dir, fn),
                              encoding="utf-8") as f:
                        group_files[os.path.splitext(fn)[0]] = json.load(f)
                except (OSError, ValueError):
                    group_files[os.path.splitext(fn)[0]] = None

    rows = []
    all_consistent = True
    for name in sorted(expected.get("groups") or {}):
        row = expected["groups"][name]
        fixed_v = (row.get("fixed") or {}).get("verdict")
        labeled_v = (row.get("networkx") or {}).get("labeled_symmetry")
        rec = {"group": name,
               "expected_fixed_verdict": fixed_v,
               "expected_labeled_symmetry": labeled_v}
        raw = group_files.get(name)
        elements = None
        if isinstance(raw, dict) and isinstance(raw.get("elements"), list):
            elements = [tuple(e) for e in raw["elements"]]
        if elements is None:
            rec["direct_check"] = "skipped: group file missing/unreadable"
            rec["fixed_row_consistent"] = None
            all_consistent = False
            rows.append(rec)
            continue
        rec["n_elements"] = len(elements)
        rec["nontrivial_elements"] = [_perm_label(e) for e in elements
                                      if list(e) != list(range(len(e)))]
        if n > DIRECT_CHECK_MAX_STATES:
            rec["direct_check"] = ("skipped: n_states=%d > %d (per-element "
                                   "direct criterion not run)"
                                   % (n, DIRECT_CHECK_MAX_STATES))
            rec["fixed_row_consistent"] = None
            rows.append(rec)
            continue
        flags = [element_is_fixed_aut(trans, list(e)) for e in elements]
        rec["all_elements_fixed_aut"] = all(flags)
        want_pass = (fixed_v == "pass")
        rec["fixed_row_consistent"] = bool(want_pass == all(flags))
        if not rec["fixed_row_consistent"]:
            all_consistent = False
        # 枚举成员资格（完整枚举 = 精确双向；触顶 = 单侧证明力）
        if enum_set is not None:
            inside = [e for e in elements if e in enum_set]
            if not truncated:
                miss = [e for e in elements if e not in enum_set]
                rec["membership_all_in"] = not miss
                rec["membership_absent_elements"] = [_perm_label(e)
                                                     for e in miss]
                rec["enumeration_membership"] = (
                    "all %d elements in the enumerated set (exact: "
                    "enumeration completed)" % len(elements) if not miss
                    else "not in enumerated set: %s (exact: enumeration "
                         "completed; these elements are not fixed "
                         "automorphisms)" % [_perm_label(e) for e in miss])
                if miss and want_pass:
                    all_consistent = False
            else:
                rec["membership_all_in"] = None
                rec["membership_found_count"] = len(inside)
                rec["enumeration_membership"] = (
                    "%d/%d elements found in the partial enumeration "
                    "(found => proven automorphism; not found => "
                    "inconclusive at cap %d)"
                    % (len(inside), len(elements), discovery["cap"]))
        else:
            inside = [e for e in elements if e in gens]
            rec["enumeration_membership"] = (
                "generating-set storage: %d/%d declared elements appear "
                "verbatim among the stored generators (membership against "
                "the full enumerated set is not recordable at cap)"
                % (len(inside), len(elements)))
        rows.append(rec)
    return {"checked": True,
            "expected_file": os.path.relpath(
                exp_path, os.path.dirname(cases_dir)),
            "criterion_direct": ("multiset(trans[pi(s)][a]) == "
                                 "multiset{(p, pi(t), r)} per (s, a) - the "
                                 "sealed fixed criterion"),
            "groups": rows,
            "all_consistent": all_consistent}


def _reconcile_sealed(case_name, discovery, sealed_dir):
    """field 五案的密封真值对账（--sealed-dir 提供时才跑）。"""
    if not sealed_dir:
        return {"checked": False,
                "reason": ("no sealed dir provided (--sealed-dir); sealed "
                           "reconciliation not run")}
    path = os.path.join(sealed_dir, "%s.truth.json" % case_name)
    if not os.path.isfile(path):
        return {"checked": False,
                "reason": ("no sealed truth file for this case in the "
                           "provided sealed dir (%s.truth.json)" % case_name)}
    with open(path, "r", encoding="utf-8") as f:
        sealed = json.load(f)
    tp = sealed.get("truth_primary") or {}
    sealed_order = tp.get("fixed_aut_order")
    enum = discovery["enumeration"]
    rec = {"checked": True,
           "sealed_file": "%s.truth.json" % case_name,
           "sealed_file_sha256": _sha256(path),
           "sealed_fixed_aut_order": sealed_order,
           "sealed_method": tp.get("method"),
           "discovered_order": enum["order"],
           "discovered_truncated": enum["truncated"]}
    if sealed_order is None:
        rec["order_matches"] = None
        rec["note"] = "sealed truth records no fixed_aut_order"
    elif enum["truncated"]:
        rec["order_matches"] = None
        rec["note"] = ("enumeration truncated at cap %d: the discovered "
                       "order is a lower bound (>= %d); the sealed order "
                       "%s exceeds the cap, so no contradiction is "
                       "derivable from this run; structural consistency "
                       "evidence is recorded below"
                       % (discovery["cap"], enum["enumerated_count"],
                          sealed_order))
    else:
        rec["order_matches"] = (enum["order"] == sealed_order)
        rec["note"] = ("enumeration completed: exact order comparison"
                       if rec["order_matches"] else
                       "ORDER MISMATCH: discovered %d vs sealed %s - a real "
                       "disagreement, recorded not smoothed over"
                       % (enum["order"], sealed_order))
    sealed_elems = tp.get("fixed_aut_elements")
    if sealed_elems and not enum["truncated"] \
            and enum["elements"] is not None:
        rec["elements_set_match"] = (
            sorted(tuple(e) for e in sealed_elems) ==
            sorted(tuple(e) for e in enum["elements"]))
    elif enum["truncated"]:
        # 触顶案的单侧结构一致性：每个已枚举置换是否固定全部非哑填充态
        # （密封 isolated-filler 口径下协议态被钉死）。
        pads = set(discovery["structural_pad_states"])
        real = [s for s in range(discovery["graph"]["nodes"]) if s not in pads]
        elems = enum["elements"]
        label = "enumerated elements"
        if elems is None:
            elems = enum["generators"] or []
            label = "stored generators"
        bad = [e for e in elems if any(e[s] != s for s in real)]
        rec["partial_enumeration_vs_sealed_structure"] = (
            "all %d %s fix every non-pad state: %s"
            % (len(elems), label, "yes" if not bad else
               "NO (%d violations - a real disagreement)" % len(bad)))
    return rec


def _smoke_directions(case_name, model, discovery, reconciliation):
    """
    冒烟双方向（tcp 系案卷的验收口径，两个方向都必须成立）：
      · pads 方向：结构性哑填充态应被自动发现为对称（完整枚举时：落在
        同一精确轨道块内）；
      · swap 方向：案卷声明的 swap 类群（结构直觉的假对称）不应被自动
        发现——两条独立证据：逐元素直接判据否定 + 枚举集合精确不含。
    非 tcp 系案卷返回 {"applicable": false}。触顶案两方向都降级为
    inconclusive（禁假精确：完整枚举才有「不在」的精确证明）。
    """
    if "tcp" not in case_name:
        return {"applicable": False}
    pads = discovery["structural_pad_states"]
    enum = discovery["enumeration"]
    out = {"applicable": True, "pad_states": pads, "directions": {}}
    exact = not enum["truncated"]

    def _find_rec(token):
        for r in reconciliation.get("groups") or []:
            if token in (r.get("group") or ""):
                return r
        return None

    # pads 方向：完整枚举 = pads 落在同一精确轨道块；触顶 = 只能凭
    # 已声明的 pads 群逐元素直接判据（判定性的证据），否则如实 inconclusive
    pads_rec = _find_rec("pads")
    if exact:
        orb_sets = [set(b) for b in discovery["orbits"]["blocks"]]
        same_block = bool(pads) and any(all(s in b for s in pads)
                                        for b in orb_sets)
        out["directions"]["pads_discovered"] = same_block
        out["directions"]["pads_evidence"] = (
            "structural pad states %s form a single exact orbit block "
            "(enumeration complete, order %s)" % (pads, enum["order"]))
    elif pads_rec is not None and \
            pads_rec.get("all_elements_fixed_aut") is True:
        out["directions"]["pads_discovered"] = True
        out["directions"]["pads_evidence"] = (
            "truncated enumeration: every element of the declared pads "
            "group passes the direct fixed criterion (%s); orbit evidence "
            "is bounded (see orbits note)"
            % pads_rec.get("enumeration_membership"))
    else:
        out["directions"]["pads_discovered"] = None
        out["directions"]["pads_evidence"] = (
            "inconclusive at cap: pad states %s share one 1-WL block "
            "(upper bound only); proven-symmetric coverage from the partial "
            "enumeration is in orbits.lower_bound_blocks" % pads)
    # swap 方向：直接判据的否定是判定性的（与枚举无关）；完整枚举时
    # 「不在已枚举集合」是第二独立证据
    swap_rec = _find_rec("swap")
    if swap_rec is None:
        out["directions"]["swap_not_discovered"] = None
        out["directions"]["swap_evidence"] = \
            "no swap-declared group in expected.json"
    else:
        direct_no = (swap_rec.get("all_elements_fixed_aut") is False)
        if exact:
            absent = swap_rec.get("membership_all_in") is False
            out["directions"]["swap_not_discovered"] = \
                bool(direct_no or absent)
            out["directions"]["swap_evidence"] = (
                "declared swap group %r: direct criterion "
                "all_elements_fixed_aut=%s; exact enumeration membership "
                "absent=%s (%s)"
                % (swap_rec.get("group"),
                   swap_rec.get("all_elements_fixed_aut"), absent,
                   swap_rec.get("enumeration_membership")))
        elif direct_no:
            out["directions"]["swap_not_discovered"] = True
            out["directions"]["swap_evidence"] = (
                "declared swap group %r: direct criterion rejects "
                "(all_elements_fixed_aut=false, decisive regardless of "
                "enumeration); enumeration absence inconclusive at cap"
                % swap_rec.get("group"))
        else:
            out["directions"]["swap_not_discovered"] = None
            out["directions"]["swap_evidence"] = (
                "inconclusive at cap (direct criterion did not reject: "
                "all_elements_fixed_aut=%s)" %
                swap_rec.get("all_elements_fixed_aut"))
    return out


# ---------------------------------------------------------------- 工具
def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_now():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- 一案全流程
def run_discover_case(case_name, cases_dir, verdicts_dir, vendored_dir,
                      cap=AUTOMORPHISM_CAP_DEFAULT, budget_s=None,
                      timeout=ENGINE_TIMEOUT_DEFAULT, sealed_dir=None):
    """
    一案的 discover 全流程：数学核心 → 候选群文件 → 闸门臂 → 对账 →
    落盘 verdicts/discover.<case>.json。返回 (verdict dict, error|None)。
    """
    case_dir = os.path.join(cases_dir, case_name)
    model_path = os.path.join(case_dir, "model.json")
    if not os.path.isfile(model_path):
        return None, "model.json not found in %s" % case_dir
    try:
        model = load_model(model_path)
    except (OSError, ValueError) as e:
        return None, "model.json unreadable: %s" % e
    model["path"] = model_path

    core = discover_case(model, cap=cap, budget_s=budget_s)
    discovery = core["discovery"]

    # 候选群文件 + 闸门臂（vendored 引擎 check --strict）
    os.makedirs(verdicts_dir, exist_ok=True)
    candidate_path = os.path.join(
        verdicts_dir, "discover.%s.candidate.json" % case_name)
    candidate, closure_trunc = _candidate_group(model, discovery)
    write_candidate_file(candidate_path, case_name, candidate)
    t_gate = time.monotonic()
    gate = run_engine_check(vendored_dir, model_path, candidate_path,
                            strict=True, timeout=timeout)
    gate_seconds = round(time.monotonic() - t_gate, 6)
    gate_row = {
        "candidate_group_file":
            "verdicts/discover.%s.candidate.json" % case_name,
        "candidate": {"kind": candidate["kind"],
                      "order": candidate["order"],
                      "closure_truncated": closure_trunc},
        "engine_check": {"exit": gate.get("exit"),
                         "verdict": gate.get("verdict"),
                         "worst_tv": gate.get("worst_tv"),
                         "judge": gate.get("judge"),
                         "reason": gate.get("reason"),
                         "error": gate.get("error"),
                         "command": gate.get("command"),
                         "cwd": gate.get("cwd"),
                         "strict": gate.get("strict")},
        "engine_group_order_reported":
            ((gate.get("payload") or {}).get("group") or {}).get("order"),
        "gate_seconds": gate_seconds,
    }

    # 对账（expected + 可选密封真值）与冒烟双方向
    reconciliation = _reconcile_all(cases_dir, model, case_dir, discovery)
    sealed = _reconcile_sealed(case_name, discovery, sealed_dir)
    smoke = _smoke_directions(case_name, model, discovery, reconciliation)

    # 剥离非序列化私有键后组装判决书
    discovery_out = {k: v for k, v in discovery.items()
                     if k != "_enumerated_set"}
    timing = dict(core["timing_seconds"])
    timing["gate_engine"] = gate_seconds

    verdict = {
        "case": case_name,
        "generated_utc": _utc_now(),
        "capability": {
            "name": "discover",
            "semantics": SEMANTICS_FIXED,
            "honesty_boundary": _HONESTY_BOUNDARY,
            "method": _METHOD_LINE,
            "cap": cap,
            "wall_clock_budget_s": budget_s,
        },
        "model": {
            "path": os.path.relpath(model_path, os.path.dirname(cases_dir)),
            "n_bits": model["n_bits"], "n_states": model["n_states"],
            "n_actions": model["n_actions"],
            "source_system": model["meta"].get("source_system"),
            "source_citation": model["meta"].get("source_citation"),
        },
        "discovery": discovery_out,
        "gate_arm": gate_row,
        "reconciliation": reconciliation,
        "sealed_truth": sealed,
        "smoke": smoke,
        "timing_seconds": timing,
        "provenance": {
            "recorded_from_live_run": True,
            "how": ("python -X utf8 -m symmetry_court discover [--case %s]; "
                    "the candidate group file is independently replayable: "
                    "python -X utf8 -m wuxing_gua check --trans "
                    "<cases>/<case>/model.json --group "
                    "verdicts/discover.%s.candidate.json --strict "
                    "(cwd=vendored/)" % (case_name, case_name)),
            "correctness_anchors": (
                "VF2 enumeration set-equal to S_n brute force and equal to "
                "field-trial sealed fixed_aut_order on the five n<=8 cases "
                "during bring-up (orders 1/2/1/6/24); the WL node_match "
                "pruning is sound because WL colors are "
                "automorphism-invariant"),
        },
    }
    out_path = os.path.join(verdicts_dir, "discover.%s.json" % case_name)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(verdict, ensure_ascii=False, indent=1) + "\n")
    return verdict, None

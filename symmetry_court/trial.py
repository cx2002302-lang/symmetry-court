# -*- coding: utf-8 -*-
"""
trial.py —— 三方庭审的核心机械

对一案（<cases-dir>/<name>/）执行：
  臂 1  wuxing-gua@relabel  : vendored 引擎 check（群文件被法庭盖 relabel 章，
                              引擎按声明分派到 relabel 家族判据）
  臂 2  wuxing-gua@fixed    : vendored 引擎 check --strict（--strict 覆盖声明为
                              fixed，= 动作名原样对应）
  臂 3  networkx 仲裁        : 对群内每个置换做
                              (a) 结构同构直接判定（边集代数，O(E)）
                              (b) 带事件标签同构直接判定
                              (c) networkx 匹配器独立复核（relabel+is_isomorphic）
                              (d) networkx 自同构枚举计数（全模型 / 非哑态子图，
                                  规模护栏内才跑，超出如实记 skipped）

判据实现零复用：引擎判据在 vendored/ 里（subprocess 调用）；networkx 仲裁是
独立实现（参考过上游 tcp_three_way.py 的思路，未 import 它的任何代码）。
"""

import json
import os
import subprocess
import sys
import tempfile

import networkx as nx

from . import REPO_ROOT, VENDORED_DIR, engine_env

# ---------------------------------------------------------------- 规模护栏
# 自同构枚举的节点数上限与计数上限：超出如实记 skipped/truncated，不硬跑。
AUTOS_ENUM_MAX_STATES = 64
AUTOS_ENUM_CAP = 200000
# 每群明细里逐元素记录的上限（超出只记计数）。
PER_ELEMENT_DETAIL_CAP = 64
# 引擎 subprocess 超时（秒）。
ENGINE_TIMEOUT_DEFAULT = 300

TV_FLOAT_TOL = 1e-12


class CaseError(Exception):
    """一案无法审理（模型/群文件缺失或非法）。"""


# ---------------------------------------------------------------- 装载
def load_model(path):
    """读模型 JSON（只为法庭自用：nx 建图与展示；引擎侧另做完整校验）。"""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    for key in ("n_bits", "n_actions", "trans"):
        if key not in raw:
            raise CaseError("模型缺少字段 %r：%s" % (key, path))
    n_bits, n_actions = raw["n_bits"], raw["n_actions"]
    trans = raw["trans"]
    n_states = 1 << n_bits
    if not isinstance(trans, list) or len(trans) != n_states:
        raise CaseError("trans 长度与 2**n_bits 不一致：%s" % path)
    meta = raw.get("meta") or {}
    action_names = meta.get("action_names") or meta.get("event_names")
    if not isinstance(action_names, list) or len(action_names) != n_actions:
        action_names = ["a%d" % a for a in range(n_actions)]
    return {"path": path, "raw": raw, "n_bits": n_bits,
            "n_actions": n_actions, "n_states": n_states,
            "trans": trans, "meta": meta, "action_names": action_names,
            "goals": raw.get("goals", [])}


def load_group(path):
    """读群 JSON（候选被告）。返回 (name, dict)。"""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict) or "elements" not in raw:
        raise CaseError("群文件缺 elements 字段：%s" % path)
    name = os.path.splitext(os.path.basename(path))[0]
    return name, raw


# ---------------------------------------------------------------- 建图
def build_graph(model):
    """
    模型 → nx.DiGraph。同一 (s,u) 上的多个事件聚合成排序元组存入
    attr "events"（DiGraph 不存平行边；带标签判定按事件集合比较，信息不丢）。
    """
    G = nx.DiGraph()
    G.add_nodes_from(range(model["n_states"]))
    events_by_edge = {}
    for s, row in enumerate(model["trans"]):
        for a, outcomes in enumerate(row):
            for outcome in outcomes:
                p, u = outcome[0], outcome[1]
                if float(p) <= 0.0:
                    continue
                events_by_edge.setdefault((s, u), set()).add(
                    model["action_names"][a])
    for (s, u), evs in events_by_edge.items():
        G.add_edge(s, u, events=tuple(sorted(evs)))
    return G, {e: frozenset(v) for e, v in events_by_edge.items()}


def structural_pad_states(model):
    """
    结构性哑态：每个动作都是「单后继自环 r=0」的行（与引擎 discover 的
    pad 哑态检测同一定义）。只用于给陪审团的计数加一个非哑态子图口径，
    不参与任何判决布尔——判决布尔只用全模型。
    """
    pads = []
    for s, row in enumerate(model["trans"]):
        pad_like = True
        for outcomes in row:
            if len(outcomes) != 1:
                pad_like = False
                break
            _p, u, r = outcomes[0][0], outcomes[0][1], outcomes[0][2]
            if u != s or float(r) != 0.0:
                pad_like = False
                break
        if pad_like:
            pads.append(s)
    return pads


# ---------------------------------------------------------------- 陪审团
def perm_direct_check(events_by_edge, p):
    """给定置换 p 的直接判定（边集代数，O(E)）：(结构同构, 带标签同构)。"""
    structural = True
    labeled = True
    for (s, u), evs in events_by_edge.items():
        if (p[s], p[u]) not in events_by_edge:
            structural = False
            labeled = False
            break
        if events_by_edge[(p[s], p[u])] != evs:
            labeled = False
    return structural, labeled


def enumerate_automorphisms(G, labeled, n_states):
    """
    networkx VF2 枚举自同构集（自同构 = G 到自身的同构映射）。
    返回 (成员集|None, 计数, truncated, skip原因|None)。
    成员集用于「给定置换是否在枚举出的自同构集合里」的独立复核——
    注意不能用 is_isomorphic(G, π(G)) 复核：π: G→π(G) 永远是同构，
    那样问出来的恒真，没有证据力（本仓曾在冒烟中被此坑过，记录在案）。
    """
    if n_states > AUTOS_ENUM_MAX_STATES:
        return None, None, False, ("n_states>%d, automorphism enumeration "
                                   "skipped" % AUTOS_ENUM_MAX_STATES)
    em = (lambda a, b: a["events"] == b["events"]) if labeled else None
    GM = nx.algorithms.isomorphism.DiGraphMatcher(G, G, edge_match=em)
    members = set()
    count = 0
    truncated = False
    try:
        for mapping in GM.isomorphisms_iter():
            members.add(tuple(mapping[i] for i in range(n_states)))
            count += 1
            if count >= AUTOS_ENUM_CAP:
                truncated = True
                break
    except Exception as e:  # noqa: BLE001 陪审团内部异常不掩埋
        return None, None, False, "enumerator error: %r" % (e,)
    return members, count, truncated, None


def networkx_arm(model, group_raw):
    """臂 3：networkx 仲裁（对给定群的每个置换做结构/带标签判定）。

    主判定 = 直接边集代数（O(E)，可手工验算）；独立复核 = networkx VF2
    自同构枚举的成员资格（规模护栏内才跑；截断时复核记 inconclusive）。
    两种方法矛盾 = 陪审团内部不一致，记入 method_conflicts（arbitrate 视为
    审理失败，fail loud）。
    """
    G, events_by_edge = build_graph(model)
    elements = group_raw["elements"]
    uniq = sorted({tuple(e) for e in elements})
    n_nontrivial = sum(1 for e in uniq if list(e) != list(range(len(e))))

    members_s, n_s, tr_s, skip_s = enumerate_automorphisms(
        G, labeled=False, n_states=model["n_states"])
    members_l, n_l, tr_l, skip_l = enumerate_automorphisms(
        G, labeled=True, n_states=model["n_states"])

    detail = []
    struct_flags, labeled_flags = [], []
    method_conflicts = []
    for idx, e in enumerate(uniq):
        p = list(e)
        is_id = (p == list(range(len(p))))
        s_direct, l_direct = perm_direct_check(events_by_edge, p)
        # 独立复核：p 是否在 VF2 枚举出的自同构集合里
        if members_s is not None and not tr_s:
            m_s = tuple(p) in members_s
        else:
            m_s = None
        if members_l is not None and not tr_l:
            m_l = tuple(p) in members_l
        else:
            m_l = None
        for kind, direct, member in (("structural", s_direct, m_s),
                                     ("labeled", l_direct, m_l)):
            if member is not None and member != direct:
                method_conflicts.append(
                    {"element_index": idx, "kind": kind,
                     "direct_edge_check": direct, "nx_vf2_membership": member})
        struct_flags.append(is_id or s_direct)
        labeled_flags.append(is_id or l_direct)
        if len(detail) < PER_ELEMENT_DETAIL_CAP:
            detail.append({
                "element": p, "is_identity": is_id,
                "structural": s_direct, "labeled": l_direct,
                "nx_vf2_membership_structural": m_s,
                "nx_vf2_membership_labeled": m_l,
            })

    res = {
        "structure_symmetry": all(struct_flags),
        "labeled_symmetry": all(labeled_flags),
        "n_elements": len(elements),
        "n_unique_elements": len(uniq),
        "n_nontrivial": n_nontrivial,
        "per_element": detail,
        "per_element_truncated": len(uniq) > PER_ELEMENT_DETAIL_CAP,
        "method": ("primary=direct edge-set check (O(E), hand-checkable); "
                   "cross-check=networkx VF2 automorphism-set membership "
                   "(independent implementation)"),
        "method_conflicts": method_conflicts,
        "crosscheck_status": ("ok" if (members_s is not None and members_l is
                                       not None and not tr_s and not tr_l)
                              else ("skipped: %s" % (skip_s or skip_l)
                                    if (skip_s or skip_l) else
                                    "inconclusive: enumeration truncated at cap")),
        "scope": "full model (all n_states=%d, padding included)" % model["n_states"],
    }

    # 自同构计数：全模型口径已在上方枚举；此处只补非哑态子图口径
    # （哑态=全动作自环 r=0 行，与引擎 pad-aware 模式同一检测规则）。
    res["n_autos_structure"] = n_s
    res["n_autos_labeled"] = n_l
    res["autos_truncated"] = bool(tr_s or tr_l)
    res["autos_skipped_reason"] = skip_s or skip_l

    pads = structural_pad_states(model)
    res["structural_pad_states"] = pads
    pad_set = set(pads)
    real = [s for s in range(model["n_states"]) if s not in pad_set]
    # 真态行引用哑态时子图口径不适用（会丢边），如实跳过。
    refs_pad = any(outcome[1] in pad_set
                   for s in real
                   for outcomes in model["trans"][s]
                   for outcome in outcomes)
    if pads and not refs_pad and real:
        G_sub = G.subgraph(real).copy()
        _mem_s, cnt_s, _tr_s, _sk_s = enumerate_automorphisms(
            G_sub, labeled=False, n_states=len(real))
        _mem_l, cnt_l, _tr_l, _sk_l = enumerate_automorphisms(
            G_sub, labeled=True, n_states=len(real))
        res["n_autos_structure_nonpad"] = cnt_s
        res["n_autos_labeled_nonpad"] = cnt_l
        res["autos_nonpad_scope"] = ("subgraph over the %d non-pad states "
                                     "(structural pads excluded; a pad state = "
                                     "every action single self-loop successor "
                                     "with r=0, the same rule the engine's "
                                     "pad-aware mode uses)" % len(real))
    else:
        res["n_autos_structure_nonpad"] = None
        res["n_autos_labeled_nonpad"] = None
        res["autos_nonpad_scope"] = ("not applicable (no structural pads, or real "
                                     "rows reference pad states)")
    return res


# ---------------------------------------------------------------- 引擎臂
def _sanitize(obj, workdir=None):
    """
    脱敏（宪法③：落盘文件零本地路径）：把记录里出现的
      · 解释器绝对路径   -> "python"
      · 仓库根绝对路径   -> ""
      · 庭审临时目录     -> "<court_tmp>"
    递归处理 str/list/dict（注意必须先在原始字符串上替换，不能在 JSON
    转义文本上替换——反斜杠会被转义成 \\\\ 而匹配不上）。
    """
    reps = [(sys.executable, "python")]
    root = REPO_ROOT.rstrip("\\/") + os.sep
    reps.append((root, ""))
    reps.append((REPO_ROOT, "<repo>"))
    if workdir:
        reps.append((workdir, "<court_tmp>"))

    def clean(s):
        for old, new in reps:
            s = s.replace(old, new)
        return s

    if isinstance(obj, str):
        return clean(obj)
    if isinstance(obj, list):
        return [_sanitize(x, workdir) for x in obj]
    if isinstance(obj, dict):
        return {k: _sanitize(v, workdir) for k, v in obj.items()}
    return obj


def run_engine_check(vendored_dir, model_path, group_path, strict, timeout,
                     workdir=None):
    """
    经 subprocess 调 vendored 引擎：python -X utf8 -m wuxing_gua check。
    cwd=vendored（保证解析的是本仓的引擎副本，而非机器上可能过期的安装版）；
    PYTHONDONTWRITEBYTECODE=1（vendored 树保持字节原始）。
    返回 dict（exit/verdict/worst_tv/judge/semantics/reason/payload/error）。
    判决记录里的路径一律相对化（落盘零本地路径）。
    """
    cmd = [sys.executable, "-X", "utf8", "-m", "wuxing_gua", "check",
           "--trans", os.path.abspath(model_path),
           "--group", os.path.abspath(group_path)]
    if strict:
        cmd.append("--strict")
    rec = {"command": _sanitize(cmd, workdir), "cwd": "vendored/",
           "strict": bool(strict)}
    try:
        proc = subprocess.run(cmd, cwd=vendored_dir, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, env=engine_env())
    except subprocess.TimeoutExpired:
        rec["error"] = "engine timeout after %ss" % timeout
        return rec
    rec["exit"] = proc.returncode
    rec["stderr_tail"] = _sanitize((proc.stderr or "")[-2000:], workdir)
    payload = None
    try:
        payload = json.loads(proc.stdout)
    except ValueError:
        rec["error"] = "engine stdout not parseable JSON (exit=%s)" % proc.returncode
        return rec
    rec["payload"] = payload
    rec["verdict"] = payload.get("verdict")
    lt = payload.get("layer_transition") or {}
    rec["worst_tv"] = lt.get("worst_tv")
    sem = payload.get("semantics") or {}
    rec["judge"] = sem.get("judge")
    rec["semantics"] = sem
    rec["reason"] = payload.get("reason")
    # 引擎自己报的 exit_code 与进程返回码不一致 = 异常，如实记录
    if payload.get("exit_code") is not None and payload["exit_code"] != proc.returncode:
        rec["error"] = ("engine payload exit_code=%r != process returncode %r"
                        % (payload.get("exit_code"), proc.returncode))
    return rec


def stamped_relabel_copy(group_raw):
    """
    臂 1 用的「relabel 章」副本：semantics.action 强制为 relabel（原声明保留
    在判决记录里）。引擎对未知键宽容，note 说明盖章来历。
    """
    stamped = json.loads(json.dumps(group_raw))  # 深拷贝
    stamped["semantics"] = {
        "action": "relabel",
        "note": ("court-stamped relabel frame for the wuxing-gua@relabel column; "
                 "the group file's own declaration (if any) is preserved in the "
                 "verdict record, not in this copy"),
    }
    return stamped


# ---------------------------------------------------------------- 一群的庭审
def _row_from_engine(rec):
    """引擎臂记录 → 判决表行（契约字段 exit/verdict/worst_tv/judge + 附件）。"""
    return {
        "exit": rec.get("exit"),
        "verdict": rec.get("verdict"),
        "worst_tv": rec.get("worst_tv"),
        "judge": rec.get("judge"),
        "error": rec.get("error"),
        "reason": rec.get("reason"),
        "semantics": rec.get("semantics"),
        "command": rec.get("command"),
        "stderr_tail": rec.get("stderr_tail"),
    }


def _consistency(relabel_row, fixed_row, nx_res, declared_action):
    """
    一致性判语。口径内配对：
      relabel 臂(引擎) ↔ structure 列(networkx)   —— 两者都答「只看结构行不行」
      fixed 臂(引擎)   ↔ labeled 列(networkx)     —— 两者都答「钉住事件名行不行」
    ruling_code ∈ agree / semantics_duality / disagree / error
    """
    if relabel_row.get("error") or fixed_row.get("error") \
            or relabel_row.get("verdict") is None or fixed_row.get("verdict") is None:
        return {"relabel_vs_structure": None, "fixed_vs_labeled": None,
                "arms_differ": None, "ruling_code": "error",
                "ruling": "engine arm failed; no consistency ruling",
                "binding_verdict": None}

    rel_pass = (relabel_row["verdict"] == "pass")
    fix_pass = (fixed_row["verdict"] == "pass")
    pair_a = (rel_pass == bool(nx_res["structure_symmetry"]))
    pair_b = (fix_pass == bool(nx_res["labeled_symmetry"]))
    arms_differ = (relabel_row["verdict"] != fixed_row["verdict"])

    binding = None
    if declared_action == "relabel":
        binding = relabel_row["verdict"]
    elif declared_action in ("fixed", "explicit"):
        binding = fixed_row["verdict"]

    if pair_a and pair_b and not arms_differ:
        code = "agree"
        ruling = ("all columns agree: engine (both standards) and networkx "
                  "(both scopes) say %r for this group" % relabel_row["verdict"])
    elif pair_a and pair_b and arms_differ:
        code = "semantics_duality"
        ruling = ("the two engine standards disagree (relabel=%s / fixed=%s) and "
                  "networkx mirrors the split exactly (structure=%s / labeled=%s); "
                  "each column is consistent with the standard it answers under; "
                  "the group file declares semantics=%r, so the binding column is "
                  "wuxing-gua@%s -> %s"
                  % (relabel_row["verdict"], fixed_row["verdict"],
                     nx_res["structure_symmetry"], nx_res["labeled_symmetry"],
                     declared_action,
                     "relabel" if declared_action == "relabel" else "fixed",
                     binding if binding else "n/a (explicit)"))
    else:
        code = "disagree"
        ruling = ("column disagreement: engine@relabel=%s vs nx@structure=%s "
                  "(pair %s); engine@fixed=%s vs nx@labeled=%s (pair %s) — "
                  "recorded as a finding, not smoothed over"
                  % (relabel_row["verdict"], nx_res["structure_symmetry"],
                     "consistent" if pair_a else "INCONSISTENT",
                     fixed_row["verdict"], nx_res["labeled_symmetry"],
                     "consistent" if pair_b else "INCONSISTENT"))
    return {"relabel_vs_structure": "agree" if pair_a else "disagree",
            "fixed_vs_labeled": "agree" if pair_b else "disagree",
            "arms_differ": arms_differ,
            "ruling_code": code, "ruling": ruling,
            "binding_verdict": binding}


def try_group(model, group_name, group_raw, workdir, timeout, vendored_dir):
    """一群的三方庭审 → dict（判决书里该群的完整记录）。"""
    declared = (group_raw.get("semantics") or {})
    declared_action = declared.get("action")

    # 臂 1：relabel 章（若群已声明 relabel 则用原文件，不盖章）
    if declared_action == "relabel":
        rec_rel = run_engine_check(vendored_dir, model["path"],
                                   _group_src_path(group_raw), False, timeout,
                                   workdir=workdir)
        stamp_note = "group already declares relabel; original file used as-is"
    else:
        stamped = stamped_relabel_copy(group_raw)
        stamped_path = os.path.join(workdir, "%s.relabel.json" % group_name)
        with open(stamped_path, "w", encoding="utf-8", newline="") as f:
            f.write(json.dumps(stamped, ensure_ascii=False, indent=1) + "\n")
        rec_rel = run_engine_check(vendored_dir, model["path"], stamped_path,
                                   False, timeout, workdir=workdir)
        stamp_note = ("court-stamped relabel copy used (original declaration: %r)"
                      % declared_action)
    relabel_row = _row_from_engine(rec_rel)
    relabel_row["frame"] = "relabel"
    relabel_row["stamp_note"] = stamp_note

    # 臂 2：fixed（--strict 覆盖声明为 fixed；群原文件不动）
    rec_fix = run_engine_check(vendored_dir, model["path"],
                               _group_src_path(group_raw), True, timeout,
                               workdir=workdir)
    fixed_row = _row_from_engine(rec_fix)
    fixed_row["frame"] = "fixed"
    fixed_row["stamp_note"] = "original group file, --strict flag (fixed frame)"

    # 臂 3：networkx
    nx_res = networkx_arm(model, group_raw)

    cons = _consistency(relabel_row, fixed_row, nx_res, declared_action)
    return {
        "group_file": "groups/%s.json" % group_name,
        "declared_semantics": declared if declared else None,
        "claim": (group_raw.get("meta") or {}).get("claim"),
        "order_engine_reported": ((rec_rel.get("payload") or {}).get("group")
                                  or {}).get("order"),
        "relabel": relabel_row,
        "fixed": fixed_row,
        "networkx": nx_res,
        "consistency": cons,
    }


def _group_src_path(group_raw):
    """群原文件路径（装载时记在 raw 里的内部键，不进输出）。"""
    return group_raw.get("_src_path")


# ---------------------------------------------------------------- 一案的庭审
def try_case(cases_dir, case_name, timeout=ENGINE_TIMEOUT_DEFAULT,
             vendored_dir=VENDORED_DIR):
    """一案的三方庭审 → (verdict_dict|None, error_message|None)。"""
    case_dir = os.path.join(cases_dir, case_name)
    model_path = os.path.join(case_dir, "model.json")
    if not os.path.isfile(model_path):
        return None, "model.json not found in %s" % case_dir
    if not os.path.isdir(vendored_dir):
        return None, "vendored engine dir not found: %s" % vendored_dir
    groups_dir = os.path.join(case_dir, "groups")
    group_files = []
    if os.path.isdir(groups_dir):
        group_files = sorted(
            fn for fn in os.listdir(groups_dir) if fn.endswith(".json"))
    if not group_files:
        return None, "no group files under %s" % groups_dir

    try:
        model = load_model(model_path)
    except (OSError, ValueError) as e:
        return None, "model.json unreadable: %s" % e
    model["path"] = model_path

    groups_out = {}
    errors = []
    with tempfile.TemporaryDirectory(prefix="symmetry_court_") as workdir:
        for fn in group_files:
            gpath = os.path.join(groups_dir, fn)
            try:
                name, group_raw = load_group(gpath)
            except (OSError, ValueError) as e:
                errors.append({"group": fn, "error": "group file unreadable: %s" % e})
                continue
            group_raw["_src_path"] = gpath
            try:
                groups_out[name] = try_group(model, name, group_raw, workdir,
                                             timeout, vendored_dir)
            except CaseError as e:
                errors.append({"group": name, "error": str(e)})

    verdict = {
        "case": case_name,
        "generated_utc": _utc_now(),
        "tools": _tools_block(vendored_dir),
        "model": {
            "path": os.path.relpath(model_path, os.path.dirname(cases_dir)),
            "n_bits": model["n_bits"], "n_states": model["n_states"],
            "n_actions": model["n_actions"],
            "source_system": model["meta"].get("source_system"),
            "source_citation": model["meta"].get("source_citation"),
        },
        "groups": groups_out,
        "group_errors": errors,
        "rollup": _rollup(groups_out, errors),
    }
    return verdict, None


def _utc_now():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tools_block(vendored_dir):
    version = None
    try:
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "wuxing_gua", "--version"],
            cwd=vendored_dir, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=60, env=engine_env())
        version = (proc.stdout or "").strip()
    except Exception:  # noqa: BLE001
        version = None
    return {
        "engine": {
            "name": "wuxing_gua", "version": version,
            "location": "vendored/wuxing_gua",
            "provenance": "pinned source revision + sha256 manifest in NOTICE",
            "invocation": ("python -X utf8 -m wuxing_gua check --trans <model> "
                           "--group <group> [--strict]; cwd=vendored/; "
                           "PYTHONDONTWRITEBYTECODE=1"),
        },
        "networkx": nx.__version__,
        "python": sys.version.split()[0],
    }


def _rollup(groups_out, errors):
    codes = {"agree": 0, "semantics_duality": 0, "disagree": 0, "error": 0}
    for g in groups_out.values():
        c = g["consistency"]["ruling_code"]
        codes[c] = codes.get(c, 0) + 1
    return {
        "groups": len(groups_out),
        "group_errors": len(errors),
        "ruling_codes": {k: v for k, v in codes.items() if v},
        "all_consistent_pairs": bool(groups_out) and not errors and all(
            g["consistency"]["relabel_vs_structure"] == "agree"
            and g["consistency"]["fixed_vs_labeled"] == "agree"
            for g in groups_out.values()),
    }

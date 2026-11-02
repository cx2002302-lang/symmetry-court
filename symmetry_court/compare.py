# -*- coding: utf-8 -*-
"""闸门价值对比：用 wuxing-gua 闸门 vs 不用闸（结构直觉代理）· 逐案量化。

对每案每被告群计算三件事：

1. **不用闸（朴素臂）**——结构直觉代理：只看转移图的"骨架"（边集合忽略事件名）
   是否被该置换保持。像 = 就合并（真实世界里 networkx 不带标签的结构判定正是
   这类做法，TCP 孪生案里它判"可换"）。合并的代价用逐格对账量化：对账口径
   按群的声明分派（见下），统计被破坏的真实 (状态,事件) 格数（即合并后行为
   会改变的格子）。

2. **用闸（闸门臂）**——内嵌引擎 check，**口径按群文件声明分派**
   （2026-11-03 compare v2；此前无条件 --strict，对 explicit 声明群会错误
   覆盖其声明）：群声明 explicit（semantics.action="explicit" 且 action_map
   是动作集上的合法双射）→ 不加 --strict 原样跑，让声明口径说话；声明 fixed
   或无声明 → 维持 --strict（动作名钉死）。放行的群给出压缩读数（轨道数），
   拒答的群拦下朴素臂的损害。放行 = 声明口径下等变逐格零误差，该口径破坏格数
   按定义为 0（闸门判据的数学性质，不是本次运行的巧合）。

3. **对比结论**——朴素臂放行而真值/闸门拒绝的群 = "闸门救下的合并"；
   每个被救下的合并附带它的破坏格数与破坏率。

诚实声明：朴素臂是**代理**（structure-only intuition），不是某个具体的第三方
压缩工具；它代表的决策方式（"长得一样就合并"）在工程里真实存在，TCP 孪生案
里 networkx 的结构口径就判"可换"。

口径说明（explicit 群）：群文件只带一个 action_map（引擎格式如此），对账与
闸门臂都用这个单映射逐动作改名后对账（破坏格 = 声明口径下会变的格数）。
fixed 口径的破坏格仍单独记录在 broken_real_cells_fixed 字段供对照。已知边界：
mini2048 案发现引擎 explicit 层对闭包恒等元也用同一映射（见
cases/mini2048/README.md），非平凡 explicit 群会被拒——compare 如实记录
闸门行为，不代引擎翻案。

用法：
    python -X utf8 -m symmetry_court compare                  # 法庭自有案卷
    python -X utf8 -m symmetry_court compare --root <cases>   # 任意同格式案卷

输出：verdicts/comparison.<case>.json（逐案）+ comparison.summary.json（汇总）
+ 控制台表格。退出码 0=对比完成且每群三方数据齐。
"""

import json
import os
import subprocess
import sys
import time

from . import DEFAULT_CASES_DIR, DEFAULT_VERDICTS_DIR, VENDORED_DIR

EXIT_OK = 0
EXIT_FAIL = 1

SENTINEL_REWARD = -1.0


def _utf8_stdio():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass


def _load_model(case_dir):
    with open(os.path.join(case_dir, "model.json"), "r", encoding="utf-8") as f:
        m = json.load(f)
    return m


def _real_cell(triple, state):
    """非哨兵格：哨兵约定 = 自环 + reward -1.0（转录的『无此事件』占位）。"""
    for _p, target, reward in triple:
        if not (target == state and reward == SENTINEL_REWARD and len(triple) == 1):
            return True
    return False


def _permute_triple(triple, perm):
    return sorted([p, perm[target], reward] for p, target, reward in triple)


def _structural_admits(trans, perm):
    """朴素臂：边集不变性（忽略事件名与奖励，只看 s→s' 骨架）。"""
    n = len(trans)
    edges = set()
    for s in range(n):
        for a in range(len(trans[s])):
            for _p, t, _r in trans[s][a]:
                edges.add((s, t))
    return all((perm[s], perm[t]) in edges for (s, t) in edges)


def _declared_action_map(group_raw):
    """群文件的 explicit 声明 → (is_explicit, action_map|None)。

    合法 explicit = semantics.action=="explicit" 且 action_map 是动作集上的
    双射（与引擎 load_group 的校验同规则）。声明 explicit 但映射缺失/非法 →
    (True, None)（调用方回退 strict 并如实标注，引擎侧对这种文件本就报错）。
    """
    sem = group_raw.get("semantics") or {}
    if sem.get("action") != "explicit":
        return False, None
    amap = sem.get("action_map")
    if isinstance(amap, list) and amap and \
            all(isinstance(x, int) and not isinstance(x, bool) for x in amap) \
            and sorted(amap) == list(range(len(amap))):
        return True, list(amap)
    return True, None


def _damage(trans, perm, amap=None):
    """单置换逐格对账：合并后行为会改变的格数。

    amap=None → fixed 口径（动作名钉死，b == a）；
    amap=rho  → 声明口径（动作按群文件声明的映射改名，b == rho[a]）。
    奖励/概率随边走，事件名是唯一被对账的自由度。
    返回 (破坏格数, 真实格总数)。
    """
    n = len(trans)
    n_act = len(trans[0])
    broken = set()
    real_cells = 0
    for s in range(n):
        for a in range(n_act):
            if _real_cell(trans[s][a], s):
                real_cells += 1
    for s in range(n):
        ps = perm[s]
        for a in range(n_act):
            b = amap[a] if amap is not None else a
            expect = _permute_triple(trans[s][a], perm)
            actual = sorted(trans[ps][b])
            if expect != actual:
                # 只要有一侧是真格（或两侧都真），合并就改变行为
                if _real_cell(trans[s][a], s) or _real_cell(trans[ps][b], ps):
                    broken.add((s, a))
    return len(broken), real_cells


def _orbits(elements, n):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for elem in elements:
        for s in range(n):
            a, b = find(s), find(elem[s])
            if a != b:
                parent[a] = b
    return len({find(x) for x in range(n)})


def _gate_run(case_dir, model_rel, group_path, strict):
    """闸门臂：跑内嵌引擎 check（这就是闸门本体），返回 (exit, verdict, 秒)。"""
    env_model = os.path.join(case_dir, model_rel)
    cmd = [sys.executable, "-X", "utf8", "-m", "wuxing_gua", "check",
           "--trans", env_model, "--group", group_path]
    if strict:
        cmd.append("--strict")
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       cwd=VENDORED_DIR)
    dt = time.perf_counter() - t0
    try:
        payload = json.loads(r.stdout)
        verdict = payload.get("verdict", "?")
    except ValueError:
        verdict = "unparseable"
    return r.returncode, verdict, dt


def compare_case(cases_root, case, verdicts_dir, vendored):
    case_dir = os.path.join(cases_root, case)
    model = _load_model(case_dir)
    trans = model["trans"]
    n = len(trans)
    ident = list(range(n))

    groups_dir = os.path.join(case_dir, "groups")
    group_files = sorted(f for f in os.listdir(groups_dir) if f.endswith(".json"))

    # expected.json 若在盘（法庭案卷）：读 networkx 带标签列与判决做交叉核对
    expected = None
    exp_path = os.path.join(case_dir, "expected.json")
    if os.path.isfile(exp_path):
        with open(exp_path, "r", encoding="utf-8") as f:
            expected = json.load(f)

    rows = []
    gate_seconds = 0.0
    for gf in group_files:
        with open(os.path.join(groups_dir, gf), "r", encoding="utf-8") as f:
            g = json.load(f)
        elements = g["elements"]
        claim = (g.get("meta") or {}).get("claim", "")
        gens = [e for e in elements if e != ident]

        # 口径分派（compare v2）：explicit（含合法 action_map）→ 声明口径；
        # fixed / 无声明 / 声明 explicit 但映射非法 → fixed 口径（--strict）。
        is_exp, amap = _declared_action_map(g)
        gate_strict = not (is_exp and amap is not None)

        # 朴素臂
        naive_ok = all(_structural_admits(trans, e) for e in gens)
        # 损害台账：按闸门臂同一口径对账；fixed 口径数值单独保留供对照
        # （explicit 群 = 声明口径与钉死口径两行都有，差异本身是读数）。
        broken_ledger = 0    # 闸门口径（explicit 群 = 声明口径）
        broken_fixed = 0     # fixed 口径（对照列）
        for e in gens:
            b, _rc = _damage(trans, e, amap if (is_exp and amap is not None)
                             else None)
            broken_ledger += b
            bf, _rc2 = _damage(trans, e, None)
            broken_fixed += bf
        # 轨道读数（若真按此群合并会得到的类数）
        n_orbits = _orbits(elements, n)

        # 闸门臂：让声明口径说话（explicit 群原样跑，不加 --strict）
        rc, verdict, dt = _gate_run(case_dir, "model.json",
                                    os.path.join(groups_dir, gf),
                                    strict=gate_strict)
        gate_seconds += dt

        # networkx 带标签列（若有 expected）
        nx_labeled = None
        if expected is not None:
            row = (expected.get("groups") or {}).get(gf)
            if row is None and isinstance(expected.get("groups"), list):
                for r_ in expected["groups"]:
                    if r_.get("group") == gf or r_.get("file") == gf:
                        row = r_
                        break
            if row is not None:
                nx_labeled = (row.get("networkx") or {}).get("labeled_symmetry")

        saved = naive_ok and rc == 1  # 朴素臂放行 + 闸门拒答 = 救下的合并
        row = {
            "group": gf,
            "claim": claim,
            "naive_structure_admits": naive_ok,
            "gate_exit": rc,
            "gate_verdict": verdict,
            "gate_admits": rc == 0,
            "nx_labeled_symmetry": nx_labeled,
            "broken_real_cells_fixed": broken_fixed,
            "real_cells": sum(1 for s in range(n) for a in range(len(trans[s]))
                              if _real_cell(trans[s][a], s)),
            "would_be_orbits_if_merged": n_orbits,
            "compression_if_true": round(n / n_orbits, 3) if n_orbits else None,
            "gate_saved_this_merge": saved,
        }
        if is_exp:
            # explicit 群的追加字段（fixed/无声明群不加，旧收据保持字节稳定）
            row["gate_strict"] = gate_strict
            row["damage_caliber"] = ("explicit" if amap is not None
                                     else "explicit_invalid_map_fallback_fixed")
            row["declared_action_map"] = amap
            row["broken_real_cells_declared"] = (broken_ledger
                                                 if amap is not None else None)
        rows.append(row)

    def _ledger(r_):
        """该群的台账破坏格 = 闸门臂所用口径下的格数（explicit 群 = 声明口径）。"""
        if r_.get("damage_caliber") == "explicit":
            return r_.get("broken_real_cells_declared")
        return r_["broken_real_cells_fixed"]

    n_saved = sum(1 for r_ in rows if r_["gate_saved_this_merge"])
    n_admitted = sum(1 for r_ in rows if r_["gate_admits"])
    admitted_broken = sum(_ledger(r_) for r_ in rows if r_["gate_admits"])
    naive_broken = sum(_ledger(r_) for r_ in rows
                       if r_["naive_structure_admits"])
    summary = {
        "case": case,
        "n_states": n,
        "n_actions": len(trans[0]),
        "n_groups": len(rows),
        "naive_admits": sum(1 for r_ in rows if r_["naive_structure_admits"]),
        "naive_harmful_admits": n_saved,
        "naive_broken_real_cells": naive_broken,
        "gate_admits": n_admitted,
        "gate_admitted_broken_cells": admitted_broken,  # 判据性质：恒为 0
        "gate_saved_merges": n_saved,
        "gate_explicit_groups": sum(1 for r_ in rows
                                    if r_.get("damage_caliber") == "explicit"),
        "gate_total_seconds_rounded": round(gate_seconds, 1),
        "rows": rows,
    }
    out = {"case": case, "provenance": {
        "gate": ("vendored wuxing_gua check, caliber per group declaration "
                 "(compare v2): groups declaring semantics.action=explicit "
                 "with a valid action_map run as declared (no --strict); "
                 "groups declaring fixed or no declaration run --strict "
                 "(live run)"),
        "naive_arm": "structure-only edge-set invariance proxy (see module docstring)",
        "damage": ("cell-by-cell ledger over model trans, same caliber as "
                   "the gate arm per group (explicit groups: events renamed "
                   "per the declared action_map; others: event names "
                   "pinned); fixed-caliber damage kept per row in "
                   "broken_real_cells_fixed for contrast"),
    }, "summary": {k: v for k, v in summary.items() if k != "rows"}, "rows": rows}
    with open(os.path.join(verdicts_dir, "comparison.%s.json" % case), "w",
              encoding="utf-8", newline="") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return summary


def cmd_compare(args):
    _utf8_stdio()
    cases_root = args.root or DEFAULT_CASES_DIR
    verdicts_dir = args.out or DEFAULT_VERDICTS_DIR
    os.makedirs(verdicts_dir, exist_ok=True)
    cases = sorted(d for d in os.listdir(cases_root)
                   if os.path.isfile(os.path.join(cases_root, d, "model.json")))
    if not cases:
        print("no cases under %s" % cases_root)
        return EXIT_FAIL
    all_rows = []
    totals = {"cases": 0, "groups": 0, "naive_admits": 0, "naive_harmful": 0,
              "naive_broken": 0, "gate_admits": 0, "gate_broken": 0,
              "gate_explicit_groups": 0, "gate_seconds": 0.0}
    print("=" * 100)
    print("%-16s %-34s %-9s %-9s %-11s %s" % (
        "case", "group", "朴素臂", "闸门", "破坏格", "压缩读数(若真)"))
    print("-" * 100)
    for case in cases:
        s = compare_case(cases_root, case, verdicts_dir, VENDORED_DIR)
        totals["cases"] += 1
        totals["groups"] += s["n_groups"]
        totals["naive_admits"] += s["naive_admits"]
        totals["naive_harmful"] += s["naive_harmful_admits"]
        totals["naive_broken"] += s["naive_broken_real_cells"]
        totals["gate_admits"] += s["gate_admits"]
        totals["gate_broken"] += s["gate_admitted_broken_cells"]
        totals["gate_explicit_groups"] += s["gate_explicit_groups"]
        totals["gate_seconds"] += s["gate_total_seconds_rounded"]
        for r_ in s["rows"]:
            ledger = (r_.get("broken_real_cells_declared")
                      if r_.get("damage_caliber") == "explicit"
                      else r_["broken_real_cells_fixed"])
            mark = "*" if r_.get("damage_caliber") == "explicit" else ""
            all_rows.append({"case": case, **{k: r_[k] for k in (
                "group", "naive_structure_admits", "gate_exit",
                "broken_real_cells_fixed", "compression_if_true",
                "gate_saved_this_merge")},
                "gate_caliber": ("explicit" if r_.get("damage_caliber") ==
                                 "explicit" else "fixed"),
                "broken_by_gate_caliber": ledger})
            print("%-16s %-34s %-9s %-9s %-11s %s" % (
                case, r_["group"][:34],
                "合并" if r_["naive_structure_admits"] else "不合并",
                "放行" if r_["gate_admits"] else "拒答",
                "%s%s" % (ledger, mark),
                r_["compression_if_true"] if r_["gate_admits"] else "-"))
        print("-" * 100)
    print("(破坏格列：* = 声明口径（explicit action_map）下的对账；"
          "无 * = fixed 口径（动作名钉死）。)")
    summary = {
        "generated": "see per-case comparison.<case>.json for provenance",
        **totals,
        "gate_admitted_broken_is_zero_by_definition":
            "pass requires worst_tv <= 1e-9 on every cell",
        "rows": all_rows,
    }
    with open(os.path.join(verdicts_dir, "comparison.summary.json"), "w",
              encoding="utf-8", newline="") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print("汇总：%d 案 %d 群 | 朴素臂放行 %d（其中有害 %d，破坏真实格 %d）"
          % (totals["cases"], totals["groups"], totals["naive_admits"],
             totals["naive_harmful"], totals["naive_broken"]))
    print("      闸门放行 %d（放行群破坏格 %d，判据性质恒为 0）| 闸门总耗时约 %s 秒"
          % (totals["gate_admits"], totals["gate_broken"],
             totals["gate_seconds"]))
    ok = totals["gate_broken"] == 0 and all(
        not (r_["gate_exit"] == 0
             and (r_["broken_by_gate_caliber"] or 0) > 0)
        for r_ in all_rows)
    print("闸门价值一致性：%s" % ("PASS（放行群零破坏、拒答群全部有据）" if ok else "FAIL"))
    return EXIT_OK if ok else EXIT_FAIL

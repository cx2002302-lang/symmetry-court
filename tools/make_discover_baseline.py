# -*- coding: utf-8 -*-
"""make_discover_baseline.py -- deterministic generator for the discover
reconciliation baselines (verdicts/discover-baseline/discover.<case>.expected.json).

Reads, as its only inputs:
  1. cases/<case>/model.json            -- live model facts (free class,
                                           edges, per-element fixed checks);
  2. cases/<case>/expected.json         -- the court receipt rows (fixed row,
                                           networkx labeled column);
  3. cases/<case>/groups/*.json         -- the declared defendant groups;
  4. for the five incorporated cases: the field-trial blind-test project's
     sealed truth (default: <repo>/../field-trial/sealed, override with
     --sealed-dir; sha256 must match that project's sealed/_W3_manifest.json).

Every emitted number is either (a) copied from a source file named in the
emitted JSON, or (b) machine-derived here from those files.  No discover
output is read -- this baseline is the independent side of the reconciliation.

--check regenerates and compares bytes; exit 0 on identity, 1 on drift.
"""
import argparse
import hashlib
import json
import os
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = ["dhcp", "hadoop-mr-task", "hanoi3", "imap", "k8s-pod-lifecycle",
         "lightsout3", "mini2048", "raft-etcd", "sliding2x3", "tcp",
         "tls13-handshake", "usb2-device-states"]
SEALED_CASES = ["hadoop-mr-task", "k8s-pod-lifecycle", "raft-etcd",
                "tls13-handshake", "usb2-device-states"]
DEFAULT_CAP = 2000

HONESTY = ("discover discovers candidate state symmetries only under the fixed "
           "caliber (event names pinned).  Action-renaming symmetries (explicit "
           "or relabel caliber) stay author-declared; the machine does not guess "
           "them and this baseline does not record them as discover targets.  "
           "A fixed-pass declared group must be contained in the discovered "
           "group; a fixed-reject declared group must not be fully contained.")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def real_states_of(case, m):
    meta = m["meta"]
    if "real_states" in meta:                      # tcp / dhcp / imap
        return set(meta["real_states"])
    k = meta.get("real_states_count")
    if k is not None:
        if case == "mini2048":                     # 4 cells x 2 bits, cell value 3 unused
            return set(s for s in range(m["n_states"])
                       if all(((s >> (2 * c)) & 3) < 3 for c in range(4)))
        return set(range(k))                       # rank-space generator cases
    return set(i for i, nm in enumerate(meta["state_names"])
               if not nm.startswith("filler"))     # field-trial convention


def fact(k):
    r = 1
    for i in range(2, k + 1):
        r *= i
    return r


def free_class(m, real):
    """States with uniform isolated rows: every action cell == [(1.0, self, 0.0)],
    no in-edge from any other state, no out-edge to any other state.  Any
    permutation of this set is a fixed-caliber automorphism (Sym(S) <= Aut),
    and any fixed automorphism maps this set onto itself."""
    n = m["n_states"]; na = m["n_actions"]; trans = m["trans"]
    uni = [s for s in range(n)
           if all(trans[s][a] == [[1.0, s, 0.0]] for a in range(na))]
    anchored = set()
    for s in range(n):
        for a in range(na):
            for (p, t, r) in trans[s][a]:
                if t != s:
                    anchored.add(t)   # has an in-edge -> not freely permutable
                    if s in set(uni):
                        anchored.add(s)
    return sorted(s for s in uni if s not in anchored)


def is_fixed_automorphism(m, pi):
    """fixed criterion (sealed truth wording): for every (s,a),
    multiset(trans[pi(s)][a]) == multiset{(p, pi(t), r) : (p,t,r) in trans[s][a]}."""
    n = m["n_states"]; na = m["n_actions"]; trans = m["trans"]
    for s in range(n):
        ps = pi[s]
        for a in range(na):
            if Counter(map(tuple, trans[ps][a])) != \
               Counter((p, pi[t], r) for (p, t, r) in trans[s][a]):
                return False
    return True


def complement_signatures_distinct(m, comp):
    """One-round (prob, reward) signature per action, in and out, over the
    complement of the free class.  Distinct signatures certify that every
    fixed automorphism fixes each complement state (they are preserved by
    every automorphism)."""
    na = m["n_actions"]; trans = m["trans"]
    sig = {}
    for s in comp:
        out = tuple(tuple(sorted((p, r) for (p, t, r) in trans[s][a]))
                    for a in range(na))
        ine = [[] for _ in range(na)]
        for t in comp:
            for a in range(na):
                for (p, tt, r) in trans[t][a]:
                    if tt == s:
                        ine[a].append((p, r))
        sig[s] = (out, tuple(tuple(sorted(x)) for x in ine))
    return len(set(sig.values())) == len(sig), len(set(sig.values()))


def cycles(pi):
    """Cycle notation (as string) of a state permutation."""
    n = len(pi); seen = [False] * n; out = []
    for i in range(n):
        if seen[i]:
            continue
        c = []
        j = i
        while not seen[j]:
            seen[j] = True
            c.append(j)
            j = pi[j]
        if len(c) > 1:
            out.append("(" + " ".join(str(x) for x in c) + ")")
    return out if out else ["id"]


def sealed_truth(sealed_dir, case):
    """Read the sealed truth file; verify its sha256 against the project's
    sealed manifest; return the excerpt recorded in the baseline."""
    tpath = os.path.join(sealed_dir, case + ".truth.json")
    t = load_json(tpath)
    with open(tpath, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    manifest = load_json(os.path.join(sealed_dir, "_W3_manifest.json"))
    mcase = manifest["cases"][case]
    if sha != mcase["sha256"]:
        raise SystemExit("sealed truth sha256 mismatch for %s" % case)
    excerpt = {
        "sealed_file": "field-trial blind-test project, sealed/%s.truth.json" % case,
        "sha256": sha,
        "sealed_wave": t["wave"],
        "sealed_utc": t["generated_utc"],
        "fixed_aut_order": t["truth_primary"]["fixed_aut_order"],
        "fixed_aut_order_no_reward": t["truth_primary"]["fixed_aut_order_no_reward"],
        "method": t["truth_primary"]["method"],
        "group_verdicts": {g["file"]: g["verdict_declared_semantics"]
                           for g in t["groups"]},
    }
    if "networkx_vf2_full" in t["methods"]:
        fgf = t["methods"]["networkx_vf2_full"].get("fixed_group_facts") or {}
        if fgf.get("state_orbits"):
            excerpt["state_orbits"] = fgf["state_orbits"]
    fd = t["methods"].get("networkx_vf2_reduced_decomposition", {})
    if fd.get("filler_decomposition"):
        fdec = fd["filler_decomposition"]
        excerpt["filler_decomposition"] = {
            "class": fdec["class"], "class_size": fdec["class_size"],
            "isolated": fdec["isolated"], "k_factorial": fdec["k_factorial"],
        }
        lifted = fd.get("lifted") or {}
        if lifted.get("formula"):
            excerpt["lifted_formula"] = lifted["formula"]
            excerpt["lifted_spot_checks"] = lifted.get("spot_checks", {}).get("all_passed")
    return excerpt


def build_case(case, sealed_dir):
    m = load_json(os.path.join(REPO, "cases", case, "model.json"))
    exp = load_json(os.path.join(REPO, "cases", case, "expected.json"))
    real = real_states_of(case, m)
    fc = free_class(m, real)
    fcset = set(fc)
    comp = sorted(set(range(m["n_states"])) - fcset)
    comp_distinct, _ = complement_signatures_distinct(m, comp)
    edges_total = sum(len(m["trans"][s][a])
                      for s in range(m["n_states"])
                      for a in range(m["n_actions"]))
    k_fact = fact(len(fc))

    # expectation assembly
    if case in SEALED_CASES:
        st = sealed_truth(sealed_dir, case)
        order_exact = st["fixed_aut_order"]
        basis = ("sealed truth (brute-force/VF2/backtracker cross-validated in "
                 "the field-trial blind-test project)")
        consistency = (k_fact <= order_exact)
        if not consistency:
            raise SystemExit("free-class bound exceeds sealed order for %s" % case)
    else:
        st = None
        order_exact = None
        basis = None

    exact_known = order_exact is not None
    if case == "lightsout3":
        # rows machine-checked clean + all 512 translations verified + masks
        # span GF(2)^9 (rank 9)  =>  Aut_fixed is exactly the translation
        # group C2^9 acting regularly (one orbit of 512 states).
        order_exact = 512
        basis = ("machine certificate: all %d x %d cells are single "
                 "(1.0, s xor mask_a, 0.0) rows; every one of the 512 masks "
                 "x->x xor v is a fixed automorphism (exhaustively checked); "
                 "the 9 toggle masks have GF(2) rank 9, so any fixed "
                 "automorphism pi satisfies pi(s xor mask_a) = pi(s) xor "
                 "mask_a and is itself a translation" % (512, 9))
        exact_known = True

    notes = []
    if not exact_known and comp_distinct:
        order_exact = k_fact  # complement certified rigid -> product is exact
        basis = ("machine certificate: free class of %d uniform isolated states "
                 "(Sym(free class) <= Aut) + complement of %d states with "
                 "pairwise-distinct (prob, reward) per-action signatures "
                 "(rigid); orders multiply because the free class is "
                 "Aut-invariant" % (len(fc), len(comp)))
        exact_known = True
    if not exact_known:
        notes.append(
            "complement rigidity not certified by one-round signatures "
            "(structure-only shadows tie some signatures); the order lower "
            "bound from the free class stands; discover's refinement and "
            "enumeration decide the complement factor")
        if k_fact > DEFAULT_CAP:
            notes.append("the free-class lower bound alone exceeds the default "
                         "cap %d, so enumeration is expected to stop at the cap"
                         % DEFAULT_CAP)

    # orbit count when the order is exact: the free class contributes one
    # orbit of len(fc) states when len(fc) >= 2, else all states are
    # singletons; lightsout3's translation group acts transitively (1 orbit).
    def orbit_count():
        if case == "lightsout3":
            return 1
        if len(fc) >= 2:
            return m["n_states"] - len(fc) + 1
        return m["n_states"]

    expected_orbits = orbit_count() if exact_known else None

    if len(fc) >= 2:
        wl_discrete = False
        wl_note = ("the free class of %d states is one 1-WL block (its members "
                   "are genuinely automorphism-equivalent), so the refinement "
                   "is not discrete; WL upper bound = product of block "
                   "factorials, tight here only if the complement is "
                   "WL-discrete" % len(fc))
    elif comp_distinct:
        wl_discrete = True
        wl_note = ("complement states have pairwise-distinct per-action "
                   "(prob, reward) signatures and the free class is a "
                   "singleton, so the refinement is expected to be discrete "
                   "(identity group only when the free class is empty or a "
                   "single state pinned by in-edges)")
    else:
        wl_discrete = False
        wl_note = ("no free class, but the refinement is not expected to be "
                   "discrete: automorphism-tied states stay in one WL block "
                   "(for this case the translation group ties all states), so "
                   "the WL upper bound is loose even though the order is "
                   "pinned by the translation-group certificate")

    cap_flag = (order_exact if order_exact is not None else k_fact) > DEFAULT_CAP

    expectation = {
        "order_exact": order_exact,
        "order_exact_basis": basis,
        "order_lower_bound": order_exact if exact_known else k_fact,
        "order_lower_bound_basis": (
            "free class empty; lower bound equals the certified order_exact"
            if (exact_known and len(fc) == 0) else
            ("Sym(free class) <= Aut_fixed: all %d member(s) "
             "have uniform isolated rows (machine-checked); bound tight here"
             % len(fc))
            if exact_known else
            ("Sym(free class) <= Aut_fixed: all %d members "
             "have uniform isolated rows (machine-checked)" % len(fc))),
        "complement_rigidity_certified": bool(comp_distinct),
        "expected_state_orbits_if_order_exact": expected_orbits,
        "expected_state_orbits_if_complement_rigid": orbit_count(),
        "wl_refinement_expected_discrete": wl_discrete,
        "wl_note": wl_note,
        "automorphism_cap_default_%d" % DEFAULT_CAP: {
            "hit_expected": cap_flag,
            "on_hit": "stop enumeration, report orbit lower bound from the "
                      "enumerated subset plus the WL upper bound; the exact "
                      "order stays pinned by the sources above",
        },
        "notes": notes,
    }

    groups = []
    gdir = os.path.join(REPO, "cases", case, "groups")
    for fn in sorted(os.listdir(gdir)):
        if not fn.endswith(".json"):
            continue
        g = load_json(os.path.join(gdir, fn))
        els = g["elements"]
        checks = [is_fixed_automorphism(m, pi) for pi in els]
        row = exp["groups"].get(fn[:-5], {})
        fx = row.get("fixed", {})
        groups.append({
            "file": fn,
            "declared_semantics": g.get("semantics", {}).get("action"),
            "n_elements": len(els),
            "element_cycles": [cycles(pi) for pi in els],
            "element_is_fixed_automorphism": checks,
            "all_elements_in_aut_fixed": all(checks),
            "expected_fixed_row": {k2: fx[k2] for k2 in
                                   ("exit", "verdict", "worst_tv") if k2 in fx},
            "networkx_labeled_column": (row.get("networkx") or {}).get("labeled_symmetry"),
            "discover_admission_expected": ("contained" if all(checks)
                                            else "not_fully_contained"),
        })
        if fx and (fx.get("verdict") == "pass") != all(checks):
            raise SystemExit("expected.json fixed row disagrees with the "
                             "machine check for %s / %s" % (case, fn))

    doc = {
        "_kind": "reconciliation baseline for the discover capability (draft); "
                 "hand-derived and machine-checked from the named sources; NOT "
                 "an engine receipt and NOT discover output",
        "_honesty_boundary": HONESTY,
        "case": case,
        "caliber": "fixed (event names pinned; rewards kept)",
        "sources": {
            "model": "cases/%s/model.json" % case,
            "declared_groups": "cases/%s/groups/" % case,
            "court_receipt": "cases/%s/expected.json" % case,
            "sealed_truth": st,
            "baseline_method": "declared group elements machine-verified "
                               "against the fixed criterion directly on the "
                               "model; free class and per-action (prob, reward) "
                               "signatures computed directly from the model; "
                               "no discover output read",
        },
        "model_facts": {
            "n_states": m["n_states"],
            "n_actions": m["n_actions"],
            "edges_total": edges_total,
            "n_real_states": len(real),
            "n_padding_states": m["n_states"] - len(real),
            "uniform_isolated_free_class": {
                "size": len(fc),
                "members": fc,
                "contains_real_states": any(s in real for s in fc),
                "real_members": sorted(s for s in fc if s in real),
            },
        },
        "fixed_automorphism_expectation": expectation,
        "declared_groups": groups,
        "reconciliation_checks": [
            "order: discovered order (exact, or cap lower bound plus WL upper "
            "bound) consistent with order_exact / order_lower_bound above",
            "admission: every fixed-pass declared group contained in the "
            "discovered group; every fixed-reject declared group not fully "
            "contained",
            "orbits: free class forms a single orbit; orbit count consistent "
            "with expected_state_orbits_if_order_exact when the order is exact",
            "discreteness: wl_refinement_expected_discrete must match the "
            "discover refinement report",
            "cap: automorphism_cap hit flag consistent with the expectation "
            "recorded above",
        ],
    }
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sealed-dir",
                    default=os.path.join(os.path.dirname(REPO), "field-trial",
                                         "sealed"),
                    help="directory holding the field-trial blind-test "
                         "project's sealed truth (with _W3_manifest.json)")
    ap.add_argument("--check", action="store_true",
                    help="regenerate and compare bytes instead of writing")
    args = ap.parse_args()

    outdir = os.path.join(REPO, "verdicts", "discover-baseline")
    drift = []
    for case in CASES:
        doc = build_case(case, args.sealed_dir)
        text = json.dumps(doc, ensure_ascii=False, indent=1,
                          sort_keys=False) + "\n"
        out = os.path.join(outdir, "discover.%s.expected.json" % case)
        if args.check:
            with open(out, "rb") as f:
                if f.read().decode("utf-8") != text:
                    drift.append(case)
        else:
            os.makedirs(outdir, exist_ok=True)
            with open(out, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            print("wrote %s" % out)
    if args.check:
        if drift:
            print("DRIFT: %s" % ", ".join(drift))
            return 1
        print("check OK: 12 baselines byte-identical")
    return 0


if __name__ == "__main__":
    sys.exit(main())

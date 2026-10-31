# -*- coding: utf-8 -*-
"""
selftest.py —— 门禁：全案重放对 expected + vendored 完整性

  1. 对 <cases-dir> 下每案重跑三方庭审（与 arbitrate 同一套机械），
     与该案 expected.json 逐字段比对：
       relabel/fixed 两臂 × exit/verdict/worst_tv/judge
       networkx 列 × structure_symmetry/labeled_symmetry
  2. 若 verdicts/<case>.verdict.json 已存在，顺带核对其契约字段与
     expected 一致（判决书是否过期）。
  3. vendored 完整性：按 NOTICE 的 sha256 清单逐文件重算哈希；
     清单外多出的实体文件（__pycache__/*.pyc 豁免）也算漂移。
  4. 引擎健康：python -X utf8 -m wuxing_gua --version 可解析。

退出码：0=全过；1=任一比对比失败/案件残缺/引擎或 vendored 漂移。
无案件（0 cases）时退出 0 并明说（空卷宗上门禁空过，README 数字仍须
有 expected/verdict 收据背书）。

expected.json 布局（规约；读取时兼容每群平铺的旧式行）：
  {"case": "...",
   "groups": {"<群名>": {
       "claim": "...",
       "relabel": {"exit": 0, "verdict": "pass", "worst_tv": 0.0, "judge": "generalized"},
       "fixed":   {"exit": 1, "verdict": "reject", "worst_tv": 1.0, "judge": "strict"},
       "networkx": {"structure_symmetry": true, "labeled_symmetry": false}}}}
"""

import argparse
import json
import os
import re
import sys

from . import (DEFAULT_CASES_DIR, DEFAULT_VERDICTS_DIR, REPO_ROOT,
               VENDORED_DIR)
from .trial import ENGINE_TIMEOUT_DEFAULT, try_case, TV_FLOAT_TOL

EXIT_OK = 0
EXIT_FAIL = 1

_NOTICE = os.path.join(REPO_ROOT, "NOTICE")
_MANIFEST_RE = re.compile(r"^([0-9a-f]{64})  (.+)$")
_CONTRACT_FIELDS = ("exit", "verdict", "worst_tv", "judge")
_NX_FIELDS = ("structure_symmetry", "labeled_symmetry")


# ---------------------------------------------------------------- 比对
def _num_eq(a, b):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= TV_FLOAT_TOL
    return a == b


def _field_eq(field, got, want):
    if field in ("worst_tv",):
        return _num_eq(got, want)
    return got == want


def compare_case(expected, verdict):
    """expected vs 重放判决 → (failures[list[str]], checked[int])。"""
    fails, checked = [], 0
    exp_groups = expected.get("groups")
    if not isinstance(exp_groups, dict) or not exp_groups:
        return ["expected.json has no 'groups' object (or it is empty)"], 0
    got_groups = verdict.get("groups") or {}
    for name in sorted(exp_groups):
        want = exp_groups[name]
        got = got_groups.get(name)
        if got is None:
            fails.append("group %r: present in expected, missing from replay" % name)
            continue
        for arm in ("relabel", "fixed"):
            want_row = want.get(arm)
            got_row = got.get(arm)
            if not isinstance(want_row, dict) or got_row is None:
                fails.append("group %r arm %r: expected row missing/unreadable"
                             % (name, arm))
                continue
            for f in _CONTRACT_FIELDS:
                checked += 1
                if not _field_eq(f, got_row.get(f), want_row.get(f)):
                    fails.append("group %r %s.%s: expected %r, replay %r"
                                 % (name, arm, f, want_row.get(f), got_row.get(f)))
        want_nx = want.get("networkx") or {
            k: want.get(k) for k in _NX_FIELDS}  # 兼容平铺旧式
        got_nx = got.get("networkx") or {}
        for f in _NX_FIELDS:
            checked += 1
            if bool(got_nx.get(f)) != bool(want_nx.get(f)):
                fails.append("group %r networkx.%s: expected %r, replay %r"
                             % (name, f, want_nx.get(f), got_nx.get(f)))
    extra = sorted(set(got_groups) - set(exp_groups))
    if extra:
        fails.append("groups only in replay (not in expected): %s"
                     % ", ".join(extra))
    return fails, checked


def load_expected(case_dir):
    with open(os.path.join(case_dir, "expected.json"), "r",
              encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- vendored 完整性
def vendor_check():
    """NOTICE sha256 清单 vs vendored/ 实况。返回 (failures, n_checked)。"""
    fails = []
    if not os.path.isfile(_NOTICE):
        return ["NOTICE not found at repo root: %s" % _NOTICE], 0
    if not os.path.isdir(VENDORED_DIR):
        return ["vendored/ dir not found: %s" % VENDORED_DIR], 0
    import hashlib
    manifest = {}
    with open(_NOTICE, "r", encoding="utf-8") as f:
        for line in f:
            m = _MANIFEST_RE.match(line.rstrip("\n"))
            if m:
                manifest[m.group(2).strip()] = m.group(1)
    if not manifest:
        return ["NOTICE contains no sha256 manifest lines "
                "(expected '<64hex>  <path>' entries)"], 0

    def sha256(path):
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    n = 0
    for rel, want in sorted(manifest.items()):
        p = os.path.join(VENDORED_DIR, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            fails.append("vendored file missing: %s" % rel)
            continue
        got = sha256(p)
        n += 1
        if got != want:
            fails.append("vendored file DRIFT: %s (NOTICE %s... vs actual %s...)"
                         % (rel, want[:12], got[:12]))

    # 清单外多出的实体文件（__pycache__/*.pyc 豁免）也是漂移
    listed = {rel.replace("/", os.sep) for rel in manifest}
    for root, dirs, files in os.walk(VENDORED_DIR):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fn in files:
            if fn.endswith(".pyc"):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, VENDORED_DIR)
            if rel not in listed:
                fails.append("vendored extra file not in NOTICE manifest: %s" % rel)
    return fails, n


# ---------------------------------------------------------------- 主流程
def run(argv=None):
    ap = argparse.ArgumentParser(
        prog="python -X utf8 -m symmetry_court selftest",
        description="门禁：全案重放对 expected + vendored 完整性")
    ap.add_argument("--cases-dir", default=DEFAULT_CASES_DIR,
                    help="案卷目录（默认 <repo>/cases）")
    ap.add_argument("--verdicts-dir", default=DEFAULT_VERDICTS_DIR,
                    help="判决书目录（默认 <repo>/verdicts，用于过期核对）")
    ap.add_argument("--timeout", type=int, default=ENGINE_TIMEOUT_DEFAULT)
    ap.add_argument("--skip-vendor-check", action="store_true",
                    help="跳过 NOTICE 清单核验（不推荐；调试用）")
    args = ap.parse_args(argv)

    all_ok = True

    # 1) vendored 完整性 + 引擎健康（与案卷数无关，总是跑）
    if args.skip_vendor_check:
        print("[vendored] 按参数跳过清单核验")
    else:
        vfails, n = vendor_check()
        if vfails:
            all_ok = False
            print("[vendored] FAIL（%d/%d 文件核验）：" % (n - len(vfails), n))
            for m in vfails:
                print("    - %s" % m)
        else:
            print("[vendored] OK：NOTICE 清单 %d 文件逐一重算 sha256 一致，无清单外文件" % n)

    try:
        from .trial import _tools_block
        tools = _tools_block(VENDORED_DIR)
        eng = tools["engine"]["version"]
        if eng and "wuxing_gua" in eng:
            print("[engine] OK：%s（cwd=vendored/，PYTHONDONTWRITEBYTECODE=1）" % eng)
        else:
            all_ok = False
            print("[engine] FAIL：--version 不可解析：%r" % eng)
    except Exception as e:  # noqa: BLE001
        all_ok = False
        print("[engine] FAIL：%r" % (e,))

    # 2) 全案重放
    cases = []
    if os.path.isdir(args.cases_dir):
        for entry in sorted(os.listdir(args.cases_dir)):
            d = os.path.join(args.cases_dir, entry)
            if os.path.isdir(d) and os.path.isfile(os.path.join(d, "model.json")):
                cases.append(entry)
    if not cases:
        print("[replay] 无案件（0 cases）——门禁空过（退出 0）；"
              "README 数字仍须有 expected/verdict 收据背书")
        print("SELFTEST %s" % ("PASS" if all_ok else "FAIL"))
        return EXIT_OK if all_ok else EXIT_FAIL

    total_checked = 0
    for case_name in cases:
        case_dir = os.path.join(args.cases_dir, case_name)
        exp_path = os.path.join(case_dir, "expected.json")
        print("-" * 72)
        print("[replay] case %s" % case_name)
        if not os.path.isfile(exp_path):
            all_ok = False
            print("    FAIL：expected.json 缺失（案件残缺——门禁要求每案有期望判决表）")
            continue
        try:
            expected = load_expected(case_dir)
        except (OSError, ValueError) as e:
            all_ok = False
            print("    FAIL：expected.json 不可读：%s" % e)
            continue
        try:
            verdict, err = try_case(args.cases_dir, case_name,
                                    timeout=args.timeout,
                                    vendored_dir=VENDORED_DIR)
        except Exception as e:  # noqa: BLE001
            all_ok = False
            print("    FAIL：重放异常 %r" % (e,))
            continue
        if err is not None:
            all_ok = False
            print("    FAIL：重放失败：%s" % err)
            continue

        fails, checked = compare_case(expected, verdict)
        total_checked += checked
        # 判决书收据核对：仓库里的 verdict 文件也必须与 expected 一致
        # （README 门禁口径：「every verdict in the repository still matches
        # its expected record」）。缺失或过期都算 FAIL，修法=重跑 arbitrate。
        stale_msgs = []
        vd_path = os.path.join(args.verdicts_dir, "%s.verdict.json" % case_name)
        if os.path.isfile(vd_path):
            try:
                with open(vd_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                sfails, _schecked = compare_case(expected, saved)
                if sfails:
                    stale_msgs.append("saved verdict file STALE: %d field(s) "
                                      "differ from expected (run arbitrate to "
                                      "refresh)" % len(sfails))
            except (OSError, ValueError) as e:
                stale_msgs.append("saved verdict file unreadable: %s" % e)
        else:
            stale_msgs.append("no saved verdict file (arbitrate has not been "
                              "run for this case; run it to mint the receipt)")

        if fails:
            all_ok = False
            print("    FAIL：%d/%d 个契约字段不一致：" % (len(fails), checked))
            for m in fails:
                print("      - %s" % m)
        else:
            print("    PASS：expected 全部 %d 个契约字段与重放一致" % checked)
            print("    判语: %s" % json.dumps(
                (verdict.get("rollup") or {}).get("ruling_codes", {}),
                ensure_ascii=False))
        if stale_msgs:
            all_ok = False
            for m in stale_msgs:
                print("    FAIL：%s" % m)
        else:
            print("    PASS：判决书收据（verdicts/%s.verdict.json）与 expected 一致"
                  % case_name)

    print("=" * 72)
    print("SELFTEST %s（重放契约字段 %d 个）" % ("PASS" if all_ok else "FAIL",
                                              total_checked))
    return EXIT_OK if all_ok else EXIT_FAIL


def main(argv=None):
    try:
        return run(argv)
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 3
        return code if code in (0, 1) else 3


if __name__ == "__main__":
    sys.exit(main())

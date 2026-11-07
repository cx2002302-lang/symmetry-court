# -*- coding: utf-8 -*-
"""
入口：python -X utf8 -m symmetry_court <arbitrate|selftest|compare|discover|list>

  arbitrate  开庭：cases/ 全案三方庭审 → verdicts/<case>.verdict.json + 判决书表格
  selftest   门禁：全案重放对 expected（逐字段）+ vendored 完整性；退出码 0=全过
  compare    闸门价值对比：朴素臂（结构直觉代理）vs 闸门臂（check --strict），
             逐群量化『不用闸会破坏多少真实转移格』（见 compare.py 文档串）
  discover   候选发现：fixed 口径（事件名钉死）候选对称群自动发现
             （networkx VF2 + 1-WL 细化 + 硬上限）→ 候选群文件过 vendored
             引擎 check 验证（闸门臂）→ verdicts/discover.<case>.json；
             只覆盖 fixed 口径，动作改名类候选仍由案卷作者显式声明
  list       列案卷：案名 / 模型规模 / 群数 / 是否有 expected / 判决书收据状态
"""

import json
import os
import sys

from . import (DEFAULT_CASES_DIR, DEFAULT_SMOKE_DIR, DEFAULT_VERDICTS_DIR,
               VENDORED_DIR, __version__)

USAGE = ("usage: python -X utf8 -m symmetry_court "
         "<arbitrate|selftest|compare|discover|list> [flags]")

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 3


def _utf8_stdio():
    """Windows 控制台强制 UTF-8（项目惯例 python -X utf8 已设，这里兜底）。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001 非 TextIO 时忽略
            pass


def _case_brief(cases_dir, verdicts_dir, label):
    rows = []
    if not os.path.isdir(cases_dir):
        print("%s %s：目录不存在" % (label, cases_dir))
        return rows
    entries = sorted(os.listdir(cases_dir))
    dirs = [e for e in entries if os.path.isdir(os.path.join(cases_dir, e))]
    print("%s %s：%d 个子目录" % (label, cases_dir, len(dirs)))
    for entry in dirs:
        d = os.path.join(cases_dir, entry)
        model_path = os.path.join(d, "model.json")
        if not os.path.isfile(model_path):
            print("  %-14s (无 model.json——非案件目录或在途)" % entry)
            continue
        n_groups = "-"
        groups_dir = os.path.join(d, "groups")
        if os.path.isdir(groups_dir):
            n_groups = str(len([f for f in os.listdir(groups_dir)
                                if f.endswith(".json")]))
        shape = "?"
        try:
            with open(model_path, "r", encoding="utf-8") as f:
                m = json.load(f)
            shape = "%d态/%d动作" % (m.get("n_states", 1 << m.get("n_bits", 0)),
                                    m.get("n_actions", 0))
        except (OSError, ValueError):
            shape = "model.json 不可读"
        has_expected = "yes" if os.path.isfile(os.path.join(d, "expected.json")) else "NO"
        vd = os.path.join(verdicts_dir, "%s.verdict.json" % entry)
        has_verdict = "yes" if os.path.isfile(vd) else "NO"
        print("  %-14s %-14s groups=%-4s expected=%-3s verdict=%-3s"
              % (entry, shape, n_groups, has_expected, has_verdict))
        rows.append(entry)
    return rows


def cmd_list(args):
    rows = _case_brief(args.cases_dir, args.verdicts_dir, "案卷 docket")
    if not os.path.isdir(args.cases_dir):
        # 走查 F1 修复（2026-11-07）：案卷目录不存在也是用法级失败——
        # 上面已如实打印，这里再把退出码置 3，与其他子命令统一口径。
        print("list：案卷目录不存在（exit 3）：%s" % args.cases_dir,
              file=sys.stderr)
        return EXIT_USAGE
    if os.path.isdir(DEFAULT_SMOKE_DIR):
        _case_brief(DEFAULT_SMOKE_DIR, args.verdicts_dir,
                    "烟测 smoke（非正式案卷，正式以 cases/ 为准）")
    print("引擎 vendored: %s（存在=%s；来源与字节清单见 NOTICE）"
          % (VENDORED_DIR, os.path.isdir(VENDORED_DIR)))
    print("symmetry_court %s" % __version__)
    return EXIT_OK


def _discover_case_brief(verdict):
    """一案 discover 的人读摘要行。"""
    d = verdict["discovery"]
    enum = d["enumeration"]
    orb = d["orbits"]
    gate = verdict["gate_arm"]
    gate_check = gate.get("engine_check") or {}
    order_s = str(enum["order"]) if enum["order"] is not None \
        else ">=%d" % enum["enumerated_count"]
    orb_s = "%d (exact)" % orb["n_orbits"] if orb["status"] == "exact" \
        else "LB %d / UB %d (bounded)" % (len(orb["lower_bound_blocks"]),
                                          len(orb["upper_bound_blocks"]))
    print("  WL 细分: %d 块, 离散=%s | 枚举: %d 个自同构, 触顶=%s"
          % (d["wl_refinement"]["n_blocks"], d["wl_refinement"]["discrete"],
             enum["enumerated_count"], enum["truncated"]))
    print("  群阶: %s | 轨道: %s" % (order_s, orb_s))
    print("  闸门臂(vendored check --strict, 候选阶 %s): %s"
          % (gate.get("candidate", {}).get("order"),
             gate_check.get("verdict")))
    rec = verdict.get("reconciliation") or {}
    if rec.get("checked"):
        print("  对账 expected: %s 群一致=%s"
              % (len(rec.get("groups") or []), rec.get("all_consistent")))
    sealed = verdict.get("sealed_truth") or {}
    if sealed.get("checked"):
        print("  对账 sealed truth: order_matches=%s"
              % sealed.get("order_matches"))
    smoke = verdict.get("smoke") or {}
    if smoke.get("applicable"):
        dirs = smoke.get("directions") or {}
        print("  冒烟双方向: pads 发现=%s | swap 不发现=%s"
              % (dirs.get("pads_discovered"),
                 dirs.get("swap_not_discovered")))


def cmd_discover(args):
    """discover 子命令：逐案 fixed 口径候选发现 + 闸门臂 + 对账。"""
    from .discover import (AUTOMORPHISM_CAP_DEFAULT, run_discover_case)
    all_cases = []
    if os.path.isdir(args.cases_dir):
        for entry in sorted(os.listdir(args.cases_dir)):
            d = os.path.join(args.cases_dir, entry)
            if os.path.isdir(d) and os.path.isfile(os.path.join(d, "model.json")):
                all_cases.append(entry)
    available = ", ".join(all_cases) or "(none)"
    cases = all_cases
    if args.case:
        cases = [c for c in cases if c == args.case]
        if not cases:
            print("unknown case: %r / available: %s（--cases-dir=%s；"
                  "--case 为精确单案名，案名可先跑 `list` 查看）"
                  % (args.case, available, args.cases_dir), file=sys.stderr)
            return EXIT_USAGE
    if not cases:
        # 走查 F1 修复（2026-11-07）：0 案受审绝不静默 exit 0——
        # 用法级失败：退出码 3 + stderr 明示。
        print("无案件可发现（0 cases）——案卷 %s 不存在、为空或不包含案件目录"
              "（案件目录 = 含 model.json 的子目录）；正式案卷以 cases/ 为准，"
              "烟测可用 --cases-dir smoke" % args.cases_dir, file=sys.stderr)
        return EXIT_USAGE
    if not args.quiet:
        print("候选发现 discover（fixed 口径：事件名钉死；动作改名类候选"
              "由案卷作者显式声明，机器不猜）")
        print("案卷 %s：%d 案 | cap=%d%s"
              % (args.cases_dir, len(cases), args.cap,
                 ("" if args.sealed_dir is None
                  else " | sealed-dir: %s" % os.path.basename(
                      os.path.normpath(args.sealed_dir)))))
    os.makedirs(args.verdicts_dir, exist_ok=True)
    failures = []
    for case_name in cases:
        if not args.quiet:
            print("=" * 72)
            print("discover case: %s" % case_name)
        verdict, err = None, None
        try:
            verdict, err = run_discover_case(
                case_name, args.cases_dir, args.verdicts_dir, VENDORED_DIR,
                cap=args.cap, budget_s=args.budget_seconds,
                timeout=args.timeout, sealed_dir=args.sealed_dir)
        except Exception as e:  # noqa: BLE001 单案异常不拖垮全部
            err = "unhandled discover error: %r" % (e,)
        if err is not None:
            failures.append((case_name, err))
            print("  [发现失败] %s: %s" % (case_name, err), file=sys.stderr)
            continue
        if not args.quiet:
            _discover_case_brief(verdict)
            print("  判决书已写出: verdicts/discover.%s.json "
                  "(+ candidate 群文件，均可重放)" % case_name)
        # fail loud 条件：闸门臂报错/拒绝、对账不一致、群阶阶数不一致
        gate_check = (verdict["gate_arm"].get("engine_check") or {})
        rec = verdict.get("reconciliation") or {}
        sealed = verdict.get("sealed_truth") or {}
        if gate_check.get("error"):
            failures.append((case_name, "gate arm error: %s"
                             % gate_check.get("error")))
        elif gate_check.get("verdict") not in ("pass", None):
            failures.append((case_name, "gate arm verdict=%r on the "
                             "discovered candidate (see verdict file)"
                             % gate_check.get("verdict")))
        if rec.get("checked") and rec.get("all_consistent") is False:
            failures.append((case_name,
                             "reconciliation vs expected.json inconsistent "
                             "(see verdict file)"))
        if sealed.get("checked") and sealed.get("order_matches") is False:
            failures.append((case_name,
                             "sealed-truth order mismatch (see verdict "
                             "file)"))
    if failures:
        print("发现结束，但有 %d 项失败/不一致：" % len(failures),
              file=sys.stderr)
        for name, msg in failures:
            print("  %s: %s" % (name, msg), file=sys.stderr)
        return EXIT_FAIL
    if not args.quiet:
        print("发现结束：全部 %d 案已发现并写出判决书与候选群文件。"
              % len(cases))
    return EXIT_OK


def main(argv=None):
    _utf8_stdio()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(USAGE)
        print(__doc__)
        return EXIT_OK if argv else EXIT_USAGE
    cmd, rest = argv[0], argv[1:]
    if cmd in ("-V", "--version"):
        print("symmetry_court %s" % __version__)
        return EXIT_OK
    try:
        return _dispatch(cmd, rest)
    except SystemExit as e:
        # 走查 F1 修复（2026-11-07）：argparse 用法错误统一落到本法庭的
        # 退出码 3（exit 2 也算用法错误——stderr 已由 argparse 写明）。
        code = e.code if isinstance(e.code, int) else EXIT_USAGE
        return code if code in (0, 1) else EXIT_USAGE


def _dispatch(cmd, rest):
    if cmd == "arbitrate":
        from . import arbitrate
        return arbitrate.main(rest)
    if cmd == "selftest":
        from . import selftest
        return selftest.main(rest)
    if cmd == "compare":
        import argparse
        from . import compare
        ap = argparse.ArgumentParser(prog="symmetry_court compare",
                                     allow_abbrev=False)
        ap.add_argument("--root", default=None,
                        help="cases 根目录（默认法庭自有 cases/；可指向同格式案卷集）")
        ap.add_argument("--out", default=None,
                        help="对比结果输出目录（默认 verdicts/）")
        args = ap.parse_args(rest)
        return compare.cmd_compare(args)
    if cmd == "discover":
        import argparse
        from .discover import AUTOMORPHISM_CAP_DEFAULT
        ap = argparse.ArgumentParser(
            prog="symmetry_court discover",
            description="fixed 口径（事件名钉死）候选对称群自动发现 + "
                        "vendored 引擎闸门臂 + 对既有真值对账",
            allow_abbrev=False)  # 走查 F1：禁前缀歧义匹配（全子命令统一口径）
        ap.add_argument("--case", default=None, metavar="NAME",
                        help="只发现名字为 NAME 的案件（默认全部）")
        ap.add_argument("--all", action="store_true",
                        help="全部案件（默认行为，显式声明的同义标志）")
        ap.add_argument("--cap", type=int, default=AUTOMORPHISM_CAP_DEFAULT,
                        help="自同构枚举硬上限（默认 %d；触顶即停并如实"
                             "记录下界口径）" % AUTOMORPHISM_CAP_DEFAULT)
        ap.add_argument("--budget-seconds", type=float, default=None,
                        help="单案枚举墙钟预算（秒；默认不限，只受 --cap 约束）")
        ap.add_argument("--cases-dir", default=DEFAULT_CASES_DIR,
                        help="案卷目录（默认 <repo>/cases；烟测可用 smoke/）")
        ap.add_argument("--verdicts-dir", default=DEFAULT_VERDICTS_DIR,
                        help="判决书输出目录（默认 <repo>/verdicts）")
        ap.add_argument("--sealed-dir", default=None,
                        help="field-trial 密封真值目录（可选；提供时对 field "
                             "五案做 fixed_aut_order 对账）")
        ap.add_argument("--timeout", type=int, default=300,
                        help="闸门臂单次引擎调用超时秒数（默认 300）")
        ap.add_argument("--quiet", action="store_true", help="只打印错误与摘要")
        args = ap.parse_args(rest)
        return cmd_discover(args)
    if cmd == "list":
        import argparse
        ap = argparse.ArgumentParser(prog="symmetry_court list",
                                     allow_abbrev=False)
        ap.add_argument("--cases-dir", default=DEFAULT_CASES_DIR)
        ap.add_argument("--verdicts-dir", default=DEFAULT_VERDICTS_DIR)
        args = ap.parse_args(rest)
        return cmd_list(args)
    sys.stderr.write("%s\n（未知命令 %r）\n" % (USAGE, cmd))
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())

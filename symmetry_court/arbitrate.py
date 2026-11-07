# -*- coding: utf-8 -*-
"""
arbitrate.py —— 开庭：对 cases/ 全案执行三方庭审

用法（仓库根目录）：
  python -X utf8 -m symmetry_court arbitrate                    # 官方案卷 cases/
  python -X utf8 -m symmetry_court arbitrate --cases-dir smoke  # 烟测案卷
  python -X utf8 -m symmetry_court arbitrate --case tcp         # 只审名为 tcp 的案
        # （--case = 精确单案名，与 discover --case 行为一致）
  python -X utf8 -m symmetry_court arbitrate --only tcp         # 只审名字含 tcp 的案
  python -X utf8 -m symmetry_court arbitrate --emit-expected-template
        # 额外打印每个群按 expected.json 契约观察到的行——给案例工程师
        # 落 expected.json 用（只打印，不写 cases/；数字以实际开庭为准）

行为：
  · 每案产出 verdicts/<case>.verdict.json（缩进 1、UTF-8、末尾换行）；
  · 控制台打印判决书表格：三方列（wuxing-gua@relabel / wuxing-gua@fixed /
    networkx@labeled）+ networkx 透明列（structure）+ 一致性判语；
  · 案件目录 = cases-dir 下含 model.json 的子目录（按名排序；无 model.json
    的子目录跳过并提示——兼容案例工程在途状态）；
  · 0 案受审绝不静默放行（走查 F1 修复，2026-11-07）：筛选后没有案件
    （--case/--only 无匹配，或案卷本身为空）一律退出码 3 并写 stderr 明示；
  · 退出码：0=全部案件均已开庭并写出判决（个别群 engine 报错也如实记录在
    判决书里，但会置退出码 1）；1=任一案件无法审理或审理中有错误；3=用法错误
    （含 0 案受审、未知案名、未知旗标——argparse 禁用前缀歧义匹配）。
"""

import argparse
import json
import os
import sys
import unicodedata

from . import (DEFAULT_CASES_DIR, DEFAULT_VERDICTS_DIR, VENDORED_DIR)
from .trial import (ENGINE_TIMEOUT_DEFAULT, CaseError, try_case)

EXIT_OK = 0
EXIT_TRIAL_FAILURE = 1
EXIT_USAGE = 3


# ---------------------------------------------------------------- 输出工具
def _w(s):
    """显示宽度（CJK 记 2）。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1
               for ch in s)


def _pad(s, width, align="left"):
    s = str(s)
    gap = width - _w(s)
    if gap <= 0:
        return s
    return s + " " * gap if align == "left" else " " * gap + s


def _fmt_engine_cell(row):
    if row.get("error"):
        return "ERR(%s)" % row.get("exit", "?")
    tv = row.get("worst_tv")
    tv_s = ""
    if isinstance(tv, (int, float)):
        tv_s = " tv=%g" % tv
    return "%s%s" % (row.get("verdict"), tv_s)


def _fmt_nx_cell(v):
    if v is None:
        return "n/a"
    return "yes" if v else "no"


def print_verdict_table(verdict, stream=sys.stdout):
    """一案判决书表格：三方列 + 透明列 + 判语。"""
    groups = verdict.get("groups") or {}
    header = ("群 group", "wuxing-gua@relabel", "wuxing-gua@fixed",
              "nx@structure", "nx@labeled", "一致性判语 ruling")
    rows = []
    for name in sorted(groups):
        g = groups[name]
        cons = g["consistency"]
        code = cons["ruling_code"]
        short = {
            "agree": "两口径一致:%s" % g["relabel"]["verdict"],
            "semantics_duality": "口径二义:relabel=%s/fixed=%s; nx 分列支持; 按声明(%s)终判=%s"
                                 % (g["relabel"]["verdict"], g["fixed"]["verdict"],
                                    (g["declared_semantics"] or {}).get("action"),
                                    cons.get("binding_verdict")),
            "disagree": "列间不一致——详见判决书",
            "error": "审理出错——详见判决书",
        }.get(code, code)
        rows.append((
            name,
            _fmt_engine_cell(g["relabel"]),
            _fmt_engine_cell(g["fixed"]),
            _fmt_nx_cell(g["networkx"]["structure_symmetry"]),
            _fmt_nx_cell(g["networkx"]["labeled_symmetry"]),
            short,
        ))
    widths = [max(_w(h), max((_w(r[i]) for r in rows), default=0))
              for i, h in enumerate(header)]
    sep = "-+-".join("-" * w for w in widths)
    line = " | ".join(_pad(h, widths[i]) for i, h in enumerate(header))
    print(line, file=stream)
    print(sep, file=stream)
    for r in rows:
        print(" | ".join(_pad(r[i], widths[i]) for i in range(len(r))),
              file=stream)
    rollup = verdict.get("rollup") or {}
    print("  判语汇总 ruling codes: %s | 口径内配对全部一致: %s"
          % (json.dumps(rollup.get("ruling_codes", {}), ensure_ascii=False),
             rollup.get("all_consistent_pairs")), file=stream)
    for err in verdict.get("group_errors") or []:
        print("  [群文件错误] %s: %s" % (err.get("group"), err.get("error")),
              file=stream)


# ---------------------------------------------------------------- 主流程
def _discover_cases(cases_dir):
    """含 model.json 的子目录列表（排序）。不含 model.json 的子目录跳过。"""
    if not os.path.isdir(cases_dir):
        return [], []
    cases, skipped = [], []
    for entry in sorted(os.listdir(cases_dir)):
        d = os.path.join(cases_dir, entry)
        if not os.path.isdir(d):
            continue
        if os.path.isfile(os.path.join(d, "model.json")):
            cases.append(entry)
        else:
            skipped.append(entry)
    return cases, skipped


def _emit_expected_template(verdict, stream=sys.stdout):
    """按 expected.json 契约打印观察到的行（给案例工程师抄进生成器用）。"""
    template = {"case": verdict["case"],
                "provenance": {
                    "recorded_from_live_run": verdict.get("generated_utc"),
                    "how": ("observed rows from "
                            "`python -X utf8 -m symmetry_court arbitrate "
                            "--emit-expected-template`; paste into the case "
                            "generator so --check can pin them byte-exactly"),
                },
                "groups": {}}
    for name in sorted(verdict.get("groups") or {}):
        g = verdict["groups"][name]
        template["groups"][name] = {
            "claim": g.get("claim"),
            "relabel": {k: g["relabel"].get(k)
                        for k in ("exit", "verdict", "worst_tv", "judge")},
            "fixed": {k: g["fixed"].get(k)
                      for k in ("exit", "verdict", "worst_tv", "judge")},
            "networkx": {k: g["networkx"].get(k)
                         for k in ("structure_symmetry", "labeled_symmetry")},
        }
    json.dump(template, stream, ensure_ascii=False, indent=1)
    stream.write("\n")


def run(argv=None):
    ap = argparse.ArgumentParser(
        prog="python -X utf8 -m symmetry_court arbitrate",
        description="三方庭审：wuxing-gua 双口径 × networkx 仲裁",
        allow_abbrev=False)  # 走查 F1：--case 曾被前缀匹配静默解析成 --cases-dir
    ap.add_argument("--cases-dir", default=DEFAULT_CASES_DIR,
                    help="案卷目录（默认 <repo>/cases）")
    ap.add_argument("--verdicts-dir", default=DEFAULT_VERDICTS_DIR,
                    help="判决书输出目录（默认 <repo>/verdicts）")
    ap.add_argument("--case", default=None, metavar="NAME",
                    help="只审名字为 NAME 的案件（精确匹配，单案名；"
                         "与 discover --case 行为一致）")
    ap.add_argument("--only", default=None, metavar="NAME",
                    help="只审名字包含 NAME 的案件（子串匹配）")
    ap.add_argument("--timeout", type=int, default=ENGINE_TIMEOUT_DEFAULT,
                    help="单次引擎调用超时秒数（默认 %d）" % ENGINE_TIMEOUT_DEFAULT)
    ap.add_argument("--emit-expected-template", action="store_true",
                    help="额外打印按 expected 契约观察到的行（stdout，不落盘）")
    ap.add_argument("--quiet", action="store_true", help="只打印错误与退出摘要")
    args = ap.parse_args(argv)

    all_cases, skipped = _discover_cases(args.cases_dir)
    available = ", ".join(all_cases) or "(none)"
    cases = all_cases
    if args.case:
        cases = [c for c in cases if c == args.case]
    if args.only:
        cases = [c for c in cases if args.only in c]
    if not args.quiet:
        print("案卷 %s：%d 案受审%s"
              % (args.cases_dir, len(cases),
                 ("；%d 个子目录无 model.json 跳过（在途？）: %s"
                  % (len(skipped), ", ".join(skipped))) if skipped else ""))
    if not cases:
        # 走查 F1 修复（2026-11-07）：0 案受审绝不静默 exit 0——
        # 用法级失败：退出码 3 + stderr 明示，让脚本与人都看得见。
        if args.case or args.only:
            picked = ("--case %r（精确单案名）" % args.case) if args.case \
                else ("--only %r（子串匹配）" % args.only)
            print("unknown case: %s / available: %s——在案卷 %s 中无匹配；"
                  "案名可先跑 `list` 查看；烟测卷另见 --cases-dir smoke"
                  % (picked, available, args.cases_dir), file=sys.stderr)
        else:
            print("无案件可审（0 cases）——案卷 %s 不存在、为空或不包含案件"
                  "目录（案件目录 = 含 model.json 的子目录）；正式案卷以 "
                  "cases/ 为准，烟测可用 --cases-dir smoke" % args.cases_dir,
                  file=sys.stderr)
        return EXIT_USAGE

    os.makedirs(args.verdicts_dir, exist_ok=True)
    failures = []
    for case_name in cases:
        if not args.quiet:
            print("=" * 72)
            print("开庭 case: %s" % case_name)
        verdict, err = None, None
        try:
            verdict, err = try_case(args.cases_dir, case_name,
                                    timeout=args.timeout,
                                    vendored_dir=VENDORED_DIR)
        except Exception as e:  # noqa: BLE001 单案异常不拖垮全庭
            err = "unhandled trial error: %r" % (e,)
        if err is not None:
            failures.append((case_name, err))
            print("  [无法审理] %s: %s" % (case_name, err), file=sys.stderr)
            continue

        out_path = os.path.join(args.verdicts_dir,
                                "%s.verdict.json" % case_name)
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            f.write(json.dumps(verdict, ensure_ascii=False, indent=1) + "\n")
        if not args.quiet:
            print_verdict_table(verdict)
            print("  判决书已写出: %s" % out_path)
        if args.emit_expected_template:
            print("--- expected template (observed) for %s ---" % case_name,
                  file=sys.stdout)
            _emit_expected_template(verdict)
        method_conflicts = sum(len(g["networkx"].get("method_conflicts") or [])
                               for g in verdict["groups"].values())
        if verdict["rollup"]["group_errors"] or method_conflicts or any(
                g["relabel"].get("error") or g["fixed"].get("error")
                for g in verdict["groups"].values()):
            failures.append((case_name,
                             "trial completed with errors%s (see verdict file)"
                             % (" / %d jury method conflicts" % method_conflicts
                                if method_conflicts else "")))

    if failures:
        print("审判结束，但有 %d 项失败/出错：" % len(failures), file=sys.stderr)
        for name, msg in failures:
            print("  %s: %s" % (name, msg), file=sys.stderr)
        return EXIT_TRIAL_FAILURE
    if not args.quiet:
        print("审判结束：全部 %d 案均开庭并写出判决书。" % len(cases))
    return EXIT_OK


def main(argv=None):
    try:
        return run(argv)
    except SystemExit as e:  # argparse 用法错误
        code = e.code if isinstance(e.code, int) else EXIT_USAGE
        return code if code in (0, 1) else EXIT_USAGE
    except CaseError as e:
        sys.stderr.write("[案件错误（退出码 1）] %s\n" % e)
        return EXIT_TRIAL_FAILURE


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""
入口：python -X utf8 -m symmetry_court <arbitrate|selftest|list>

  arbitrate  开庭：cases/ 全案三方庭审 → verdicts/<case>.verdict.json + 判决书表格
  selftest   门禁：全案重放对 expected（逐字段）+ vendored 完整性；退出码 0=全过
  list       列案卷：案名 / 模型规模 / 群数 / 是否有 expected / 判决书收据状态
"""

import json
import os
import sys

from . import (DEFAULT_CASES_DIR, DEFAULT_SMOKE_DIR, DEFAULT_VERDICTS_DIR,
               VENDORED_DIR, __version__)

USAGE = "usage: python -X utf8 -m symmetry_court <arbitrate|selftest|list> [flags]"

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
    if os.path.isdir(DEFAULT_SMOKE_DIR):
        _case_brief(DEFAULT_SMOKE_DIR, args.verdicts_dir,
                    "烟测 smoke（非正式案卷，正式以 cases/ 为准）")
    print("引擎 vendored: %s（存在=%s；来源与字节清单见 NOTICE）"
          % (VENDORED_DIR, os.path.isdir(VENDORED_DIR)))
    print("symmetry_court %s" % __version__)
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
    if cmd == "arbitrate":
        from . import arbitrate
        return arbitrate.main(rest)
    if cmd == "selftest":
        from . import selftest
        return selftest.main(rest)
    if cmd == "list":
        import argparse
        ap = argparse.ArgumentParser(prog="symmetry_court list")
        ap.add_argument("--cases-dir", default=DEFAULT_CASES_DIR)
        ap.add_argument("--verdicts-dir", default=DEFAULT_VERDICTS_DIR)
        args = ap.parse_args(rest)
        return cmd_list(args)
    sys.stderr.write("%s\n（未知命令 %r）\n" % (USAGE, cmd))
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())

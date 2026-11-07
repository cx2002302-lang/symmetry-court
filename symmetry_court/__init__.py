# -*- coding: utf-8 -*-
"""
symmetry_court —— 对称主张的法庭

一个主张（候选对称群）、三名法官、两个显名口径、一份可复跑的判决书：

  wuxing-gua@relabel   vendored 引擎，relabel 口径（动作可随状态换名）
  wuxing-gua@fixed     同一引擎，fixed 口径（--strict，动作名必须原样对应）
  networkx@labeled     独立陪审团（networkx），带事件标签判定
  (+ networkx 透明列: 只看结构的判定，记录于 expected/verdict 文件)

分工红线：
  · vendored/ 下的引擎字节级零修改（来源与清单见 NOTICE）——本包只经
    subprocess 调它，绝不重实现判据；
  · networkx 只当陪审团（仲裁列），不是守门人；
  · cases/ 目录归案例工程师所有，本包只读不写。

命令（仓库根目录运行）：
  python -X utf8 -m symmetry_court arbitrate|selftest|compare|discover|list
  （discover = 第四个能力：fixed 口径候选发现 + 闸门臂，见 discover.py 文档串）
"""

import os

__version__ = "0.1.0"

# 仓库根 = 本包目录的上一级（symmetry_court/ 与 vendored/、cases/ 平级）
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# vendored 引擎位置（NOTICE 记录来源与字节清单）。
# 引擎的 __init__ 要求 src/ 与包同级（PROJECT_ROOT = 包目录的上一级），
# 因此引擎一律以 cwd=vendored/ 经 subprocess 调用，并设
# PYTHONDONTWRITEBYTECODE=1 保持 vendored/ 字节原始。
VENDORED_DIR = os.path.join(REPO_ROOT, "vendored")

DEFAULT_CASES_DIR = os.path.join(REPO_ROOT, "cases")
DEFAULT_VERDICTS_DIR = os.path.join(REPO_ROOT, "verdicts")
DEFAULT_SMOKE_DIR = os.path.join(REPO_ROOT, "smoke")


def engine_env(base=None):
    """引擎 subprocess 的环境：禁写字节码缓存（vendored 树保持字节原始）。"""
    env = dict(base if base is not None else os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env

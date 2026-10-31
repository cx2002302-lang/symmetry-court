# -*- coding: utf-8 -*-
"""
tools/selftest.py -- thin adapter so the repo-root habit
(`python -X utf8 tools/selftest.py`) and the NOTICE prose
("`tools/selftest.py` re-verifies the manifest") both hold.

The gate itself lives in the symmetry_court package
(symmetry_court/selftest.py); this adapter simply delegates. Same flags,
same exit codes (0 = green).

Written by the arbitration/court stream, 2026-10-31.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from symmetry_court.selftest import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

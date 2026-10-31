@echo off
rem ============================================================
rem Symmetry Court - one-command trial run (official docket, then the
rem smoke docket). Every python call uses the project
rem convention: python -X utf8
rem Exit code 0 only if every step below passes.
rem ============================================================
setlocal
cd /d "%~dp0"

echo === [1/6] docket list ===
python -X utf8 -m symmetry_court list || goto :fail

echo === [2/6] arbitrate official cases/ ===
python -X utf8 -m symmetry_court arbitrate --quiet || goto :fail

echo === [3/6] selftest official cases/ (gate) ===
python -X utf8 -m symmetry_court selftest || goto :fail

echo === [4/6] arbitrate smoke docket ===
python -X utf8 -m symmetry_court arbitrate --cases-dir smoke || goto :fail

echo === [5/6] selftest smoke docket (gate) ===
python -X utf8 -m symmetry_court selftest --cases-dir smoke || goto :fail

echo === [6/6] smoke generator byte-identity ===
python -X utf8 smoke\tcp_smoke\make_tcp_smoke.py --check || goto :fail

echo.
echo ALL RUNS OK
exit /b 0

:fail
echo.
echo RUN FAILED (see above)
exit /b 1

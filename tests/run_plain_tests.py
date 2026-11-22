#!/usr/bin/env python3
"""Runner for the plain-function test files (pytest style: bare `def test_*()` with
asserts, no runner of their own). Started as `python tests/x.py` they ran NOTHING, so
they gated nothing. This imports each listed file and calls every test_* function.

CONTROL FIRST (audit-tools-must-fail): a built-in test that must fail is run through the
same call path; if the runner doesn't catch it, it stops before trusting any pass.

Pure stdlib, no bible.db. Exit 1 on any failure. Run:  python tests/run_plain_tests.py
A new plain-style file goes in FILES below (the two test lists only name this runner).
"""
import importlib.util
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)   # `import ai` etc. resolve from the repo root
sys.path.insert(1, HERE)

FILES = [
    "test_cache_key_scope",
    "test_curation_parse",
    "test_scope_detect",
    "test_verse_ref_parse",
    "test_lexica_book_norm",
    "test_lexica_coverage",
    "test_number_fold",
    "test_lexica_draw_cache",
]


def _run_one(fn):
    """None on pass, else the failure text."""
    try:
        fn()
        return None
    except Exception:
        return traceback.format_exc(limit=3)


def _control_must_fail():
    assert 1 == 2, "control"


def main() -> int:
    if _run_one(_control_must_fail) is None:
        print("CONTROL FAILED: the runner did not catch a failing test — trusting nothing.")
        return 1
    total = bad = 0
    for name in FILES:
        try:
            spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception:
            bad += 1
            print(f"FAIL: {name} did not import\n{traceback.format_exc(limit=3)}")
            continue
        tests = [k for k in vars(mod) if k.startswith("test_") and callable(getattr(mod, k))]
        if not tests:
            bad += 1
            print(f"FAIL: {name} has no test_* functions")
            continue
        file_bad = 0
        for k in tests:
            total += 1
            err = _run_one(getattr(mod, k))
            if err:
                file_bad += 1
                print(f"FAIL: {name}.{k}\n{err}")
        bad += file_bad
        if not file_bad:
            print(f"  ok: {name} ({len(tests)} tests)")
    if bad:
        print(f"\n{bad} FAILURE(S) of {total}")
        return 1
    print(f"\nAll {total} plain-style tests passed ({len(FILES)} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

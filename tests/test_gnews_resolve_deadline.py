#!/usr/bin/env python3
"""Locks the hard stop on the Google redirect lookup (scripts/news/gnews_resolve.resolve) —
ruling 2026-10-25.

Why: PA runs googlenewsdecoder 0.1.7 (pinned in requirements.txt), whose gnewsdecoder() takes no
timeout and makes requests calls with none. Every caller comes through resolve(): the live site's
Copy-shortlist resolver (a web worker), the nightly headline-link job, the backfills and the
page-date check. One silent Google connection used to wait forever (a page-date dry run sat
1h45m). resolve() must give up within its limit and return None — never hang, never raise.

The real library is replaced by a stub, so this runs offline in CI (which doesn't install it).
Run from repo root:  python tests/test_gnews_resolve_deadline.py
"""
import os
import sys
import time
import types
import threading

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

WRAPPER = "https://news.google.com/rss/articles/CBMiTEST?oc=5"
_release = threading.Event()          # lets the "hung" stub threads finish at the end
calls = []


def _install(fn):
    mod = types.ModuleType("googlenewsdecoder")
    mod.gnewsdecoder = fn
    sys.modules["googlenewsdecoder"] = mod


def never_returns(source_url, interval=None, proxy=None):     # 0.1.7's real signature
    calls.append(("hang", source_url, interval))
    _release.wait(60)
    return {"status": True, "decoded_url": "https://too-late.example/"}


def answers(source_url, interval=None, proxy=None):
    calls.append(("ok", source_url, interval))
    return {"status": True, "decoded_url": "https://real.example/article"}


def raises(source_url, interval=None, proxy=None):
    raise RuntimeError("429")


from scripts.news.gnews_resolve import resolve, RESOLVE_LIMIT   # noqa: E402

n = 0


def test(name, fn):
    global n
    fn()
    n += 1
    print("ok  " + name)


def t_hang():
    _install(never_returns)
    t0 = time.time()
    got = resolve(WRAPPER, timeout=0.5)
    took = time.time() - t0
    assert got is None, got
    assert took < 2.0, f"took {took:.1f}s - the hard stop did not hold"


def t_default_limit_is_bounded():
    assert 0 < RESOLVE_LIMIT <= 60, RESOLVE_LIMIT


def t_normal():
    _install(answers)
    assert resolve(WRAPPER) == "https://real.example/article"
    assert calls[-1] == ("ok", WRAPPER, 1)       # called WITHOUT a timeout kwarg (0.1.7 has none)


def t_failures():
    _install(raises)
    assert resolve(WRAPPER) is None                              # library error: None, no raise
    _install(lambda u, interval=None, proxy=None: {"status": False, "message": "x"})
    assert resolve(WRAPPER) is None                              # library says no: None
    assert resolve("https://example.com/not-a-wrapper") is None  # not a Google link: untouched


try:
    test("a lookup that never returns is cut off at the limit (returns None)", t_hang)
    test("the default limit is a real, bounded number", t_default_limit_is_bounded)
    test("a normal lookup returns the real link (no timeout kwarg passed)", t_normal)
    test("library errors / refusals / non-Google links -> None, never raise", t_failures)
finally:
    _release.set()
    sys.modules.pop("googlenewsdecoder", None)

print(f"\n{n} passed")

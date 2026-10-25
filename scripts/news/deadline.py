#!/usr/bin/env python3
"""deadline.py — a hard wall-clock stop for one call. ONE copy, shared by the Google redirect
lookup (gnews_resolve.resolve — the live site's Copy-shortlist resolver and the nightly
headline-link job) and the page-date check (date_pass).

Why it exists: PA runs googlenewsdecoder 0.1.7, whose gnewsdecoder() takes NO timeout and makes
requests calls with none, so one silent Google connection can wait forever (it froze the first
full page-date dry run for 1h45m, 2026-10-25). A library timeout setting can't fix that — this
version drops it — so the call runs in a background thread and the caller stops waiting after
`secs`. The abandoned thread is a daemon: it can't hold the process open, and it ends whenever
its connection finally gives up.
"""
import threading

TIMED_OUT = object()


def with_deadline(fn, *args, secs):
    """fn(*args), or TIMED_OUT if it hasn't returned within `secs` seconds. An exception inside
    fn counts as None (every caller already treats None as 'nothing found')."""
    box = {}

    def run():
        try:
            box["v"] = fn(*args)
        except Exception:
            box["v"] = None

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(secs)
    return TIMED_OUT if t.is_alive() else box.get("v")

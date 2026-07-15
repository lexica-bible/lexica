#!/usr/bin/env python3
"""News watch has TWO gates and they must not collapse into each other.

  read  (_can_read)  — any signed-in account, ANY tier, or the no-login share key
  write (_reviewer)  — admin or share-key holder only

THE TRAP THIS EXISTS FOR (found in the 2026-07-15 audit): /api/news/resolve is a WRITE
(it caches into items.resolved_url and fires outbound fetches) that was gated on
_can_read(). While reads were admin-only that was invisible — everyone who could read
could also write, so the two gates were the same set and nothing could tell them apart.
Opening reads to every account is exactly what pulls them apart, and it would have opened
resolve as a side effect. Anyone who later "tidies" resolve back onto the read gate
reintroduces it silently, because the routes still return 200 for the admin who tests it.

No DB, no request context: the collaborators (is_logged_in / is_admin / ai_caller /
_shared_key_ok) are swapped for stubs, so this runs offline in CI.
"""
import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import views_news


class _Gate:
    """Swap in one caller identity for the duration of a check, then put it all back."""

    def __init__(self, *, logged_in=False, admin=False, uid=None, role="nologin", key=False):
        self.patch = {
            "is_logged_in": lambda: logged_in,
            "is_admin": lambda: admin,
            "ai_caller": lambda: (role, uid),
            "_shared_key_ok": lambda: key,
        }

    def __enter__(self):
        self.saved = {k: getattr(views_news, k) for k in self.patch}
        for k, v in self.patch.items():
            setattr(views_news, k, v)
        return self

    def __exit__(self, *exc):
        for k, v in self.saved.items():
            setattr(views_news, k, v)
        return False


# The five identities that can hit this blueprint, and what each is allowed to do.
# (label, gate kwargs, may_read, may_write)
CASES = [
    ("anonymous",    dict(),                                                   False, False),
    ("plain user",   dict(logged_in=True, role="user", uid=7),                 True,  False),
    ("berean",       dict(logged_in=True, role="berean", uid=8),               True,  False),
    ("admin",        dict(logged_in=True, admin=True, role="admin", uid=1),    True,  True),
    ("share key",    dict(key=True),                                           True,  True),
]


def _check(fails, label, got, want):
    if got != want:
        fails.append(f"{label}: got {got!r}, want {want!r}")


def check_gate_truth_table(fails):
    """Every identity reads/writes exactly what it should — including the two that make
    the gates differ at all: a plain account (reads, cannot write) and anonymous (neither)."""
    for label, kw, may_read, may_write in CASES:
        with _Gate(**kw):
            _check(fails, f"read/{label}", views_news._can_read(), may_read)
            _, can_write = views_news._reviewer()
            _check(fails, f"write/{label}", can_write, may_write)


def check_read_is_not_tier_based(fails):
    """The gate is auth-only BY RULING — a plain 'user' reads the same feed as a berean.
    A tier check sneaking in here would still pass the truth table above if someone only
    updated the expected values, so state the invariant itself."""
    with _Gate(logged_in=True, role="user", uid=7):
        plain = views_news._can_read()
    with _Gate(logged_in=True, role="berean", uid=8):
        berean = views_news._can_read()
    _check(fails, "tier-free read (user == berean)", plain, berean)


def check_reviewer_ids_stay_separate(fails):
    """An admin and a share-key holder must never land on the same reviewer id — their
    keep/dismiss rows are scoped by it, so a collision would cross their triage."""
    with _Gate(logged_in=True, admin=True, role="admin", uid=1):
        admin_rid, _ = views_news._reviewer()
    with _Gate(key=True):
        key_rid, _ = views_news._reviewer()
    _check(fails, "admin reviewer id prefix", str(admin_rid).startswith("u"), True)
    _check(fails, "share-key reviewer id prefix", str(key_rid).startswith("k"), True)
    _check(fails, "admin != share-key id", admin_rid != key_rid, True)


def check_resolve_sits_on_the_write_gate(fails):
    """resolve must gate on can_write, NOT on _can_read. Source-level on purpose: the
    routes need a request context + news.db to exercise, and the regression is invisible
    to anyone testing as admin (who passes both gates).

    Control (the rule that a detector must fire on a known positive): the same check is
    run against a real READ route, which MUST show the opposite shape. If read routes stop
    reading as read-gated, this check has gone blind and its silence means nothing."""
    write_src = inspect.getsource(views_news.resolve_urls)
    _check(fails, "resolve gates on can_write", "can_write" in write_src, True)
    _check(fails, "resolve does NOT gate on _can_read", "_can_read" not in write_src, True)

    read_src = inspect.getsource(views_news.list_news)
    _check(fails, "CONTROL: a read route still gates on _can_read",
           "_can_read" in read_src, True)
    _check(fails, "CONTROL: a read route does not gate on can_write",
           "can_write" not in read_src, True)


def check_status_stays_on_the_write_gate(fails):
    """status was already correct — lock it so the resolve fix can't be 'matched' by
    dragging status the other way."""
    src = inspect.getsource(views_news.set_status)
    _check(fails, "status gates on can_write", "can_write" in src, True)
    _check(fails, "status does NOT gate on _can_read", "_can_read" not in src, True)


def main():
    fails = []
    for check in (check_gate_truth_table,
                  check_read_is_not_tier_based,
                  check_reviewer_ids_stay_separate,
                  check_resolve_sits_on_the_write_gate,
                  check_status_stays_on_the_write_gate):
        check(fails)
        print(f"  ran {check.__name__}")
    if fails:
        print(f"\n{len(fails)} FAILED")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("\nNews gates hold: reads auth-only + tier-free, writes admin/share-key only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

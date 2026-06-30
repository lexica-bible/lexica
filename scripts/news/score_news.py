#!/usr/bin/env python3
"""
score_news.py — let Haiku rate each gathered article against Tudor's worldview.

WHAT IT DOES
  - Reads news.db for articles that haven't been scored yet.
  - Sends them to Haiku in small batches with the WORLDVIEW as the brief (not a
    keyword list — so it can also flag a fresh angle nobody put on the list).
  - Writes back, per article: a 0-10 relevance score, the best-fit thread (or
    "new"), a "new angle?" flag, and a one-line reason.
  - Re-runnable: it only looks at articles with no score yet, so a second run
    just picks up whatever the last gather added.

THE KEY
  Like the nightly health-check, a scheduled run can't see the web app's
  settings. Put ANTHROPIC_API_KEY in ~/bible-db/.env (the same file the health
  check uses) and this script reads it. Or export it in the shell before running.

USAGE
  python3 scripts/news/score_news.py              # score everything not yet scored
  python3 scripts/news/score_news.py --limit 20   # only the next 20 (a test batch)
  python3 scripts/news/score_news.py --batch 8    # articles per AI call (default 8)
  python3 scripts/news/score_news.py --dry-run    # print verdicts, save nothing
  python3 scripts/news/score_news.py --rescore    # redo ALL articles (after a prompt change)
"""
import os
import re
import sys
import json
import time
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from queries import THREADS  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(REPO_ROOT, "news.db")

# Load the key from ~/bible-db/.env BEFORE we build the AI client (a cron run has
# no web-app settings). Read the file ourselves so this works under a plain
# `python3` too — no python-dotenv needed (the web app's venv has it, but a cron
# or a bare shell may not).
def _load_env_file(path):
    """Pull simple KEY=VALUE lines from a .env into the environment. Won't clobber
    a value already set in the shell. Tolerates quotes, blank lines, and #comments."""
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass


_load_env_file(os.path.join(REPO_ROOT, ".env"))

DRY_RUN = "--dry-run" in sys.argv
RESCORE = "--rescore" in sys.argv


def _arg(flag, default=None, cast=str):
    if flag + "=" in " ".join(a + ("=" if "=" in a else "") for a in sys.argv):
        for a in sys.argv:
            if a.startswith(flag + "="):
                return cast(a.split("=", 1)[1])
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return cast(sys.argv[i + 1])
    return default


LIMIT = _arg("--limit", 0, int)
BATCH = _arg("--batch", 8, int)
DB_PATH = _arg("--db", DEFAULT_DB)

MODEL = "claude-haiku-4-5-20251001"

# The thread menu Haiku picks from — built straight off the watch list so the two
# never drift. "new" is always an option for a fresh angle not covered here.
_THREAD_MENU = "\n".join(f"  - {k}: {v['label']}" for k, v in THREADS.items())
_VALID_THREADS = set(THREADS.keys()) | {"new"}

SYSTEM = f"""You are an analyst helping a Bible-prophecy researcher triage the news.
He reads current events through a historicist, "two-beasts" framework. Your job is
NOT to judge whether his theology is right — it is to rate how strongly each news
item ADVANCES the specific storyline he is watching, so he can decide what to cover
on his podcast.

THE STORYLINE (his lens):
A manufactured sense of crisis pushes the public to cry out for moral order, and
that authority consolidates under Rome (the Vatican / papacy) — governments,
Protestant and other denominations, and even technology/AI deferring to the church
as the moral arbiter, with the United States acting as the enforcing power. The
"two beasts" endgame: Rome leading, America enforcing.

THREADS he watches (pick the best-fit key, or "new"):
{_THREAD_MENU}

For EACH article, judging only its headline and blurb, decide:
  - score (0-10): how strongly it advances the storyline. 0 = unrelated noise that
    only matched a search by keyword. 10 = a direct, unmistakable step (e.g. a tech
    leader endorsing church oversight of AI, a Protestant body submitting to Rome,
    a worship/rest law, a digital-ID payment mandate).
  - thread: the single best-fit key from the list, or "new" if it genuinely advances
    the storyline through an angle the list doesn't name.
  - new_flag: 1 only if thread is "new", else 0.
  - why: ONE short, plain sentence on why it fits — or why it's borderline.

Be sober. MOST general headlines should land 0-3. Reserve 7-10 for items that
clearly move a thread. Do not force-fit a keyword match into a high score."""

USER_HEAD = ("Score these articles. Return ONLY a JSON array — one object per "
             "article, keys exactly: id, score, thread, new_flag, why.\n\n")

_FENCE = re.compile(r"^```(?:json)?|```$", re.MULTILINE)

# Haiku sees each article in a batch as "id=NNN | ...", so it sometimes writes a
# back-reference reason ("Same event as id=12345") instead of a real one. That id
# means nothing to a reader and leaks into the card body, so drop the whole reason
# when it's just a pointer at another article.
_BACKREF_WHY = re.compile(
    r"^\s*(?:same(?:\s+event)?\s+as|same\s+story\s+as|duplicate\s+of|see)\s+(?:id\s*=?\s*)?\d+",
    re.IGNORECASE)


def _clean_why(why):
    return "" if _BACKREF_WHY.match(why or "") else (why or "")


def build_client():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ANTHROPIC_API_KEY not set. Put it in ~/bible-db/.env or export it "
                 "(grab it from /var/www/www_lexica_bible_wsgi.py).")
    import anthropic
    return anthropic.Anthropic(api_key=key)


def score_batch(client, rows):
    """Send one batch to Haiku, return {id: verdict-dict}."""
    lines = []
    for r in rows:
        blurb = (r["summary"] or "")[:300]
        lines.append(f'id={r["id"]} | {r["title"]} | source: {r["source"] or "?"} '
                     f'| blurb: {blurb}')
    msg = client.messages.create(
        model=MODEL,
        max_tokens=900,
        temperature=0,
        system=SYSTEM,
        messages=[{"role": "user", "content": USER_HEAD + "\n".join(lines)}],
    )
    text = msg.content[0].text.strip() if msg.content else "[]"
    text = _FENCE.sub("", text).strip()
    try:
        data = json.loads(text)
    except Exception:
        # Last-ditch: grab the outermost [ ... ] and try again.
        m = re.search(r"\[.*\]", text, re.DOTALL)
        data = json.loads(m.group(0)) if m else []
    out = {}
    for d in data:
        try:
            vid = int(d["id"])
        except Exception:
            continue
        thread = d.get("thread") or "new"
        if thread not in _VALID_THREADS:
            thread = "new"
        score = max(0, min(10, int(d.get("score", 0))))
        out[vid] = {
            "score": score,
            "thread": thread,
            "new_flag": 1 if (d.get("new_flag") or thread == "new") else 0,
            "why": _clean_why((d.get("why") or "").strip())[:240],
        }
    return out


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    where = "" if RESCORE else "WHERE score IS NULL"
    sql = f"SELECT id, title, source, summary FROM items {where} ORDER BY id"
    if LIMIT:
        sql += f" LIMIT {LIMIT}"
    rows = conn.execute(sql).fetchall()
    if not rows:
        print("nothing to score (all caught up).")
        return

    print(f"{'DRY RUN — ' if DRY_RUN else ''}scoring {len(rows)} articles "
          f"in batches of {BATCH}")
    client = build_client()

    done = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        try:
            verdicts = score_batch(client, batch)
        except Exception as e:
            print(f"  ERR  batch at {i}: {str(e)[:80]}")
            continue
        for r in batch:
            v = verdicts.get(r["id"])
            if not v:
                continue
            done += 1
            if DRY_RUN:
                tag = f'{v["score"]:2d}/10 [{v["thread"]}]'
                print(f'  {tag:34s} {r["title"][:64]}')
                print(f'       └ {v["why"]}')
            else:
                conn.execute(
                    "UPDATE items SET score=?, ai_thread=?, ai_new_flag=?, ai_why=? "
                    "WHERE id=?",
                    (v["score"], v["thread"], v["new_flag"], v["why"], r["id"]))
        if not DRY_RUN:
            conn.commit()
        time.sleep(0.5)

    conn.close()
    print(f"\n{'(dry run) ' if DRY_RUN else ''}scored {done}/{len(rows)} articles")


if __name__ == "__main__":
    main()

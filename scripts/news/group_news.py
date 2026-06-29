#!/usr/bin/env python3
"""
group_news.py — let Haiku group the scored articles by the real-world EVENT.

Word-matching can't tell that "Pope Leo urges AI disarmament", "Magnifica Humanitas
discussion", and "42,000-word letter on AI" are the SAME encyclical — they share no
distinctive words. So here the AI reads the headlines together and tags each with a
short canonical event label. The tab then collapses everything sharing a label into
ONE card. Haiku sees the running list of labels it's already used, so the same event
gets the same label across batches (that's what keeps it consistent).

Re-runnable: only fills articles that don't have an event yet, so a nightly run just
labels whatever the last gather/score added. Pairs with gather_news + score_news.

USAGE
  python3 scripts/news/group_news.py              # label scored, unlabeled articles
  python3 scripts/news/group_news.py --min 5      # only score >=5 (default; saves cost)
  python3 scripts/news/group_news.py --batch 40   # headlines per AI call (default 40)
  python3 scripts/news/group_news.py --dry-run    # show labels, save nothing
  python3 scripts/news/group_news.py --regroup    # redo ALL (after a prompt change)

The key comes from ~/bible-db/.env (same as score_news.py).
"""
import os
import re
import sys
import json
import time
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(REPO_ROOT, "news.db")


def _load_env_file(path):
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip(); v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


_load_env_file(os.path.join(REPO_ROOT, ".env"))

DRY_RUN = "--dry-run" in sys.argv
REGROUP = "--regroup" in sys.argv


def _arg(flag, default, cast=str):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
            return cast(sys.argv[i + 1])
    return default


MIN = _arg("--min", 5, int)
BATCH = _arg("--batch", 40, int)
DB_PATH = _arg("--db", DEFAULT_DB)
MODEL = "claude-haiku-4-5-20251001"

SYSTEM = """You group news headlines by the real-world EVENT each one is about, so that
duplicate coverage of one event collapses into a single item.

Rules:
- Headlines about the SAME event get the SAME label — even when worded completely
  differently (e.g. "Pope Leo urges AI disarmament", "Magnifica Humanitas discussion",
  and "Pope's 42,000-word letter on AI" are all the same encyclical → one label).
- Genuinely different events get different labels.
- A label is SHORT (3-6 words), Title Case, and names the event concretely, e.g.
  "Pope Leo AI Encyclical", "Pentagon-Vatican Meeting Clash", "Trump-Pope Leo Tension",
  "Vatican AI Ethics Commission".
- REUSE an existing label (you'll be given the ones already in use) whenever a headline
  fits it. Only invent a new label when none fits.
- Do NOT create a separate label for a LATER PHASE of an event you have already
  labeled (its launch, release, reaction, vote, ruling, or follow-up) — reuse the base
  label so all coverage of one event stays in one card.

Return ONLY a JSON array, one object per headline, keys exactly: id, event."""

_FENCE = re.compile(r"^```(?:json)?|```$", re.MULTILINE)


def build_client():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ANTHROPIC_API_KEY not set. Put it in ~/bible-db/.env or export it.")
    import anthropic
    return anthropic.Anthropic(api_key=key)


def label_batch(client, rows, known):
    known_txt = ("\n".join(f"  - {k}" for k in known)) if known else "  (none yet)"
    lines = [f'id={r["id"]} | {r["title"]}' for r in rows]
    user = ("Existing labels already in use:\n" + known_txt +
            "\n\nGroup these headlines. Reuse a label above when it fits.\n\n" +
            "\n".join(lines))
    msg = client.messages.create(
        model=MODEL, max_tokens=1600, temperature=0,
        system=SYSTEM, messages=[{"role": "user", "content": user}],
    )
    text = msg.content[0].text.strip() if msg.content else "[]"
    text = _FENCE.sub("", text).strip()
    try:
        data = json.loads(text)
    except Exception:
        m = re.search(r"\[.*\]", text, re.DOTALL)
        data = json.loads(m.group(0)) if m else []
    out = {}
    for d in data:
        try:
            vid = int(d["id"])
        except Exception:
            continue
        ev = (d.get("event") or "").strip()[:80]
        if ev:
            out[vid] = ev
    return out


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cols = [r[1] for r in conn.execute("PRAGMA table_info(items)")]
    if "event" not in cols:
        conn.execute("ALTER TABLE items ADD COLUMN event TEXT")
        conn.commit()

    where = "score IS NOT NULL AND score >= ?"
    if not REGROUP:
        where += " AND (event IS NULL OR event = '')"
    rows = conn.execute(
        f"SELECT id, title FROM items WHERE {where} ORDER BY score DESC, published DESC",
        (MIN,)).fetchall()
    if not rows:
        print("nothing to group (all caught up).")
        return

    print(f"{'DRY RUN — ' if DRY_RUN else ''}grouping {len(rows)} articles "
          f"(score >= {MIN}) in batches of {BATCH}")
    client = build_client()

    known = []                       # running list of labels, for cross-batch consistency
    known_set = set()
    done = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        try:
            labels = label_batch(client, batch, known)
        except Exception as e:
            print(f"  ERR  batch at {i}: {str(e)[:80]}")
            continue
        for r in batch:
            ev = labels.get(r["id"])
            if not ev:
                continue
            if ev not in known_set:
                known_set.add(ev); known.append(ev)
            done += 1
            if DRY_RUN:
                print(f"  {ev[:34]:34s} | {r['title'][:60]}")
            else:
                conn.execute("UPDATE items SET event = ? WHERE id = ?", (ev, r["id"]))
        if not DRY_RUN:
            conn.commit()
        time.sleep(0.4)

    conn.close()
    print(f"\n{'(dry run) ' if DRY_RUN else ''}labeled {done} articles into "
          f"{len(known)} events")


if __name__ == "__main__":
    main()

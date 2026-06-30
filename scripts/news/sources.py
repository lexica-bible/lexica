#!/usr/bin/env python3
"""
sources.py — outlet RSS feeds for the Phase-4 by-outlet ingestion path.

The Google-News path (queries.py) searches the whole web by TOPIC. This file is
the other half: a fixed list of OUTLET feeds we pull straight from the source.
Both paths feed the same shelf (news.db items table); scoring + grouping pick up
new rows automatically, and the card layer merges same-event duplicates across
the two paths (a direct outlet link and a Google redirect link are different
strings, so they never collide as rows — the merge happens at the card).

An outlet feed is a firehose: most of it is off-topic. So each source has a
GATE level:
  - "light": already-aligned / niche source — save everything, let the score>=5
    grouping floor trim it. Light is recoverable (a low-scored item still sits on
    the shelf and can resurface).
  - "hard": broad mainstream firehose — the item must mention a watch term
    (queries.gate_vocabulary()) in its title/blurb or it's dropped at ingest.
    A hard drop leaves NO row and can't be recovered, so it's reserved for true
    firehoses only.
Anything ambiguous between the two defaults to "light".

thread_hint = the seed thread we tag the row's `thread` column with. The AI
scorer assigns the real `ai_thread` later (that's what the feed displays), so
thread_hint is only a hint / provenance note — it never has to be exactly right.

Endpoint notes (verified 2026-06-30):
  - CNA now redirects to EWTN News; we point straight at the final URL.
  - ZeroHedge's old /fullrss2.xml and /rss.xml are dead; FeedBurner is live.
  - LifeSiteNews /rss/ redirects to /feed/.
  - NCR / End Time Headlines / Adventist News couldn't be machine-confirmed
    (bot-block / rate-limit); the PA dry-run (inserted>0 per source) confirms them.
  - European Sunday Alliance is HELD for wave 2 — it serves a self-signed TLS
    cert that feedparser/urllib reject; do not add it without a working cert or
    an explicit insecure-fetch decision.
"""

SOURCES = [
    # --- Vatican / Catholic core (light: mostly on-topic already) ------------
    {"url": "https://www.vaticannews.va/en.rss.xml", "name": "Vatican News",
     "gate_level": "light", "thread_hint": "papacy_moral_authority"},
    {"url": "https://www.ewtnnews.com/rss", "name": "EWTN News (CNA)",
     "gate_level": "light", "thread_hint": "papacy_moral_authority"},
    {"url": "https://www.pillarcatholic.com/feed", "name": "The Pillar",
     "gate_level": "light", "thread_hint": "papacy_moral_authority"},
    {"url": "https://www.ncregister.com/rss", "name": "National Catholic Register",
     "gate_level": "light", "thread_hint": "papacy_moral_authority"},
    {"url": "https://www.lifesitenews.com/feed/", "name": "LifeSiteNews",
     "gate_level": "light", "thread_hint": "culture_shaping"},

    # --- Niche / aligned watch sources (light) -------------------------------
    {"url": "https://novusordowatch.org/feed/", "name": "Novus Ordo Watch",
     "gate_level": "light", "thread_hint": "ecumenism"},
    {"url": "https://www.complicitclergy.com/feed/", "name": "Complicit Clergy",
     "gate_level": "light", "thread_hint": "papacy_moral_authority"},
    {"url": "https://adventmessenger.org/feed/", "name": "Advent Messenger",
     "gate_level": "light", "thread_hint": "sabbath_sunday"},
    {"url": "https://endtimeheadlines.org/feed/", "name": "End Time Headlines",
     "gate_level": "light", "thread_hint": "signs_wonders"},

    # --- Gap-fillers (light) -------------------------------------------------
    {"url": "https://orthodoxtimes.com/feed/", "name": "Orthodox Times",
     "gate_level": "light", "thread_hint": "ecumenism_orthodox"},
    {"url": "https://adventist.news/feed", "name": "Adventist News Network",
     "gate_level": "light", "thread_hint": "protestant_collapse"},

    # --- Broad firehose canary (hard gate) -----------------------------------
    {"url": "https://feeds.feedburner.com/zerohedge/feed", "name": "ZeroHedge",
     "gate_level": "hard", "thread_hint": "political_realignment"},
]


if __name__ == "__main__":
    # Quick sanity print.
    light = sum(1 for s in SOURCES if s.get("gate_level") != "hard")
    hard = len(SOURCES) - light
    for s in SOURCES:
        print(f"  {s.get('gate_level','light'):5s}  {s['name']:28s} {s['url']}")
    print(f"\n{len(SOURCES)} feeds — {light} light, {hard} hard")

#!/bin/bash
# Lexica news — nightly gather -> score -> group. Point the PA scheduled task here:
#   bash ~/bible-db/scripts/news/daily.sh
#
# INCREMENTAL on purpose: score_news and group_news only touch stories that came
# in tonight. Do NOT add --rescore here — that re-tags the WHOLE corpus and costs
# Haiku money every single night. --rescore is a by-hand step, only run after the
# thread list in queries.py changes.
#
# Runs the bible-env venv's python directly. The system python3 on PA does NOT
# have the `anthropic` package, so a scheduled task that calls plain `python3`
# fails silently at the scoring step. This is the usual PA scheduled-task gotcha.

cd ~/bible-db || exit 1

PY="$HOME/.virtualenvs/bible-env/bin/python"
if [ ! -x "$PY" ]; then
  echo "ERROR: venv python missing at $PY (the anthropic package lives in bible-env)." >&2
  exit 1
fi

echo "==> [$(date -u '+%F %T') UTC] gathering new stories..."
"$PY" scripts/news/gather_news.py

echo "==> pulling outlet RSS feeds..."
"$PY" scripts/news/pull_rss.py

echo "==> scoring new stories (incremental — no --rescore)..."
"$PY" scripts/news/score_news.py

echo "==> grouping new stories into events..."
"$PY" scripts/news/group_news.py

echo "==> resolving new-story faces (forward-fill)..."
"$PY" scripts/news/resolve_new_faces.py || true

# DISABLED 2026-07-05 — resolve_backfill_all.py crashed mid-flush and corrupted news.db
# (see diagnosis). Re-enable only after the flush/connection issue is fixed. The RSS pull,
# scoring, grouping, and forward-fill (resolve_new_faces) above are unaffected.
# echo "==> backfill archive wrapper-faces (capped)..."
# "$PY" scripts/news/resolve_backfill_all.py --limit 1000 --workers 3 --sleep 1.0 || true

echo "==> news refresh done."

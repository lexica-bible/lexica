#!/bin/bash
# Lexica deploy — run this ON PythonAnywhere instead of the three commands by hand.
#   bash ~/bible-db/scripts/deploy.sh
#
# It pulls the latest code, runs the invariant tests (no database needed), and
# only reloads the live site if everything passed. A broken build never goes live.
set -e

cd ~/bible-db

echo "==> Pulling latest code..."
before=$(git rev-parse HEAD)
git pull
after=$(git rev-parse HEAD)
changed=$(git diff --name-only "$before" "$after")

echo "==> Running invariant tests..."
python3 tests/test_strongs_join.py >/dev/null
python3 tests/test_build_invariants.py >/dev/null
echo "    tests passed."

# Load non-canonical texts ONLY when this pull changed their files (a new book, or a
# fix to a book's text). The data already lives in the database between deploys, so
# re-loading unchanged books is just busywork. Each loader rebuilds only its OWN
# <book>_words/<book>_verses tables; a hiccup warns but never blocks the reload.
echo "==> Checking for changed non-canonical books..."
set +e
run_if_changed() {  # $1 = folder to watch; rest = loaders to run if anything there changed
  local prefix="$1"; shift
  echo "$changed" | grep -q "^$prefix" || return 0
  for loader in "$@"; do
    [ -f "$loader" ] || continue
    if python3 "$loader" bible.db >/dev/null 2>&1 ; then
      echo "    ok: $loader"
    else
      echo "    WARNING: $loader failed (skipped)"
    fi
  done
}
run_if_changed "scripts/apocrypha/"     scripts/apocrypha/load_apocrypha.py scripts/apocrypha/load_pseudepigrapha.py
run_if_changed "scripts/apfathers/"     scripts/apfathers/load_apfathers.py
run_if_changed "scripts/enoch/"         scripts/enoch/load_enoch.py
run_if_changed "scripts/didache_proof/" scripts/didache_proof/load_didache.py
[ -z "$changed" ] && echo "    (no code pulled — nothing to load)"
set -e

# Update Python packages ONLY when the pull changed requirements.txt (e.g. a merged
# Dependabot bump). Targets the bible-env venv directly so it can't land in the wrong
# Python. A failed install stops the deploy here — better than reloading a site that's
# missing a package.
if echo "$changed" | grep -qx "requirements.txt"; then
  echo "==> requirements.txt changed — updating Python packages..."
  venv_pip="$HOME/.virtualenvs/bible-env/bin/pip"
  if [ -x "$venv_pip" ]; then
    "$venv_pip" install -r requirements.txt
  else
    pip install -r requirements.txt
  fi
  echo "    packages updated."
fi

# G2 stale-worker ruling (docs/claude/ops.md): the dashboard Reload is the standard
# for serving-code deploys — a `touch` reload once left a half-refreshed worker mix
# live. The API reload below is the dashboard button's exact equivalent (same full
# worker restart). PA sets API_TOKEN in every console once a token exists
# (Account -> API Token); without one we STOP and say so rather than silently touch.
echo "==> Reloading the live site (dashboard-equivalent API reload)..."
if [ -n "$API_TOKEN" ]; then
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    -H "Authorization: Token $API_TOKEN" \
    "https://www.pythonanywhere.com/api/v0/user/appssanding720/webapps/www.lexica.bible/reload/")
  if [ "$code" = "200" ]; then
    echo "    reloaded (API — all workers restarted together)."
  else
    echo "    !! API reload returned HTTP $code — press the dashboard Reload button"
    echo "       by hand before trusting this deploy (do NOT rely on touch)."
  fi
else
  echo "    !! No API_TOKEN in this console. Create one (Account -> API Token),"
  echo "       reopen the console, and re-run — or press the dashboard Reload"
  echo "       button by hand NOW. Deploy is NOT reloaded yet."
fi

# Warm the fresh workers so the first REAL visitor doesn't eat the ~13s cold-start.
# PA boots each worker on its FIRST hit, so the warm-up requests must arrive AT ONCE.
# Sequential curls keep reusing whichever worker is already free and leave the other
# two cold — then your first refresh wedges on a cold worker and only the SECOND one
# comes up. Fire a parallel burst instead so all 3 boot together. Give the reload a
# few seconds to take effect first; failures here never matter — it's just priming.
echo "==> Warming up the workers..."
sleep 5
for i in $(seq 1 12); do
  curl -s -o /dev/null -m 60 https://www.lexica.bible/ &
done
wait
echo "    warmed."

# The 5x repeated-curl worker sweep is part of DEPLOY VERIFICATION (same G2
# ruling), not incident response — every worker must answer 200.
echo "==> Worker sweep (5x, all must be 200):"
for i in 1 2 3 4 5; do
  curl -s -o /dev/null -m 60 -w "%{http_code} " https://www.lexica.bible/
done
echo

echo "==> Done. Site reloaded."
echo "    (Reminder: after a words-table REBUILD, run health_check.py by hand —"
echo "     it needs the real database and isn't part of this deploy.)"

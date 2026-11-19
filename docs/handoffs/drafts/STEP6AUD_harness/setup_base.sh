# STEP6AUD tests: the base clone (d34d6723 + ONE test-only commit re-pinning cert_manifest.json over the made-up feeds),
# the made-up feeds, and the clean test copies. WSL only; nothing here touches the Windows checkout or any real db.
set -euo pipefail
S6=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/2c800d5c-aa55-4d34-b144-23d87cfc5ca6/scratchpad/s6
WIN=/mnt/c/Users/JP/projects/bible-db
G=~/gate6
rm -rf "$G"; mkdir -p "$G"
git clone -q ~/gate4/repo "$G/base"
cd "$G/base"
[ "$(git log -1 --format=%h)" = d34d6723 ] || { echo "base is not d34d6723"; exit 1; }
git config user.name test; git config user.email test@example.invalid
mkdir -p abp_app_html
cp "$WIN/abp_app_html/abp_app_slots.tsv" "$WIN/abp_app_html/abp_app_slots_italic.tsv" abp_app_html/
mkdir -p "$G/feedhome"
python3 "$S6/mkfeeds.py" "$G/feedhome" "$G/base/bh_scrape.db"
HOME="$G/feedhome" python3 scripts/cert_manifest.py build
git add cert_manifest.json
git commit -q -m "TEST ONLY: cert_manifest.json re-pinned over the made-up STEP6AUD test feeds"
echo "test commit: $(git log -1 --format=%h) - diff vs d34d6723: $(git diff --stat d34d6723 HEAD | tail -1)"
python3 "$S6/mkdbs.py" "$G/base" ~/gate5/home3/bible-db "$G/dbs"
ls -la "$G/dbs"

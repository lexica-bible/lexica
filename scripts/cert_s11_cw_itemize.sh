#!/usr/bin/env bash
# cert_s11_cw_itemize.sh — S11 compare_words itemization (READ-ONLY).
#
# compare_words keys by (verse, position), so two adjacent words trading physical
# positions read as a strongs "swap" at each slot (the symmetric G3588<->noun pattern).
# To separate a REAL re-tag from a benign reorder, dump one "ref|value" line PER WORD
# with NO position: a within-verse reorder yields the identical line-set and cancels in
# a diff, so only a genuinely changed / added / removed value survives. Deterministic —
# plain `sort`, never group_concat's unguaranteed order.
#
# Run on PA:  bash scripts/cert_s11_cw_itemize.sh
set -uo pipefail
cd "$(dirname "$0")/.."
LIVE=bible.db
NEW=bible_test.db.new

dump() {   # $1=db  $2=column  ->  stdout: "Book c:v|value" per word, sorted
  sqlite3 "$1" "SELECT v.book||' '||v.chapter||':'||v.verse||'|'||coalesce(w.$2,'NULL') \
                FROM words w JOIN verses v ON v.id=w.verse_id" | sort
}

echo "===== STRONGS_BASE — real re-tags (physical reorders excluded) ====="
dump "$LIVE" strongs_base > /tmp/sb_live.txt
dump "$NEW"  strongs_base > /tmp/sb_new.txt
diff /tmp/sb_live.txt /tmp/sb_new.txt > /tmp/sb_diff.txt || true
echo "changed word-lines:  <live=$(grep -c '^<' /tmp/sb_diff.txt)   >scratch=$(grep -c '^>' /tmp/sb_diff.txt)"
grep -E '^[<>]' /tmp/sb_diff.txt | sed -E 's/^[<>] //; s/\|.*//' | sort -u > /tmp/retag_verses.txt
echo "distinct verses with a real strongs re-tag: $(wc -l < /tmp/retag_verses.txt)"
echo "-- book distribution --"
awk '{print $1}' /tmp/retag_verses.txt | sort | uniq -c | sort -rn
echo "-- sample verses --"
head -25 /tmp/retag_verses.txt

echo
echo "===== ENGLISH_HEAD — changed verses vs the 208 survivors ====="
dump "$LIVE" english_head > /tmp/eh_live.txt
dump "$NEW"  english_head > /tmp/eh_new.txt
diff /tmp/eh_live.txt /tmp/eh_new.txt | grep -E '^[<>]' | sed -E 's/^[<>] //; s/\|.*//' | sort -u > /tmp/eh_verses.txt
echo "distinct verses with an english_head change: $(wc -l < /tmp/eh_verses.txt)"
echo "-- of those, NOT in AUDIT_reassembly_survivors.txt (want: only corrections + P2 + Mat 12:14) --"
comm -23 /tmp/eh_verses.txt <(sort AUDIT_reassembly_survivors.txt)

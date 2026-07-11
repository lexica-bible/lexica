#!/bin/bash
# fix_psyche_sense4.sh — the JP-ruled 2026-07-11 G5590 psyche sense-4 overclaim fix.
# Six exact swaps via fix_lexica_raw.py (each aborts unless its text occurs exactly once).
# Dry-run by default; pass --apply to write. Record: V9_PILE.md sense-header-overclaim entry.
# Ruling: sense 4 recut to Mat 10:28 attested scope; 1Co 15:45 -> sense 1 (quotes Gen 2:7);
# Mar 8:36 RULED sense-1 life-as-stake (8:35 wordplay); Range + gloss-note restatements swept.
set -e
APPLY="$1"   # "" or --apply

run() {
  python3 ~/bible-db/scripts/fix_lexica_raw.py --word G5590 --old "$1" --new "$2" $APPLY
}

# 1. Sense 4: header + body recut; Mar 8:36 and 1Co 15:45 removed here.
run "**4. The aspect of a person, distinct from the body, that persists beyond bodily death and stands under judgment** — where the contrast with the body is explicit and the point is that the body's destruction does not terminate the soul. (Mat 10:28, kill the body but not the soul; the one able to destroy both soul and body in Gehenna. Mar 8:36, losing one's soul as a loss distinct from and greater than losing the world. 1Co 15:45 recites \"living soul\" as the first-Adam condition in contrast to the life-giving spirit of the last Adam — the soul here marks the merely animate, mortal register of human existence.)" \
    "**4. The soul as distinct from the body — beyond the reach of human violence, standing under God's judgment, God alone able to destroy it** — where the contrast with the body is explicit: men can kill the body but cannot kill the soul; God is able to destroy both soul and body in Gehenna. (Mat 10:28, do not fear the ones killing the body but not able to kill the soul; fear the one able to destroy both soul and body in Gehenna.)"

# 2. Sense 1: 1Co 15:45 inserted beside Gen 2:7 (Paul quotes Gen 2:7 there).
run "living soul; Act 20:10" \
    "living soul; 1Co 15:45, the first man Adam became a living soul — the merely animate, mortal register, contrasted with the life-giving spirit of the last Adam; Act 20:10"

# 3. Sense 1 stake sub-use: Mar 8:36 beside Luk 9:56 (JP ruling B).
run "Luk 9:56, not destroying lives;" \
    "Luk 9:56, not destroying lives; Mar 8:36, suffering loss of one's soul against gaining the whole world — the life as ultimate stake (cf. Mar 8:35);"

# 4. Range sentence: same overclaim, same recut.
run "At its most extended, it designates what survives bodily death and stands under eschatological judgment (Mat 10:28)." \
    "At its most extended, it designates the soul as distinct from the body, beyond human killing and standing under God's judgment (Mat 10:28)."

# 5. Range tail: third restatement of the overclaim.
run "inner disposition, or trans-mortem identity." \
    "inner disposition, or the body-distinct soul under God's judgment."

# 6. Gloss note: un-pair Mar 8:36 from Mat 10:28 (it is now the stake use).
run "The gloss **\"soul\"** at Mat 10:28 and Mar 8:36 is the least freighted option available and matches what the contexts establish: the translators were right not to use \"life\" there, since the contrast with the destructible body is explicit." \
    "The gloss **\"soul\"** at Mat 10:28 is the least freighted option available and matches what the context establishes: the translators were right not to use \"life\" there, since the contrast with the destructible body is explicit. At Mar 8:36 either \"soul\" or \"life\" is defensible — the verse is the life-as-stake use (cf. Mar 8:35)."

echo
echo "All six swaps ${APPLY:+APPLIED}${APPLY:-dry-run OK (nothing written; re-run with --apply)}."

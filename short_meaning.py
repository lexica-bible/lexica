"""The word card's short meaning, built from the card's own "renders as" counts (JP's ruling,
DESIGN 9.253). Greek reads the ABP list, Hebrew the Hebrew OT list, most used first.

  * Forms of one word count as one: spirit + spirits, say + said + saying. A form folds only into
    a base that is ALSO in this word's own list, so "blessed" alone stays "blessed".
  * Up to 3 renderings. After the first, each needs 3% of the word's uses and 3 uses (or, on a
    rare word, 2 uses that are 10% of its uses). A one-off never shows after the first.
  * Filler that a phrase left behind ("holy ONE", "holy PLACE", "himself") never takes a later
    slot, and leads only when no real word has a quarter of the uses.
  * COUNTS_MISLEAD: words whose counts would misinform a reader keep their reviewed gloss.

Pure functions, no database.
"""
from number_fold import normalize as _number_fold

MAX_SHOWN = 3
MIN_SHARE = 0.03    # a later rendering needs 3% of the word's uses...
MIN_USES = 3        # ...and 3 uses, or
RARE_SHARE = 0.10   # ...2 uses that are 10% of a rare word's uses (a one-off never shows)
LEAD_SHARE = 0.25

# Irregular forms -> base. Used only when the base is in the same word's list.
_IRREGULAR = {
    "said": "say", "says": "say", "came": "come", "went": "go", "gone": "go", "goes": "go",
    "saw": "see", "seen": "see", "beheld": "behold", "knew": "know", "known": "know",
    "did": "do", "done": "do", "does": "do", "made": "make", "gave": "give", "given": "give",
    "took": "take", "taken": "take", "heard": "hear", "brought": "bring", "spoke": "speak",
    "spoken": "speak", "stood": "stand", "sat": "sit", "sent": "send", "told": "tell",
    "found": "find", "held": "hold", "kept": "keep", "left": "leave", "lost": "lose",
    "thought": "think", "built": "build", "bought": "buy", "sold": "sell", "sought": "seek",
    "taught": "teach", "struck": "strike", "slew": "slay", "slain": "slay", "wrote": "write",
    "written": "write", "ate": "eat", "eaten": "eat", "drank": "drink", "drunk": "drink",
    "ran": "run", "led": "lead", "fell": "fall", "fallen": "fall", "rose": "rise", "risen": "rise",
    "began": "begin", "begun": "begin", "became": "become", "bore": "bear", "borne": "bear",
    "chose": "choose", "chosen": "choose", "drew": "draw", "drawn": "draw", "drove": "drive",
    "driven": "drive", "flew": "fly", "forgave": "forgive", "forgiven": "forgive", "grew": "grow",
    "grown": "grow", "hid": "hide", "hidden": "hide", "laid": "lay", "lain": "lie", "met": "meet",
    "paid": "pay", "shown": "show", "showed": "show", "sang": "sing", "sung": "sing", "slept": "sleep",
    "swore": "swear", "sworn": "swear", "threw": "throw", "thrown": "throw", "understood": "understand",
    "won": "win", "wept": "weep", "lives": "life", "selves": "self", "wives": "wife", "loaves": "loaf",
    "leaves": "leaf", "wolves": "wolf", "knives": "knife", "thieves": "thief", "sheaves": "sheaf",
    "clothed": "clothe", "died": "die", "dying": "die", "lied": "lie", "lying": "lie", "tied": "tie", "tying": "tie",
}

# -ing words that are nouns in their own right: "offering" must not read "offer".
_ING_NOUNS = frozenset({
    "offering", "blessing", "dwelling", "beginning", "clothing", "evening", "morning", "thing", "king",
    "ring", "wing", "spring", "string", "being", "building", "teaching", "writing", "understanding",
    "meeting", "wedding", "lodging", "gathering", "suffering", "feeling", "warning", "opening", "covering",
    "ending", "binding", "anointing", "rejoicing", "mourning", "weeping", "fasting", "lightning", "sprinkling",
    "ceiling", "sibling", "nothing", "something", "anything", "everything", "tiding", "tidings", "learning",
    "reasoning", "reckoning", "commandment", "planting", "harvesting", "crossing", "landing", "pudding",
})

# Left behind by a phrase ("holy one", "holy place", "the thing"); never a later slot.
_FILLER = frozenset({
    "one", "ones", "thing", "things", "place", "places", "legal", "himself", "herself", "itself",
    "themselves", "yourself", "yourselves", "myself", "ourselves", "away",
})

# Words whose counts mislead, so the header keeps the reviewed gloss. Each with why.
COUNTS_MISLEAD = {
    # Hand overrides kept: the most-used English is a church term or a borrowed word.
    "G5484": "range: favor, kindness", "G5485": "KJV 'grace'", "G166": "'eternal'; plain sense is age-long",
    "G1228": "'devil'", "G3341": "'repentance'", "G3340": "'repent'", "G5486": "plain sense of the gift",
    "G32": "'angel' leads", "G652": "'apostle'", "G4352": "'obeisance' only", "G86": "borrowed 'Hades'",
    "G1067": "borrowed 'Gehenna'", "G39": "'holy' alone; carries set-apart",
    "H7585": "borrowed 'sheol'", "H5769": "'perpetuity, ever'; plain sense is age", "H2617": "'loyalty' alone",
    # Contested or grammatical: one count-led word would take a side or misstate it.
    "G1344": "fork-neutral wording, must not lead 'justified'", "G1510": "forms of 'to be'",
    # Dotted hand overrides: numerals and fixed phrases. The count list keeps only a phrase's last word.
    "G1501.1": "numeral", "G1768.1": "numeral", "G1768.3": "numeral", "G3589.4": "numeral", "G3589.5": "numeral",
    "G5144.9": "numeral", "G4001.3": "numeral", "G4004.4": "'fifty years OLD'", "G1835.4": "'sixty years OLD'",
    "G2193.2": "numeral letter", "G3766.2": "fixed phrase", "G438.1": "particle", "G446.2": "particle",
    "G1758.1": "particle", "G3748.1": "fixed phrase",
    # Hand overrides kept: the source's English is wrong or split at this number.
    "H8577": "'jackals' is a different word", "H5848": "'away'", "H5710": "'yourself'", "H6696": "'siege, fashioned'",
    "H4541": "splits 'molten image'", "H6672": "'noons, noontides'", "H4531": "'despair'", "H6872": "'pebble'",
    "H2006": "'therefore'", "H5599": "'grain'", "H7623": "'calm'", "H7663": "'examining'", "H1238": "too few uses",
    "H5844": "'himself'", "H5860": "three one-off uses",
    # No override, same problem: the head word of a phrase outnumbers the meaning.
    "G1096": "'came to PASS', 'took PLACE'", "G5547": "title", "G2098": "'good NEWS' heads as 'news'",
}


def _candidates(w):
    """Possible base forms of a rendering, most specific first. The number fold comes first, so
    "lives" reaches "live" when the verb is listed and "life" only when it is not; its own guards
    keep "news" whole. An -ing word that is a noun in its own right never folds."""
    n = _number_fold(w)
    out = [n] if n and n != w else []
    if w in _IRREGULAR:
        out.append(_IRREGULAR[w])
        return [c for c in out if c != w]
    if w.endswith("ing") and len(w) >= 5 and w not in _ING_NOUNS:
        s = w[:-3]
        out += [s + "e", s] + ([s[:-1]] if len(s) > 2 and s[-1] == s[-2] else [])
    if w.endswith("ied") and len(w) > 4:
        out.append(w[:-3] + "y")
    if w.endswith("ed") and len(w) > 4:
        s = w[:-2]
        out += [s + "e", s] + ([s[:-1]] if len(s) > 2 and s[-1] == s[-2] else [])
    return [c for c in out if c and c != w]


def fold_renderings(rows):
    """[(rendering, count)] -> [(base, count)], most used first. A form folds only into a base in
    this same list. Ties keep the list's own order."""
    counts = {}
    for g, c in rows:
        counts[g] = counts.get(g, 0) + c
    def base(w, seen=()):
        for c in _candidates(w):
            if c in counts and c not in seen:
                return base(c, seen + (w,))
        return w
    out = {}
    for g, c in counts.items():
        b = base(g)
        out[b] = out.get(b, 0) + c
    return sorted(out.items(), key=lambda x: -x[1])


def from_counts(rows):
    """The short meaning from (rendering, count) rows; "" when there are none."""
    folded = fold_renderings([(g, c) for g, c in rows if g])
    if not folded:
        return ""
    total = sum(c for _g, c in folded)
    # Filler can lead only when no real word has a quarter of the uses: "one, just" reads "just",
    # while εἷς "one" and τόπος "place" keep their own word.
    if folded[0][0] in _FILLER:
        real = next(((g, c) for g, c in folded if g not in _FILLER), None)
        if real and real[1] / total >= LEAD_SHARE:
            folded = [real] + [x for x in folded if x[0] != real[0]]
    shown = [folded[0][0]]
    for g, c in folded[1:]:
        if len(shown) == MAX_SHOWN:
            break
        share = c / total
        if g not in _FILLER and share >= MIN_SHARE and (c >= MIN_USES or (c == 2 and share >= RARE_SHARE)):
            shown.append(g)
    return ", ".join(shown)

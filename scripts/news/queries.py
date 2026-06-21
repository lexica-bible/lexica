#!/usr/bin/env python3
"""
queries.py — the watch list for the end-times news gatherer.

There is NO curated source-site list. Instead, each of Tudor's "threads" is
turned into one or more plain news SEARCHES. The gatherer runs every search
against Google News (which hands back a feed for any query), so we pull whatever
the whole web surfaced for that idea — not just a handful of prophecy blogs.

The underlying story all 12 threads serve (this is also fed to the AI scorer):

    Manufactured crisis -> public cry for moral order -> all authority (states,
    denominations, even tech/AI) consolidating under Rome, with America as the
    enforcer -- the two-beasts endgame.

So a headline does NOT have to mention prophecy to matter. An ordinary news item
(a tech CEO at the Vatican, a Protestant body aligning with Rome, a digital-ID
bill) is exactly the kind of thing this is meant to catch.

Each thread holds a short label + a list of search strings. Keep the searches
SHARP (quoted phrases for exact wording, a couple of OR variants) — a vague
search drowns the feed in noise the AI then has to throw away.
"""

THREADS = {
    "exposure_to_moral_authority": {
        "label": "Dark-to-light: scandal exposed → cry for a moral authority",
        "searches": [
            '"deep state" exposed corruption church',
            'moral crisis "need for" moral leadership society',
            'scandal trust institutions collapse church authority',
        ],
    },
    "papacy_moral_authority": {
        "label": "Papacy stepping in as the world's moral authority",
        "searches": [
            'Vatican global ethics governance',
            'Pope moral authority world leaders',
            'Holy See United Nations moral',
        ],
    },
    "american_pope": {
        "label": "Pope Leo XIV (the American pope) and US–Vatican convergence",
        "searches": [
            '"Pope Leo" America',
            '"Pope Leo XIV"',
            'American pope United States Vatican',
        ],
    },
    "encyclical_political": {
        "label": "Encyclicals / Vatican doctrine going political",
        "searches": [
            'Pope encyclical',
            'Vatican encyclical artificial intelligence',
            'papal document ethics technology',
        ],
    },
    "ai_moralized": {
        "label": "AI being 'moralized' — tech courting the Vatican",
        "searches": [
            'Vatican artificial intelligence ethics',
            'AI companies Vatican meeting',
            'Anthropic OR OpenAI Vatican OR Pope',
            'AI regulation moral framework church',
        ],
    },
    "legislating_morality": {
        "label": "Legislating worship/morality (first four commandments, blasphemy)",
        "searches": [
            'blasphemy law',
            'Sunday rest law legislation',
            'religious observance mandate law',
        ],
    },
    "ecumenism": {
        "label": "Ecumenism / interfaith unity under Rome",
        "searches": [
            'ecumenism Christian unity Rome',
            'interfaith declaration Vatican',
            'church unity movement Pope',
        ],
    },
    "jesuits": {
        "label": "Jesuit statements / signaling",
        "searches": [
            'Jesuits statement',
            'Society of Jesus peace',
        ],
    },
    "trump_vs_leo": {
        "label": "Trump vs. Pope Leo (the two beasts circling)",
        "searches": [
            'Trump Pope Leo',
            'Trump Vatican',
            'White House Holy See tension OR meeting',
        ],
    },
    "alien_agenda": {
        "label": "Alien / UFO disclosure agenda (the strong delusion)",
        "searches": [
            'UFO disclosure congress OR Pentagon',
            'UAP disclosure government',
            'pastors briefed extraterrestrial OR aliens',
        ],
    },
    "protestants_to_rome": {
        "label": "Protestants / denominations folding back into Rome",
        "searches": [
            'evangelical Catholic unity Rome',
            'Protestant denomination reconciliation Vatican',
            'Anglican OR Lutheran full communion Catholic',
        ],
    },
    "financial_control": {
        "label": "Financial control signals (CBDC, digital ID, cashless)",
        "searches": [
            'central bank digital currency CBDC',
            'digital ID payments mandate',
            'cashless society control de-dollarization',
        ],
    },
}


def all_searches():
    """Flat list of (thread_key, search_string) for the gatherer to loop over."""
    out = []
    for key, t in THREADS.items():
        for s in t["searches"]:
            out.append((key, s))
    return out


if __name__ == "__main__":
    # Quick sanity print: how many searches, grouped by thread.
    total = 0
    for key, t in THREADS.items():
        n = len(t["searches"])
        total += n
        print(f"{n:2d}  {key:28s} {t['label']}")
    print(f"\n{len(THREADS)} threads, {total} searches total")

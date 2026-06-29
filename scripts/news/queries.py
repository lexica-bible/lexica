#!/usr/bin/env python3
"""
queries.py — the watch list for the end-times news gatherer.

There is NO curated source-site list. Instead, each of Tudor's "threads" is
turned into one or more plain news SEARCHES. The gatherer runs every search
against Google News (which hands back a feed for any query), so we pull whatever
the whole web surfaced for that idea — not just a handful of prophecy blogs.

The underlying story all 10 threads serve (this is also fed to the AI scorer):

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
    "papacy_moral_authority": {
        "label": "Papacy stepping in as the world's moral authority",
        "searches": [
            'Vatican global ethics governance',
            'Pope moral authority world leaders',
            'Holy See United Nations moral',
            'scandal institutions church authority',
        ],
    },
    "american_pope": {
        "label": "Vatican–US relations (Pope Leo XIV, Trump, White House–Holy See)",
        "searches": [
            '"Pope Leo" America',
            'Trump Vatican',
            'White House Holy See',
            'Pope Leo XIV United States',
        ],
    },
    "encyclical_political": {
        "label": "Encyclicals / Vatican doctrine going political",
        "searches": [
            'Pope encyclical',
            'Vatican encyclical economy OR finance',
            'papal document climate',
            'Vatican statement war OR peace',
            'encyclical politics OR corruption',
        ],
    },
    "ai_moralized": {
        "label": "Economic & tech control tightening — AI, digital ID, CBDC, payment mandates",
        "searches": [
            'Vatican artificial intelligence ethics',
            'AI companies Vatican meeting',
            'Vatican crypto OR bitcoin',
            'Pope CBDC OR digital currency',
            'Church digital ID statement',
            'Vatican robotics ethics',
        ],
    },
    "legislating_morality": {
        "label": "Legislating worship/morality (blasphemy, religious observance)",
        "searches": [
            'blasphemy law',
            'religious observance mandate',
            'morality legislation religious',
        ],
    },
    "ecumenism": {
        "label": "Ecumenism / denominations folding back into Rome",
        "searches": [
            'ecumenism Christian unity Rome',
            'interfaith declaration Vatican',
            'Anglican OR Lutheran full communion Catholic',
            'Orthodox Catholic unity',
            'evangelicalism decline',
            'Protestant denomination collapse',
            'evangelical Catholic conversion',
        ],
    },
    "alien_agenda": {
        "label": "Alien / UFO disclosure agenda (the strong delusion)",
        "searches": [
            'UFO disclosure congress OR Pentagon',
            'UAP disclosure government',
            'pastors briefed extraterrestrial',
        ],
    },
    "culture_shaping": {
        "label": "Culture being shaped toward faith/Rome (conversions, media, revivals)",
        "searches": [
            'celebrity conversion Catholicism',
            'musician OR rapper faith God',
            'movie OR show Catholic theme',
            'influencer suddenly religious',
            'NASA God OR Jesus',
            'Eucharistic miracle',
            'Marian apparition',
            'Muslim conversion Christianity',
            'Iran house church revival',
            'Jewish believers Jesus',
        ],
    },
    "political_realignment": {
        "label": "Political left/right realigning around religion & morality",
        "searches": [
            'left religion morality shift',
            'conservatives away from Zionism',
            'right toward Catholicism',
            'left right common ground social issues',
            'secularism decline religion',
        ],
    },
    "sabbath_sunday": {
        "label": "Sabbath / Sunday-law legislation",
        "searches": [
            'Sunday rest law legislation',
            'Sunday closing law',
            'European Sunday Alliance',
            'anti-Sabbath OR Sabbath observance',
            'day of rest mandate',
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

#!/usr/bin/env python3
"""classify_gnews.py — bucket Google News RSS wrapper URLs by decode type.

READ-ONLY. No network. No writes.
Usage: python3 classify_gnews.py /path/to/news.db

Buckets each news.google.com/rss/articles/ URL:
  offline  — inner string is a plain URL (CBMi), decodes for free
  opaque   — inner string starts AU_yqL, needs a batchexecute network call
  malformed — failed to parse at all (a wrapper shape we don't handle yet)

The frame-strip logic here is the front half of the B2 offline CBMi decoder.
"""
import sys
import sqlite3
import base64
from urllib.parse import urlparse


def inner_string(url):
    # path segment right after /articles/ , drop any ?query and trailing slash
    path = urlparse(url).path
    seg = path.split("/articles/", 1)[1]
    seg = seg.split("/", 1)[0]
    # url-safe base64, pad to a multiple of 4
    raw = base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4))
    # strip the protobuf frame
    if raw[:3] == b"\x08\x13\x22":
        raw = raw[3:]
    if raw[-3:] == b"\xd2\x01\x00":
        raw = raw[:-3]
    # skip the length prefix bytes; don't trust the value (a 3-byte length
    # would trip a strict varint parse, and we only need the body's front)
    start = 2 if raw[0] >= 0x80 else 1
    body = raw[start:]
    # "replace" not "strict": we intentionally over-read the tail, so a body
    # that's valid at the front but ragged at the end must not throw.
    return body.decode("utf-8", "replace")


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 classify_gnews.py /path/to/news.db")
    db = sys.argv[1]
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = con.execute(
        "SELECT url FROM items WHERE url LIKE '%news.google.com/rss/articles/%'"
    ).fetchall()
    con.close()

    offline = opaque = malformed = 0
    for (url,) in rows:
        try:
            s = inner_string(url)
        except Exception:
            malformed += 1
            continue
        if s.startswith("AU_yqL"):
            opaque += 1
        else:
            offline += 1

    print(f"offline (CBMi, free):      {offline}")
    print(f"opaque  (AU_yqL, network): {opaque}")
    print(f"malformed:                 {malformed}")


if __name__ == "__main__":
    main()

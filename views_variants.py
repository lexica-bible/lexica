#!/usr/bin/env python3
"""ABP textual-variant footnotes (the dagger apparatus).

Serves the ABP's own variant readings — e.g. "Complutensian reads 'reprove'" at
Isaiah 2:4 — so the reader can show a small dagger on a verse that opens a panel
listing them. The data is a static file (static/abp_variants.json), book ->
chapter -> verse -> [notes], built from the printed ABP apparatus. No database
and no AI at request time, so it deploys with a plain pull (nothing to load on PA).

Isaiah only for now (the proof book). Other books get added to the JSON later.
"""
import json
import os

from flask import Blueprint, jsonify

from core import log

bp = Blueprint("variants", __name__)

_HERE = os.path.dirname(os.path.abspath(__file__))
_VARIANTS_JSON = os.path.join(_HERE, "static", "abp_variants.json")

# book -> {chapter -> {verse -> [notes]}}, loaded once at startup. Small static
# file; a missing/oversized file just disables the feature (the route returns {}).
_VARIANTS = {}
try:
    with open(_VARIANTS_JSON, encoding="utf-8") as f:
        _VARIANTS = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
except Exception as exc:   # pragma: no cover - missing file just disables the feature
    log.warning("variants: could not load %s: %s", _VARIANTS_JSON, exc)


@bp.route("/api/variants/<book>/<int:chapter>")
def chapter_variants(book, chapter):
    """Variant notes for one chapter, as {verse: [notes]} (empty {} if none).
    The frontend uses the keys to mark verses and the lists to fill the panel."""
    chapters = _VARIANTS.get(book) or {}
    return jsonify(chapters.get(str(chapter), {}))

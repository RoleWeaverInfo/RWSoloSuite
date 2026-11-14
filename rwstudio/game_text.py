"""Normalize typography before the game's legacy string/JSON boundary.

Keep accented names and other languages intact. Only typographic punctuation and
invisible formatting are replaced; JSON keys and gameplay identifiers are not.
"""
import unicodedata

PUNCTUATION = str.maketrans({
    '\u2018': "'", '\u2019': "'", '\u201a': "'", '\u201b': "'",
    '\u201c': '"', '\u201d': '"', '\u201e': '"', '\u201f': '"',
    '\u2010': '-', '\u2011': '-', '\u2012': '-', '\u2013': '-',
    '\u2014': ' - ', '\u2212': '-', '\u2026': '...',
    '\u00a0': ' ', '\u202f': ' ', '\u200b': '', '\ufeff': '',
})


def game_text(value):
    return unicodedata.normalize('NFC', value).translate(PUNCTUATION)


def response_text(value):
    """The bridge owns this boundary, covering NPC, DM, visit and social replies."""
    if isinstance(value, dict):
        return {key: game_text(item) if key in ('reply', 'line_a', 'line_b') and isinstance(item, str)
                else response_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [response_text(item) for item in value]
    return value

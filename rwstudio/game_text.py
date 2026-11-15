"""Normalize typography before the game's legacy string/JSON boundary.

Keep accented names and other languages intact. Only typographic punctuation and
invisible formatting are replaced; JSON keys and gameplay identifiers are not.
"""
import unicodedata
import re

PUNCTUATION = str.maketrans({
    '\u2018': "'", '\u2019': "'", '\u201a': "'", '\u201b': "'",
    '\u201c': '"', '\u201d': '"', '\u201e': '"', '\u201f': '"',
    '\u2010': '-', '\u2011': '-', '\u2012': '-', '\u2013': '-',
    '\u2014': ' - ', '\u2212': '-', '\u2026': '...',
    '\u00a0': ' ', '\u202f': ' ', '\u200b': '', '\ufeff': '',
})


def game_text(value):
    return unicodedata.normalize('NFC', value).translate(PUNCTUATION)


META_SPEECH = re.compile(r"\b(?:the game (?:failed|did not|didn't|cannot|can't|engine)|game (?:engine|inventory|mechanics|system)|(?:in|inside) (?:this|the|a) (?:video )?game|as an? (?:AI|language model)|API key|NWScript|NWNX|inside (?:a|the) (?:video )?game)\b", re.I)
def character_text(value):
    if META_SPEECH.search(value):
        return "I could not confirm that. Let me take another look before I give you an answer."
    return game_text(value)

def response_text(value):
    """The bridge owns this boundary, covering NPC, DM, visit and social replies."""
    if isinstance(value, dict):
        return {key: (character_text(item) if key != 'task_question' else game_text(item)) if key in ('reply', 'line_a', 'line_b', 'task_question') and isinstance(item, str)
                else response_text(item) for key, item in value.items()}
    if isinstance(value, list):
        return [response_text(item) for item in value]
    return value

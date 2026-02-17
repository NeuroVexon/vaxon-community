"""
Axon Skill: Wort-/Zeichenzähler

Zählt Wörter, Zeichen, Sätze und Absätze in einem Text.
"""

SKILL_NAME = "word_count"
SKILL_DISPLAY_NAME = "Wort- und Zeichenzähler"
SKILL_DESCRIPTION = "Zählt Wörter, Zeichen, Sätze und Absätze in einem Text"
SKILL_VERSION = "1.0.0"
SKILL_AUTHOR = "NeuroVexon"
SKILL_RISK_LEVEL = "low"

SKILL_PARAMETERS = {
    "text": {
        "type": "string",
        "description": "Der zu analysierende Text",
        "required": True,
    }
}


def execute(params: dict) -> dict:
    """Analysiert den Text und gibt Statistiken zurück"""
    import re

    text = params.get("text", "")

    if not text.strip():
        return {
            "words": 0,
            "characters": 0,
            "characters_no_spaces": 0,
            "sentences": 0,
            "paragraphs": 0,
            "reading_time_minutes": 0,
        }

    words = len(text.split())
    characters = len(text)
    characters_no_spaces = len(text.replace(" ", "").replace("\n", ""))
    sentences = len(re.split(r"[.!?]+", text.strip())) - 1
    paragraphs = len([p for p in text.split("\n\n") if p.strip()])
    reading_time = round(words / 200, 1)  # ~200 WPM

    return {
        "words": words,
        "characters": characters,
        "characters_no_spaces": characters_no_spaces,
        "sentences": max(sentences, 0),
        "paragraphs": max(paragraphs, 1),
        "reading_time_minutes": reading_time,
    }

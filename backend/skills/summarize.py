"""
Axon Skill: Text-Zusammenfassung

Fasst einen gegebenen Text in wenigen Sätzen zusammen.
Nutzt einfache Heuristik (kein LLM-Aufruf nötig).
"""

SKILL_NAME = "summarize"
SKILL_DISPLAY_NAME = "Text zusammenfassen"
SKILL_DESCRIPTION = "Fasst einen langen Text in wenigen Sätzen zusammen (extraktiv)"
SKILL_VERSION = "1.0.0"
SKILL_AUTHOR = "NeuroVexon"
SKILL_RISK_LEVEL = "low"

SKILL_PARAMETERS = {
    "text": {
        "type": "string",
        "description": "Der zu zusammenfassende Text",
        "required": True,
    },
    "max_sentences": {
        "type": "integer",
        "description": "Maximale Anzahl Sätze",
        "default": 3,
    },
}


def execute(params: dict) -> str:
    """Extraktive Zusammenfassung — wählt die wichtigsten Sätze aus"""
    text = params.get("text", "")
    max_sentences = params.get("max_sentences", 3)

    if not text.strip():
        return "Kein Text zum Zusammenfassen."

    # Sätze extrahieren
    import re

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    if len(sentences) <= max_sentences:
        return text.strip()

    # Einfache Heuristik: Sätze nach Länge und Position gewichten
    scored = []
    for i, sentence in enumerate(sentences):
        score = 0
        # Erste und letzte Sätze sind oft wichtiger
        if i == 0:
            score += 3
        elif i == len(sentences) - 1:
            score += 2
        # Längere Sätze enthalten oft mehr Info
        score += min(len(sentence.split()) / 10, 2)
        scored.append((score, i, sentence))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = sorted(scored[:max_sentences], key=lambda x: x[1])

    return " ".join(s[2] for s in top)

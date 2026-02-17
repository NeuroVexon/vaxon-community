"""
Axon Skill: JSON Formatter

Formatiert und validiert JSON-Strings.
Kann auch JSON ↔ YAML konvertieren.
"""

SKILL_NAME = "json_formatter"
SKILL_DISPLAY_NAME = "JSON Formatter"
SKILL_DESCRIPTION = "Formatiert, validiert und analysiert JSON-Daten"
SKILL_VERSION = "1.0.0"
SKILL_AUTHOR = "NeuroVexon"
SKILL_RISK_LEVEL = "low"

SKILL_PARAMETERS = {
    "json_string": {
        "type": "string",
        "description": "JSON-String zum Formatieren",
        "required": True,
    },
    "indent": {"type": "integer", "description": "Einrückung (Spaces)", "default": 2},
    "sort_keys": {
        "type": "boolean",
        "description": "Keys alphabetisch sortieren",
        "default": False,
    },
}


def execute(params: dict) -> dict:
    """JSON formatieren und analysieren"""
    import json

    json_string = params.get("json_string", "")
    indent = params.get("indent", 2)
    sort_keys = params.get("sort_keys", False)

    if not json_string.strip():
        return {"error": "Kein JSON eingegeben", "valid": False}

    try:
        parsed = json.loads(json_string)
    except json.JSONDecodeError as e:
        return {
            "error": f"Ungültiges JSON: {str(e)}",
            "valid": False,
            "position": e.pos,
        }

    formatted = json.dumps(
        parsed, indent=indent, sort_keys=sort_keys, ensure_ascii=False
    )

    # Analyse
    def count_elements(obj, depth=0):
        if isinstance(obj, dict):
            return sum(count_elements(v, depth + 1) for v in obj.values()) + len(obj)
        elif isinstance(obj, list):
            return sum(count_elements(v, depth + 1) for v in obj) + len(obj)
        return 1

    return {
        "valid": True,
        "formatted": formatted,
        "type": type(parsed).__name__,
        "elements": count_elements(parsed),
        "size_bytes": len(formatted.encode("utf-8")),
    }

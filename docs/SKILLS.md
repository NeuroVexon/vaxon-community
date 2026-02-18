# Skills System

Axon supports extensible skills — community plugins that add new capabilities.

## Security Gate

Every skill goes through a **security process** before it can be executed:

1. **Scan**: The skills directory is searched for `.py` files
2. **Validation**: Structure is verified (required attributes, execute function)
3. **Registration**: Skill is stored in the database (not active)
4. **Approval**: User must explicitly approve the skill in the UI
5. **Hash Check**: On every execution, the SHA-256 hash of the file is verified
6. **Auto-Revocation**: If the file is modified, the approval is automatically revoked

## Creating a Skill

Create a `.py` file in `backend/skills/`:

```python
"""
My Custom Skill
"""

# Required attributes
SKILL_NAME = "my_skill"              # Unique name (snake_case)
SKILL_DISPLAY_NAME = "My Skill"      # Display name
SKILL_DESCRIPTION = "Description"    # What does the skill do?
SKILL_VERSION = "1.0.0"              # SemVer

# Optional attributes
SKILL_AUTHOR = "Your Name"
SKILL_RISK_LEVEL = "low"             # low, medium, high, critical

SKILL_PARAMETERS = {
    "input": {"type": "string", "description": "Input", "required": True},
    "option": {"type": "integer", "description": "Option", "default": 5}
}


def execute(params: dict) -> str:
    """Main function — called by the agent"""
    input_text = params.get("input", "")
    option = params.get("option", 5)

    # Your logic here
    result = f"Processed: {input_text}"

    return result
```

### Required Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `SKILL_NAME` | str | Unique technical name |
| `SKILL_DESCRIPTION` | str | Description of the functionality |
| `SKILL_VERSION` | str | Version number (SemVer) |
| `execute(params)` | function | Main function (sync or async) |

### Optional Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `SKILL_DISPLAY_NAME` | str | = SKILL_NAME | Display name in the UI |
| `SKILL_AUTHOR` | str | None | Author of the skill |
| `SKILL_RISK_LEVEL` | str | "medium" | Risk level |
| `SKILL_PARAMETERS` | dict | {} | Parameter definitions |

## Included Skills

### summarize
- **Description**: Extractively summarizes a text in a few sentences
- **Risk**: Low
- **Parameters**: `text` (string), `max_sentences` (int, default: 3)

### word_count
- **Description**: Counts words, characters, sentences, and paragraphs
- **Risk**: Low
- **Parameters**: `text` (string)

### json_formatter
- **Description**: Formats, validates, and analyzes JSON data
- **Risk**: Low
- **Parameters**: `json_string` (string), `indent` (int), `sort_keys` (bool)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/skills` | List all skills (incl. auto-scan) |
| GET | `/api/v1/skills/{id}` | Get a single skill |
| POST | `/api/v1/skills/{id}/approve` | Approve/revoke a skill |
| POST | `/api/v1/skills/{id}/toggle` | Enable/disable a skill |
| DELETE | `/api/v1/skills/{id}` | Remove skill from database |
| POST | `/api/v1/skills/scan` | Manual directory scan |

## Security Notes

- Skills are **not** executed in a sandbox — they have full access to the Python process
- **Always** review the source code of a skill before approving it
- The hash system protects against **unnoticed changes**, not against malicious code
- Only use skills from unknown sources if you understand the code
- A Docker sandbox for skills is planned for a future version

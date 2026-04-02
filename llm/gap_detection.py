"""
Gap detection — runs before generation.
Uses Haiku to flag missing or thin fields.
Returns a list of gap dicts: {field, severity, message}
"""
import json
import anthropic
import config

_CLIENT = None


def _client() -> anthropic.Anthropic:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _CLIENT


SYSTEM = """You are a handoff quality reviewer. Given a partially filled handoff form, identify fields that are missing or too thin to be useful.

Return ONLY a JSON array. Each item: {"field": "<field name>", "severity": "error"|"warning", "message": "<short actionable message>"}

Rules:
- "error": critically missing (recipient cannot do their job without it)
- "warning": present but thin, vague, or likely important
- Only flag genuine gaps — don't flag optional fields that are intentionally empty
- Return [] if the form looks complete
"""


def detect_gaps(handoff_type: str, form_data: dict) -> list[dict]:
    """
    handoff_type: "sales_to_cs" or "tam_to_tam"
    form_data: dict of field_name -> value (strings, lists, dicts)
    Returns list of {field, severity, message}
    """
    prompt = f"""Handoff type: {handoff_type}

Form data:
{json.dumps(form_data, indent=2)}

Identify any critical gaps or thin fields."""

    response = _client().messages.create(
        model=config.HAIKU_MODEL,
        max_tokens=512,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        return json.loads(response.content[0].text)
    except Exception:
        return []

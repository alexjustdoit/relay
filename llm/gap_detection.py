"""
Gap detection — runs before generation.
Uses gpt-5.4-nano to flag missing or thin fields.
Returns a list of gap dicts: {field, severity, message}
"""
import json
import openai
import config

_CLIENT = None


def _client() -> openai.OpenAI:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = openai.OpenAI(api_key=config.OPENAI_API_KEY)
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

    response = _client().chat.completions.create(
        model=config.NANO_MODEL,
        max_tokens=512,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM + "\nWrap your array in {\"gaps\": [...]}"},
            {"role": "user", "content": prompt},
        ],
    )

    try:
        data = json.loads(response.choices[0].message.content)
        return data.get("gaps", data) if isinstance(data, dict) else data
    except Exception:
        return []

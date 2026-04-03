"""
Gap detection — runs before generation.
Uses claude-haiku-4-5 (Anthropic) or Ollama (local) to flag missing or thin fields.
Returns a list of gap dicts: {field, severity, message}
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from llm import router

SYSTEM = """You are a handoff quality reviewer. Given a partially filled handoff form, identify fields that are missing or too thin to be useful.

Return ONLY a JSON array. Each item: {"field": "<field name>", "severity": "error"|"warning", "message": "<short actionable message>"}

Rules:
- "error": critically missing (recipient cannot do their job without it)
- "warning": present but thin, vague, or likely important
- Only flag genuine gaps — don't flag optional fields that are intentionally empty
- Return [] if the form looks complete
"""

GAP_MODEL = "claude-haiku-4-5-20251001"


def detect_gaps(handoff_type: str, form_data: dict) -> list[dict]:
    """
    handoff_type: "sales_to_cs" or "tam_to_tam"
    form_data: dict of field_name -> value (strings, lists, dicts)
    Returns list of {field, severity, message}
    """
    prompt = f"""Handoff type: {handoff_type}

Form data:
{json.dumps(form_data, indent=2)}

Identify any critical gaps or thin fields. Return a JSON array only."""

    if router.is_local():
        # Ollama fallback via OpenAI-compatible client
        client = router.get_client()
        response = client.chat.completions.create(
            model=router.gap_model(),
            max_tokens=512,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )
        text = response.choices[0].message.content
    else:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=GAP_MODEL,
            max_tokens=512,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text

    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        return data.get("gaps", [])
    except Exception:
        return []

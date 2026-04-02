"""
Handoff document generation.
Uses gpt-5.4-mini (API) or Ollama (local). Streams output back to Streamlit.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm import router

_SALES_TO_CS_SYSTEM = """You are writing a professional account handoff document from a Sales rep to a Customer Success Manager.

Your job is to take structured form data and produce a clear, well-written handoff document that the CSM can act on immediately.

Format the output as a document with these sections (use ## for headers):
## Account Overview
## Why They Bought
## Stakeholders
## Commitments & Promises
## Red Flags & Risks
## Key Upcoming Dates
## Suggested Onboarding Approach  ← this is your AI contribution: synthesize everything above and recommend a concrete onboarding plan
## Additional Notes

Write in a professional but direct tone. Be specific — vague sentences like "the customer seems happy" are not useful. If a field was left blank, omit that section rather than saying "not provided".
"""

_TAM_TO_TAM_SYSTEM = """You are writing a professional account handoff document from one Technical Account Manager to another.

Your job is to take structured form data and produce a clear, well-written handoff document the incoming TAM can act on immediately.

Format the output as a document with these sections (use ## for headers):
## Account Overview
## Technical Environment
## Relationship Map
## In-Flight Work
## Product Gaps & Commitments
## Red Flags & Risks
## Key Upcoming Dates
## Suggested First 30 Days  ← this is your AI contribution: synthesize everything above and recommend a concrete plan for the first 30 days
## Additional Notes

Write in a professional but direct tone. Be specific. If a field was left blank, omit that section rather than saying "not provided".
"""


def stream_handoff(handoff_type: str, form_data: dict):
    """
    Generator that yields text chunks as they stream from the active provider.
    handoff_type: "sales_to_cs" or "tam_to_tam"
    """
    system = _SALES_TO_CS_SYSTEM if handoff_type == "sales_to_cs" else _TAM_TO_TAM_SYSTEM

    prompt = f"""Here is the handoff form data:

{json.dumps(form_data, indent=2)}

Write the handoff document now."""

    client = router.get_client()
    model = router.gen_model()

    stream = client.chat.completions.create(
        model=model,
        max_tokens=2048,
        stream=True,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

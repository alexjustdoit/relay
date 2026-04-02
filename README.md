# Relay

AI-powered account handoff document builder for Sales and Customer Success teams.

Fill in a structured form, let Claude flag gaps before you generate, and get a professional narrative handoff document — ready to save directly to Google Drive.

**[Try the live demo →](https://cx-relay.streamlit.app)**

> **Note:** Hosted on Streamlit's free tier — the app sleeps after a period of inactivity. If you see a "This app has gone to sleep" screen, click the wake-up button and allow 30–60 seconds to start.

---

## Why I built this

Account handoffs are one of the highest-stakes moments in the customer lifecycle. A bad Sales→CS handoff means the CSM walks into onboarding blind — wrong stakeholders, undisclosed commitments, no context on why the customer bought. A bad TAM→TAM handoff means months of relationship context, product workarounds, and in-flight work disappears overnight.

The problem isn't that people don't know what to write — it's that there's no structure that captures it all and no prompt to surface what's missing before the document gets handed off.

This is a portfolio project targeting Solutions Architect and pre-sales engineering roles. It demonstrates both domain fluency — the fields and workflow reflect what someone who has actually done TAM and SA work would care about — and practical LLM engineering: structured gap detection, streaming generation, and Google Drive integration via OAuth.

---

## Workflow

**1. Choose handoff type** — Two modes on a single form: Sales→CS (new customer handoff from AE to CSM) or TAM→TAM (account transfer between Technical Account Managers). Selected via prominent type cards before the form appears.

**2. Fill the form** — Structured fields covering everything the recipient needs: account context, stakeholders (repeatable rows with name, title, role, technical savviness, sentiment), commitments, red flags by category, key upcoming dates, and free-form notes. TAM→TAM mode adds technical environment, in-flight work, product gaps, and account health (Red/Yellow/Green).

**3. Check for gaps** — Before generating, run gap detection. The LLM reviews the form and flags missing or thin fields inline — errors for critically missing information, warnings for fields that are present but vague. Gaps appear next to the relevant fields so you know exactly what to fix.

**4. Generate** — One click streams a complete, professional handoff document. The AI synthesizes all form inputs into a narrative and contributes a "Suggested Onboarding Approach" (Sales→CS) or "Suggested First 30 Days" (TAM→TAM) section that the form alone can't produce.

**5. Save or download** — Connect Google Drive via OAuth to save directly as a Google Doc in a "Relay Handoffs" folder (auto-created on first save). Or download as plain text.

---

## Architecture

```
Gap detection  → gpt-5.4-nano    ← structured JSON output, cost-sensitive
Generation     → gpt-5.4-mini    ← narrative writing, mid-tier quality
Google Drive   → OAuth 2.0       ← Drive API + Docs API, no service account
```

Gap detection uses `response_format: json_object` so the output is always parseable — no prompt-level JSON coercion needed. Generation streams token-by-token directly into Streamlit so the output appears in real time.

Google OAuth uses the standard web application flow. Tokens are cached locally (`~/.relay/tokens.json`) so the connection persists across sessions. On Streamlit Community Cloud where the filesystem is ephemeral, the auth lives in session state only — users re-authenticate each session.

---

## Stack

Python · Streamlit · OpenAI gpt-5.4-nano + gpt-5.4-mini · Google Drive API · Google Docs API · google-auth-oauthlib

---

## Setup

Requires Python 3.10+.

```bash
git clone https://github.com/alexjustdoit/relay
cd relay
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # add API keys
streamlit run app/streamlit_app.py
```

**Windows:** replace `source venv/bin/activate` with `venv\Scripts\activate`.

**Environment variables** (in `.env`):

```
OPENAI_API_KEY=             # required
GOOGLE_CLIENT_ID=           # from Google Cloud Console OAuth credentials
GOOGLE_CLIENT_SECRET=       # from Google Cloud Console OAuth credentials
GOOGLE_REDIRECT_URI=http://localhost:8501
```

**Google OAuth setup:**
1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable the Drive API and Docs API
3. Create an OAuth client ID (Web application type)
4. Add `http://localhost:8501` as an authorized redirect URI
5. Copy the client ID and secret into `.env`

**Streamlit Cloud:** fork the repo, set main file to `app/streamlit_app.py`, and add all four variables under Settings → Secrets. Set `GOOGLE_REDIRECT_URI` to your SCC app URL and add it as an authorized redirect URI in Google Cloud Console.

---

## Project Structure

```
relay/
├── app/
│   ├── streamlit_app.py        # entry point, type selection, both forms, output
│   └── components/sidebar.py   # branding + Google Drive connection status
├── llm/
│   ├── gap_detection.py        # gpt-5.4-nano, json_object mode, inline hints
│   └── generation.py           # gpt-5.4-mini, streaming
├── gdrive/
│   ├── auth.py                 # OAuth flow, token cache, credential refresh
│   └── drive.py                # folder creation, Doc creation via Docs API
└── config.py                   # reads from st.secrets (SCC) or .env (local)
```

---

## Portfolio Talking Points

**LLM engineering**
- Two-stage LLM pipeline: cheap structured classification (gap detection) followed by quality narrative generation — different models sized to the task
- `response_format: json_object` for gap detection guarantees parseable output without prompt-level JSON coercion
- Streaming generation with real-time token rendering in Streamlit — output appears as it's written, not after a multi-second wait
- Config layer reads from `st.secrets` (Streamlit Cloud) or `.env` (local) transparently — no environment-specific code paths in the application

**Product and domain depth**
- Field map reflects real handoff practice: commitments split into written, verbal, and functionality promises; red flags categorized by type (technical, relationship, commercial, adoption); stakeholders include technical savviness as a freeform field, not a dropdown
- Gap detection runs before generation — surfaces what's missing while there's still time to fix it, rather than generating a thin document silently
- Two modes (Sales→CS and TAM→TAM) with distinct field sets sharing a common structure — type-switching prompts a confirmation dialog if the form has been filled
- AI "wow moment" is scoped specifically: the Suggested Onboarding Approach / First 30 Days section synthesizes inputs the form can't capture on its own

**Engineering decisions**
- Google Drive integration via full OAuth (not a service account) — the user's own Drive, not a shared app credential
- Token persistence with graceful degradation: file cache locally, session state only on ephemeral cloud filesystems
- `gdrive/` module named to avoid shadowing the `google` namespace package from google-auth

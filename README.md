# Relay

AI-powered account handoff document builder for Sales and Customer Success teams.

Fill in a structured form, let the AI flag gaps before you generate, and get a professional narrative handoff document — ready to save directly to Google Drive.

**[Try the live demo →](https://cx-relay.streamlit.app)**

> **Note:** Hosted on Streamlit's free tier — the app sleeps after a period of inactivity. If you see a "This app has gone to sleep" screen, click the wake-up button and allow 30–60 seconds to start.

---

## Why I built this

Account handoffs are one of the highest-stakes moments in the customer lifecycle. A bad Sales→CS handoff means the CSM walks into onboarding blind — wrong stakeholders, undisclosed commitments, no context on why the customer bought. A bad TAM→TAM handoff means months of relationship context, product workarounds, and in-flight work disappears overnight.

The problem isn't that people don't know what to write — it's that there's no structure that captures it all and no prompt to surface what's missing before the document gets handed off.

This is a portfolio project targeting Solutions Architect, TAM, and pre-sales engineering roles. It demonstrates domain fluency — the fields and workflow reflect what someone who has actually done TAM and SA work would care about — and practical LLM engineering: multi-provider routing, structured gap detection, streaming generation, and Google Drive integration via OAuth.

---

## Workflow

**1. Choose handoff type** — Two modes: Sales→CS (new customer from AE to CSM) or TAM→TAM (account transfer between Technical Account Managers). Selected via type cards on the home page or builder.

**2. Fill the form** — Structured fields covering everything the recipient needs: account context, stakeholders (repeatable rows with name, title, role, technical savviness, sentiment), commitments, red flags by category, key upcoming dates, and free-form notes. TAM→TAM mode adds technical environment, in-flight work, product gaps, and account health (Red/Yellow/Green).

**3. Load demo data (optional)** — Four pre-built scenarios (two per handoff type) populate the form instantly so you can see a realistic example without manual entry.

**4. Check for gaps** — Before generating, run gap detection. The AI reviews the form and flags missing or thin fields inline — errors for critically missing information, warnings for vague fields. Gaps appear next to the relevant fields so you know exactly what to fix.

**5. Generate** — One click streams a complete, professional handoff document. The AI synthesizes all inputs into a narrative and contributes a "Suggested Onboarding Approach" (Sales→CS) or "Suggested First 30 Days" (TAM→TAM) section that the form alone can't produce.

**6. Save or export** — Connect Google Drive via OAuth to save directly as a Google Doc in a "Relay Handoffs" folder (auto-created). Copy to clipboard, or download as plain text.

**Draft autosave** — The form saves automatically as you type. If you close the tab mid-fill, your work is restored when you return (localStorage on SCC, local file when self-hosted).

**History** — Generated handoffs are saved to a History page (last 50, with per-entry delete and clear all).

---

## Architecture

```
Gap detection  → gpt-5.4-nano        ← structured JSON output, always OpenAI
Generation     → gpt-5.4-mini        ← default (testing / development)
               → claude-sonnet-4-6   ← high-quality mode (toggle in Technical Info)
Google Drive   → OAuth 2.0           ← Drive API + Docs API, no service account
Local LLM      → Ollama              ← optional, zero API cost, dev/offline use
```

Gap detection uses `response_format: json_object` so the output is always parseable. Generation streams token-by-token into Streamlit so output appears in real time.

The generation provider is switchable at runtime via a toggle in the Technical Info developer page: `gpt-5.4-mini` for fast/cheap testing, `claude-sonnet-4-6` for highest-quality demo output. Gap detection stays on `gpt-5.4-nano` regardless.

Google OAuth uses the standard web application flow. Tokens are cached locally (`~/.relay/tokens.json`) across sessions. On Streamlit Community Cloud where the filesystem is ephemeral, auth lives in session state — users re-authenticate each session.

Persistence uses a three-layer strategy: session state (always) → browser localStorage (survives refresh on SCC) → `~/.relay/*.json` (local only, silent fail on SCC).

---

## Stack

Python · Streamlit · OpenAI API (gpt-5.4-nano, gpt-5.4-mini) · Anthropic API (claude-sonnet-4-6) · Ollama (optional local) · Google Drive API · Google Docs API

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
OPENAI_API_KEY=             # required — gap detection + default generation
ANTHROPIC_API_KEY=          # required for high-quality generation (claude-sonnet-4-6)
GOOGLE_CLIENT_ID=           # from Google Cloud Console OAuth credentials
GOOGLE_CLIENT_SECRET=       # from Google Cloud Console OAuth credentials
GOOGLE_REDIRECT_URI=http://localhost:8501
USE_LOCAL_LLM=false         # set true to use Ollama instead of OpenAI
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

**Google OAuth setup:**
1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable the Drive API and Docs API
3. Create an OAuth client ID (Web application type)
4. Add `http://localhost:8501` as an authorized redirect URI
5. Copy the client ID and secret into `.env`

**Streamlit Cloud:** fork the repo, set main file to `app/streamlit_app.py`, and add all variables under Settings → Secrets. Set `GOOGLE_REDIRECT_URI` to your SCC app URL and add it as an authorized redirect URI in Google Cloud Console. Also set `SCC_MODE=true` to disable the Ollama toggle on the hosted demo.

---

## Project Structure

```
relay/
├── app/
│   ├── streamlit_app.py            # entry point, home page, navigation
│   ├── components/
│   │   └── sidebar.py              # branding, LLM toggle, Google Drive status
│   └── pages/
│       ├── 1_Builder.py            # form, gap detection, generation, output
│       ├── 2_History.py            # saved handoff history
│       └── 3_Technical_Info.py     # developer reference, model quality toggle
├── llm/
│   ├── router.py                   # provider routing (OpenAI / Anthropic / Ollama)
│   ├── gap_detection.py            # gpt-5.4-nano, structured JSON output
│   └── generation.py               # gpt-5.4-mini (default) or claude-sonnet-4-6 (HQ)
├── gdrive/
│   ├── auth.py                     # OAuth 2.0 web flow, token cache
│   └── drive.py                    # folder + Doc creation via Docs API
├── data/
│   ├── store.py                    # draft + history persistence (session / localStorage / file)
│   └── demos.py                    # 4 demo scenarios (2 Sales→CS, 2 TAM→TAM)
├── config.py                       # reads from st.secrets (SCC) or .env (local)
└── .github/workflows/keep_alive.yml  # pings SCC every 6 hours to prevent sleep
```

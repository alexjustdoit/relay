# Changelog

All notable changes to Relay are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2026-04-02

Initial public release.

### Added

**Core workflow**
- Two handoff types: Sales→CS and TAM→TAM, selected via type cards on home page or builder
- Structured form covering account context, stakeholders (repeatable rows), commitments, red flags, key dates, and free-form notes
- TAM→TAM-specific fields: technical environment, in-flight work, product gaps, account health (Red/Yellow/Green)
- Four pre-built demo scenarios (two per handoff type) for instant realistic examples

**AI features**
- Gap detection via `gpt-5.4-nano` — structured JSON output flags missing or thin fields inline before generation
- Streaming narrative generation via `gpt-5.4-mini` (default) or `claude-sonnet-4-6` (high-quality mode)
- AI-contributed section: "Suggested Onboarding Approach" (Sales→CS) or "Suggested First 30 Days" (TAM→TAM)
- Generation quality toggle on Technical Info page — stays on mini for testing, switch to Sonnet for demos

**Persistence**
- Draft autosave — form saves as you type; restored on return (localStorage on SCC, file when self-hosted)
- Three-layer persistence stack: session state → browser localStorage → `~/.relay/*.json`
- History page — last 50 generated handoffs, per-entry delete, and clear all
- Confirmation dialogs before destructive actions (Start Over, Change Type)

**Export**
- Google Drive OAuth 2.0 — saves handoffs directly as Google Docs in a "Relay Handoffs" folder (auto-created)
- Copy to clipboard (one-click, no browser permission prompt)
- Download as plain text

**Infrastructure**
- Multi-provider routing: OpenAI (gap detection + default generation), Anthropic (high-quality generation), Ollama (optional local/offline)
- `SCC_MODE` flag disables Ollama toggle on hosted demo
- GitHub Actions workflow pings Streamlit Community Cloud every 6 hours to prevent sleep

---

## Backlog (planned)

- Google Drive history persistence — sync `relay_history.json` to Drive for cross-device access
- Permanent model upgrade — switch default generation to `claude-sonnet-4-6` once evaluation is complete; remove toggle
- Generation quality eval — side-by-side comparison of `claude-sonnet-4-6`, `gpt-5.4-mini`, and `gpt-5.4-nano` for handoff narrative quality

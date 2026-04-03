# Changelog

All notable changes to Relay are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.0] — 2026-04-02

### Added
- **PDF export** — download any handoff as a formatted PDF (Builder output + History page); uses `fpdf2`, no system dependencies
- **Gap check prompt** — if a user clicks Generate without running a gap check first, a dialog asks whether to check first or generate anyway; tracks `gap_checked` state per session and clears it on Start Over, Change Type, and new handoff starts
- **History per-entry downloads** — each History entry now has Download .txt, Download PDF, and Delete buttons inline

### Fixed
- **Gap detection `BadRequestError`** — GPT-5.x dropped `max_tokens` support; removed the parameter for the API path (Ollama still receives it); reverted gap model back to `gpt-5.4-nano`
- **Browser blank mid-generation** — replaced manual chunk accumulation (`output_placeholder.markdown(full_text)`) with `st.write_stream`, which sends only deltas and prevents WebSocket overload
- **Ghost empty element below output** — caused by `components.html` iframe from the clipboard button; removed clipboard button
- **Download .txt broken on SCC** — special characters (`→`, `—`) in filenames broke SCC URL routing; filenames are now sanitized before use in download buttons
- **Gap inline hints not showing** — `render_stakeholder_rows` and `render_red_flags` were never wired to call `_gap_hint`; added calls and switched to partial/substring field name matching (AI returns inconsistent casing and spacing)
- **Collapsed sections with gap hints** — sections now auto-expand when they contain a gap hint
- **Google Drive caption** — updated from "Connect Google Drive to save" to "Sign in with Google to export as a Google Doc" to avoid implying there's no other save option

### Changed
- History timestamps reformatted from raw ISO string to `M/D/YYYY · H:MM AM/PM`
- Removed copy-to-clipboard button from output action bar

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

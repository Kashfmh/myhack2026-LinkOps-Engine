<div align="center">

<br/>

# 🔗 LinkOps Engine

**Automated Startup Ecosystem Matchmaking Dashboard**

*Built for program administrators at accelerators and national innovation funds.*

<br/>

**[View Demo](https://youtu.be/aBJoMC6OOAc)**

<br/>

[![Demo](https://img.shields.io/badge/YouTube-Demo-red?logo=youtube)](https://youtu.be/aBJoMC6OOAc)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-ff4b4b?logo=streamlit)](https://streamlit.io)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?logo=google)](https://ai.google.dev)

</div>

---

## About

LinkOps is a human-in-the-loop AI dashboard that automates the process of matching startup pitch decks to the right mentors and ecosystem partners. An admin uploads PDF or image pitch decks, the AI reads and analyses them using Gemini 2.5 Flash, and surfaces a ranked recommendation for the single best mentor and partner match from a curated database — with a 2-sentence justification for each decision.

The admin then approves, rejects, or interrogates those decisions through an Explainable AI chat before any linkage is committed to the ledger. Nothing gets approved without a human saying so.

Built as a demo for Cradle Fund Malaysia, but the architecture is generic enough to drop into any accelerator, corporate VC, or government innovation program.


---

## Features


### Pitch Deck Processing
- drag-and-drop bulk upload (PDF, PNG, JPG, JPEG)
- up to 5 files per session, 10MB per file
- per-file status badges — **Analysed** / **Pending**
- smart submit button — counts only unprocessed files, disables itself when nothing new is queued
- animated progress bar that fills realistically as each deck is analysed (API runs in a background thread)
- granular error handling — partial failures reported individually, success/error toast notifications for every action

### AI Matchmaking Engine
- reads the actual pitch deck content (multimodal — not just filename)
- matches against a live CSV database of 30 mentors and 18 partners
- returns structured JSON: startup profile + best mentor match + best partner match, each with a 2-sentence justification
- temperature 0.3 for consistent, low-hallucination output

### Human-in-the-Loop Approvals
- each processed startup gets an approval card with its profile, recommended mentor, and recommended partner
- one-click Approve for each linkage — idempotent (can't double-approve)
- dismiss cards once done
- approved linkages flow to the ledger instantly

### Explainable AI (XAI) Chat
- per-startup chat modal — ask the AI *why* it picked a specific mentor or partner
- scoped strictly to matchmaking — refuses off-topic questions with a consistent response
- handles questions about names not in the database (explains they're not in the pool)
- streaming response rendered inside a scrollable container, no layout jumps
- rate limiting: 3s cooldown between messages, 20 message session cap, 500 char input limit
- Malaysian 3R content guardrails at the system instruction level

### Ecosystem Pool Browsers
- Browse Mentor Pool / Browse Partner Pool buttons in the sidebar
- opens a full-screen modal with the entire database in a native sortable, filterable table
- scales to any size — no inline sidebar rendering

### Approved Linkages Ledger
- custom HTML table — Match Reason column wraps text fully, nothing gets cut off
- status badge, hover highlight, full match justification always visible
- one-click CSV export of the full ledger

### Sidebar
- live session metrics (files queued, processed, approved)
- pool browser shortcuts
- CSV export shortcut when linkages exist

---

## Tech Stack

| Layer | Tool |
|---|---|
| UI Framework | [Streamlit](https://streamlit.io) ≥ 1.30 |
| AI Model | [Gemini 2.5 Flash](https://ai.google.dev) via `google-genai` SDK |
| Data | Pandas + CSV (mentor/partner/startup databases) |
| Concurrency | `concurrent.futures.ThreadPoolExecutor` |
| Containerisation | Docker |
| Fonts | Geist (body), Material Symbols Outlined (icons) |

---

## Prerequisites

- Python 3.11+
- A [Google AI Studio](https://aistudio.google.com) API key with Gemini 2.5 Flash access
- pip

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/linkops.git
cd linkops
pip install -r requirements.txt
```

---

## Configuration

Create `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your_api_key_here"
```

> if deploying via Docker or Cloud Run, set `GEMINI_API_KEY` as an environment variable instead — the app reads from `os.environ` first.

---

## Running Locally

```bash
streamlit run app.py
```

opens at `http://localhost:8501`

---

## Docker

```bash
docker build -t linkops .
docker run -p 8080:8080 -e GEMINI_API_KEY=your_key linkops
```

---

## Project Structure

```
linkops/
├── app.py                  # ~70 lines — page config, state init, section calls
├── config.py               # constants (MAX_FILES, model name, XAI limits)
├── requirements.txt
├── Dockerfile
├── core/
│   ├── __init__.py
│   └── matchmaker.py       # execute_match_protocol, query_xai, approve_linkage
├── ui/
│   ├── __init__.py
│   ├── styles.py           # inject_styles(), show_toast()
│   ├── dialogs.py          # all @st.dialog functions (pools, preview, XAI chat)
│   ├── sidebar.py          # render_sidebar()
│   ├── file_manager.py     # render_file_manager() + DummyFile
│   ├── approvals.py        # render_approvals()
│   └── ledger.py           # render_ledger()
├── data/
│   ├── mentors.csv         # mentor database (30 mentors)
│   ├── partners.csv        # partner database (18 partners)
│   └── startups.csv        # sample startups for reference
└── .streamlit/
    ├── config.toml         # theme + toolbar config
    └── secrets.toml        # api key (gitignored)
```

---

## Extending the Databases

The mentor and partner pools are flat CSVs — swap them out or append rows, no code changes needed.

**mentors.csv** columns: `Name`, `Expertise`

**partners.csv** columns: `Name`, `Focus`

The AI reads the full database content at inference time, so new entries are picked up immediately on the next session start.

---

## Limitations

- session state is in-memory — approved linkages reset on page refresh (no database persistence yet)
- file/size limits are defined in `config.py` (`MAX_FILES`, `MAX_FILE_SIZE_MB`)
- XAI chat history is per-session only

---

## License

MIT — do whatever you want with it.

---

*Built at a hackathon. Powered by Gemini.*

# Profile Summarizer Agent ✨

A lightweight agent that turns **messy user profiles** (TXT / PDF / JSON) into a **clean, single-paragraph summary** using **Google Gemini** — with a tiny codebase and **no LangChain**.

| Stage | Tech |
|------:|------|
| Config loading | JSON / YAML / INI / key=value `.txt` (+ `@@` pointers) |
| Ingestion | JSON (dict or list), TXT (key:value or free text), PDF (pypdf) |
| Prompt construction | Deterministic `key: value` lines (sorted keys) |
| LLM call | `google-generativeai` (Gemini) |
| Post-processing | Strips echoed scaffolding (`Summary:` / `User attributes:`) |
| CLI demos | `examples/` scripts |
| Testing | `pytest` (no network; stubs model) |


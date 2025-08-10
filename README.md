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

---

## 1) Folder Structure

profile-summarizer/
├─ src/
│ └─ profile_summarizer_agent.py
├─ examples/
│ ├─ demo_run.py
│ ├─ complex_demo.py
│ └─ profile_from_file_demo.py
├─ configs/
│ ├─ config.json # pointer → "@@config.txt"
│ ├─ config.yaml # pointer → "@@config.txt"
│ ├─ config.txt # real settings (key=value)
│ └─ prompt.txt # your base prompt template
├─ samples/
│ ├─ jian_profile.json
│ ├─ multi_profiles.json
│ ├─ layla_profile.txt
│ └─ layla_profile.pdf
├─ tests/
│ ├─ test_agent_basic.py
│ └─ test_agent_advanced.py
├─ requirements.txt
├─ setup.py
└─ README.md

yaml
Copy
Edit

---

## 2) Quick Start (Windows / Linux)

```bash
git clone <your-repo-url> profile-summarizer
cd profile-summarizer

# Create & activate venv
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
# Windows CMD
# venv\Scripts\activate.bat
# macOS/Linux
# source venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
Create .env in project root:

ini
Copy
Edit
GEMINI_API_KEY=your-gemini-key-here
PowerShell note (if activation blocked):
Run as Admin:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

3) Configuration
You can use JSON, YAML, INI, or simple key=value .txt.
Best practice: keep the real settings in config.txt and make JSON/YAML point to it.

configs/config.json

json
Copy
Edit
"@@config.txt"
configs/config.yaml

yaml
Copy
Edit
"@@config.txt"
configs/config.txt

ini
Copy
Edit
temp=0.1
model_name=models/gemini-1.5-flash-latest
prompt=@@prompt.txt
configs/prompt.txt

sql
Copy
Edit
You are a helpful profile summarization agent.
Summarize the given user attributes into one concise paragraph.
Focus on role, goals, interests, and a personable detail.
Avoid labels and bullet points. Return only the final paragraph.
Path rule: Inline pointers like @@prompt.txt are resolved relative to the file that contains them.
Because config.txt lives in configs/, @@prompt.txt resolves to configs/prompt.txt.
Don’t write @@configs/prompt.txt inside configs/config.txt (that would become configs/configs/...).

Fully JSON (no indirection)
json
Copy
Edit
{
  "temp": 0.1,
  "model_name": "models/gemini-1.5-flash-latest",
  "prompt": "@@configs/prompt.txt"
}
4) Run the Pipeline
Stages:

Load Config → JSON/YAML/INI/TXT with optional @@ pointer(s).

Ingest Profiles → queue dicts or read JSON/TXT/PDF from disk.

Normalize → lower-case keys (optional), trim strings, canonicalize lists.

Build Prompt Body → sorted key: value lines, stable ordering.

Call Gemini → google-generativeai with your model_name + temp.

Post-process → strip any echoed Summary: / User attributes: headers.

Return → one clean paragraph (also cached via final_result()).

Commands
Demo	Command	Notes
Minimal	python examples/demo_run.py --config yaml	Or --config json
Complex (multi-record)	python examples/complex_demo.py --config yaml	Add --model "models/gemini-1.5-flash-latest" to override
From JSON file	python examples/profile_from_file_demo.py --file samples/multi_profiles.json --config json	Accepts dict or list
From TXT (key:value or free text)	python examples/profile_from_file_demo.py --file samples/layla_profile.txt --config yaml	Free text becomes raw_text
From PDF	python examples/profile_from_file_demo.py --file samples/layla_profile.pdf --config yaml	Needs pypdf

What you should see

sql
Copy
Edit
=== SUMMARY FROM FILE ===

Layla is a 28-year-old senior front-end engineer in Dubai who...
5) Python API
python
Copy
Edit
from profile_summarizer_agent import ProfileSummarizerAgent

# Create from any config file (json/yaml/ini/txt)
agent = ProfileSummarizerAgent.from_config_file("configs/config.yaml")

# Queue a dict
agent.append_input({
  "first_name": "Layla",
  "age": 28,
  "role": "Senior Front-End Engineer",
  "location": "Dubai, UAE",
  "hobbies": ["kickboxing", "food blogging"]
})

# Or load from a JSON file (dict or list[dict])
agent.append_input_from_json("samples/multi_profiles.json")

# Generate
summary = agent.process()
print(summary)           # one clean paragraph
print(agent.final_result())  # last result cached
6) Testing
All tests avoid network calls (they stub the model).

bash
Copy
Edit
pytest
tests/test_agent_basic.py → core flows (queueing, JSON ingestion, deterministic body, config indirection, scaffold stripping)

tests/test_agent_advanced.py → deep coverage (inline includes resolved relative to config; loop detection; kv parsing & inference; JSON shape errors; robust stripping for mixed case/spacing; queue behavior; env errors)

7) Listing Available Gemini Models (optional)
bash
Copy
Edit
python - <<'PY'
import os, google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
print("\n".join(m.name for m in genai.list_models()))
PY
Use any shown model ID (e.g., models/gemini-1.5-flash-latest) in configs/config.txt, or pass --model on the CLI.

8) Troubleshooting
Issue	Fix
GEMINI_API_KEY missing in .env or shell	Create .env with GEMINI_API_KEY=... in the repo root.
FileNotFoundError ... configs/configs/prompt.txt	Inside configs/config.txt, write prompt=@@prompt.txt (relative to itself), not @@configs/prompt.txt.
PowerShell blocks venv activation	Run PowerShell as Admin, then Set-ExecutionPolicy RemoteSigned -Scope CurrentUser.
Model not found or quota errors	Check model ID via the snippet above and your API quota at Google AI Studio.
PDF text is empty	Some PDFs are image-based; use OCR first or supply TXT/JSON.

9) Roadmap
🔤 Auto language detection; summarize in the user’s language

🧵 Streaming output (token-by-token)

🐳 Dockerfile for reproducible runs

⚙️ CLI packaging (console_scripts)

✅ GitHub Actions workflow for tests & lint

10) License
MIT — see LICENSE.

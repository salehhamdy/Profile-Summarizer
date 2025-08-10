Profile Summarizer Agent
Turn messy user profiles (TXT / PDF / JSON) into clean, single-paragraph summaries using Google Gemini — no LangChain required.

✅ Config via YAML, JSON, INI, or simple key=value config.txt

✅ Config indirection (config.json/config.yaml → @@config.txt)

✅ Inline file pointers: any config value may be @@path/to/file.txt

✅ Inputs: JSON (dict or list), TXT (key:value or free text), PDF

✅ Deterministic prompt building + robust post-processing (strips “Summary:” scaffolding)

✅ Comprehensive tests (no network calls)

Table of Contents
Features

Requirements

Installation

Configuration

Usage

Examples

Python API

Project Structure

Testing

Troubleshooting

Contributing

License

Features
Direct Gemini API using google-generativeai (no LangChain).

Flexible configs: JSON/YAML/INI/key=value with @@ pointers.

Inline includes: put long prompts in prompt.txt and reference it from config with @@prompt.txt.

File ingestion: read structured/unstructured profiles (TXT), PDFs (via pypdf), or JSON objects/lists.

Deterministic prompt body: stable key: value ordering.

Safe post-processing: removes echoed headers like User attributes: and Summary: in any case/spacing.

Requirements
Python 3.10+ (tested on 3.13)

A Gemini API key in .env (GEMINI_API_KEY=...)

Packages from requirements.txt:

google-generativeai, python-dotenv, pyyaml (optional), pypdf (for PDFs), pytest

Installation
bash
Copy
Edit
# 1) Create & activate a virtual environment
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
# Windows CMD
# venv\Scripts\activate.bat
# macOS/Linux
# source venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Editable install so imports work everywhere
pip install -e .
Create .env in the project root:

ini
Copy
Edit
GEMINI_API_KEY=your-gemini-key-here
Configuration
You can drive the agent with JSON, YAML, INI, or key=value .txt. Easiest is to keep real settings in config.txt and have config.json / config.yaml point at it.

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

pgsql
Copy
Edit
You are a helpful profile summarization agent.
Summarize the following attributes into one concise paragraph, focusing on role, goals,
interests, and a friendly icebreaker question. Avoid repeating labels. No bullet points.
Note on paths: Inline pointers like @@prompt.txt are resolved relative to the file that contains them.
Because config.txt sits in configs/, @@prompt.txt resolves to configs/prompt.txt.
Do not write @@configs/prompt.txt inside configs/config.txt — that would double the folder.

Fully JSON (no indirection)
json
Copy
Edit
{
  "temp": 0.1,
  "model_name": "models/gemini-1.5-flash-latest",
  "prompt": "@@configs/prompt.txt"
}
Usage
Quick demos
bash
Copy
Edit
# YAML config
python examples/demo_run.py --config yaml

# JSON config (indirection to config.txt)
python examples/demo_run.py --config json

# Override model at runtime
python examples/demo_run.py --config json --model "models/gemini-1.5-flash-latest"
Profiles from files (TXT / PDF / JSON)
bash
Copy
Edit
# JSON: single dict or list of dicts
python examples/profile_from_file_demo.py --file samples/jian_profile.json --config json

# Many profiles in one JSON array
python examples/profile_from_file_demo.py --file samples/multi_profiles.json --config json

# TXT with key:value lines or free text
python examples/profile_from_file_demo.py --file samples/layla_profile.txt --config yaml

# PDF (requires pypdf)
python examples/profile_from_file_demo.py --file samples/layla_profile.pdf --config yaml
Rich, multi-record example
bash
Copy
Edit
python examples/complex_demo.py --config yaml
python examples/complex_demo.py --config json --model "models/gemini-1.5-flash-latest"
Python API
python
Copy
Edit
from profile_summarizer_agent import ProfileSummarizerAgent

# From a config file (json/yaml/ini/txt supported)
agent = ProfileSummarizerAgent.from_config_file("configs/config.yaml")

# Queue one record (dict)
agent.append_input({
    "first_name": "Layla",
    "age": 28,
    "role": "Senior Front-End Engineer",
    "location": "Dubai, UAE",
    "hobbies": ["kickboxing", "food blogging"],
})

# Or load JSON file (dict or list of dicts)
agent.append_input_from_json("samples/multi_profiles.json")

# Generate
summary = agent.process()
print(summary)           # one clean paragraph
print(agent.final_result())  # last result cached
Key methods

from_config_file(path) → instantiate using the loader (supports pointers and inline files)

append_input(dict) → queue one profile record

append_input_from_json(path) → file can be dict or list[dict]

process() → builds prompt, calls Gemini, strips scaffolding, returns text

final_result() → last summary returned

Project Structure
arduino
Copy
Edit
profile-summarizer/
├─ src/
│  └─ profile_summarizer_agent.py
├─ examples/
│  ├─ demo_run.py
│  ├─ complex_demo.py
│  └─ profile_from_file_demo.py
├─ configs/
│  ├─ config.json        # "pointer" → "@@config.txt"
│  ├─ config.yaml        # "pointer" → "@@config.txt"
│  ├─ config.txt         # real settings (key=value)
│  └─ prompt.txt         # base prompt
├─ samples/
│  ├─ jian_profile.json
│  ├─ multi_profiles.json
│  ├─ layla_profile.txt
│  └─ layla_profile.pdf
├─ tests/
│  ├─ test_agent_basic.py
│  └─ test_agent_advanced.py
├─ requirements.txt
├─ setup.py
└─ README.md
Testing
All tests avoid network calls by stubbing the model invocation.

bash
Copy
Edit
pytest
tests/test_agent_basic.py: core flows (queueing, JSON ingestion, prompt body, config indirection, scaffold stripping)

tests/test_agent_advanced.py: deep cases (inline file resolution relative to config, loop detection, key=value inference, JSON shape errors, robust stripping across casing/spacing, queue behavior, env errors)

Troubleshooting
GEMINI_API_KEY missing in .env or shell
Create .env in the repo root:

ini
Copy
Edit
GEMINI_API_KEY=your-gemini-key-here
Config pointer resolves to configs/configs/...
Inline @@ is resolved relative to the file that contains it.
Inside configs/config.txt, use prompt=@@prompt.txt (not @@configs/prompt.txt).

PowerShell blocks venv activation
Start PowerShell as Admin and run:

powershell
Copy
Edit
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
List available Gemini models

bash
Copy
Edit
python - <<'PY'
import os, google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
print("\n".join(m.name for m in genai.list_models()))
PY

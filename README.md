Profile Summarizer Agent
A lightweight, dependency-minimal agent that turns messy user profiles (TXT/PDF/JSON) into clean, single-paragraph summaries using Google Gemini — no LangChain needed.

Configurable via YAML, JSON, INI, or simple key=value config.txt.

Supports config indirection: config.yaml / config.json can point to @@config.txt.

Inline file pointers: any config value can be @@path/to/file.txt (resolved relative to the config file).

Ingests JSON (dict or list of dicts), TXT (key:value or free text), and PDF.

Features
Direct Gemini API via google-generativeai (no LangChain).

Robust config loader with:

JSON / YAML / INI / key=value parsing

@@file root pointers and inline pointers (resolved per-file)

Type inference for key=value (true/false, numbers)

Flexible inputs:

append_input() for dicts

append_input_from_json() for JSON files (object or array)

Example script reads TXT/PDF and converts to attributes

Deterministic prompt body (sorted keys)

Post-processing that strips echoed scaffolding (Summary: headers, etc.)

Comprehensive unit tests (basic + advanced) with zero network calls

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
│  ├─ config.yaml        # "pointer": "@@config.txt"
│  ├─ config.json        # "pointer": "@@config.txt"
│  ├─ config.txt         # actual settings (key=value)
│  └─ prompt.txt         # your base prompt template
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
Requirements
Python 3.10+ (tested on 3.13)

pip install -r requirements.txt

google-generativeai, python-dotenv, pyyaml (optional), pypdf (for PDF), tqdm, pydantic

A Gemini API key set as GEMINI_API_KEY (loaded from .env)

Setup
1) Create & activate a venv
PowerShell (Windows):

powershell
Copy
Edit
python -m venv venv
.\venv\Scripts\Activate.ps1
CMD (Windows):

cmd
Copy
Edit
python -m venv venv
venv\Scripts\activate.bat
macOS/Linux:

bash
Copy
Edit
python -m venv venv
source venv/bin/activate
2) Install dependencies & package (editable)
bash
Copy
Edit
pip install -r requirements.txt
pip install -e .
3) Add your Gemini key
Create .env in project root:

ini
Copy
Edit
GEMINI_API_KEY=your-gemini-key-here
The code automatically loads .env using python-dotenv.

Configuration
You can provide config via YAML, JSON, INI, or key=value .txt.

Recommended layout (use indirection)
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
Summarize the following attributes into one concise paragraph...
(Your custom instructions here)
Important: Inline pointers @@prompt.txt are resolved relative to the file that contains them. Because config.txt is in configs/, @@prompt.txt means configs/prompt.txt. You do not need configs/prompt.txt there.

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
A) Minimal demo
bash
Copy
Edit
python examples/demo_run.py --config yaml
# or
python examples/demo_run.py --config json
B) Complex demo (multiple records, override model if you want)
bash
Copy
Edit
python examples/complex_demo.py --config yaml
python examples/complex_demo.py --config json --model "models/gemini-1.5-flash-latest"
C) File-based demo (JSON/TXT/PDF)
bash
Copy
Edit
# JSON: single dict or list of dicts
python examples/profile_from_file_demo.py --file samples/jian_profile.json --config json

# Many profiles in one JSON array
python examples/profile_from_file_demo.py --file samples/multi_profiles.json --config json

# TXT key:value OR free-form text
python examples/profile_from_file_demo.py --file samples/layla_profile.txt --config yaml

# PDF (requires pypdf)
python examples/profile_from_file_demo.py --file samples/layla_profile.pdf --config yaml
You can override the model at runtime with --model "models/gemini-1.5-flash-latest".

Programmatic Example
python
Copy
Edit
from profile_summarizer_agent import ProfileSummarizerAgent

agent = ProfileSummarizerAgent.from_config_file("configs/config.yaml")
agent.append_input({
    "first_name": "Layla",
    "age": 28,
    "role": "Senior Front-End Engineer",
    "location": "Dubai, UAE",
    "hobbies": ["kickboxing", "food blogging"],
})
print(agent.process())           # returns a single-paragraph summary
print(agent.final_result())      # last summary cached
Load from JSON file
python
Copy
Edit
agent = ProfileSummarizerAgent.from_config_file("configs/config.json")
agent.append_input_from_json("samples/multi_profiles.json")  # dict or list[dict]
print(agent.process())
API: Class & Functions
ProfileSummarizerAgent.from_config_file(path)
Classmethod that loads a dict config from path using load_config and instantiates the agent.

__init__(temp: float, model_name: str, prompt: str)
temp: generation temperature

model_name: Gemini model ID (e.g., models/gemini-1.5-flash-latest)

prompt: base prompt template (string; can be file-inlined)

Initializes the Gemini client using GEMINI_API_KEY.

append_input(user_profile: Dict[str, Any])
Queues a single profile record (dict). Multiple calls will batch into one model invocation when process() is called.

append_input_from_json(path, *, lower_keys=True, strip_strings=True)
Reads a JSON file that is either:

A single dict → appended as one record

A list of dicts → each item appended

Also normalizes keys and trims strings (toggleable).

process() -> str
Renders queued records into deterministic key: value lines.

Calls the model once with the composed prompt.

Strips echoed “User attributes:”/“Summary:” scaffolding.

Clears the input queue and stores the last result.

Returns the summary text.

final_result() -> str | None
Returns the last generated summary.

Private helpers
_build_prompt_body(): deterministic lines by sorted keys; joins lists with commas.

_postprocess_summary(text): robustly removes any echoed scaffolding.

_normalize_record(...): optional lowercasing & trimming.

_call_model(attribute_block): calls Gemini and returns raw text (no stripping).

load_config(path): supports JSON/YAML/INI/TXT with @@ pointers, inline file expansion relative to the config file, and key/value inference.

Input Formats
JSON
Single object:

json
Copy
Edit
{
  "first_name": "Jian",
  "age": 33,
  "role": "Software Engineer",
  "hobbies": ["Go", "vintage cameras"]
}
List of objects:

json
Copy
Edit
[
  {"first_name": "Layla", "age": 28},
  {"first_name": "Kai", "age": 34}
]
TXT (key:value)
vbnet
Copy
Edit
first_name: Layla
age: 28
role: Senior Front-End Engineer
hobbies: kickboxing, food blogging
TXT (free text)
sql
Copy
Edit
Layla Al-Hashimi is a 28-year-old senior front-end engineer in Dubai...
(Example script treats it as raw_text.)

PDF
Extracted via pypdf.PdfReader in the example script.

Running Tests
bash
Copy
Edit
pytest
tests/test_agent_basic.py: happy-path unit tests for core features.

tests/test_agent_advanced.py: deeper coverage: config indirection, inline expansion (relative), JSON shape errors, post-processing robustness, queue behavior, env errors, etc.

Tests stub _call_model to avoid network calls. A dummy GEMINI_API_KEY is set for instantiation.

Troubleshooting
GEMINI_API_KEY missing in .env or shell

Add it to .env at the project root.

FileNotFoundError ... configs/configs/prompt.txt

Inline pointers are resolved relative to the file that contains them.
If you’re in configs/config.txt, write prompt=@@prompt.txt (not @@configs/prompt.txt).

Windows PowerShell blocks venv activation

Run PowerShell as Admin:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Then .\venv\Scripts\Activate.ps1.

Notes
This project uses direct Gemini API (no LangChain).

Model IDs evolve; you can list available models:

bash
Copy
Edit
python - <<'PY'
import os, google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
print("\n".join(m.name for m in genai.list_models()))
PY
Swap models by editing configs/config.txt or passing --model on the CLI.

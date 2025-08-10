import argparse
import re
from pathlib import Path

from profile_summarizer_agent import ProfileSummarizerAgent

# Config shortcuts
CFG_DIR = Path("configs")
SHORTCUT = {"yaml": CFG_DIR / "config.yaml", "json": CFG_DIR / "config.json"}

# CLI
parser = argparse.ArgumentParser()
parser.add_argument("--file", required=True, help="Profile TXT / PDF / JSON")
parser.add_argument("--config", default="yaml",
                    help="'yaml', 'json', or path to any config file")
parser.add_argument("--model",
                    help="Override model_name at runtime (e.g., flash vs pro)")
args = parser.parse_args()

cfg_path = SHORTCUT.get(args.config.lower(), Path(args.config)).expanduser()
agent = ProfileSummarizerAgent.from_config_file(cfg_path)
if args.model:
    agent.model_name = args.model

# Load JSON / PDF / TXT
file_path = Path(args.file)
suffix = file_path.suffix.lower()

if suffix == ".json":
    agent.append_input_from_json(file_path)   # dict or list[dict]
    print("\n=== SUMMARY FROM FILE ===\n")
    print(agent.process())
    raise SystemExit(0)

if suffix == ".pdf":
    from pypdf import PdfReader
    reader = PdfReader(str(file_path))
    raw_text = "\n".join(page.extract_text() or "" for page in reader.pages)
else:
    raw_text = file_path.read_text("utf-8")

# Parse key:value, or fallback to raw prose
profile = {}
for line in raw_text.splitlines():
    m = re.match(r"\s*([^:]+?)\s*:\s*(.+)", line)
    if m:
        k, v = m.groups()
        v = [x.strip() for x in v.split(",")] if "," in v else v.strip()
        profile[k.strip().lower()] = v

if not profile:
    profile = {"raw_text": raw_text.strip()[:4_000]}  # safety cap

agent.append_input(profile)

print("\n=== SUMMARY FROM FILE ===\n")
print(agent.process())
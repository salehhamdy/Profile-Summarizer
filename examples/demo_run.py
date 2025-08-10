import argparse
from pathlib import Path
from profile_summarizer_agent import ProfileSummarizerAgent

# ---------- default config shortcuts ----------------------------------
CFG_DIR  = Path("configs")
SHORTCUT = {"yaml": CFG_DIR / "config.yaml",
            "json": CFG_DIR / "config.json"}

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="yaml",
                    help="'yaml', 'json', or path to a config file")
parser.add_argument("--model",
                    help="Override model_name from the chosen config")
args = parser.parse_args()

cfg_path = SHORTCUT.get(args.config.lower(), Path(args.config)).expanduser()
agent    = ProfileSummarizerAgent.from_config_file(cfg_path)

if args.model:
    agent.model_name = args.model            # on-the-fly override

# --- demo data ---------------------------------------------------------
agent.append_input({"first_name": "Layla", "gender": "female",    "age": 28})
agent.append_input({"first_name": "Kai",   "gender": "nonbinary", "age": 34})

print("\n=== PROFILE SUMMARY ===")
print(agent.process())

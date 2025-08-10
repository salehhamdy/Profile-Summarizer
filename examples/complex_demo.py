import argparse
from pathlib import Path
from profile_summarizer_agent import ProfileSummarizerAgent

# ─── default shortcut map ---------------------------------------------
CFG_DIR   = Path("configs")
SHORTCUTS = {
    "yaml": CFG_DIR / "config.yaml",
    "json": CFG_DIR / "config.json",
}

# ─── CLI ---------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument(
    "--config",
    default="yaml",
    help="'yaml', 'json', or a full path to any config file",
)
parser.add_argument(
    "--model",
    help="Override model_name from the chosen config (e.g. flash vs pro)",
)
args = parser.parse_args()

cfg_path = SHORTCUTS.get(args.config.lower(), Path(args.config)).expanduser()
agent    = ProfileSummarizerAgent.from_config_file(cfg_path)

if args.model:
    agent.model_name = args.model  # quick override without editing file

# ─── Layla ─────────────────────────────────────────────────────────────
agent.append_input({
    "first_name": "Layla",
    "gender": "female",
    "age": 28,
    "location": "Dubai, UAE",
    "role": "Sr. Front-End Engineer",
    "company": "FinTechX",
    "years_in_role": 3,
    "preferred_language": "Arabic",
    "hobbies": ["kickboxing", "food blogging"],
    "goals": "lead a cross-functional UI guild",
})

# ─── Kai ───────────────────────────────────────────────────────────────
agent.append_input({
    "first_name": "Kai",
    "gender": "nonbinary",
    "age": 34,
    "pronouns": "they/them",
    "location": "Berlin, Germany",
    "role": "Product Manager",
    "industry": "ClimateTech",
    "hobbies": ["bouldering", "analog photography"],
    "goals": "scale carbon-offset API to EU market",
})

# ─── María ─────────────────────────────────────────────────────────────
agent.append_input({
    "first_name": "María",
    "gender": "female",
    "age": 41,
    "location": "Mexico City",
    "role": "Head of Marketing",
    "company": "EduSoft LATAM",
    "years_at_company": 7,
    "languages": ["Spanish", "English"],
    "hobbies": ["road cycling", "salsa dancing"],
    "recent_win": "closed $1 M partnership with UNAM",
})

print("\n=== ENHANCED SUMMARIES ===\n")
print(agent.process())

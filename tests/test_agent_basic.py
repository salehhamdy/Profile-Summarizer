import os
import json
from pathlib import Path

import pytest

from profile_summarizer_agent import ProfileSummarizerAgent, load_config


def _make_agent():
    """
    Build an agent safely for tests.

    - Sets a dummy GEMINI_API_KEY so __init__ doesn't raise.
    - We stub _call_model in tests to avoid any real API calls.
    """
    os.environ.setdefault("GEMINI_API_KEY", "test-key")
    return ProfileSummarizerAgent(
        temp=0.0,
        model_name="models/gemini-1.5-flash-latest",
        prompt="Summarise attributes. Return ONLY the final paragraph.",
    )


def test_queue_and_process_with_mock():
    agent = _make_agent()
    agent.append_input({"first_name": "Layla", "age": 28})
    agent.append_input({"first_name": "Kai", "age": 34})

    # Stub the model call so no network is used
    agent._call_model = lambda block: "[MOCKED SUMMARY]"  # type: ignore[attr-defined]

    out = agent.process()
    assert out == "[MOCKED SUMMARY]"
    assert agent.final_result() == "[MOCKED SUMMARY]"
    # inputs cleared after successful process
    assert agent.inputs == []


def test_append_input_from_json_single(tmp_path: Path):
    agent = _make_agent()

    # Mixed-case keys and extra whitespace to verify normalization
    content = {
        "First_Name": "  Layla  ",
        "Role": " Senior Front-End Engineer ",
        "hobbies": [" kickboxing ", " food blogging  "],
    }
    p = tmp_path / "single.json"
    p.write_text(json.dumps(content), encoding="utf-8")

    agent.append_input_from_json(p)  # default lower_keys=True, strip_strings=True

    assert len(agent.inputs) == 1
    rec = agent.inputs[0]
    # Keys lowercased
    assert set(rec.keys()) == {"first_name", "role", "hobbies"}
    # Strings stripped
    assert rec["first_name"] == "Layla"
    assert rec["role"] == "Senior Front-End Engineer"
    # List items stripped
    assert rec["hobbies"] == ["kickboxing", "food blogging"]


def test_append_input_from_json_list(tmp_path: Path):
    agent = _make_agent()

    data = [
        {"first_name": "Layla", "age": 28},
        {"first_name": "Kai", "age": 34},
    ]
    p = tmp_path / "multi.json"
    p.write_text(json.dumps(data), encoding="utf-8")

    agent.append_input_from_json(p)

    assert len(agent.inputs) == 2
    assert agent.inputs[0]["first_name"] == "Layla"
    assert agent.inputs[1]["first_name"] == "Kai"


def test_build_prompt_body_deterministic_and_list_join():
    agent = _make_agent()
    agent.append_input(
        {
            "b_key": "second",
            "a_key": "first",
            "hobbies": ["cycling", "cooking"],
        }
    )
    body = agent._build_prompt_body()  # internal but deterministic
    # Keys should be sorted alphabetically: a_key, b_key, hobbies
    lines = [line for line in body.splitlines() if line.strip()]
    assert lines[0] == "a_key: first"
    assert lines[1] == "b_key: second"
    assert lines[2] == "hobbies: cycling, cooking"


def test_load_config_indirection_and_inline(tmp_path: Path):
    """
    Verify:
      • root-level pointer in JSON ("@@config.txt") is followed
      • key=value parsing works
      • inline '@@<file>' value is expanded with the file's contents
      • numeric types are inferred
    """
    cfg_dir = tmp_path / "configs"
    cfg_dir.mkdir()

    # Prompt file (inline expansion)
    prompt_file = cfg_dir / "prompt.txt"
    prompt_file.write_text("You are a test prompt.", encoding="utf-8")

    # Authoritative config.txt using absolute path for inline pointer
    config_txt = cfg_dir / "config.txt"
    config_txt.write_text(
        "\n".join(
            [
                "temp=0.2",
                "model_name=models/gemini-1.5-flash-latest",
                f"prompt=@@{prompt_file.as_posix()}",
            ]
        ),
        encoding="utf-8",
    )

    # JSON pointer that delegates to config.txt (relative to its own folder)
    config_json = cfg_dir / "config.json"
    config_json.write_text('"@@config.txt"', encoding="utf-8")

    cfg = load_config(config_json)

    assert isinstance(cfg, dict)
    assert pytest.approx(cfg["temp"], rel=1e-9) == 0.2
    assert cfg["model_name"] == "models/gemini-1.5-flash-latest"
    assert cfg["prompt"] == "You are a test prompt."


def test_process_returns_only_summary_text():
    """
    Ensure scaffold stripping works even when _call_model is mocked.
    Requires process() to post-process the raw text.
    """
    agent = _make_agent()
    agent.append_input({"first_name": "Jian", "age": 33})

    # Return text that includes the scaffold; process() should strip it.
    def fake_call(_block: str) -> str:
        return "User attributes:\n...\n\nSummary:\nClean summary only."

    agent._call_model = fake_call  # type: ignore[attr-defined]

    out = agent.process()
    assert out == "Clean summary only."

import os
import json
from pathlib import Path

import pytest

from profile_summarizer_agent import ProfileSummarizerAgent, load_config


# ---------- helpers ----------------------------------------------------

def _make_agent():
    """Create an agent that won't hit the network (we stub calls in tests)."""
    os.environ.setdefault("GEMINI_API_KEY", "test-key")
    return ProfileSummarizerAgent(
        temp=0.0,
        model_name="models/gemini-1.5-flash-latest",
        prompt="Summarise attributes. Return ONLY the final paragraph.",
    )


# ---------- CONFIG LOADER ADVANCED TESTS -------------------------------

def test_kv_txt_parsing_and_inference(tmp_path: Path):
    """Pure key=value parsing + type inference; no inline file access."""
    cfg = tmp_path / "config.txt"
    cfg.write_text(
        "\n".join(
            [
                "# comment",
                "temp=0.25",
                "flag=true",
                "count=42",
                "pi=3.14",
                "model_name=models/gemini-1.5-flash-latest",
                "prompt=Just a literal value",  # no @@ inline here
            ]
        ),
        encoding="utf-8",
    )
    result = load_config(cfg)
    assert result["temp"] == 0.25
    assert result["flag"] is True
    assert result["count"] == 42
    assert result["pi"] == 3.14
    assert result["model_name"].endswith("flash-latest")
    assert result["prompt"] == "Just a literal value"


def test_inline_prompt_expansion_absolute_path(tmp_path: Path):
    # Create a real prompt file
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("INLINE PROMPT CONTENT", encoding="utf-8")

    # Create a kv config that inlines that prompt via ABS path
    cfg = tmp_path / "config.txt"
    cfg.write_text(
        "\n".join(
            [
                "temp=0.1",
                "model_name=models/gemini-1.5-flash-latest",
                f"prompt=@@{prompt_file.as_posix()}",
            ]
        ),
        encoding="utf-8",
    )
    result = load_config(cfg)
    assert result["prompt"] == "INLINE PROMPT CONTENT"


def test_root_pointer_json_relative(tmp_path: Path):
    """
    JSON points to config.txt; config.txt uses a RELATIVE inline '@@prompt.txt'.
    The loader should resolve relative to config.txt's folder.
    """
    cfg_dir = tmp_path / "configs"
    cfg_dir.mkdir()

    # prompt file next to config.txt
    prompt_file = cfg_dir / "prompt.txt"
    prompt_file.write_text("RELATIVE PROMPT CONTENT", encoding="utf-8")

    # Authoritative txt with RELATIVE inline pointer
    cfg_txt = cfg_dir / "config.txt"
    cfg_txt.write_text(
        "temp=0.3\nmodel_name=models/gemini-1.5-flash-latest\nprompt=@@prompt.txt",
        encoding="utf-8",
    )

    # JSON pointer that delegates to txt (relative path)
    cfg_json = cfg_dir / "config.json"
    cfg_json.write_text('"@@config.txt"', encoding="utf-8")

    out = load_config(cfg_json)
    assert out["temp"] == 0.3
    assert out["model_name"].endswith("flash-latest")
    assert out["prompt"] == "RELATIVE PROMPT CONTENT"


def test_indirection_loop_detection(tmp_path: Path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    c = tmp_path / "c.json"
    d = tmp_path / "d.json"
    a.write_text('"@@b.json"', encoding="utf-8")
    b.write_text('"@@c.json"', encoding="utf-8")
    c.write_text('"@@d.json"', encoding="utf-8")
    d.write_text('"@@a.json"', encoding="utf-8")  # loops back

    with pytest.raises(RuntimeError):
        load_config(a)


def test_bad_kv_line_raises(tmp_path: Path):
    cfg = tmp_path / "bad.txt"
    cfg.write_text("no_equals_sign_here", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(cfg)


def test_unsupported_config_extension(tmp_path: Path):
    cfg = tmp_path / "config.xyz"
    cfg.write_text("whatever", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(cfg)


# ---------- AGENT INIT / ENV BEHAVIOR ---------------------------------

def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(EnvironmentError):
        ProfileSummarizerAgent(temp=0.1, model_name="m", prompt="p")


# ---------- JSON INGESTION ADVANCED -----------------------------------

def test_append_input_from_json_bad_top_level(tmp_path: Path):
    agent = _make_agent()
    p = tmp_path / "not_dict_or_list.json"
    p.write_text(json.dumps("hello"), encoding="utf-8")
    with pytest.raises(TypeError):
        agent.append_input_from_json(p)


def test_append_input_from_json_list_with_nondict(tmp_path: Path):
    agent = _make_agent()
    p = tmp_path / "bad_list.json"
    p.write_text(json.dumps([{"ok": 1}, 3, {"ok": 2}]), encoding="utf-8")
    with pytest.raises(TypeError):
        agent.append_input_from_json(p)


def test_append_input_from_json_normalization_toggles(tmp_path: Path):
    agent = _make_agent()
    data = {"First_Name": "  Layla  ", "Hobbies": [" a ", " b  "]}
    p = tmp_path / "norm.json"
    p.write_text(json.dumps(data), encoding="utf-8")

    # keep original keys and whitespace
    agent.append_input_from_json(p, lower_keys=False, strip_strings=False)
    rec = agent.inputs[-1]
    assert "First_Name" in rec and rec["First_Name"] == "  Layla  "
    assert rec["Hobbies"] == [" a ", " b  "]


# ---------- POST-PROCESSING ROBUSTNESS --------------------------------

def test_postprocess_multiple_summary_occurrences():
    agent = _make_agent()
    agent.append_input({"x": 1})

    # Return text with two 'Summary:' occurrences; expect last segment kept
    def fake_call(_block: str):
        return "Header\nSummary: keep?\nNoise\nSUMMARY:\nThis is final."

    agent._call_model = fake_call  # type: ignore[attr-defined]
    out = agent.process()
    assert out == "This is final."


def test_postprocess_case_and_spacing():
    agent = _make_agent()
    agent.append_input({"x": 1})

    def fake_call(_):
        return "something\nsumMary :   Final line here."

    agent._call_model = fake_call  # type: ignore[attr-defined]
    assert agent.process() == "Final line here."


def test_postprocess_fallback_user_attributes():
    agent = _make_agent()
    agent.append_input({"x": 1})

    def fake_call(_):
        return "User Attributes: Preamble only, no summary."

    agent._call_model = fake_call  # type: ignore[attr-defined]
    assert agent.process() == "Preamble only, no summary."


def test_postprocess_no_scaffold_passthrough():
    agent = _make_agent()
    agent.append_input({"x": 1})

    def fake_call(_):
        return "Already clean text."

    agent._call_model = fake_call  # type: ignore[attr-defined]
    assert agent.process() == "Already clean text."


# ---------- INPUT QUEUE & RESULT BEHAVIOR ------------------------------

def test_process_clears_inputs_and_sets_final_result():
    agent = _make_agent()
    agent.append_input({"a": 1})

    agent._call_model = lambda _: "Result 1"  # type: ignore[attr-defined]
    out1 = agent.process()
    assert out1 == "Result 1"
    assert agent.final_result() == "Result 1"
    assert agent.inputs == []

    # Add another record; ensure final_result updates
    agent.append_input({"b": 2})
    agent._call_model = lambda _: "Result 2"  # type: ignore[attr-defined]
    out2 = agent.process()
    assert out2 == "Result 2"
    assert agent.final_result() == "Result 2"


def test_process_without_inputs_raises():
    agent = _make_agent()
    with pytest.raises(ValueError):
        agent.process()


# ---------- PROMPT BODY MULTI-RECORD RENDERING ------------------------

def test_build_prompt_body_multiple_records_separated():
    agent = _make_agent()
    agent.append_input({"a": "one"})
    agent.append_input({"b": "two"})
    body = agent._build_prompt_body()
    # Should contain a blank line between records
    assert "a: one\n\nb: two" in body

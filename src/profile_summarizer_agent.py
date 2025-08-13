from __future__ import annotations

import json, configparser, os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
load_dotenv()

# YAML optional
try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore

import google.generativeai as genai

# ────────────────────────── CONFIG LOADER ─────────────────────────────
def load_config(path: str | Path, _depth: int = 0) -> Dict[str, Any]:
    if _depth > 3:
        raise RuntimeError("Config indirection loop detected")

    path = Path(path).expanduser()
    if not path.exists():
        raise FileNotFoundError(path)

    ext = path.suffix.lower()
    if ext == ".json":
        obj: Any = json.loads(path.read_text("utf-8"))
    elif ext in {".yaml", ".yml"}:
        if yaml is None:
            raise ImportError("pip install pyyaml to parse YAML")
        obj = yaml.safe_load(path.read_text("utf-8"))  # type: ignore
    elif ext == ".ini":
        cp = configparser.ConfigParser()
        cp.read(path, encoding="utf-8")
        sect = cp.defaults() or cp["DEFAULT"]
        obj = {k: _infer(sect[k]) for k in sect}
    elif ext == ".txt":
        obj = _parse_kv_text(path)
    else:
        raise ValueError("Unsupported config format")

    # follow root-level @@ pointer
    if isinstance(obj, str) and obj.startswith("@@"):
        target = (path.parent / obj[2:]).resolve()
        return load_config(target, _depth + 1)

    # expand inline @@ pointers inside dict values
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v.startswith("@@"):
                obj[k] = Path(v[2:]).read_text("utf-8")
        return obj

    raise ValueError("Config must resolve to a dict")


def _parse_kv_text(p: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for line in p.read_text("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, sep, v = line.partition("=")
        if not sep:
            raise ValueError(f"Bad line in {p}: {line!r}")
        out[k.strip()] = _infer(v.strip())
    return out


def _infer(val: str) -> Any:
    lo = val.lower()
    if lo in {"true", "false"}:
        return lo == "true"
    try:
        return float(val) if "." in val else int(val)
    except ValueError:
        return val

# ────────────────────────── MAIN AGENT ────────────────────────────────
class ProfileSummarizerAgent:
    @classmethod
    def from_config_file(cls, path: str | Path) -> "ProfileSummarizerAgent":
        return cls(**load_config(path))

    def __init__(self, temp: float, model_name: str, prompt: str) -> None:
        self.base_prompt = prompt.strip()
        self.temperature = temp
        self.model_name = model_name
        self.inputs: List[Dict[str, Any]] = []
        self._last_summary: str | None = None

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY missing in .env or shell")
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(self.model_name)

    # public API --------------------------------------------------------
    def append_input(self, user_profile: Dict[str, Any]) -> None:
        """Queue a single profile record."""
        self.inputs.append(user_profile)

    def append_input_from_json(
        self,
        path: str | Path,
        *,
        lower_keys: bool = True,
        strip_strings: bool = True,
    ) -> None:
        """
        Read one or many profile records from a JSON file and queue them.

        The JSON file may be:
          • a dict   -> appended as one record
          • a list   -> each dict item appended as a record
        """
        path = Path(path).expanduser()
        data = json.loads(path.read_text("utf-8"))

        if isinstance(data, dict):
            self.inputs.append(self._normalize_record(data, lower_keys, strip_strings))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if not isinstance(item, dict):
                    raise TypeError(
                        f"Item #{i} in {path} is {type(item).__name__}, expected dict"
                    )
                self.inputs.append(self._normalize_record(item, lower_keys, strip_strings))
        else:
            raise TypeError(
                f"Top-level JSON in {path} must be dict or list[dict], got {type(data).__name__}"
            )

    def final_result(self) -> str | None:
        return self._last_summary

    def process(self) -> str:
        """Build prompt from queued inputs, invoke model once, return summary."""
        if not self.inputs:
            raise ValueError("No inputs queued")
        body = self._build_prompt_body()
        raw_text = self._call_model(body)               # may be mocked in tests
        summary = self._postprocess_summary(raw_text)   # <- always strip here
        self.inputs.clear()
        self._last_summary = summary
        return summary

    # helpers -----------------------------------------------------------
    def _normalize_record(
        self,
        rec: Dict[str, Any],
        lower_keys: bool,
        strip_strings: bool,
    ) -> Dict[str, Any]:
        """Normalize keys/values for consistent prompting."""
        out: Dict[str, Any] = {}
        for k, v in rec.items():
            key = k.lower() if lower_keys else k
            if isinstance(v, str) and strip_strings:
                out[key] = v.strip()
            elif isinstance(v, list) and strip_strings:
                out[key] = [x.strip() if isinstance(x, str) else x for x in v]
            else:
                out[key] = v
        return out

    def _build_prompt_body(self) -> str:
        """Render queued dicts into deterministic 'key: value' lines."""
        lines: List[str] = []
        for rec in self.inputs:
            for k in sorted(rec):
                v = rec[k]
                v = ", ".join(v) if isinstance(v, list) else v
                lines.append(f"{k}: {v}")
            lines.append("")
        return "\n".join(lines).strip()

    def _call_model(self, attribute_block: str) -> str:
        """Compose final prompt → call Gemini → return raw text (no stripping)."""
        prompt = (
            f"{self.base_prompt}\n\n"
            f"User attributes:\n{attribute_block}\n\n"
            "Summary:"
        )
        response = self._model.generate_content(
            prompt,
            generation_config={"temperature": self.temperature},
        )
        return response.text.strip()

    def _postprocess_summary(self, text: str) -> str:
        """
        Remove any echoed scaffolding like 'Summary:' or 'User attributes:'.
        Works even if tests mock _call_model and return the scaffold.
        """
        if not isinstance(text, str):
            return text
        t = text.strip()

        # Prefer the LAST 'Summary:' occurrence (case-insensitive)
        low = t.lower()
        needle = "summary:"
        idx = low.rfind(needle)
        if idx != -1:
            return t[idx + len(needle):].strip()

        # Fallback: if 'User attributes:' exists but no 'Summary:', drop that prefix
        import re
        ua = re.compile(r'(?i)\buser\s+attributes\s*:\s*')
        m = ua.search(t)
        if m:
            return t[m.end():].strip()

        return t

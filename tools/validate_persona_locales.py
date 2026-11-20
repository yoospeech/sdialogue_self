# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Codex <https://openai.com>
# SPDX-License-Identifier: MIT
"""Validate 1,000 personas and 36 scenarios in every language locale."""
from pathlib import Path

import yaml


LANGUAGES = (
    "en", "ar", "zh", "fr", "de", "it", "ja", "ko", "pt", "es", "vi", "th", "id", "hi", "ru", "pl",
)
PERSONA_FIELDS = {
    "scenario_id", "speaker", "name", "age", "role", "background", "goal", "mood",
    "communication_style", "experience", "constraint", "circumstances", "rules",
}
ROOT = Path(__file__).resolve().parents[1] / "data" / "locales"


def _read(path):
    if not path.is_file():
        raise ValueError(f"missing {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected YAML mapping in {path}")
    return value


def _same_shape(source, translated, path):
    if isinstance(source, dict):
        if not isinstance(translated, dict) or set(source) != set(translated):
            raise ValueError(f"structure differs at {path}")
        for key in source:
            _same_shape(source[key], translated[key], f"{path}.{key}")
    elif isinstance(source, list):
        if not isinstance(translated, list) or len(source) != len(translated):
            raise ValueError(f"list structure differs at {path}")
        for index, (left, right) in enumerate(zip(source, translated)):
            _same_shape(left, right, f"{path}[{index}]")


def main():
    source_scenarios = _read(ROOT / "ko" / "scenarios.yaml")
    persona_ids = None
    scenario_ids = None
    identity = None
    for language in LANGUAGES:
        directory = ROOT / language
        document = _read(directory / "personas.yaml")
        personas = document.get("personas", {})
        scenarios = _read(directory / "scenarios.yaml")
        marker = {"method": "llm", "source_language": "ko", "version": 1}
        if language != "ko" and document.get("translation") != marker:
            raise ValueError(f"{language}: personas are not marked as per-record LLM translations")
        serialized = yaml.safe_dump(personas, allow_unicode=True)
        if language != "ko" and ("한국어" in serialized or "korean" in serialized.lower()):
            raise ValueError(f"{language}: persona text still contains a Korean-language instruction")
        if len(personas) != 1000:
            raise ValueError(f"{language}: expected 1000 personas, found {len(personas)}")
        if len(scenarios) != 36:
            raise ValueError(f"{language}: expected 36 scenarios, found {len(scenarios)}")
        _same_shape(source_scenarios, scenarios, f"{language}.scenarios")
        if any(set(value) != PERSONA_FIELDS for value in personas.values()):
            raise ValueError(f"{language}: persona fields do not match the required schema")
        if any(value["speaker"] not in {"user", "agent"} for value in personas.values()):
            raise ValueError(f"{language}: invalid persona speaker")
        current_personas = set(personas)
        current_scenarios = set(scenarios)
        persona_ids = current_personas if persona_ids is None else persona_ids
        scenario_ids = current_scenarios if scenario_ids is None else scenario_ids
        if current_personas != persona_ids or current_scenarios != scenario_ids:
            raise ValueError(f"{language}: semantic ID set differs from the other locales")
        if any(value["scenario_id"] not in scenarios for value in personas.values()):
            raise ValueError(f"{language}: persona references an unknown scenario")
        current_identity = {
            key: (value["age"], value["speaker"], value["scenario_id"])
            for key, value in personas.items()
        }
        identity = current_identity if identity is None else identity
        if current_identity != identity:
            raise ValueError(f"{language}: persona identity fields differ from the other locales")
    print("validated 16 languages, 16000 personas, and 576 scenarios")


if __name__ == "__main__":
    main()

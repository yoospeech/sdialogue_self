# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Codex <https://openai.com>
# SPDX-License-Identifier: MIT
"""Materialize 1,000 complete persona records from a finished locale catalog."""
import argparse
from pathlib import Path

import yaml


def _read(path):
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a YAML mapping: {path}")
    return value


def materialize(locale_dir, count=1000):
    """Return a persona document populated from localized scenarios and moods."""
    scenarios = _read(locale_dir / "scenarios.yaml")
    document = _read(locale_dir / "personas.yaml")
    moods = document.get("moods", {})
    if len(scenarios) != 36:
        raise ValueError(f"{locale_dir.name} has {len(scenarios)} scenarios; expected 36")
    if not moods:
        raise ValueError(f"{locale_dir.name} has no localized moods")
    scenario_items = list(scenarios.items())
    mood_items = list(moods.values())
    personas = {}
    for index in range(count):
        scenario_id, scenario = scenario_items[index % len(scenario_items)]
        participant = scenario["participants"][(index // len(scenario_items)) % 2]
        base = participant["persona"]
        mood = mood_items[(index // (len(scenario_items) * 2)) % len(mood_items)]
        persona_id = f"persona_{index + 1:04d}"
        personas[persona_id] = {
            "scenario_id": scenario_id,
            "speaker": participant["speaker"],
            "name": f"{base['name']} {index + 1}",
            "age": 20 + (index * 17) % 56,
            "role": base["role"],
            "background": base["background"],
            "goal": participant["goal"],
            "mood": mood["mood"],
            "communication_style": mood["style"],
            "experience": base["background"],
            "constraint": base["circumstances"],
            "circumstances": base["circumstances"],
            "rules": base["rules"],
        }
    document["personas"] = personas
    return document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("languages", nargs="+")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    for language in args.languages:
        if language != "ko":
            raise ValueError(
                "Only the Korean source may be materialized; translate every target persona with "
                "generate_persona_locales.py"
            )
        path = args.root / "data" / "locales" / language / "personas.yaml"
        document = materialize(path.parent)
        path.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")
        print(f"{language}: {len(document['personas'])} personas")


if __name__ == "__main__":
    main()

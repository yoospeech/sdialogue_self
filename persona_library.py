# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Codex <https://openai.com>
# SPDX-License-Identifier: MIT
"""Load complete language-specific persona and scenario records."""
import copy
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


LANGUAGES = {
    "en": "English", "ar": "Arabic", "zh": "Chinese", "fr": "French",
    "de": "German", "it": "Italian", "ja": "Japanese", "ko": "Korean",
    "pt": "Portuguese", "es": "Spanish", "vi": "Vietnamese", "th": "Thai",
    "id": "Indonesian", "hi": "Hindi", "ru": "Russian", "pl": "Polish",
}
DATA_ROOT = Path(__file__).with_name("data") / "locales"
EXPECTED_PERSONAS = 1000
EXPECTED_SCENARIOS = 36
PERSONA_FIELDS = {
    "scenario_id", "speaker", "name", "age", "role", "background", "goal", "mood",
    "communication_style", "experience", "constraint", "circumstances", "rules",
}


def _language_code(language: str) -> str:
    for code, name in LANGUAGES.items():
        if language.casefold() in (code, name.casefold()):
            return code
    raise ValueError(f"Unknown language {language!r}; choose from {list(LANGUAGES)}")


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing locale data: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Locale data must be a YAML mapping: {path}")
    return value


@lru_cache(maxsize=len(LANGUAGES))
def _locale_data(language: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load a complete locale without cross-language fallback."""
    code = _language_code(language)
    directory = DATA_ROOT / code
    document = _read_yaml(directory / "personas.yaml")
    scenarios = _read_yaml(directory / "scenarios.yaml")
    personas = document.get("personas")
    if not isinstance(personas, dict):
        raise ValueError(f"{code}/personas.yaml has no 'personas' mapping")
    if len(personas) != EXPECTED_PERSONAS:
        raise ValueError(f"{code}: found {len(personas)} personas; expected {EXPECTED_PERSONAS}")
    if len(scenarios) != EXPECTED_SCENARIOS:
        raise ValueError(f"{code}: found {len(scenarios)} scenarios; expected {EXPECTED_SCENARIOS}")
    return personas, scenarios


@dataclass(frozen=True)
class PersonaProfile:
    """A fully localized fictional participant."""
    persona_id: str
    scenario_id: str
    speaker: str
    name: str
    age: int
    role: str
    background: str
    goal: str
    mood: str
    communication_style: str
    experience: str
    constraint: str
    circumstances: str
    rules: str
    language: str

    @classmethod
    def from_dict(cls, persona_id: str, value: Dict[str, Any], language: str) -> "PersonaProfile":
        missing = PERSONA_FIELDS - value.keys()
        if missing:
            raise ValueError(f"{language}/{persona_id} is missing fields: {sorted(missing)}")
        fields = {key: value[key] for key in PERSONA_FIELDS}
        return cls(persona_id=persona_id, language=language, **fields)

    def to_sdialog(self, language: Optional[str] = None) -> Any:
        """Build an SDialog Persona; an override loads the same ID in that locale.

        :param language: Optional language code or English language name.
        :return: A new ``sdialog.personas.Persona`` object.

        Example:
            persona = profile.to_sdialog(language="English")
        """
        from sdialog.personas import Persona

        code = _language_code(language or self.language)
        profile = self if code == self.language else get_persona(self.persona_id, code)
        return Persona(
            name=profile.name, age=profile.age, language=LANGUAGES[code], role=profile.role,
            background=f"{profile.background} {profile.experience}".strip(),
            personality=f"{profile.mood}. {profile.communication_style}".strip(),
            circumstances=f"{profile.circumstances} {profile.constraint}".strip(),
            rules=profile.rules,
        )


@dataclass(frozen=True)
class DialogueSetup:
    """A localized scenario and its randomly selected participant pair."""
    language: str
    scenario: Dict[str, Any]
    user: PersonaProfile
    agent: PersonaProfile


def get_persona(persona_id: str, language: str = "ko") -> PersonaProfile:
    """Load one persona by stable ID from the requested locale."""
    code = _language_code(language)
    personas, _ = _locale_data(code)
    try:
        value = personas[persona_id]
    except KeyError as exc:
        raise KeyError(f"Unknown persona {persona_id!r} for language {code!r}") from exc
    return PersonaProfile.from_dict(persona_id, value, code)


def get_personas(scenario_id: str, speaker: Optional[str] = None,
                 language: str = "ko") -> List[PersonaProfile]:
    """Load all localized personas matching a scenario and speaker slot."""
    if speaker not in (None, "user", "agent"):
        raise ValueError("speaker must be user, agent, or None")
    code = _language_code(language)
    personas, _ = _locale_data(code)
    return [
        PersonaProfile.from_dict(persona_id, value, code)
        for persona_id, value in personas.items()
        if value["scenario_id"] == scenario_id and (speaker is None or value["speaker"] == speaker)
    ]


def get_pair(scenario_id: str, variant: int = 0,
             language: str = "ko") -> Tuple[PersonaProfile, PersonaProfile]:
    """Return a deterministic localized pair for the legacy interface."""
    if variant < 0:
        raise ValueError("variant must be nonnegative")
    users = get_personas(scenario_id, "user", language)
    agents = get_personas(scenario_id, "agent", language)
    if not users or not agents:
        raise ValueError(f"No complete participant pair for {language}/{scenario_id}")
    return users[variant % len(users)], agents[variant % len(agents)]


def get_scenario(scenario_id: str, language: str = "ko") -> Dict[str, Any]:
    """Return an independent scenario from the requested locale."""
    code = _language_code(language)
    _, scenarios = _locale_data(code)
    try:
        result = copy.deepcopy(scenarios[scenario_id])
    except KeyError as exc:
        raise KeyError(f"Unknown scenario {scenario_id!r} for language {code!r}") from exc
    for value in result.get("audio", {}).get("noise", {}).values():
        if isinstance(value, dict) and isinstance(value.get("snr"), list):
            value["snr"] = tuple(value["snr"])
    return result


def get(language: str = "ko", scenario_id: Optional[str] = None,
        seed: Optional[int] = None) -> DialogueSetup:
    """Randomly select a stored scenario and compatible pair, reproducibly by seed."""
    code = _language_code(language)
    _, scenarios = _locale_data(code)
    rng = random.Random(seed)
    selected_id = scenario_id or rng.choice(tuple(scenarios))
    scenario = get_scenario(selected_id, code)
    users = get_personas(selected_id, "user", code)
    agents = get_personas(selected_id, "agent", code)
    if not users or not agents:
        raise ValueError(f"No complete participant pair for {code}/{selected_id}")
    return DialogueSetup(code, scenario, rng.choice(users), rng.choice(agents))


def available_scenario_ids(language: str = "ko") -> Tuple[str, ...]:
    """Return scenario IDs after validating the selected locale."""
    _, scenarios = _locale_data(language)
    return tuple(scenarios)


# Backward-compatible Korean collections.
SCENARIO_IDS = available_scenario_ids("ko")
PERSONAS = tuple(get_persona(persona_id) for persona_id in _locale_data("ko")[0])
PERSONAS_BY_ID = {profile.persona_id: profile for profile in PERSONAS}
PERSONAS_BY_SCENARIO = {
    scenario_id: tuple(profile for profile in PERSONAS if profile.scenario_id == scenario_id)
    for scenario_id in SCENARIO_IDS
}

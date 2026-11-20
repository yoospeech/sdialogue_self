# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Codex <https://openai.com>
# SPDX-License-Identifier: MIT
"""Importable, deterministic library of 1,000 fictional adults across 36 scenarios.

Example:
    from persona_library import PERSONAS, get_personas, get_pair
    customer, partner = get_pair("travel", variant=2)
    # Agent(persona=customer.to_sdialog(), ...)

Import uses only the standard library: no models, GPU, or network are needed.
Profiles are deterministic attribute combinations, not 1,000 LLM-written biographies.
"""
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Language preferences, not a guarantee of LLM/TTS language support.
LANGUAGES = {"en": "English", "ar": "Arabic", "zh": "Chinese", "fr": "French",
             "de": "German", "it": "Italian", "ja": "Japanese", "ko": "Korean",
             "pt": "Portuguese", "es": "Spanish", "vi": "Vietnamese", "th": "Thai",
             "id": "Indonesian", "hi": "Hindi", "ru": "Russian", "pl": "Polish"}


def _language_code(language: str) -> str:
    for code, name in LANGUAGES.items():
        if language.casefold() in (code, name.casefold()):
            return code
    raise ValueError(f"Unknown language {language!r}; choose from {list(LANGUAGES)}")


@dataclass(frozen=True)
class PersonaProfile:
    """A fictional scenario-specific participant, convertible to SDialog Persona.

    :param persona_id: Stable unique identifier.
    :param scenario_id: Scenario catalog key.
    :param speaker: Participant slot (user or agent), not necessarily a customer/support role.

    Example:
        profile = get_personas("weekend")[0]
        persona = profile.to_sdialog()
    """
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
    language: str = "ko"

    def to_sdialog(self, language: Optional[str] = None) -> Any:
        """Build a standard SDialog Persona with the participant's own information.

        :param language: Language code or English name; None uses the profile's language.
        :return: A new sdialog.personas.Persona object.

        Example:
            persona = PERSONAS[0].to_sdialog(language="Korean")
        """
        from sdialog.personas import Persona
        language_code = _language_code(language or self.language)
        language_name = LANGUAGES[language_code]
        if language_code != "ko":
            scenario_name = self.scenario_id.replace("_", " ")
            name = f"{self.scenario_id}-{self.persona_id.rsplit('_', 1)[-1]}"
            role = f"{self.speaker} participant in the {scenario_name} scenario"
            background = f"A fictional adult participating in a {scenario_name} conversation."
            personality = f"Mood: {self.mood}. Communication style: concise and collaborative."
            circumstances = f"{scenario_name} conversation. Constraint: communicate clearly and stay in role."
            rules = (
                f"Speak natural {language_name} in one or two sentences. Stay within the {scenario_name} scenario. "
                "Do not invent private information or unverified facts."
            )
            goal = f"Make practical progress on the shared {scenario_name} objective."
            experience = "This is a fictional scenario-specific participant."
        else:
            name = self.name
            role = self.role
            background = f"{self.background} {self.experience}"
            personality = f"현재 감정: {self.mood}. 말하기 방식: {self.communication_style}"
            circumstances = f"{self.circumstances} 개인 제약: {self.constraint}"
            rules = self.rules.replace("자연스러운 한국어로", f"자연스러운 {language_name}로")
            goal = self.goal
            experience = self.experience
        return Persona(
            name=name, age=self.age, language=language_name, role=role,
            background=background,
            personality=personality,
            circumstances=circumstances,
            rules=(f"{rules} Goal: {goal}. Experience: {experience}. Name: {name}. "
                   f"Speak in {language_name}. The profile descriptions are metadata, not the output language. "
                   f"Express numbers and codes as spoken words in {language_name}."),
        )


_CATALOG_PATH = Path(__file__).with_name("persona_catalog.json")
_CATALOG = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
SCENARIO_IDS = tuple(row["id"] for row in _CATALOG["templates"])
_SCENARIOS = {row["id"]: row for row in _CATALOG["templates"]}
_MOODS = {row["id"]: row for row in _CATALOG["mood_variants"]}
_STYLES = (
    "핵심부터 간결하게 말함",
    "이유를 먼저 설명하고 결론을 말함",
    "예시를 들어 설명함",
    "확인 질문으로 이해를 맞춤",
    "생각할 시간을 가진 뒤 신중하게 말함",
    "상대의 말을 요약하고 답함",
    "자신의 경험을 짧게 덧붙임", "여러 선택지의 장단점을 비교함",
)
_EXPERIENCES = (
    "비슷한 상황은 처음이어서 절차를 확인하고 싶다.",
    "유사한 경험이 한 번 있지만 이번 상황의 차이를 확인하려 한다.",
    "비슷한 경험이 여러 번 있어 필요한 질문을 구체적으로 한다.",
    "과거의 오해를 반복하지 않으려고 합의 내용을 확인한다.",
    "관련 경험은 있지만 상대의 입장은 아직 알지 못한다.",
)
_CONSTRAINTS = (
    "대화할 시간이 짧아 우선순위를 정해야 한다.",
    "결정 전에 충분히 생각할 시간이 필요하다.",
    "여러 단계를 한꺼번에 듣기보다 하나씩 확인하고 싶다.",
    "가능하면 익숙한 방식으로 진행하고 싶다.",
    "기존 계획을 크게 바꾸기는 어렵지만 작은 조정은 가능하다.",
    "새로운 방법도 시도할 의향이 있다.",
    "자신이 맡을 수 있는 범위를 명확히 정하고 싶다.",
)


def _build_profiles() -> Tuple[PersonaProfile, ...]:
    profiles = []
    # Each scenario has 27 or 28 people; both roles receive at least 13 people.
    for scenario_index, scenario in enumerate(_CATALOG["templates"]):
        count = 1000 // len(SCENARIO_IDS) + (scenario_index < 1000 % len(SCENARIO_IDS))
        for index in range(count):
            participant = scenario["participants"][index % 2]
            source = participant["persona"]
            serial = len(profiles)
            variant = index // 2
            mood_id = scenario["suitable_moods"][(variant + index % 2) % len(scenario["suitable_moods"])]
            mood = _MOODS[mood_id]
            # Names are opaque fictional labels; demographics do not determine behavior.
            profiles.append(PersonaProfile(
                persona_id=f"{scenario['id']}_{index + 1:03d}", scenario_id=scenario["id"],
                speaker=participant["speaker"], name=f"가상인물_{serial + 1:04d}",
                age=20 + (serial * 17) % 56, role=source["role"], background=source["background"],
                goal=participant["goal"], mood=mood["mood"],
                communication_style=f"{_STYLES[variant % len(_STYLES)]}. {mood['style']}",
                experience=_EXPERIENCES[(variant + scenario_index) % len(_EXPERIENCES)],
                constraint=_CONSTRAINTS[(variant * 3 + scenario_index) % len(_CONSTRAINTS)],
                circumstances=source["circumstances"], rules=source["rules"],
                language=tuple(LANGUAGES)[(scenario_index + variant) % len(LANGUAGES)],
            ))
    return tuple(profiles)


PERSONAS = _build_profiles()
PERSONAS_BY_ID = {profile.persona_id: profile for profile in PERSONAS}
PERSONAS_BY_SCENARIO = {
    scenario: tuple(profile for profile in PERSONAS if profile.scenario_id == scenario)
    for scenario in SCENARIO_IDS
}


def get_personas(scenario_id: str, speaker: Optional[str] = None,
                 language: Optional[str] = None) -> List[PersonaProfile]:
    """Select profiles by scenario and optional participant slot.

    :param scenario_id: A key from SCENARIO_IDS.
    :param speaker: Optional user or agent slot.
    :param language: Filter by stored language code or English name, or None for all languages.
        Some scenario/language combinations have no stored profiles. Use get_pair(language=...)
        to select participants and override their language for any scenario.
    :return: A new list of matching profiles.

    Example:
        students = get_personas("tutoring", speaker="agent")
    """
    if speaker not in (None, "user", "agent"):
        raise ValueError("speaker must be user, agent, or None")
    code = _language_code(language) if language is not None else None
    return [p for p in PERSONAS_BY_SCENARIO[scenario_id]
            if (speaker is None or p.speaker == speaker) and (code is None or p.language == code)]


def get_pair(scenario_id: str, variant: int = 0,
             language: Optional[str] = None) -> Tuple[PersonaProfile, PersonaProfile]:
    """Select one participant per role, with cyclic variation within the scenario.

    :param scenario_id: Scenario key.
    :param variant: Nonnegative variant index.
    :param language: Override both participants' language without changing stored profiles.
    :return: User-slot and agent-slot profiles.

    Example:
        friend_a, friend_b = get_pair("weekend", variant=3)
    """
    if variant < 0:
        raise ValueError("variant must be nonnegative")
    first, second = get_personas(scenario_id, "user"), get_personas(scenario_id, "agent")
    a, b = first[variant % len(first)], second[variant % len(second)]
    code = _language_code(language) if language is not None else a.language
    return replace(a, language=code), replace(b, language=code)


def get_scenario(scenario_id: str, language: Optional[str] = None) -> Dict[str, Any]:
    """Return an independent copy of context, goals, audio settings and evaluation criteria.

    :param scenario_id: Scenario key.
    :param language: Optional language for human-readable scenario metadata. Korean uses the Korean catalog;
        all other languages use neutral metadata with the selected output language in the instructions.
    :return: A scenario dictionary. Noise SNR ranges are tuples for the Audio API.

    Example:
        options = get_scenario("remote")["audio"]
    """
    import copy
    result = copy.deepcopy(_SCENARIOS[scenario_id])
    if language is not None and _language_code(language) != "ko":
        title = scenario_id.replace("_", " ").title()
        result["title"] = title
        result["relationship"] = "Two fictional participants"
        result["context"] = {
            "location": "a suitable conversation space",
            "environment": "phone call" if result["context"]["environment"] == "전화" else "in person",
            "circumstances": title,
        }
        result["scenario"]["goal"] = f"Make practical progress on the {title.lower()} scenario."
        result["scenario"]["facts_policy"] = "Use only facts established in the conversation."
        result["evaluation_criteria"] = [
            "Both participants maintain their roles and knowledge boundaries",
            "The conversation makes practical progress toward a shared objective",
            "Responses are relevant, concise, and natural in the selected language",
            "There is no hidden reasoning, special token, or mechanical repetition",
        ]
    for value in result["audio"].get("noise", {}).values():
        if isinstance(value, dict) and isinstance(value.get("snr"), list):
            value["snr"] = tuple(value["snr"])
    return result


if __name__ == "__main__":
    print(f"{len(PERSONAS)} personas / {len(SCENARIO_IDS)} scenarios")
    for scenario_id in SCENARIO_IDS:
        print(f"{scenario_id:16} {len(PERSONAS_BY_SCENARIO[scenario_id]):2}  {_SCENARIOS[scenario_id]['title']}")

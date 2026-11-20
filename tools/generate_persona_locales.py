# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Codex <https://openai.com>
# SPDX-License-Identifier: MIT
"""Translate every persona and scenario record with a local Hugging Face LLM."""
import argparse
import copy
import json
import re
from pathlib import Path

import yaml


LANGUAGES = {
    "en": "English", "ar": "Arabic", "zh": "Chinese", "fr": "French", "de": "German",
    "it": "Italian", "ja": "Japanese", "ko": "Korean", "pt": "Portuguese", "es": "Spanish",
    "vi": "Vietnamese", "th": "Thai", "id": "Indonesian", "hi": "Hindi", "ru": "Russian",
    "pl": "Polish",
}
TRANSLATED_FIELDS = {
    "title", "relationship", "location", "environment", "circumstances", "facts_policy", "goal",
    "name", "role", "background", "personality", "rules", "mood", "style", "evaluation_criteria",
    "communication_style", "experience", "constraint",
}
TRANSLATION_VERSION = 1


def _extract_json(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("model response contains no JSON object")
    return json.loads(text[start:end + 1])


def _same_structure(source, translated, path="root"):
    if isinstance(source, dict):
        if set(source) != set(translated):
            raise ValueError(f"key mismatch at {path}")
        for key in source:
            _same_structure(source[key], translated[key], f"{path}.{key}")
    elif isinstance(source, list):
        if not isinstance(translated, list) or len(source) != len(translated):
            raise ValueError(f"list mismatch at {path}")
        for index, (a, b) in enumerate(zip(source, translated)):
            _same_structure(a, b, f"{path}[{index}]")


def _translate(pipe, source, language, max_new_tokens=4096):
    translated = copy.deepcopy(source)
    slots = []

    def collect(value, parent_key=None):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in TRANSLATED_FIELDS and isinstance(item, str):
                    slots.append((value, key, item))
                elif key in TRANSLATED_FIELDS and isinstance(item, list):
                    for index, text in enumerate(item):
                        if isinstance(text, str):
                            slots.append((item, index, text))
                else:
                    collect(item, key)
        elif isinstance(value, list):
            for item in value:
                collect(item, parent_key)

    collect(translated)
    source_strings = {f"t{index}": text for index, (_, _, text) in enumerate(slots)}
    prompt = (
        "/no_think\n"
        f"Translate every value in this JSON object into natural {language}. Return exactly one JSON object. "
        "Preserve every t-number key and return every key exactly once. Do not add commentary. "
        f"Replace every instruction to speak Korean with an instruction to speak {language}; "
        f"the translated values must not contain the word Korean or the text 한국어. "
        "Preserve negation, quantities, time spans, and factual meaning exactly. "
        "Use concise native phrasing suitable for an LLM system prompt.\nJSON:\n"
        + json.dumps(source_strings, ensure_ascii=False)
    )
    messages = [{"role": "user", "content": prompt}]
    output = pipe(messages, max_new_tokens=max_new_tokens, do_sample=False)[0]["generated_text"]
    if isinstance(output, list):
        output = output[-1]["content"]
    translated_strings = _extract_json(output)
    if set(translated_strings) != set(source_strings):
        raise ValueError("translated string key mismatch")
    for key, value in translated_strings.items():
        if isinstance(value, str):
            value = value.replace("한국어", language)
            value = re.sub(r"\bKorean\b", language, value, flags=re.I)
            translated_strings[key] = value
    for index, (container, key, _) in enumerate(slots):
        container[key] = translated_strings[f"t{index}"]
    _same_structure(source, translated)
    return translated


def _write_yaml(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")
    temporary.replace(path)


def _translate_batch(pipe, batch, language, max_new_tokens):
    """Translate a batch, splitting it when a model response is incomplete."""
    try:
        return _translate(pipe, batch, language, max_new_tokens=max_new_tokens)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        if len(batch) <= 1:
            raise
        items = list(batch.items())
        middle = len(items) // 2
        left = _translate_batch(pipe, dict(items[:middle]), language, max_new_tokens)
        right = _translate_batch(pipe, dict(items[middle:]), language, max_new_tokens)
        return {**left, **right}


def _translate_personas(pipe, source, path, code, batch_size, max_personas, max_new_tokens):
    existing = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    marker = existing.get("translation", {}) if isinstance(existing, dict) else {}
    if marker != {"method": "llm", "source_language": "ko", "version": TRANSLATION_VERSION}:
        existing = {}
    document = {
        "language": {"code": code, "name": LANGUAGES[code]},
        "translation": {"method": "llm", "source_language": "ko", "version": TRANSLATION_VERSION},
        "personas": dict(existing.get("personas", {})),
    }
    memory = {}
    for persona_id, translated in document["personas"].items():
        original = source.get(persona_id, {})
        for field in TRANSLATED_FIELDS:
            if isinstance(original.get(field), str) and isinstance(translated.get(field), str):
                memory[(field, original[field])] = translated[field]
    items = list(source.items())
    if max_personas is not None:
        items = items[:max_personas]
    pending = [(key, value) for key, value in items if key not in document["personas"]]
    for offset in range(0, len(pending), batch_size):
        batch = dict(pending[offset:offset + batch_size])
        representatives = {}
        representative_keys = {}
        for value in batch.values():
            for field in TRANSLATED_FIELDS:
                text = value.get(field)
                memory_key = (field, text)
                if isinstance(text, str) and memory_key not in memory and memory_key not in representative_keys:
                    item_id = f"item_{len(representatives)}"
                    representatives[item_id] = {field: text}
                    representative_keys[memory_key] = item_id
        if representatives:
            translated_representatives = _translate_batch(
                pipe, representatives, LANGUAGES[code], max_new_tokens
            )
            for memory_key, item_id in representative_keys.items():
                field = memory_key[0]
                memory[memory_key] = translated_representatives[item_id][field]
        translated = copy.deepcopy(batch)
        for value in translated.values():
            for field in TRANSLATED_FIELDS:
                if isinstance(value.get(field), str):
                    value[field] = memory[(field, value[field])]
        document["personas"].update(translated)
        _write_yaml(path, document)
        print(f"{code}: translated {len(document['personas'])}/{len(items)} personas", flush=True)
    return document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen3-4B")
    parser.add_argument("--languages", nargs="*", default=list(LANGUAGES))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-personas", type=int)
    parser.add_argument("--max-new-tokens", type=int, default=4096)
    parser.add_argument("--device", default="cpu", help="Transformers device, for example cpu, 0, 1, or auto")
    args = parser.parse_args()
    if args.batch_size < 1 or args.max_new_tokens < 1:
        parser.error("--batch-size and --max-new-tokens must be positive")

    from transformers import pipeline
    catalog = json.loads((args.root / "persona_catalog.json").read_text(encoding="utf-8"))
    out_root = args.root / "data" / "locales"
    source_document = yaml.safe_load((out_root / "ko" / "personas.yaml").read_text(encoding="utf-8"))
    source_personas = source_document.get("personas", {})
    if len(source_personas) != 1000:
        raise ValueError(f"Korean source must contain 1000 personas, found {len(source_personas)}")
    pipe = None
    for code in args.languages:
        if code not in LANGUAGES:
            raise ValueError(f"unsupported language: {code}")
        locale_dir = out_root / code
        locale_dir.mkdir(parents=True, exist_ok=True)
        scenarios_path = locale_dir / "scenarios.yaml"
        existing = yaml.safe_load(scenarios_path.read_text(encoding="utf-8")) if scenarios_path.exists() else {}
        scenarios = existing or {}
        if code == "ko":
            scenarios = {row["id"]: row for row in catalog["templates"]}
            scenarios_path.write_text(
                yaml.safe_dump(scenarios, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            continue
        else:
            if args.device == "auto":
                pipe = pipe or pipeline(
                    "text-generation", model=args.model, device_map="auto", dtype="auto"
                )
            else:
                device = int(args.device) if args.device.lstrip("-").isdigit() else args.device
                pipe = pipe or pipeline("text-generation", model=args.model, device=device, dtype="auto")
            for row in catalog["templates"]:
                if row["id"] in scenarios:
                    continue
                scenarios[row["id"]] = _translate(
                    pipe, row, LANGUAGES[code], max_new_tokens=args.max_new_tokens
                )
                _write_yaml(scenarios_path, scenarios)
        _write_yaml(scenarios_path, scenarios)
        _translate_personas(
            pipe, source_personas, locale_dir / "personas.yaml", code,
            args.batch_size, args.max_personas, args.max_new_tokens,
        )


if __name__ == "__main__":
    main()

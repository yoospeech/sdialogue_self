# Multilingual Persona Localization Handoff

Read `AGENTS.md` before continuing. This document records the exact state of the
language-specific persona and scenario work at commit `ec63586`.

## Goal

Maintain fully localized data without a shared `common/` persona file or runtime
translation:

- 16 supported languages
- 1,000 complete persona records per language
- 36 complete scenario records per language
- 16,000 persona records and 576 scenario records in total
- stable persona and scenario IDs across every language
- unchanged `PersonaProfile.to_sdialog()` input/output interface
- reproducible random selection through `persona_library.get(language=..., seed=...)`

Supported language codes:

```text
en ar zh fr de it ja ko pt es vi th id hi ru pl
```

## Current status

Korean is the source locale. These translated locales are complete:

```text
en ar zh fr it ja pt vi th id hi pl
```

The remaining locales are:

- `de`: personas and scenarios are missing.
- `es`: personas and scenarios are missing.
- `ru`: 1,000 personas and 36 scenarios exist, but the personas are old derived
  records without the required per-record LLM translation marker. Review and
  regenerate the Russian text; do not merely add the marker.

## Required locale layout

Each directory must contain:

```text
data/locales/<language>/
├── personas.yaml      # exactly 1,000 records
└── scenarios.yaml     # exactly 36 records
```

Every non-Korean `personas.yaml` must include:

```yaml
translation:
  method: llm
  source_language: ko
  version: 1
```

Translate every persona's complete text fields:

```text
name
role
background
goal
mood
communication_style
experience
constraint
circumstances
rules
```

Preserve these identity fields exactly across languages:

```text
persona_id
age
speaker
scenario_id
```

For scenarios, preserve IDs, nested keys, list lengths, speaker values, mood IDs,
and audio configuration. Replace Korean language instructions in `rules` with the
target language. A non-Korean locale must not retain Korean or `Korean` speaking
instructions, and the loader must never silently fall back to another language.

`tools/materialize_personas.py` is only for bootstrapping the Korean source. Do
not use it to claim that a target locale has per-record LLM translations.

## Relevant files

```text
persona_library.py
sample.py
sample_compact.py
persona_catalog.json
tools/generate_persona_locales.py
tools/materialize_personas.py
tools/validate_persona_locales.py
data/locales/*/personas.yaml
data/locales/*/scenarios.yaml
```

## Validation

After completing German, Spanish, and Russian, run:

```bash
python3 tools/validate_persona_locales.py

/data/util/anaconda3/envs/sdialog/bin/flake8 \
  --ignore=W503 \
  --max-line-length=120 \
  persona_library.py \
  sample.py \
  sample_compact.py \
  tools/generate_persona_locales.py \
  tools/materialize_personas.py \
  tools/validate_persona_locales.py
```

Run the loader smoke test:

```bash
PYTHONPATH=src /data/util/anaconda3/envs/sdialog/bin/python - <<'PY'
from persona_library import LANGUAGES, get

for language in LANGUAGES:
    first = get(language=language, seed=42)
    second = get(language=language, seed=42)
    assert first == second
    assert first.user.to_sdialog().language
    print(language, first.scenario["id"], first.user.persona_id, first.agent.persona_id)
PY
```

The final validator must report 16 languages, 16,000 personas, and 576 scenarios.

## Commit guidance

The current checkpoint is:

```text
ec63586 Add multilingual persona generation checkpoint
```

After the remaining locales and all validation pass, create a follow-up commit:

```text
Complete multilingual persona localizations
```

Do not include or delete these unrelated untracked user files:

```text
dialog_0.json
dialog_id.json
dialog_ja.json
dialog_ko.json
fast_softlanding.py
fast_softlanding.sh
```

<div align="center">

# SDialogue Self

**From personas to conversations to speech.**

A multilingual dialogue dataset generator powered by SDialog and local Hugging Face models.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](#installation)
[![License: MIT](https://img.shields.io/badge/License-MIT-22C55E?style=flat-square)](LICENSE)
[![Powered by SDialog](https://img.shields.io/badge/Powered_by-SDialog-6366F1?style=flat-square)](https://github.com/idiap/sdialog)
![Hugging Face](https://img.shields.io/badge/Models-Hugging_Face-FFD21E?style=flat-square&logo=huggingface&logoColor=black)

![Scenarios](https://img.shields.io/badge/Scenarios-36-0EA5E9?style=flat-square)
![Personas](https://img.shields.io/badge/Personas-1%2C000-8B5CF6?style=flat-square)
![Language options](https://img.shields.io/badge/Language_options-16-F59E0B?style=flat-square)

[Features](#features) · [Installation](#installation) · [Quickstart](#quickstart) · [Roadmap](#roadmap)

</div>

## Features

- **Diverse conversations:** 36 everyday, social, and professional scenarios.
- **Reusable personas:** 1,000 fictional adult profiles built from deterministic attribute combinations.
- **Multilingual prompts:** 16 selectable output languages.
- **Flexible turn counts:** fixed lengths or seeded selection within an even-numbered range.
- **Automatic evaluation:** a text-based HF judge requiring no structured output or tool calling.
- **Audio generation:** scenario-specific acoustic presets, stereo output, and optional user-only effects.
- **Dataset artifacts:** dialogue JSON, evaluation JSON, audio, annotations, and RTTM files.

SDialog is pinned as a Git submodule under `vendor/sdialog`. The generator entry point is `sample.py`.

### Language options

English (`en`), Arabic (`ar`), Chinese (`zh`), French (`fr`), German (`de`), Italian (`it`),
Japanese (`ja`), Korean (`ko`), Portuguese (`pt`), Spanish (`es`), Vietnamese (`vi`), Thai (`th`),
Indonesian (`id`), Hindi (`hi`), Russian (`ru`), and Polish (`pl`).

Language selection controls the generation prompt. Actual quality and speech support depend on the
chosen LLM and TTS backend; the default TTS does not necessarily support every listed language.

## Installation

Python 3.10 or newer is recommended. Audio generation requires SDialog's optional audio dependencies.

```bash
git clone --recurse-submodules https://github.com/yoospeech/sdialogue_self.git
cd sdialogue_self
python -m pip install -r requirements.txt
```

If you already cloned the repository, initialize the submodule before installing dependencies:

```bash
git submodule update --init --recursive
```

## Quickstart

List available scenarios and their audio presets:

```bash
python sample.py --list-scenarios
```

Generate and evaluate a six-turn Korean conversation, then synthesize audio if it passes:

```bash
python sample.py --scenario weekend --language ko --turns 6
```

Generate three Japanese travel conversations with 6–12 turns each, applying acoustic effects only to
the `user` speaker. Shared timing still follows the selected preset:

```bash
python sample.py \
  --scenario travel \
  --language ja \
  --count 3 \
  --min-turns 6 \
  --max-turns 12 \
  --user-only-augmentation
```

Generate dialogue and evaluation JSON without synthesizing audio:

```bash
python sample.py --scenario random --language en --count 10 --skip-audio
```

The default model is `LiquidAI/LFM3-1.7B`. Use `--model` to select another Hugging Face model and
`python sample.py --help` to view all options. Verify compatibility and output quality for your checkpoint.

## How it works

```text
Select scenario and personas
  -> Generate a conversation between two persona-driven agents
  -> Evaluate with the shared HF model
  -> Save dialogue and evaluation JSON
  -> Synthesize accepted conversations and save audio annotations
```

Generation and evaluation share one loaded model. The judge returns a single line such as `PASS: reason`
or `FAIL: reason`, allowing evaluation without structured output. Malformed verdicts are treated as
evaluation failures. The LLM is released before audio synthesis begins.

The `user` and `agent` labels identify speaker slots; conversations are not limited to customer support.
Audio presets model acoustic environments, not guaranteed emotional delivery.

### Output layout

Each run creates a separate directory under `output/sample/` by default:

```text
output/sample/run_*/
├── config.json         # Run settings
├── summary.json        # Evaluation summary
├── dialogs/            # Generated conversations
├── evaluations/        # Verdicts, reasons, and participant metadata
└── audio/              # WAV or FLAC, JSON annotations, and RTTM
```

All generated conversations are saved, including failed evaluations. Audio is generated for passing
conversations by default; `--skip-judge` and `--audio-on-fail` explicitly change this behavior.

## Roadmap

- [ ] **Explicit backchannel generation:** create listener responses and insert them during another speaker's turn.
  Currently unsupported; audio overlap only shifts existing turns and does not generate backchannels.
- [ ] Natural interruptions and turn-taking modeling.
- [ ] Preflight validation of TTS language support.
- [ ] Separate model selection for generation and evaluation.
- [ ] Resume and recovery for large generation jobs.

## License

This project's code is released under the [MIT License](LICENSE). SDialog retains its own license and
copyright notices in [vendor/sdialog](vendor/sdialog).

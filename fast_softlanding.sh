#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Codex <https://openai.com>
# SPDX-License-Identifier: MIT
# Generate customer-support text dialogues and matching conversational audio.
#
# Prerequisites:
#   pip install -e '.[audio]'
#   export OPENAI_API_KEY=...  # unless using a local Ollama model
#
# Examples:
#   ./fast_softlanding.sh
#   MODEL=ollama:qwen3:14b COUNT=5 ./fast_softlanding.sh

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
model="${MODEL:-openai:gpt-4.1}"
count="${COUNT:-1}"
output_dir="${OUTPUT_DIR:-${script_dir}/output/fast_softlanding}"
audio_dir="${AUDIO_DIR:-${output_dir}/audio}"

export PYTHONPATH="${script_dir}/src${PYTHONPATH:+:${PYTHONPATH}}"

python3 "${script_dir}/fast_softlanding.py" \
  --model "${model}" \
  --count "${count}" \
  --output "${output_dir}" \
  --audio-output "${audio_dir}" \
  --preset "${PRESET:-conversational}" \
  "$@"

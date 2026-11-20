#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Codex <https://openai.com>
# SPDX-License-Identifier: MIT
"""Generate a small synthetic customer-support dialogue dataset.

Examples:

    OPENAI_API_KEY=... python fast_softlanding.py
    python fast_softlanding.py --model ollama:qwen3:14b --count 5 --output output/dialogs
"""
import argparse
from pathlib import Path

import sdialog
from sdialog import Context
from sdialog.agents import Agent
from sdialog.personas import Customer, SupportAgent


def parse_args():
    """Parse command-line options for dataset generation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="openai:gpt-4.1", help="SDialog model name (default: %(default)s)")
    parser.add_argument("--count", type=int, default=1, help="Number of dialogues to generate (default: %(default)s)")
    parser.add_argument("--output", type=Path, default=Path("output/fast_softlanding"),
                        help="Directory for JSON dialogues (default: %(default)s)")
    parser.add_argument("--audio-output", type=Path, default=None,
                        help="Directory for WAV, JSON, and RTTM audio artifacts")
    parser.add_argument("--preset", default="conversational",
                        help="Audio scene preset when --audio-output is set (default: %(default)s)")
    parser.add_argument("--stereo", action="store_true", help="Write one audio channel per speaker")
    parser.add_argument("--seed", type=int, default=13, help="First random seed (default: %(default)s)")
    return parser.parse_args()


def build_agents():
    """Create the customer and support agents used for each simulation."""
    customer = Agent(
        name="Customer",
        first_utterance="안녕하세요. 결제한 서비스가 바로 시작되지 않아 도움이 필요합니다.",
        persona=Customer(
            name="민지",
            language="Korean",
            issue="A paid service has not started yet",
            desired_outcome="Confirm activation status and get a clear next step",
            sentiment="concerned but cooperative",
            urgency="high",
        ),
    )
    support = Agent(
        name="Support",
        persona=SupportAgent(
            name="지수",
            language="Korean",
            role="Customer support specialist",
            communication_style="warm, concise, and clear",
            empathy_level="high",
            politeness="high",
            rules=("Acknowledge the concern, collect only necessary account details, explain the next step, "
                   "and never claim an action was completed without evidence."),
        ),
    )
    return customer, support


def main():
    """Generate and save the requested dialogues."""
    args = parse_args()
    if args.count < 1:
        raise ValueError("--count must be at least 1")

    sdialog.config.llm(args.model, temperature=0.7)
    args.output.mkdir(parents=True, exist_ok=True)
    if args.audio_output:
        args.audio_output.mkdir(parents=True, exist_ok=True)
    context = Context(location="web chat", environment="customer support", circumstances="service activation")

    for index in range(args.count):
        customer, support = build_agents()
        dialog = customer.dialog_with(support, context=context, max_turns=12, seed=args.seed + index)
        path = args.output / f"dialog_{index:03d}.json"
        dialog.to_file(path)
        print(f"Saved {path}")
        if args.audio_output:
            audio_path = args.audio_output / f"dialog_{index:03d}"
            dialog.to_audio(path=str(audio_path), preset=args.preset, stereo=args.stereo, seed=args.seed + index)
            print(f"Saved {audio_path}.wav, {audio_path}.json, and {audio_path}.rttm")


if __name__ == "__main__":
    main()

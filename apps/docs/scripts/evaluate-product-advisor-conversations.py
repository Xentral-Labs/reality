"""Run the connected ERP-selection conversation suite against a live advisor."""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = (
    ROOT
    / "packages/reality-core/tests/fixtures/product_advisor_conversations.yaml"
)


def _post(url: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url", default="http://localhost:8000/api/journey-guide/questions"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--conversation",
        action="append",
        default=[],
        help="Run only the selected conversation ID; may be repeated.",
    )
    args = parser.parse_args()
    conversations = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))[
        "conversations"
    ]
    if args.conversation:
        conversations = [
            item for item in conversations if item["id"] in args.conversation
        ]
    results: list[dict[str, object]] = []
    for conversation in conversations:
        history: list[dict[str, str]] = []
        turns: list[dict[str, object]] = []
        for question in conversation["questions"]:
            answer = _post(
                args.url,
                {
                    "question": question,
                    "locale": conversation["locale"],
                    "history": history,
                },
            )
            turns.append({"question": question, "answer": answer})
            history.extend(
                (
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": str(answer["text"])},
                )
            )
            history = history[-20:]
        results.append({**conversation, "turns": turns})
    rendered = json.dumps({"conversations": results}, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()

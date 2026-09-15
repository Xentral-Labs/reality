"""Provider SSE decoding. Only complete messages can supply executable tool calls."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Callable
from typing import Any

import httpx

ChatEventSink = Callable[[dict[str, Any]], None]


async def _events(response: httpx.Response) -> AsyncIterator[str]:
    data: list[str] = []
    async for line in response.aiter_lines():
        if not line:
            if data:
                yield "\n".join(data)
                data = []
        elif line.startswith("data:"):
            data.append(line[5:].lstrip(" "))
    # An unterminated frame is not a completed provider response.


async def streamed_message(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    provider: str,
    emit: ChatEventSink,
) -> tuple[Any, dict[str, Any]]:
    blocks: dict[int, dict[str, Any]] = {}
    arguments: dict[int, str] = {}
    calls: dict[int, dict[str, Any]] = {}
    text = ""
    usage: dict[str, Any] = {}
    complete = False
    async with client.stream(
        "POST", url, headers=headers, json={**payload, "stream": True}
    ) as response:
        response.raise_for_status()
        async for raw in _events(response):
            if provider == "openai" and raw == "[DONE]":
                complete = True
                break
            event = json.loads(raw)
            if "error" in event or event.get("type") == "error":
                raise ValueError("Provider stream failed")
            if provider == "anthropic":
                kind = event.get("type")
                index = event.get("index", 0)
                if kind == "message_start":
                    usage.update(event.get("message", {}).get("usage", {}))
                elif kind == "content_block_start":
                    blocks[index] = dict(event["content_block"])
                    initial = blocks[index].get("text", "")
                    if blocks[index].get("type") == "text" and initial:
                        emit({"type": "delta", "text": initial})
                elif kind == "content_block_delta":
                    delta = event["delta"]
                    if delta.get("type") == "text_delta":
                        value = delta["text"]
                        blocks[index]["text"] += value
                        emit({"type": "delta", "text": value})
                    elif delta.get("type") == "input_json_delta":
                        arguments[index] = (
                            arguments.get(index, "") + delta["partial_json"]
                        )
                elif kind == "message_delta":
                    usage.update(event.get("usage", {}))
                elif kind == "message_stop":
                    complete = True
                    break
            else:
                usage.update(event.get("usage") or {})
                choices = event.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                value = delta.get("content") or ""
                if value:
                    text += value
                    emit({"type": "delta", "text": value})
                for fragment in delta.get("tool_calls") or []:
                    call = calls.setdefault(
                        fragment["index"],
                        {
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        },
                    )
                    if fragment.get("id"):
                        call["id"] += fragment["id"]
                    function = fragment.get("function") or {}
                    for key in ("name", "arguments"):
                        call["function"][key] += function.get(key) or ""
    if not complete:
        raise ValueError("Provider stream is incomplete")
    if provider == "anthropic":
        for index, value in arguments.items():
            blocks[index]["input"] = json.loads(value) if value.strip() else {}
        return [blocks[index] for index in sorted(blocks)], usage
    assistant: dict[str, Any] = {"role": "assistant", "content": text or None}
    if calls:
        assistant["tool_calls"] = [calls[index] for index in sorted(calls)]
    return assistant, usage

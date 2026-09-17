"""Request-scoped streaming bridge over the ordinary synchronous chat service."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from typing import Any

from sqlalchemy.orm import Session

from reality.services.analytics.reports import caller
from reality.services.core import InvalidOperation, NotFound

_active_sends: set[asyncio.Task[None]] = set()


async def chat_events(
    session_factory: Callable[..., Session],
    send: Callable[..., Any],
    tenant_id: str,
    session_id: str,
    message: str,
    *,
    principal: Any,
    options: dict[str, Any],
) -> AsyncIterator[str]:
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    connected = True

    def emit(event: dict[str, Any]) -> None:
        def put() -> None:
            if connected:
                queue.put_nowait(event)

        try:
            loop.call_soon_threadsafe(put)
        except RuntimeError:
            # A closed client/event loop must not replay or interrupt persistence.
            pass

    def work() -> None:
        try:
            with session_factory() as session, caller(principal):
                user, assistant = send(
                    session,
                    tenant_id,
                    session_id,
                    message,
                    on_event=emit,
                    **options,
                )
                result = {
                    "type": "done",
                    "user": {"id": user.id, "content": user.content},
                    "assistant": {"id": assistant.id, "content": assistant.content},
                }
            emit(result)
        except (NotFound, InvalidOperation) as error:
            emit({"type": "error", "message": str(error)})
        except Exception:  # noqa: BLE001
            emit(
                {
                    "type": "error",
                    "message": "The chat could not complete. Reload to check its status.",
                }
            )

    task = asyncio.create_task(asyncio.to_thread(work))
    # Keep a reference until completion even if the client disconnects. The thread
    # owns its session; it completes the original send once, never a retry.
    _active_sends.add(task)
    task.add_done_callback(_active_sends.discard)
    task.add_done_callback(
        lambda finished: finished.exception() if not finished.cancelled() else None
    )
    try:
        yield json.dumps({"type": "start"}) + "\n"
        while True:
            event = await queue.get()
            yield json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
            if event["type"] in {"done", "error"}:
                await task
                break
    finally:
        connected = False

import asyncio
import json

import httpx
import pytest

from reality.agent.streaming import streamed_message


class Chunks(httpx.AsyncByteStream):
    def __init__(self, chunks):
        self.chunks = chunks

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk


def frames(provider, *, complete=True, tool=False):
    if provider == "anthropic":
        events = [
            {"type": "message_start", "message": {"usage": {"input_tokens": 4}}},
            {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""},
            },
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": "Grüße"},
            },
        ]
        if tool:
            events += [
                {
                    "type": "content_block_start",
                    "index": 1,
                    "content_block": {
                        "type": "tool_use",
                        "id": "call1",
                        "name": "inventory_read",
                        "input": {},
                    },
                },
                {
                    "type": "content_block_delta",
                    "index": 1,
                    "delta": {"type": "input_json_delta", "partial_json": '{"limit":'},
                },
                {
                    "type": "content_block_delta",
                    "index": 1,
                    "delta": {"type": "input_json_delta", "partial_json": "2}"},
                },
            ]
        events += [
            {
                "type": "message_delta",
                "delta": {"stop_reason": "tool_use" if tool else "end_turn"},
                "usage": {"output_tokens": 3},
            }
        ]
        if complete:
            events.append({"type": "message_stop"})
        return "".join(
            "data: " + json.dumps(e, ensure_ascii=False) + "\n\n" for e in events
        ).encode()
    deltas = [{"content": "Grüße"}]
    if tool:
        deltas += [
            {
                "tool_calls": [
                    {
                        "index": 0,
                        "id": "call1",
                        "type": "function",
                        "function": {
                            "name": "inventory_read",
                            "arguments": '{"limit":',
                        },
                    }
                ]
            },
            {"tool_calls": [{"index": 0, "function": {"arguments": "2}"}}]},
        ]
    text = "".join(
        "data: " + json.dumps({"choices": [{"delta": d}]}, ensure_ascii=False) + "\n\n"
        for d in deltas
    )
    return (text + ("data: [DONE]\n\n" if complete else "")).encode()


@pytest.mark.parametrize("provider", ["anthropic", "openai"])
def test_stream_assembles_complete_tools_and_emits_only_text(provider):
    events = []
    raw = frames(provider, tool=True)

    # Byte-at-a-time covers split UTF-8 and SSE boundaries.
    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200, stream=Chunks([raw[i : i + 1] for i in range(len(raw))])
                )
            )
        ) as client:
            return await streamed_message(
                client,
                "https://provider.test/messages",
                {},
                {},
                provider,
                events.append,
            )

    message, usage = asyncio.run(run())
    assert events == [{"type": "delta", "text": "Grüße"}]
    if provider == "anthropic":
        assert message[1]["input"] == {"limit": 2}
        assert usage == {"input_tokens": 4, "output_tokens": 3}
    else:
        assert json.loads(message["tool_calls"][0]["function"]["arguments"]) == {
            "limit": 2
        }


@pytest.mark.parametrize("provider", ["anthropic", "openai"])
def test_truncated_stream_is_not_a_complete_answer(provider):
    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200, stream=Chunks([frames(provider, complete=False)])
                )
            )
        ) as client:
            return await streamed_message(
                client,
                "https://provider.test/messages",
                {},
                {},
                provider,
                lambda e: None,
            )

    with pytest.raises(ValueError, match="incomplete"):
        asyncio.run(run())


def test_anthropic_cache_and_lossless_results(session, business, monkeypatch, caplog):
    from reality.agent import mcp_chat

    requests = []
    original_client = httpx.AsyncClient
    result = {
        "amount": "12.3400",
        "id": "opaque",
        "nested": ["é", None],
        "next_cursor": "page",
    }

    def response(request):
        requests.append(json.loads(request.content))
        content = (
            [{"type": "tool_use", "id": "call", "name": "inventory_read", "input": {}}]
            if len(requests) == 1
            else [{"type": "text", "text": "Done"}]
        )
        return httpx.Response(
            200, json={"content": content, "usage": {"input_tokens": 10}}
        )

    monkeypatch.setattr(
        mcp_chat.httpx,
        "AsyncClient",
        lambda **kw: original_client(transport=httpx.MockTransport(response)),
    )
    monkeypatch.setattr(mcp_chat, "dispatch_tool", lambda *a, **kw: result)
    # Migration logging configuration can disable pre-existing module loggers.
    monkeypatch.setattr(mcp_chat.logger, "disabled", False)
    with caplog.at_level("INFO", logger=mcp_chat.__name__):
        answer = asyncio.run(
            mcp_chat.reply_via_anthropic_tools(
                session=session,
                tenant_id=business.tenant.id,
                api_key="secret-test",
                history=[],
                message="private business question",
            )
        )
    assert answer == "Done"
    assert requests[0]["tools"][-1]["cache_control"] == {"type": "ephemeral"}
    system = requests[0]["system"]
    assert system[-1]["cache_control"] == {"type": "ephemeral"}
    assert "Scope and trust boundary" in system[0]["text"]
    payload = requests[1]["messages"][-1]["content"][0]["content"]
    assert json.loads(payload) == result
    assert ": " not in payload
    assert "chat_provider_round" in caplog.text
    assert "private business question" not in caplog.text
    assert "secret-test" not in caplog.text


def test_stream_route_completes_and_blocks_foreign_session(
    session, business, monkeypatch
):
    from contextlib import contextmanager

    from fastapi.testclient import TestClient

    from reality.services.core import create_chat_session, create_tenant
    from reality.web import api
    from reality.web.app import app

    chat = create_chat_session(session, business.tenant.id)
    other = create_tenant(session, "Other tenant")
    other_chat = create_chat_session(session, other.id)
    app.dependency_overrides[api.database_session] = lambda: session

    @contextmanager
    def factory():
        yield session

    monkeypatch.setattr(api, "Session", factory)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    try:
        with TestClient(app) as client:
            url = f"/api/tenants/{business.tenant.id}/copilot/sessions/"
            denied = client.post(
                url + other_chat.id + "/messages?stream=true", json={"message": "Hello"}
            )
            assert denied.status_code == 404
            response = client.post(
                url + chat.id + "/messages?stream=true", json={"message": "Hello"}
            )
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("application/x-ndjson")
            events = [json.loads(line) for line in response.text.splitlines()]
            assert events[0] == {"type": "start"}
            assert events[-1]["type"] == "done"
            assert events[-1]["assistant"]["id"]
            assert response.headers["x-accel-buffering"] == "no"
    finally:
        app.dependency_overrides.clear()


def test_anthropic_empty_tool_arguments_are_valid():
    events = [
        {
            "type": "content_block_start",
            "index": 0,
            "content_block": {
                "type": "tool_use",
                "id": "call",
                "name": "inventory_read",
                "input": {},
            },
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "input_json_delta", "partial_json": ""},
        },
        {"type": "message_stop"},
    ]
    raw = "".join("data: " + json.dumps(e) + "\n\n" for e in events).encode()

    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, stream=Chunks([raw]))
            )
        ) as client:
            return await streamed_message(
                client,
                "https://provider.test/messages",
                {},
                {},
                "anthropic",
                lambda e: None,
            )

    message, _ = asyncio.run(run())
    assert message[0]["input"] == {}


@pytest.mark.parametrize("provider", ["anthropic", "openai"])
def test_streaming_adapter_dispatches_once_after_complete_arguments(
    provider, session, business, monkeypatch
):
    from reality.agent import mcp_chat

    original_client = httpx.AsyncClient
    requests, dispatched, events = [], [], []

    def response(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            200, stream=Chunks([frames(provider, tool=len(requests) == 1)])
        )

    monkeypatch.setattr(
        mcp_chat.httpx,
        "AsyncClient",
        lambda **kw: original_client(transport=httpx.MockTransport(response)),
    )

    def dispatch(db, tenant, name, arguments, *, allowed_access):
        dispatched.append((tenant, name, arguments, allowed_access))
        return {"available": "3.0000"}

    monkeypatch.setattr(mcp_chat, "dispatch_tool", dispatch)
    options = {
        "session": session,
        "tenant_id": business.tenant.id,
        "api_key": "test",
        "history": [],
        "message": "Stock?",
        "on_event": events.append,
    }

    if provider == "anthropic":
        answer = asyncio.run(mcp_chat.reply_via_anthropic_tools(**options))
    else:
        answer = asyncio.run(
            mcp_chat.reply_via_tools(
                **options, model="test", base_url="https://provider.test"
            )
        )
    assert answer == "Grüße"
    assert dispatched == [
        (
            business.tenant.id,
            "inventory_read",
            {"limit": 2},
            ("read", "propose", "confirm"),
        )
    ]
    assert [e["type"] for e in events] == ["reset", "delta", "reset", "delta"]


def test_partial_provider_failure_is_replaced_by_durable_failure(
    session, business, monkeypatch
):
    from reality.agent import mcp_chat
    from reality.services.core import (
        chat_messages,
        create_chat_session,
        send_chat_message,
    )

    async def failure(**kwargs):
        kwargs["on_event"]({"type": "delta", "text": "Incomplete private answer"})
        raise ValueError("incomplete")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(mcp_chat, "reply_via_anthropic_tools", failure)
    chat = create_chat_session(session, business.tenant.id)
    events = []
    _, answer = send_chat_message(
        session, business.tenant.id, chat.id, "Stock?", on_event=events.append
    )
    assert "could not answer" in answer.content
    assert all(
        "Incomplete private answer" not in row.content
        for row in chat_messages(session, business.tenant.id, chat.id)
    )
    assert events[0]["type"] == "delta"


def test_disconnect_finishes_original_work_once_and_closes_owned_session():
    from contextlib import contextmanager
    from threading import Event
    from types import SimpleNamespace

    from reality.web.chat_stream import _active_sends, chat_events

    release, finished = Event(), Event()
    calls = []

    @contextmanager
    def factory():
        try:
            yield object()
        finally:
            finished.set()

    def send(db, tenant, session_id, message, **kwargs):
        calls.append((tenant, session_id))
        kwargs["on_event"]({"type": "delta", "text": "Early"})
        assert release.wait(5)
        return SimpleNamespace(id="u", content=message), SimpleNamespace(
            id="a", content="Done"
        )

    async def run():
        stream = chat_events(
            factory, send, "tenant", "session", "Question", principal=None, options={}
        )
        assert json.loads(await anext(stream))["type"] == "start"
        assert json.loads(await anext(stream))["type"] == "delta"
        await stream.aclose()
        assert not finished.is_set()
        release.set()
        await asyncio.gather(*list(_active_sends))
        assert finished.is_set()

    asyncio.run(run())
    assert calls == [("tenant", "session")]


def test_stream_preflight_does_not_load_message_history(session, business, monkeypatch):
    from contextlib import contextmanager
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from sqlalchemy import event

    from reality.services.core import create_chat_session
    from reality.web import api
    from reality.web.app import app

    chat = create_chat_session(session, business.tenant.id)
    app.dependency_overrides[api.database_session] = lambda: session

    @contextmanager
    def factory():
        yield session

    monkeypatch.setattr(api, "Session", factory)
    monkeypatch.setattr(
        api,
        "send_chat_message",
        lambda *args, **kwargs: (
            SimpleNamespace(id="u", content="Question"),
            SimpleNamespace(id="a", content="Answer"),
        ),
    )
    statements = []

    def capture(conn, cursor, statement, parameters, context, many):
        statements.append(statement)

    event.listen(session.get_bind(), "before_cursor_execute", capture)
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/tenants/{business.tenant.id}/copilot/sessions/{chat.id}/messages?stream=true",
                json={"message": "Question"},
            )
        assert response.status_code == 200
        assert not any("FROM chat_message " in statement for statement in statements)
    finally:
        event.remove(session.get_bind(), "before_cursor_execute", capture)
        app.dependency_overrides.clear()


def test_authenticated_stream_preflight_releases_connection(
    session, business, scheduled_owner, monkeypatch
):
    from types import SimpleNamespace

    from reality.services.core import create_chat_session
    from reality.web import api, chat_stream

    chat = create_chat_session(session, business.tenant.id)
    expected = (
        scheduled_owner.id,
        scheduled_owner.language,
        scheduled_owner.locale,
        scheduled_owner.timezone,
    )

    def events(*args, **kwargs):
        assert not session.in_transaction(), (
            "Preflight must not retain a provider-wait connection"
        )
        options = kwargs["options"]
        assert (
            options["actor_user_id"],
            options["language"],
            options["locale"],
            options["timezone"],
        ) == expected
        assert kwargs["principal"].user_id == expected[0]

        async def empty():
            if False:
                yield ""

        return empty()

    monkeypatch.setattr(chat_stream, "chat_events", events)
    response = api.post_copilot_message(
        business.tenant.id,
        chat.id,
        api.CopilotMessageWrite(message="Question"),
        SimpleNamespace(state=SimpleNamespace(user=scheduled_owner)),
        session,
        stream=True,
    )
    assert response.media_type == "application/x-ndjson"

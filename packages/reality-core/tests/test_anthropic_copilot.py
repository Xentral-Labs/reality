import pytest

from reality.agent import mcp_chat


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


@pytest.mark.anyio
async def test_anthropic_copilot_executes_canonical_tool_and_returns_text(
    monkeypatch, session, business
):
    requests = []
    responses = iter(
        [
            {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "inventory_read",
                        "input": {},
                    }
                ]
            },
            {"content": [{"type": "text", "text": "Two units are available."}]},
        ]
    )

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, headers, json):
            requests.append((url, headers, json))
            return FakeResponse(next(responses))

    monkeypatch.setattr(mcp_chat.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    monkeypatch.setattr(
        mcp_chat,
        "model_tool_schemas",
        lambda **kwargs: [
            {
                "type": "function",
                "function": {
                    "name": "inventory_read",
                    "description": "Read inventory",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ],
    )
    monkeypatch.setattr(
        mcp_chat,
        "dispatch_tool",
        lambda *args, **kwargs: {"available": "2"},
    )

    result = await mcp_chat.reply_via_anthropic_tools(
        session=session,
        tenant_id=business.tenant.id,
        api_key="secret",
        workspace_id="wrk_123",
        history=[],
        message="How much inventory?",
        language="de",
        locale="de-DE",
        timezone="Europe/Berlin",
    )

    assert result == "Two units are available."
    assert requests[0][0] == "https://api.anthropic.com/v1/messages"
    assert requests[0][1]["x-api-key"] == "secret"
    assert requests[0][1]["anthropic-workspace-id"] == "wrk_123"
    assert requests[0][2]["model"] == "claude-haiku-4-5-20251001"
    assert requests[0][2]["tools"][0]["input_schema"]["type"] == "object"
    assert "UI language: de" in requests[0][2]["system"]
    assert "Locale and number format: de-DE" in requests[0][2]["system"]
    assert "Display timezone: Europe/Berlin" in requests[0][2]["system"]
    assert "date-only values" in requests[0][2]["system"]
    assert "opaque IDs" in requests[0][2]["system"]
    assert requests[1][2]["messages"][-2]["content"][0]["type"] == "tool_result"


@pytest.mark.anyio
async def test_openai_compatible_copilot_receives_the_same_presentation_contract(
    monkeypatch, session, business
):
    requests = []

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, headers, json):
            requests.append(json)
            return FakeResponse({"choices": [{"message": {"content": "25,00 €"}}]})

    monkeypatch.setattr(mcp_chat.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    monkeypatch.setattr(mcp_chat, "model_tool_schemas", lambda **kwargs: [])
    result = await mcp_chat.reply_via_tools(
        session=session,
        tenant_id=business.tenant.id,
        api_key="secret",
        model="example",
        base_url="https://example.test",
        history=[],
        message="Kundenguthaben?",
        language="de",
        locale="de-DE",
        timezone="Europe/Berlin",
    )

    assert result == "25,00 €"
    system = requests[0]["messages"][0]["content"]
    assert "UI language: de" in system
    assert "Locale and number format: de-DE" in system
    assert "Display timezone: Europe/Berlin" in system

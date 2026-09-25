import pytest

from reality.agent import mcp_chat


class FakeResponse:
    is_error = False

    def __init__(self, payload):
        self.payload = payload

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
    system = "\n".join(block["text"] for block in requests[0][2]["system"])
    assert "UI language: de" in system
    assert "Locale and number format: de-DE" in system
    assert "Display timezone: Europe/Berlin" in system
    assert "date-only values" in system
    assert "opaque IDs" in system
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


@pytest.mark.anyio
async def test_a_refused_tool_call_reaches_the_model_instead_of_ending_the_turn(
    monkeypatch, session, business
):
    """Found by asking it: "make a report of the last 7 days" answered nothing.

    The model wrote a filter field without its alias, the traversal refused it,
    and the exception travelled past the whole loop into the handler that turns
    everything into "could not answer right now". The one sentence that would
    have let the model fix its own call was the one that did not survive.
    """
    from reality.services.core import InvalidOperation

    responses = iter(
        [
            {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "graph_ask",
                        "input": {"question": {"from": "order"}},
                    }
                ]
            },
            {"content": [{"type": "text", "text": "Hier ist der Bericht."}]},
        ]
    )
    requests = []

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, headers, json):
            requests.append(json)
            return FakeResponse(next(responses))

    def refuse(*args, **kwargs):
        raise InvalidOperation("a field is alias.property, got 'ordered_at'")

    monkeypatch.setattr(mcp_chat.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    monkeypatch.setattr(mcp_chat, "model_tool_schemas", lambda **kwargs: [])
    monkeypatch.setattr(mcp_chat, "dispatch_tool", refuse)

    result = await mcp_chat.reply_via_anthropic_tools(
        session=session,
        tenant_id=business.tenant.id,
        api_key="secret",
        workspace_id="wrk_123",
        history=[],
        message="Alle Aufträge der letzten 7 Tage als Bericht",
        language="de",
        locale="de-DE",
        timezone="Europe/Berlin",
    )

    assert result == "Hier ist der Bericht."
    # The request payload is mutated in place between rounds, so the tool
    # result is the second-to-last message once the turn has finished.
    sent_back = requests[1]["messages"][-2]["content"][0]
    assert sent_back["is_error"] is True
    assert "alias.property" in sent_back["content"]


@pytest.mark.anyio
async def test_a_tool_failure_that_is_not_about_the_request_still_travels_up(
    monkeypatch, session, business
):
    """The positive control for the test above: not every error is a refusal.

    A database that is gone is not something the model can correct by writing a
    better call, so it must not be fed back as advice.
    """

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, headers, json):
            return FakeResponse(
                {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "toolu_1",
                            "name": "graph_ask",
                            "input": {},
                        }
                    ]
                }
            )

    def collapse(*args, **kwargs):
        raise RuntimeError("the connection pool is gone")

    monkeypatch.setattr(mcp_chat.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    monkeypatch.setattr(mcp_chat, "model_tool_schemas", lambda **kwargs: [])
    monkeypatch.setattr(mcp_chat, "dispatch_tool", collapse)

    with pytest.raises(RuntimeError):
        await mcp_chat.reply_via_anthropic_tools(
            session=session,
            tenant_id=business.tenant.id,
            api_key="secret",
            workspace_id="wrk_123",
            history=[],
            message="Alle Aufträge",
            language="de",
            locale="de-DE",
            timezone="Europe/Berlin",
        )


@pytest.mark.anyio
async def test_running_out_of_steps_says_what_was_tried(monkeypatch, session, business):
    """ "The model exceeded the maximum number of tool steps" told nobody anything.

    An acceptance run put five realistic ERP questions to the copilot and four
    ended on that sentence. What the reader needed to know is that the question
    was looked at repeatedly and still has no answer — which usually means part
    of it cannot be expressed, not that another attempt would help.
    """

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, headers, json):
            return FakeResponse(
                {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "toolu_1",
                            "name": "graph_ask",
                            "input": {},
                        }
                    ]
                }
            )

    monkeypatch.setattr(mcp_chat.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    monkeypatch.setattr(mcp_chat, "model_tool_schemas", lambda **kwargs: [])
    monkeypatch.setattr(mcp_chat, "dispatch_tool", lambda *a, **k: {"rows": []})

    reply = await mcp_chat.reply_via_anthropic_tools(
        session=session,
        tenant_id=business.tenant.id,
        api_key="secret",
        workspace_id="wrk_123",
        history=[],
        message="Offene Posten nach Alter",
        language="de",
        locale="de-DE",
        timezone="Europe/Berlin",
    )

    assert "graph_ask" in reply, "name the tool it kept reaching for"
    assert "cannot be expressed" in reply, "and why another attempt will not help"
    assert "maximum number of tool steps" not in reply


UNION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "discriminator": {"propertyName": "operation"},
    "properties": {"reason": {"type": "string"}},
    "required": ["reason"],
    "oneOf": [
        {
            "type": "object",
            "title": "Assign",
            "properties": {
                "operation": {"type": "string", "const": "assign"},
                "document_id": {"type": "string"},
                "parts": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["operation", "reason", "document_id", "parts"],
        },
        {
            "type": "object",
            "title": "Withdraw",
            "properties": {
                "operation": {"type": "string", "const": "withdraw"},
                "basis_id": {"type": "string"},
                "parts": {"type": "object"},
            },
            "required": ["operation", "reason", "basis_id"],
        },
    ],
}


def test_a_top_level_union_is_folded_into_one_object_schema():
    """Found by asking it: "Welche Kundenaufträge sind noch offen?" answered nothing.

    Four propose tools declare their arguments as a discriminated union, and the
    Messages API refuses oneOf, allOf and anyOf at the top level of an input
    schema. One such tool in the catalog rejected the whole request, so every
    question reached the user as "could not answer right now".
    """
    branches = mcp_chat._union_branches(UNION_SCHEMA)
    flattened = mcp_chat._flattened_schema(UNION_SCHEMA, branches)

    assert not {"oneOf", "allOf", "anyOf", "discriminator"} & set(flattened)
    assert flattened["type"] == "object"
    # The discriminator reads as the set of values that select a branch.
    assert flattened["properties"]["operation"]["enum"] == ["assign", "withdraw"]
    # Every branch's own fields stay reachable.
    assert {"reason", "operation", "document_id", "basis_id", "parts"} == set(
        flattened["properties"]
    )
    # Only what every branch demands survives as required.
    assert flattened["required"] == ["reason", "operation"]
    # A field the branches disagree about keeps both readings, which is legal
    # one level down.
    assert flattened["properties"]["parts"]["anyOf"] == [
        {"type": "array", "items": {"type": "string"}},
        {"type": "object"},
    ]


def test_the_branches_the_flattened_schema_cannot_enforce_are_described():
    guidance = mcp_chat._union_guidance(mcp_chat._union_branches(UNION_SCHEMA))

    assert 'Assign (operation="assign"): also requires document_id, parts' in guidance
    assert 'Withdraw (operation="withdraw"): also requires basis_id' in guidance


def test_a_schema_without_a_union_is_handed_over_unchanged():
    schema = {"type": "object", "properties": {"item_id": {"type": "string"}}}

    branches = mcp_chat._union_branches(schema)

    assert branches == []
    assert mcp_chat._flattened_schema(schema, branches) is schema
    assert mcp_chat._union_guidance(branches) == ""


def test_no_catalog_tool_reaches_the_provider_with_a_top_level_union():
    offenders = {
        tool["name"]: sorted({"oneOf", "allOf", "anyOf"} & set(tool["input_schema"]))
        for tool in mcp_chat._anthropic_tool_schemas(("read", "propose"))
        if {"oneOf", "allOf", "anyOf"} & set(tool["input_schema"])
    }

    assert offenders == {}


@pytest.mark.anyio
async def test_a_rejected_request_reports_what_the_provider_objected_to():
    """raise_for_status() reports only the status line.

    On a streamed response the body has not been read yet either, so the reason
    the request was refused never reached the log and the 400 had to be
    reproduced by hand to find out which tool the provider had objected to.
    """
    import httpx

    from reality.agent import streaming

    class Rejected:
        is_error = True
        status_code = 400
        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")

        def __init__(self):
            self.text = ""

        async def aread(self):
            self.text = (
                '{"type":"error","error":{"type":"invalid_request_error",'
                '"message":"tools.9.custom.input_schema: input_schema does not '
                'support oneOf, allOf, or anyOf at the top level"}}'
            )

    with pytest.raises(httpx.HTTPStatusError) as rejection:
        await streaming.raise_for_status(Rejected(), "anthropic")

    message = str(rejection.value)
    assert "anthropic rejected the request with 400" in message
    assert "does not support oneOf, allOf, or anyOf at the top level" in message


@pytest.mark.anyio
async def test_an_accepted_response_passes_through():
    from reality.agent import streaming

    class Accepted:
        is_error = False

    assert await streaming.raise_for_status(Accepted(), "anthropic") is None

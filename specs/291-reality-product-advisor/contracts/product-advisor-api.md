# Contract: Product Advisor Question API

The existing public route remains backward compatible:

`POST /api/journey-guide/questions`

## Request

```json
{
  "question": "Wie würden wir B2B-Vertrieb mit Reality abbilden?",
  "locale": "en",
  "history": []
}
```

`locale` becomes a surface-language hint for ambiguous or very short input. The latest substantive question determines the answer language. History remains anonymous, ephemeral and read-only; clients may submit at most twenty turns (ten exchanges). The service compacts prior user concerns for referential or synthesis questions and never treats prior assistant prose as product evidence.

## Additive response

```json
{
  "question": "Wie würden wir B2B-Vertrieb mit Reality abbilden?",
  "detected_language": "de",
  "intent": "solution_advice",
  "status": "partial",
  "text": "Reality deckt den üblichen Ablauf ...",
  "citations": ["A01", "C07", "E02"],
  "matches": [],
  "outcome": "researched",
  "knowledge_version": "advisor-v1:sha256:...",
  "clarification": null,
  "claims": [
    {
      "id": "claim_...",
      "statement": "Mehrere Lieferungen können in einer Monatsrechnung zusammengefasst werden.",
      "support": "proven",
      "workflow_role": "native",
      "source_ids": ["journey:E02"],
      "limitations": [],
      "tools": []
    }
  ],
  "sources": [
    {
      "id": "journey:E02",
      "kind": "journey",
      "title": "Monthly collective invoice over several shipments",
      "url": "https://docs.example/getting-started/business-journeys#E02"
    }
  ]
}
```

## Compatibility and safety

- Existing clients may continue to render `text`, `status`, `citations`, `matches` and `outcome`.
- `citations` remains Journey IDs; other references appear in `sources`.
- New fields are optional to clients and clients never recalculate status.
- Provider failure returns validated deterministic evidence, one clarification or not established.
- Failed claim validation never passes raw provider prose through.
- The canonical read tool returns the same public structure. Authorized internal and tenant context is additive through existing scoped paths.

## Additive progress mode

Clients may request newline-delimited JSON progress from the same route:

`POST /api/journey-guide/questions?stream=true`

The request body is unchanged. The response media type is `application/x-ndjson`. Each line is one JSON object with an increasing sequence number:

```json
{"sequence":1,"stage":"accepted","elapsed_ms":0}
{"sequence":2,"stage":"researching","elapsed_ms":4}
{"sequence":3,"stage":"composing","elapsed_ms":1210}
{"sequence":4,"stage":"validating","elapsed_ms":6930}
{"sequence":5,"stage":"complete","elapsed_ms":7012,"answer":{"status":"supported","text":"..."}}
```

- Allowed stages are `accepted`, `researching`, `composing`, `validating` and `complete`.
- A non-terminal event contains no answer text, claim, source, provider output or user content.
- A stage is omitted when that work is skipped; clients must not infer a missing product conclusion.
- `complete.answer` is the same validated response object returned by the compatible JSON path.
- The server ends the response after `complete`. If the client disconnects, later avoidable provider stages are cancelled or not scheduled.
- Existing rate limits, history bounds and public evidence restrictions apply unchanged.

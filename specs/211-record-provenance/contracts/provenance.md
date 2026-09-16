# Provenance read contract

Existing register, detail and Inspector reads gain one optional `origin` object on records that can carry a source:

`{kind, system_code, system_name, source_type, external_id, source_version, received_at, source_record_id, url?, superseded?}`

`kind` is `source` or `application`. For `application`, only `kind` and an optional `actor` naming the deciding user are present; the client renders a stated origin, never a blank. For `source`, `system_name` falls back to the retained `system_code` when no configured system exists under that code within the tenant, and `url` is then absent.

`url`, when present, is an absolute `https` address composed from the configured base address, the connector's relative template for `source_type`, and the percent-encoded `external_id`. It is absent whenever the base address is unset, the connector declares no template for that source type, or the record has no external reference. It is never composed from payload content, and it is never stored.

Detail reads additionally carry `contributing_systems`: a bounded, ordered list of distinct source system codes taken from the record's Facts, present only when more than one distinct system contributed. Register reads never carry it.

The `source_record` Inspector kind keeps every existing row and adds: the retained payload as bounded read-only text with an explicit `truncated` flag; the terminal interpretation outcome as `{classification, interpreter_name, interpreter_version, reason_code}`, or the label `not_recorded` when no terminal outcome exists; and the resolved `url` where one exists. Existing rows, links, back navigation and the compact and full variants are unchanged.

Configuration adds one write on the existing source-system surface: set or clear `base_url` on a configured `SourceSystem`. It is validated as absolute, `https`, without user information, and bounded in length. It goes through the shared application service and the existing business-operation policy. No new application-tool schema, no vendor call, no credential storage.

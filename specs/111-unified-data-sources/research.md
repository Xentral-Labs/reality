# Research

Read-only research delegated under speckit-plan and checked against installed code.

- Existing integrations/source APIs load all original payloads and jobs; a new bounded metadata adapter avoids these reads without changing existing clients.
- SourceRecord source_system is its existing exact code; opaque source ID selects a version. ImportJob is unique per tenant/source, so a scoped outer join does not multiply rows.
- Source-system counts group all held SourceRecord versions, never distinct external IDs.
- Existing document_page supports exact source-system code but not exact source ID. Add the shortest source-record filter before paging and preserve all callers.
- Existing Inspector safely renders selected payload as text. ImportJob status alone does not establish interpretation success; display it neutrally with a clear explanation.
- Evidence query searches number, IDs and source metadata, not party name. Do not show commitment-count data as total Reality links.

# Research
Plan-skill read-only agent order_research audited real API/browser harness options.
- Decision: use existing postgres_database fixture and separate Uvicorn/Vite processes. Rationale: ordinary session fixture wraps an outer transaction invisible to a separate API. Alternative mocked HTTP cannot prove handoffs.
- Decision: enabled auth with test-only ordinary owner/membership; real login. Rationale: platform admin would bypass tenant membership; no shared credentials required.
- Decision: explicit tests/browser/unified_business_journey.py runner rather than adding browser dependency to every backend invocation. Existing backend service story remains in standard collection.
- Decision: service-created reference/opening stock seed, actual UI business mutations and real receipt reads. Existing browser scripts supply locators only; no route.fulfill financial fixtures.
- Decision: existing schema migrations, dedicated ephemeral ports, subprocess ownership and database fixture cleanup. No new storage or infrastructure.

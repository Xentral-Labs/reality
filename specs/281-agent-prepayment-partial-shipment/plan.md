# Implementation Plan: Agent-Guided Prepayment and Partial Shipment

## Constitution Check

PASS. The feature reuses order-backed invoice proposals, shipment proposals, fulfillment readiness and human proposal review. It adds no schema, document status, alternate rule path or direct Chat write.

## Design

1. Extend the server-owned Chat instruction with the canonical sequence: resolve → read readiness → prepare exact proposal → human review → reread.
2. Ensure both provider catalogs expose the necessary readiness, sales-invoice and shipment proposal tools while decision tools remain absent.
3. Add contract tests before the prompt change and run focused Chat/catalog tests.

## Files

- `packages/reality-core/src/reality/agent/mcp_chat.py`
- `packages/reality-core/tests/test_mcp_chat.py`

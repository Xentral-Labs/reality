# Copilot Contracts

## Settings read

`GET /api/tenants/{tenant_id}/settings/ai` remains owner-authorized and returns MCP configuration plus a `copilot` object containing only `managed`, `available`, and `provider_name`. It does not return provider credentials or internal model identifiers.

## Chat runtime

The managed provider receives conversation history, the current message, the system instruction, and read/propose schemas derived from the canonical tool catalog. Tool requests dispatch through the existing tenant-scoped dispatcher. Confirmation tools are never included. Failures return a safe generic Copilot message.


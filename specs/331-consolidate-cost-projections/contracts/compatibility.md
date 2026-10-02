# Compatibility contract

No public tool, command, view, projection, exception, event or MCP schema changes.
Existing logical record kinds, selection IDs, result shapes, precision, error codes,
confirmation requirements and pagination bindings remain unchanged. SQL consumers use
filtered updatable views with their original names and columns. Internal discriminator
columns are not mapped to public fields. Compatibility views hold no authority.

Direct writes to shared physical storage receive the same constraint/lifecycle checks
as writes through logical views. Existing saved analytics definitions need no rewrite.

# Use your own data

Once you have tried the demo, start with one business question from your company — for example,
which customer orders still need delivery. Agree which source records are needed to answer it.

## 1. Check the connection first

Open **Integrations** in your company and check the source you want to use. Registering a source
system does not connect it to an ERP. Authentication, data transport and interpretation must be
available for the record types you intend to receive.

The presence of Shopify, Xentral or Odoo in an integration catalog does not mean that a ready-to-use
connection is available. Confirm the actual integration scope with the person implementing it before
planning an import.

## 2. Start with a small, separate pilot

Use a separate company and a small set of records with known results. Include an ordinary order, a
partial delivery and a difficult case. Keep the first pilot read-only towards your upstream ERP:
receive its data in Reality and compare the resulting answers without changing the ERP.

## 3. Check one answer all the way back

Ask your [agent](../getting-started/connect-agent) a specific question. Compare the answer with your
source system and follow its records back through **Reality → Evidence → Source**. Missing or
uninterpreted records must remain visible as gaps; they are not proof that no work is outstanding.

Only expand the data scope when the result is understood. Agree permissions, proposal review and
verification separately before enabling actions.

For the technical implementation, use the
[repository integration handbook](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/integrations/connector-contract.md).

# Glossary

Key terms from Reality, the interactive command catalog and the developer guides. Entries explain
meaning, purpose and distinctions while keeping technical model names recognizable.

**A starting map:** sources supply original data, documents structure evidence, and Reality records
support the business position. Commands perform operations, Projections derive answers and Views
present them.

## Product and access

### Reality

The operational and financial model of a company: obligations, stock allocations, movements and
postings. These records support action and explain the current position. Documents provide evidence;
delivery and payment state are derived from the operational records rather than stored as document
status.

### Business Graph

Relationships and the timeline of related business records. For example, follow an order to its
lines, delivery commitments and shipments. It exposes the context Reality holds; it does not promise
complete history from every upstream system. [Explore the model](/concepts/business-reality-guide).

### Business Facts

The product area for inspecting individual records, including sources, documents and operational
records. The name covers more than the specific [Fact](#fact) record type. Use it to inspect the
actual records behind a graph relationship or a calculated result.

### Tools

Business capabilities exposed to people and agents: operations, views and calculated results. Some
tools only read; others prepare or execute changes under their authorization and confirmation rules.
The [interactive command catalog](/tool-usage/) explains available capabilities, inputs and effects.

### Tenant

The isolation boundary for business data, normally the company selected for the request. Every
business query and operation enforces this scope. A record ID from another company does not grant
access to that record. An account and its company access are distinct from the business records
themselves.

### Sandbox and Live Demo

A Sandbox is a company for practice with test data. Live Demo adds synthetic incoming business
activity through the shared background services. New demo orders do not mean an agent has fulfilled
them: source intake and downstream agent work are separate.
[Try a demo company](/getting-started/demo-company).

## Sources and evidence

### SourceRecord

Immutable, lossless accepted input from a source, such as an ERP order payload. Reality preserves
what the source actually sent, including fields that have no typed business meaning yet. Changed
input creates a new version or event instead of overwriting the original.

### Payload

The original content delivered by an external system. It may contain business fields, nested
structures and source-specific metadata. Retaining it losslessly lets you inspect what was received
without making every external field part of the core model.

### Document and DocumentLine

Structured business evidence interpreted from source input, such as an order and its individual
lines. Received amounts and quantities remain the values the source stated. A document does not own
reservation, delivery or payment state: those answers come from linked Reality records.

### Evidence

The structured support for a business statement or action, connecting it to accepted source input.
For example, an order line supports a delivery commitment, and its document points to the original
SourceRecord. Evidence explains why a record exists; it is not another copy of operational state.

### Provenance and traceability

The path from a result to its contributing records, evidence and original source payload. For
example, trace available stock to movements and active reservations, then follow their supporting
links where applicable. An explanation must make this path inspectable rather than only present a
plausible narrative.

### Connector

The transport that brings data from an external system into Reality. It handles source access and
delivery of payloads; it does not invent stock or financial effects merely because a field exists
upstream. Business interpretation belongs to the interpreter.
[Connect ERP and data sources](/development/connectors).

### Interpreter

The component that gives accepted source data business meaning. An order interpreter can create
structured order evidence and supported commitments; an actual shipment requires its own supporting
source and interpretation. Transporting a payload and understanding its business effect are separate
responsibilities. [Source interpretation](/integrations/connector-contract).

### Idempotency

Repeating the same accepted request or source version must not create duplicate business effects.
For example, delivering the same shipment payload twice must not double the stock movement. A
genuinely changed upstream version remains a separate input with its own history.

### Source authority

The agreed responsibility for a business statement or effect: which source supplies the order, the
actual shipment or the payment. Two systems may report the same event; importing both must not
record its effect twice. Received values are retained as stated, while observations such as current
stock are derived from the records held.
[Agree source authority](/integrations/connector-contract#agree-source-authority-and-cutover).

## Operational and financial records

### Fact

An immutable observation explicitly supported by a same-tenant SourceRecord and attached to an
existing Reality subject through a reviewed predicate. It is not an agent guess or a copy of typed
operational state. A fact records what a source supports; a current calculated stock balance is a
derived answer instead.
[Facts and open questions](/concepts/business-reality-guide/06-facts-and-open-questions#facts).

### Predicate

The defined meaning of a Fact: what is being stated about its subject and what evidence supports
that statement. Predicates require reviewed semantics; an arbitrary label from an agent does not
establish a new authoritative business concept. They differ from typed quantities used by stock or
payment services.

### Commitment

An obligation to deliver, receive, pay or collect. A sales line can support an outgoing delivery
commitment; incoming supply supports an incoming one. The remaining work is derived from the
commitment and its linked fulfillment records, rather than a delivery status on the order document.

### Reservation

An allocation of stock or capacity directly to a Commitment. Reserving stock makes it unavailable
for other commitments without physically shipping it. The shortest business relationship is
Reservation → Commitment; the reservation does not need duplicate links to the order and source.

### Movement

A recorded quantity moving between locations or inventory positions, such as a goods receipt or
shipment. Physical stock is derived from movements; an order or reservation alone creates no
physical stock change. Corrections preserve the original movement and create an explicit audit
trail.

### LedgerEntry

A debit or credit posting in balanced financial reality. Related postings explain a financial effect
and support financial-position calculations. A reversal creates explicit reversing postings and
their relationship to the original group instead of editing the original entries.

### Physical, reserved and available stock

Physical stock comes from recorded movements. Reserved stock is allocated to active commitments;
available stock is physical stock minus active reservations. Projected availability also considers
incoming and outgoing commitments. These figures answer different questions; available stock alone
is not permission to ship.

### Opaque ID

A system identity with no business meaning, used to address and link the exact record. An order
number or SKU is useful for human search but is not record identity. Resolve a number to the actual
ID before an operation so similar numbers or records in other companies cannot be confused.

### Shortest true links

Relationships point directly to the record that owns their meaning. A reservation links to its
commitment; the evidence can be reached through that commitment where present. Avoiding duplicate
indirect links prevents competing relationships and keeps explanations consistent.

### Master data: partner, article and location

Business partners identify parties such as customers, suppliers and your own company. Articles
identify what is traded; locations identify where stock is held or moved. Operational records link
to their opaque IDs. Names, SKUs and addresses help people find and understand records but do not
replace their identity.

### Hold

An explicit restriction on an operation, such as a delivery hold on a commitment or business
partner. It prevents the affected shipment even if stock is available. A hold is different from an
Exception: an Exception reports a condition, while placing or releasing a hold is an authorized
business change. [Delivery holds](/agent-playbooks/order-to-cash-fulfilment).

### Payment allocation

The assignment of a received or paid amount to a particular invoice or financial obligation.
Recording money and allocating it answer different questions: what moved, and which open item it
settles. An excess payment can remain unallocated; it must not silently settle an unrelated invoice.
[Receivables and payments](/agent-playbooks/receivables-and-payments).

## Commands, calculations and agents

### Command

A defined application operation with inputs, results and a business purpose. A Command can read,
such as credit exposure, or mutate, such as reserving stock; the name alone does not mean a write.
Its shared service owns the business rule and its declared mutation boundary governs confirmation.
[Develop Commands](/development/commands).

### Application Tool

The shared callable application capability that wraps a service and exposes stable inputs and
results. Web, Chat, MCP, API and CLI reuse this boundary. For example, the reservation tool calls
the reservation service; each interface must not implement its own stock checks.

### Agent Tool

A capability exposed to an agent with a discoverable name and input schema. It translates agent
input to existing application tools or readers. Reading inventory and preparing a change proposal
are different capabilities; an agent interface does not bypass tenant scope, authorization or
confirmation. [Agent interfaces](/development/agent-tools).

### View

A business read surface that presents records or a calculated answer to the user, such as an order
list or warehouse queue. A View can reuse a register or Projection; a new page does not
automatically need a new calculation. It provides filters and a path to the underlying records.
[Explore views](/tool-usage/views).

### Projection

A reusable read model derived from authoritative Reality records, such as physical, reserved and
available inventory. It may be calculated at read time or materialized as a rebuildable cache. It is
not a second source of truth. A View presents an answer; a Projection supplies its derived data.
[Explore projections](/tool-usage/views).

### Register

A read surface over a defined set of records, with filters and deterministic pagination. For
example, a register lets you inspect individual movements instead of only an inventory total.
Listing underlying records and calculating an aggregate are different tasks, even when both appear
in Views.

### Exception

A derived business condition requiring attention, such as an outgoing commitment at risk. This is an
operational warning, not a programming error or a manually closed ticket. It appears while its
defined condition holds and clears when the underlying condition disappears; changing the business
situation uses normal Commands. [Explore exceptions](/tool-usage/exceptions).

### Business Event

A recorded event describing a business change, such as a reservation being created. Events provide
history and can invalidate derived read models. They describe an effect that happened; they are
neither a Command requesting an effect nor a current Exception indicating risk.
[Explore events](/tool-usage/events).

### Catalog

A structured description of available Commands, Views, Projections, Exceptions or Events. Catalogs
document executable vocabulary and power discovery and the interactive reference. An entry does not
create business state or prove an external integration is connected and running.
[Browse the catalog](/tool-usage/).

### Change proposal and confirmation

A proposal prepares an exact operation, its arguments and a server preview for review. Creating it
does not execute the business change. The authorized human checks the intended effect and confirms
separately; afterwards, read the records again to verify the result.
[Prepare your first action](/getting-started/first-action).

### MCP, API and CLI

Different interfaces to shared capabilities. MCP (Model Context Protocol) makes tools available to
connected agents; an API serves programmatic requests; a CLI exposes operations in a terminal. They
translate inputs and responses while business rules remain in shared services.
[Connect an agent](/getting-started/connect-agent).

### Service and adapter

A service owns an application business rule and its tenant-scoped execution. An adapter translates
an interface, such as an HTTP or MCP request, into that shared capability. A new interface reuses
the same rule; it does not create a second implementation of reservation or payment logic.
[Application surfaces](/development/application-surfaces).

### Scheduled job

A task with explicitly configured recurring or queued execution. A prompt describing daily work does
not itself schedule an agent. Background work uses shared scheduling services and handlers that
preserve scope and approval rules; source intake does not authorize downstream mutations.
[Define an operating rhythm](/agent-playbooks/operating-rhythm).

## Analytics vocabulary

### Analytics

The analysis editor and agent capabilities for querying the business graph over existing Reality
records. Queries use declared relationships, measures and shared stock or finance calculations. An
analysis can explain only the data and observation coverage actually available.
[Analytics guide](/analytics/).

### Node and edge

A Node declares what a record represents, such as one order or article. An Edge declares a true
relationship, such as an order containing lines. The analytics graph describes these existing
records and relationships in PostgreSQL; it does not require a separate graph database.

### Grain

The level represented by one result row: one order, one order line, or one article/location pair.
Joining an order to four lines can repeat its amount four times. Declaring grain prevents
interpreting those repeated values as four separate orders and summing them incorrectly.

### Measure

A declared number with a defined business meaning and aggregation rules. For example, received order
value is separated by currency and is not recognized revenue. Quantities preserve their units;
values that cannot safely be combined are not silently added together.

### Coverage

The observation a query can support: current state, activity within a period or a supported dated
snapshot. Current inventory does not establish historical inventory for every past month. Coverage
makes such limits explicit so the answer matches the question and available records.

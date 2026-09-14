# Idea: Attachments on business objects

**Status:** Brainstorming — not approved, not an implementation specification
**Working title:** Tenant-scoped attachments

## Problem

Users need to retain files close to the business object they help explain: for
example a signed PDF on a Document, correspondence on a Party, a product drawing on
an Item, or a photograph on a Movement. Today Reality has immutable `SourceArtifact`
storage for imported source evidence, but no small, shared concept for ordinary
attachments across business objects.

The result should feel simple in the product: open an object, see its files, upload a
file, download it, and understand who added it and why. Underneath, storage, tenant
scope, provenance, and the distinction between source evidence and supporting
material must remain explicit.

## Proposed product concept

An **Attachment** is an immutable file plus tenant-scoped metadata. An
**AttachmentLink** says which business object the attachment is shown on and what
role it has there.

```text
private S3/MinIO object
        ^
        | opaque storage key
    Attachment <---- AttachmentLink ----> allowed business object
```

Cardinality:

```text
allowed business object 1 ---- 0..n AttachmentLink 0..n ---- 1 Attachment
```

Each supported business object may therefore have no attachment, one attachment, or
any number of attachments. The attachment collection is optional and does not add
nullable attachment foreign keys or numbered attachment columns to Document, Party,
Item, or other domain tables.

PostgreSQL holds identity and metadata; private S3-compatible object storage holds
the bytes. The database never stores a public or deployment-specific object URL.
Downloads go through a tenant-scoped service or a short-lived signed URL.

One stored file may be linked to more than one object without copying its bytes. A
link is a contextual association, not ownership and not business identity.

## Initial attachment targets

Start only with objects for which a concrete user story is clear:

1. **Document** — original PDF, signed copy, supplementary document.
2. **Party** — contract, certificate, correspondence, onboarding material.
3. **Item** — drawing, specification, safety sheet, product image.
4. **Commitment** — customer or supplier correspondence relevant to execution.
5. **Movement** — proof of delivery, packing photograph, carrier document.
6. **LedgerEntry or payment evidence** — receipt or remittance advice, if financial
   review proves that the attachment belongs here rather than on the originating
   Document.

Possible later targets, only after a proven use case: Location, Reservation, Lot,
SerialUnit, HandlingUnit, ImportJob, operational exception, or a chat session.

Avoid promising attachments on “everything.” Each allowed target must have a named
workflow, authorization rule, retention expectation, and useful UI location.

### ERP target map

The likely ERP attachment homes and their characteristic uses are:

| Target | Typical attachments | Suggested phase |
|---|---|---|
| Document | Invoice, order, credit note, delivery note, signed copy | 1 |
| Party | Contract, certificate, registration extract, correspondence, onboarding form | 1 |
| Item | Data sheet, drawing, manual, safety sheet, product image | 1 |
| Commitment | Order confirmation, delivery-date agreement, execution correspondence | 2 |
| Movement | Proof of delivery, freight document, damage photograph, packing list | 2 |
| Operational exception | Screenshot, correspondence, or evidence used to explain and resolve an exception | 2 |
| Lot | Batch certificate, analysis report, certificate of origin | 3 |
| SerialUnit | Warranty document, inspection report, repair evidence | 3 |
| HandlingUnit | Shipping label, packing photograph, pallet or container document | 3 |
| Location | Warehouse plan, safety document, site photograph, access instruction | 3 |
| Payment or OpenItem | Remittance advice, bank receipt, reconciliation evidence | 4, after selecting the true financial anchor |

Targets that may become useful but need a more specific story first:

- **Reservation** — an exceptional approval or manual rationale, when review truly
  happens at the reservation rather than its Commitment or an operational exception.
- **ImportJob** — mapping notes or an error report. The imported original remains a
  SourceArtifact and must not be duplicated as an Attachment.
- **Source system or integration** — interface documentation, mapping agreement, or
  acceptance record. Credentials and secrets must never be uploaded as attachments.
- **ChangeProposal** — durable decision material, only if confirmation evidence must
  remain auditable with the proposal.
- **ChatSession** — user-provided conversational context. The product must explicitly
  distinguish temporary chat input, a retained Attachment, and Source ingestion.

### Prefer the true business home

An attachment should have one understandable **primary business home**. Additional
links are allowed when users deliberately need the same file in more than one context,
but the UI should not automatically scatter it across every derived record.

Apply the shortest-true-link rule:

- attach an invoice to its Document, not separately to every derived LedgerEntry;
- attach source evidence through SourceArtifact and SourceRecord, not to every Fact;
- attach general order correspondence to the Commitment, not to its Reservations;
- attach a delivery proof to the Movement, not to a generated timeline entry;
- attach a file to a Document rather than a DocumentLine unless its meaning is truly
  line-specific, such as a customer drawing for one configured item.

Objects that normally should not be direct attachment targets are Fact, DocumentLine,
LedgerEntry, generated timeline entries, and materialized projections. An explicit
workflow may justify an exception, but convenience alone does not. Payment or OpenItem
should be preferred over LedgerEntry when that is the actual review context.

### Suggested rollout

1. **Document, Party, Item** — broad everyday value and clear business ownership.
2. **Commitment, Movement, OperationalException** — execution and explainability.
3. **Lot, SerialUnit, HandlingUnit, Location** — quality, warehouse, and logistics.
4. **Payment/OpenItem and exceptional targets** — only after their precise ownership,
   retention, and permission stories are proven.

## Source evidence versus supporting attachment

This distinction is the central domain decision:

- A file that is ingested to create or substantiate business evidence follows the
  existing `SourceArtifact -> SourceRecord -> Document/DocumentLine -> Reality`
  flow. Attaching it must not create an alternative ingestion route.
- A supporting file uploaded to an existing business object is an Attachment. It
  explains or supplements the object but does not silently create facts, commitments,
  balances, reservations, or other operational truth.
- If a user explicitly promotes an uploaded file to source evidence, that is a
  separate confirmed application action using the existing ingestion service. The
  resulting SourceRecord should be traceable without re-uploading the bytes.
- A SourceArtifact may be displayed as the original source of an object without also
  creating a redundant AttachmentLink.

This prevents an invoice PDF used for ingestion, a Party logo, and an internal note
from all acquiring the same semantics merely because they are files.

## Minimal metadata

Potential typed metadata, subject to proof during specification:

- opaque attachment ID and tenant ID;
- generated opaque storage key;
- original filename, media type, exact byte size, and SHA-256;
- creation timestamp and actor;
- lifecycle state such as available or quarantined;
- optional user-facing title or description;
- on the link: allowed target kind, target ID, and a small role such as `supporting`,
  `signed_copy`, `image`, or `delivery_proof` only where workflows actually use it.

Do not type arbitrary upstream file metadata pre-emptively. Preserve upload metadata
losslessly if it is needed for audit, while promoting fields only when core behavior
repeatedly uses them.

## Domain and security invariants

- Every Attachment and every AttachmentLink is tenant-scoped; both sides of a link
  must belong to the same tenant.
- Object keys are generated by Reality and tenant-prefixed. User filenames never
  become object identity or object keys.
- Content is addressed and may be deduplicated by SHA-256 within one tenant, never
  across tenants.
- The object store is private. Authorization is checked before download or signed-URL
  creation.
- Uploads are streamed, size-limited, content-inspected where required, and never
  passed as base64 through chat proposals.
- File bytes are immutable. Replacing a file creates a new Attachment; history is not
  overwritten.
- Linking or unlinking a file never changes operational truth. Mutating chat actions
  require confirmation and use the same application service as Web and CLI.
- Deleting a link and deleting stored content are different operations. Physical
  deletion requires an explicit retention policy and proof that no links, source
  records, audit requirements, or legal holds still refer to the content.
- Lists, uploads, links, downloads, and removals must enforce tenant scope in repository
  queries, not only in the UI.

## Smallest plausible implementation shape

Do not commit to a schema in this idea, but investigate this minimal split:

1. Generalize the existing artifact-storage service into an internal immutable binary
   object abstraction, while preserving `SourceArtifact` semantics and behavior.
2. Add Attachment metadata for supporting files rather than overloading SourceRecord.
3. Add one shared attachment application service used by API, Web, CLI, chat, and MCP.
4. Support an explicit allowlist of target types. Reject arbitrary table names or
   caller-provided model names.
5. Start with Document and Party, then add another target only when its acceptance
   story and permission behavior are proven.

The technical plan must compare two link designs:

- one compact allowlisted `(target_kind, target_id)` link, with service-level target
  validation and careful orphan handling;
- explicit association tables or foreign keys, which provide database referential
  integrity but cost more schema and code per target.

The chosen design must prove tenant isolation and referential integrity. A universal
polymorphic link is not acceptable merely for convenience.

## First useful slice

Deliver the smallest end-to-end proof:

1. A user opens a Document or Party and sees its attachments.
2. The user uploads one file with an optional title.
3. Reality streams it into private object storage and records tenant-scoped metadata.
4. After confirmation, Reality links it to the selected object.
5. An authorized user downloads it through a mediated, expiring access path.
6. The UI shows filename, type, size, upload time, actor, role, and whether it is a
   supporting attachment or original source evidence.
7. Tests prove cross-tenant access is impossible, identical content is safely handled,
   and linking a file does not alter operational state.

Out of scope for the first slice: previews for every format, OCR, full-text search,
editing file contents, folders, arbitrary external URLs, public sharing, email
ingestion, version comparison, and attaching files to every model.

## Open product questions

1. Are attachments internal to tenant members, or do we already need access for
   customers, suppliers, or auditors?
2. Must files ever be hard-deleted, or is unlinking plus retention/tombstoning enough?
3. Which two initial targets create the most value: Document and Party, or Document
   and Item?
4. Does the first version need antivirus/quarantine handling before a file becomes
   downloadable?
5. Which attachment roles drive real behavior or filtering, rather than merely being
   descriptive labels?
6. Should comments/descriptions be editable while the file and provenance remain
   immutable, and must that edit history be audited?

## Promotion trigger

Move this idea into a numbered Spec Kit feature only after the owner chooses the first
two targets, intended audience, and deletion/retention expectation. The specification
should then define observable workflows and permissions; the plan should decide
whether existing `SourceArtifact` storage code is generalized or reused behind a
separate Attachment concept.

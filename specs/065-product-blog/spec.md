# Feature Specification: Product Blog

**Feature Branch**: `[065-product-blog]`
**Created**: 2026-09-04
**Status**: Approved
**Language**: English
**Input**: "ich überlege gerade ob ich einen Blog erstelle in dem ich regelmäßig was poste — was wäre da das beste Medium für international education für diese neue Art der Kerne" and "kannst du direkt einen Bereich machen wo ich die Ideen für Beiträge sammle" and "ich würde gern sehen wieviel Leute was lesen"

## Context and Intent

### Problem

The documentation explains what Business Reality is. Nothing on any public surface argues why the
document-centred model it replaces breaks down. That argument is the one an ERP reader has to accept
before the reference material means anything to them, and it cannot be made once on a landing page:
it has to be made repeatedly, from different situations, over time.

There is also nowhere to write regularly. Adding an essay as a documentation page puts an argument
into a reference structure that readers navigate by task, where it is neither findable nor datable,
and where it silently claims the authority of a contract.

Two consequences follow from choosing where such writing lives. Writing that defines a category has
to be citable from an origin the project controls, because the definition is the asset. And a reader
who wants to be told about the next article needs a way to ask for that which does not require the
project to hold their identity.

### Scope

- A blog section on the documentation surface, in every documentation language.
- A machine-readable feed per language, and a reader-facing way to subscribe to it.
- A publishing state for unfinished writing that keeps it out of everything a reader sees.
- An editorial workspace in the repository that is never published.
- Optional, self-hosted measurement of what is read.

### Non-Goals

- An email newsletter. It requires holding reader addresses, double opt-in, a processor agreement
  and ongoing deliverability work. The feed is the starting point; the subscribe surface is a single
  component so that a form can replace it later without touching anything else.
- A hosted blogging platform as the canonical home. It would move the definition of the category off
  an origin the project controls.
- Comments, reactions, or any reader-submitted content.
- Measuring how far down an article a reader scrolled. That needs a custom event and is deliberately
  not part of this feature.
- Changing the practical guide, the product guides, or any existing documentation page.

### Existing Contracts

- [Product Documentation](../031-product-documentation/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the blog in your own language (Priority: P1)

As a reader of the documentation, I find the blog from the same navigation as everything else, and
it is written in the language I already selected.

**Why this priority**: A section that only exists in one language is not a publishing surface for an
international audience, and the documentation already promises every page in every language.

**Independent Test**: Open the documentation in each language and follow the blog entry.

**Acceptance Scenarios**:

1. **Given** any documentation language, **When** the navigation is read, **Then** it offers a blog
   entry that opens the blog in that language.
2. **Given** the blog index in any language, **When** it is read, **Then** it lists every published
   article of that language, newest first, with its date and author.
3. **Given** an article in one language, **When** the language is switched, **Then** the
   corresponding article of the other language opens.
4. **Given** the blog index, **When** it is rendered, **Then** it lists no article of another
   language.

### User Story 2 - Be told when something new is published (Priority: P1)

As a reader, I can subscribe to new articles without creating an account or handing over an address.

**Why this priority**: This is the reader's half of publishing regularly. Writing that nobody is
told about is a page, not a blog.

**Independent Test**: Open the blog in each language, follow the stated feed address, and read the
returned document.

**Acceptance Scenarios**:

1. **Given** the blog index or any article, **When** it is read, **Then** it states the feed address
   for that language in full and links to it.
2. **Given** the feed address of a language, **When** it is retrieved, **Then** it returns a valid
   feed whose entries are that language's published articles, newest first, each with an absolute
   address, a title, a description and a publication date.
3. **Given** any blog page, **When** its markup is read, **Then** it declares the feed of every
   language as an alternate representation.
4. **Given** the subscribe surface, **When** it is rendered, **Then** it requires no reader
   identity and loads no third-party code.

### User Story 3 - Finish an article before announcing it (Priority: P2)

As the author, I can commit and preview an unfinished article without it appearing to any reader.

**Why this priority**: Writing that can only be reviewed once it is public forces the choice between
publishing something unfinished and reviewing nothing.

**Independent Test**: Mark an article as a draft, build, and read the index, the feed and the
article's own address.

**Acceptance Scenarios**:

1. **Given** an article marked as a draft, **When** the index is read, **Then** it does not appear.
2. **Given** an article marked as a draft, **When** the feed of its language is retrieved, **Then**
   it does not appear.
3. **Given** an article marked as a draft, **When** its own address is opened, **Then** the article
   renders.
4. **Given** an article whose draft mark has been removed, **When** the surface is rebuilt, **Then**
   it appears in both the index and the feed.

### User Story 4 - Keep a backlog without publishing it (Priority: P2)

As the author, I keep ideas, the pipeline and the editorial rules in the repository, and none of it
reaches a reader.

**Why this priority**: An editorial backlog contains half-formed claims about the product. Publishing
it by accident is worse than not having one.

**Independent Test**: Build the documentation and look for any editorial content in the output.

**Acceptance Scenarios**:

1. **Given** the built documentation, **When** its output is inspected, **Then** no editorial file
   appears at any address.
2. **Given** the editorial workspace, **When** it is read, **Then** it names the pipeline stages, the
   conditions for publishing, and the idea backlog.
3. **Given** a new article is scaffolded, **When** the result is inspected, **Then** every
   documentation language has its own file, each starting as a draft and each carrying that
   language's own text.
4. **Given** an article already exists under a chosen name, **When** scaffolding is attempted again,
   **Then** it fails without altering either file.

### User Story 5 - See what is read, without exposing the reader (Priority: P3)

As the author, I can measure what is read on a surface I operate myself, and measurement never
reaches builds that are not the published one.

**Why this priority**: Writing regularly without knowing what lands is guesswork. Measuring it by
handing readers to a third party contradicts what the surface otherwise claims.

**Independent Test**: Build the documentation with and without the measurement settings and compare
the output.

**Acceptance Scenarios**:

1. **Given** both measurement settings are configured, **When** the surface is built, **Then** its
   pages report to the configured collector.
2. **Given** either measurement setting is absent, **When** the surface is built, **Then** its pages
   contain no measurement code at all.
3. **Given** the measurement stack, **When** it is started, **Then** it runs with its own database
   and is not a dependency of any Reality runtime.
4. **Given** the measurement stack, **When** its configuration is read, **Then** it shares no
   credential, database or volume with a Reality runtime.

### User Story 6 - One written voice across both editions (Priority: P2)

As the author, the way a post reads is written down once, so neither a person nor an agent has to be
told again what the voice is.

**Why this priority**: Voice re-litigated per post is voice that drifts. The German edition in
particular went wrong twice by being translated rather than written, which is a repeatable mistake
and therefore a recordable rule.

**Independent Test**: Read the voice guide, then read either edition of any published article
against it.

**Acceptance Scenarios**:

1. **Given** the editorial workspace, **When** it is read, **Then** exactly one file is the
   authority on voice, length and the German address form.
2. **Given** the agent skill for writing a post, **When** it is read, **Then** it loads that file
   rather than restating its rules.
3. **Given** any German article, **When** it is read, **Then** it addresses the reader informally
   and never formally.
4. **Given** any German article, **When** its typography is read, **Then** quotation marks open and
   close in the German form.
5. **Given** two articles published on the same date, **When** the index and the feed are read,
   **Then** both present them in the same deliberate order.

### Edge Cases

- A language whose blog holds no published article yet, where the index must say so rather than
  render an empty list.
- An article whose date is written without a time, which must be presented as the same day in every
  reader's time zone.
- A published address that must not change: an article is addressed by its name, not by its date.
- A first build after a language is added, where the article inventory of the two languages must
  still match.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The documentation navigation MUST offer a blog entry in every documentation language,
  opening that language's blog.
- **FR-002**: The blog index MUST be derived from the articles themselves and MUST NOT require a
  hand-maintained list.
- **FR-003**: The index MUST list only articles of the language being read, newest first, each with
  its title, description, date and author.
- **FR-004**: Every documentation language MUST have its own feed at a stable address, containing
  that language's published articles with absolute addresses.
- **FR-005**: Every blog page MUST state its language's feed address in full, link to it, and
  declare every language's feed as an alternate representation.
- **FR-006**: The subscribe surface MUST require no reader identity and MUST load no third-party
  code.
- **FR-007**: An article marked as a draft MUST be absent from every index and every feed while
  remaining reachable at its own address.
- **FR-008**: An article's address MUST be derived from its name alone, so that publishing does not
  encode a date into an address that is later shared.
- **FR-009**: Editorial material MUST NOT be reachable at any address of the built surface.
- **FR-010**: Scaffolding an article MUST create one file per documentation language, each starting
  as a draft with that language's own text, and MUST refuse to overwrite an existing article.
- **FR-011**: Reader measurement MUST require both a collector address and a surface identifier;
  with either absent the built surface MUST contain no measurement code.
- **FR-012**: The absolute addresses a feed publishes MUST come from the surface's configured public
  origin rather than a value compiled into the source.

- **FR-013**: Articles sharing a publication date MUST be ordered deterministically and
  identically in the index and in every feed, and the order MUST be the author's choice rather than
  a consequence of the file name.
- **FR-014**: Exactly one file MUST be the authority on how a post reads. Tooling that writes a post
  MUST load it instead of restating its rules.
- **FR-015**: A German article MUST address the reader informally throughout and MUST use German
  quotation marks.

### Domain and Traceability Requirements

- **DR-001**: The blog is a public, tenant-independent surface. It MUST NOT read tenant data, require
  authentication, or call a Reality runtime.
- **DR-002**: The blog MUST add no table, column, endpoint or domain mutation.
- **DR-003**: Both language editions of an article MUST exist, and MUST NOT be identical, so that a
  published language is never silently the other language's text.
- **DR-004**: Reader measurement MUST run as its own deployable stack with its own database and
  volume, and MUST NOT be a dependency of any Reality runtime.
- **DR-005**: The blog MUST NOT restate a normative contract. Where it makes a claim about product
  behaviour it MUST link to the page, catalog or specification that establishes it.

### Key Entities *(when data is involved)*

- **Article**: One dated, authored piece of writing in one language, addressed by its name, either
  published or a draft.
- **Feed**: One language's published articles in a machine-readable form, addressed absolutely.
- **Idea**: One candidate article in the editorial backlog, at one stage of the pipeline. Never
  published.

## Success Criteria *(mandatory)*

- **SC-001**: Each documentation language reaches its blog from the navigation and sees only its own
  articles.
- **SC-002**: Each language's feed retrieves that language's published articles with absolute
  addresses and dates.
- **SC-003**: A draft is absent from every index and feed and present at its own address.
- **SC-004**: The built surface contains no editorial file and, absent the measurement settings, no
  measurement code.
- **SC-005**: Scaffolding produces a complete set of language editions, or fails without writing.
- **SC-006**: Every FR and DR has an acceptance scenario and executable proof.
- **SC-007**: Two articles published on the same date appear in the intended order everywhere.
- **SC-008**: Every German article passes the informal-address and quotation-mark checks.

## Assumptions and Dependencies

- The documentation surface is the right home: it is already public, tenant-independent,
  multilingual, searchable, and served from an origin the project controls. A separate deployable
  boundary for a blog would duplicate all of that.
- A feed is a sufficient subscription mechanism to start with. It reaches technical readers well and
  ERP practitioners poorly; that gap is accepted for now and named in the Non-Goals rather than
  hidden.
- The existing documentation contract already requires every language to mirror the page inventory
  and to differ in content. The blog inherits that, which is what makes DR-003 enforceable without
  new machinery.
- Reader measurement is optional. A deployment that configures neither setting is a valid
  deployment, not a degraded one.
- The publication date of an article is a day, not an instant. Presenting it as a day in a fixed
  reference zone is correct and avoids the same article appearing to be published on two dates.
  Because a day is not an instant, two articles can share one, and the author rather than the file
  system decides which a reader meets first.

## Open Questions

None.

A hosted platform was considered and rejected as the canonical home. It would publish faster, but
the writing exists to define a category, and the definition has to be citable from an origin the
project controls. A hosted platform remains available as a place to republish with the canonical
address attached.

An email newsletter was considered and deferred rather than rejected. It reaches the intended
audience better than a feed does, and it is the expected next step; it is out of scope here because
it introduces reader identity, consent and deliverability, none of which the feed requires.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | Contract asserting a blog navigation entry and route per language |
| FR-002 | US1 scenario 2 | Contract asserting the index derives its list from the articles |
| FR-003 | US1 scenarios 2-4 | Contract asserting per-language listing, ordering and required fields |
| FR-004 | US2 scenario 2 | Feed generated per language and inspected in the built output |
| FR-005 | US2 scenarios 1, 3 | Contract asserting the stated feed address and the alternate declarations |
| FR-006 | US2 scenario 4 | Diff review of the subscribe surface for identity fields and third-party code |
| FR-007 | US3 scenarios 1-4 | Draft excluded from index and feed, present at its own address, in the built output |
| FR-008 | US3 scenario 3 | Article addresses inspected in the built output |
| FR-009 | US4 scenario 1 | Built output inspected for any editorial address |
| FR-010 | US4 scenarios 3-4 | Scaffolding run for a new name and for an existing one |
| FR-011 | US5 scenarios 1-2 | Surface built with and without both settings and the output compared |
| FR-012 | US2 scenario 2 | Feed addresses traced to the configured public origin |
| FR-013 | US6 scenario 5 | Index and feed ordering asserted against two same-date articles |
| FR-014 | US6 scenarios 1-2 | Contract asserting the voice guide exists and that the skill loads it |
| FR-015 | US6 scenarios 3-4 | Contract asserting informal address and balanced German quotation marks |
| DR-001-DR-002 | US1-US2 | Diff review for tenant independence and absence of schema or endpoint change |
| DR-003 | US4 scenario 3 | Existing documentation contract on language inventory and content difference |
| DR-004 | US5 scenarios 3-4 | Contract asserting the measurement stack's isolation from every runtime |
| DR-005 | US1 scenario 2 | Editorial review requiring every product claim to link to its source |
| SC-001-SC-008 | All scenarios | Full required quality gates |

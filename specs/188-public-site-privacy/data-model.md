# Data Model: Public Site Privacy

No business entity, SQL table, Alembic migration or new browser storage is introduced.
The following shapes are build/review inputs, not application records.

## Deployment legal input

`provider-site/legal/deployment.json` identifies deployment and canonical origin, operator
facts, locale content versions, inventory version and approval evidence references.
Operator facts include legal name/form, address, representative, contact and applicable
register/tax details. Applicable-but-missing fields fail release validation; non-applicable
fields require a reviewed reason. Values must be explicit, never inferred from a domain.
Only public facts enter shipped assets; private agreements remain outside the bundle.

## Legal content

`provider-site/legal/content/{en,de,nl,es}.json` contains title, section headings, paragraphs
and explicit links for both documents. Render escaped strings; allow only ordinary safe
link schemes, with no raw HTML, executable URLs, embeds or arbitrary scripts. Require
complete equivalent locale coverage and review/version references. Official names and
identifiers are preserved, not translated by the runtime localization observer.

## Processing inventory and release dossier

Inventory entries contain service/provider, destination, purpose, data categories,
storage name/type/scope when applicable, retention period or criterion, consent
classification/justification, operational owner and review reference. Unknown fields
remain visibly unresolved and block publication. The initial optional list must be empty.

Release dossiers under `docs/privacy/releases/` reference deployment, candidate artifact
digest, legal-content/inventory digests, operator approval, reviewer/date, evidence paths,
blockers, host settings review, pre-release status and post-deploy smoke status. Reviews
bind to content and inventory, not an unversioned true/false flag. Changed inputs invalidate
associated approvals. Workflow: draft → candidate verified → pre-release approved →
deployed verification pending → verified; any failed check → blocked/remediation.
These states report review progress and do not assert legal immunity.

## Presentation language and legacy cleanup

Allowed language values remain en/de/nl/es. Selection is validated URL lang followed by
current-page in-memory selection; authenticated fallback remains the existing profile
language. Defaults are not persisted. Explicit choices replace only lang in the current
URL. No new timestamp, expiry, browser identifier or consent record is necessary.

Legacy cleanup is best effort, idempotent and restricted to:

- `localStorage.removeItem('reality.language')` on each affected origin.
- Expiring `reality_language` with Path=/ on the current host.
- Expiring the same cookie with Domain=runreality.ai only on that domain or its subdomains.

Do not read legacy preference values, enumerate unrelated storage, infer arbitrary parent
domains, clear session data or mutate account profiles. Blocked storage is ignored without
preventing navigation. Cleanup requests remove the old key; they do not establish new
persistent preference authority. Finite retention is therefore zero for new browser
language preferences. Existing server account preference policy is outside this change.

## Conditional consent

No consent record is implemented in the default design. FR-009–FR-012 are conditional.
If a service is approved for retention, amend this design before implementation to model
purpose/provider/version binding, expiry, withdrawal, evidence minimization and multi-page
propagation. Do not silently add a consent database or treat URL language as consent.

## Hosting configuration

No business entities change. Deployment evidence consists of a dedicated S3 bucket and
policy, unversioned 30-day lifecycle, ALB attributes and delivery metadata, explicitly
identified error-log destinations, and effective container logging settings. Keep raw
visitor logs and credentials out of evidence artifacts.

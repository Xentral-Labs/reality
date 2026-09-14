# Research: Separate Public Site and Product Web App

## Decision: Use two browser applications

**Decision**: `provider-site` owns the public landing page; `apps/web` owns authentication,
onboarding, and the operational product.

**Rationale**: The domains, runtime dependencies, availability expectations, and
release purposes are different. Explicit applications match the repository convention
introduced by Spec 021 and avoid host-dependent branches inside one bundle.

**Alternatives considered**:

- One bundle branching on `location.host`: rejected because it couples deployments and
  can expose the wrong surface through proxy or preview configuration.
- Rename product Web to `app`: rejected because `apps/web` already clearly describes
  the browser product and changing it again adds churn without improving deployment ownership.

## Decision: Keep the public site static

**Decision**: Site has no API proxy, auth request, tenant state, or backend dependency.

**Rationale**: Its content and language selection are static. This preserves independent
availability and prevents a second browser adapter from acquiring business behavior.

**Alternatives considered**:

- Proxy account/API routes from site: rejected because it blurs security and ownership.
- Add CMS or server rendering: rejected because no current content workflow proves it.

## Decision: Configure an absolute product origin

**Decision**: Site account actions compose `/login` and `/signup` against
`APP_URL`, translated by the Site build into an internal constant, with a documented local default and production value
`https://app.runreality.ai`.

**Rationale**: Absolute destinations are deterministic in local, preview, and production
deployments and preserve language query parameters.

**Alternatives considered**:

- Hard-code production URLs: rejected because local and review deployments need valid destinations.
- Relative links: rejected because they stay on the public-site origin.

## Decision: Defer a shared TypeScript UI package

**Decision**: Each deployable owns its presentation snapshot, including its logo and
localization helpers, until repeated joint evolution proves a stable shared package.

**Rationale**: A package/workspace/build abstraction would be larger than the two small
presentational reuse points and would couple independent builds immediately.

**Alternatives considered**:

- Add `packages/reality-ui`: deferred until at least several components require coordinated reuse.
- Import Site source from Web: rejected because it destroys independent build ownership.

## Decision: Redirect www at the hosting edge

**Decision**: The canonical-host redirect is a deployment contract, not a React or
Nginx-in-container rule shared by all environments.

**Rationale**: TLS termination and host routing happen before the static container in
typical production. Edge ownership prevents redirect loops and preserves path/query.

**Alternatives considered**:

- Client-side redirect: rejected because it is not canonical HTTP behavior.
- Container host-name redirect: rejected because provider ingress may not forward the original host consistently.

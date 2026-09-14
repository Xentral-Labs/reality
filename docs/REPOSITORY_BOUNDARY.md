# Repository boundary: product versus operations

Reality is published as an open source product. This repository holds everything a person
needs to build, run, install and extend Reality. It does not hold how the maintainers run
their own instances. This page records where each kind of material lives and why.

## The four places

| Where | What it holds | Who can read it |
|---|---|---|
| `Xentral-Labs/reality` (this repository) | The product: application core, apps, installer, Helm chart with generic values, documentation, specifications | Public |
| The maintainers' private operations repository | Provider-operated content and the operations runbook: the `runreality.ai` marketing site, the cluster values file, the Helm prerequisites, privacy release dossiers | Maintainers |
| The maintainers' private GitOps repository | The desired state: the Argo CD Application per cluster, including the image tag | Maintainers |
| Vault | Every actual secret value: database URL, master key, SMTP credentials, provider API keys | Cluster + operators |
| This repository's GitHub **secrets** | The identifiers the deploy workflow needs at runtime: AWS account, region, deploy role ARN, registry name, and the App credentials used to signal a deployment | Repository admins |

Nothing in the third and fourth rows is referenced by name anywhere in this repository.

## Belongs here (public)

- The application core, the apps, the installer and the Helm chart with generic example values.
- The product documentation (`apps/docs`), in every published language, because most of it is
  generated from the code.
- Specifications, plans and decisions under `specs/` and `docs/`. They explain why the product
  is shaped the way it is.
- Workflows that every fork benefits from: quality gates, the installer proof, publishing images
  to a registry the fork can rename, and a deploy workflow that is inert without secrets.

## Belongs in the operations repository

Nothing below is secret. It is operator-specific: it names one AWS account, one cluster, one
Vault, one registry. A fork cannot use it, and publishing it tells the world more about one
installation than about the product.

| What | Why it is not here |
|---|---|
| The `runreality.ai` marketing site | Provider content: pricing, early-access capacity, analytics, imprint and privacy pages. Not part of the product a fork runs. The chart no longer ships a `site` component; `urls.site` remains only as a link target for Product Web and Docs. |
| `helm/reality/values-testing.yaml` | Hostnames, bucket, IRSA role and ESO layout of one cluster |
| `helm/reality/prerequisites/` | IAM policies, Vault policy and ClusterSecretStore for one account |
| The operations sections of the old chart README | Account id, cluster, Vault path, SES identity, ECR lifecycle. The public [chart README](../helm/reality/README.md) keeps the values contract and generic install steps. |
| `docs/privacy/releases/` | Provider deployment dossiers naming real roles and accounts |

Historical specifications and decision records under `specs/` and `docs/` still describe
work on that site. They refer to it by the path prefix `provider-site/`, which is not a
directory in this repository: it stands for the marketing site in the operations
repository. Those records are kept as written because they explain why the product is
shaped the way it is.

## How deployment works across the boundary

The deploy workflow **stays in this repository** and still runs on every push to `main`, so a
commit produces images without waiting on anything else. What changed is that it carries no
operator values and does not know where it deploys to:

1. `.github/workflows/deploy.yml` builds and pushes the runtime images. The AWS account,
   region, role ARN and registry all come from repository **secrets**, which GitHub masks in
   logs and never exposes to pull requests from forks. Authentication is OIDC — there are no
   long-lived keys.
2. The workflow then sends a `repository_dispatch` event carrying only the tag, the
   environment and the commit, using a GitHub App token minted per run and scoped to one
   repository. The event type is qualified by environment —
   `reality-image-published-<environment>`, from the `DEPLOY_ENVIRONMENT` variable — so one
   receiving repository can route each environment to its own Argo CD Application. This
   repository never learns which Application that is.
3. The receiving repository owns the cluster, the GitOps layout and the rollout. Which
   repository that is, and which file it patches, is itself a secret here.

A fork, or any clone without those secrets, skips the whole workflow cleanly rather than
failing: the `meta` job checks for `AWS_DEPLOY_ROLE_ARN` and reports a notice when it is absent.

### Secrets this repository expects

| Secret | Used for |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | OIDC role to assume; also the on/off switch for the whole workflow |
| `AWS_ACCOUNT_ID`, `AWS_REGION`, `ECR_REPOSITORY` | Registry coordinates |
| `DEPLOY_APP_ID`, `DEPLOY_APP_PRIVATE_KEY` | GitHub App that mints the dispatch token |
| `DEPLOY_TARGET_REPO` | Repository that receives the deployment signal |

`vars.APP_URL`, `vars.SITE_URL` and `vars.DOCS_URL` are repository *variables*, not secrets:
they are public hostnames baked into the Docs image at build time. `vars.DEPLOY_ENVIRONMENT`
names the deployment this branch feeds (for example `testing`); it is required whenever
`AWS_DEPLOY_ROLE_ARN` is set, and the build fails early with a clear message if it is missing
or is not a plain lowercase slug.

## Rules once the repository is public

- Never commit an operator value that identifies one installation when an example value would
  do. Account ids, key ids, hosted-zone ids, project ids and internal hostnames belong in the
  operations repository even when they are not secrets.
- Secret scanning with push protection stays enabled. A flagged commit is fixed by rotating the
  credential, not by rewriting history.
- Security reports follow [SECURITY.md](../SECURITY.md); contribution rules follow
  [CONTRIBUTING.md](../CONTRIBUTING.md).

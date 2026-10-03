# Kubernetes with Helm

The repository ships a Helm chart in `helm/reality` for clusters that already provide ingress,
secrets management and PostgreSQL. It deploys the API, Web App, MCP, scheduler, worker and the
migration Job from the same images the other options use.

## What the chart assumes

- A managed PostgreSQL reachable from the cluster; `REALITY_DATABASE_URL` arrives as a Secret.
- An S3 bucket for source binaries with an IAM policy as in `helm/reality/prerequisites`.
- An ingress controller with TLS; the App is one host that serves the SPA and `/api/`, MCP is its
  own host at the origin root.
- `REALITY_MASTER_KEY`, the platform admin credentials and any email or Copilot secrets as Secrets
  (the chart's README shows the External Secrets layout the maintainers use).

## Images

The chart's default image repository is the maintainers' private testing registry. Point it at the
public images and pick a release:

```yaml
image:
  repository: ghcr.io/xentral-labs
  tag: "0.1.0"
```

Check the chart's `values.yaml` for how component names are composed into image references; the
published images are named `reality-api`, `reality-web`, `reality-mcp`, `reality-scheduler` and
`reality-worker`.

## Install

```bash
helm upgrade --install reality ./helm/reality -n reality --create-namespace -f my-values.yaml
```

Run the migration Job before rolling the API, as the chart does through its hooks, and read the
chart README for the ingress, HPA and PodDisruptionBudget settings. The chart is maintained for the
team's testing cluster first; treat other clusters as supported through the values you set, and
report gaps.

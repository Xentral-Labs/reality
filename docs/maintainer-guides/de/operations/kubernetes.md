# Kubernetes mit Helm

Das Repository liefert in `helm/reality` ein Helm-Chart für Cluster, die Ingress, Secret-Verwaltung
und PostgreSQL bereits mitbringen. Es rollt API, Web-App, MCP, Scheduler, Worker und den
Migrations-Job aus denselben Images aus wie die anderen Optionen.

## Was das Chart voraussetzt

- Ein verwaltetes PostgreSQL, das aus dem Cluster erreichbar ist; `REALITY_DATABASE_URL` kommt als
  Secret.
- Einen S3-Bucket für Quelldateien mit einer IAM-Policy wie in `helm/reality/prerequisites`.
- Einen Ingress-Controller mit TLS; die App ist ein Host, der SPA und `/api/` bedient, MCP ist ein
  eigener Host auf dem Origin-Root.
- `REALITY_MASTER_KEY`, die Plattform-Admin-Zugangsdaten und etwaige E-Mail- oder
  Copilot-Geheimnisse als Secrets (die README des Charts zeigt das External-Secrets-Layout der
  Maintainer).

## Images

Das Standard-Image-Repository des Charts ist die private Test-Registry der Maintainer. Zeige auf die
öffentlichen Images und wähle ein Release:

```yaml
image:
  repository: ghcr.io/xentral-labs
  tag: "0.1.0"
```

Prüfe in der `values.yaml` des Charts, wie Komponentennamen zu Image-Referenzen zusammengesetzt
werden; die veröffentlichten Images heißen `reality-api`, `reality-web`, `reality-mcp`,
`reality-scheduler` und `reality-worker`.

## Installieren

```bash
helm upgrade --install reality ./helm/reality -n reality --create-namespace -f my-values.yaml
```

Führe den Migrations-Job vor dem Rollout der API aus, wie das Chart es über seine Hooks tut, und
lies die Chart-README zu Ingress-, HPA- und PodDisruptionBudget-Einstellungen. Das Chart wird zuerst
für den Test-Cluster des Teams gepflegt; andere Cluster gelten über die gesetzten Values als
unterstützt. Melde Lücken.

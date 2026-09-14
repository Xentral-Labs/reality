# Install options

A Reality installation has two responsibilities:

```text
People and agents
       |
       v
  Reality App
       |
       v
   PostgreSQL
```

The **Reality App** provides the product, application API, business services, migrations and
required background work. **PostgreSQL** is the only supported business database. The Docker
packaging runs these responsibilities in several cooperating containers, but operators install and
manage one application rather than a collection of public sites.

Self-hosted Reality is the complete product: the same images as the cloud, MIT licensed, no feature
gating, no licence key. Choose the way to run it that fits your situation.

| Option                               | Choose this when                                                                                                       | You need                                   |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| [One-line setup](./installation)     | You want Reality running in minutes on a laptop, a VPS or a home server, with upgrades and backups as single commands. | Docker with the Compose v2 plugin, curl    |
| [Docker Compose](./docker-compose)   | You need every variable explicit or want to fold Reality into an existing Compose project.                             | Docker Compose v2 and a hand-filled `.env` |
| [Kubernetes with Helm](./kubernetes) | You already run a cluster with ingress, secrets management and managed PostgreSQL.                                     | Helm 3, a Kubernetes cluster, an S3 bucket |
| [Railway](./railway)                 | You want a short-lived hosted demo without your own server.                                                            | A Railway account and the Railway CLI      |

Every option runs the same published images from `ghcr.io/xentral-labs`. Migrations run before the
App accepts traffic, PostgreSQL is never exposed publicly, and the encryption key for stored
credentials lives in your configuration, never in the database.

The Reality marketing site and this documentation are operated by the product provider. They are not
part of a customer installation. A separately offered managed infrastructure will have its own
contract when it becomes available.

After installing, [Operate with Docker](./deployment) covers upgrades, backups, health and the
security checklist. Runtime values are listed in the
[Environment reference](/reference/environment).

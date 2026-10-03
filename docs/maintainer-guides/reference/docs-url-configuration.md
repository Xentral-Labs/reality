# Configure Links from Docs

The links in the Docs header are deployment configuration, not hard-coded product decisions.

| Visible destination             | Build variable | Production example           |
| ------------------------------- | -------------- | ---------------------------- |
| **Commercial offering**         | `SITE_URL`     | `https://runreality.ai`      |
| **Open Reality**                | `APP_URL`      | `https://app.runreality.ai`  |
| Docs itself and generated feeds | `DOCS_URL`     | `https://docs.runreality.ai` |

Trailing slashes are removed before links are generated. When a value is absent, the production
examples above are the image defaults.

## Docker Compose

Set the origins in the environment used by Docker Compose and rebuild Docs:

```bash
APP_URL=https://app.example.com \
SITE_URL=https://www.example.com \
DOCS_URL=https://docs.example.com \
docker compose build docs

docker compose up -d docs
```

The `docs` service passes all three values to `apps/docs/Dockerfile` as build arguments.

## Railway

Add `APP_URL`, `SITE_URL`, and `DOCS_URL` to the **Docs service variables**. Railway makes declared
service variables available during the Docker build, and the Docs Dockerfile declares all three as
`ARG` in its build stage.

VitePress produces static HTML and JavaScript. The configured origins are therefore embedded by
`npm run build`. After changing one of them, create a new deployment with a new image build. A
container restart alone continues to serve the previously generated links.

Use exact public HTTPS origins without a path:

```text
APP_URL=https://app.example.com
SITE_URL=https://www.example.com
DOCS_URL=https://docs.example.com
```

These values are public browser destinations, not secrets.

## Verify the deployed result

After deployment:

1. Open Docs in a private browser window.
2. Follow **Commercial offering** and confirm it opens `SITE_URL`.
3. Follow **Open Reality** and confirm it opens `APP_URL`.
4. Open the generated feed URL under `DOCS_URL`.
5. If an old link remains, confirm that Railway performed a new build and then rule out stale
   browser or CDN caching.

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const docsRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(docsRoot, "../..");
const readRepo = (relativePath) => fs.readFileSync(path.join(repoRoot, relativePath), "utf8");

test("Product discovery uses the configured app origin in both Docs editions", () => {
  const config = readRepo("apps/docs/.vitepress/config.mts");
  assert.match(config, /productUrl: `\$\{appUrl\}\/app`/);
  assert.match(config, /__APP_URL__/);
  for (const locale of ["", "de/"]) {
    assert.match(readRepo(`apps/docs/content/${locale}index.md`), /link: __APP_URL__/);
    for (const page of [
      "getting-started/index.md",
      "concepts/business-reality-guide/02-orders-stock-and-deliveries.md",
    ])
      assert.match(readRepo(`apps/docs/content/${locale}${page}`), /<ProductLink>/);
  }
});

test("Docs has an independent container and health route", () => {
  const dockerfile = fs.readFileSync(path.join(docsRoot, "Dockerfile"), "utf8");
  const nginx = fs.readFileSync(path.join(docsRoot, "nginx.conf"), "utf8");
  assert.match(dockerfile, /FROM node:22-alpine AS build/u);
  assert.match(dockerfile, /FROM nginx:1\.27-alpine/u);
  assert.match(nginx, /location = \/healthz/u);
  assert.match(nginx, /try_files \$uri\.html \$uri \$uri\/ \/404\.html/u);
});

test("Compose runs Docs without business-service dependencies", () => {
  const compose = readRepo("compose.yml");
  const dev = readRepo("compose.dev.yml");
  const docsBlock =
    compose.match(/\n  docs:\n([\s\S]*?)(?=\n  [a-z][\w-]*:\n|\nvolumes:)/u)?.[1] || "";
  assert.match(docsBlock, /apps\/docs\/Dockerfile/u);
  assert.match(docsBlock, /DOCS_PORT:-8083/u);
  assert.doesNotMatch(docsBlock, /depends_on/u);
  assert.match(dev, /\n  docs:\n/u);
  assert.match(dev, /docs_node_modules/u);
});

test("DOCS_URL is additive and existing surface URL names remain intact", () => {
  const files = [
    "compose.yml",
    "README.md",
    "docs/WEB_SPEC.md",
    "apps/web/Dockerfile",
    "apps/web/vite.config.ts",
  ]
    .map(readRepo)
    .join("\n");
  assert.match(files, /DOCS_URL/u);
  for (const variable of ["SITE_URL", "APP_URL", "API_URL", "MCP_URL"]) {
    assert.match(files, new RegExp(variable), `Existing variable ${variable} disappeared`);
  }
  assert.doesNotMatch(files, /DOCS_PUBLIC_URL|PRODUCT_URL|MARKETING_URL/u);
});

test("Docs builds every public surface link from APP_URL and SITE_URL", () => {
  const dockerfile = fs.readFileSync(path.join(docsRoot, "Dockerfile"), "utf8");
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  const home = fs.readFileSync(path.join(docsRoot, "content", "index.md"), "utf8");

  assert.match(dockerfile, /ARG APP_URL=https:\/\/app\.runreality\.ai/u);
  assert.match(dockerfile, /ARG SITE_URL=https:\/\/runreality\.ai/u);
  assert.match(dockerfile, /ENV APP_URL=\$\{APP_URL\}/u);
  assert.match(dockerfile, /SITE_URL=\$\{SITE_URL\}/u);
  assert.match(config, /transformPageData/u);
  assert.match(config, /action\.link === "__APP_URL__"/u);
  assert.match(home, /link: __APP_URL__/u);
  assert.doesNotMatch(home, /https:\/\/app\.runreality\.ai/u);
});

test("deployment guidance explains configurable Docs navigation URLs", () => {
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  const railway = readRepo("docs/RAILWAY_DEMO.md");
  assert.match(config, /labels\.docsUrls.*\/reference\/docs-url-configuration/u);

  for (const locale of ["", "de/"]) {
    const guide = fs.readFileSync(
      path.join(docsRoot, "content", locale, "reference", "docs-url-configuration.md"),
      "utf8",
    );
    for (const variable of ["APP_URL", "SITE_URL", "DOCS_URL"]) {
      assert.match(guide, new RegExp(variable), `Missing ${variable} in ${locale || "English"}`);
    }
    assert.match(guide, /build|Build/u);
    assert.match(guide, /restart|Neustart/u);
    assert.match(guide, /Railway/u);
  }

  assert.match(railway, /set `APP_URL`, `SITE_URL`, and `DOCS_URL` on the\s+Docs service/u);
  assert.match(railway, /require a new deployment, not\s+only a container restart/u);
});

test("repository quality gates own the Docs surface", () => {
  assert.match(readRepo("Makefile"), /docs-build:/u);
  const quality = readRepo(".github/workflows/quality.yml");
  assert.match(quality, /docs-quality:/u);
  assert.match(quality, /apps\/docs\/package-lock\.json/u);
});

test("Docs serves feeds from a configurable public origin", () => {
  const dockerfile = fs.readFileSync(path.join(docsRoot, "Dockerfile"), "utf8");
  const nginx = fs.readFileSync(path.join(docsRoot, "nginx.conf"), "utf8");
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  assert.match(dockerfile, /ARG DOCS_URL=https:\/\/docs\.runreality\.ai/u);
  assert.match(dockerfile, /DOCS_URL=\$\{DOCS_URL\}/u);
  assert.match(
    config,
    /normalizedUrl\(process\.env\.DOCS_URL, "https:\/\/docs\.runreality\.ai"\)/u,
  );
  assert.match(nginx, /location ~ \\\.rss\$/u);
  assert.match(nginx, /default_type application\/rss\+xml/u);
});

test("self-hosted analytics is a separate optional stack, never a runtime dependency", () => {
  const dockerfile = fs.readFileSync(path.join(docsRoot, "Dockerfile"), "utf8");
  const analytics = readRepo("compose.analytics.yml");
  const compose = readRepo("compose.yml");
  const makefile = readRepo("Makefile");
  const readme = readRepo("README.md");

  assert.match(dockerfile, /ARG ANALYTICS_SCRIPT_URL=/u);
  assert.match(dockerfile, /ARG ANALYTICS_WEBSITE_ID=/u);
  assert.match(analytics, /image: ghcr\.io\/umami-software\/umami:postgresql-v\d+\.\d+/u);
  assert.match(analytics, /DISABLE_TELEMETRY: "1"/u);
  assert.match(analytics, /UMAMI_APP_SECRET:\?/u);
  assert.match(analytics, /UMAMI_DB_PASSWORD:\?/u);
  assert.doesNotMatch(analytics, /REALITY_|postgres_data/u);
  assert.doesNotMatch(analytics, /^ {2}db:$/mu);
  assert.doesNotMatch(compose, /umami/iu);
  assert.match(makefile, /^analytics:$/mu);
  assert.match(makefile, /^analytics-down:$/mu);
  assert.match(readme, /ANALYTICS_SCRIPT_URL/u);
  assert.match(readme, /ANALYTICS_WEBSITE_ID/u);
});

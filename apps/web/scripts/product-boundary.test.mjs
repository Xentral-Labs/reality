import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
const webRoot = path.resolve(import.meta.dirname, "..");
test("only the unified browser presentation ships", () => {
  for (const name of ["legacy", "playground", "LandingPage.tsx", "styles.css", "chat.css"])
    assert.equal(fs.existsSync(path.join(webRoot, "src", name)), false, name);
  const app = fs.readFileSync(path.join(webRoot, "src/App.tsx"), "utf8");
  assert.match(app, /<AuthGate>/);
  assert.match(app, /<UnifiedApp/);
  assert.doesNotMatch(app, /VITE_UNIFIED_APP|LegacyProductApp|PracticeEntry/);
});
test("product container keeps the API private and runtime configurable", () => {
  const nginx = fs.readFileSync(path.join(webRoot, "default.conf.template"), "utf8");
  const dockerfile = fs.readFileSync(path.join(webRoot, "Dockerfile"), "utf8");

  assert.match(nginx, /set \$api_upstream \$\{API_UPSTREAM\};/u);
  assert.match(nginx, /proxy_pass http:\/\/\$api_upstream;/u);
  assert.match(dockerfile, /API_UPSTREAM=api:8000/u);
  assert.match(dockerfile, /NGINX_ENVSUBST_FILTER=/u);
  assert.match(dockerfile, /default\.conf\.template/u);
  assert.doesNotMatch(dockerfile, /api\.railway\.internal/u);
});

test("product proxy states its own API timeouts instead of inheriting them", () => {
  // Feature 199: an implicit default is not a decision. Company setup no longer seeds
  // a profile inside its request, so no API request needs more than this.
  const nginx = fs.readFileSync(path.join(webRoot, "default.conf.template"), "utf8");

  assert.match(nginx, /proxy_read_timeout \d+s;/u);
  assert.match(nginx, /proxy_send_timeout \d+s;/u);
  assert.match(nginx, /proxy_connect_timeout \d+s;/u);
});

test("product proxy re-resolves the private API after an API-only redeploy", () => {
  const nginx = fs.readFileSync(path.join(webRoot, "default.conf.template"), "utf8");
  const dockerfile = fs.readFileSync(path.join(webRoot, "Dockerfile"), "utf8");

  assert.match(nginx, /resolver \$\{NGINX_LOCAL_RESOLVERS\} valid=10s ipv6=on;/u);
  assert.match(nginx, /set \$api_upstream \$\{API_UPSTREAM\};/u);
  assert.match(nginx, /proxy_pass http:\/\/\$api_upstream;/u);
  assert.doesNotMatch(nginx, /proxy_pass http:\/\/\$\{API_UPSTREAM\}/u);
  assert.match(dockerfile, /NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1/u);
  assert.match(dockerfile, /API_UPSTREAM\|NGINX_LOCAL_RESOLVERS/u);
});

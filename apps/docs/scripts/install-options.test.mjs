// The installation docs cannot drift from the shipped installer (spec 187 FR-017, FR-018, SC-005).
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const docsRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(docsRoot, "..", "..");
const readRepo = (relative) => fs.readFileSync(path.join(repoRoot, relative), "utf8");
const readDocs = (relative) => fs.readFileSync(path.join(docsRoot, "content", relative), "utf8");

const installer = readRepo("installer/install.sh");
const installerReadme = readRepo("installer/README.md");
const compose = readRepo("installer/compose.yml");
const envExample = readRepo("installer/.env.example");

const ONE_LINE = "curl -fsSL https://get.runreality.ai | sh";
const COMMANDS = ["status", "logs", "stop", "start", "upgrade", "backup", "restore"];
const OPTION_PAGES = ["installation", "docker-compose", "kubernetes", "railway"];
const locales = ["", "de/"];

test("the installer README and the script agree on the one-line command and the commands", () => {
  assert.match(installer, /curl -fsSL https:\/\/get\.runreality\.ai \| sh/u);
  assert.match(installerReadme, new RegExp(ONE_LINE.replace(/[|.]/gu, "\\$&"), "u"));
  for (const command of COMMANDS) {
    assert.match(installerReadme, new RegExp(`\\./reality\\.sh ${command}`, "u"), command);
    assert.match(installer, new RegExp(`\\b${command}\\)`, "u"), `install.sh handles ${command}`);
  }
});

test("the install options index lists every option in both languages", () => {
  for (const locale of locales) {
    const index = readDocs(`${locale}operations/index.md`);
    for (const page of OPTION_PAGES) {
      assert.match(index, new RegExp(`\\]\\(\\./${page}\\)`, "u"), `${locale}index links ${page}`);
      assert.ok(
        fs.existsSync(path.join(docsRoot, "content", locale, "operations", `${page}.md`)),
        page,
      );
    }
  }
});

test("the one-line setup page carries the exact command, flags and control commands", () => {
  const flags = [...installer.matchAll(/^ {2}(--[a-z-]+)/gmu)].map((m) => m[1]);
  assert.ok(flags.includes("--domain") && flags.includes("--email"), "usage text lists the flags");
  for (const locale of locales) {
    const page = readDocs(`${locale}operations/installation.md`);
    assert.match(
      page,
      new RegExp(ONE_LINE.replace(/[|.]/gu, "\\$&"), "u"),
      `${locale}one-line command`,
    );
    for (const command of COMMANDS) {
      assert.match(page, new RegExp(`reality\\.sh ${command}`, "u"), `${locale}${command}`);
    }
    for (const flag of flags) {
      assert.match(page, new RegExp(`\`${flag}`, "u"), `${locale}${flag}`);
    }
    assert.match(page, /REALITY_MASTER_KEY/u);
  }
});

test("the Docker Compose page names the shipped files, the published images and the modes", () => {
  const images = [...compose.matchAll(/reality-([a-z]+):\$\{REALITY_VERSION\}/gu)].map((m) => m[1]);
  assert.deepEqual([...new Set(images)].sort(), ["api", "mcp", "scheduler", "web", "worker"]);
  for (const locale of locales) {
    const page = readDocs(`${locale}operations/docker-compose.md`);
    for (const file of [
      "compose.yml",
      "compose.direct.yml",
      "compose.proxy.yml",
      "compose.s3.yml",
      "Caddyfile",
      "env.example",
    ]) {
      assert.match(page, new RegExp(file.replace(/\./gu, "\\."), "u"), `${locale}${file}`);
    }
    assert.match(page, /ghcr\.io\/xentral-labs\/reality-api/u);
    assert.match(page, /COMPOSE_FILE=compose\.yml:compose\.direct\.yml/u);
    assert.match(page, /COMPOSE_FILE=compose\.yml:compose\.proxy\.yml/u);
    assert.match(page, /compose\.s3\.yml/u);
  }
});

test("the environment reference documents every installer variable that the example declares", () => {
  const declared = envExample
    .split("\n")
    .filter((line) => line && !line.startsWith("#"))
    .map((line) => line.split("=")[0]);
  const documented = new Set([
    "REALITY_VERSION",
    "REALITY_IMAGE_REGISTRY",
    "COMPOSE_PROJECT_NAME",
    "COMPOSE_FILE",
    "REALITY_BIND",
    "REALITY_PORT",
    "REALITY_MCP_PORT",
    "REALITY_DOMAIN",
    "APP_URL",
    "MCP_URL",
    "REALITY_COOKIE_SECURE",
    "REALITY_MCP_ENV",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "REALITY_MASTER_KEY",
    "REALITY_PLATFORM_ADMIN_EMAIL",
    "REALITY_PLATFORM_ADMIN_PASSWORD",
    "REALITY_AUTO_APPROVE_LIMIT",
    "REALITY_ARTIFACT_DIR",
    "REALITY_ENV",
    "REALITY_COMMIT",
  ]);
  for (const locale of locales) {
    const page = readDocs(`${locale}reference/environment.md`);
    for (const variable of declared) {
      if (!documented.has(variable)) continue; // optional email, Copilot and MinIO values are grouped
      assert.match(page, new RegExp(`\`${variable}`, "u"), `${locale}${variable}`);
    }
    assert.match(page, /REALITY_EMAIL_PROVIDER/u);
    assert.match(page, /MINIO_ROOT_USER/u);
    assert.match(page, /ANTHROPIC_API_KEY/u);
  }
});

test("the sidebar exposes the install options in every docs locale", () => {
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  for (const label of [
    "installOptions",
    "oneLineSetup",
    "dockerCompose",
    "kubernetes",
    "railway",
  ]) {
    assert.equal(
      (config.match(new RegExp(`\\b${label}:`, "gu")) || []).length,
      3,
      `${label} typed + en + de`,
    );
  }
  assert.match(config, /\/operations\/docker-compose/u);
  assert.match(config, /\/operations\/kubernetes/u);
  assert.match(config, /\/operations\/railway/u);
});

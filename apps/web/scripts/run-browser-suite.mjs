// Runs the fixture-based browser scripts listed in browser-suite.json against one Vite dev
// server, one after another, and reports every result before failing.
//
//   PLAYWRIGHT_MODULE=/path/to/node_modules/playwright/index.mjs node scripts/run-browser-suite.mjs
//
// Optional: BROWSER_SUITE_SHARD=1/7 selects one duration-balanced shard. BROWSER_SUITE_PORT
// (5177 by default; several scripts still navigate to 5177 literally) and
// BROWSER_SUITE_TIMEOUT (seconds per script, 300) can be overridden.
import { spawn } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { distributeByDuration, parseShard } from "./browser-suite-sharding.mjs";

const scripts = fileURLToPath(new URL(".", import.meta.url));
const web = fileURLToPath(new URL("..", import.meta.url));
const port = Number(process.env.BROWSER_SUITE_PORT || 5177);
const timeout = Number(process.env.BROWSER_SUITE_TIMEOUT || 300) * 1000;
const base = `http://127.0.0.1:${port}`;
if (!process.env.PLAYWRIGHT_MODULE) throw new Error("Set PLAYWRIGHT_MODULE.");

const suite = JSON.parse(readFileSync(new URL("./browser-suite.json", import.meta.url), "utf8"));
const { index, count } = parseShard(process.env.BROWSER_SUITE_SHARD);
const shards = distributeByDuration(suite.scripts, suite.estimated_seconds, count);
const selected = shards[index - 1].scripts;
console.log(
  `Selected ${selected.length} scripts for shard ${index}/${count} ` +
    `(${shards[index - 1].seconds}s estimated)`,
);

const vite = spawn("npx", ["vite", "--port", String(port), "--strictPort", "--host", "127.0.0.1"], {
  cwd: web,
  stdio: ["ignore", "pipe", "pipe"],
  detached: true,
});
let viteOutput = "";
vite.stdout.on("data", (chunk) => (viteOutput += chunk));
vite.stderr.on("data", (chunk) => (viteOutput += chunk));
const stopVite = () => {
  try {
    process.kill(-vite.pid, "SIGTERM");
  } catch {
    // Already gone.
  }
};

const ready = async () => {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${base}/app`);
      if (response.ok) return;
    } catch {
      // Not listening yet.
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`Vite did not start on ${base}:\n${viteOutput}`);
};

const run = (script) =>
  new Promise((resolve) => {
    const started = Date.now();
    let output = "";
    const child = spawn(process.execPath, [`${scripts}${script}`], {
      cwd: web,
      env: {
        ...process.env,
        UNIFIED_BASE_URL: base,
        UNIFIED_APP_URL: base,
        BASE_URL: base,
      },
      stdio: ["ignore", "pipe", "pipe"],
    });
    child.stdout.on("data", (chunk) => (output += chunk));
    child.stderr.on("data", (chunk) => (output += chunk));
    const timer = setTimeout(() => child.kill("SIGKILL"), timeout);
    child.on("close", (code) => {
      clearTimeout(timer);
      resolve({ script, code, seconds: Math.round((Date.now() - started) / 1000), output });
    });
  });

const results = [];
try {
  await ready();
  // The first request compiles the app; warm it so the first script's timeouts are fair.
  await fetch(`${base}/app/finance`).catch(() => {});
  for (const script of selected) {
    const result = await run(script);
    results.push(result);
    console.log(`${result.code === 0 ? "PASS" : "FAIL"} ${script} (${result.seconds}s)`);
    if (result.code !== 0) console.log(result.output.split("\n").slice(-40).join("\n"));
  }
} finally {
  stopVite();
}
const failed = results.filter((result) => result.code !== 0);
const total = results.reduce((sum, result) => sum + result.seconds, 0);
if (process.env.BROWSER_SUITE_RESULTS) {
  writeFileSync(
    process.env.BROWSER_SUITE_RESULTS,
    `${JSON.stringify(
      Object.fromEntries(results.map(({ script, seconds }) => [script, seconds])),
      null,
      2,
    )}\n`,
  );
}
console.log(
  `\n${results.length - failed.length}/${results.length} browser scripts passed in ${total}s` +
    (count > 1 ? ` (shard ${index}/${count})` : ""),
);
if (failed.length) {
  console.log(`Failed: ${failed.map((result) => result.script).join(", ")}`);
  process.exit(1);
}

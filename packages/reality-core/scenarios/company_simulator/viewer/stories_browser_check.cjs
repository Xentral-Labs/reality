// Run against an already started loopback viewer and a retained complete-v2 month.
const base = process.env.SIMULATOR_VIEWER_URL || "http://127.0.0.1:8765";
const run =
  process.env.SIMULATOR_STORY_RUN || "correspondence_acceptance/prompt";
const { chromium } = require(
  process.env.PLAYWRIGHT_MODULE || "playwright-core",
);
(async () => {
  const b = await chromium.launch({
    executablePath: process.env.PLAYWRIGHT_EXECUTABLE || "/usr/bin/chromium",
    args: ["--no-sandbox"],
  });
  const p = await b.newPage();
  const errors = [],
    methods = [];
  p.on("pageerror", (e) => errors.push(e.message));
  p.on("request", (r) => methods.push(r.method()));
  const data = await (await fetch(`${base}/api/stories/${run}`)).json();
  let latest = 8;
  await p.route("**/api/runs", (r) =>
    r.fulfill({ json: { runs: [{ key: "demo" }] } }),
  );
  await p.route("**/api/stories/demo", (r) =>
    r.fulfill({
      json: {
        ...data,
        report: {},
        checkpoints: data.checkpoints.filter((c) => c.day <= latest),
      },
    }),
  );
  await p.goto(`${base}/stories`);
  await p.locator("#day").filter({ hasText: "Day 8" }).waitFor();
  if (!(await p.locator("#play").isHidden()))
    throw Error("Play shown in watch");
  latest = 9;
  await p
    .locator("#day")
    .filter({ hasText: "Day 9" })
    .waitFor({ timeout: 8000 });
  await p.locator("#replay").click();
  await p.locator("#scrub").fill("3");
  latest = 10;
  await p.waitForTimeout(5500);
  if (!(await p.locator("#day").textContent()).includes("Day 3 /"))
    throw Error("Replay day moved during poll");
  await p.locator('[data-order="S01"]').first().click();
  await p.locator("#mailtab").click();
  await p.locator("#close").click();
  await p.locator("#watch").click();
  await p.locator('[data-order="S01"]').first().click();
  latest = 11;
  await p.waitForTimeout(5500);
  if (!(await p.locator("#day").textContent()).includes("Day 11 /"))
    throw Error("Watch not latest");
  if (!(await p.locator("#drawer").isVisible())) throw Error("Story lost");
  await p.setViewportSize({ width: 390, height: 844 });
  if (await p.evaluate(() => document.documentElement.scrollWidth > innerWidth))
    throw Error("Mobile overflow");
  if (errors.length) throw Error(errors.join("\n"));
  if (methods.some((x) => x !== "GET")) throw Error("Mutation request");
  await p.screenshot({
    path:
      process.env.SIMULATOR_STORY_SCREENSHOT ||
      "/tmp/simulator-stories-live.png",
  });
  console.log(
    "PASS growing checkpoint watch, replay isolation, story preservation, mobile, GET-only, CSP/JS",
  );
  await b.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});

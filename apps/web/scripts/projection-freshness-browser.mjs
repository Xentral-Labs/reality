// The stored-result notice must say what a Refresh did (spec 180, FR-009).
// Fixtures control the response delay and the completed time, which is the only way
// to observe the in-flight state and the "nothing changed" outcome.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir, readFile } from "node:fs/promises";
const guidanceCatalog = JSON.parse(
  await readFile(
    new URL("../../../packages/reality-core/config/resolution_guidance.json", import.meta.url),
    "utf8",
  ),
);
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(10000);
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177",
  out = "/private/tmp/reality-freshness-browser";
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
let language = "en",
  completedAt = "2026-09-16T19:45:00Z",
  processed = 900,
  target = 900,
  delay = 0,
  state = "ready",
  readFails = false,
  summaryRequests = 0,
  failureCode = null,
  worker = "ready";

const metadata = () => ({
  projection: "exceptions",
  calculation_mode: "stored",
  state,
  processed_event_sequence: processed,
  target_event_sequence: target,
  completed_at: completedAt,
  projection_version: 1,
  upstream_freshness: "unknown",
  consistency: "completed_snapshot",
  failure_code: state === "failed" ? failureCode : null,
  guidance:
    state === "ready"
      ? null
      : {
          reason_code: state === "failed" && failureCode ? failureCode : `projection_${state}`,
          steps: [
            {
              code: "system_status",
              state: "open",
              role: "operator",
              path: "system_status",
              targets: [],
              target_count: 0,
            },
          ],
        },
});

await page.route("**/api/**", async (route) => {
  const u = new URL(route.request().url()),
    path = u.pathname;
  const reply = (data) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(data) });
  if (path.endsWith("/copilot"))
    return reply({
      sessions: [],
      active_session_id: null,
      messages: [],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (path === "/api/auth/me")
    return reply({
      id: "operator",
      email: "operator@example.test",
      display_name: "Operator",
      status: "active",
      language,
      locale: "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap")
    return reply({ tenants: [{ id: "t1", name: "Northstar" }], default_tenant_id: "t1" });
  if (path.endsWith("/application-reference"))
    return reply({ workspaces: [], resolution_guidance: guidanceCatalog });
  if (path.endsWith("/readiness"))
    return reply({
      status: worker === "ready" ? "ready" : worker,
      observed_at: completedAt,
      components: { connection: "ready", scheduler: "ready", worker },
    });
  if (path === "/api/playground/exception-catalog")
    return reply({
      version: 1,
      classes: [
        {
          id: "late_delivery",
          label: "Late customer delivery",
          description: "A delivery promised to a customer is late.",
          severity: "high",
          owner: "sales",
        },
      ],
    });
  if (path.endsWith("/attention/summary")) {
    summaryRequests++;
    if (delay) await new Promise((resolve) => setTimeout(resolve, delay));
    if (readFails) return route.fulfill({ status: 503, body: "Unavailable" });
    return reply({
      classes: [{ class_id: "late_delivery", open: 3 }],
      total: 3,
      observed_at: completedAt,
      metadata: metadata(),
    });
  }
  if (readFails && path.endsWith("/attention"))
    return route.fulfill({ status: 503, body: "Unavailable" });
  return reply({
    metadata: metadata(),
    items: [],
    page: { number: 1, size: 50, total: 0, pages: 1, has_next: false, has_previous: false },
  });
});

const notice = () => page.locator("[data-projection-freshness]");
const refreshButton = () => notice().getByRole("button");

await mkdir(out, { recursive: true });
try {
  await page.goto(`${base}/app/inspector?tenant=t1&inspector_view=exceptions`);
  await notice().waitFor();

  const initialButton = await refreshButton().boundingBox();
  const initialNotice = await notice().boundingBox();

  const timestampBox = await notice().locator("[data-projection-timestamp]").boundingBox();
  assert.ok(
    Math.abs(initialButton.x - timestampBox.x - timestampBox.width - 12) < 1,
    "Refresh must sit directly beside the timestamp",
  );
  const feedbackBox = await notice().locator("[data-projection-feedback]").boundingBox();
  assert.ok(
    feedbackBox.width <= 1 && feedbackBox.height <= 1,
    "outcome feedback must not occupy a visible row",
  );
  const spinner = () => notice().locator("[data-refresh-spinner]");

  assert.equal(await spinner().isVisible(), true, "idle button has a visible refresh icon");
  assert.equal(await spinner().evaluate((node) => getComputedStyle(node).animationName), "none");
  await refreshButton().focus();

  // 1. In flight: the control says so and cannot be pressed twice.
  delay = 1200;
  const requestsBeforeClick = summaryRequests;
  await refreshButton().press("Enter");
  await page.waitForFunction(
    () =>
      document.querySelector("[data-projection-freshness]")?.getAttribute("aria-busy") === "true",
  );
  assert.equal(
    await refreshButton().isDisabled(),
    true,
    "the control stays pressable while reading",
  );
  assert.equal(await refreshButton().innerText(), "Refresh");
  assert.equal(await spinner().isVisible(), true);
  assert.notEqual(await spinner().evaluate((node) => getComputedStyle(node).animationName), "none");
  assert.equal(await refreshButton().evaluate((node) => document.activeElement === node), true);
  assert.deepEqual(await refreshButton().boundingBox(), initialButton);
  assert.deepEqual(await notice().boundingBox(), initialNotice);
  await notice()
    .getByText("Checking for a newer calculation…", { exact: true })
    .filter({ visible: true })
    .waitFor();
  await refreshButton().press("Enter");
  await refreshButton().evaluate((node) => node.click());
  assert.equal(
    summaryRequests,
    requestsBeforeClick + 1,
    "busy activation must not issue another read",
  );
  await page.screenshot({ path: `${out}/in-flight.png` });

  // 2. Nothing changed upstream: say so instead of leaving the view identical.
  await page.waitForFunction(
    () =>
      document.querySelector("[data-projection-freshness]")?.getAttribute("aria-busy") !== "true",
  );
  assert.match(
    await notice().innerText(),
    /No newer calculation available/,
    "an unchanged result must be stated, not left silent",
  );
  assert.equal(await refreshButton().isDisabled(), false);
  await page.screenshot({ path: `${out}/unchanged.png` });

  assert.deepEqual(await refreshButton().boundingBox(), initialButton);
  assert.deepEqual(await notice().boundingBox(), initialNotice);

  // 3. A newer generation arrived: say that too.
  completedAt = "2026-09-16T20:15:00Z";
  await refreshButton().click();
  await page.locator('[data-projection-outcome="updated"]').waitFor();
  assert.match(
    await notice().innerText(),
    /Newer calculation loaded/,
    "a newer result must be announced",
  );
  await page.screenshot({ path: `${out}/updated.png` });

  // 4. A backlog is the reason to press the control at all.
  ((delay = 0), (state = "ready"), (readFails = false));
  processed = 880;
  target = 900;
  await refreshButton().click();
  await page.locator("[data-projection-behind]").waitFor();
  assert.equal(
    await page.locator("[data-projection-behind]").getAttribute("data-projection-behind"),
    "20",
    "the backlog behind the stored result is not stated",
  );
  assert.match(await notice().innerText(), /Events not yet included: 20/);
  await page.screenshot({ path: `${out}/behind.png` });

  // Repeated fast reads of a failed calculation keep the layout stable, including mobile.
  state = "failed";
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto(`${base}/app/inspector?tenant=t1&inspector_view=exceptions`);
    await notice().waitFor();
    const buttonBox = await refreshButton().boundingBox();
    const noticeBox = await notice().boundingBox();
    for (let attempt = 0; attempt < 3; attempt++) {
      const clickedAt = Date.now();
      await refreshButton().click();
      assert.equal(await spinner().isVisible(), true);
      assert.equal(await refreshButton().isDisabled(), true);
      await page.locator('[data-projection-outcome="unchanged"]').waitFor();
      assert.ok(Date.now() - clickedAt >= 950, "fast reads keep feedback for one second");
      assert.equal(await spinner().isVisible(), true);
      assert.equal(
        await spinner().evaluate((node) => getComputedStyle(node).animationName),
        "none",
      );
      assert.deepEqual(await refreshButton().boundingBox(), buttonBox);
      assert.deepEqual(await notice().boundingBox(), noticeBox);
      assert.match(await notice().innerText(), /The calculation could not be updated/);
      assert.match(await notice().innerText(), /No newer calculation available/);
      assert.doesNotMatch(await notice().innerText(), /Unchanged/);
    }
    await page.screenshot({ path: `${out}/stable-${width}.png` });
  }

  await page.emulateMedia({ reducedMotion: "reduce" });
  await refreshButton().click();
  assert.equal(await spinner().isVisible(), true);
  assert.equal(await spinner().evaluate((node) => getComputedStyle(node).animationName), "none");
  await page.locator('[data-projection-outcome="unchanged"]').waitFor();
  await page.emulateMedia({ reducedMotion: "no-preference" });

  // A failed HTTP read must never be described as a successful check.
  readFails = true;
  await refreshButton().click();
  await page
    .getByText(/Unavailable|503/)
    .first()
    .waitFor();
  assert.equal(await page.locator('[data-projection-outcome="unchanged"]').count(), 0);
  assert.equal(await page.locator('[data-projection-outcome="updated"]').count(), 0);
  readFails = false;

  // Work lists retain metadata on failed reads, so they need explicit error feedback.
  await page.goto(`${base}/app/attention?tenant=t1`);
  await notice().waitFor();
  readFails = true;
  await refreshButton().click();
  await notice()
    .getByText("Could not check for a newer calculation. Try again.", { exact: true })
    .filter({ visible: true })
    .waitFor();
  assert.equal(await page.locator('[data-projection-outcome="unchanged"]').count(), 0);
  await page.waitForFunction(
    () =>
      document
        .querySelector("[data-projection-freshness] button")
        ?.getAttribute("aria-disabled") !== "true",
  );
  readFails = false;
  await refreshButton().click();
  await page.locator('[data-projection-outcome="unchanged"]').waitFor();

  // Spec 279 FR-011: a result that is not current explains itself.
  state = "uninitialized";
  completedAt = null;
  worker = "unavailable";
  await page.goto(`${base}/app/attention?tenant=t1`);
  const explanation = page.locator('[data-projection-guidance="projection_uninitialized"]');
  await explanation.getByText("Waiting for the first calculation", { exact: true }).waitFor();
  await explanation
    .getByText("Background processing is currently unavailable, so calculations cannot run.", {
      exact: true,
    })
    .waitFor();
  state = "failed";
  completedAt = "2026-09-16T19:45:00Z";
  failureCode = "handler_timeout";
  worker = "ready";
  await page.reload();
  const failed = page.locator('[data-projection-guidance="handler_timeout"]');
  await failed.getByText("The calculation took too long", { exact: true }).waitFor();
  assert.equal(await failed.locator("[data-projection-processing]").count(), 0);
  const errorsBeforeHome = errors.length;
  await failed.getByRole("button", { name: "Open system status" }).click();
  await page.waitForURL((url) => url.pathname === "/app" || url.pathname === "/app/");
  // This fixture serves only the stored-result reads, not the Home page it links to:
  // leave Home before its reads settle and discard what they raised.
  await page.goto(`${base}/app/attention?tenant=t1`);
  errors.splice(errorsBeforeHome);
  state = "ready";
  failureCode = null;

  // 5. Every wording exists in all four languages.
  for (language of ["de", "nl", "es"]) {
    await page.goto(`${base}/app/inspector?tenant=t1&inspector_view=exceptions`);
    await notice().waitFor();
    await refreshButton().click();
    await page.waitForFunction(
      () =>
        document.querySelector("[data-projection-freshness]")?.getAttribute("aria-busy") !== "true",
    );
    const text = await notice().innerText();
    assert.doesNotMatch(
      text,
      /No newer calculation|Checking for|Events not yet included/,
      `${language} untranslated`,
    );
    assert.notEqual(text.trim(), "", `${language}: the notice is empty`);
    await page.screenshot({ path: `${out}/notice-${language}.png` });
  }

  assert.deepEqual(errors, []);
  console.log(
    "Projection freshness: in-flight state, unchanged and updated outcomes, backlog and four languages passed.",
  );
} catch (error) {
  console.error(errors, page.url(), (await page.locator("body").innerText()).slice(-2000));
  throw error;
} finally {
  await browser.close();
}

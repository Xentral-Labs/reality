// Real component and HTTP calls; PostgreSQL tests prove the business/control rules.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage();
page.setDefaultTimeout(10000);
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
const errors = [],
  writes = [],
  reads = [];
page.on("pageerror", (error) => errors.push(error.message));
let adopted = false,
  failTakeover = true,
  unsettled = false,
  contextMode = false;
const value = {
  case_id: "case_order",
  kind: "order_fulfillment",
  order_document_id: "doc_order",
  return_announcement_id: null,
  control_mode: "automation",
  control_revision: 1,
  goal_state: "outstanding",
  work: [{ commitment_id: "com_order", status: "open", open_quantity: "3" }],
  source_record_ids: ["src_order"],
  unavailable_capabilities: ["live_shopify_transport", "refund_intent_execution"],
  related_case_ids: [],
  actions: [],
  unsettled_actions: [],
  coverage_gaps: [],
};
await page.route("**/api/**", async (route) => {
  const req = route.request(),
    path = new URL(req.url()).pathname;
  const reply = (data, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
  if (req.method() === "POST") {
    const body = req.postDataJSON();
    writes.push({ path, body });
    assert.equal(body.confirmed, true);
    if (path.endsWith("/adoption")) {
      adopted = true;
      return reply({});
    }
    if (path.endsWith("/takeover")) {
      if (failTakeover) {
        failTakeover = false;
        return reply({ detail: "Temporary control failure" }, 503);
      }
      assert.equal(body.expected_revision, value.control_revision);
      value.control_mode = "human";
      value.control_revision++;
      return reply(value);
    }
    if (path.endsWith("/handback")) {
      assert.equal(body.review_digest, "d".repeat(64));
      value.control_mode = "automation";
      value.control_revision++;
      return reply(value);
    }
  }
  reads.push(path);
  if (path.endsWith("/objects/document/doc_order")) return reply({ case_ids: [value.case_id] });
  if (path.endsWith("/case_order")) return reply(value);
  if (path.endsWith("/status")) return reply({ adopted, can_adopt: true, can_control: true });
  if (path.endsWith("/handback-review"))
    return reply({
      ...value,
      unsettled_actions: unsettled ? ["act_unknown"] : [],
      digest: "d".repeat(64),
    });
  return reply(adopted && !contextMode ? [value] : []);
});
try {
  await page.goto(base + "/scripts/fixtures/operational-case-harness.html");
  await page.getByText("Operational cases", { exact: true }).click();
  await page.getByRole("button", { name: "Enable cases for new work", exact: true }).click();
  assert.equal(writes.length, 0);
  await page.getByRole("button", { name: "Confirm activation", exact: true }).click();
  await page
    .getByRole("button", { name: "Take over manually / stop automation", exact: true })
    .click();
  assert.equal(writes.length, 1);
  await page.getByRole("button", { name: "Confirm manual takeover", exact: true }).click();
  await page.getByRole("alert").waitFor();
  await page.getByRole("button", { name: "Confirm manual takeover", exact: true }).click();
  await page.getByText("Manually owned — automation stopped", { exact: true }).waitFor();
  assert.equal(
    writes[1].body.request_key,
    writes[2].body.request_key,
    "retry preserves exact control identity",
  );
  assert.equal(await page.locator('a[href*="src_order"]').count(), 1);
  unsettled = true;
  await page
    .getByRole("button", { name: "Review before returning to automation", exact: true })
    .click();
  await page.getByRole("button", { name: "Return to automation", exact: true }).waitFor();
  assert(
    await page.getByRole("button", { name: "Return to automation", exact: true }).isDisabled(),
  );
  unsettled = false;
  await page
    .getByRole("button", { name: "Review before returning to automation", exact: true })
    .click();
  await page.getByRole("button", { name: "Return to automation", exact: true }).click();
  await page.getByText("Automation owns this work", { exact: true }).waitFor();
  assert.equal(writes.at(-1).body.review_digest, "d".repeat(64));
  contextMode = true;
  const readBoundary = reads.length;
  await page.goto(base + "/scripts/fixtures/operational-case-harness.html?document=doc_order");
  await page.getByText("Operational cases", { exact: true }).click();
  await page.getByRole("button", { name: "Copy case ID", exact: true }).waitFor();
  assert(reads.slice(readBoundary).some((path) => path.endsWith("/objects/document/doc_order")));
  assert(!reads.slice(readBoundary).some((path) => path.endsWith("/operational-cases")));
  assert.deepEqual(errors, []);
  console.log(
    "Operational cases browser: confirmation, takeover retry, provenance, exact handback and direct object discovery passed",
  );
} finally {
  await browser.close();
}

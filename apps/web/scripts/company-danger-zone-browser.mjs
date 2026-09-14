// Spec 186: stateful HTTP fixtures; no company is archived or deleted in a real database.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(10000);
const base = process.env.UNIFIED_APP_URL || "http://127.0.0.1:5177";
const out = "/private/tmp/reality-186-browser";
await mkdir(out, { recursive: true });
const requests = [],
  errors = [],
  unmatched = [];
page.on("pageerror", (e) => errors.push(e.message));

let language = "en";
let archiveMode = "ok";
const usage = {
  state: "in_use",
  source_count: 2,
  evidence_count: 14,
  reality_count: 37,
  configured_count: 5,
  last_activity_at: "2026-09-10T10:00:00Z",
};
let companies = [
  { id: "north", name: "Northstar Commerce", role: "owner", archived_at: null },
  { id: "south", name: "Southline Trading", role: "owner", archived_at: null },
  { id: "shared", name: "Shared Works", role: "member", archived_at: "2026-08-20T09:00:00Z" },
];
let runs = [];
const runActive = (row) =>
  !row.sandbox_run_id || runs.find((run) => run.id === row.sandbox_run_id)?.status === "active";
const active = () => companies.filter((row) => !row.archived_at && runActive(row));
const bootstrap = () => ({
  tenants: active().map(({ archived_at: _archived, ...tenant }) => tenant),
  default_tenant_id: active()[0]?.id ?? null,
});

await page.route("**/api/**", async (route) => {
  const req = route.request(),
    path = new URL(req.url()).pathname;
  requests.push({ path, method: req.method(), body: req.postDataJSON() });
  const reply = (data, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
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
      id: "owner",
      email: "owner@example.test",
      display_name: "Owner",
      status: "active",
      language,
      locale: language === "de" ? "de-DE" : "en-GB",
      timezone: "UTC",
      is_platform_admin: false,
    });
  if (path === "/api/v1/bootstrap") return reply(bootstrap());
  if (path === "/api/v1/companies")
    return reply(
      companies.map((row) => ({
        ...row,
        created_at: "2026-08-01T08:00:00Z",
        ...usage,
      })),
    );
  const lifecycle = path.match(/^\/api\/v1\/companies\/([a-z]+)\/(archive|restore|delete)$/);
  if (lifecycle && req.method() === "POST") {
    const [, id, action] = lifecycle;
    const row = companies.find((entry) => entry.id === id);
    if (action === "archive") {
      if (archiveMode === "refuse")
        return reply(
          { detail: "Create or restore another tenant before archiving this one." },
          400,
        );
      row.archived_at = "2026-09-13T12:00:00Z";
      return reply({ id, name: row.name, archived_at: row.archived_at });
    }
    if (action === "restore") {
      row.archived_at = null;
      return reply({ id, name: row.name, archived_at: null });
    }
    const body = req.postDataJSON();
    if (body.confirmation_name !== row.name || body.confirmation_word !== "DELETE")
      return reply({ detail: "Tenant name and DELETE confirmation must match exactly." }, 400);
    companies = companies.filter((entry) => entry.id !== id);
    return route.fulfill({ status: 204, body: "" });
  }
  if (path === "/api/playground" && req.method() === "GET")
    return reply({ runs, total: runs.length, limit: 100, offset: 0 });
  const sandboxLifecycle = path.match(/^\/api\/playground\/runs\/([a-z0-9_]+)\/(archive|restore)$/);
  if (sandboxLifecycle && req.method() === "POST") {
    const [, id, action] = sandboxLifecycle;
    const run = runs.find((entry) => entry.id === id);
    if (req.postDataJSON().confirmed !== true)
      return reply({ detail: "Confirm archiving the sandbox first." }, 403);
    run.status = action === "archive" ? "archived" : "active";
    run.archived_at = action === "archive" ? "2026-09-13T13:00:00Z" : null;
    return reply(run);
  }
  if (path.endsWith("/application-reference")) return reply({ workspaces: [] });
  unmatched.push(path);
  return reply({ detail: `unmatched ${path}` }, 404);
});

const zone = page.locator("[data-danger-zone]");
const open = (tenant) =>
  page.goto(`${base}/app/settings?tenant=${tenant}&settings_view=company&lang=${language}`, {
    waitUntil: "networkidle",
  });

// 1. Archive the selected company: dialog, request, bootstrap reload, archived list.
await open("north");
await zone.scrollIntoViewIfNeeded();
await assert.doesNotReject(zone.getByRole("heading", { name: "Danger zone" }).waitFor());
const archiveButton = zone.locator('[data-danger-action="archive"] button');
assert.equal(await archiveButton.isEnabled(), true, "owner of two companies may archive");
assert.equal(await zone.locator("[data-danger-reason]").count(), 0);
await page.screenshot({ path: `${out}/01-zone.png`, fullPage: true });
await archiveButton.click();
const archiveDialog = page.locator('dialog[data-lifecycle-dialog][aria-label="Archive company"]');
await archiveDialog.waitFor();
await page.screenshot({ path: `${out}/02-archive-dialog.png` });
await archiveDialog.getByRole("button", { name: "Archive company" }).click();
await page.locator('[data-company-card="south"] [aria-current="true"]').waitFor();
assert.ok(
  requests.some((r) => r.method === "POST" && r.path === "/api/v1/companies/north/archive"),
  "archive posted",
);
assert.equal(await archiveDialog.count(), 0, "dialog closed after success");
assert.equal(
  await page.getByText("Company created").count(),
  0,
  "archive is not announced as a creation",
);
const archivedNorth = page.locator('[data-archived-company="north"]');
await archivedNorth.waitFor();
assert.match(await archivedNorth.innerText(), /Northstar Commerce/);
assert.match(await archivedNorth.innerText(), /Sources: 2/);
assert.match(await archivedNorth.innerText(), /Reality records: 37/);
const sharedRow = page.locator('[data-archived-company="shared"]');
assert.match(await sharedRow.innerText(), /Only company owners can restore or delete/);
assert.equal(await sharedRow.getByRole("button").count(), 0, "member rows carry no actions");
await page.screenshot({ path: `${out}/03-archived-list.png`, fullPage: true });

// 2. Delete permanently: gated confirm button, exact payload, row removed.
await archivedNorth.getByRole("button", { name: "Delete permanently" }).click();
const deleteDialog = page.locator(
  'dialog[data-lifecycle-dialog][aria-label="Delete company permanently"]',
);
await deleteDialog.waitFor();
const confirmDelete = deleteDialog.getByRole("button", { name: "Delete permanently" });
assert.equal(await confirmDelete.isEnabled(), false, "empty confirmation stays disabled");
await deleteDialog.locator('input[name="confirmation_name"]').fill("Northstar commerce");
await deleteDialog.locator('input[name="confirmation_word"]').fill("DELETE");
assert.equal(await confirmDelete.isEnabled(), false, "wrong case stays disabled");
await deleteDialog.locator('input[name="confirmation_name"]').fill("Northstar Commerce");
await deleteDialog.locator('input[name="confirmation_word"]').fill("delete");
assert.equal(await confirmDelete.isEnabled(), false, "lower-case word stays disabled");
await deleteDialog.locator('input[name="confirmation_word"]').fill("DELETE");
assert.equal(await confirmDelete.isEnabled(), true, "exact name and word enable deletion");
await page.screenshot({ path: `${out}/04-delete-dialog.png` });
await confirmDelete.click();
await archivedNorth.waitFor({ state: "detached" });
const deleteRequest = requests.find(
  (r) => r.method === "POST" && r.path === "/api/v1/companies/north/delete",
);
assert.deepEqual(deleteRequest.body, {
  confirmation_name: "Northstar Commerce",
  confirmation_word: "DELETE",
});
assert.equal(await deleteDialog.count(), 0);

// 3. Last active company: archive disabled with its reason.
assert.equal(await archiveButton.isEnabled(), false, "last active company cannot be archived");
await zone.locator('[data-danger-reason="last-active"]').waitFor();
await page.screenshot({ path: `${out}/05-last-active.png`, fullPage: true });

// 4. Restore an archived company brings it back to the switcher.
companies.push({
  id: "west",
  name: "Westport Goods",
  role: "owner",
  archived_at: "2026-09-01T00:00:00Z",
});
await open("south");
const westRow = page.locator('[data-archived-company="west"]');
await westRow.waitFor();
await westRow.getByRole("button", { name: "Restore" }).click();
await page.locator('[data-company-card="west"]').waitFor();
await westRow.waitFor({ state: "detached" });
assert.ok(requests.some((r) => r.method === "POST" && r.path === "/api/v1/companies/west/restore"));
assert.equal(await archiveButton.isEnabled(), true, "two active companies again");

// 5. A server refusal stays in the dialog as an alert.
archiveMode = "refuse";
await archiveButton.click();
await archiveDialog.waitFor();
await archiveDialog.getByRole("button", { name: "Archive company" }).click();
await archiveDialog.getByRole("alert").waitFor();
assert.match(await archiveDialog.getByRole("alert").innerText(), /another tenant/);
await archiveDialog.getByRole("button", { name: "Cancel" }).click();
await archiveDialog.waitFor({ state: "detached" });
archiveMode = "ok";

// 6. Members are explained; a sandbox owner archives and restores through the run.
companies = [
  { id: "south", name: "Southline Trading", role: "member", archived_at: null },
  { id: "west", name: "Westport Goods", role: "owner", archived_at: null },
];
await open("south");
assert.equal(await archiveButton.isEnabled(), false);
await zone.locator('[data-danger-reason="not-owner"]').waitFor();
companies = [
  {
    id: "box",
    name: "Practice run",
    role: "owner",
    archived_at: null,
    purpose: "playground",
    sandbox_run_id: "pgr_1",
  },
  {
    id: "old",
    name: "Old Lab",
    role: "owner",
    archived_at: null,
    purpose: "playground",
    sandbox_run_id: "pgr_9",
  },
  { id: "west", name: "Westport Goods", role: "owner", archived_at: null },
];
runs = [
  {
    id: "pgr_1",
    sandbox_kind: "practice",
    company_name: "Practice run",
    tenant_id: "box",
    status: "active",
    created_at: "2026-09-10T08:00:00Z",
    archived_at: null,
  },
  {
    id: "pgr_9",
    sandbox_kind: "practice",
    company_name: "Old Lab",
    tenant_id: "old",
    status: "archived",
    created_at: "2026-09-01T08:00:00Z",
    archived_at: "2026-09-05T08:00:00Z",
  },
];
await open("box");
await zone.locator('[data-danger-action="archive"][data-lifecycle-kind="sandbox"]').waitFor();
assert.equal(await archiveButton.isEnabled(), true, "a sandbox owner may archive the sandbox");
assert.equal(await archiveButton.innerText(), "Archive sandbox");
const oldLab = page.locator('[data-archived-sandbox="pgr_9"]');
await oldLab.waitFor();
assert.match(await oldLab.innerText(), /Old Lab/);
assert.equal(await oldLab.getByRole("button", { name: "Restore" }).count(), 1);
await page.screenshot({ path: `${out}/06-sandbox.png`, fullPage: true });
await archiveButton.click();
const sandboxDialog = page.locator('dialog[data-lifecycle-dialog][aria-label="Archive sandbox"]');
await sandboxDialog.waitFor();
await sandboxDialog.getByRole("button", { name: "Archive sandbox" }).click();
await page.locator('[data-company-card="west"] [aria-current="true"]').waitFor();
const sandboxArchive = requests.find(
  (r) => r.method === "POST" && r.path === "/api/playground/runs/pgr_1/archive",
);
assert.deepEqual(sandboxArchive.body, { confirmed: true });
await page.locator('[data-archived-sandbox="pgr_1"]').waitFor();
assert.equal(await page.locator('[data-company-card="box"]').count(), 0, "sandbox left the list");
await oldLab.getByRole("button", { name: "Restore" }).click();
await page.locator('[data-company-card="old"]').waitFor();
await oldLab.waitFor({ state: "detached" });
assert.ok(
  requests.some((r) => r.method === "POST" && r.path === "/api/playground/runs/pgr_9/restore"),
);
await page.screenshot({ path: `${out}/06b-sandbox-restored.png`, fullPage: true });

// 7. German at phone width: the zone stays inside the viewport.
language = "de";
runs = [];
companies = [
  { id: "north", name: "Northstar Commerce", role: "owner", archived_at: null },
  { id: "south", name: "Southline Trading", role: "owner", archived_at: "2026-09-02T00:00:00Z" },
];
await page.setViewportSize({ width: 390, height: 844 });
await open("north");
await zone.getByRole("heading", { name: "Gefahrenbereich" }).waitFor();
await page
  .locator('[data-archived-company="south"]')
  .getByRole("button", { name: "Endgültig löschen" })
  .waitFor();
const geometry = await zone.evaluate((node) => ({
  right: Math.round(node.getBoundingClientRect().right),
  width: window.innerWidth,
}));
assert.ok(geometry.right <= geometry.width, JSON.stringify(geometry));
await page
  .locator('[data-archived-company="south"]')
  .getByRole("button", { name: "Endgültig löschen" })
  .click();
// Dialog labels are translated, so the German step addresses the dialog by its marker.
const germanDialog = page.locator("dialog[data-lifecycle-dialog]");
await germanDialog.waitFor();
await germanDialog.getByText("DELETE", { exact: true }).waitFor();
await page.screenshot({ path: `${out}/07-de-390.png`, fullPage: true });
await germanDialog.getByRole("button", { name: "Abbrechen" }).click();

assert.deepEqual(errors, [], "no page errors");
assert.deepEqual(
  unmatched.filter((path) => !path.includes("/copilot")),
  [],
  "every fixture route matched",
);
await browser.close();
console.log("company danger zone browser checks passed", out);

// Spec 192: stateful HTTP fixtures; no account is deleted in a real database.
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
const out = "/private/tmp/reality-192-browser";
await mkdir(out, { recursive: true });
const requests = [];
const errors = [];
page.on("pageerror", (event) => errors.push(event.message));

let language = "en";
let deleteMode = "ok";
const admin = {
  id: "usr_admin",
  email: "owner@reality.local",
  display_name: "Owner",
  status: "active",
  is_platform_admin: true,
  application: { id: "app_admin", status: "approved" },
};
let applicants = [
  {
    id: "usr_free5",
    email: "benedikt.sauter+free5@xentral.com",
    display_name: "",
    status: "active",
    is_platform_admin: false,
    application: { id: "app_free5", status: "approved" },
  },
  {
    id: "usr_pending",
    email: "benedikt.sauter+20260914@xentral.com",
    display_name: "",
    status: "pending_approval",
    is_platform_admin: false,
    application: { id: "app_pending", status: "pending" },
  },
  {
    id: "usr_colleague",
    email: "second-admin@xentral.com",
    display_name: "Tobi",
    status: "active",
    is_platform_admin: true,
    application: { id: "app_colleague", status: "approved" },
  },
];

const row = (user) => ({
  ...user,
  language,
  locale: language === "de" ? "de-DE" : "en-GB",
  timezone: "UTC",
  application: {
    company_name: "",
    company_website: "",
    orders_per_day: "",
    role_title: "",
    requested_at: "2026-09-14T08:00:00Z",
    reviewed_at: null,
    ...user.application,
  },
});

const preview = {
  user_id: "usr_free5",
  email: "benedikt.sauter+free5@xentral.com",
  is_platform_admin: false,
  deleted_companies: [
    { id: "ten_sandbox", name: "Practice Company", purpose: "playground", record_count: 412 },
  ],
  kept_companies: [{ id: "ten_shared", name: "Shared Works" }],
  sandbox_count: 1,
  record_count: 412,
};

await page.route("**/api/**", async (route) => {
  const request = route.request();
  const path = new URL(request.url()).pathname;
  requests.push({ path, method: request.method(), body: request.postDataJSON() });
  const reply = (data, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(data) });
  if (path === "/api/auth/me") return reply(row(admin));
  if (path === "/api/admin/access-applications") return reply([admin, ...applicants].map(row));
  if (path === "/api/admin/access-capacity") return reply({ used: 0, limit: null });
  if (path.endsWith("/deletion-preview")) return reply(preview);
  if (path.endsWith("/delete") && request.method() === "POST") {
    if (deleteMode === "refuse")
      return reply({ detail: "Account e-mail and DELETE confirmation must match exactly." }, 400);
    applicants = applicants.filter((user) => !path.includes(user.application.id));
    return reply(preview);
  }
  return reply({});
});

// `?lang=` is the explicit choice; it outranks the remembered preference, which
// in turn outranks the account language the /me fixture returns.
const open = async () => {
  await page.goto(`${base}/admin/access?lang=${language}`, { waitUntil: "networkidle" });
  await page.waitForSelector(".application-list article");
};

await open();

// FR-001: offered for other applicants, withheld for the administrator's own row
// and for a colleague administrator.
const deleteButton = (email) =>
  page.locator(`.application-list article:has(small:text-is("${email}")) .delete-applicant`);
assert.equal(await deleteButton("benedikt.sauter+free5@xentral.com").count(), 1);
assert.equal(await deleteButton("owner@reality.local").count(), 0, "own row offers deletion");
assert.equal(
  await deleteButton("second-admin@xentral.com").count(),
  0,
  "colleague administrator offers deletion",
);
await page.screenshot({ path: `${out}/list-en.png`, fullPage: true });

// FR-002: the dialog names what is lost before anything can be confirmed.
await deleteButton("benedikt.sauter+free5@xentral.com").click();
const dialog = page.locator("dialog.applicant-delete-dialog");
await dialog.waitFor({ state: "visible" });
await page.waitForFunction(() => !!document.querySelector(".deletion-losses"));
const losses = await page.locator(".deletion-losses").innerText();
assert.match(losses, /Practice Company/);
assert.match(losses, /412/);
assert.match(losses, /Shared Works/);
await page.screenshot({ path: `${out}/dialog-en.png` });

// FR-003: both answers gate the confirm button.
const confirm = dialog.locator("button[type=submit]");
const emailField = dialog.locator("input[name=confirmation_email]");
const wordField = dialog.locator("input[name=confirmation_word]");
assert.equal(await confirm.isDisabled(), true, "confirm enabled before any answer");
await emailField.fill("benedikt.sauter+free5@xentral.com");
assert.equal(await confirm.isDisabled(), true, "confirm enabled without the word");
await wordField.fill("delete");
assert.equal(await confirm.isDisabled(), true, "lower-case word enabled the confirm");
await wordField.fill("DELETE");
assert.equal(await confirm.isDisabled(), false, "correct answers left the confirm disabled");
await emailField.fill("someone.else@xentral.com");
assert.equal(await confirm.isDisabled(), true, "wrong address enabled the confirm");
await emailField.fill("Benedikt.Sauter+Free5@Xentral.com");
assert.equal(await confirm.isDisabled(), false, "a differently cased address was refused");

// A server refusal is shown without removing the row.
deleteMode = "refuse";
await confirm.click();
await page.waitForSelector("dialog.applicant-delete-dialog [role=alert]");
assert.match(await dialog.locator("[role=alert]").innerText(), /match exactly/);
await page.screenshot({ path: `${out}/dialog-refused-en.png` });

// FR-004/FR-011: the confirmed payload the server receives, then the row is gone.
deleteMode = "ok";
requests.length = 0;
await confirm.click();
await page.waitForFunction(() => !document.querySelector("dialog.applicant-delete-dialog"), null, {
  timeout: 10000,
});
const sent = requests.find((entry) => entry.path.endsWith("/delete"));
assert.deepEqual(sent.body, {
  confirmation_email: "Benedikt.Sauter+Free5@Xentral.com",
  confirmation_word: "DELETE",
});
assert.equal(sent.path, "/api/admin/access-applications/app_free5/delete");
await page.waitForFunction(
  () => !document.body.innerText.includes("benedikt.sauter+free5@xentral.com"),
);
await page.screenshot({ path: `${out}/list-after-en.png`, fullPage: true });

// FR-012: German, and the narrow viewport the admin page is also read on.
language = "de";
await page.setViewportSize({ width: 390, height: 900 });
await open();
await deleteButton("benedikt.sauter+20260914@xentral.com").click();
await dialog.waitFor({ state: "visible" });
await page.waitForFunction(() => !!document.querySelector(".deletion-losses"));
const german = await dialog.innerText();
assert.match(german, /Konto löschen/);
assert.match(german, /Es kann nicht rückgängig gemacht werden/);
assert.match(german, /DELETE/, "the confirmation word must stay literal in German");
await page.screenshot({ path: `${out}/dialog-de-390.png` });

// The dialog must fit the phone viewport. The page itself already overflows by
// 2px at 390px through its 44px heading, which predates this feature and is
// unchanged by it: the same measurement with every delete control withheld
// reports the same 392px.
const fits = await page.evaluate(() => {
  const box = document.querySelector("dialog.applicant-delete-dialog").getBoundingClientRect();
  return box.left >= 0 && box.right <= window.innerWidth;
});
assert.equal(fits, true, "the confirmation dialog overflows the 390px viewport");

assert.deepEqual(errors, []);
console.log(`Spec 192 browser proof passed; screenshots in ${out}`);
await browser.close();

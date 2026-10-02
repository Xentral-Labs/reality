// Spec 328: a chat shows only its own proposals, after the answer that made them,
// keeps decided ones with their outcome, and only counts pending approvals elsewhere.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));

const message = (id, role, content, minute) => ({
  id,
  role,
  content,
  created_at: `2026-10-02T10:0${minute}:00+00:00`,
});
const proposal = (id, status, after) => ({
  id,
  tool: "normal_month",
  actor_type: "agent",
  status,
  input: {},
  output: {},
  preview: {},
  created_at: "2026-10-02T10:01:30+00:00",
  decided_at: status === "proposed" ? null : "2026-10-02T10:05:00+00:00",
  decided_by: null,
  decider: { kind: "unknown" },
  review_kind: "common",
  review_destination: "proposal-review",
  review_label: "Run the normal month",
  review_purpose: "",
  after_message_id: after,
});
const conversations = {
  first: {
    messages: [
      message("u1", "user", "Run the normal month", 1),
      message("a1", "assistant", "Prepared the normal month proposal.", 2),
      message("u2", "user", "And reserve stock", 3),
      message("a2", "assistant", "Prepared the reservation.", 4),
    ],
    proposals: [
      proposal("pending-one", "proposed", "a1"),
      proposal("decided-one", "rejected", "a2"),
    ],
    pending_elsewhere: 2,
  },
  second: { messages: [], proposals: [], pending_elsewhere: 0 },
};

await page.route("**/api/**", async (route) => {
  const url = new URL(route.request().url());
  const path = url.pathname;
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (path === "/api/auth/me")
    return reply({
      id: "user",
      email: "user@example.test",
      status: "active",
      language: "en",
      locale: "en-GB",
      timezone: "UTC",
    });
  if (path === "/api/v1/bootstrap")
    return reply({
      tenants: [{ id: "one", name: "One", purpose: "playground" }],
      default_tenant_id: "one",
    });
  if (path.endsWith("/copilot")) {
    const active = url.searchParams.get("session_id") || "first";
    return reply({
      sessions: [
        { id: "first", title: "First conversation", message_count: 4 },
        { id: "second", title: "Second conversation", message_count: 0 },
      ],
      active_session_id: active,
      ...conversations[active],
      suggestions: [],
      has_archived: false,
    });
  }
  // No recorded basis for these answers.
  if (path.includes("/storyline/chat/")) return reply({ detail: "Not found" }, 404);
  if (path.endsWith("/change-proposals"))
    return reply({ items: [], page: { page: 1, size: 50, total: 0, pages: 1 } });
  return reply({ items: [], workspaces: [], commands: [] });
});

const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
// The page chat; the hidden global dock renders the same conversation again.
const root = "[data-independent-free-play]";
const chat = page.locator(root);
const follows = (earlier, later) =>
  page.evaluate(
    ([a, b, root]) =>
      !!(
        document
          .querySelector(`${root} ${a}`)
          .compareDocumentPosition(document.querySelector(`${root} ${b}`)) &
        Node.DOCUMENT_POSITION_FOLLOWING
      ),
    [earlier, later, root],
  );
try {
  await page.goto(`${base}/app/chat?tenant=one&session=first`);
  const pending = chat.locator("[data-chat-decision=pending-one]");
  const decided = chat.locator("[data-chat-decision=decided-one]");
  await pending.waitFor();
  await decided.waitFor();

  // Each proposal follows the answer of its own turn, not the end of the history.
  const answers = chat.locator("[data-chat-role=assistant]");
  const questions = chat.locator("[data-chat-role=user]");
  assert.equal(await answers.count(), 2);
  assert.equal(await questions.count(), 2);
  await page.evaluate((root) => {
    const [a1, a2] = document.querySelectorAll(`${root} [data-chat-role=assistant]`);
    const [, u2] = document.querySelectorAll(`${root} [data-chat-role=user]`);
    a1.setAttribute("data-probe", "a1");
    a2.setAttribute("data-probe", "a2");
    u2.setAttribute("data-probe", "u2");
  }, root);
  assert.ok(await follows("[data-probe=a1]", "[data-chat-decision=pending-one]"));
  assert.ok(await follows("[data-chat-decision=pending-one]", "[data-probe=u2]"));
  assert.ok(await follows("[data-probe=a2]", "[data-chat-decision=decided-one]"));

  // Pending opens its review; decided keeps its outcome and offers no approval.
  assert.equal(await pending.getByRole("button", { name: "Review", exact: true }).count(), 1);
  assert.equal(await decided.getByRole("button", { name: "Review", exact: true }).count(), 0);
  assert.equal(await decided.locator("[data-decision=decided-one]").count(), 1);
  assert.equal(await decided.getAttribute("data-chat-decision-status"), "rejected");

  // Decisions made elsewhere are a count, not a list in the conversation.
  const elsewhere = chat.locator("[data-chat-pending-elsewhere]");
  await elsewhere.waitFor();
  assert.equal(await elsewhere.getAttribute("data-chat-pending-elsewhere"), "2");
  assert.match(await elsewhere.innerText(), /2\s*Other pending approvals/u);
  await page.screenshot({ path: "/private/tmp/reality-chat-scoped-proposals.png" });

  // A conversation without proposals shows none and no hint when nothing is pending.
  await page.goto(`${base}/app/chat?tenant=one&session=second`);
  await chat.getByText("What would you like to understand or do?").waitFor();
  assert.equal(await chat.locator("[data-chat-decision]").count(), 0);
  assert.equal(await chat.locator("[data-chat-pending-elsewhere]").count(), 0);

  await page.goto(`${base}/app/chat?tenant=one&session=first`);
  await elsewhere.click();
  await page.waitForURL(/\/app\/decisions/u);

  assert.deepEqual(errors, []);
  console.log("chat scoped proposals browser proof passed");
} finally {
  await browser.close();
}

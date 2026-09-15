// Spec 182 (T021): the Storyline page against fixtures. The service tests prove what a
// chapter records; this proves the narrator, the stage and the protocol show it, that
// confirmation goes through the storyline route only, and that the page holds at 390px
// in four languages.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { mkdir } from "node:fs/promises";
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE));
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.PLAYWRIGHT_EXECUTABLE,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(12000);
const base = process.env.UNIFIED_BASE_URL || "http://127.0.0.1:5177";
const errors = [],
  writes = [];
let enterThroughHome = false,
  entryReads = 0;
let language = "en",
  phase = "idle",
  started = false,
  imported = false,
  blocked = false,
  restarted = false;
let independentCreated = false;
let independentSession = null;
let independentRemaining = 18;
let independentSessionCreates = 0;
const independentMessages = [];
let chatSession = null;
const chatMessages = [],
  chatSends = [],
  evidenceReads = [];
const deltaQueries = [],
  profileSaves = [];
page.on("pageerror", (e) => errors.push(e.message));

const text = (en, de) => ({ en, de, nl: `${en} (nl)`, es: `${en} (es)` });
const openChapters = async () => {
  if (!(await page.locator("[data-storyline-chapters][open]").count()))
    await page.locator("[data-storyline-chapters] > summary").click();
};
const chapters = () => [
  {
    key: "order",
    status: phase === "done" ? "done" : "current",
    kind: "command",
    step_id: phase === "idle" ? null : "step-order",
    step_status: phase === "idle" ? null : phase === "pending" ? "pending" : "done",
    refused: null,
    marker: phase === "idle" ? null : { sequence: 12, at: "2026-09-12T10:00:00Z" },
    title: text("Create the order", "Auftrag anlegen"),
    view: "view:orders",
    command: "order_create",
    branches: [],
  },
  {
    key: "reference",
    status: phase === "done" ? "current" : "upcoming",
    kind: "command",
    step_id: null,
    step_status: null,
    refused: null,
    marker: null,
    title: text("Note the customer reference", "Kundenreferenz festhalten"),
    view: "view:documents",
    command: "fact_observe",
    branches: [],
  },
  {
    key: "review",
    status: "upcoming",
    kind: "read",
    step_id: null,
    step_status: null,
    refused: null,
    marker: null,
    title: text("Month-end review", "Monatsrückblick"),
    view: "view:activity",
    command: null,
    branches: [],
  },
];
const step = () =>
  phase === "idle"
    ? null
    : {
        step_id: "step-order",
        chapter: "order",
        sequence: 1,
        status: phase === "pending" ? "pending" : "done",
        proposal_id: "act-order",
        proposal_status: phase === "pending" ? "proposed" : "executed",
        preview_revision: "rev-1",
        review: phase === "pending" ? { tool: "order_create", targets: [] } : null,
        arguments: { direction: "sales", number: "AT-0041", gross_amount: "294.00" },
        output: phase === "done" ? { commitment_ids: ["com_new0000001"] } : null,
        refused: null,
        context: null,
        marker: { sequence: 12, at: "2026-09-12T10:00:00Z" },
        receipt:
          phase === "done"
            ? {
                kind: "command",
                records: [{ family: "commitment", id: "com_new0000001" }],
                event_ids: ["evt-1"],
                event_sequence: 14,
              }
            : null,
      };
const trace = () =>
  phase === "idle"
    ? []
    : [
        {
          id: "trc-1",
          ordinal: 1,
          step_id: "step-order",
          chapter: "order",
          kind: "propose",
          name: "order_create",
          access: "propose",
          actor: "storyline",
          proposal_id: "act-order",
          marker: null,
          before_exceptions: null,
          input: { direction: "sales", number: "AT-0041" },
          result: { proposal_id: "act-order", status: "proposed" },
          duration_ms: 9,
          recorded_at: "2026-09-12T10:00:01Z",
        },
        ...(phase === "done"
          ? [
              {
                id: "trc-2",
                ordinal: 2,
                step_id: "step-order",
                chapter: "order",
                kind: "confirm",
                name: "order_create",
                access: "confirm",
                actor: "storyline",
                proposal_id: "act-order",
                marker: { sequence: 12, at: "2026-09-12T10:00:00Z" },
                before_exceptions: [],
                input: { direction: "sales" },
                result: { commitment_ids: ["com_new0000001"] },
                duration_ms: 44,
                recorded_at: "2026-09-12T10:00:02Z",
              },
            ]
          : []),
      ];
// Two calls a person made in the ordinary app while the story waited (FR-011).
const freeTrace = () =>
  phase !== "done"
    ? []
    : [
        {
          id: "trc-7",
          ordinal: 7,
          step_id: null,
          chapter: null,
          kind: "propose",
          name: "reserve",
          access: "propose",
          actor: "person",
          proposal_id: "act-free",
          marker: null,
          before_exceptions: null,
          input: { commitment_id: "com_new0000001" },
          result: { proposal_id: "act-free", status: "proposed" },
          duration_ms: 6,
          recorded_at: "2026-09-12T10:05:01Z",
        },
        {
          id: "trc-8",
          ordinal: 8,
          step_id: null,
          chapter: null,
          kind: "confirm",
          name: "reserve",
          access: "confirm",
          actor: "person",
          proposal_id: "act-free",
          marker: { sequence: 20, at: "2026-09-12T10:05:00Z" },
          before_exceptions: ["exc__outgoing_commitment_at_risk"],
          input: { commitment_id: "com_new0000001" },
          result: { reservation_id: "res_free000001" },
          duration_ms: 31,
          recorded_at: "2026-09-12T10:05:02Z",
        },
      ];
const delta = {
  range: {
    after_sequence: 12,
    after_at: "2026-09-12T10:00:00Z",
    latest_sequence: 14,
    available: true,
    has_more: false,
  },
  events: [
    {
      id: "evt-1",
      sequence: 13,
      type: "document.created",
      subject_type: "document",
      subject_id: "doc_new0000001",
      title: "Order recorded",
      occurred_at: "2026-09-12T10:00:02Z",
      recorded_at: "2026-09-12T10:00:02Z",
      action_id: "act-order",
    },
    {
      id: "evt-2",
      sequence: 14,
      type: "commitment.created",
      subject_type: "commitment",
      subject_id: "com_new0000001",
      title: "Commitment created",
      occurred_at: "2026-09-12T10:00:02Z",
      recorded_at: "2026-09-12T10:00:02Z",
      action_id: "act-order",
    },
  ],
  facts: [],
  records: [
    { record_type: "document", record_id: "doc_new0000001" },
    { record_type: "commitment", record_id: "com_new0000001" },
  ],
  exceptions: {
    raised: [
      {
        id: "exc__outgoing_commitment_at_risk__com_new0000001",
        class_id: "outgoing_commitment_at_risk",
        record_type: "commitment",
        record_id: "com_new0000001",
        label: text("Customer commitment at risk", "Kundenverpflichtung gefährdet"),
        title: "Customer commitment at risk",
        impact: "4 remain unreserved",
        severity: "high",
        clears_through: "Reserving stock or receiving goods.",
      },
    ],
    cleared: [],
  },
  graph: {
    record: { record_type: "commitment", record_id: "com_new0000001" },
    nodes: [
      { record_type: "commitment", record_id: "com_new0000001", new: true, primary: true },
      { record_type: "party", record_id: "pty_0000000001", new: false, primary: false },
    ],
    edges: [
      {
        from: "commitment:com_new0000001",
        to: "party:pty_0000000001",
        relation: "to_party",
        new: true,
      },
    ],
  },
};

await page.route("**/api/**", async (route) => {
  const req = route.request(),
    u = new URL(req.url()),
    // The fresh company after a restart answers like the first one.
    p = u.pathname.replace("/tenants/story-2/", "/tenants/story/");
  const reply = (body, status = 200) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  if (req.method() !== "GET") writes.push(p);
  if (p === "/api/storyline/free-play") {
    if (req.method() === "POST") {
      assert.equal(req.postDataJSON().confirmed, true);
      independentCreated = true;
    }
    return reply(
      independentCreated
        ? {
            available: true,
            tenant_id: "independent",
            run_id: "independent-run",
            name: "Free Play",
            status: "ready",
            environment: "sandbox",
            error_code: null,
            profile: null,
          }
        : { available: false },
    );
  }
  if (p === "/api/tenants/plain/copilot")
    return reply({
      sessions: [{ id: "plain-chat", title: "Company chat" }],
      active_session_id: "plain-chat",
      messages: [
        {
          id: "plain-answer",
          role: "assistant",
          content: "Existing company answer.",
          created_at: "2026-09-15T09:00:00Z",
        },
      ],
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (p === "/api/tenants/plain/storyline/chat/plain-answer")
    return route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ detail: "No recorded Sandbox found." }),
    });
  if (p.includes("/tenants/independent/")) {
    if (p.endsWith("/copilot/sessions") && req.method() === "POST") {
      independentSessionCreates++;
      independentSession = { id: "independent-chat", title: "Independent chat" };
      return reply(independentSession);
    }
    if (p.endsWith("/copilot/sessions/independent-chat/messages") && req.method() === "POST") {
      if (!independentMessages.length)
        independentMessages.push(
          ...Array.from({ length: 24 }, (_, index) => ({
            id: `history-${index}`,
            role: "user",
            content: `Earlier Sandbox question ${index}. `.repeat(8),
            created_at: "2026-09-15T09:00:00Z",
          })),
        );
      independentMessages.push(
        {
          id: "independent-question",
          role: "user",
          content: req.postDataJSON().message,
          created_at: "2026-09-15T10:00:01Z",
        },
        {
          id: "independent-answer",
          role: "assistant",
          content: "Independent Sandbox answer.",
          created_at: "2026-09-15T10:00:02Z",
        },
      );
      return reply({});
    }
    if (p.endsWith("/copilot"))
      return reply({
        sessions: independentSession
          ? [independentSession, { id: "older-chat", title: "Earlier conversation" }]
          : [],
        active_session_id:
          u.searchParams.get("session_id") === "older-chat"
            ? "older-chat"
            : independentSession?.id || null,
        allowance: {
          limit: 20,
          used: 20 - independentRemaining,
          remaining: independentRemaining,
          resets_at: "2099-09-15T00:00:00Z",
        },
        messages:
          u.searchParams.get("session_id") === "older-chat"
            ? [
                {
                  id: "older-answer",
                  role: "assistant",
                  content: "Earlier session content.",
                  created_at: "2026-09-15T08:00:00Z",
                },
              ]
            : independentMessages,
        proposals: [],
        suggestions: [],
        has_archived: false,
      });
    if (p.endsWith("/storyline/chat/independent-answer"))
      return reply({ available: true, items: [], has_more: false });
  }
  if (p.endsWith("/copilot/sessions") && req.method() === "POST") {
    chatSession = {
      id: "free-chat",
      title: "Free Play",
      archived: false,
      created_at: "2026-09-15T10:00:00Z",
    };
    return reply(chatSession);
  }
  if (p.endsWith("/copilot/sessions/free-chat/messages") && req.method() === "POST") {
    const body = req.postDataJSON();
    chatSends.push(body);
    chatMessages.push(
      {
        id: "question-free",
        role: "user",
        content: body.message,
        created_at: "2026-09-15T10:00:01Z",
      },
      {
        id: "answer-free",
        role: "assistant",
        content: "I checked the open findings in this Sandbox.",
        created_at: "2026-09-15T10:00:02Z",
      },
    );
    return reply({});
  }
  if (p.endsWith("/storyline/chat/answer-free")) {
    evidenceReads.push(p);
    return reply({
      available: true,
      has_more: false,
      items: [
        {
          id: "trc-chat-read",
          ordinal: 10,
          step_id: null,
          chapter: null,
          kind: "read",
          name: "exceptions",
          access: "read",
          actor: "chat",
          proposal_id: null,
          marker: null,
          before_exceptions: null,
          input: {},
          result: { items: [] },
          duration_ms: 4,
          recorded_at: "2026-09-15T10:00:02Z",
        },
      ],
    });
  }
  if (p.endsWith("/copilot"))
    return reply({
      sessions: chatSession ? [chatSession] : [],
      active_session_id: chatSession?.id || null,
      messages: chatMessages,
      proposals: [],
      suggestions: [],
      has_archived: false,
    });
  if (p === "/api/auth/profile" && req.method() === "PUT") {
    language = req.postDataJSON().language;
    profileSaves.push(language);
  }
  if (p === "/api/auth/me" || p === "/api/auth/profile")
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
  if (p === "/api/company-setup/playground") {
    assert.equal(req.method(), "GET", "refresh must not create a company");
    entryReads++;
    await new Promise((resolve) => setTimeout(resolve, 250));
    return reply({
      requested: false,
      archived: false,
      enabled: true,
      eligible: true,
      receipt: null,
    });
  }
  if (p === "/api/v1/bootstrap")
    return reply({
      tenants: [
        { id: "plain", name: "Northstar Commerce", company_kind: "company" },
        ...(independentCreated
          ? [{ id: "independent", name: "Free Play", company_kind: "sandbox", role: "owner" }]
          : []),
        ...(started
          ? [{ id: "story", name: "Order to close", company_kind: "sandbox", role: "owner" }]
          : []),
        ...(restarted
          ? [{ id: "story-2", name: "Order to close 2", company_kind: "sandbox", role: "owner" }]
          : []),
      ],
      default_tenant_id: enterThroughHome ? "story" : "plain",
    });
  if (p.endsWith("/application-reference")) return reply({ workspaces: [], commands: [] });
  if (p === "/api/storyline/library" && req.method() === "GET")
    return reply({
      enabled: true,
      items: [
        {
          key: "order-to-close",
          version: 1,
          title: text("Order to close", "Auftrag bis Abschluss"),
          summary: text("One order, one story.", "Ein Auftrag, eine Geschichte."),
          author: "Reality team",
          chapters: 3,
          origin: "builtin",
          imported_at: null,
          run: started
            ? {
                run_id: "run-1",
                tenant_id: "story",
                status: "active",
                current_chapter: phase === "done" ? "reference" : "order",
                position: phase === "done" ? 2 : 1,
                total: 3,
                done: phase === "done" ? 1 : 0,
                company_name: "Order to close",
              }
            : null,
        },
        ...(imported
          ? [
              {
                key: "my-story",
                version: 1,
                title: text("My story", "Meine Story"),
                summary: text("Imported.", "Importiert."),
                author: null,
                chapters: 3,
                origin: "import",
                imported_at: "2026-09-13T08:00:00Z",
                run: null,
              },
            ]
          : []),
      ],
    });
  if (p === "/api/storyline/library" && req.method() === "POST") {
    if (u.searchParams.get("filename") === "broken.yaml")
      return reply(
        {
          detail: "The storyline package did not validate.",
          errors: [
            { path: "chapters[0].command", code: "unknown_command", detail: "no_such_command" },
            { path: "chapters[0].view", code: "unknown_view", detail: "view:nowhere" },
          ],
        },
        422,
      );
    imported = true;
    return reply(
      {
        key: "my-story",
        version: 1,
        title: text("My story", "Meine Story"),
        chapters: 3,
        warnings: [],
        replaced: false,
      },
      201,
    );
  }
  if (p === "/api/storyline/library/my-story/1" && req.method() === "DELETE") {
    imported = false;
    return route.fulfill({ status: 204, body: "" });
  }
  if (p === "/api/storyline/runs" && req.method() === "POST") {
    started = true;
    return reply({
      run_id: "run-1",
      tenant_id: "story",
      status: "active",
      key: "order-to-close",
      version: 1,
      error: null,
      current_chapter: "order",
    });
  }
  if (p === "/api/tenants/plain/storyline")
    return reply({ detail: "This company has no storyline run." }, 404);
  if (p === "/api/tenants/story/storyline")
    return reply({
      run_id: "run-1",
      tenant_id: "story",
      status: "active",
      key: "order-to-close",
      version: 1,
      title: text("Order to close", "Auftrag bis Abschluss"),
      chapters: chapters(),
      current_chapter: phase === "done" ? "reference" : "order",
      branches: {},
      start: "2026-09-12T09:00:00Z",
    });
  if (p === "/api/tenants/story/storyline/chapters/order")
    return reply({
      chapter: {
        key: "order",
        kind: "command",
        title: text("Create the order", "Auftrag anlegen"),
        situation: text(
          "Nordlicht orders 12 mugs. Create the order.",
          "Nordlicht bestellt 12 Becher. Leg den Auftrag an.",
        ),
        explain: text("One command, several events.", "Ein Befehl, mehrere Ereignisse."),
        view: "view:orders",
        command: "order_create",
        input: { direction: "sales" },
        context: {},
        reads: [],
        primary: { record_type: "commitment", from: "output.commitment_ids[0]" },
        expect: { raised: ["outgoing_commitment_at_risk"], cleared: [], facts: [] },
        next: "reference",
        branches: [],
      },
      status: phase === "done" ? "done" : "current",
      preconditions: [{ kind: "reference", name: "$ref.parties.nordlicht", holds: true }],
      can_run: phase !== "done",
      step: step(),
    });
  if (p === "/api/tenants/story/storyline/chapters/reference")
    return reply({
      chapter: {
        key: "reference",
        kind: "command",
        title: text("Note the customer reference", "Kundenreferenz festhalten"),
        situation: text("Record PO-2026-118 as a Fact.", "Halte PO-2026-118 als Fakt fest."),
        explain: text(
          "A Fact is what Reality holds to be true.",
          "Ein Fakt ist, was Reality für wahr hält.",
        ),
        view: "view:documents",
        command: "fact_observe",
        input: {},
        context: {},
        reads: [],
        primary: null,
        expect: { raised: [], cleared: [], facts: ["order.customer_reference"] },
        next: "review",
        branches: [],
      },
      status: phase === "done" ? "current" : "upcoming",
      preconditions: blocked
        ? [{ kind: "finding_present", name: "overdue_receivable", holds: false }]
        : [],
      can_run: phase === "done" && !blocked,
      step: null,
    });
  if (p === "/api/tenants/story/storyline/restart") {
    restarted = true;
    blocked = false;
    return reply({
      run_id: "run-2",
      tenant_id: "story-2",
      status: "active",
      key: "order-to-close",
      version: 1,
      error: null,
      current_chapter: "order",
    });
  }
  if (p === "/api/tenants/story/storyline/chapters/order/prepare") {
    phase = "pending";
    return reply(step());
  }
  if (p === "/api/tenants/story/storyline/chapters/order/confirm") {
    const body = req.postDataJSON();
    assert.equal(body.confirmed, true);
    assert.equal(body.preview_revision, "rev-1");
    phase = "done";
    return reply(step());
  }
  if (p === "/api/tenants/story/storyline/trace")
    return reply({
      items:
        u.searchParams.get("free") === "true"
          ? freeTrace()
          : u.searchParams.get("step_id")
            ? trace()
            : [],
      has_more: false,
    });
  if (p === "/api/tenants/story/storyline/delta") {
    deltaQueries.push(u.search);
    if (u.searchParams.get("ordinal") === "8")
      return reply({
        ...delta,
        range: { ...delta.range, after_sequence: 20, latest_sequence: 21 },
        events: [delta.events[0]],
        facts: [],
        records: [{ record_type: "reservation", record_id: "res_free000001" }],
        exceptions: { raised: [], cleared: delta.exceptions.raised },
        graph: { nodes: [], edges: [] },
      });
    if (u.searchParams.get("ordinal")) return reply({ detail: "No marker" }, 404);
    return reply(delta);
  }
  if (p.startsWith("/api/tenants/story/storyline/tool-reference/"))
    return reply({
      key: "order_create",
      kind: "command",
      label: text("Create order", "Auftrag anlegen"),
      description: "Records a manual order as Source and Document Evidence.",
      access: "confirm",
      parameters: [
        { name: "direction", type: "string", required: true, description: "" },
        { name: "lines", type: "array", required: true, description: "" },
      ],
      projections: ["document", "commitment"],
      docs_path: "/tool-usage/commands#command-order_create",
    });
  if (p.endsWith("/evidence-documents"))
    return reply({
      items: [
        {
          id: "doc_old00000001",
          type: "sales_order",
          number: "AT-0040",
          party: "Nordlicht Handels GmbH",
          gross_amount: "612.50",
        },
        ...(phase === "done"
          ? [
              {
                id: "doc_new0000001",
                type: "sales_order",
                number: "AT-0041",
                party: "Nordlicht Handels GmbH",
                gross_amount: "294.00",
              },
            ]
          : []),
      ],
      page: { number: 1, size: 50, total: 1, pages: 1, has_previous: false, has_next: false },
    });
  return reply({ detail: "Fixture unavailable" }, 404);
});

// 1. A company without a run shows the library; import refuses a bad file with every
// error, accepts a good one, and removes it again; download is a plain link.
async function assertContainedScroll() {
  for (const [width, height] of [
    [1440, 900],
    [390, 640],
    [1440, 500],
  ]) {
    await page.setViewportSize({ width, height });
    const list = page.locator("[data-independent-free-play] [data-chat-messages]");
    const header = page.locator("[data-independent-free-play] > header");
    const input = page.locator("[data-independent-free-play] textarea");
    await list.evaluate((node) => {
      node.scrollTop = 0;
    });
    const headerBefore = await header.boundingBox();
    assert.ok(headerBefore.height <= (width < 1280 ? 44 : 0), "Chat has no desktop toolbar");
    assert.equal(await header.locator("h2, [data-chat-usage]").count(), 0);
    assert.equal(
      await page.locator("[data-independent-free-play] .reality-chat > header").count(),
      0,
    );
    if (width < 1280)
      await header.getByRole("button", { name: "Conversation history", exact: true }).waitFor();
    else {
      assert.equal(
        await page
          .locator("[data-free-play-toolbar]")
          .getByRole("button", { name: "Conversation history", exact: true })
          .isVisible(),
        false,
      );
      const sessions = await page.locator("[data-free-play-sessions]").boundingBox();
      const chat = await page.locator("[data-independent-free-play]").boundingBox();
      assert.ok(sessions.x + sessions.width <= chat.x, "sessions are left of chat");
    }
    assert.equal(
      await page.locator("[data-independent-free-play] select[aria-label='Conversation']").count(),
      0,
    );
    assert.equal(
      await header.getByRole("button", { name: "Back to selection", exact: true }).count(),
      0,
    );
    assert.equal(
      await header.getByRole("button", { name: "New conversation", exact: true }).count(),
      0,
    );
    assert.equal(
      await page
        .locator("[data-free-play-sessions]")
        .getByRole("button", { name: "New conversation", exact: true, includeHidden: true })
        .count(),
      1,
    );
    assert.equal(
      await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
      false,
    );
    const inputBefore = await input.boundingBox();
    assert.ok(inputBefore.y + inputBefore.height <= height, "composer stays in viewport");
    assert.equal(
      await page.evaluate(() => document.documentElement.scrollHeight > innerHeight),
      false,
    );
    const box = await list.boundingBox();
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.wheel(0, 700);
    await page.waitForFunction(
      () =>
        document.querySelector("[data-independent-free-play] [data-chat-messages]").scrollTop > 0,
    );
    assert.equal((await header.boundingBox()).y, headerBefore.y);
    assert.equal((await input.boundingBox()).y, inputBefore.y);
    assert.equal(await page.evaluate(() => scrollY), 0);
    await list.evaluate((node) => {
      node.scrollTop = node.scrollHeight;
    });
    await page.mouse.wheel(0, 1200);
    assert.equal(await page.evaluate(() => scrollY), 0);
    await page.screenshot({ path: `/private/tmp/compact-chat-${width}-${height}.png` });
  }
}
async function assertMainCompanyFreePlay() {
  await page.setViewportSize({ width: 1440, height: 900 });
  independentCreated = true;
  started = true;
  independentSession ||= { id: "independent-chat", title: "Independent chat" };
  const before = writes.length;
  await page.goto(`${base}/app/storyline?tenant=story&chapter=library`);
  await page.locator("[data-storyline-library]").waitFor();
  assert.equal(await page.locator("[data-free-play-entry]").count(), 0);
  const navigation = page.locator("a[data-navigation-item]");
  assert.deepEqual(
    (await navigation.allTextContents()).slice(0, 2).map((text) => text.trim()),
    ["Home", "Chat"],
  );
  await page.getByRole("link", { name: "Chat", exact: true }).click();
  await page.waitForURL(/\/app\/chat/);
  assert.equal(
    await page.getByRole("link", { name: "Chat", exact: true }).getAttribute("aria-current"),
    "page",
  );
  assert.equal(
    await page
      .locator('a[data-navigation-item][href*="/app/storyline"]')
      .getAttribute("aria-current"),
    null,
  );
  const input = page.locator("[data-independent-free-play] textarea");
  await input.waitFor();
  assert.match(page.url(), /tenant=story/);
  assert.equal(
    await page
      .locator(
        "[data-free-play-company], [data-free-play-start], [data-free-play-choose], [data-free-play-open]",
      )
      .count(),
    0,
  );
  assert.equal(
    await page
      .locator("[data-independent-free-play]")
      .getByRole("button", { name: "Storylines", exact: true })
      .count(),
    0,
  );
  const switchMain = async (id) => {
    await page.getByRole("button", { name: "Switch company", exact: true }).click();
    await page.locator(`[data-company-option="${id}"]`).click();
    await page.waitForURL(new RegExp(`tenant=${id}`));
    await input.waitFor();
    assert.match(page.url(), /\/app\/chat/);
    assert.equal(new URL(page.url()).searchParams.has("session"), false);
    assert.equal(await input.inputValue(), "");
  };
  await input.fill("Unsent story draft");
  await switchMain("plain");
  await page.locator("[data-free-play-real-data]").waitFor();
  await page.locator('[data-chat-evidence="plain-answer"] summary').click();
  await page
    .getByText(
      "Reality did not record which calls produced this reply. The reply itself draws on this company's current data.",
      { exact: true },
    )
    .waitFor();
  await switchMain("independent");
  await page.locator('[data-chat-session="independent-chat"]').click();
  await page.waitForURL(/session=independent-chat/);
  await input.fill("Unsent sandbox draft");
  await switchMain("plain");
  assert.equal(await page.locator('[data-chat-session="independent-chat"]').count(), 0);
  await page.reload();
  await input.waitFor();
  assert.match(page.url(), /tenant=plain/);
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 844 });
    assert.equal(
      await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
      false,
    );
    await page.screenshot({ path: `/private/tmp/free-play-main-company-${width}.png` });
  }
  assert.equal(
    writes.length,
    before,
    "Free Play navigation and global company switching are read-only",
  );
}
if (process.env.FREE_PLAY_COMPANY_ONLY === "1") {
  await page.route("**/api/tenants/plain/copilot?*", async (route) => {
    if (new URL(route.request().url()).searchParams.get("session_id") !== "missing")
      return route.fallback();
    return route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ detail: "ChatSession not found." }),
    });
  });
  await page.goto(`${base}/app/chat?tenant=plain&session=missing`);

  await page.locator("[data-independent-free-play] textarea").waitFor();
  assert.equal(new URL(page.url()).searchParams.has("session"), false);

  assert.equal(await page.getByText("ChatSession not found.", { exact: true }).count(), 0);
  await page.reload();
  await page.locator("[data-independent-free-play] textarea").waitFor();
  await page.route("**/api/tenants/plain/copilot?*", async (route) => {
    if (new URL(route.request().url()).searchParams.get("session_id") !== "unavailable")
      return route.fallback();
    return route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Temporarily unavailable" }),
    });
  });
  await page.goto(`${base}/app/chat?tenant=plain&session=unavailable`);
  await page
    .locator("#main-content")
    .getByText("Temporarily unavailable", { exact: true })
    .waitFor();
  assert.equal(new URL(page.url()).searchParams.get("session"), "unavailable");
  await assertMainCompanyFreePlay();
  assert.deepEqual(errors, []);
  await browser.close();
  console.log(
    "PASS: direct Free Play entry, global company switch, cleared draft/session/evidence, reload and responsive layout without creation",
  );
  process.exit(0);
}
if (process.env.FREE_PLAY_SCROLL_ONLY === "1") {
  independentCreated = true;
  independentSession = { id: "independent-chat", title: "Independent chat" };
  independentMessages.push(
    ...Array.from({ length: 24 }, (_, index) => ({
      id: `scroll-${index}`,
      role: "user",
      content: "Earlier Sandbox question. ".repeat(20),
      created_at: "2026-09-15T09:00:00Z",
    })),
  );
  await page.goto(`${base}/app/free-play?tenant=independent&play=chat`);
  await page.locator("[data-independent-free-play] textarea").waitFor();
  await page.setViewportSize({ width: 390, height: 640 });
  const historyToggle = page
    .locator("[data-free-play-toolbar]")
    .getByRole("button", { name: "Conversation history", exact: true });
  await historyToggle.click();
  assert.equal(await historyToggle.getAttribute("aria-expanded"), "true");
  await page
    .locator("[data-free-play-sessions]")
    .getByRole("button", { name: "Close", exact: true })
    .click();
  assert.equal(await historyToggle.getAttribute("aria-expanded"), "false");
  await historyToggle.click();
  await page.keyboard.press("Escape");
  assert.equal(await historyToggle.getAttribute("aria-expanded"), "false");
  assert.equal(await historyToggle.evaluate((el) => document.activeElement === el), true);
  await historyToggle.click();
  await page.locator("[data-chat-session='older-chat']").click();
  await page
    .locator("[data-independent-free-play]")
    .getByText("Earlier session content.", { exact: true })
    .waitFor();
  assert.equal(await historyToggle.getAttribute("aria-expanded"), "false");
  await historyToggle.click();
  await page.locator("[data-chat-session='independent-chat']").click();
  await page
    .locator("[data-chat-session='independent-chat'][aria-current='true']")
    .waitFor({ state: "attached" });

  await assertContainedScroll();
  independentRemaining = 0;
  await page.setViewportSize({ width: 390, height: 640 });
  await page.reload();
  const limit = page.locator("[data-free-play-limit]");
  await limit.waitFor();
  assert.match(await limit.innerText(), /2099/);
  assert.equal(await page.locator("[data-independent-free-play] textarea").count(), 0);
  assert.ok((await limit.boundingBox()).height < 90);
  await page.screenshot({ path: "/private/tmp/free-play-exhausted-mobile.png" });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.screenshot({ path: "/private/tmp/free-play-exhausted-desktop.png" });
  independentRemaining = 18;

  await page.reload();
  await page.locator("[data-independent-free-play] textarea").waitFor();
  independentMessages.length = 0;
  const createsBefore = independentSessionCreates;
  const newChat = page
    .locator("[data-free-play-sessions]")
    .getByRole("button", { name: "New conversation", exact: true });
  await Promise.all([
    page.waitForResponse(
      (response) =>
        response.url().endsWith("/copilot/sessions") &&
        response.request().method() === "POST" &&
        response.status() === 200,
    ),
    newChat.click(),
  ]);
  assert.equal(independentSessionCreates, createsBefore + 1);
  await page.reload();
  const empty = page.locator("[data-independent-free-play] .reality-chat-empty");
  await empty.waitFor();
  const area = await page
    .locator("[data-independent-free-play] [data-chat-messages]")
    .boundingBox();
  const greeting = await empty.boundingBox();
  assert.ok(Math.abs(greeting.y + greeting.height / 2 - area.y - area.height / 2) < 3);
  const main = await page.locator("#main-content").boundingBox();
  const layout = await page.locator("[data-free-play-layout]").boundingBox();
  assert.equal(main.x, layout.x);
  assert.equal(main.y, layout.y);
  await page.locator("[data-free-play-sessions] [data-chat-usage] button").first().click();
  await page.getByRole("dialog", { name: "Usage", exact: true }).waitFor();
  await page.waitForFunction(() => {
    const dialog = document
      .querySelector("[data-free-play-sessions] [role=dialog]")
      .getBoundingClientRect();
    return dialog.top >= 0 && dialog.bottom <= innerHeight;
  });
  await page.keyboard.press("Escape");
  await page.screenshot({ path: "/private/tmp/chat-empty-desktop.png" });
  assert.equal(await page.evaluate(() => scrollY), 0);
  assert.deepEqual(errors, []);
  await browser.close();
  console.log(
    "PASS: long-history scroll remains within Free Play at desktop, mobile and short heights; header/composer geometry, document boundaries and reload stay stable.",
  );
  process.exit(0);
}
await page.goto(`${base}/app/storyline?tenant=plain`);
await page.locator("[data-storyline-library]").waitFor();
assert.match(
  await page.locator("[data-storyline-download='order-to-close']").getAttribute("href"),
  /\/api\/storyline\/library\/order-to-close\/1\?download=yaml$/,
);
// Import is a secondary entrance behind one button, not a form on the page.
assert.equal(await page.locator("#storyline-import-file").count(), 0);
await page.locator("[data-storyline-action='import']").click();
await page.locator("#storyline-import-file").setInputFiles({
  name: "broken.yaml",
  mimeType: "application/yaml",
  buffer: Buffer.from("key: broken\ncommand: no_such_command\n"),
});
await page.locator("[data-storyline-import-problems] li").nth(1).waitFor();
assert.equal(await page.locator("[data-storyline-import-problems] li").count(), 2);
await page.locator("#storyline-import-file").setInputFiles({
  name: "my-story.storyline.yaml",
  mimeType: "application/yaml",
  buffer: Buffer.from("key: my-story\n"),
});
await page.locator("[data-storyline-item='my-story']").waitFor();
await page.locator("[data-storyline-item='my-story'] [data-storyline-menu] > summary").click();
await page.locator("[data-storyline-remove='my-story']").click();
await page.locator("[data-storyline-item='my-story']").waitFor({ state: "detached" });
assert.equal(await page.locator("[data-storyline-free='order-to-close']").count(), 0);
await page.locator("[data-storyline-start='order-to-close']").click();
await page.locator("[data-storyline-page]").waitFor();
assert.match(page.url(), /tenant=story/);

// 2. Chapter 1: prepare shows a preview and nothing else happened.
await page.locator("[data-storyline-current-chapter='order']").waitFor();
assert.equal(await page.locator("[data-storyline-chapter]").count(), 3);
// The list is folded away in the header; opened, it still marks the current chapter.
await openChapters();
await page.locator("[data-storyline-chapter='order'][aria-current='step']").waitFor();
await page.keyboard.press("Escape");
await page.locator("[data-storyline-action='prepare']").click();
await page.locator("[data-storyline-preview]").waitFor();
assert.deepEqual(
  writes.filter((w) => !w.includes("/storyline")),
  [],
);
assert.equal(await page.locator("[data-storyline-call='propose']").count(), 1);

// 3. Confirm goes through the storyline route; protocol, delta and stage react.
await page.locator("[data-storyline-action='confirm']").click();
await page.locator("[data-storyline-explain]").waitFor();
assert.ok(writes.includes("/api/tenants/story/storyline/chapters/order/confirm"));
assert.equal(
  writes.some((w) => w.includes("/change-proposals")),
  false,
  "no ordinary confirm",
);
await page.locator("[data-storyline-call='confirm']").waitFor();
await page
  .locator("[data-storyline-delta]")
  .getByText("outgoing_commitment_at_risk")
  .waitFor()
  .catch(() => {});
await page.locator("[data-storyline-delta]").getByText("Customer commitment at risk").waitFor();
await page.locator("[data-storyline-row-new='true']").waitFor();
await page.locator("[data-storyline-expectations]").getByText("✓").first().waitFor();
await page.locator("[data-storyline-graph]").waitFor();

// 4. A call expands to its catalog explanation with a docs link.
await page.locator("[data-storyline-call='confirm'] summary").click();
await page.locator("[data-storyline-reference]").waitFor();
const docs = await page.locator("[data-storyline-reference] a").getAttribute("href");
assert.match(docs, /\/tool-usage\/commands\?lang=en#command-order_create$/);

// 5. A delta record opens its ordinary surface; the story continues at the next chapter.
await page.locator("[data-storyline-delta] button", { hasText: "commitment" }).first().click();
await page.waitForURL(/\/app\/inspector/);
await page.goBack();
await page.locator("[data-storyline-page]").waitFor();
await page.locator("[data-storyline-action='next']").click();
await page.locator("[data-storyline-current-chapter='reference']").waitFor();

// 5b. A reload resumes at the current chapter; an earlier chapter is read-only, and a
// finding of its delta opens the Exceptions page (FR-008, FR-009).
await page.goto(`${base}/app/storyline?tenant=story`);
await page.locator("[data-storyline-current-chapter='reference']").waitFor();
assert.equal(await page.locator("[data-storyline-action='prepare']").count(), 1);
await openChapters();
await page.locator("[data-storyline-chapter='order']").click();
await page.locator("[data-storyline-explain]").waitFor();
assert.equal(await page.locator("[data-storyline-action='prepare']").count(), 0);
assert.equal(await page.locator("[data-storyline-call]").count(), 2);
await page
  .locator("[data-storyline-delta] button", { hasText: "Customer commitment at risk" })
  .click();
await page.waitForURL(/\/app\/attention\?.*exception=exc__outgoing_commitment_at_risk/);
await page.goBack();
await page.locator("[data-storyline-page]").waitFor();

// 7. Free play: the calls made outside the story are listed, a confirmed one shows what
// it added, and "Back to the story" returns to the current chapter (FR-011).
assert.equal(await page.locator("[data-storyline-action='free-play']").count(), 0);
const beforeSelection = writes.length;
const returnToSelection = page.locator("[data-storyline-action='library']");
assert.equal(await returnToSelection.innerText(), "Back to selection");
await returnToSelection.click();
await page.locator("[data-storyline-library]").waitFor();
assert.equal(writes.length, beforeSelection, "returning to selection is read-only");
await page.goto(`${base}/app/storyline?tenant=story&chapter=free`);
await page.waitForURL(/chapter=free/);
await page
  .locator("[data-storyline-protocol][data-mode='free'] [data-storyline-call='confirm']")
  .waitFor();
assert.equal(await page.locator("[data-storyline-call]").count(), 2);
assert.equal(await page.locator("[data-storyline-action='prepare']").count(), 0);
await page.locator("[data-storyline-call='confirm'] summary").click();
await page.locator("[data-storyline-action='pick-call']").click();
await page
  .locator("[data-storyline-delta] button", { hasText: "Customer commitment at risk" })
  .waitFor();
assert.ok(deltaQueries.includes("?ordinal=8"), `delta queries: ${deltaQueries.join(" ")}`);
await page.locator("[data-storyline-action='back-to-story']").click();
await page.locator("[data-storyline-current-chapter='reference']").waitFor();
assert.doesNotMatch(page.url(), /chapter=free/);

// 8. A chapter whose precondition no longer holds names what is missing and offers a
// fresh company; the restart opens the new company at its first chapter (FR-011, FR-012).
blocked = true;
await page.goto(`${base}/app/storyline?tenant=story&chapter=reference`);
await page.locator("[data-storyline-missing]").waitFor();
assert.match(await page.locator("[data-storyline-missing]").innerText(), /overdue_receivable/);
assert.equal(await page.locator("[data-storyline-action='prepare']").count(), 0);
await page.locator("[data-storyline-actions] [data-storyline-action='restart']").click();
await page.waitForURL(/tenant=story-2/);
await page.locator("[data-storyline-current-chapter='reference']").waitFor();
assert.ok(writes.includes("/api/tenants/story/storyline/restart"));

// 9. Presentation mode (FR-013, SC-003): the timed run issues the same ordered chapter
// calls as the run by hand; any click pauses it; a language switch while it is paused
// re-renders the texts and changes nothing in the trace; an error pauses it too.
const chapterCalls = (list) =>
  list.filter((w) => w.includes("/storyline/chapters/") || w.endsWith("/storyline/branches"));
const byHand = chapterCalls(writes).map((w) => w.replace("/tenants/story-2/", "/tenants/story/"));
assert.deepEqual(byHand, [
  "/api/tenants/story/storyline/chapters/order/prepare",
  "/api/tenants/story/storyline/chapters/order/confirm",
]);
phase = "idle";
const timedFrom = writes.length;
await page.goto(`${base}/app/storyline?tenant=story`);
await page.locator("[data-storyline-current-chapter='order']").waitFor();
await page.evaluate(() => sessionStorage.setItem("storyline.pace", "60000"));
await page.locator("[data-storyline-action='present']").click();
await page.locator("[data-storyline-presentation='playing']").waitFor();
// The bar says what comes next and fills over the wait.
await page.locator("[data-storyline-autoplay-progress='prepare'] .storyline-fill").waitFor();
// A click anywhere outside the autoplay control switches it off before anything was called.
await openChapters();
await page.locator("[data-storyline-presentation='off']").waitFor();
await page.locator("[data-storyline-chapter='review']").click();
assert.deepEqual(chapterCalls(writes.slice(timedFrom)), []);
// The presenter switches the language while paused: texts change, the trace does not.
await page.goto(`${base}/app/settings?tenant=story&settings_view=personal`);
await page.locator("select[name='language']").selectOption("de");
await page.getByRole("button", { name: "Save preferences" }).click();
// The confirmation already renders in the new language; the fixture saw the save.
for (let waited = 0; profileSaves.length === 0 && waited < 100; waited += 1)
  await new Promise((resolve) => setTimeout(resolve, 100));
assert.deepEqual(profileSaves, ["de"]);
await page.locator("select[name='language']").waitFor();
// Home entry keeps TrialEntry mounted while navigating into Storyline.
enterThroughHome = true;
await page.goto(`${base}/app`);
await page.locator("a[href*='/app/storyline']").first().click();
await page.locator("[data-storyline-library]").waitFor();
await page.locator("[data-storyline-start='order-to-close']").click();
await openChapters();
await page.locator("[data-storyline-chapter='order']", { hasText: "Auftrag anlegen" }).waitFor();
await page.keyboard.press("Escape");
const readsBeforeAutoplay = entryReads;
assert.deepEqual(chapterCalls(writes.slice(timedFrom)), []);
// Resumed at a fast pace, the run prepares, confirms and advances on its own, and it
// pauses on the first chapter the fixture cannot prepare instead of retrying.
await page.evaluate(() => sessionStorage.setItem("storyline.pace", "150"));
await page.locator("[data-storyline-action='present']").click();
await page.locator("[data-storyline-current-chapter='reference']").waitFor();
await page
  .locator("[data-storyline-presentation='off'][data-storyline-presentation-note]")
  .waitFor();
assert.ok(entryReads > readsBeforeAutoplay, "completed steps refresh trial entry");
enterThroughHome = false;
const timed = chapterCalls(writes.slice(timedFrom));
assert.deepEqual(timed.slice(0, byHand.length), byHand);
assert.deepEqual(timed.slice(byHand.length), [
  "/api/tenants/story/storyline/chapters/reference/prepare",
]);
language = "en";

// 10. Other stories: the library opens from a running story and leads back; it offers the
// run as a storyline draft (a plain link to the draft route) and a fresh start.
await page.goto(`${base}/app/storyline?tenant=story&chapter=order`);
await page.locator("[data-storyline-action='library']").click();
await page.waitForURL(/chapter=library/);
await page
  .locator("[data-storyline-library] [data-storyline-start-over='order-to-close']")
  .waitFor({ state: "attached" });
assert.equal(await page.locator("[data-storyline-free]").count(), 0);
await assertMainCompanyFreePlay();
await page.goto(`${base}/app/storyline?tenant=plain`);
await page.locator("[data-storyline-library]").waitFor();
await page.setViewportSize({ width: 1440, height: 1000 });
await page.screenshot({ path: "/private/tmp/reality-182-browser/library-1440.png" });
await page.setViewportSize({ width: 390, height: 844 });
await page.screenshot({ path: "/private/tmp/reality-182-browser/library-390.png" });
await page.setViewportSize({ width: 1280, height: 900 });
assert.match(
  await page.locator("[data-storyline-draft='order-to-close']").getAttribute("href"),
  /\/api\/storyline\/runs\/run-1\/draft\?format=yaml$/,
);

// 6. Four languages, two widths, light and dark: no overflow, no page errors.
await mkdir("/private/tmp/reality-182-browser", { recursive: true });
for (const lang of ["en", "de", "nl", "es"])
  for (const theme of ["light", "dark"])
    for (const width of [390, 1440]) {
      language = lang;
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      // The language is explicit in the URL: a remembered choice never wins over it.
      await page.goto(`${base}/app/storyline?tenant=story&chapter=order&lang=${lang}`);
      await page.locator("[data-storyline-explain]").waitFor();
      assert.equal(await page.evaluate(() => document.documentElement.lang), lang);
      await page.evaluate(
        (theme) => document.documentElement.setAttribute("data-theme", theme),
        theme,
      );
      const overflow = await page.evaluate(() => ({
        inner: innerWidth,
        scroll: document.documentElement.scrollWidth,
      }));
      assert.ok(
        overflow.scroll <= overflow.inner,
        `overflow ${lang}/${theme}/${width}: ${JSON.stringify(overflow)}`,
      );
      await page.screenshot({
        path: `/private/tmp/reality-182-browser/${lang}-${theme}-${width}.png`,
        animations: "disabled",
      });
    }
// Spec 195: handoff preserves the draft without sending; evidence is reply-specific.
language = "en";
phase = "idle";
await page.setViewportSize({ width: 1440, height: 1000 });
await page.goto(`${base}/app/storyline?tenant=story&chapter=order&lang=en`);
await page.locator("[data-storyline-say]").fill("What is still open in this Sandbox?");
const beforeDraft = writes.length;
await page.locator("[data-storyline-action='own-words']").click();
await page.waitForURL(/chapter=free/);
const composer = page.locator("[data-storyline-free-play] textarea");
await composer.waitFor();
assert.equal(await composer.inputValue(), "What is still open in this Sandbox?");
assert.equal(writes.length, beforeDraft, "handoff must not send or mutate");
await composer.fill("Show the open findings, please.");
await composer.press("Enter");
await page.locator('[data-chat-evidence="answer-free"]').waitFor();
await page.waitForFunction(
  () => document.activeElement === document.querySelector("[data-storyline-free-play] textarea"),
);
assert.equal(chatSends.length, 1, "one explicit send creates one request");
assert.equal(chatSends[0].message, "Show the open findings, please.");
assert.equal(evidenceReads.length, 0, "evidence is loaded on demand");
await page.locator('[data-chat-evidence="answer-free"] > summary').click();
await page.locator('[data-chat-evidence="answer-free"] [data-storyline-call="read"]').waitFor();
assert.equal(
  await page.locator('[data-chat-evidence="answer-free"] [data-storyline-call]').count(),
  1,
);
await page.reload();
await page.locator('[data-chat-evidence="answer-free"]').waitFor();
assert.equal(chatSends.length, 1, "reload does not resend");
assert.equal(await composer.inputValue(), "");
for (const lang of ["en", "de", "nl", "es"])
  for (const theme of ["light", "dark"])
    for (const width of [390, 1440]) {
      language = lang;
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      await page.goto(
        `${base}/app/storyline?tenant=story&chapter=free&session=free-chat&lang=${lang}`,
      );
      await composer.waitFor();
      await page.locator('[data-chat-evidence="answer-free"] > summary').click();
      await page
        .locator('[data-chat-evidence="answer-free"] [data-storyline-call="read"]')
        .waitFor();
      await page.evaluate(
        (theme) => document.documentElement.setAttribute("data-theme", theme),
        theme,
      );
      const size = await page.evaluate(() => ({
        inner: innerWidth,
        scroll: document.documentElement.scrollWidth,
      }));
      assert.ok(size.scroll <= size.inner, `Free Play overflow ${lang}/${theme}/${width}`);
      const box = await composer.boundingBox();
      assert.ok(box && box.height > 20 && box.width > 150, "composer remains usable");
      await page.screenshot({
        path: `/private/tmp/reality-182-browser/free-chat-${lang}-${theme}-${width}.png`,
        animations: "disabled",
      });
    }
for (const lang of ["en", "de", "nl", "es"])
  for (const theme of ["light", "dark"])
    for (const width of [390, 1440]) {
      language = lang;
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
      await page.goto(`${base}/app/free-play?tenant=independent&play=chat&lang=${lang}`);
      await page.locator("[data-independent-free-play] textarea").waitFor();
      assert.equal(
        await page
          .locator('[data-independent-free-play] [data-chat-evidence="answer-free"]')
          .count(),
        0,
      );
      await page
        .locator('[data-independent-free-play] [data-chat-evidence="independent-answer"]')
        .waitFor();
      await page.evaluate(
        (theme) => document.documentElement.setAttribute("data-theme", theme),
        theme,
      );
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({
        path: `/private/tmp/reality-182-browser/independent-${lang}-${theme}-${width}.png`,
        animations: "disabled",
      });
    }
assert.deepEqual(errors, []);
console.log(
  "Storyline browser passed: library import/download/remove, start, prepare/confirm through the storyline route, protocol, delta, stage marks, docs link, record link, next chapter, resume and read-only chapter, finding link, free play with its own delta, blocked chapter and restart, presentation run with the same calls as by hand, pause on click, language switch while paused, draft link, 48 localized layouts, independent Free Play creation/chat/reopen with separate tenant history, contextual chat draft/send/reload and per-reply evidence.",
);
await browser.close();

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const docsRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const contentRoot = path.join(docsRoot, "content");
const repositoryRoot = path.resolve(docsRoot, "..", "..");
const translatedLocales = ["de"];

test("operational recap emphasizes record types rather than calculated balances", () => {
  for (const locale of ["", "de/"]) {
    const chapter = fs.readFileSync(
      path.join(contentRoot, locale, "concepts/business-reality-guide/05-one-order-end-to-end.md"),
      "utf8",
    );
    const section = chapter.split("## 2.")[1].split("## 3.")[0];
    for (const term of ["SourceRecord", "Document", "DocumentLine", "Movement", "Reservation"])
      assert.ok(section.includes(`**${term}**`), term);
    assert.match(section, /\*\*(?:Kunden-)?Commitment\*\*/u);
    assert.doesNotMatch(section, /\*\*(?:available|verfügbar|open|offen|physical|physisch)\b/iu);
  }
});

test("closing agent recap is bilingual, linked and honest about its illustrative scope", () => {
  const slug = "05-one-order-end-to-end";
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress/config.mts"), "utf8");
  assert.ok(config.includes(`"${slug}"`));
  for (const locale of ["", "de/"]) {
    const chapter = fs.readFileSync(
      path.join(contentRoot, locale, `concepts/business-reality-guide/${slug}.md`),
      "utf8",
    );
    const overview = fs.readFileSync(
      path.join(contentRoot, locale, "concepts/business-reality-guide.md"),
      "utf8",
    );
    const previous = fs.readFileSync(
      path.join(
        contentRoot,
        locale,
        "concepts/business-reality-guide/04-working-as-process-owner.md",
      ),
      "utf8",
    );
    assert.ok(overview.includes(slug));
    assert.ok(previous.includes(slug));
    for (const term of [
      "Reality-Timeline",
      "Huber",
      "SettlementAllocation",
      "870",
      "970",
      locale ? "1.470" : "1,470",
      "Fact",
      "SourceRecord",
    ])
      assert.ok(chapter.includes(term), term);
    assert.match(chapter, /not a live agent response|keine echte Agentenantwort/u);
    assert.match(chapter, /INV-1001/u);
    assert.match(chapter.replace(/\s+/gu, " "), /not automatically|nicht automatisch/u);
    assert.match(chapter, /due date|Fälligkeit/u);
    assert.match(
      chapter.replace(/\s+/gu, " "),
      /not part of this base sequence|nicht zu diesem Grundablauf/u,
    );
  }
});

test("inventory walkthrough separates explicit records, automatic effects and derived balances", () => {
  for (const locale of ["", "de/"]) {
    const text = fs.readFileSync(
      path.join(
        contentRoot,
        locale,
        "concepts/business-reality-guide/02-orders-stock-and-deliveries.md",
      ),
      "utf8",
    );
    for (const term of ["SO-1001", "PO-2001", "Huber", "LightWorks", "30", "22"])
      assert.ok(text.includes(term), `Missing shared order context: ${term}`);
    const prose = text.replace(/\s+/gu, " ");
    assert.match(prose, /explicit reservation action|ausdrückliche Reservierungsaktion/u);
    assert.match(prose, /calculated balances|berechnete Salden/u);
    assert.match(
      prose,
      /does not automatically create a purchase order|erzeugt nicht automatisch eine Bestellung/u,
    );
    assert.match(prose, /no Reservation is created|keine Reservation angelegt/u);
    assert.match(prose, /does not move goods|bewegt keine Ware/u);
  }
});

test("original timed learning paths retain model, operator and integration progression", () => {
  for (const locale of ["", "de/"]) {
    const home = fs.readFileSync(path.join(contentRoot, locale, "index.md"), "utf8");
    for (const minutes of [15, 30, 60])
      assert.ok(home.includes(`${minutes} ${locale ? "Minuten" : "minutes"}`));
    for (const target of [
      "concepts/business-reality-guide/01-from-erp-documents-to-business-reality",
      "concepts/business-reality-guide/04-working-as-process-owner",
      "integrations/customization",
      "integrations/order-example",
    ])
      assert.ok(home.includes(target), target);
    assert.match(home, /learning time|Lernzeit/u);
    assert.doesNotMatch(home, /60 minutes — connect an ERP|60 Minuten – ein ERP anbinden/u);
    const journey = fs.readFileSync(
      path.join(contentRoot, locale, "getting-started/index.md"),
      "utf8",
    );
    assert.match(journey, /30-minute learning path|30-Minuten-Lernreise/u);
  }
});

test("the original product journey retains a bounded illustrative case", () => {
  const home = fs.readFileSync(path.join(contentRoot, "index.md"), "utf8");
  const journey = fs.readFileSync(path.join(contentRoot, "getting-started/index.md"), "utf8");
  const trace = fs.readFileSync(path.join(contentRoot, "getting-started/first-trace.md"), "utf8");
  for (const text of ["Three learning paths", "Other paths", "Process Owners"])
    assert.ok(home.includes(text), text);
  for (const text of ["10 lamps", "4 shipped", "6 still", "2 reserved", "4 not yet reserved"])
    assert.ok(journey.includes(text), text);
  assert.match(journey, /Illustrative example/u);
  assert.match(trace, /SettlementAllocation/u);
  assert.match(trace.replace(/\s+/gu, " "), /missing evidence/iu);
});

test("missing-information guidance separates facts, warnings and actions", () => {
  const guidance = fs.readFileSync(
    path.join(contentRoot, "concepts/business-reality-guide/06-facts-and-open-questions.md"),
    "utf8",
  );
  for (const text of [
    "Open questions",
    "owner",
    "simulate",
    "activate",
    "replay",
    "Exception",
    "does not authorize",
  ])
    assert.ok(guidance.toLowerCase().includes(text.toLowerCase()), text);
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress/config.mts"), "utf8");
  assert.match(config, /06-facts-and-open-questions/u);
  for (const relative of ["concepts/business-reality-guide.md", "integrations/customization.md"])
    assert.match(
      fs.readFileSync(path.join(contentRoot, relative), "utf8"),
      /facts-and-open-questions|missing-information/u,
    );
});

const requiredAreas = [
  ["First product journey", "getting-started/index.md"],
  ["Reality for ERP professionals", "concepts/business-reality-guide.md"],
  ["Get started", "getting-started/index.md"],
  ["Agents", "agent-playbooks/index.md"],
  ["API and agent interfaces", "api-tools/index.md"],
  ["Installation & Operations", "operations/index.md"],
  ["Reality Core Development", "development/index.md"],
  ["Tool Usage", "tool-usage/index.md"],
  ["Storylines", "storylines/index.md"],
  ["Reference", "reference/index.md"],
];

const markdownFiles = (directory) =>
  fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const target = path.join(directory, entry.name);
    return entry.isDirectory() ? markdownFiles(target) : target.endsWith(".md") ? [target] : [];
  });

test("content inventory covers the complete reader journey", () => {
  assert.ok(fs.existsSync(path.join(contentRoot, "index.md")));
  for (const [, relativePath] of requiredAreas) {
    assert.ok(fs.existsSync(path.join(contentRoot, relativePath)), `Missing ${relativePath}`);
  }

  const content = markdownFiles(contentRoot)
    .map((file) => fs.readFileSync(file, "utf8"))
    .join("\n");
  for (const term of [
    "SourceRecord",
    "DocumentLine",
    "Commitment",
    "Reservation",
    "Movement",
    "LedgerEntry",
    "shortest true links",
    "Operations Cockpit",
    "Business Reality Inspector",
    "Ask Reality",
    "lossless",
    "idempotency",
    "OpenAPI",
  ]) {
    assert.match(content, new RegExp(term), `Missing required topic: ${term}`);
  }
});

test("navigation and search expose all required areas", () => {
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  assert.match(config, /provider:\s*["']local["']/u);
  assert.match(config, /outline:\s*\{\s*level:\s*\[2,\s*3\]/u);
  for (const [label] of requiredAreas) assert.match(config, new RegExp(`"${label}"`));
  for (const route of [
    "/tool-usage/",
    "/concepts/business-reality-guide",
    "/api-tools/connect-mcp",
  ]) {
    assert.ok(config.includes(route), `Missing navigation route: ${route}`);
  }
});

test("configuration exposes every product language with localized theme and search copy", () => {
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  for (const marker of [
    'label: "English"',
    'lang: "en-GB"',
    'label: "Deutsch"',
    'lang: "de-DE"',
    "themeConfig: localeTheme.root",
    "themeConfig: localeTheme.de",
    "searchLocales",
    "i18nRouting",
  ]) {
    assert.ok(config.includes(marker), `Missing locale configuration: ${marker}`);
  }
});

test("translated locales mirror the canonical Markdown page inventory", () => {
  const canonical = markdownFiles(contentRoot)
    .map((file) => path.relative(contentRoot, file))
    .filter((file) => !translatedLocales.some((locale) => file.startsWith(`${locale}/`)))
    .sort();
  for (const locale of translatedLocales) {
    const localizedRoot = path.join(contentRoot, locale);
    assert.ok(fs.existsSync(localizedRoot), `Missing locale directory: ${locale}`);
    const localized = markdownFiles(localizedRoot)
      .map((file) => path.relative(localizedRoot, file))
      .sort();
    assert.deepEqual(localized, canonical, `Page inventory differs for locale ${locale}`);
    for (const relativePath of canonical) {
      assert.notEqual(
        fs.readFileSync(path.join(localizedRoot, relativePath), "utf8"),
        fs.readFileSync(path.join(contentRoot, relativePath), "utf8"),
        `Localized page is unchanged English content: ${locale}/${relativePath}`,
      );
    }
  }
});

test("translated pages preserve Markdown table structure", () => {
  const canonical = markdownFiles(contentRoot).filter(
    (file) => !translatedLocales.some((locale) => file.startsWith(path.join(contentRoot, locale))),
  );
  for (const sourceFile of canonical) {
    const relativePath = path.relative(contentRoot, sourceFile);
    const sourceRows = fs.readFileSync(sourceFile, "utf8").match(/^\|/gmu)?.length || 0;
    for (const locale of translatedLocales) {
      const localizedRows =
        fs.readFileSync(path.join(contentRoot, locale, relativePath), "utf8").match(/^\|/gmu)
          ?.length || 0;
      assert.equal(
        localizedRows,
        sourceRows,
        `Markdown table row count differs for ${locale}/${relativePath}`,
      );
    }
  }
});

test("each translated edition contains native reader and search language markers", () => {
  const markers = {
    de: ["Dokumentation", "Geschäft"],
  };
  for (const locale of translatedLocales) {
    const content = markdownFiles(path.join(contentRoot, locale))
      .map((file) => fs.readFileSync(file, "utf8"))
      .join("\n");
    for (const marker of markers[locale]) {
      assert.match(content, new RegExp(marker, "iu"), `Missing ${locale} marker: ${marker}`);
    }
  }
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  for (const searchLabel of ["Dokumentation durchsuchen"]) {
    assert.ok(config.includes(searchLabel), `Missing localized search label: ${searchLabel}`);
  }
});

test("book-length guide explains the operational model through worked business cases", () => {
  const guideRoot = path.join(contentRoot, "concepts", "business-reality-guide");
  const guide = [
    fs.readFileSync(path.join(contentRoot, "concepts", "business-reality-guide.md"), "utf8"),
    ...fs
      .readdirSync(guideRoot)
      .sort()
      .map((file) => fs.readFileSync(path.join(guideRoot, file), "utf8")),
  ].join("\n");
  assert.equal(fs.readdirSync(guideRoot).filter((file) => file.endsWith(".md")).length, 8);
  for (const term of [
    "From ERP Documents to Business Reality",
    "The Process Owner Role",
    "entering a sales order",
    "partial goods receipt",
    "When an external customer changes an order",
    "Invoice, partial payment and credit",
    "Inventory Cost, DB1 and DB2",
    "DB1 = received net revenue",
    "Unknown is not zero",
    "Exceptions, Approvals and Responsibility",
    "Decision guide",
  ]) {
    assert.match(guide, new RegExp(term, "iu"), `Missing guide chapter: ${term}`);
  }
  const reference = fs.readFileSync(path.join(contentRoot, "reference", "table-map.md"), "utf8");
  for (const term of ["Table map by responsibility", "Common misconceptions"]) {
    assert.match(reference, new RegExp(term), `Missing reference appendix: ${term}`);
  }
  for (const locale of ["", "de/"]) {
    const usage = fs.readFileSync(path.join(contentRoot, locale, "tool-usage", "index.md"), "utf8");
    assert.ok(
      usage.includes("{#how-to-read-the-lists}"),
      `${locale || "en"}: list explanation missing`,
    );
    assert.match(usage, /What is open\?|Was ist offen\?/u);
  }
});

test("the contribution chapter is directly available in both handbook sidebars", () => {
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  assert.match(config, /"Inventory cost, DB1 and DB2"/);
  assert.match(config, /"Bestandskosten, DB1 und DB2"/);
  assert.match(config, /"08-inventory-cost-and-contribution"/);
});

test("ERP handbook explains the complete contribution bridge in both languages", () => {
  const editions = [
    [
      "",
      ["Consumed acquisition cost", "Direct selling cost", "DB2 rate", "Inspect cost basis"],
      ["1,200", "630", "570", "90", "24", "456", "38%"],
    ],
    [
      "de/",
      [
        "Verbrauchte Anschaffungskosten",
        "Direkte Vertriebskosten",
        "DB2-Quote",
        "Kostengrundlage prüfen",
      ],
      ["1.200", "630", "570", "90", "24", "456", "38%"],
    ],
  ];
  for (const [locale, terms, amounts] of editions) {
    const page = fs.readFileSync(
      path.join(
        contentRoot,
        locale,
        "concepts/business-reality-guide/08-inventory-cost-and-contribution.md",
      ),
      "utf8",
    );
    for (const term of terms) assert.ok(page.includes(term), `${locale || "en"}: missing ${term}`);
    for (const amount of amounts)
      assert.ok(page.replace(/\s+/gu, "").includes(amount), `${locale || "en"}: missing ${amount}`);
  }
});

test("the ERP practical book is a first-class navigation section", () => {
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  assert.ok(config.includes('realityGuide: "Reality for ERP professionals"'));
  assert.ok(config.includes('realityGuide: "Reality für ERP-Profis"'));
  assert.ok(config.includes('realityChapters: "Overview"'));
  assert.ok(config.includes('realityChapters: "Überblick"'));
  assert.ok(config.indexOf("text: labels.realityGuide") < config.indexOf("text: labels.toolUsage"));
});

test("the learning journey positions ERP professionals as accountable Process Owners", () => {
  const home = fs.readFileSync(path.join(contentRoot, "index.md"), "utf8");
  const role = fs.readFileSync(
    path.join(contentRoot, "concepts", "business-reality-guide", "04-working-as-process-owner.md"),
    "utf8",
  );
  for (const term of [
    "open reference core",
    "ERP professionals becoming",
    "Three learning paths",
    "What open source means here",
  ]) {
    assert.match(home, new RegExp(term, "iu"), `Missing learning position: ${term}`);
  }
  for (const term of [
    "Process Owner is the accountable business person",
    "governed operating loop",
    "What may be claimed?",
    "Check your understanding",
    "Learning outcome",
  ]) {
    assert.match(role, new RegExp(term, "iu"), `Missing Process Owner lesson: ${term}`);
  }
});

test("technical guidance gives code-grounded ERP extension paths", () => {
  const extensionFiles = [
    "index.md",
    "connectors.md",
    "commands.md",
    "derived-views.md",
    "application-surfaces.md",
  ];
  const developmentRoot = path.join(contentRoot, "development");
  const guidance = extensionFiles
    .map((file) => fs.readFileSync(path.join(developmentRoot, file), "utf8"))
    .join("\n");
  for (const term of [
    "Repository map",
    "Connect an ERP System",
    "Implement Business Operations",
    "Develop Metrics and Operational Warnings",
    "Expose Functions through API and MCP",
    "SOURCE_INTERPRETERS",
    "mutating=True",
    "OPERATIONAL_PROJECTIONS",
    "DERIVATION_REGISTRY",
    "packages/reality-core/src/reality/web/api.py",
  ]) {
    assert.match(guidance, new RegExp(term), `Missing extension guidance: ${term}`);
  }
  assert.ok(fs.existsSync(path.join(contentRoot, "operations", "installation.md")));
  assert.match(
    fs.readFileSync(path.join(contentRoot, "getting-started", "index.md"), "utf8"),
    /operations\/installation/,
  );
});

test("ERP customization separates implementation work from Reality Core development", () => {
  const customization = fs.readFileSync(
    path.join(contentRoot, "integrations", "customization.md"),
    "utf8",
  );
  const example = fs.readFileSync(
    path.join(contentRoot, "integrations", "order-example.md"),
    "utf8",
  );
  for (const term of [
    "What Can Be Adapted?",
    "connector transport and order interpreter",
    "workspace catalog",
    "Reality Core development",
  ]) {
    assert.ok(customization.includes(term), `Missing customization guidance: ${term}`);
  }
  for (const term of [
    "SOURCE_INTERPRETERS",
    "_shopify_interpretation",
    "SourceRecord",
    "outgoing Commitment",
    "fulfillment queue",
  ]) {
    assert.ok(example.includes(term), `Missing end-to-end ERP example: ${term}`);
  }
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  assert.ok(config.includes('development: "Reality-Core-Entwicklung"'));
  assert.match(config, /text: labels\.development,\s+collapsed: true/u);
});

test("ERP professionals can run a truthful parallel pilot before enabling actions", () => {
  for (const locale of ["", "de/"]) {
    const home = fs.readFileSync(path.join(contentRoot, locale, "index.md"), "utf8");
    assert.match(home, /Shopify, Xentral (?:or|oder) Odoo/u);
    assert.match(home, /integrations\/parallel-test/u);
    assert.match(home, /Try it with my ERP|Mit meinem ERP testen/u);
    assert.match(home, /Start Reality alongside my ERP|Reality parallel zu meinem ERP starten/u);
    assert.match(
      home.replace(/\s+/gu, " "),
      /not mean a finished connection|nicht, dass eine fertige Anbindung/u,
    );
  }

  for (const locale of ["", ...translatedLocales]) {
    const guide = fs.readFileSync(
      path.join(contentRoot, locale, "integrations", "parallel-test.md"),
      "utf8",
    );
    for (const term of [
      "Shopify",
      "Xentral",
      "Odoo",
      "source_record_ingest_propose",
      "interpretation_coverage",
      "SOURCE_INTERPRETERS",
      "connector_catalog.yaml",
      "unmapped",
    ]) {
      assert.match(
        guide,
        new RegExp(term, "u"),
        `Missing parallel-test guidance: ${locale}/${term}`,
      );
    }
    assert.match(guide, /Capture|Capture –/u);
    assert.match(guide, /Interpret|Interpret –/u);
    assert.match(guide, /Compare|Compare –/u);
    assert.match(guide, /Act|Act –/u);
    assert.match(guide, /keine ausgehende ERP-Mutation|No outbound ERP mutation/iu);
  }
});

test("the Tool Usage reference is generated, bilingual and written like manual pages", () => {
  const pages = [
    "resources.md",
    "processes.md",
    "commands.md",
    "views.md",
    "exceptions.md",
    "events.md",
  ];
  for (const locale of ["", ...translatedLocales]) {
    const root = path.join(contentRoot, locale, "tool-usage");
    for (const file of pages) {
      const content = fs.readFileSync(path.join(root, file), "utf8");
      assert.match(content, /Automatically generated|Automatisch aus/u);
    }
    const index = fs.readFileSync(path.join(root, "index.md"), "utf8");
    assert.ok(index.includes("<ToolUsage />"), `${locale || "en"}: interactive explorer missing`);
    assert.match(index, /apropos/u);
    for (const file of pages) assert.ok(index.includes(`(./${file.replace(".md", "")})`), file);
  }
  const commands = fs.readFileSync(path.join(contentRoot, "tool-usage", "commands.md"), "utf8");
  for (const term of [
    "## Finance",
    "## Agent tools without a business command",
    "**Synopsis**",
    "**Parameters**",
    "**Reach via:**",
    "**See also:**",
    "{#command-reserve}",
    "{#tool-reservation_propose}",
    "{#tool-proposal_approve_and_execute}",
    "reservation_propose commitment_id [quantity]",
    "shipments_list",
    "shipment_explain",
    "shipment_notice_record_propose",
    "shipment_dispatch_propose",
    "shipment_receive_propose",
    "shipment_event_record_propose",
    "shipment_event_supersede_propose",
    "| Required |",
    "`commitment_id`",
  ]) {
    assert.ok(commands.includes(term), `Missing manual page detail: ${term}`);
  }
  const views = fs.readFileSync(path.join(contentRoot, "tool-usage", "views.md"), "utf8");
  for (const term of [
    "## Workspaces",
    "## Views",
    "## Projections",
    "## Actions",
    "{#view-inventory}",
    "{#projection-inventory}",
    "{#action-reserve_stock}",
    "(./commands#command-reserve)",
  ]) {
    assert.ok(views.includes(term), `Missing views detail: ${term}`);
  }
  const exceptions = fs.readFileSync(path.join(contentRoot, "tool-usage", "exceptions.md"), "utf8");
  assert.ok(exceptions.includes("{#exception-overdue_outgoing_customer_commitment}"));
  assert.ok(exceptions.includes("(./commands#tool-exceptions_list)"));
  assert.ok(
    fs
      .readFileSync(path.join(contentRoot, "tool-usage", "events.md"), "utf8")
      .includes("(./commands#command-record_movement)"),
  );

  const resources = fs.readFileSync(path.join(contentRoot, "tool-usage", "resources.md"), "utf8");
  for (const term of [
    "{#resource-order}",
    "**Lists**",
    "**Actions**",
    "**Exceptions to clear**",
    "(./commands#command-reserve)",
    "(./processes#process-order_to_cash)",
    "Sales orders, purchase orders, reservations and holds",
  ]) {
    assert.ok(resources.includes(term), `Missing resource detail: ${term}`);
  }
  const german = fs.readFileSync(
    path.join(contentRoot, "de", "tool-usage", "resources.md"),
    "utf8",
  );
  for (const term of [
    "## Auftrag",
    "## Geschäftspartner",
    "Zahlungseingang buchen",
    "Offene Posten",
    "Minderzahlung",
    "Kunden, Lieferanten und das eigene Unternehmen",
  ]) {
    assert.ok(german.includes(term), `German resource page lacks ERP wording: ${term}`);
  }
  const processes = fs.readFileSync(path.join(contentRoot, "tool-usage", "processes.md"), "utf8");
  for (const term of [
    "{#process-order_to_cash}",
    "### 1.",
    "(../agent-playbooks/order-to-cash-fulfilment)",
    "**Check afterwards:**",
    "**Can leave behind:**",
  ]) {
    assert.ok(processes.includes(term), `Missing process detail: ${term}`);
  }

  const model = JSON.parse(
    fs.readFileSync(path.join(docsRoot, ".vitepress/data/tool-usage.json"), "utf8"),
  );
  const kinds = new Set(model.entries.map((entry) => entry.kind));
  for (const kind of [
    "command",
    "tool",
    "view",
    "projection",
    "action",
    "exception",
    "event",
    "workspace",
  ]) {
    assert.ok(kinds.has(kind), `Explorer model lacks ${kind} entries`);
  }
  const ids = new Set(model.entries.map((entry) => entry.id));
  for (const entry of model.entries) {
    for (const link of entry.links)
      assert.ok(ids.has(link), `${entry.id} links to unknown ${link}`);
  }
  assert.ok(model.resources.length >= 10);
  assert.ok(model.processes.length >= 4);
  for (const resource of model.resources) {
    for (const field of ["lists", "actions", "reads", "exceptions", "tools", "events"]) {
      for (const id of resource[field]) assert.ok(ids.has(id), `${resource.key}.${field} -> ${id}`);
    }
  }
  const order = model.resources.find((resource) => resource.key === "order");
  assert.ok(order.actions.includes("command:reserve"));
  assert.ok(order.lists.includes("view:orders"));
  for (const entry of model.entries) {
    if (entry.kind !== "workspace")
      assert.ok(entry.resources.length > 0, `${entry.id} has no business resource`);
    if (entry.kind === "command") assert.ok(entry.label_de, `${entry.id} has no German label`);
  }
  const reserve = model.entries.find((entry) => entry.id === "command:reserve");
  assert.ok(reserve.tools.includes("reservation_propose"));
  assert.ok(reserve.links.includes("action:reserve_stock"));
  const tool = model.entries.find((entry) => entry.id === "tool:reservation_propose");
  assert.ok(
    tool.parameters.some((parameter) => parameter.name === "commitment_id" && parameter.required),
  );
  assert.equal(tool.command, "reserve");

  const theme = fs.readFileSync(path.join(docsRoot, ".vitepress/theme/index.ts"), "utf8");
  assert.ok(theme.includes('app.component("ToolUsage", ToolUsage)'));
  const explorer = fs.readFileSync(
    path.join(docsRoot, ".vitepress/theme/components/ToolUsage.vue"),
    "utf8",
  );
  for (const marker of [
    "tool-usage.json",
    "Synopsis",
    "Aufruf",
    "tabResources",
    "Ressourcen",
    "Prozesse",
    "@media (max-width: 959px)",
    ":focus-visible",
  ]) {
    assert.ok(explorer.includes(marker), `Explorer lacks ${marker}`);
  }
});

test("translated guide editions preserve canonical technical vocabulary", () => {
  const guidePaths = [
    "concepts/business-reality-guide.md",
    ...fs
      .readdirSync(path.join(contentRoot, "concepts", "business-reality-guide"))
      .sort()
      .map((file) => `concepts/business-reality-guide/${file}`),
  ];
  const protectedTerms = [
    "Source → Evidence → Reality",
    "SourceRecord",
    "DocumentLine",
    "Commitment",
    "Reservation",
    "Movement",
    "LedgerEntry",
    "SettlementAllocation",
  ];
  for (const locale of translatedLocales) {
    const guide = guidePaths
      .map((relativePath) => fs.readFileSync(path.join(contentRoot, locale, relativePath), "utf8"))
      .join("\n");
    for (const term of protectedTerms) {
      assert.ok(guide.includes(term), `Missing protected guide term in ${locale}: ${term}`);
    }
  }
});

test("Fact guidance defines the safe write boundary with a complete example", () => {
  const facts = fs.readFileSync(
    path.join(contentRoot, "concepts", "business-reality-guide", "06-facts-and-open-questions.md"),
    "utf8",
  );
  for (const term of [
    "fact_observe_propose",
    "SourceRecord",
    "ChangeProposal",
    "Business Event",
    "order.shipping_priority",
    "idempotency",
    "Normal Commitment, Reservation, Movement, and Ledger commands do **not** manufacture mirror Facts",
  ]) {
    assert.match(facts, new RegExp(term.replaceAll("*", "\\*")), `Missing Fact guidance: ${term}`);
  }
});

test("agent capability guidance defines selection, confirmation, and verification", () => {
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  const guidance = fs.readFileSync(path.join(contentRoot, "tool-usage", "index.md"), "utf8");
  for (const term of [
    "capability_describe",
    "business_records_discover",
    "fact_observe_propose",
    "order_create_propose",
    "reservation_propose",
    "movement_create_propose",
    "interpretation_coverage",
    "order_explain",
    "commitments_list",
    "inventory_read",
    "exceptions_list",
    "fulfillment_queue",
    "fulfillment_blockers",
    "item_supply_demand",
    "exception_explain",
    "proposals_awaiting_approval",
    "finance_balances",
    "what the read proves or explicitly does not prove",
    "A successful response is not sufficient proof",
    "Adding guidance for another capability",
  ]) {
    assert.match(guidance, new RegExp(term), `Missing agent capability guidance: ${term}`);
  }
  assert.ok(guidance.includes("{#choosing-a-tool}"));
  assert.ok(config.includes('getStarted: "Get started"'));
});

test("MCP connection guidance is bilingual, discoverable, and matches current authentication", () => {
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  assert.ok(config.includes("/api-tools/connect-mcp"));
  for (const locale of ["", "de/"]) {
    const guide = fs.readFileSync(
      path.join(contentRoot, locale, "api-tools/connect-mcp.md"),
      "utf8",
    );
    for (const marker of [
      "MCP_URL",
      "Bearer",
      "tool allowlist",
      "business_records_discover",
      "proposal",
      "revok",
      "OAuth",
      "choosing-a-tool",
      "tool-usage/commands",
    ])
      assert.match(guide, new RegExp(marker, "iu"), `${locale || "en"}:${marker}`);
  }
});

test("the blog is a bilingual publishing surface with an editorial desk behind it", () => {
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  const theme = fs.readFileSync(path.join(docsRoot, ".vitepress", "theme", "index.ts"), "utf8");

  for (const locale of ["", ...translatedLocales]) {
    const blogRoot = path.join(contentRoot, locale, "blog");
    const index = fs.readFileSync(path.join(blogRoot, "index.md"), "utf8");
    assert.match(index, /<PostList \/>/u, `Blog index does not list posts: ${locale || "root"}`);
    assert.match(
      index,
      /sidebar: false/u,
      `Blog index keeps the docs sidebar: ${locale || "root"}`,
    );

    const posts = fs.readdirSync(blogRoot).filter((file) => file !== "index.md");
    assert.ok(posts.length > 0, `No published article for locale: ${locale || "root"}`);
    for (const file of posts) {
      const post = fs.readFileSync(path.join(blogRoot, file), "utf8");
      for (const field of ["title:", "description:", "date:", "author:"]) {
        assert.ok(post.includes(field), `Post ${locale}/blog/${file} is missing ${field}`);
      }
      assert.match(post, /<PostMeta \/>/u, `Post ${locale}/blog/${file} carries no byline`);
    }
  }

  assert.ok(config.includes('blog: "Blog"'));
  assert.ok(config.includes('link: route(locale, "/blog/")'));
  for (const marker of [
    'pattern: "blog/*.md"',
    'pattern: "de/blog/*.md"',
    'outputFile: "blog/feed.rss"',
    'outputFile: "de/blog/feed.rss"',
    "await buildFeeds(config)",
    "application/rss+xml",
  ]) {
    assert.ok(config.includes(marker), `Missing feed configuration: ${marker}`);
  }
  assert.ok(theme.includes('app.component("PostList", PostList)'));
  assert.ok(theme.includes('app.component("PostMeta", PostMeta)'));
  assert.ok(theme.includes('app.component("Subscribe", Subscribe)'));

  for (const file of [
    "editorial/README.md",
    "editorial/voice.md",
    "editorial/ideas.md",
    "editorial/templates/post.en.md",
    "editorial/templates/post.de.md",
    "scripts/new-post.mjs",
  ]) {
    assert.ok(fs.existsSync(path.join(docsRoot, file)), `Missing editorial file: ${file}`);
  }
  const board = fs.readFileSync(path.join(docsRoot, "editorial", "ideas.md"), "utf8");
  for (const section of ["## Drafting", "## Next", "## Backlog", "## Published", "## Parked"]) {
    assert.ok(board.includes(section), `Idea board is missing a pipeline stage: ${section}`);
  }
  const packageManifest = JSON.parse(fs.readFileSync(path.join(docsRoot, "package.json"), "utf8"));
  assert.equal(packageManifest.scripts["blog:new"], "node scripts/new-post.mjs");
});

test("unfinished blog drafts stay out of the index and the feeds", () => {
  const loader = fs.readFileSync(
    path.join(docsRoot, ".vitepress", "theme", "posts.data.mts"),
    "utf8",
  );
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  assert.match(loader, /draft === true/u);
  assert.match(loader, /!post\.draft/u);
  assert.match(config, /frontmatter\.draft !== true/u);
  // Committing a draft is the point of the mechanism, so the invariant worth holding is not
  // "no draft in the tree" but that an article is a draft in every language or in none. A draft
  // in one language only would publish an article whose other edition is missing.
  const isDraft = (locale, file) =>
    /^draft: true$/mu.test(fs.readFileSync(path.join(contentRoot, locale, "blog", file), "utf8"));
  const articles = fs
    .readdirSync(path.join(contentRoot, "blog"))
    .filter((entry) => entry !== "index.md");
  for (const file of articles) {
    for (const locale of translatedLocales) {
      assert.equal(
        isDraft(locale, file),
        isDraft("", file),
        `Draft state differs between language editions: ${file}`,
      );
    }
  }
});

test("every blog page offers the feed as the way to follow new writing", () => {
  const subscribe = fs.readFileSync(
    path.join(docsRoot, ".vitepress", "theme", "components", "Subscribe.vue"),
    "utf8",
  );
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  assert.ok(config.includes("      docsUrl,\n"), "Components cannot resolve the public origin");
  for (const marker of ['path: "/blog/feed.rss"', 'path: "/de/blog/feed.rss"']) {
    assert.ok(subscribe.includes(marker), `Missing feed address: ${marker}`);
  }
  for (const locale of ["", ...translatedLocales]) {
    const blogRoot = path.join(contentRoot, locale, "blog");
    for (const file of fs.readdirSync(blogRoot)) {
      const page = fs.readFileSync(path.join(blogRoot, file), "utf8");
      assert.match(page, /<Subscribe \/>/u, `No subscribe call to action: ${locale}/blog/${file}`);
    }
  }
  for (const template of ["post.en.md", "post.de.md"]) {
    const body = fs.readFileSync(path.join(docsRoot, "editorial", "templates", template), "utf8");
    assert.match(body, /<Subscribe \/>/u, `Template drops the call to action: ${template}`);
  }
});

test("reader analytics stays opt-in and out of local and CI builds", () => {
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  assert.match(config, /process\.env\.ANALYTICS_SCRIPT_URL/u);
  assert.match(config, /process\.env\.ANALYTICS_WEBSITE_ID/u);
  assert.match(config, /analyticsScriptUrl && analyticsWebsiteId/u);
  assert.match(config, /\.\.\.analyticsHead,/u);
  assert.doesNotMatch(config, /googletagmanager|google-analytics/iu);
});

test("one written voice governs both editions and the German stays informal", () => {
  const voice = fs.readFileSync(path.join(docsRoot, "editorial", "voice.md"), "utf8");
  for (const rule of [
    "Address the reader as `du`",
    "Not a translation",
    "450-550 words",
    "Keep the canonical model terms in English",
  ]) {
    assert.ok(voice.includes(rule), `Voice guide is missing a rule: ${rule}`);
  }

  // The skill is the trigger; the guide is the content. It must point at the guide rather than
  // restate it, or the two drift apart.
  const skill = fs.readFileSync(
    path.join(docsRoot, "..", "..", ".claude", "skills", "blog-post", "SKILL.md"),
    "utf8",
  );
  assert.match(skill, /^---\nname: blog-post\ndescription: /u);
  assert.ok(skill.includes("apps/docs/editorial/voice.md"), "Skill does not load the voice guide");

  const politeAddress = /\b(?:Ihnen|Ihre[nmrs]?)\b/u;
  const informalAddress = /\b(?:du|dir|dich|dein\w*)\b/u;
  const germanBlog = path.join(contentRoot, "de", "blog");
  for (const file of fs.readdirSync(germanBlog).filter((entry) => entry !== "index.md")) {
    const post = fs.readFileSync(path.join(germanBlog, file), "utf8");
    assert.doesNotMatch(post, politeAddress, `German post addresses the reader formally: ${file}`);
    assert.match(post, informalAddress, `German post never addresses the reader at all: ${file}`);

    // German opens with „ and closes with " — a straight quote closing a German one is the
    // typography mistake that survives every proofread.
    const opened = (post.match(/\u201e/gu) || []).length;
    const closed = (post.match(/\u201c/gu) || []).length;
    assert.equal(opened, closed, `German quotation marks are unbalanced: ${file}`);
    assert.doesNotMatch(
      post,
      /\u201e[^\u201c]*"/u,
      `German quotation closed with a straight quote: ${file}`,
    );
  }
});

test("the configured documentation logo is shipped from the public directory", () => {
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  assert.match(config, /logo:\s*["']\/reality-mark\.svg["']/u);
  assert.ok(fs.existsSync(path.join(contentRoot, "public", "reality-mark.svg")));
});

test("relative Markdown links resolve inside public documentation", () => {
  const failures = [];
  for (const file of markdownFiles(contentRoot)) {
    const source = fs.readFileSync(file, "utf8");
    for (const match of source.matchAll(/\[[^\]]+\]\(([^)]+)\)/gu)) {
      const href = match[1].split("#", 1)[0];
      if (!href || /^(?:https?:|mailto:|\/)/u.test(href)) continue;
      const target = path.resolve(path.dirname(file), decodeURIComponent(href));
      const candidates = [target, `${target}.md`, path.join(target, "index.md")];
      if (!candidates.some((candidate) => fs.existsSync(candidate))) {
        failures.push(`${path.relative(contentRoot, file)} -> ${href}`);
      }
    }
  }
  assert.deepEqual(failures, []);
});

test("public guidance labels claims and provides recovery content", () => {
  const content = markdownFiles(contentRoot)
    .map((file) => fs.readFileSync(file, "utf8"))
    .join("\n");
  assert.match(content, /Current behavior/u);
  assert.match(content, /Normative invariant/u);
  assert.match(content, /Example/u);
  const notFound = fs.readFileSync(path.join(contentRoot, "404.md"), "utf8");
  assert.match(notFound, /Back to documentation/u);
});

test("theme contracts preserve narrow-screen and keyboard usability", () => {
  const styles = fs.readFileSync(path.join(docsRoot, ".vitepress", "theme", "custom.css"), "utf8");
  assert.match(styles, /:root:not\(\.dark\)[\s\S]*--vp-c-bg:/u);
  assert.match(styles, /:root\.dark[\s\S]*--vp-c-brand-1:/u);
  assert.match(styles, /\.vpi-languages[\s\S]*circle[^}]*M2 12h20/u);
  assert.doesNotMatch(styles, /\.VPFeature\s*\{[^}]*border-color:\s*#[0-9a-f]+/iu);
  assert.match(styles, /:focus-visible[\s\S]*outline:/u);
  assert.match(styles, /@media \(max-width: 420px\)/u);
  assert.match(styles, /max-width: 100%/u);
  assert.match(styles, /overflow-x: auto/u);
});

test("documentation does not leak custom-container markup into rendered text", () => {
  for (const file of markdownFiles(contentRoot)) {
    const content = fs.readFileSync(file, "utf8");
    assert.doesNotMatch(
      content,
      /^:::/gmu,
      `Custom-container markup in ${path.relative(contentRoot, file)}`,
    );
  }
});

test("the open reference core declares and explains its MIT license", () => {
  const license = fs.readFileSync(path.join(repositoryRoot, "LICENSE"), "utf8");
  assert.match(license, /^MIT License$/mu);
  assert.match(license, /Copyright \(c\) 2026 Reality contributors/u);
  assert.match(license, /Permission is hereby granted, free of charge/u);
  const pyproject = fs.readFileSync(
    path.join(repositoryRoot, "packages", "reality-core", "pyproject.toml"),
    "utf8",
  );
  assert.match(pyproject, /^license = "MIT"$/mu);
  for (const relativePath of ["reference/license.md", "concepts/business-reality-guide.md"]) {
    assert.match(
      fs.readFileSync(path.join(contentRoot, relativePath), "utf8"),
      /MIT License/u,
      `Missing MIT explanation in ${relativePath}`,
    );
  }
});

test("commercial services are linked without restricting MIT use", () => {
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress", "config.mts"), "utf8");
  assert.equal((config.match(/website: "Website"/gu) || []).length, 2);
  assert.match(config, /text: labels\.website,\s*link: languageHref\(siteUrl/u);
  for (const relativePath of ["index.md", "reference/license.md"]) {
    const content = fs.readFileSync(path.join(contentRoot, relativePath), "utf8");
    assert.ok(content.includes("https://runreality.ai"));
    assert.match(
      content.replace(/\s+/gu, " "),
      /does not require an additional commercial license|remains independently available for commercial use/u,
    );
  }
});

test("handbook teaches the business model before integration details", () => {
  for (const locale of ["", "de/"]) {
    const root = path.join(contentRoot, locale, "concepts/business-reality-guide");
    const intro = fs.readFileSync(
      path.join(root, "01-from-erp-documents-to-business-reality.md"),
      "utf8",
    );
    assert.ok(intro.indexOf("Huber") < intro.indexOf("SourceRecord"));
    assert.doesNotMatch(
      intro,
      /Shopify-JSON|Shopify JSON|projection_checkpoint|source_capability/u,
    );
    assert.ok(intro.includes("../../reference/table-map"));
    const finance = fs.readFileSync(path.join(root, "03-invoices-and-payments.md"), "utf8");
    assert.ok(
      finance.includes("INV-1001") && finance.includes("SO-1001") && finance.includes("Huber"),
    );
    assert.doesNotMatch(
      finance,
      /### 22\.|Lies zuerst das \[Finanzkapitel\]|Read the \[finance chapter\] first/u,
    );
    const facts = fs.readFileSync(path.join(root, "06-facts-and-open-questions.md"), "utf8");
    assert.ok(facts.indexOf("{#missing-information}") < facts.indexOf("```json"));
  }
});

test("the shared order example reconciles stock, allocations and fulfilment", () => {
  for (const locale of ["", "de/"]) {
    const chapter = fs.readFileSync(
      path.join(
        contentRoot,
        locale,
        "concepts/business-reality-guide/02-orders-stock-and-deliveries.md",
      ),
      "utf8",
    );
    const rows = chapter.split("\n").filter((line) => /^\|[^|]+\|(?:\s*\d+\s*\|){5}$/.test(line));
    assert.equal(rows.length, 9);
    for (const [index, row] of rows.entries()) {
      const [physical, reserved, available, shipped, open] = row
        .split("|")
        .slice(2, -1)
        .map(Number);
      assert.equal(physical - reserved, available, row);
      assert.ok(reserved <= physical && reserved <= open, row);
      assert.equal(shipped + open, index === 0 ? 0 : 30, row);
    }
    assert.deepEqual(rows.at(-1).split("|").slice(2, -1).map(Number), [0, 0, 0, 30, 0]);
  }
});

test("the closing summary connects shared records, tools and the limits of the journal metaphor", () => {
  const slug = "07-model-at-a-glance";
  const config = fs.readFileSync(path.join(docsRoot, ".vitepress/config.mts"), "utf8");
  assert.ok(config.includes(slug));
  for (const locale of ["", "de/"]) {
    const root = path.join(contentRoot, locale, "concepts");
    const summary = fs.readFileSync(
      path.join(root, "business-reality-guide", `${slug}.md`),
      "utf8",
    );
    for (const term of [
      "SourceRecord",
      "Document",
      "Commitment",
      "Reservation",
      "Movement",
      "LedgerEntry",
      "Fact",
    ])
      assert.ok(summary.includes(term), term);
    assert.match(
      summary.replace(/\s+/gu, " "),
      /not every record is immutable|nicht jeder Datensatz ist unveränderlich/u,
    );
    assert.match(summary, /supported|unterstützt/u);
    assert.ok(summary.includes("../../tool-usage/"));
    for (const name of [
      "business-reality-guide.md",
      "business-reality-guide/06-facts-and-open-questions.md",
    ])
      assert.ok(fs.readFileSync(path.join(root, name), "utf8").includes(slug));
  }
});

test("the docs dark ground matches the product rather than the VitePress default", () => {
  // The light ground was matched to the product and the dark one was not, which left
  // the docs on a neutral near-black beside an app and a site that both sit on a
  // blue-tinted ground. Compare the hue and saturation, not the exact bytes: the
  // product may retune its palette, and a copy of its literal values would not say
  // what is being protected.
  const theme = fs.readFileSync(path.join(docsRoot, ".vitepress/theme/custom.css"), "utf8");
  const dark = theme.split(":root.dark {")[1].split("}")[0];
  const app = fs.readFileSync(path.join(repositoryRoot, "apps/web/src/tailwind.css"), "utf8");
  const appDark = app.split('[data-theme="dark"] {')[1].split("}")[0];
  const value = (block, name) => block.match(new RegExp(`--${name}:\\s*(#[0-9a-f]{6})`, "i"))?.[1];
  const hsl = (hex) => {
    const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
    const max = Math.max(r, g, b),
      min = Math.min(r, g, b),
      l = (max + min) / 2;
    if (max === min) return { hue: 0, saturation: 0, lightness: l * 100 };
    const d = max - min;
    const saturation = d / (l > 0.5 ? 2 - max - min : max + min);
    const hue =
      max === r
        ? ((g - b) / d + (g < b ? 6 : 0)) * 60
        : max === g
          ? ((b - r) / d + 2) * 60
          : ((r - g) / d + 4) * 60;
    return { hue, saturation: saturation * 100, lightness: l * 100 };
  };
  for (const [docsToken, appToken] of [
    ["vp-c-bg", "bg"],
    ["vp-c-bg-alt", "surface"],
    ["vp-c-bg-soft", "surface-muted"],
    ["vp-c-text-1", "text-strong"],
  ]) {
    const here = value(dark, docsToken),
      there = value(appDark, appToken);
    assert.ok(here, `docs dark is missing --${docsToken}`);
    assert.ok(there, `the app dark theme is missing --${appToken}`);
    const a = hsl(here),
      b = hsl(there);
    assert.ok(
      Math.abs(a.hue - b.hue) <= 20,
      `--${docsToken} (${here}) is hue ${Math.round(a.hue)}; the app's --${appToken} (${there}) is ${Math.round(b.hue)}`,
    );
    assert.ok(
      Math.abs(a.saturation - b.saturation) <= 20,
      `--${docsToken} (${here}) is ${Math.round(a.saturation)}% saturated; the app's --${appToken} (${there}) is ${Math.round(b.saturation)}%`,
    );
  }
});

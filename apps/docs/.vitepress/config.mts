import { languageHref } from "../../shared/language";
import fs from "node:fs";
import path from "node:path";
import { createContentLoader, defineConfig, type SiteConfig } from "vitepress";

const normalizedUrl = (value: string | undefined, fallback: string) =>
  (value || fallback).replace(/\/+$/, "");

const siteUrl = normalizedUrl(process.env.SITE_URL, "https://runreality.ai");
const appUrl = normalizedUrl(process.env.APP_URL, "https://app.runreality.ai");
const docsUrl = normalizedUrl(process.env.DOCS_URL, "https://docs.runreality.ai");

type LocaleKey = "root" | "de";

type NavigationCopy = {
  guide: string;
  concepts: string;
  toolsAndModel: string;
  blog: string;
  reference: string;
  openReality: string;
  website: string;
  gettingStarted: string;
  overview: string;
  realityGuide: string;
  realityChapters: string;
  chapters: string[];
  agentPlaybooks: string;
  playbookFulfilment: string;
  playbookReceivables: string;
  playbookContribution: string;
  playbookPurchasing: string;
  playbookReturns: string;
  playbookMasterData: string;
  playbookRhythm: string;
  customization: string;
  orderExample: string;
  connectorContract: string;
  apiTools: string;
  connectMcp: string;
  getStarted: string;
  operations: string;
  installOptions: string;
  oneLineSetup: string;
  dockerCompose: string;
  kubernetes: string;
  railway: string;
  productionDeployment: string;
  development: string;
  connectors: string;
  commands: string;
  derivedViews: string;
  applicationSurfaces: string;
  toolUsage: string;
  learn: string;
  setupAndOperate: string;
  storylines: string;
  environment: string;
  docsUrls: string;
  glossary: string;
  tableMap: string;
  license: string;
  outline: string;
  edit: string;
  footer: string;
};

const copy: Record<LocaleKey, NavigationCopy> = {
  root: {
    guide: "Get started",
    concepts: "Understand",
    toolsAndModel: "Tools",
    blog: "Blog",
    reference: "Reference",
    openReality: "Open Reality",
    website: "Website",
    gettingStarted: "First product journey",
    overview: "Overview",
    realityGuide: "Reality for ERP professionals",
    realityChapters: "Overview",
    chapters: [
      "From ERP documents to Business Reality",
      "Orders, stock and deliveries",
      "Invoices and payments",
      "Working as Process Owner",
      "One order from start to finish",
      "Facts and open questions",
      "Inventory cost, DB1 and DB2",
      "Summary",
    ],
    agentPlaybooks: "Agents",
    playbookFulfilment: "Sales and fulfilment",
    playbookReceivables: "Receivables and payments",
    playbookContribution: "Contribution margin",
    playbookPurchasing: "Purchasing and replenishment",
    playbookReturns: "Returns",
    playbookMasterData: "Master data and sources",
    playbookRhythm: "Operating rhythm",
    customization: "What can be adapted?",
    orderExample: "Example: an ERP order",
    connectorContract: "Connector contract",
    apiTools: "API and agent interfaces",
    connectMcp: "Connect an MCP client",
    getStarted: "Get started",
    operations: "Installation & Operations",
    installOptions: "Install options",
    oneLineSetup: "One-line setup",
    dockerCompose: "Docker Compose",
    kubernetes: "Kubernetes with Helm",
    railway: "Railway",
    productionDeployment: "Operate with Docker",
    development: "Reality Core Development",
    connectors: "Connect another ERP",
    commands: "Implement business operations",
    derivedViews: "Develop metrics and operational warnings",
    applicationSurfaces: "Expose functions through API and MCP",
    toolUsage: "Tool Usage",
    learn: "Get to know",
    setupAndOperate: "Set up and operate",
    storylines: "Storylines",
    environment: "Environment",
    docsUrls: "Configure Docs links",
    glossary: "Glossary",
    tableMap: "Table map and misconceptions",
    license: "MIT License",
    outline: "On this page",
    edit: "Improve this page",
    footer: "Reality documentation",
  },
  de: {
    guide: "Loslegen",
    concepts: "Verstehen",
    toolsAndModel: "Tools",
    blog: "Blog",
    reference: "Referenz",
    openReality: "Reality öffnen",
    website: "Website",
    gettingStarted: "Erster Produktdurchlauf",
    overview: "Übersicht",
    realityGuide: "Reality für ERP-Profis",
    realityChapters: "Überblick",
    chapters: [
      "Von ERP-Belegen zur Business Reality",
      "Aufträge, Bestand und Lieferungen",
      "Rechnungen und Zahlungen",
      "Als Prozessverantwortliche/r arbeiten",
      "Ein Auftrag von Anfang bis Ende",
      "Facts und offene Fragen",
      "Bestandskosten, DB1 und DB2",
      "Zusammenfassung",
    ],
    agentPlaybooks: "Agenten",
    playbookFulfilment: "Vertrieb und Versand",
    playbookReceivables: "Forderungen und Zahlungen",
    playbookContribution: "Deckungsbeitrag",
    playbookPurchasing: "Einkauf und Nachschub",
    playbookReturns: "Retouren",
    playbookMasterData: "Stammdaten und Quellen",
    playbookRhythm: "Betriebsrhythmus",
    customization: "Was kann angepasst werden?",
    orderExample: "Beispiel: ein ERP-Auftrag",
    connectorContract: "Connector-Vertrag",
    apiTools: "API und Agentenschnittstellen",
    connectMcp: "Einen MCP-Client verbinden",
    getStarted: "Loslegen",
    operations: "Installation & Betrieb",
    installOptions: "Installationsoptionen",
    oneLineSetup: "Einzeiler-Setup",
    dockerCompose: "Docker Compose",
    kubernetes: "Kubernetes mit Helm",
    railway: "Railway",
    productionDeployment: "Mit Docker betreiben",
    development: "Reality-Core-Entwicklung",
    connectors: "Ein weiteres ERP anbinden",
    commands: "Neue Geschäftsabläufe implementieren",
    derivedViews: "Kennzahlen und operative Warnungen entwickeln",
    applicationSurfaces: "Funktionen über API und MCP anbieten",
    toolUsage: "Tools nutzen",
    learn: "Kennenlernen",
    setupAndOperate: "Einrichten & Betreiben",
    storylines: "Storylines",
    environment: "Umgebung",
    docsUrls: "Docs-Links konfigurieren",
    glossary: "Glossar",
    tableMap: "Tabellenübersicht und Missverständnisse",
    license: "MIT-Lizenz",
    outline: "Auf dieser Seite",
    edit: "Diese Seite verbessern",
    footer: "Reality-Dokumentation",
  },
};

const prefixFor = (locale: LocaleKey) => (locale === "root" ? "" : `/${locale}`);
const route = (locale: LocaleKey, path: string) => `${prefixFor(locale)}${path}`;

const navigation = (locale: LocaleKey) => {
  const labels = copy[locale];
  return [
    // Same words and order as the sidebar: get to know, understand, tools.
    { text: labels.learn, link: route(locale, "/getting-started/") },
    { text: labels.concepts, link: route(locale, "/concepts/business-reality-guide") },
    { text: labels.toolsAndModel, link: route(locale, "/tool-usage/") },
    { text: labels.blog, link: route(locale, "/blog/") },
    { text: labels.website, link: languageHref(siteUrl, locale === "de" ? "de" : "en") },
    { text: labels.openReality, link: languageHref(appUrl, locale === "de" ? "de" : "en") },
  ];
};

const sidebar = (locale: LocaleKey) => {
  const labels = copy[locale];
  const chapterFiles = [
    "01-from-erp-documents-to-business-reality",
    "02-orders-stock-and-deliveries",
    "03-invoices-and-payments",
    "04-working-as-process-owner",
    "05-one-order-end-to-end",
    "06-facts-and-open-questions",
    "08-inventory-cost-and-contribution",
    "07-model-at-a-glance",
  ];
  return [
    // Groups by intent, in the order a newcomer needs them: try it, understand it, use the
    // tools, set it up, look things up, develop. Only the first group opens by itself, so the
    // sidebar is a table of contents, not a wall. No link stands alone on the top level.
    {
      text: labels.learn,
      collapsed: false,
      items: [
        { text: labels.gettingStarted, link: route(locale, "/getting-started/") },
        { text: labels.storylines, link: route(locale, "/storylines/") },
      ],
    },
    {
      text: labels.realityGuide,
      collapsed: true,
      items: [
        {
          text: labels.realityChapters,
          link: route(locale, "/concepts/business-reality-guide"),
        },
        ...chapterFiles.map((file, index) => ({
          text: labels.chapters[index],
          link: route(locale, `/concepts/business-reality-guide/${file}`),
        })),
      ],
    },
    {
      // Everything a person or an agent calls, in one place: the interactive Tool Usage page
      // (resources, processes, technical view) and the playbooks that use those tools.
      text: labels.toolUsage,
      collapsed: true,
      items: [
        { text: labels.overview, link: route(locale, "/tool-usage/") },
        {
          // The playbooks are one chapter of Tool Usage, not six. The group link opens the
          // introduction; the pages sit one level down so the parent group stays scannable.
          text: labels.agentPlaybooks,
          link: route(locale, "/agent-playbooks/"),
          collapsed: true,
          items: [
            {
              text: labels.playbookRhythm,
              link: route(locale, "/agent-playbooks/operating-rhythm"),
            },
            {
              text: labels.playbookFulfilment,
              link: route(locale, "/agent-playbooks/order-to-cash-fulfilment"),
            },
            {
              text: labels.playbookReceivables,
              link: route(locale, "/agent-playbooks/receivables-and-payments"),
            },
            {
              text: labels.playbookContribution,
              link: route(locale, "/agent-playbooks/contribution-margin"),
            },
            {
              text: labels.playbookPurchasing,
              link: route(locale, "/agent-playbooks/purchasing-and-replenishment"),
            },
            { text: labels.playbookReturns, link: route(locale, "/agent-playbooks/returns") },
            {
              text: labels.playbookMasterData,
              link: route(locale, "/agent-playbooks/master-data-and-sources"),
            },
          ],
        },
        {
          text: "Analytics",
          link: route(locale, "/analytics/"),
        },
      ],
    },
    {
      text: labels.setupAndOperate,
      collapsed: true,
      items: [
        { text: labels.connectMcp, link: route(locale, "/api-tools/connect-mcp") },
        { text: labels.apiTools, link: route(locale, "/api-tools/") },
        { text: labels.installOptions, link: route(locale, "/operations/") },
        { text: labels.oneLineSetup, link: route(locale, "/operations/installation") },
        { text: labels.dockerCompose, link: route(locale, "/operations/docker-compose") },
        { text: labels.kubernetes, link: route(locale, "/operations/kubernetes") },
        { text: labels.railway, link: route(locale, "/operations/railway") },
        { text: labels.productionDeployment, link: route(locale, "/operations/deployment") },
        { text: labels.environment, link: route(locale, "/reference/environment") },
      ],
    },
    {
      text: labels.reference,
      collapsed: true,
      items: [
        { text: labels.overview, link: route(locale, "/reference/") },
        { text: labels.docsUrls, link: route(locale, "/reference/docs-url-configuration") },
        { text: labels.glossary, link: route(locale, "/reference/glossary") },
        { text: labels.tableMap, link: route(locale, "/reference/table-map") },
        { text: labels.license, link: route(locale, "/reference/license") },
      ],
    },
    {
      text: labels.development,
      collapsed: true,
      items: [
        { text: labels.overview, link: route(locale, "/development/") },
        { text: labels.customization, link: route(locale, "/integrations/customization") },
        { text: labels.connectors, link: route(locale, "/development/connectors") },
        { text: labels.orderExample, link: route(locale, "/integrations/order-example") },
        { text: labels.connectorContract, link: route(locale, "/integrations/connector-contract") },
        { text: labels.commands, link: route(locale, "/development/commands") },
        { text: labels.derivedViews, link: route(locale, "/development/derived-views") },
        {
          text: labels.applicationSurfaces,
          link: route(locale, "/development/application-surfaces"),
        },
      ],
    },
  ];
};

const localeTheme = Object.fromEntries(
  (["root", "de"] as LocaleKey[]).map((locale) => [
    locale,
    {
      docsUrl,
      nav: navigation(locale),
      sidebar: sidebar(locale),
      outline: { level: [2, 3], label: copy[locale].outline },
      editLink: {
        pattern: "https://github.com/Xentral-Labs/reality/edit/main/apps/docs/content/:path",
        text: copy[locale].edit,
      },
      footer: {
        message: `${copy[locale].footer} · <a href="${languageHref(siteUrl, locale === "de" ? "de" : "en")}">${copy[locale].website}</a> · <a href="${route(locale, "/reference/license")}">MIT</a>`,
        copyright: "Source → Evidence → Reality",
      },
    },
  ]),
);

const searchLocales = {
  root: {
    translations: {
      button: { buttonText: "Search", buttonAriaLabel: "Search documentation" },
      modal: { noResultsText: "No documentation found for" },
    },
  },
  de: {
    translations: {
      button: {
        buttonText: "Suchen",
        buttonAriaLabel: "Dokumentation durchsuchen",
      },
      modal: { noResultsText: "Keine Dokumentation gefunden für" },
    },
  },
};

// Reader analytics is opt-in. Without both values the built pages load no external script at
// all, which is what keeps local development, CI and preview builds out of the numbers.
const analyticsScriptUrl = (process.env.ANALYTICS_SCRIPT_URL || "").trim();
const analyticsWebsiteId = (process.env.ANALYTICS_WEBSITE_ID || "").trim();

const analyticsHead: [string, Record<string, string>][] =
  analyticsScriptUrl && analyticsWebsiteId
    ? [
        [
          "script",
          {
            defer: "",
            src: analyticsScriptUrl,
            "data-website-id": analyticsWebsiteId,
          },
        ],
      ]
    : [];

type FeedDefinition = {
  pattern: string;
  outputFile: string;
  feedUrl: string;
  pageUrl: string;
  language: string;
  title: string;
  description: string;
};

const feeds: FeedDefinition[] = [
  {
    pattern: "blog/*.md",
    outputFile: "blog/feed.rss",
    feedUrl: `${docsUrl}/blog/feed.rss`,
    pageUrl: `${docsUrl}/blog/`,
    language: "en-GB",
    title: "Reality Blog",
    description:
      "Field notes on Business Reality, Agent Operations, and the open Reality reference core.",
  },
  {
    pattern: "de/blog/*.md",
    outputFile: "de/blog/feed.rss",
    feedUrl: `${docsUrl}/de/blog/feed.rss`,
    pageUrl: `${docsUrl}/de/blog/`,
    language: "de-DE",
    title: "Reality Blog",
    description:
      "Notizen zu Business Reality, Agent Operations und dem offenen Reality-Referenzkern.",
  },
];

const escapeXml = (value: string) =>
  value.replace(
    /[<>&"']/gu,
    (character) =>
      ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&apos;" })[
        character
      ] as string,
  );

const buildFeeds = async (config: SiteConfig) => {
  for (const feed of feeds) {
    const posts = (await createContentLoader(feed.pattern).load())
      .filter(
        (post) =>
          !/\/blog\/?$/u.test(post.url) && post.frontmatter.date && post.frontmatter.draft !== true,
      )
      // Same ordering as the index: date, then the author's `order` for posts sharing a date,
      // then the url so the feed never reshuffles between builds.
      .sort(
        (left, right) =>
          new Date(right.frontmatter.date).getTime() - new Date(left.frontmatter.date).getTime() ||
          Number(left.frontmatter.order ?? 100) - Number(right.frontmatter.order ?? 100) ||
          left.url.localeCompare(right.url),
      )
      .slice(0, 50);

    const items = posts.map((post) => {
      const url = `${docsUrl}${post.url}`;
      return [
        "    <item>",
        `      <title>${escapeXml(String(post.frontmatter.title || ""))}</title>`,
        `      <link>${escapeXml(url)}</link>`,
        `      <guid isPermaLink="true">${escapeXml(url)}</guid>`,
        `      <pubDate>${new Date(post.frontmatter.date).toUTCString()}</pubDate>`,
        `      <description>${escapeXml(String(post.frontmatter.description || ""))}</description>`,
        "    </item>",
      ].join("\n");
    });

    const channel = [
      '<?xml version="1.0" encoding="UTF-8"?>',
      '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
      "  <channel>",
      `    <title>${escapeXml(feed.title)}</title>`,
      `    <link>${escapeXml(feed.pageUrl)}</link>`,
      `    <description>${escapeXml(feed.description)}</description>`,
      `    <language>${feed.language}</language>`,
      `    <atom:link href="${escapeXml(feed.feedUrl)}" rel="self" type="application/rss+xml"/>`,
      ...items,
      "  </channel>",
      "</rss>",
      "",
    ].join("\n");

    const target = path.join(config.outDir, feed.outputFile);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, channel, "utf8");
  }
};

export default defineConfig({
  srcDir: "content",
  title: "Reality Docs",
  description: "Understand, integrate, deploy, and operate the Reality commerce core.",
  cleanUrls: true,
  head: [
    ["meta", { name: "theme-color", content: "#6755f5" }],
    ...feeds.map(
      (feed) =>
        [
          "link",
          {
            rel: "alternate",
            type: "application/rss+xml",
            hreflang: feed.language,
            title: `${feed.title} (${feed.language})`,
            href: feed.feedUrl,
          },
        ] as [string, Record<string, string>],
    ),
    ...analyticsHead,
  ],
  locales: {
    root: { label: "English", lang: "en-GB", themeConfig: localeTheme.root },
    de: { label: "Deutsch", lang: "de-DE", link: "/de/", themeConfig: localeTheme.de },
  },
  async buildEnd(config) {
    await buildFeeds(config);
  },
  transformPageData(pageData) {
    const actions = pageData.frontmatter.hero?.actions as Array<{ link?: string }> | undefined;
    for (const action of actions || []) {
      if (action.link === "__APP_URL__")
        action.link = languageHref(
          `${appUrl}/app`,
          pageData.relativePath.startsWith("de/") ? "de" : "en",
        );
    }
  },
  themeConfig: {
    productUrl: `${appUrl}/app`,
    websiteUrl: siteUrl,
    logo: "/reality-mark.svg",
    siteTitle: "Reality Docs",
    i18nRouting: true,
    search: {
      provider: "local",
      options: { detailedView: true, locales: searchLocales },
    },
    socialLinks: [{ icon: "github", link: "https://github.com/Xentral-Labs/reality" }],
  },
});

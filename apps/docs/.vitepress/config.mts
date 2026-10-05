import { languageHref } from "../../shared/language";
import fs from "node:fs";
import path from "node:path";
import { createContentLoader, defineConfig, type SiteConfig } from "vitepress";

const normalizedUrl = (value: string | undefined, fallback: string) =>
  (value || fallback).replace(/\/+$/, "");

const siteUrl = normalizedUrl(process.env.SITE_URL, "https://runreality.ai");
const appUrl = normalizedUrl(process.env.APP_URL, "https://app.runreality.ai");
const docsUrl = normalizedUrl(process.env.DOCS_URL, "https://docs.runreality.ai");
const apiUrl = normalizedUrl(process.env.API_URL, "http://localhost:8000");

type LocaleKey = "root" | "de";

type NavigationCopy = {
  glossary: string;
  openReality: string;
  website: string;
  gettingStarted: string;
  realityGuide: string;
  chapters: string[];
  agentPlaybooks: string;
  playbookFulfilment: string;
  playbookReceivables: string;
  playbookContribution: string;
  playbookPurchasing: string;
  playbookReturns: string;
  playbookMasterData: string;
  playbookRhythm: string;
  apiTools: string;
  connectMcp: string;
  toolUsage: string;
  learn: string;
  explore: string;
  useReality: string;
  demoStart: string;
  newBusiness: string;
  existingBusiness: string;
  analytics: string;
  storylines: string;
  demoData: string;
  businessJourneys: string;
  outline: string;
  edit: string;
  footer: string;
  development: string;
  developmentOverview: string;
  firstExtension: string;
  businessLogic: string;
  connectors: string;
  interfaces: string;
  agentTools: string;
  apiCli: string;
};

const copy: Record<LocaleKey, NavigationCopy> = {
  root: {
    glossary: "Glossary",
    openReality: "Open Reality",
    website: "Website",
    gettingStarted: "Choose your starting point",
    realityGuide: "Reality for ERP professionals",
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
    apiTools: "API and agent interfaces",
    connectMcp: "Connect an MCP client",
    toolUsage: "Tool Usage",
    learn: "Start here",
    explore: "Explore Reality",
    useReality: "Use Reality",
    demoStart: "Experience a demo company",
    newBusiness: "Build a company from scratch",
    existingBusiness: "Start with an existing company",
    analytics: "Analytics",
    storylines: "Follow a guided storyline",
    demoData: "Explore the demo company",
    businessJourneys: "Find supported business scenarios",
    outline: "On this page",
    edit: "Improve this page",
    footer: "Reality documentation",
    development: "Build with Reality",
    developmentOverview: "What you can build",
    firstExtension: "Your first extension",
    businessLogic: "Develop business logic",
    connectors: "Connect ERP and data sources",
    interfaces: "Add agent and API interfaces",
    agentTools: "Build agent tools",
    apiCli: "Add API and CLI",
  },
  de: {
    glossary: "Glossar",
    openReality: "Reality öffnen",
    website: "Website",
    gettingStarted: "Wähle deinen Einstieg",
    realityGuide: "Reality für ERP-Profis",
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
    apiTools: "API und Agentenschnittstellen",
    connectMcp: "Einen MCP-Client verbinden",
    toolUsage: "Tools nutzen",
    learn: "Hier starten",
    explore: "Reality erkunden",
    useReality: "Mit Reality arbeiten",
    demoStart: "Eine Demo-Firma erleben",
    newBusiness: "Ein Unternehmen von null aufbauen",
    existingBusiness: "Mit einer bestehenden Firma starten",
    analytics: "Analytics",
    storylines: "Eine Storyline durchspielen",
    demoData: "Die Demo-Firma erkunden",
    businessJourneys: "Unterstützte Geschäftsfälle finden",
    outline: "Auf dieser Seite",
    edit: "Diese Seite verbessern",
    footer: "Reality-Dokumentation",
    development: "Mit Reality entwickeln",
    developmentOverview: "Was du entwickeln kannst",
    firstExtension: "Deine erste Erweiterung",
    businessLogic: "Geschäftslogik entwickeln",
    connectors: "ERP und Datenquellen anbinden",
    interfaces: "Agenten- und API-Schnittstellen ergänzen",
    agentTools: "Agentenwerkzeuge entwickeln",
    apiCli: "API und CLI ergänzen",
  },
};

const prefixFor = (locale: LocaleKey) => (locale === "root" ? "" : `/${locale}`);
const route = (locale: LocaleKey, path: string) => `${prefixFor(locale)}${path}`;

const navigation = (locale: LocaleKey) => {
  const labels = copy[locale];
  return [
    // Lead with the same start, exploration and daily-use destinations as the sidebar.
    { text: labels.learn, link: route(locale, "/getting-started/") },
    { text: labels.explore, link: route(locale, "/getting-started/demo-data") },
    { text: labels.useReality, link: route(locale, "/agent-playbooks/") },
    { text: labels.development, link: route(locale, "/development/") },
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
    // Choose a starting recipe; exploration, daily work and development are separate intents.
    {
      text: labels.learn,
      collapsed: false,
      items: [
        { text: labels.gettingStarted, link: route(locale, "/getting-started/") },
        { text: labels.demoStart, link: route(locale, "/getting-started/demo-company") },
        { text: labels.newBusiness, link: route(locale, "/getting-started/start-business") },
        {
          text: labels.existingBusiness,
          link: route(locale, "/getting-started/existing-business"),
        },
      ],
    },
    {
      text: labels.explore,
      collapsed: true,
      items: [
        { text: labels.demoData, link: route(locale, "/getting-started/demo-data") },
        { text: labels.storylines, link: route(locale, "/storylines/") },
        {
          text: labels.realityGuide,
          link: route(locale, "/concepts/business-reality-guide"),
          collapsed: true,
          items: [
            ...chapterFiles.map((file, index) => ({
              text: labels.chapters[index],
              link: route(locale, `/concepts/business-reality-guide/${file}`),
            })),
            {
              text: locale === "de" ? "Bestand und offene Vorgänge" : "Inventory and open work",
              link: route(locale, "/concepts/list-evidence"),
            },
            {
              text: locale === "de" ? "Ein Ergebnis zurückverfolgen" : "Trace a result",
              link: route(locale, "/getting-started/first-trace"),
            },
          ],
        },
        {
          text: labels.businessJourneys,
          link: route(locale, "/getting-started/business-journeys"),
        },
        { text: labels.glossary, link: route(locale, "/reference/glossary") },
      ],
    },
    {
      text: labels.useReality,
      collapsed: false,
      items: [
        {
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
        { text: labels.analytics, link: route(locale, "/analytics/") },
        {
          text: labels.toolUsage,
          collapsed: false,
          items: [
            {
              text:
                locale === "de" ? "Interaktiver Kommandokatalog" : "Interactive command catalog",
              link: route(locale, "/tool-usage/"),
            },
            {
              text:
                locale === "de"
                  ? "Wie dein Agent mit Tools arbeitet"
                  : "How your agent works with tools",
              link: route(locale, "/api-tools/agent-guidance"),
            },
          ],
        },
      ],
    },
    {
      text: labels.development,
      collapsed: true,
      items: [
        { text: labels.developmentOverview, link: route(locale, "/development/") },
        { text: labels.firstExtension, link: route(locale, "/development/first-extension") },
        { text: labels.businessLogic, link: route(locale, "/development/commands") },
        { text: labels.connectors, link: route(locale, "/development/connectors") },
        {
          text: locale === "de" ? "Vorgänge übernehmen" : "Take over operational cases",
          link: route(locale, "/integrations/operational-cases"),
        },
        {
          text: labels.interfaces,
          link: route(locale, "/development/application-surfaces"),
          collapsed: true,
          items: [
            { text: labels.apiTools, link: route(locale, "/api-tools/") },
            { text: labels.agentTools, link: route(locale, "/development/agent-tools") },
            { text: labels.apiCli, link: route(locale, "/development/api-cli") },
          ],
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
        message: `${copy[locale].footer} · <a href="${languageHref(siteUrl, locale === "de" ? "de" : "en")}">${copy[locale].website}</a> · <a href="https://github.com/Xentral-Labs/reality/blob/main/LICENSE">MIT</a>`,
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
  vite: {
    define: {
      __API_URL__: JSON.stringify(apiUrl),
      __APP_URL__: JSON.stringify(appUrl),
    },
  },
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
    fs.cpSync(path.resolve(config.srcDir, "../public"), config.outDir, { recursive: true });
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
    businessLogicUrl: normalizedUrl(process.env.BUSINESS_LOGIC_API_URL, apiUrl),
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

/** Compatibility navigation is read-only and never accepts a redirect URL. */
const current = new Set([
  "",
  "facts",
  "inspector",
  "settings",
  "orders-deliveries",
  "copilot",
  "work",
  "decisions",
  "analytics",
  "master-data",
  "data-sources",
  "demo-data",
  "finance",
  "warehouse",
  "attention",
  "storyline",
  "chat",
]);
const aliases: Record<string, [string, Record<string, string>]> = {
  home: ["", {}],
  orders: ["orders-deliveries", { orders_view: "customer-orders" }],
  commitments: ["orders-deliveries", { orders_view: "deliveries" }],
  inventory: ["warehouse", { warehouse_view: "stock" }],
  reservations: ["warehouse", { warehouse_view: "reservations" }],
  movements: ["warehouse", { warehouse_view: "movements" }],
  "warehouse-queue": ["work", {}],
  "fulfillment-blockers": ["attention", {}],
  "supply-demand": ["warehouse", { warehouse_view: "stock" }],
  "open-items": ["finance", { finance_view: "open-items" }],
  payments: ["finance", { finance_view: "payments" }],
  journal: ["finance", { finance_view: "journal" }],
  parties: ["master-data", { family: "customer" }],
  items: ["master-data", { family: "item" }],
  locations: ["master-data", { family: "location" }],
  documents: ["data-sources", { data_view: "documents" }],
  integrations: ["data-sources", { data_view: "systems" }],
  imports: ["data-sources", { data_view: "records" }],
  exceptions: ["attention", {}],
  issues: ["attention", {}],
  "missing-information": ["inspector", { inspector_view: "rules" }],
  explorer: ["inspector", { inspector_view: "records" }],
  timeline: ["inspector", { inspector_view: "overview" }],
  companies: ["settings", { settings_view: "company" }],
  profile: ["settings", { settings_view: "personal" }],
  "ai-settings": ["settings", { settings_view: "ai" }],
  chat: ["chat", {}],
  "free-play": ["chat", {}],
};
export type Entry =
  { kind: "app" | "oauth" | "retired" | "missing" } | { kind: "redirect"; href: string };
export function oauthInteraction(url: URL): string | null {
  const path = url.pathname.replace(/\/+$/, "") || "/";
  const values = url.searchParams.getAll("interaction");
  if (
    path !== "/oauth/authorize" ||
    values.length !== 1 ||
    !/^oai_[A-Za-z0-9_-]{8,128}$/.test(values[0]) ||
    [...url.searchParams.keys()].some((key) => key !== "interaction") ||
    url.hash
  )
    return null;
  return values[0];
}
export function resolveEntry(url: URL): Entry {
  const path = url.pathname.replace(/\/+$/, "") || "/";
  if (path === "/oauth/authorize")
    return oauthInteraction(url) ? { kind: "oauth" } : { kind: "missing" };
  if (path === "/playground" || path.startsWith("/playground/") || path === "/app/playground")
    return { kind: "retired" };
  if (path === "/") return { kind: "redirect", href: `/app${url.search}` };
  const key = path.startsWith("/app/") ? path.slice(5) : path === "/app" ? "" : path.slice(1);
  if ((path === "/app" || path.startsWith("/app/")) && current.has(key))
    return path !== url.pathname
      ? { kind: "redirect", href: `${path}${url.search}` }
      : { kind: "app" };
  const alias = Object.hasOwn(aliases, key) ? aliases[key] : undefined;
  if (!alias) return { kind: "missing" };
  const params = new URLSearchParams();
  for (const key of ["tenant", "q", "page", "size"]) {
    const value = url.searchParams.get(key);
    if (value) params.set(key, value);
  }
  if ((key === "free-play" || key === "chat") && url.searchParams.get("session"))
    params.set("session", url.searchParams.get("session")!);
  const language = url.searchParams.get("lang");
  if (language && ["en", "de", "nl", "es"].includes(language)) params.set("lang", language);
  for (const [name, value] of Object.entries(alias[1])) params.set(name, value);
  if (key === "parties" && url.searchParams.get("role") === "supplier")
    params.set("family", "supplier");
  return {
    kind: "redirect",
    href: `/app${alias[0] ? `/${alias[0]}` : ""}${params.size ? `?${params}` : ""}`,
  };
}
export function safeAccountReturn(value: string): string | null {
  if (!value.startsWith("/") || value.startsWith("//") || /[\\#\u0000-\u0020]/.test(value))
    return null;
  const url = new URL(value, "https://local.invalid");
  if (url.pathname !== value.split("?")[0]) return null;
  const result = resolveEntry(url);
  return result.kind === "redirect" ? result.href : result.kind === "missing" ? null : value;
}
const returnKey = "reality.app.return";
export function rememberAccountDestination(): void {
  const destination = safeAccountReturn(`${location.pathname}${location.search}`);
  if (destination) sessionStorage.setItem(returnKey, destination);
  sessionStorage.removeItem("reality.playground.return");
}
export function accountDestination(fallback: string): string {
  const destination = safeAccountReturn(sessionStorage.getItem(returnKey) || "");
  sessionStorage.removeItem(returnKey);
  sessionStorage.removeItem("reality.playground.return");
  // Approval remains authoritative even when a saved destination exists.
  return fallback === "/app" ? destination || fallback : fallback;
}

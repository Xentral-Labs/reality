/** Same-browser presentation preference; never an account or authorization value. */
export type Language = "en" | "de" | "nl" | "es";
const key = "reality.language";
const cookieName = "reality_language";
export function validLanguage(value: unknown): Language | undefined {
  return value === "en" || value === "de" || value === "nl" || value === "es"
    ? value
    : undefined;
}
export function resolveLanguage(
  search: string,
  stored: unknown,
  fallback: unknown = "en",
): Language {
  return (
    validLanguage(new URLSearchParams(search).get("lang")) ??
    validLanguage(stored) ??
    validLanguage(fallback) ??
    "en"
  );
}
/** Remove only retired presentation storage; never read its value or touch account state. */
export function clearLegacyLanguage(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(key);
  } catch {
    /* Best effort on this origin. */
  }
  const host = window.location.hostname;
  const domains =
    host === "runreality.ai" || host.endsWith(".runreality.ai")
      ? ["", "; Domain=runreality.ai"]
      : [""];
  for (const domain of domains) {
    try {
      document.cookie = `${cookieName}=; Path=/; Max-Age=0; SameSite=Lax${domain}${window.location.protocol === "https:" ? "; Secure" : ""}`;
    } catch {
      /* Storage restrictions must not prevent navigation. */
    }
  }
}
// A document-lifetime choice survives SPA navigation, never a reload or another origin.
let preferenceDocument: Document | undefined;
let preferenceOrigin: string | undefined;
let currentChoice: Language | undefined;
let accountFallback: Language | undefined;
function currentDocument(): void {
  const origin = new URL(window.location.href).origin;
  if (document !== preferenceDocument || origin !== preferenceOrigin) {
    preferenceDocument = document;
    preferenceOrigin = origin;
    currentChoice = undefined;
    accountFallback = undefined;
  }
}
export function setLanguageFallback(language: Language | undefined): void {
  if (typeof window === "undefined") return;
  currentDocument();
  accountFallback = validLanguage(language);
}
export function readLanguage(): Language | undefined {
  if (typeof window === "undefined") return undefined;
  clearLegacyLanguage();
  currentDocument();
  const explicit = validLanguage(
    new URLSearchParams(window.location.search).get("lang"),
  );
  if (explicit) currentChoice = explicit;
  return explicit ?? currentChoice ?? accountFallback;
}
/** An explicit choice belongs in the current URL, never in durable browser storage. */
export function rememberLanguage(language: Language): void {
  if (typeof window === "undefined" || !validLanguage(language)) return;
  clearLegacyLanguage();
  currentDocument();
  currentChoice = language;
  const url = new URL(window.location.href);
  if (url.searchParams.get("lang") !== language) {
    url.searchParams.set("lang", language);
    window.history.replaceState(window.history.state, "", url);
  }
}
export function languageHref(
  href: string,
  language: Language,
  docs = false,
): string {
  const url = new URL(href);
  if (docs) {
    const path = url.pathname.replace(/^\/de(?=\/|$)/, "") || "/";
    url.pathname = language === "de" ? `/de${path}` : path;
  }
  url.searchParams.set("lang", language);
  return url.href;
}

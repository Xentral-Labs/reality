export type SupportedLanguage = "en" | "de" | "nl" | "es";

export type LocalizationPreferences<Locale extends string = string> = {
  language: SupportedLanguage;
  locale: Locale;
  timezone: string;
};

export function resolveTranslation(
  catalogs: Record<Exclude<SupportedLanguage, "en">, Record<string, string>>,
  language: SupportedLanguage,
  source: string,
): string {
  if (language === "en") return source;
  const translated = catalogs[language][source];
  return translated?.trim() ? translated : source;
}

export function selectLanguage<Locale extends string>(
  preferences: LocalizationPreferences<Locale>,
  language: SupportedLanguage,
): LocalizationPreferences<Locale> {
  return { ...preferences, language };
}

const publicLanguages = new Set<SupportedLanguage>(["en", "de", "nl", "es"]);

export function resolvePublicLanguage(
  search: string,
  storedLanguage: string | null,
): SupportedLanguage {
  const requested = new URLSearchParams(search).get("lang");
  if (requested && publicLanguages.has(requested as SupportedLanguage))
    return requested as SupportedLanguage;
  if (storedLanguage && publicLanguages.has(storedLanguage as SupportedLanguage))
    return storedLanguage as SupportedLanguage;
  return "en";
}

export function isOriginalContent(element: Element | null): boolean {
  return Boolean(element?.closest('[data-localization="original"], code, pre, script, style'));
}

/** Preserve English source keys; otherwise the first translated alias wins. */
export function createCanonicalSourceResolver(
  catalogs: Record<Exclude<SupportedLanguage, "en">, Record<string, string>>,
): (value: string) => string {
  let sources: Map<string, string> | undefined;
  return (value) => {
    if (!sources) {
      sources = new Map();
      // A translated alias must not rename existing English UI copy.
      for (const dictionary of Object.values(catalogs)) {
        for (const source of Object.keys(dictionary)) sources.set(source, source);
      }
      for (const dictionary of Object.values(catalogs)) {
        for (const [source, translated] of Object.entries(dictionary)) {
          if (!sources.has(translated)) sources.set(translated, source);
        }
      }
    }
    return sources.get(value) ?? value;
  };
}

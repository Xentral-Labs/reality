import type { Language } from "../../shared/language";

/** Presentation the browser already knows; the account changes it in Settings afterwards. */
export type SignupPreferences = { language?: Language; timezone?: string };

/**
 * The supported languages, declared here rather than imported so this module keeps
 * type-only imports and can be unit-tested directly. The server pairs each one with
 * its display locale; a client never states a locale.
 */
const SUPPORTED: readonly Language[] = ["en", "de", "nl", "es"];

/** The signup request caps this field; a value that would be refused is never sent. */
const ZONE_LIMIT = 64;

function supported(value: string | undefined): Language | undefined {
  const language = value?.split("-")[0]?.toLowerCase();
  return SUPPORTED.find((candidate) => candidate === language);
}

export function signupPreferences(
  chosen: string | undefined,
  requested: readonly string[] = [],
  zone: string | undefined = undefined,
): SignupPreferences {
  const language = supported(chosen) ?? requested.map(supported).find(Boolean);
  const timezone = zone?.trim();
  return {
    ...(language ? { language } : {}),
    ...(timezone && timezone.length <= ZONE_LIMIT ? { timezone } : {}),
  };
}

/** Read what this browser states. An environment that answers nothing states nothing. */
export function browserSignupPreferences(chosen?: string): SignupPreferences {
  if (typeof window === "undefined") return {};
  let zone: string | undefined;
  try {
    zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch {
    /* A browser that cannot resolve a zone leaves the account default in place. */
  }
  return signupPreferences(chosen, navigator.languages ?? [navigator.language], zone);
}

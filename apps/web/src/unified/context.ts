import type { AnalyticsDefinition } from "../api";
/** Annotation is historical presentation, never tool authority. */
export function messageContext(content: string): {
  text: string;
  context?: { id: string; label: string };
  analytics?: AnalyticsHandoff;
} {
  const prefix = "\u001ereality.context.v1:";
  if (content.startsWith(prefix)) {
    try {
      const value = JSON.parse(content.slice(prefix.length));
      if (
        value.analytics &&
        typeof value.message === "string" &&
        validAnalyticsHandoff(value.analytics, value.analytics.tenant_id)
      )
        return { text: value.message, analytics: value.analytics };
      if (typeof value.commitment_id === "string" && typeof value.message === "string")
        return {
          text: value.message,
          context: {
            id: value.commitment_id,
            label: typeof value.label === "string" ? value.label : value.commitment_id,
          },
        };
    } catch {
      /* Historical text that is not a valid annotation remains readable. */
    }
  }
  return { text: content };
}

export type AnalyticsHandoff = { version: 1; tenant_id: string; definition: AnalyticsDefinition };
export function validAnalyticsHandoff(value: unknown, tenant: string): value is AnalyticsHandoff {
  if (!value || typeof value !== "object" || JSON.stringify(value).length > 16384) return false;
  const v = value as AnalyticsHandoff;
  return (
    v.version === 1 &&
    v.tenant_id === tenant &&
    !!v.definition &&
    typeof v.definition.dataset === "string" &&
    Array.isArray(v.definition.dimensions) &&
    v.definition.dimensions.length <= 4 &&
    Array.isArray(v.definition.measures) &&
    v.definition.measures.length > 0 &&
    v.definition.measures.length <= 4
  );
}
export function readAnalyticsHandoff(hash: string, tenant: string): AnalyticsHandoff | null {
  if (!hash.startsWith("#analytics=") || hash.length > 24000) return null;
  try {
    const encoded = hash.slice(11).replace(/-/g, "+").replace(/_/g, "/");
    const value = JSON.parse(
      new TextDecoder().decode(Uint8Array.from(atob(encoded), (c) => c.charCodeAt(0))),
    );
    return validAnalyticsHandoff(value, tenant) ? value : null;
  } catch {
    return null;
  }
}
export function analyticsHash(value: AnalyticsHandoff) {
  return (
    "#analytics=" +
    btoa(String.fromCharCode(...new TextEncoder().encode(JSON.stringify(value))))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "")
  );
}

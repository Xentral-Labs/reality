/** A service refusal as the API sends it (spec 286): English detail plus its identity. */
export type RefusalValue = {
  value: string;
  kind: "text" | "term" | "number" | "amount" | "quantity" | "date";
};
export type Refusal = {
  detail: string;
  code?: string;
  template?: string;
  values?: Record<string, RefusalValue>;
};
export type RefusalHelpers = {
  t: (source: string) => string;
  exact: (value: string, preserveTrailingZeros: boolean) => string;
  date: (value: string) => string;
};

const placeholder = /\{([a-z][a-z0-9_]*)\}/g;
const names = (text: string) => [...text.matchAll(placeholder)].map((match) => match[1]).sort();

/**
 * The refusal in the account language, with every value in its placeholder.
 * Falls back to the English sentence the service sent when the refusal is uncoded, a
 * value is missing, or a translation dropped a placeholder: never a broken sentence.
 */
export function localizeRefusal(refusal: Refusal, helpers: RefusalHelpers): string {
  const { detail, template, values = {} } = refusal;
  if (!template) return detail;
  const translated = helpers.t(template);
  const expected = names(template);
  if (names(translated).join() !== expected.join()) return detail;
  if (expected.some((name) => !(name in values))) return detail;
  return translated.replace(placeholder, (_match, name: string) => {
    const { value, kind } = values[name];
    if (kind === "term") return helpers.t(value);
    if (kind === "date") return helpers.date(value);
    if (kind === "amount") return helpers.exact(value, true);
    if (kind === "number" || kind === "quantity") return helpers.exact(value, false);
    return value;
  });
}

/** The refusal fields of an API or chat stream payload, whatever shape its detail has. */
export function refusalOf(payload: unknown, fallback: string): Refusal {
  const body = (payload ?? {}) as Record<string, unknown>;
  const detail = body.detail as unknown;
  const english =
    typeof detail === "string"
      ? detail
      : typeof (detail as { message?: unknown } | undefined)?.message === "string"
        ? (detail as { message: string }).message
        : typeof body.message === "string"
          ? body.message
          : fallback;
  return {
    detail: english,
    code:
      (typeof body.code === "string" ? body.code : undefined) ??
      (typeof (detail as { code?: unknown } | undefined)?.code === "string"
        ? (detail as { code: string }).code
        : undefined),
    template: typeof body.template === "string" ? body.template : undefined,
    values:
      body.values && typeof body.values === "object"
        ? (body.values as Record<string, RefusalValue>)
        : undefined,
  };
}

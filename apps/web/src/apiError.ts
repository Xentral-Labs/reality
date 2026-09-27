import { formatDate, formatExactDecimal, t } from "./localization";
import { localizeRefusal, refusalOf, type Refusal, type RefusalValue } from "./refusals";

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    /** The English sentence the service sent (spec 286); `message` is localized. */
    public detail: string = message,
    public template?: string,
    public values?: Record<string, RefusalValue>,
  ) {
    super(message);
  }
}

/** A refusal in the account language, falling back to the English sentence. */
export function refusalMessage(refusal: Refusal): string {
  return localizeRefusal(refusal, {
    t,
    exact: formatExactDecimal,
    date: (value) => formatDate(value),
  });
}

/** The error every form shows: the service refusal, localized once for all of them. */
export function refusalError(payload: unknown, status: number, fallback: string): APIError {
  const refusal = refusalOf(payload, fallback);
  return new APIError(
    refusalMessage(refusal),
    status,
    refusal.code,
    refusal.detail,
    refusal.template,
    refusal.values,
  );
}

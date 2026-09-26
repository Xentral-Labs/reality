import type { ReactNode } from "react";
import { t } from "../localization";

const compactFieldListClass = "space-y-1.5 text-sm";
const regularFieldListClass = "mt-3 space-y-2 text-sm";

export function DecisionReviewHeader({
  category,
  title,
  close,
  busy = false,
  titleId,
}: {
  category: string;
  title: string;
  close: () => void;
  busy?: boolean;
  titleId?: string;
}) {
  return (
    <header className="mb-5 flex items-start justify-between gap-4">
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-wide text-accent">{t(category)}</p>
        <h2 id={titleId} className="mt-2 text-xl font-semibold text-fg-strong">
          {t(title)}
        </h2>
      </div>
      <button className="br-btn shrink-0" disabled={busy} onClick={close}>
        {t("Close")}
      </button>
    </header>
  );
}

export function DecisionActionBar({
  busy = false,
  reject,
  edit,
  confirm,
  confirmLabel = "Confirm change",
  rejectLabel = "Do not approve",
  editLabel = "Request changes",
  children,
}: {
  busy?: boolean;
  reject?: () => void;
  edit?: () => void;
  confirm?: () => void;
  confirmLabel?: string;
  rejectLabel?: string;
  editLabel?: string;
  children?: ReactNode;
}) {
  return (
    <footer className="mt-6 flex flex-wrap items-center justify-end gap-3 border-t border-border-default pt-5">
      {children}
      {reject && (
        <button className="br-btn" disabled={busy} onClick={reject}>
          {t(rejectLabel)}
        </button>
      )}
      {edit && (
        <button className="br-btn" disabled={busy} onClick={edit}>
          {t(editLabel)}
        </button>
      )}
      {confirm && (
        <button className="br-btn br-btn-primary" disabled={busy} onClick={confirm}>
          {t(confirmLabel)}
        </button>
      )}
    </footer>
  );
}

function humanize(key: string) {
  return key.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function BusinessValue({
  value,
  labelFor = humanize,
}: {
  value: unknown;
  labelFor?: (key: string) => string;
}) {
  if (value === null || value === undefined || value === "")
    return <span className="text-fg-muted">—</span>;
  if (typeof value === "boolean") return <>{t(value ? "Yes" : "No")}</>;
  if (Array.isArray(value)) {
    if (!value.length) return <span className="text-fg-muted">—</span>;
    const structured = value.some((entry) => typeof entry === "object" && entry !== null);
    return structured ? (
      <div className="space-y-2">
        {value.map((entry, index) => (
          <div key={index} className="rounded-lg bg-surface-muted px-3 py-2">
            <BusinessValue value={entry} labelFor={labelFor} />
          </div>
        ))}
      </div>
    ) : (
      <div className="flex flex-wrap gap-2">
        {value.map((entry, index) => (
          <span key={index} className="rounded-full bg-surface-muted px-2.5 py-1 text-sm">
            <BusinessValue value={entry} labelFor={labelFor} />
          </span>
        ))}
      </div>
    );
  }
  if (typeof value === "object")
    return (
      <BusinessFieldList record={value as Record<string, unknown>} labelFor={labelFor} compact />
    );
  const text = String(value);
  if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/u.test(text))
    return (
      <a className="break-all text-accent underline" href={`mailto:${text}`}>
        {text}
      </a>
    );
  return <span className="break-words">{text}</span>;
}

export function BusinessFieldList({
  record,
  omit = [],
  labelFor = humanize,
  compact = false,
}: {
  record: Record<string, unknown>;
  omit?: string[];
  labelFor?: (key: string) => string;
  compact?: boolean;
}) {
  return (
    <dl className={compact ? compactFieldListClass : regularFieldListClass}>
      {Object.entries(record)
        .filter(([key]) => !omit.includes(key))
        .map(([key, value]) => (
          <div
            key={key}
            className="grid min-w-0 gap-1 sm:grid-cols-[minmax(120px,1fr)_2fr] sm:gap-3"
          >
            <dt className="break-words text-fg-muted">{t(labelFor(key))}</dt>
            <dd className="min-w-0">
              <BusinessValue value={value} labelFor={labelFor} />
            </dd>
          </div>
        ))}
    </dl>
  );
}

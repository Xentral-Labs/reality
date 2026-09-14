import { Children, useId, useState, type ReactNode } from "react";
import { t } from "../localization";
import { RegisterToolbar, RegisterWorkbench } from "./RegisterWorkbench";

export function InspectorCatalog({
  query,
  onQuery,
  count,
  countPlacement = "page",
  children,
}: {
  query: string;
  onQuery: (value: string) => void;
  count?: number;
  countPlacement?: "page" | "local";
  children: ReactNode;
}) {
  return (
    <RegisterWorkbench>
      <section className="register-surface" data-inspector-catalog>
        <RegisterToolbar
          count={count}
          countPlacement={countPlacement}
          search={
            <input
              type="search"
              className="br-control"
              aria-label={t("Search inspector")}
              placeholder={t("Search")}
              value={query}
              onChange={(event) => onQuery(event.target.value)}
            />
          }
        />
        <div className="space-y-3 border-t border-border-default p-4">
          {count === 0 ? (
            <p role="status" className="text-sm text-fg-muted">
              {t("No matching records")}
            </p>
          ) : (
            children
          )}
        </div>
      </section>
    </RegisterWorkbench>
  );
}

export function InspectorDisclosure({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [summary, ...body] = Children.toArray(children);
  return (
    <details
      className="inspector-disclosure rounded-xl border border-border-default bg-surface p-4"
      onToggle={(event) => setOpen(event.currentTarget.open)}
    >
      {summary}
      {open && body}
    </details>
  );
}

export function InspectorCatalogHeading({
  title,
  count,
  explanation,
}: {
  title: string;
  count: number;
  explanation: string;
}) {
  const [open, setOpen] = useState(false);
  const id = useId();
  return (
    <header className="relative flex items-center gap-2">
      <h2 className="font-semibold">
        {t(title)} · {count}
      </h2>
      <div onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
        <button
          type="button"
          aria-label={`${t(title)}: ${t("Information")}`}
          aria-expanded={open}
          aria-controls={id}
          aria-describedby={open ? id : undefined}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onClick={() => setOpen(true)}
          onKeyDown={(event) => {
            if (event.key === "Escape") setOpen(false);
          }}
          className="rounded px-1 text-fg-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
        >
          ⓘ
        </button>
        {open && (
          <p
            id={id}
            role="tooltip"
            className="absolute inset-x-0 top-full z-20 mt-2 rounded-lg border border-border-default bg-surface p-4 text-sm font-normal leading-relaxed text-fg shadow-lg"
          >
            {t(explanation)}
          </p>
        )}
      </div>
    </header>
  );
}

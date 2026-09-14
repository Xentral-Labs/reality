import { useEffect, useId, useState } from "react";
import { api } from "../api";
import { t } from "../localization";
import { ReadLine } from "./ReadState";

export function GraphRecordInput({
  tenant,
  kind,
  value,
  onChange,
  onSelect,
}: {
  tenant: string;
  kind: string;
  value: string;
  onChange: (value: string) => void;
  onSelect: (id: string) => void;
}) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [revision, retry] = useState(0);
  const [result, setResult] = useState<{
    key: string;
    rows: { id: string; title: string }[];
    error?: string;
  }>();
  const key = JSON.stringify([tenant, kind, value]);
  const ready = result?.key === key;
  const rows = ready ? result.rows : [];
  useEffect(() => {
    if (!open) return;
    let current = true;
    setActive(-1);
    const timer = setTimeout(() => {
      api
        .explorer(tenant, value, kind)
        .then((data) => {
          if (current)
            setResult({
              key,
              rows: data.sections.flatMap((section) =>
                section.collections.flatMap((collection) => collection.records),
              ),
            });
        })
        .catch((error) => {
          if (current) setResult({ key, rows: [], error: String(error.message) });
        });
    }, 250);
    return () => {
      current = false;
      clearTimeout(timer);
    };
  }, [tenant, kind, value, open, revision]);
  const choose = (recordId: string) => {
    setOpen(false);
    onChange(recordId);
    onSelect(recordId);
  };
  return (
    <div
      className="relative min-w-0 grow basis-64"
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
    >
      <label htmlFor={id} className="text-sm">
        {t("Record ID")}
      </label>
      <input
        id={id}
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={open}
        aria-controls={open ? `${id}-list` : undefined}
        aria-activedescendant={open && active >= 0 && rows[active] ? `${id}-${active}` : undefined}
        autoComplete="off"
        maxLength={120}
        className="br-control"
        value={value}
        placeholder={t("Search by name, SKU or ID")}
        onFocus={() => setOpen(true)}
        onChange={(event) => {
          setOpen(true);
          setActive(-1);
          onChange(event.target.value);
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            event.preventDefault();
            event.stopPropagation();
            setOpen(false);
          }
          if (event.key === "ArrowDown" || event.key === "ArrowUp") {
            event.preventDefault();
            setOpen(true);
            setActive((index) =>
              rows.length
                ? index < 0
                  ? event.key === "ArrowDown"
                    ? 0
                    : rows.length - 1
                  : (index + (event.key === "ArrowDown" ? 1 : rows.length - 1)) % rows.length
                : -1,
            );
          }
          if (event.key === "Enter" && open && active >= 0 && rows[active]) {
            event.preventDefault();
            choose(rows[active].id);
          }
        }}
      />
      {open && (
        <div className="absolute inset-x-0 top-full z-30 mt-1 max-h-72 overflow-auto rounded-lg border border-border-default bg-surface p-2 shadow-lg">
          {!ready ? (
            <p className="p-2 text-sm text-fg-muted">
              <ReadLine />
            </p>
          ) : result.error ? (
            <div role="alert" className="p-2 text-sm">
              <p>{t("Could not load this view")}</p>
              <button
                type="button"
                className="br-btn mt-2"
                onClick={() => {
                  setResult(undefined);
                  retry((n) => n + 1);
                }}
              >
                {t("Retry")}
              </button>
            </div>
          ) : !rows.length ? (
            <p role="status" className="p-2 text-sm text-fg-muted">
              {t("No matching records")}
            </p>
          ) : null}
          <ul id={`${id}-list`} role="listbox" aria-label={t("Record ID")}>
            {rows.map((row, index) => (
              <li
                key={row.id}
                id={`${id}-${index}`}
                role="option"
                aria-selected={active === index}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => choose(row.id)}
                className="cursor-pointer rounded p-2 text-sm hover:bg-surface-muted aria-selected:bg-accent-soft"
              >
                <span className="block break-words font-medium" data-localization="original">
                  {row.title}
                </span>
                <code className="block break-all text-xs text-fg-muted">{row.id}</code>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

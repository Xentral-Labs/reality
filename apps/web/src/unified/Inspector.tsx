import { inspectorValue } from "./inspectorFormat";
import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { InspectorData } from "../api";
import { t } from "../localization";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";

const compactGrid = "grid gap-4 md:grid-cols-2";
const compactSection = "rounded-lg border border-border-default bg-surface p-4";

export function Inspector({
  tenant,
  target,
  close,
}: {
  tenant: string;
  target: { kind: string; id: string };
  close: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [selected, select] = useState(target);
  const [history, setHistory] = useState<(typeof target)[]>([]);
  const { data, loading, error, refresh } = useRead(
    () => api.inspector(tenant, selected.kind, selected.id),
    [tenant, selected.kind, selected.id],
  );
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    const node = dialog.current;
    node?.showModal();
    return () => {
      node?.close();
      previous?.focus();
    };
  }, []);
  return (
    <dialog
      ref={dialog}
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
      className="m-auto max-h-[90vh] w-[min(680px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <div className="mb-5 flex justify-between gap-3">
        <button
          className="br-btn"
          disabled={!history.length}
          onClick={() => {
            select(history[history.length - 1]);
            setHistory(history.slice(0, -1));
          }}
        >
          {t("Back")}
        </button>
        <button className="br-btn" onClick={close}>
          {t("Close")}
        </button>
      </div>
      {!data ? (
        <ReadState loading={loading} error={error} retry={refresh} />
      ) : (
        <InspectorContent
          data={data}
          selectedKind={selected.kind}
          follow={(target) => {
            setHistory([...history, selected]);
            select(target);
          }}
        />
      )}
    </dialog>
  );
}

export function InspectorContent({
  data,
  selectedKind,
  follow,
  compact = false,
}: {
  data: Pick<InspectorData, "title" | "sections"> & Partial<InspectorData>;
  selectedKind: string;
  follow?: (target: { kind: string; id: string }) => void;
  compact?: boolean;
}) {
  const sections = compact ? (data.preview_sections ?? data.sections.slice(0, 3)) : data.sections;
  const businessPreview = compact && !!data.preview_sections;
  const title = inspectorValue(data.title, data.title_parts);
  const subtitle = inspectorValue(data.subtitle, data.subtitle_parts);
  const meaning = data.meaning ? inspectorValue(data.meaning, data.meaning_parts) : "";
  const compactMeaningIsRedundant =
    compact && meaning.includes(title) && (subtitle === "—" || meaning.includes(subtitle));
  return (
    <div className={compact ? compactGrid : undefined}>
      {compact ? (
        <header className="flex min-w-0 flex-wrap items-baseline gap-x-2 gap-y-1 md:col-span-2">
          <h2
            data-original-content={businessPreview ? "" : undefined}
            className="text-lg font-semibold text-fg-strong"
          >
            {title}
          </h2>
          {subtitle !== "—" && <span className="text-sm text-fg-muted">· {subtitle}</span>}
        </header>
      ) : (
        <h2 className="text-xl font-semibold text-fg-strong">{title}</h2>
      )}
      {(data.coverage?.movements_has_more || data.coverage?.reservations_has_more) && (
        <p className="my-3 text-caution-text">
          {t("More records are available in the workspace.")}
        </p>
      )}
      {!compact && <p className="my-3">{subtitle}</p>}
      {meaning && !compactMeaningIsRedundant && (
        <p className={`text-fg-muted ${compact ? "md:col-span-2" : ""}`}>{meaning}</p>
      )}
      {[
        ...sections,
        ...(compact ? [] : [{ title: "Technical details", rows: data.technical_rows || [] }]),
      ].map((section) => (
        <section key={section.title} className={compact ? compactSection : "mt-6"}>
          <h3 className="mb-3 font-medium">{t(section.title)}</h3>
          {section.rows.map((row, index) => (
            <div
              key={index}
              className="flex justify-between gap-4 border-b border-border-default py-2 text-sm"
            >
              <span className="min-w-0 break-words">
                <span data-original-content={row.original_label ? "" : undefined}>
                  {row.original_label ? row.label : t(row.label)}
                </span>
                {row.hint && (
                  <span className="mt-1 block text-xs text-fg-muted">{t(row.hint)}</span>
                )}
              </span>
              {row.link && follow ? (
                <button
                  data-original-content={
                    selectedKind === "fact" || (businessPreview && !row.translate_value)
                      ? ""
                      : undefined
                  }
                  className="max-w-[65%] shrink-0 break-words text-right text-accent underline"
                  onClick={() => follow(row.link!)}
                >
                  {row.translate_value
                    ? t(String(row.value))
                    : inspectorValue(row.value, row.display_parts)}
                </button>
              ) : (
                <span
                  data-original-content={
                    (businessPreview && !row.translate_value) ||
                    (selectedKind === "fact" &&
                      [
                        "Value",
                        "Exact predicate",
                        "Subject ID",
                        "Fact ID",
                        "Source record ID",
                      ].includes(row.label))
                      ? ""
                      : undefined
                  }
                  className="max-w-[65%] break-words text-right"
                >
                  {row.translate_value
                    ? t(String(row.value))
                    : inspectorValue(row.value, row.display_parts)}
                </span>
              )}
            </div>
          ))}
          {businessPreview && section.rows.length === 0 && (
            <p className="text-sm text-fg-muted">{t("No recorded details.")}</p>
          )}
          {"has_more" in section && section.has_more === true && (
            <p className="mt-3 text-sm text-fg-muted">
              {t("More records are available in the full explanation.")}
            </p>
          )}
        </section>
      ))}
      {!compact && data.source_payload && (
        <details className="mt-5" data-source-payload>
          <summary>{t("Original source")}</summary>
          <pre
            data-original-content
            className="mt-3 overflow-auto whitespace-pre-wrap break-all text-xs"
          >
            {data.source_payload}
          </pre>
          {data.source_payload_truncated && (
            <p className="mt-2 text-sm text-fg-muted" data-source-payload-truncated>
              {t("Only the beginning of the original source is shown.")}
            </p>
          )}
        </details>
      )}
    </div>
  );
}

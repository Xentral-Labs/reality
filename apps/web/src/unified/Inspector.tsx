import { recordOpened } from "./usePaletteHistory";
import { inspectorMeta, inspectorValue } from "./inspectorFormat";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { api } from "../api";
import type { InspectorData } from "../api";
import { currentLanguage, t } from "../localization";
import { RegisterPager } from "./WarehousePage";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { DecisionLine } from "./DecisionLine";

const compactGrid = "grid gap-4 md:grid-cols-2";
const compactSection = "rounded-lg border border-border-default bg-surface p-4";
// A row states one measure and, beside it, the qualifier that measure carries.
const rowInner = "flex items-baseline justify-between gap-4 text-sm";
const rowLink = "-mx-2 w-[calc(100%+1rem)] rounded px-2 py-2 text-left hover:bg-surface-muted";
const rowPlain = "py-2";
const linkText = "text-accent underline";
const valueBeside = "flex min-w-0 items-baseline gap-x-4";
const valueStacked = "flex min-w-0 flex-col items-end gap-y-0.5";
const measure = "shrink-0 tabular-nums";
const wholeValue = "max-w-[65%] break-words text-right";
const wholeValueLink = "max-w-[65%] shrink-0 break-words text-right";
const qualifier = "text-xs text-fg-muted";
const qualifierColumn = "min-w-[9.5rem] text-right";

export function Inspector({
  tenant,
  target,
  close,
  actions,
}: {
  tenant: string;
  target: { kind: string; id: string };
  close: () => void;
  actions?: (target: { kind: string; id: string }) => ReactNode;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [selected, select] = useState(target);
  const [history, setHistory] = useState<(typeof target)[]>([]);
  const [memberPage, setMemberPage] = useState(1);
  const language = currentLanguage();
  const {
    data: loaded,
    loading,
    error,
    refresh,
  } = useRead(
    () =>
      api
        .inspector(tenant, selected.kind, selected.id, false, memberPage, language)
        .then((data) => ({
          data,
          tenant,
          kind: selected.kind,
          id: selected.id,
          memberPage,
          language,
        })),
    [tenant, selected.kind, selected.id, memberPage, language],
  );
  const data =
    loaded?.tenant === tenant &&
    loaded.kind === selected.kind &&
    loaded.id === selected.id &&
    loaded.memberPage === memberPage &&
    loaded.language === language
      ? loaded.data
      : undefined;
  useEffect(() => {
    if (data && !loading && !error) recordOpened(tenant, selected.kind, selected.id);
  }, [data, loading, error, tenant, selected.kind, selected.id]);
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
            setMemberPage(1);
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
        <>
          <InspectorContent
            data={data}
            tenant={tenant}
            selectedKind={selected.kind}
            follow={(target) => {
              setMemberPage(1);
              setHistory([...history, selected]);
              select(target);
            }}
          />
          {data.member_page && data.member_page.total > 0 && (
            <RegisterPager page={data.member_page} change={setMemberPage} />
          )}
          {actions && (
            <div className="mt-5 flex flex-wrap justify-end gap-2">{actions(selected)}</div>
          )}
        </>
      )}
    </dialog>
  );
}

const decisionRoles = {
  created: "Created by decision",
  changed: "Changed by decision",
  caused: "Caused by decision",
} as const;

export function InspectorContent({
  data,
  selectedKind,
  follow,
  compact = false,
  tenant,
}: {
  data: Pick<InspectorData, "title" | "sections"> & Partial<InspectorData>;
  selectedKind: string;
  follow?: (target: { kind: string; id: string }) => void;
  compact?: boolean;
  /** The company, so a decision behind the record can be opened. */
  tenant?: string;
}) {
  const sections = compact ? (data.preview_sections ?? data.sections.slice(0, 3)) : data.sections;
  const decisions = data.decisions ?? [];
  const businessPreview = compact && !!data.preview_sections;
  const title = inspectorValue(data.title, data.title_parts);
  const subtitle = inspectorValue(data.subtitle, data.subtitle_parts);
  const meaning = data.meaning ? inspectorValue(data.meaning, data.meaning_parts) : "";
  const compactMeaningIsRedundant =
    compact && meaning.includes(title) && (subtitle === "—" || meaning.includes(subtitle));
  return (
    <div
      data-compact-inspector={compact || undefined}
      className={compact ? compactGrid : undefined}
    >
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
        // Spec 263 FR-013: every detail view names the decisions behind its record;
        // registers and lists stay short and never carry them.
        ...(!compact && decisions.length
          ? [{ title: "Decisions", rows: [], decisions: true }]
          : []),
        ...(compact ? [] : [{ title: "Technical details", rows: data.technical_rows || [] }]),
      ].map((section) =>
        "decisions" in section ? (
          <section key="decisions" className="mt-6" data-record-decisions>
            <h3 className="mb-3 font-medium">{t("Decisions")}</h3>
            {decisions.map((decision) => (
              <div
                key={`${decision.role}:${decision.id}`}
                className={`${rowInner} ${rowPlain} border-b border-border-default`}
                data-record-decision={decision.id}
              >
                <span className="min-w-0 break-words">{t(decisionRoles[decision.role])}</span>
                <span className={wholeValue}>
                  <DecisionLine decision={decision} tenant={tenant} />
                </span>
              </div>
            ))}
          </section>
        ) : (
          <section key={section.title} className={compact ? compactSection : "mt-6"}>
            <h3 className="mb-3 font-medium">{t(section.title)}</h3>
            {section.rows.map((row, index) => {
              const linked = !!row.link && !!follow;
              const label = (
                <span className="min-w-0 break-words">
                  <span data-original-content={row.original_label ? "" : undefined}>
                    {row.original_label ? row.label : t(row.label)}
                  </span>
                  {row.hint && (
                    <span className="mt-1 block text-xs text-fg-muted">{t(row.hint)}</span>
                  )}
                </span>
              );
              const meta = inspectorMeta(row);
              // The measure stands in its own column so a section reads as one;
              // the qualifier it carries sits beside it, never inside it.
              const value = (
                <span
                  className={
                    meta
                      ? compact
                        ? valueStacked
                        : valueBeside
                      : linked
                        ? wholeValueLink
                        : wholeValue
                  }
                >
                  <span
                    data-original-content={
                      linked
                        ? selectedKind === "fact" || (businessPreview && !row.translate_value)
                          ? ""
                          : undefined
                        : (businessPreview && !row.translate_value) ||
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
                    className={`${linked ? linkText : ""} ${meta ? measure : ""}`}
                  >
                    {row.translate_value
                      ? t(String(row.value))
                      : inspectorValue(row.value, row.display_parts)}
                  </span>
                  {meta && (
                    <span
                      data-original-content=""
                      className={`${qualifier} ${compact ? "" : qualifierColumn}`}
                    >
                      {meta}
                    </span>
                  )}
                </span>
              );
              return (
                <div key={index} className="border-b border-border-default">
                  {linked ? (
                    <button className={`${rowInner} ${rowLink}`} onClick={() => follow(row.link!)}>
                      {label}
                      {value}
                    </button>
                  ) : (
                    <div className={`${rowInner} ${rowPlain}`}>
                      {label}
                      {value}
                    </div>
                  )}
                </div>
              );
            })}
            {businessPreview && section.rows.length === 0 && (
              <p className="text-sm text-fg-muted">{t("No recorded details.")}</p>
            )}
            {"has_more" in section && section.has_more === true && (
              <p className="mt-3 text-sm text-fg-muted">
                {t("More records are available in the full explanation.")}
              </p>
            )}
          </section>
        ),
      )}
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

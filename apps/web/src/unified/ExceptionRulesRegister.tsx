import { Fragment, useState } from "react";
import { ArrowRight } from "lucide-react";
import { api, operationsApi } from "../api";
import { currentLanguage, t } from "../localization";
import { InspectorCatalog } from "./InspectorCatalog";
import { RegisterTable } from "./RegisterTable";
import { PreviewButton, TablePreview } from "./InlinePreview";
import { Inspector } from "./Inspector";
import { ProjectionFreshness } from "./ProjectionFreshness";
import { ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";
import type { Selection } from "./routing";

const severities: Record<string, string> = {
  critical: "Critical",
  high: "High",
  normal: "Normal",
  low: "Low",
};
/** How many open findings the quick preview lists before pointing at the Exceptions page. */
const previewSize = 10;
const columns = 5;

type ExceptionClass = Awaited<ReturnType<typeof api.exceptionCatalog>>["classes"][number];
/** The class label in the UI language when the resource catalog records one. */
export const label = (row: ExceptionClass) => row.labels?.[currentLanguage()] || t(row.label);

/**
 * The Exception rules tab: every finding type the catalog knows, one row each, with the
 * number of findings currently open for it. The quick preview carries the full catalog
 * description and lists the open findings themselves. Counts and findings are the same
 * read-time derivation the Exceptions page shows; nothing here is stored.
 */
export function ExceptionRulesRegister({
  tenant,
  navigate,
}: {
  tenant: string;
  navigate: (value: Partial<Selection>) => void;
}) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState("");
  const [target, setTarget] = useState<{ kind: string; id: string } | null>(null);
  const catalog = useRead(() => api.exceptionCatalog(), []);
  const summary = useRead(() => operationsApi.attentionSummary(tenant), [tenant]);
  const findings = useRead(
    () =>
      open ? operationsApi.attention(tenant, "", "", 1, open, previewSize) : Promise.resolve(null),
    [tenant, open],
  );
  const counts = Object.fromEntries(
    (summary.data?.classes || []).map((row) => [row.class_id, row.open]),
  );
  const needle = search.toLocaleLowerCase();
  const rows = (catalog.data?.classes || []).filter((row) =>
    [label(row), row.label, row.description, row.owner, row.id]
      .join(" ")
      .toLocaleLowerCase()
      .includes(needle),
  );
  // A company without a completed generation has no counts yet: a placeholder, not zero.
  const uninitialized = summary.data?.metadata?.state === "uninitialized";
  const openCount = (id: string) =>
    summary.data && !uninitialized ? (counts[id] ?? 0) : summary.error || uninitialized ? "—" : "…";
  const listed = findings.data?.page.number === 1 ? findings.data.items : [];
  return (
    <div data-inline-exception-catalog>
      <InspectorCatalog
        query={search}
        onQuery={setSearch}
        count={catalog.data ? rows.length : undefined}
      >
        {!catalog.data ? (
          <ReadState loading={catalog.loading} error={catalog.error} retry={catalog.refresh} />
        ) : (
          <>
            {summary.error && (
              <ReadState loading={false} error={summary.error} retry={summary.refresh} />
            )}
            <ProjectionFreshness
              metadata={summary.data?.metadata}
              refresh={summary.refresh}
              loading={summary.loading}
              error={summary.error}
            />
            <div className="register-table-inset">
              <RegisterTable
                busy={summary.loading}
                empty={{ hint: t("No matching exception classes.") }}
                cursorView={{ id: "inspector:exceptions", widths: [190, 240, 90, 130, 80] }}
              >
                <thead>
                  <tr>
                    <th>{t("Finding type")}</th>
                    <th>{t("What it detects")}</th>
                    <th>{t("Severity")}</th>
                    <th>{t("Currently open")}</th>
                    <th>{t("Actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => {
                    const expanded = open === row.id;
                    const count = counts[row.id] ?? 0;
                    return (
                      <Fragment key={row.id}>
                        <tr data-exception-class={row.id}>
                          <td className="font-semibold">{label(row)}</td>
                          <td>
                            <div
                              className="line-clamp-2 whitespace-normal text-fg-muted"
                              data-localization="original"
                              title={row.description}
                            >
                              {row.description}
                            </div>
                          </td>
                          <td>{t(severities[row.severity] || row.severity)}</td>
                          <td data-open-count>{openCount(row.id)}</td>
                          <td>
                            <PreviewButton
                              open={expanded}
                              controls={`exception-preview-${row.id}`}
                              label={label(row)}
                              toggle={() => setOpen(expanded ? "" : row.id)}
                            />
                          </td>
                        </tr>
                        <TablePreview
                          id={`exception-preview-${row.id}`}
                          open={expanded}
                          columns={columns}
                        >
                          <div className="max-w-3xl space-y-5">
                            <div className="rounded-lg bg-surface p-4" data-open-findings>
                              <h3 className="font-semibold">
                                {t("Currently open")} · {openCount(row.id)}
                              </h3>
                              {!findings.data && (findings.loading || findings.error) ? (
                                <ReadState
                                  loading={findings.loading}
                                  error={findings.error}
                                  retry={findings.refresh}
                                />
                              ) : !listed.length ? (
                                <div className="mt-2 text-sm text-fg-muted">
                                  {t(
                                    findings.data?.metadata?.state === "uninitialized"
                                      ? "Awaiting first calculation."
                                      : "No open findings of this type right now.",
                                  )}
                                </div>
                              ) : (
                                <ul className="mt-2 divide-y divide-border-default">
                                  {listed.map((finding) => (
                                    <li
                                      key={finding.id}
                                      className="flex flex-wrap items-center justify-between gap-3 py-2"
                                    >
                                      <div className="min-w-0 flex-1">
                                        <div className="text-sm font-medium">
                                          {finding.context || label(row)}
                                        </div>
                                        <div className="text-xs text-fg-muted">
                                          {finding.impact}
                                        </div>
                                      </div>
                                      <button
                                        className="br-btn"
                                        onClick={() =>
                                          setTarget({ kind: "exception", id: finding.id })
                                        }
                                      >
                                        {t("Explain finding")}
                                      </button>
                                    </li>
                                  ))}
                                </ul>
                              )}
                              {count > listed.length && listed.length > 0 && (
                                <div className="br-help mt-2">
                                  {listed.length} / {count}
                                </div>
                              )}
                              {count > 0 && (
                                <button
                                  className="br-btn br-btn-primary mt-3"
                                  onClick={() =>
                                    navigate({
                                      route: "attention",
                                      q: row.id,
                                      severity: "",
                                      exception: "",
                                      page: 1,
                                    })
                                  }
                                >
                                  {t("Open in Exceptions")}
                                  <ArrowRight size={16} aria-hidden="true" />
                                </button>
                              )}
                            </div>
                            <div>
                              <h3 className="text-lg font-semibold text-fg-strong">{label(row)}</h3>
                              <div className="mt-2 text-sm leading-6" data-localization="original">
                                {row.description}
                              </div>
                              <dl className="mt-3 grid gap-2 text-sm">
                                <div>
                                  <dt className="font-semibold">{t("Responsible area")}</dt>
                                  <dd data-localization="original">{row.owner}</dd>
                                </div>
                                <div>
                                  <dt className="font-semibold">{t("How it clears")}</dt>
                                  <dd data-localization="original">{row.clears_through}</dd>
                                </div>
                              </dl>
                              <div className="br-help mt-3" data-localization="original">
                                {row.id} · {row.severity}
                              </div>
                            </div>
                          </div>
                        </TablePreview>
                      </Fragment>
                    );
                  })}
                </tbody>
              </RegisterTable>
            </div>
          </>
        )}
      </InspectorCatalog>
      {target && <Inspector tenant={tenant} target={target} close={() => setTarget(null)} />}
    </div>
  );
}

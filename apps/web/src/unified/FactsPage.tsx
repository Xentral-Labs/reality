import type { ReactNode } from "react";
import { RegisterWorkbench, RegisterHeader, RegisterToolbar } from "./RegisterWorkbench";
import { useRegisterQuery } from "./TableContext";
import { RegisterTable } from "./RegisterTable";
import { api } from "../api";
import { formatDateTime, t } from "../localization";
import { ReadState } from "./ReadState";
import { Inspector } from "./Inspector";
import { RegisterPager } from "./WarehousePage";
import { useRead } from "./useCompanyContext";
import type { Selection } from "./routing";

const versionPrefix = " · v";
export function FactsPage({
  selection,
  navigate,
  graph,
  embedded = false,
  extraFilters,
}: {
  embedded?: boolean;
  extraFilters?: ReactNode;
  graph?: (target: { kind: string; id: string }) => void;
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const { tenant, q, page, factSubjectType, factSubject, factSource, factTarget, entry } =
    selection;
  const table = useRegisterQuery();
  const read = useRead(
    () => api.facts(tenant, q, page, factSubjectType, factSubject, factSource, table),
    [
      tenant,
      q,
      page,
      factSubjectType,
      factSubject,
      factSource,
      table.size,
      table.sort,
      table.sort_direction,
    ],
  );
  const data = read.data;
  const change = (values: Partial<Selection>) => navigate({ ...values, page: 1, entry: "" });
  const types = Array.from(
    new Set([...(data?.subject_types || []), ...(factSubjectType ? [factSubjectType] : [])]),
  );
  return (
    <RegisterWorkbench>
      {!embedded && <RegisterHeader title="Business Facts" />}
      <section className="register-surface">
        <form
          className="register-facts-toolbar"
          onSubmit={(event) => {
            event.preventDefault();
            change({ q: String(new FormData(event.currentTarget).get("q") || "") });
          }}
        >
          <RegisterToolbar
            count={data?.page.total}
            search={
              <label className="min-w-0 basis-full text-sm sm:basis-0 sm:flex-1">
                {t("Search")}
                <input
                  key={q}
                  name="q"
                  maxLength={500}
                  aria-label={t("Search observations")}
                  defaultValue={q}
                  placeholder={t("Predicate, value, subject ID or source reference")}
                  className="br-control mt-2 w-full"
                />
              </label>
            }
            filters={
              <>
                {extraFilters}
                <label className="text-sm">
                  {t("Subject type")}
                  <select
                    aria-label={t("Subject type")}
                    value={factSubjectType}
                    className="br-control mt-2 block"
                    onChange={(event) =>
                      change({ factSubjectType: event.target.value, factSubject: "" })
                    }
                  >
                    <option value="">{t("All subject types")}</option>
                    {types.map((type) => (
                      <option key={type} value={type} data-original-content>
                        {type}
                      </option>
                    ))}
                  </select>
                </label>
              </>
            }
            submit={
              <button className="br-btn" type="submit">
                {t("Search")}
              </button>
            }
          />
        </form>
        {data?.subject_types_has_more && (
          <p className="text-sm text-fg-muted">
            {t(
              "The first 100 subject types are listed. Search can find observations of other types.",
            )}
          </p>
        )}
        {(factSource || factSubject || q) && (
          <div className="flex flex-wrap items-center gap-3 text-sm">
            {factSource && (
              <span>
                {t("Source record")}:{" "}
                <code data-original-content className="break-all">
                  {factSource}
                </code>
              </span>
            )}
            {factSubject && (
              <span>
                {t("Subject")}:{" "}
                <code data-original-content className="break-all">
                  {factSubject}
                </code>
              </span>
            )}
            <button
              className="br-btn"
              onClick={() =>
                change({ factSource: "", factSubject: "", factSubjectType: "", q: "" })
              }
            >
              {t("Clear filters")}
            </button>
          </div>
        )}
        {read.error || (read.loading && !data) ? (
          <ReadState loading={read.loading} error={read.error} retry={read.refresh} rows={8} />
        ) : (
          data && (
            <>
              <RegisterTable
                busy={read.loading}
                actionWidth={graph ? 112 : 80}
                empty={{
                  title: t("No observations found"),
                  hint: t(
                    "Try another search or clear the filters. Facts appear when a source-backed observation is recorded.",
                  ),
                }}
                footer={
                  <RegisterPager
                    page={data.page}
                    change={(page) => navigate({ page, entry: "" })}
                  />
                }
              >
                <thead>
                  <tr>
                    {[
                      "Observation",
                      "Value",
                      "Subject",
                      "Observed at",
                      "Source",
                      "Interpretation rule",
                      "Actions",
                    ].map((label) => (
                      <th key={label}>{t(label)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((row) => (
                    <tr key={row.id} data-fact-row>
                      <td data-original-content>{row.predicate}</td>
                      <td data-original-content>{row.value}</td>
                      <td data-original-content>
                        {row.subject_type} · {row.subject_id}
                      </td>
                      <td>{formatDateTime(row.observed_at)}</td>
                      <td>
                        {row.source ? (
                          <span data-original-content>
                            {row.source.system} · {row.source.external_id}
                            {row.source_version != null
                              ? `${versionPrefix}${row.source_version}`
                              : ""}
                          </span>
                        ) : (
                          t("No linked source recorded")
                        )}
                      </td>
                      <td>
                        {row.interpretation_rule ? (
                          <span data-original-content>
                            {row.interpretation_rule.logical_name}
                            {versionPrefix}
                            {row.interpretation_rule.version}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td>
                        {graph && (
                          <button
                            className="br-btn"
                            onClick={() => graph({ kind: "fact", id: row.id })}
                          >
                            {t("Record graph")}
                          </button>
                        )}
                        <button
                          className="br-btn"
                          onClick={() => navigate({ entry: row.id, factTarget: "fact" })}
                        >
                          {t("Explain observation")}
                        </button>
                        <button
                          className="br-btn"
                          onClick={() =>
                            change({
                              factSubjectType: row.subject_type,
                              factSubject: row.subject_id,
                              factSource: "",
                              q: "",
                            })
                          }
                        >
                          {t("Related observations")}
                        </button>
                        {row.source_record_id && (
                          <button
                            className="br-btn"
                            onClick={() =>
                              navigate({
                                entry: row.source_record_id!,
                                factTarget: "source_record",
                              })
                            }
                          >
                            {t("Open original")}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </RegisterTable>
            </>
          )
        )}
      </section>
      {entry && (
        <Inspector
          tenant={tenant}
          target={{ kind: factTarget, id: entry }}
          close={() => navigate({ entry: "" })}
        />
      )}
    </RegisterWorkbench>
  );
}

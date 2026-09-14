import { useState } from "react";
import { api } from "../api";
import { t } from "../localization";
import { FactsPage } from "./FactsPage";
import { RegisterWorkbench, RegisterToolbar } from "./RegisterWorkbench";
import { RegisterTable } from "./RegisterTable";
import { RegisterPager } from "./WarehousePage";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { Inspector } from "./Inspector";
import type { Selection } from "./routing";

const families = [
  ["all", "All records"],
  ["fact", "Additional facts"],
  ["party", "Parties"],
  ["item", "Items"],
  ["location", "Locations"],
  ["source_record", "Source records"],
  ["document", "Documents"],
  ["document_line", "Document lines"],
  ["commitment", "Commitments"],
  ["reservation", "Reservations"],
  ["movement", "Movements"],
  ["ledger_entry", "Ledger entries"],
  ["business_event", "Business events"],
];
type Target = { kind: string; id: string };
export function InspectorRecordsPage({
  selection,
  navigate,
  graph,
}: {
  selection: Selection;
  navigate: (value: Partial<Selection>) => void;
  graph: (target: Target) => void;
}) {
  const { tenant, q, page, tableSize } = selection;
  const requested =
    selection.inspectorRecordKind ||
    (selection.factSubject || selection.factSource || selection.factSubjectType || selection.entry
      ? "fact"
      : "all");
  const kind = families.some(([key]) => key === requested) ? requested : "all";
  const [target, setTarget] = useState<Target | null>(null);
  const read = useRead(
    () =>
      kind === "fact"
        ? Promise.resolve(null)
        : api.inspectorRecords(tenant, kind, q, page, tableSize),
    [tenant, kind, q, page, tableSize],
  );
  const picker = (
    <label className="text-sm">
      {t("Record type")}
      <select
        className="br-control mt-2 block"
        aria-label={t("Record type")}
        value={kind}
        onChange={(event) => {
          setTarget(null);
          navigate({
            inspectorRecordKind: event.target.value,
            page: 1,
            entry: "",
            factSubjectType: "",
            factSubject: "",
            factSource: "",
            q: "",
          });
        }}
      >
        {families.map(([key, label]) => (
          <option key={key} value={key}>
            {t(label)}
          </option>
        ))}
      </select>
    </label>
  );
  if (kind === "fact")
    return (
      <FactsPage
        embedded
        selection={selection}
        navigate={navigate}
        graph={graph}
        extraFilters={picker}
      />
    );
  return (
    <RegisterWorkbench>
      <section className="register-surface" data-inspector-records>
        <form
          className="register-toolbar-form"
          onSubmit={(event) => {
            event.preventDefault();
            navigate({
              q: String(new FormData(event.currentTarget).get("q") || ""),
              page: 1,
              entry: "",
            });
          }}
        >
          <RegisterToolbar
            count={read.data?.page.total}
            search={
              <input
                key={q}
                name="q"
                className="br-control"
                maxLength={500}
                defaultValue={q}
                aria-label={t("Search records")}
                placeholder={t("Search by name, type, value or ID")}
              />
            }
            filters={picker}
            submit={
              <button className="br-btn" type="submit">
                {t("Search")}
              </button>
            }
          />
        </form>
        {read.error || (read.loading && !read.data) ? (
          <ReadState loading={read.loading} error={read.error} retry={read.refresh} rows={8} />
        ) : (
          read.data && (
            <>
              <div className="register-table-inset">
                <RegisterTable
                  busy={read.loading}
                  cursorView={{
                    id: `inspector-records:${kind}`,
                    widths: [160, 280, 360, 220, 112],
                  }}
                  actionWidth={112}
                  footer={
                    <>
                      <label className="flex items-center gap-2 whitespace-nowrap text-xs">
                        {t("Rows per page")}
                        <select
                          className="br-control"
                          aria-label={t("Rows per page")}
                          value={tableSize}
                          onChange={(event) =>
                            navigate({
                              tableSize: Number(event.target.value) as 25 | 50 | 100,
                              page: 1,
                            })
                          }
                        >
                          {[25, 50, 100].map((size) => (
                            <option key={size}>{size}</option>
                          ))}
                        </select>
                      </label>
                      <RegisterPager
                        page={read.data.page}
                        change={(page) => navigate({ page, entry: "" })}
                      />
                    </>
                  }
                >
                  <thead>
                    <tr>
                      {["Record type", "Record", "Details", "Record ID", "Actions"].map((label) => (
                        <th key={label}>{t(label)}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {read.data.items.map((row) => (
                      <tr
                        key={`${row.kind}:${row.id}`}
                        data-inspector-record={`${row.kind}:${row.id}`}
                      >
                        <td>{t(row.label)}</td>
                        <td data-localization="original">{row.title}</td>
                        <td>
                          {row.details.map((detail, index) => (
                            <span key={detail.label}>
                              {index > 0 && " · "}
                              {t(detail.label)}:{" "}
                              <span data-localization="original">
                                {typeof detail.value === "object"
                                  ? JSON.stringify(detail.value)
                                  : String(detail.value ?? "—")}
                              </span>
                            </span>
                          ))}
                        </td>
                        <td data-localization="original">{row.id}</td>
                        <td>
                          <button
                            className="br-btn"
                            onClick={() => setTarget({ kind: row.kind, id: row.id })}
                          >
                            {t("Details")}
                          </button>
                          <button
                            className="br-btn"
                            onClick={() => graph({ kind: row.kind, id: row.id })}
                          >
                            {t("Record graph")}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </RegisterTable>
              </div>
            </>
          )
        )}
      </section>
      {target && (
        <Inspector
          key={`${tenant}:${target.kind}:${target.id}`}
          tenant={tenant}
          target={target}
          close={() => setTarget(null)}
        />
      )}
    </RegisterWorkbench>
  );
}

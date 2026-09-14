import { readLiveView } from "./ProjectionDataDialog";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { t } from "../localization";
import { rowIsNew, viewRoute } from "./storylineState";
import { selectionUrl, type Selection } from "./routing";

const markerClasses: Record<string, string> = {
  fresh: "shadow-[inset_3px_0_0_var(--positive-text)]",
  plain: "",
};
const hidden = new Set(["tenant_id", "payload", "metadata", "trace", "causal_values"]);

/**
 * The ordinary view a chapter names, read through the shared live reads, with
 * the rows the chapter added marked. The full page is one click away; embedding
 * it whole would portal its header into the shell header (research R6).
 */
export function StorylineStage({
  tenant,
  view,
  label,
  newIds,
  revision,
  selection,
  navigate,
}: {
  tenant: string;
  view: string | null;
  label: string;
  newIds: Set<string>;
  revision: number;
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const route = viewRoute(view);
  const read = useRead(
    () => (view ? readLiveView(tenant, view).catch(() => []) : Promise.resolve([])),
    [tenant, view, revision],
  );
  const rows = (read.data || []).slice(0, 40) as Record<string, unknown>[];
  const columns = Array.from(new Set(rows.flatMap((row) => Object.keys(row))))
    .filter((key) => !hidden.has(key))
    .slice(0, 7);
  const text = (value: unknown) =>
    value === null || value === undefined
      ? "—"
      : typeof value === "object"
        ? JSON.stringify(value)
        : String(value);
  const added = rows.filter((row) => rowIsNew(row, newIds)).length;
  return (
    <section className="flex min-w-0 flex-col gap-3" data-storyline-stage aria-label={t("View")}>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className="text-[11px] uppercase tracking-wider text-fg-muted">{t("View")}</p>
          <h3 className="text-base font-semibold text-fg-strong" data-localization="original">
            {label || (view || "").replace(/^view:/, "")}
          </h3>
        </div>
        <div className="flex items-center gap-3 text-xs text-fg-muted">
          {added > 0 && (
            <span
              className="rounded-full bg-positive-bg px-2 py-0.5 text-positive-text"
              data-storyline-added
            >
              {added} {t("new since this step")}
            </span>
          )}
          {route && (
            <a
              className="br-btn"
              href={selectionUrl({ ...selection, ...route, page: 1, q: "" } as Selection)}
              onClick={(event) => {
                event.preventDefault();
                navigate({ ...route, page: 1, q: "" });
              }}
            >
              {t("Open in app")}
            </a>
          )}
        </div>
      </div>
      {!view ? (
        <p className="text-sm text-fg-muted">{t("This step opens no view.")}</p>
      ) : read.loading && !read.data ? (
        <ReadState loading error={undefined} retry={read.refresh} />
      ) : !rows.length ? (
        <p
          role="status"
          className="rounded-xl border border-border-default bg-surface px-4 py-6 text-sm text-fg-muted"
        >
          {t("No rows yet. The view fills as the story goes on.")}
        </p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-border-default bg-surface">
          <table className="w-full min-w-[560px] text-[13px]">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th
                    key={column}
                    className="border-b border-border-default bg-surface-sunken px-3 py-2 text-left text-[11px] uppercase tracking-wider text-fg-muted"
                    data-localization="original"
                  >
                    {column.replaceAll("_", " ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => {
                const fresh = rowIsNew(row, newIds);
                return (
                  <tr
                    key={String(row.id ?? index)}
                    data-storyline-row-new={fresh ? "true" : undefined}
                    className={fresh ? "bg-positive-bg" : undefined}
                  >
                    {columns.map((column, position) => (
                      <td
                        key={column}
                        className={`max-w-[260px] truncate border-b border-border-subtle px-3 py-2 ${markerClasses[position === 0 && fresh ? "fresh" : "plain"]}`}
                        data-localization="original"
                        title={text(row[column])}
                      >
                        {text(row[column])}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

import { FilterChip } from "./FilterChip";
import { EyeOff, ChevronDown, ChevronRight } from "lucide-react";
import { createPortal } from "react-dom";
import { useRegisterTools } from "./RegisterWorkbench";
import { ExternalLink, FileText, ListFilter, Pencil, Play } from "lucide-react";
import {
  Children,
  Fragment,
  cloneElement,
  isValidElement,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactElement,
  type ReactNode,
  type HTMLAttributes,
} from "react";
import { t } from "../localization";
import { reading } from "./ReadState";
import { useTableContext } from "./TableContext";
import { TablePreview } from "./InlinePreview";
import { layoutKey, validateLayout, type TableLayout } from "./tablePreferences";
type Node = ReactElement<{
  children?: ReactNode;
  title?: string;
  "aria-label"?: string;
  className?: string;
  onClick?: HTMLAttributes<HTMLElement>["onClick"];
  "data-inline-preview"?: boolean;
  "data-action-meaning"?: string;
  "aria-expanded"?: boolean;
}>;
function nodes(value: ReactNode): Node[] {
  return Children.toArray(value).flatMap((child) =>
    isValidElement(child)
      ? child.type === Fragment
        ? nodes((child as Node).props.children)
        : [child as Node]
      : [],
  );
}
function text(value: ReactNode): string {
  return Children.toArray(value)
    .map((child) => (isValidElement(child) ? text((child as Node).props.children) : String(child)))
    .join(" ")
    .trim();
}
type Profile = { widths: number[]; sorts: (string | null)[] };
const profiles: Record<string, Profile> = {
  "master-data:customer": {
    widths: [240, 130, 140, 90, 180, 90, 80],
    sorts: ["name", null, null, null, null, "status"],
  },
  "master-data:supplier": {
    widths: [240, 130, 140, 90, 180, 90, 80],
    sorts: ["name", null, null, null, null, "status"],
  },
  "master-data:location": {
    widths: [220, 120, 200, 120, 180, 90, 80],
    sorts: ["name", null, null, null, null, "status"],
  },
  "master-data:item": {
    widths: [240, 120, 80, 100, 180, 180, 90, 80],
    sorts: ["name", null, null, null, null, null, "status"],
  },
  "orders-deliveries:deliveries": {
    widths: [220, 220, 180, 130, 100, 100, 100, 100, 80],
    sorts: ["counterparty", "item", null, "due_at", null, null, "open", "status"],
  },
  "orders-deliveries:customer-orders": {
    widths: [150, 220, 130, 130, 80, 180, 80],
    sorts: ["number", null, "date", "amount", null, null],
  },
  "orders-deliveries:supplier-orders": {
    widths: [150, 220, 130, 130, 80, 180, 80],
    sorts: ["number", null, "date", "amount", null, null],
  },
  "warehouse:stock": {
    widths: [280, 100, 100, 100, 80],
    sorts: ["name", "physical", "reserved", "available"],
  },
  "warehouse:reservations": {
    widths: [240, 200, 100, 100, 80],
    sorts: [null, null, "quantity", "status"],
  },
  "warehouse:movements": {
    widths: [240, 220, 100, 100, 80],
    sorts: [null, null, "quantity", null],
  },
  "finance:balances": {
    widths: [240, 120, 130, 130, 130, 90, 90, 110, 170],
    sorts: ["party", "open", "overdue", "credit", "balance", null, null, "oldest_due"],
  },
  "finance:open-items": {
    widths: [240, 110, 130, 130, 130, 100, 80],
    sorts: ["number", "date", "gross", "settled", "open", "status"],
  },
  "finance:payments": { widths: [240, 100, 130, 130, 130, 100, 80], sorts: [null, null, "amount"] },
  "finance:journal": {
    widths: [220, 130, 130, 130, 100, 80],
    sorts: ["account", "date", null, null, "currency"],
  },
  "data-sources:records": {
    widths: [240, 80, 130, 100, 80],
    sorts: ["reference", "version", "date", null, null],
  },
  "data-sources:documents": {
    widths: [240, 150, 130, 220, 80],
    sorts: ["number", "type", "amount"],
  },
  facts: {
    widths: [220, 220, 180, 130, 220, 180, 80],
    sorts: ["predicate", "value", "subject_type", "observed_at"],
  },
};
const numericColumns: Record<string, number[]> = {
  "orders-deliveries:deliveries": [4, 5, 6],
  "orders-deliveries:customer-orders": [3, 4],
  "orders-deliveries:supplier-orders": [3, 4],
  "warehouse:stock": [1, 2, 3],
  "warehouse:reservations": [2],
  "warehouse:movements": [2],
  "finance:open-items": [2, 3, 4],
  "finance:payments": [2, 3, 4],
  "finance:journal": [2, 3],
  "data-sources:records": [1],
  "data-sources:documents": [2],
  "inspector:exceptions": [3],
};
function actionContent(value: ReactNode): ReactNode {
  const visit = (content: ReactNode): ReactNode =>
    Children.map(content, (child) => {
      if (!isValidElement(child)) return child;
      const node = child as Node;
      if (node.type === "button" || node.type === "a") {
        const meaning = node.props["data-action-meaning"];
        const preview = meaning === "preview";
        const Icon = preview
          ? node.props["aria-expanded"]
            ? ChevronDown
            : ChevronRight
          : meaning === "filter"
            ? ListFilter
            : meaning === "edit"
              ? Pencil
              : meaning === "work"
                ? Play
                : meaning === "source"
                  ? FileText
                  : ExternalLink;
        return cloneElement(
          node,
          {
            ...({
              title: node.props.title || node.props["aria-label"] || text(node.props.children),
              "aria-label": node.props["aria-label"] || text(node.props.children),
              className: `${node.props.className || ""}${preview ? " erp-preview-action" : ""}`,
            } as object),
          },
          <>
            <span className="erp-action-icon" aria-hidden="true">
              <Icon size={16} />
            </span>
            <span className="sr-only">{node.props.children}</span>
          </>,
        );
      }
      return cloneElement(node, {}, visit(node.props.children));
    });
  return visit(value);
}
export function RegisterTable({
  children,
  footer,
  actionWidth = 80,
  actionPresentation = "icons",
  cursorView,
  busy,
  empty,
}: {
  children: ReactNode;
  cursorView?: { id: string; widths: number[] };
  footer?: ReactNode;
  actionWidth?: number;
  actionPresentation?: "icons" | "labels";
  className?: string;
  /** A newer read is in flight; the rows already shown dim instead of collapsing. */
  busy?: boolean;
  /** Shown inside the table body when the read returned no rows. */
  empty?: { title?: string; hint?: string };
}) {
  const context = useTableContext();
  const id = cursorView?.id || context?.id || "register";
  const sections = nodes(children),
    head = sections.find((n) => n.type === "thead"),
    body = sections.find((n) => n.type === "tbody");
  const headers = nodes(nodes(head?.props.children)[0]?.props.children),
    rows = nodes(body?.props.children);
  const count = headers.length;
  const selectable = /^(master-data|orders-deliveries|warehouse|finance|facts)(:|$)/.test(id);
  const isPreview = (row: Node) => row.type === TablePreview || row.props["data-inline-preview"];
  const dataRows = rows.filter((row) => !isPreview(row));
  const scope = `${context?.scope}:${dataRows.map((row) => row.key).join(",")}`;
  const [selection, setSelection] = useState<{ scope: string; keys: string[] }>({
    scope: "",
    keys: [],
  });
  const selected = selection.scope === scope ? selection.keys : [];
  const rowKey = (row: Node, index: number) => String(row.key ?? index);
  const exportRows = () => {
    const columns = visible.filter((i) => i !== count - 1);
    const quote = (value: string) =>
      '"' + (/^[\s]*[=+@-]/.test(value) ? "'" + value : value).replaceAll('"', '""') + '"';
    const lines = [
      columns.map((i) => text(headers[i].props.children)),
      ...dataRows
        .filter((row, index) => selected.includes(rowKey(row, index)))
        .map((row) => {
          const cells = nodes(row.props.children);
          return columns.map((i) => text(cells[i]?.props.children));
        }),
    ];
    const url = URL.createObjectURL(
      new Blob(["\uFEFF" + lines.map((line) => line.map(quote).join(",")).join("\r\n")], {
        type: "text/csv;charset=utf-8",
      }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = `${id.replaceAll(":", "-")}-selection.csv`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  const profile = (cursorView ? { widths: cursorView.widths, sorts: [] } : profiles[id]) || {
    widths: [220, 100, 100, 100, 80],
    sorts: ["name", null, null, "status"],
  };
  const storage = layoutKey(context?.user || "anonymous", id);
  const [layout, setLayout] = useState<TableLayout>(() => validateLayout(null, count));
  const [loaded, setLoaded] = useState("");
  const container = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const scroll = container.current;
    const register = scroll?.parentElement;
    const main = scroll?.closest("main");
    const footer = register?.querySelector<HTMLElement>(".erp-register-footer");
    if (!scroll || !main || !footer || scroll.closest("dialog")) return;
    let frame = 0;
    const measure = () => {
      frame = 0;
      const bounds = main.getBoundingClientRect();
      footer.dataset.pageFooter = "";
      footer.style.left = `${bounds.left}px`;
      footer.style.width = `${bounds.width}px`;
      const available =
        window.innerHeight -
        scroll.getBoundingClientRect().top -
        footer.getBoundingClientRect().height -
        16;
      scroll.style.height = `${Math.max(160, available)}px`;
      scroll.style.maxHeight = "none";
    };
    const schedule = () => {
      if (!frame) frame = requestAnimationFrame(measure);
    };
    const observer = new ResizeObserver(schedule);
    observer.observe(main);
    observer.observe(footer);
    window.addEventListener("resize", schedule);
    window.addEventListener("scroll", schedule);
    measure();
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", schedule);
      window.removeEventListener("scroll", schedule);
      delete footer.dataset.pageFooter;
      footer.style.removeProperty("left");
      footer.style.removeProperty("width");
      scroll.style.removeProperty("height");
      scroll.style.removeProperty("max-height");
    };
  }, [id, selectable, cursorView]);

  useEffect(() => {
    let saved = null;
    try {
      saved = JSON.parse(localStorage.getItem(storage) || "null");
    } catch {}
    setLayout(validateLayout(saved, count));
    setLoaded(storage);
  }, [storage, count]);
  const update = (value: TableLayout) => {
    const next = validateLayout(value, count);
    setLayout(next);
    try {
      localStorage.setItem(storage, JSON.stringify(next));
    } catch {}
  };
  const current = loaded === storage ? layout : validateLayout(null, count);
  const visible = headers.map((_, i) => i).filter((i) => !current.hidden.includes(i));
  const widths = visible.map((i) =>
    i === count - 1 ? actionWidth : current.widths[i] || profile.widths[i] || 150,
  );
  const openRow = (row: HTMLTableRowElement) => {
    const button =
      row.querySelector<HTMLButtonElement>("td:last-child button, td:last-child a") ||
      row.querySelector<HTMLButtonElement>("button,a");
    button?.click();
  };
  const controls = (
    <div className="erp-table-tools">
      <FilterChip
        label={t("Row density")}
        select={
          <select
            aria-label={t("Row density")}
            value={current.density}
            onChange={(event) =>
              update({
                ...current,
                density: event.target.value === "compact" ? "compact" : "normal",
              })
            }
          >
            <option value="normal">{t("Normal rows")}</option>
            <option value="compact">{t("Compact rows")}</option>
          </select>
        }
      />
      <details className="erp-column-menu">
        <summary className="br-btn register-column-chip">
          <EyeOff size={14} />
          {t("Columns")}
          <ChevronDown size={14} />
        </summary>
        <div className="erp-column-options">
          {headers.map((h, i) => (
            <label key={i}>
              <input
                type="checkbox"
                checked={!current.hidden.includes(i)}
                disabled={i === 0 || i === count - 1}
                onChange={(e) =>
                  update({
                    ...current,
                    hidden: e.target.checked
                      ? current.hidden.filter((n) => n !== i)
                      : [...current.hidden, i],
                  })
                }
              />
              {h.props.children}
            </label>
          ))}
          <button className="br-btn" onClick={() => update(validateLayout(null, count))}>
            {t("Reset table")}
          </button>
        </div>
      </details>
    </div>
  );
  const toolbar = useRegisterTools();
  return (
    <div
      className="erp-register"
      data-table-id={id}
      data-density={current.density}
      data-action-presentation={actionPresentation}
      data-selectable={selectable}
    >
      {toolbar?.target ? createPortal(controls, toolbar.target) : controls}
      <div
        ref={container}
        style={{ containerType: "inline-size" }}
        className={reading(busy, "erp-table-scroll")}
        aria-busy={busy || undefined}
        role="region"
        aria-label={t("Scrollable register")}
        tabIndex={0}
      >
        <table
          className="erp-table"
          style={{ width: "100%", minWidth: widths.reduce((a, b) => a + b, selectable ? 40 : 0) }}
        >
          <colgroup>
            {selectable && <col style={{ width: 40 }} />}
            {visible.map((i, n) => (
              <Fragment key={i}>
                {i === count - 1 && <col />}
                <col style={{ width: widths[n] }} />
              </Fragment>
            ))}
          </colgroup>
          <thead>
            <tr>
              {selectable && (
                <th className="erp-select-cell">
                  <input
                    type="checkbox"
                    aria-label={t("Select current page")}
                    ref={(node) => {
                      if (node)
                        node.indeterminate = selected.length > 0 && selected.length < rows.length;
                    }}
                    checked={rows.length > 0 && selected.length === rows.length}
                    disabled={!rows.length}
                    onChange={(e) =>
                      setSelection({ scope, keys: e.target.checked ? rows.map(rowKey) : [] })
                    }
                  />
                </th>
              )}
              {visible.map((i, n) => {
                const sort = i === count - 1 ? null : profile.sorts[i],
                  active = sort && context?.query.sort === sort;
                return (
                  <Fragment key={i}>
                    {i === count - 1 && <th aria-hidden="true" className="erp-fill" />}
                    <th
                      key={i}
                      title={text(headers[i].props.children)}
                      style={{
                        textAlign:
                          i === count - 1 ||
                          numericColumns[id]?.includes(i) ||
                          headers[i].props.className?.includes("text-right") ||
                          nodes(rows[0]?.props.children)[i]?.props.className?.includes("text-right")
                            ? "right"
                            : "left",
                      }}
                      className={headers[i].props.className}
                      aria-sort={
                        active
                          ? context?.query.sort_direction === "desc"
                            ? "descending"
                            : "ascending"
                          : undefined
                      }
                    >
                      <div
                        className="erp-heading"
                        style={{
                          justifyContent:
                            i === count - 1 || numericColumns[id]?.includes(i)
                              ? "flex-end"
                              : undefined,
                        }}
                      >
                        {sort ? (
                          <button
                            title={t("Sort column")}
                            className="erp-sort"
                            onClick={() =>
                              context?.change({
                                tableSort: sort,
                                tableDirection:
                                  active && context.query.sort_direction !== "desc"
                                    ? "desc"
                                    : "asc",
                              })
                            }
                          >
                            {headers[i].props.children}
                            <span aria-hidden="true">
                              {active
                                ? context?.query.sort_direction === "desc"
                                  ? " ↓"
                                  : " ↑"
                                : " ↕"}
                            </span>
                          </button>
                        ) : (
                          <span>{headers[i].props.children}</span>
                        )}
                        {i === 0 && (
                          <button
                            className="erp-filter"
                            title={t("Filter records")}
                            aria-label={t("Filter records")}
                            onClick={() => {
                              const root =
                                container.current?.closest(".erp-register")?.parentElement;
                              let parent = root;
                              while (parent && !parent.querySelector("input:not([type=checkbox])"))
                                parent = parent.parentElement;
                              parent
                                ?.querySelector<HTMLInputElement>("input:not([type=checkbox])")
                                ?.focus();
                            }}
                          >
                            ⌕
                          </button>
                        )}
                      </div>
                      {i < count - 1 && (
                        <span
                          role="separator"
                          aria-orientation="vertical"
                          aria-label={`${t("Resize column")}: ${text(headers[i].props.children)}`}
                          aria-valuemin={70}
                          aria-valuemax={320}
                          aria-valuenow={widths[n]}
                          tabIndex={0}
                          className="erp-resize"
                          onKeyDown={(e) => {
                            if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
                              e.preventDefault();
                              update({
                                ...current,
                                widths: {
                                  ...current.widths,
                                  [i]: widths[n] + (e.key === "ArrowRight" ? 10 : -10),
                                },
                              });
                            }
                          }}
                          onPointerDown={(e) => {
                            e.preventDefault();
                            const start = e.clientX,
                              width = widths[n],
                              target = e.currentTarget;
                            target.setPointerCapture(e.pointerId);
                            const move = (event: PointerEvent) =>
                              update({
                                ...current,
                                widths: { ...current.widths, [i]: width + event.clientX - start },
                              });
                            const up = () => {
                              target.removeEventListener("pointermove", move);
                              target.removeEventListener("pointerup", up);
                              target.removeEventListener("pointercancel", up);
                            };
                            target.addEventListener("pointermove", move);
                            target.addEventListener("pointerup", up);
                            target.addEventListener("pointercancel", up);
                          }}
                        />
                      )}
                    </th>
                  </Fragment>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {!rows.length && (
              <tr className="erp-empty-row">
                <td
                  colSpan={
                    visible.length + (selectable ? 1 : 0) + (visible.includes(count - 1) ? 1 : 0) ||
                    1
                  }
                >
                  <div className="erp-empty" role="status">
                    <h2>{empty?.title || t("No matching records")}</h2>
                    <p>{empty?.hint || t("Try another filter or inspect the original records.")}</p>
                  </div>
                </td>
              </tr>
            )}
            {rows.map((row, r) => {
              if (isPreview(row))
                return cloneElement(row, {
                  key: row.key || `preview-${r}`,
                  columns:
                    visible.length + (selectable ? 1 : 0) + (visible.includes(count - 1) ? 1 : 0),
                } as object);
              const dataIndex = rows
                .slice(0, r)
                .filter((candidate) => !isPreview(candidate)).length;
              const cells = nodes(row.props.children);
              return (
                <tr
                  {...row.props}
                  key={row.key || r}
                  tabIndex={0}
                  onClick={(e) => {
                    if ((e.target as HTMLElement).closest("button,a,input,select,summary")) return;
                    if (row.props.onClick) row.props.onClick(e);
                    else openRow(e.currentTarget);
                  }}
                  onKeyDown={(e) => {
                    if (e.target === e.currentTarget && e.key === "Enter") {
                      e.preventDefault();
                      if (row.props.onClick) e.currentTarget.click();
                      else openRow(e.currentTarget);
                    }
                  }}
                >
                  {selectable && (
                    <td className="erp-select-cell">
                      <input
                        type="checkbox"
                        aria-label={`${t("Select row")}: ${text(nodes(row.props.children)[0]?.props.children)}`}
                        checked={selected.includes(rowKey(row, dataIndex))}
                        onChange={(e) =>
                          setSelection({
                            scope,
                            keys: e.target.checked
                              ? [...selected, rowKey(row, dataIndex)]
                              : selected.filter((key) => key !== rowKey(row, dataIndex)),
                          })
                        }
                      />
                    </td>
                  )}
                  {visible.map((i) => {
                    const cell = cells[i];
                    if (!cell) return <td key={i} />;
                    return (
                      <Fragment key={i}>
                        {i === count - 1 && <td aria-hidden="true" className="erp-fill" />}
                        <td
                          {...cell.props}
                          className={`${cell.props.className || ""}${i === count - 1 ? " erp-actions-cell" : ""}`}
                          style={{
                            textAlign: numericColumns[id]?.includes(i) ? "right" : undefined,
                          }}
                          title={text(cell.props.children)}
                        >
                          <div className="erp-cell" data-original-content={undefined}>
                            {i === count - 1 && actionPresentation === "icons"
                              ? actionContent(cell.props.children)
                              : cell.props.children}
                          </div>
                        </td>
                      </Fragment>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {(selectable || !cursorView || footer) && (
        <div className="erp-register-footer">
          {selectable && (
            <div className="erp-selection-tools">
              <span className="text-xs text-fg-muted">
                {selected.length} {t("Selected on this page")}
              </span>
              <button className="br-btn" disabled={!selected.length} onClick={exportRows}>
                {t("Export selection")}
              </button>
            </div>
          )}
          <div className="erp-pagination-tools ml-auto">
            {!cursorView && (
              <label className="flex items-center gap-2 text-sm">
                {t("Rows per page")}
                <select
                  aria-label={t("Rows per page")}
                  className="br-control"
                  value={context?.query.size || 50}
                  onChange={(e) =>
                    context?.change({ tableSize: Number(e.target.value) as 25 | 50 | 100 })
                  }
                >
                  {[25, 50, 100].map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </select>
              </label>
            )}
            {footer}
          </div>
        </div>
      )}
    </div>
  );
}

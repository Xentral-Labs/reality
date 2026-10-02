import { useEffect, useRef, useState } from "react";
import { api, stockCounts, type StockCountProposal } from "../api";
import { formatDateTime, formatQuantity, t } from "../localization";
import { ReadLine } from "./ReadState";
import { useRead } from "./useCompanyContext";

type CountRow = { id: string; name: string; sku: string; unit: string; physical: string };

/**
 * Spec 307: count a location and post the differences in one confirmation.
 *
 * Only the items given a counted quantity are counted. The server compares
 * each with the book at the counting time, shows where a loss comes from and
 * which reservations it leaves uncovered; nothing is posted before the person
 * confirms, and a review they walk away from is withdrawn.
 */
export function StockCountCard({
  tenant,
  location,
  rows,
  close,
  settled,
}: {
  tenant: string;
  location: { id: string; name: string };
  rows: CountRow[];
  close: () => void;
  settled: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    alive = useRef(true),
    open = useRef<string | null>(null);
  const [counted, setCounted] = useState<Record<string, string>>({}),
    [note, setNote] = useState(""),
    [proposal, setProposal] = useState<StockCountProposal | null>(null),
    [done, setDone] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const withdraw = async () => {
    const id = open.current;
    open.current = null;
    if (id) await api.rejectProposal(tenant, id, null).catch(() => undefined);
  };
  useEffect(() => {
    alive.current = true;
    const previous = document.activeElement as HTMLElement,
      node = dialog.current;
    node?.showModal();
    return () => {
      alive.current = false;
      void withdraw();
      node?.close();
      previous?.focus();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (failure) {
      if (alive.current) setError(t((failure as Error).message));
    } finally {
      if (alive.current) setBusy(false);
    }
  };
  const lines = rows
    .filter((row) => (counted[row.id] ?? "").trim() !== "")
    .map((row) => ({ item_id: row.id, counted_quantity: counted[row.id].trim() }));
  const prepare = () =>
    !busy &&
    run(async () => {
      const value = await stockCounts.prepare(tenant, {
        location_id: location.id,
        ...(note.trim() ? { note: note.trim() } : {}),
        lines,
      });
      if (!alive.current) {
        void api.rejectProposal(tenant, value.id, null).catch(() => undefined);
        return;
      }
      open.current = value.id;
      setProposal(value);
    });
  const edit = () =>
    run(async () => {
      await withdraw();
      if (alive.current) setProposal(null);
    });
  const leave = () => {
    void withdraw();
    close();
  };
  const confirm = () =>
    run(async () => {
      if (!proposal) return;
      open.current = null;
      await stockCounts.confirm(tenant, proposal.id);
      if (!alive.current) return;
      setDone(true);
      settled();
    });
  const review = proposal?.preview.stock_count;
  return (
    <dialog
      ref={dialog}
      aria-labelledby="stock-count-title"
      onCancel={(event) => {
        if (busy) event.preventDefault();
        else leave();
      }}
      className="m-auto max-h-[90vh] w-[min(720px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
      data-stock-count-card
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <h2 id="stock-count-title" className="text-xl font-semibold text-fg-strong">
          {t("Stock count")} · {location.name}
        </h2>
        <button className="br-btn" disabled={busy} onClick={leave}>
          {t("Close")}
        </button>
      </header>
      <div className="mb-5 rounded-lg bg-surface-muted p-3 text-sm text-fg-muted">
        {t(
          "Enter what you counted; items left empty are not counted. Each difference is posted against the stock at the counting time, so work at the location can carry on. A loss comes off free stock first, then blocked stock. Nothing is posted before you confirm.",
        )}
      </div>
      {!proposal && (
        <form
          className="space-y-4 text-sm"
          onSubmit={(event) => {
            event.preventDefault();
            void prepare();
          }}
        >
          <table className="w-full text-left">
            <thead className="text-fg-muted">
              <tr>
                <th className="py-1 pr-3 font-medium">{t("Item")}</th>
                <th className="py-1 pr-3 text-right font-medium">{t("In stock")}</th>
                <th className="py-1 text-right font-medium">{t("Counted")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-t border-border-default">
                  <td className="py-2 pr-3">
                    {row.name} <span className="text-fg-muted">· {row.sku}</span>
                  </td>
                  <td className="py-2 pr-3 text-right">
                    {formatQuantity(row.physical)} {row.unit}
                  </td>
                  <td className="py-2 text-right">
                    <input
                      className="br-control w-28 text-right"
                      aria-label={`${t("Counted")} · ${row.name}`}
                      inputMode="decimal"
                      value={counted[row.id] ?? ""}
                      onChange={(event) => setCounted({ ...counted, [row.id]: event.target.value })}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <label className="block">
            {t("Note")}
            <input
              className="br-control mt-2 w-full"
              aria-label={t("Note")}
              value={note}
              onChange={(event) => setNote(event.target.value)}
            />
          </label>
          <div className="flex justify-end">
            <button className="br-btn br-btn-primary" disabled={busy || !lines.length}>
              {t("Review change")}
            </button>
          </div>
        </form>
      )}
      {review && (
        <section className="space-y-4 text-sm" data-stock-count-review>
          <table className="w-full text-left">
            <thead className="text-fg-muted">
              <tr>
                <th className="py-1 pr-3 font-medium">{t("Item")}</th>
                <th className="py-1 pr-3 text-right font-medium">{t("Book")}</th>
                <th className="py-1 pr-3 text-right font-medium">{t("Counted")}</th>
                <th className="py-1 text-right font-medium">{t("Difference")}</th>
              </tr>
            </thead>
            <tbody>
              {review.lines.map((line) => (
                <tr
                  key={`${line.item_id}:${line.lot_id || ""}`}
                  className="border-t border-border-default"
                >
                  <td className="py-2 pr-3">
                    {line.item}
                    {Number(line.from_blocks) > 0 && (
                      <div className="text-xs text-fg-muted">
                        {t("Of which from blocked stock")}: {formatQuantity(line.from_blocks)}{" "}
                        {line.unit}
                      </div>
                    )}
                  </td>
                  <td className="py-2 pr-3 text-right">{formatQuantity(line.book)}</td>
                  <td className="py-2 pr-3 text-right">{formatQuantity(line.counted)}</td>
                  <td className="py-2 text-right font-medium">
                    {Number(line.difference) > 0 ? "+" : ""}
                    {formatQuantity(line.difference)} {line.unit}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!!review.uncovered.length && (
            <div className="rounded-lg border border-border-default p-3" data-stock-count-uncovered>
              <div className="font-medium text-fg-strong">
                {t("No longer covered after this count")}
              </div>
              {review.uncovered.map((entry) => (
                <div key={entry.item_id} className="mt-2">
                  <div>
                    {entry.item}: {t("reserved")} {formatQuantity(entry.reserved)},{" "}
                    {t("in stock after")} {formatQuantity(entry.physical_after)}
                  </div>
                  <ul className="mt-1 text-fg-muted">
                    {entry.reservations.map((row) => (
                      <li key={row.reservation_id}>
                        {row.customer || row.commitment_id} · {formatQuantity(row.quantity)}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
              <div className="mt-2 text-fg-muted">
                {t("Nothing is released by the count; decide who waits.")}
              </div>
            </div>
          )}
          {done ? (
            <div role="status" className="font-medium">
              {t("Done.")}
            </div>
          ) : (
            <div className="flex justify-end gap-2">
              <button className="br-btn" disabled={busy} onClick={edit}>
                {t("Edit")}
              </button>
              <button className="br-btn br-btn-primary" disabled={busy} onClick={confirm}>
                {t("Confirm")}
              </button>
            </div>
          )}
        </section>
      )}
      {error && (
        <div role="alert" className="mt-4 text-sm text-danger">
          {error}
        </div>
      )}
    </dialog>
  );
}

/** Spec 307: the counts of a location, each opening its lines and differences. */
export function StockCountList({ tenant, location }: { tenant: string; location: string }) {
  const read = useRead(() => stockCounts.list(tenant, location), [tenant, location]);
  const [opened, setOpened] = useState("");
  const detail = useRead(
    () => (opened ? stockCounts.detail(tenant, opened) : Promise.resolve(null)),
    [tenant, opened],
  );
  const rows = Array.isArray(read.data?.rows) ? read.data!.rows : [];
  if (!rows.length) return null;
  return (
    <section
      className="my-5 rounded-xl border border-border-default bg-surface p-4 text-sm"
      data-stock-count-list
    >
      <h3 className="font-semibold text-fg-strong">{t("Stock counts")}</h3>
      <ul className="mt-2 divide-y divide-border-default">
        {rows.map((row) => (
          <li key={row.id} className="py-2">
            <button
              className="text-left underline-offset-2 hover:underline"
              aria-expanded={opened === row.id}
              onClick={() => setOpened(opened === row.id ? "" : row.id)}
            >
              {formatDateTime(row.created_at)} · {row.lines} {t("lines")}
              {row.note ? ` · ${row.note}` : ""}
            </button>
            {opened === row.id &&
              (detail.data ? (
                <ul className="mt-2 space-y-1 text-fg-muted">
                  {detail.data.lines.map((line) => (
                    <li key={`${line.item_id}:${line.lot_id || ""}`}>
                      {line.item}: {t("Book")} {formatQuantity(line.book)} · {t("Counted")}{" "}
                      {formatQuantity(line.counted)} · {Number(line.difference) > 0 ? "+" : ""}
                      {formatQuantity(line.difference)} {line.unit}
                    </li>
                  ))}
                </ul>
              ) : (
                <ReadLine />
              ))}
          </li>
        ))}
      </ul>
    </section>
  );
}

import { useEffect, useRef, useState } from "react";
import { api, backorders, workspaceApi, type BackorderServingProposal } from "../api";
import { formatDate, formatQuantity, t } from "../localization";
import { ReadLine, ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";

/**
 * Spec 305: give arrived stock to the orders waiting for it.
 *
 * The server proposes the serving order (the orders the received purchase is
 * assigned to first, then by due date) and what each gets. The person may change
 * a quantity and review again; nothing is reserved before they confirm, and a
 * review they walk away from is withdrawn.
 */
export function BackorderServingCard({
  tenant,
  item,
  location,
  purchase,
  close,
  settled,
}: {
  tenant: string;
  item: { id: string; name: string; unit?: string };
  location?: string;
  purchase?: string;
  close: () => void;
  settled: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    alive = useRef(true);
  const [place, setPlace] = useState(location || ""),
    [proposal, setProposal] = useState<BackorderServingProposal | null>(null),
    [quantities, setQuantities] = useState<Record<string, string>>({}),
    [edited, setEdited] = useState(false),
    [done, setDone] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const locations = useRead(
    () =>
      location
        ? Promise.resolve(null)
        : workspaceApi.references(tenant, "location", "", 1, true, { size: 100 }),
    [tenant, location],
  );
  useEffect(() => {
    alive.current = true;
    const previous = document.activeElement as HTMLElement,
      node = dialog.current;
    node?.showModal();
    return () => {
      alive.current = false;
      node?.close();
      previous?.focus();
    };
  }, []);
  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (reason) {
      if (alive.current) setError(t((reason as Error).message));
    } finally {
      if (alive.current) setBusy(false);
    }
  };
  const withdraw = async () => {
    if (proposal && !done) await api.rejectProposal(tenant, proposal.id, null);
  };
  const prepare = (lines?: Array<{ commitment_id: string; quantity: string }>) =>
    run(async () => {
      await withdraw();
      const value = await backorders.prepare(tenant, {
        item_id: item.id,
        location_id: place,
        ...(purchase ? { supplier_commitment_id: purchase } : {}),
        ...(lines ? { lines } : {}),
      });
      if (!alive.current) return;
      setProposal(value);
      setEdited(false);
      setQuantities(
        Object.fromEntries(
          value.preview.backorder_serving.lines.map((line) => [line.commitment_id, line.quantity]),
        ),
      );
    });
  // The first review needs no input once the location is known.
  useEffect(() => {
    if (place && !proposal) void prepare();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [place]);
  const leave = () => {
    void withdraw().catch(() => undefined);
    close();
  };
  const confirm = () =>
    run(async () => {
      if (!proposal) return;
      await backorders.confirm(tenant, proposal.id);
      if (!alive.current) return;
      setDone(true);
      settled();
    });
  const review = proposal?.preview.backorder_serving;
  const unit = item.unit || review?.unit || "";
  return (
    <dialog
      ref={dialog}
      aria-labelledby="backorder-serving-title"
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else leave();
      }}
      className="m-auto max-h-[90vh] w-[min(640px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
      data-backorder-serving-card
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <h2 id="backorder-serving-title" className="text-xl font-semibold text-fg-strong">
          {t("Serve backorders")}
        </h2>
        <button className="br-btn" disabled={busy} onClick={leave}>
          {t("Close")}
        </button>
      </header>
      <div className="mb-5 rounded-lg bg-surface-muted p-3 text-sm text-fg-muted">
        {t(
          "Orders this purchase is assigned to come first, then the others by due date. Nothing is reserved before you confirm.",
        )}
      </div>
      <div className="mb-4 text-sm">
        <strong>{item.name}</strong>
        {review && <span className="text-fg-muted"> · {review.location}</span>}
      </div>
      {!location && (
        <label className="mb-4 block text-sm">
          {t("Location")}
          <select
            className="br-control mt-2 w-full"
            aria-label={t("Location")}
            disabled={busy || done}
            value={place}
            onChange={(e) => {
              setProposal(null);
              setPlace(e.target.value);
            }}
          >
            <option value="">{t("Choose a location")}</option>
            {(locations.data?.items || [])
              .filter((row) => row.allows_stock !== false)
              .map((row) => (
                <option key={row.id} value={row.id}>
                  {String(row.name)}
                </option>
              ))}
          </select>
          {locations.loading && <ReadLine />}
        </label>
      )}
      {place && !review && !error && <ReadState loading rows={3} />}
      {review && (
        <section className="space-y-4 text-sm" data-backorder-serving-review>
          <div className="text-fg-muted">
            {t("Available here")}: {formatQuantity(review.available)} {unit}
          </div>
          <table className="w-full text-left">
            <thead className="text-fg-muted">
              <tr>
                <th className="py-1 pr-3 font-medium">{t("Customer")}</th>
                <th className="py-1 pr-3 font-medium">{t("Due")}</th>
                <th className="py-1 pr-3 text-right font-medium">{t("Still needed")}</th>
                <th className="py-1 text-right font-medium">{t("Reserve")}</th>
              </tr>
            </thead>
            <tbody>
              {review.lines.map((line) => (
                <tr key={line.commitment_id} className="border-t border-border-default">
                  <td className="py-2 pr-3">
                    {line.customer || line.commitment_id}
                    {line.why === "assigned" && (
                      <span className="ml-2 text-xs text-fg-muted">
                        {t("Assigned to this purchase")}
                      </span>
                    )}
                  </td>
                  <td className="py-2 pr-3">{line.due_at ? formatDate(line.due_at) : "—"}</td>
                  <td className="py-2 pr-3 text-right">
                    {formatQuantity(line.need)} {unit}
                  </td>
                  <td className="py-2 text-right">
                    <input
                      className="br-control w-24 text-right"
                      aria-label={`${t("Reserve")} · ${line.customer || line.commitment_id}`}
                      inputMode="decimal"
                      disabled={busy || done}
                      value={quantities[line.commitment_id] ?? ""}
                      onChange={(e) => {
                        setQuantities({ ...quantities, [line.commitment_id]: e.target.value });
                        setEdited(true);
                      }}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!!review.held.length && (
            <div className="text-fg-muted">
              {t("On hold, not served")}:{" "}
              {review.held
                .map(
                  (line) =>
                    `${line.customer || line.commitment_id} (${formatQuantity(line.need)} ${unit})`,
                )
                .join(", ")}
            </div>
          )}
          {!edited && (
            <div>
              {t("Reserved after confirming")}: {formatQuantity(review.reserving)} {unit} ·{" "}
              {t("Available after confirming")}: {formatQuantity(review.free_after)} {unit}
            </div>
          )}
          {done ? (
            <div role="status" className="font-medium">
              {t("Done.")}
            </div>
          ) : edited ? (
            <div className="flex justify-end">
              <button
                className="br-btn br-btn-primary"
                disabled={busy}
                onClick={() =>
                  void prepare(
                    review.lines.map((line) => ({
                      commitment_id: line.commitment_id,
                      quantity: quantities[line.commitment_id] || "0",
                    })),
                  )
                }
              >
                {t("Review change")}
              </button>
            </div>
          ) : (
            <div className="flex justify-end">
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

/** Spec 305: from when, and how much, the item can be promised. */
export function AvailableToPromise({ tenant, item }: { tenant: string; item: string }) {
  const read = useRead(() => backorders.promise(tenant, item), [tenant, item]);
  const answer = read.data;
  if (!answer) return read.loading ? <ReadLine /> : null;
  const unit = answer.unit;
  const short = Number(answer.now.free) < 0;
  return (
    <div className="mb-3 text-sm" data-available-to-promise>
      <div className="font-medium text-fg-strong">{t("Available to promise")}</div>
      <div className="mt-1">
        {short
          ? `${t("Short now")}: ${formatQuantity(answer.now.free.replace("-", ""))} ${unit}`
          : `${t("Now")}: ${formatQuantity(answer.now.free)} ${unit}`}
      </div>
      {answer.purchases.map((row) => (
        <div key={row.commitment_id} className="text-fg-muted">
          {row.due_at ? `${t("From")} ${formatDate(row.due_at)}` : t("Without a date")}: +
          {formatQuantity(row.adds)} {unit} ({row.supplier || row.commitment_id}) · {t("Total")}{" "}
          {formatQuantity(row.total)} {unit}
          {row.overdue && ` · ${t("overdue")}`}
        </div>
      ))}
    </div>
  );
}

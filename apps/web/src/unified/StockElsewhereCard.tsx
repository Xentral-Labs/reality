import { useEffect, useRef, useState } from "react";
import { api, deliveryActions, type AttentionRow, type DeliveryProposal } from "../api";
import { formatQuantity, t } from "../localization";

type Place = { location_id: string; name: string; available: string; proposed: string };

/**
 * Spec 303: serve an order line from the warehouse that has its stock.
 *
 * The finding names where stock lies; the person picks a warehouse, a way and a
 * quantity, and the server reviews it as any delivery action: reserving the
 * rest there, so that warehouse ships it, or transferring the stock to the
 * order's warehouse. Nothing changes before the review is confirmed.
 */
export function StockElsewhereCard({
  tenant,
  finding,
  close,
  settled,
}: {
  tenant: string;
  finding: AttentionRow;
  close: () => void;
  settled: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    alive = useRef(true),
    request = useRef(crypto.randomUUID());
  const places = ((finding.trace as unknown as { locations?: Place[] }).locations || []) as Place[];
  const [place, setPlace] = useState(places[0]?.location_id || ""),
    [quantity, setQuantity] = useState(places[0]?.proposed || ""),
    [proposal, setProposal] = useState<DeliveryProposal | null>(null),
    [done, setDone] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const chosen = places.find((row) => row.location_id === place);
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
  const prepare = (way: "reserve" | "transfer") =>
    run(async () => {
      request.current = crypto.randomUUID();
      const trace = finding.trace;
      const value =
        way === "reserve"
          ? await deliveryActions.prepare(tenant, request.current, "reserve", {
              commitment_id: trace.commitment_id,
              location_id: place,
              quantity,
            })
          : await deliveryActions.prepare(tenant, request.current, "movement_create", {
              movement_type: "transfer",
              item_id: trace.item_id,
              quantity,
              from_location_id: place,
              to_location_id: trace.location_id,
            });
      if (alive.current) setProposal(value);
    });
  // A review the person walks away from is withdrawn, so no decision waits.
  const withdraw = async () => {
    if (proposal && !done) await api.rejectProposal(tenant, proposal.id, null);
  };
  const edit = () =>
    run(async () => {
      await withdraw();
      if (alive.current) setProposal(null);
    });
  const leave = () => {
    void withdraw().catch(() => undefined);
    close();
  };
  const confirm = () =>
    run(async () => {
      if (!proposal?.review) return;
      await deliveryActions.confirm(tenant, proposal.id, proposal.review.token);
      if (!alive.current) return;
      setDone(true);
      settled();
    });
  const effect = proposal?.review?.effect as Record<string, string> | undefined;
  return (
    <dialog
      ref={dialog}
      aria-labelledby="stock-elsewhere-title"
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else leave();
      }}
      className="m-auto max-h-[90vh] w-[min(560px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
      data-stock-elsewhere-card
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <h2 id="stock-elsewhere-title" className="text-xl font-semibold text-fg-strong">
          {t("Serve from another warehouse")}
        </h2>
        <button className="br-btn" disabled={busy} onClick={leave}>
          {t("Close")}
        </button>
      </header>
      <div className="mb-5 rounded-lg bg-surface-muted p-3 text-sm text-fg-muted">
        {t(
          "Reserve the rest where the stock is, and that warehouse ships it as its own package, or transfer the stock to the order's warehouse first. Nothing changes before you confirm.",
        )}
      </div>
      {!proposal && (
        <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
          <label className="block text-sm">
            {t("Warehouse")}
            <select
              className="br-control mt-2 w-full"
              aria-label={t("Warehouse")}
              value={place}
              onChange={(e) => {
                setPlace(e.target.value);
                setQuantity(
                  places.find((row) => row.location_id === e.target.value)?.proposed || "",
                );
              }}
            >
              {places.map((row) => (
                <option key={row.location_id} value={row.location_id}>
                  {row.name} · {formatQuantity(row.available)} {t("available")}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            {t("Quantity")}
            <input
              className="br-control mt-2 w-full"
              aria-label={t("Quantity")}
              inputMode="decimal"
              required
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
            />
          </label>
          <div className="flex flex-wrap justify-end gap-2">
            <button
              type="button"
              className="br-btn"
              disabled={busy || !chosen || !quantity}
              onClick={() => void prepare("transfer")}
            >
              {t("Prepare transfer")}
            </button>
            <button
              type="button"
              className="br-btn br-btn-primary"
              disabled={busy || !chosen || !quantity}
              onClick={() => void prepare("reserve")}
            >
              {t("Reserve there")}
            </button>
          </div>
        </form>
      )}
      {proposal?.review && (
        <section className="space-y-3 text-sm" data-stock-elsewhere-review>
          <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-2">
            <dt className="text-fg-muted">{t("Warehouse")}</dt>
            <dd>{chosen?.name}</dd>
            {Object.entries(effect || {})
              .filter(([key]) => ["applied", "shortage", "transferred"].includes(key))
              .map(([key, value]) => (
                <div key={key} className="contents">
                  <dt className="text-fg-muted">
                    {t(
                      key === "applied"
                        ? "Reserved after confirming"
                        : key === "shortage"
                          ? "Still missing"
                          : "Transferred after confirming",
                    )}
                  </dt>
                  <dd>{formatQuantity(value)}</dd>
                </div>
              ))}
          </dl>
          {(proposal.review.warnings || []).map((warning) => (
            <div
              key={warning.code}
              role="note"
              className="rounded-lg border border-border-default bg-surface-muted p-3"
            >
              {t(warning.message)}
            </div>
          ))}
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

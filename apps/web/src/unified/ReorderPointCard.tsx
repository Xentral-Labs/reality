import { useEffect, useRef, useState } from "react";
import {
  reorderPoints,
  workspaceApi,
  type ReorderPoint,
  type ReorderPointProposal,
  type ReorderPointValues,
} from "../api";
import { formatQuantity, t } from "../localization";
import { ReadLine, ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";

/**
 * Spec 302: state, change or remove the reorder point of an item at a location.
 *
 * The server reviews the change and shows the values it found beside the new
 * ones; nothing is stated until the person confirms that review, and a point
 * changed by someone else in between is refused rather than overwritten.
 */
export function ReorderPointCard({
  tenant,
  item,
  existing,
  removing = false,
  close,
  settled,
}: {
  tenant: string;
  item: { id: string; name: string; unit?: string };
  existing?: ReorderPoint;
  removing?: boolean;
  close: () => void;
  settled: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    alive = useRef(true);
  const [location, setLocation] = useState(existing?.location_id || ""),
    [point, setPoint] = useState(existing?.reorder_point || ""),
    [quantity, setQuantity] = useState(existing?.reorder_quantity || ""),
    [proposal, setProposal] = useState<ReorderPointProposal | null>(null),
    [done, setDone] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const locations = useRead(
    () =>
      existing
        ? Promise.resolve(null)
        : workspaceApi.references(tenant, "location", "", 1, true, { size: 100 }),
    [tenant, existing?.id],
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
  const prepare = () =>
    run(async () => {
      const value = await reorderPoints.prepare(tenant, {
        operation: removing ? "remove" : "set",
        item_id: item.id,
        location_id: location,
        ...(removing ? {} : { reorder_point: point, reorder_quantity: quantity }),
      });
      if (alive.current) setProposal(value);
    });
  const confirm = () =>
    run(async () => {
      if (!proposal) return;
      await reorderPoints.confirm(tenant, proposal.id);
      if (!alive.current) return;
      setDone(true);
      settled();
    });
  const review = proposal?.preview.reorder_point;
  const unit = review?.unit || item.unit || "";
  const values = (row: ReorderPointValues | null) =>
    row
      ? `${formatQuantity(row.reorder_point)} ${unit} · ${t("Reorder quantity")} ${formatQuantity(row.reorder_quantity)} ${unit}`
      : t("None");
  const title = removing
    ? "Remove reorder point"
    : existing
      ? "Change reorder point"
      : "Set reorder point";
  return (
    <dialog
      ref={dialog}
      aria-labelledby="reorder-point-title"
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else close();
      }}
      className="m-auto max-h-[90vh] w-[min(560px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
      data-reorder-point-card
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <h2 id="reorder-point-title" className="text-xl font-semibold text-fg-strong">
          {t(title)}
        </h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </header>
      <div className="mb-5 rounded-lg bg-surface-muted p-3 text-sm text-fg-muted">
        {t(
          "When available plus incoming stock at the location falls to the reorder point, Exceptions proposes the reorder quantity. Nothing is ordered without your confirmation.",
        )}
      </div>
      {!proposal && (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            void prepare();
          }}
        >
          <div className="text-sm">
            <strong>{item.name}</strong>
          </div>
          {existing ? (
            <div className="text-sm">
              {t("Location")}: {existing.location}
            </div>
          ) : (
            <label className="block text-sm">
              {t("Location")}
              <select
                className="br-control mt-2 w-full"
                aria-label={t("Location")}
                required
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              >
                <option value="">{t("Choose a location")}</option>
                {(locations.data?.items || []).map((row) => (
                  <option key={row.id} value={row.id}>
                    {String(row.name)}
                  </option>
                ))}
              </select>
              {locations.loading && <ReadLine />}
            </label>
          )}
          {!removing && (
            <div className="grid gap-4 sm:grid-cols-2">
              {(
                [
                  ["Reorder point", point, setPoint],
                  ["Reorder quantity", quantity, setQuantity],
                ] as const
              ).map(([label, value, change]) => (
                <label key={label} className="block text-sm">
                  {t(label)}
                  {unit ? ` (${unit})` : ""}
                  <input
                    className="br-control mt-2 w-full"
                    aria-label={t(label)}
                    inputMode="decimal"
                    required
                    value={value}
                    onChange={(e) => change(e.target.value)}
                  />
                </label>
              ))}
            </div>
          )}
          <div className="flex justify-end">
            <button className="br-btn br-btn-primary" disabled={busy || !location}>
              {t("Review change")}
            </button>
          </div>
        </form>
      )}
      {review && (
        <section className="space-y-3 text-sm" data-reorder-point-review>
          <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-2">
            <dt className="text-fg-muted">{t("Location")}</dt>
            <dd>{review.location}</dd>
            <dt className="text-fg-muted">{t("Now")}</dt>
            <dd>{values(review.current)}</dd>
            <dt className="text-fg-muted">{t("After confirming")}</dt>
            <dd>{review.proposed ? values(review.proposed) : t("No reorder point")}</dd>
          </dl>
          {done ? (
            <div role="status" className="font-medium">
              {t(removing ? "Reorder point removed." : "Reorder point saved.")}
            </div>
          ) : (
            <div className="flex justify-end gap-2">
              <button className="br-btn" disabled={busy} onClick={() => setProposal(null)}>
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

/** The reorder points of one item, on its master-data record. */
export function ReorderPoints({
  tenant,
  item,
}: {
  tenant: string;
  item: { id: string; name: string; unit?: string };
}) {
  const read = useRead(() => reorderPoints.list(tenant, item.id), [tenant, item.id]);
  const [editing, setEditing] = useState<{ existing?: ReorderPoint; removing?: boolean } | null>(
    null,
  );
  const rows = read.data?.rows || [];
  return (
    <section className="mt-4 text-sm" data-reorder-points>
      <div className="flex items-center justify-between gap-2">
        <h4 className="font-semibold">{t("Reorder points")}</h4>
        <button className="br-btn" onClick={() => setEditing({})}>
          {t("Set reorder point")}
        </button>
      </div>
      {!read.data && <ReadState loading={read.loading} error={read.error} retry={read.refresh} />}
      {read.data && !rows.length && (
        <div className="mt-2 text-fg-muted">{t("No reorder point is stated for this item.")}</div>
      )}
      {rows.length > 0 && (
        <ul className="mt-2 divide-y divide-border-default rounded-lg border border-border-default">
          {rows.map((row) => (
            <li key={row.id} className="flex flex-wrap items-center justify-between gap-2 p-3">
              <span>
                <strong>{row.location}</strong> · {t("Reorder point")}{" "}
                {formatQuantity(row.reorder_point)} {row.unit} · {t("Reorder quantity")}{" "}
                {formatQuantity(row.reorder_quantity)} {row.unit}
              </span>
              <span className="flex gap-2">
                <button className="br-btn" onClick={() => setEditing({ existing: row })}>
                  {t("Change")}
                </button>
                <button
                  className="br-btn"
                  onClick={() => setEditing({ existing: row, removing: true })}
                >
                  {t("Remove")}
                </button>
              </span>
            </li>
          ))}
        </ul>
      )}
      {editing && (
        <ReorderPointCard
          tenant={tenant}
          item={item}
          existing={editing.existing}
          removing={editing.removing}
          close={() => setEditing(null)}
          settled={read.refresh}
        />
      )}
    </section>
  );
}

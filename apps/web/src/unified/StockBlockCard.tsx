import { useEffect, useRef, useState } from "react";
import {
  api,
  stockBlocks,
  workspaceApi,
  type StockBlock,
  type StockBlockProposal,
  type StockBlockReason,
} from "../api";
import { formatQuantity, t } from "../localization";
import { ReadLine } from "./ReadState";
import { useRead } from "./useCompanyContext";

const reasons: [StockBlockReason, string][] = [
  ["quality", "Quality"],
  ["damage", "Damage"],
  ["expiry", "Expiry"],
  ["inspection", "Inspection"],
];
export const blockReasonLabel = (code: string) =>
  t(reasons.find(([value]) => value === code)?.[1] || code);

/**
 * Spec 304: block stock where it lies, or release or scrap a block.
 *
 * The server reviews each change and shows what stays available; nothing is
 * held back, released or written off before the person confirms, and a review
 * the person walks away from is withdrawn.
 */
export function StockBlockCard({
  tenant,
  mode,
  item,
  block,
  prefill,
  close,
  settled,
}: {
  tenant: string;
  mode: "block" | "release" | "scrap";
  item?: { id: string; name: string; unit?: string };
  block?: StockBlock;
  prefill?: { location_id?: string; lot_id?: string; quantity?: string; reason?: StockBlockReason };
  close: () => void;
  settled: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    alive = useRef(true);
  const [location, setLocation] = useState(prefill?.location_id || ""),
    [lot, setLot] = useState(prefill?.lot_id || ""),
    [quantity, setQuantity] = useState(
      prefill?.quantity || (mode === "block" ? "" : block?.open_quantity || ""),
    ),
    [reason, setReason] = useState<StockBlockReason>(prefill?.reason || "quality"),
    [note, setNote] = useState(""),
    [why, setWhy] = useState(""),
    [proposal, setProposal] = useState<StockBlockProposal | null>(null),
    [done, setDone] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const locations = useRead(
    () =>
      mode === "block" && !proposal
        ? workspaceApi.references(tenant, "location", "", 1, true, { size: 100 })
        : Promise.resolve(null),
    [tenant, mode, proposal?.id],
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
      const body: Record<string, string> =
        mode === "block"
          ? {
              operation: "block",
              item_id: item!.id,
              location_id: location,
              quantity,
              reason_code: reason,
              ...(note ? { note } : {}),
              ...(lot ? { lot_id: lot } : {}),
            }
          : { operation: mode, block_id: block!.id, quantity, reason: why };
      const value = await stockBlocks.prepare(tenant, body);
      if (alive.current) setProposal(value);
    });
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
      if (!proposal) return;
      await stockBlocks.confirm(tenant, proposal.id);
      if (!alive.current) return;
      setDone(true);
      settled();
    });
  const review = proposal?.preview.stock_block;
  const unit = item?.unit || block?.unit || review?.unit || "";
  const title =
    mode === "block"
      ? "Block stock"
      : mode === "release"
        ? "Release blocked stock"
        : "Scrap blocked stock";
  return (
    <dialog
      ref={dialog}
      aria-labelledby="stock-block-title"
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else leave();
      }}
      className="m-auto max-h-[90vh] w-[min(560px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
      data-stock-block-card
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <h2 id="stock-block-title" className="text-xl font-semibold text-fg-strong">
          {t(title)}
        </h2>
        <button className="br-btn" disabled={busy} onClick={leave}>
          {t("Close")}
        </button>
      </header>
      <div className="mb-5 rounded-lg bg-surface-muted p-3 text-sm text-fg-muted">
        {t(
          mode === "scrap"
            ? "Scrapping writes the goods off their location with one adjustment. Nothing changes before you confirm."
            : "Blocked stock stays where it lies and cannot be reserved, shipped or moved until it is released or scrapped. Nothing changes before you confirm.",
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
            <strong>{item?.name || block?.item}</strong>
            {block && (
              <span className="text-fg-muted">
                {" "}
                · {block.location} · {blockedQuantity(block)} {unit} ·{" "}
                {blockReasonLabel(block.reason_code)}
              </span>
            )}
          </div>
          {mode === "block" && (
            <>
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
              <label className="block text-sm">
                {t("Reason")}
                <select
                  className="br-control mt-2 w-full"
                  aria-label={t("Reason")}
                  value={reason}
                  onChange={(e) => setReason(e.target.value as StockBlockReason)}
                >
                  {reasons.map(([value, label]) => (
                    <option key={value} value={value}>
                      {t(label)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm">
                {t("Lot ID (if the item is lot-tracked)")}
                <input
                  className="br-control mt-2 w-full"
                  aria-label={t("Lot ID (if the item is lot-tracked)")}
                  value={lot}
                  onChange={(e) => setLot(e.target.value)}
                />
              </label>
              <label className="block text-sm">
                {t("Note")}
                <input
                  className="br-control mt-2 w-full"
                  aria-label={t("Note")}
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                />
              </label>
            </>
          )}
          <label className="block text-sm">
            {t("Quantity")}
            {unit ? ` (${unit})` : ""}
            <input
              className="br-control mt-2 w-full"
              aria-label={t("Quantity")}
              inputMode="decimal"
              required
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
            />
          </label>
          {mode !== "block" && (
            <label className="block text-sm">
              {t("Why")}
              <input
                className="br-control mt-2 w-full"
                aria-label={t("Why")}
                required
                value={why}
                onChange={(e) => setWhy(e.target.value)}
              />
            </label>
          )}
          <div className="flex justify-end">
            <button
              className="br-btn br-btn-primary"
              disabled={busy || (mode === "block" && !location)}
            >
              {t("Review change")}
            </button>
          </div>
        </form>
      )}
      {review && (
        <section className="space-y-3 text-sm" data-stock-block-review>
          <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-2">
            {mode === "block" ? (
              <>
                <dt className="text-fg-muted">{t("Location")}</dt>
                <dd>{review.location}</dd>
                <dt className="text-fg-muted">{t("Available now")}</dt>
                <dd>
                  {formatQuantity(review.free_before || "0")} {unit}
                </dd>
                <dt className="text-fg-muted">{t("Blocked after confirming")}</dt>
                <dd>
                  {formatQuantity(review.quantity || "0")} {unit} ·{" "}
                  {blockReasonLabel(review.reason_code || "")}
                </dd>
                <dt className="text-fg-muted">{t("Available after confirming")}</dt>
                <dd>
                  {formatQuantity(review.free_after || "0")} {unit}
                </dd>
              </>
            ) : (
              <>
                <dt className="text-fg-muted">{t("Location")}</dt>
                <dd>{review.location}</dd>
                <dt className="text-fg-muted">
                  {t(
                    mode === "release" ? "Released after confirming" : "Scrapped after confirming",
                  )}
                </dt>
                <dd>
                  {formatQuantity(review.resolving || "0")} {unit}
                </dd>
                <dt className="text-fg-muted">{t("Why")}</dt>
                <dd>{review.reason}</dd>
              </>
            )}
          </dl>
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

/** What a block still holds back, and what it was stated with once partly resolved. */
function blockedQuantity(block: StockBlock) {
  if (block.open_quantity === block.quantity) return formatQuantity(block.quantity);
  return t("{open} of {stated} still blocked")
    .replace("{open}", formatQuantity(block.open_quantity))
    .replace("{stated}", formatQuantity(block.quantity));
}

/** The active blocks of the company, or of one item, with release and scrap. */
export function StockBlockList({ tenant, item = "" }: { tenant: string; item?: string }) {
  const read = useRead(() => stockBlocks.list(tenant, item), [tenant, item]);
  const [acting, setActing] = useState<{ mode: "release" | "scrap"; block: StockBlock } | null>(
    null,
  );
  const rows = read.data?.rows || [];
  // A secondary list: the table's Blocked column already carries the numbers,
  // so it shows only once it has blocks to list.
  if (!rows.length) return null;
  return (
    <section
      className="my-5 rounded-xl border border-border-default bg-surface p-4 text-sm"
      data-stock-block-list
    >
      <h3 className="font-semibold text-fg-strong">{t("Blocked stock")}</h3>
      <ul className="mt-2 divide-y divide-border-default">
        {rows.map((row) => (
          <li key={row.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
            <span>
              <strong>{row.item}</strong> · {row.location} · {blockedQuantity(row)} {row.unit} ·{" "}
              {blockReasonLabel(row.reason_code)}
              {row.note ? ` · ${row.note}` : ""}
            </span>
            <span className="flex gap-2">
              <button className="br-btn" onClick={() => setActing({ mode: "release", block: row })}>
                {t("Release")}
              </button>
              <button className="br-btn" onClick={() => setActing({ mode: "scrap", block: row })}>
                {t("Scrap")}
              </button>
            </span>
          </li>
        ))}
      </ul>
      {acting && (
        <StockBlockCard
          tenant={tenant}
          mode={acting.mode}
          block={acting.block}
          close={() => setActing(null)}
          settled={() => {
            read.refresh();
            window.dispatchEvent(new Event("reality:delivery-settled"));
          }}
        />
      )}
    </section>
  );
}

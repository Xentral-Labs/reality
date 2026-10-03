import { useEffect, useRef, useState } from "react";
import { api, kits, workspaceApi, type KitReview, type ReferenceRow } from "../api";
import { formatQuantity, t } from "../localization";
import { ReadLine, ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";

// Spec 333: a kit's components, what each location can build, and the two
// reviewed actions behind it: stating the components once, and assembling
// whole kits from them. The server reviews both; nothing changes until the
// person confirms, and a part that runs short in between refuses the whole.

type Row = { query: string; itemId: string; quantity: string; share: string };
const blank = (): Row => ({ query: "", itemId: "", quantity: "1", share: "" });

function ComponentRow({
  tenant,
  row,
  change,
  remove,
}: {
  tenant: string;
  row: Row;
  change: (row: Row) => void;
  remove?: () => void;
}) {
  const [items, setItems] = useState<ReferenceRow[]>([]);
  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(() => {
      workspaceApi
        .references(tenant, "item", row.query, 1, false)
        .then((page) => active && setItems(page.items))
        .catch(() => undefined);
    }, 200);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [tenant, row.query]);
  return (
    <div className="grid gap-2 sm:grid-cols-[1fr_1fr_6rem_6rem_auto]" data-kit-component-row>
      <input
        className="br-control"
        aria-label={t("Search items")}
        placeholder={t("Search items")}
        value={row.query}
        onChange={(event) => change({ ...row, query: event.target.value })}
      />
      <select
        className="br-control"
        aria-label={t("Component")}
        required
        value={row.itemId}
        onChange={(event) => change({ ...row, itemId: event.target.value })}
      >
        <option value="">{t("Choose an item")}</option>
        {items.map((item) => (
          <option key={item.id} value={item.id}>
            {item.sku ? `${item.sku} · ` : ""}
            {item.name}
          </option>
        ))}
      </select>
      <input
        className="br-control"
        aria-label={t("Quantity per kit")}
        inputMode="decimal"
        required
        value={row.quantity}
        onChange={(event) => change({ ...row, quantity: event.target.value })}
      />
      <input
        className="br-control"
        aria-label={t("Price share")}
        placeholder={t("Share")}
        inputMode="decimal"
        value={row.share}
        onChange={(event) => change({ ...row, share: event.target.value })}
      />
      {remove ? (
        <button type="button" className="br-btn" onClick={remove}>
          {t("Remove")}
        </button>
      ) : (
        <span />
      )}
    </div>
  );
}

/** The kit an item is, or the kits it is part of, on its master-data record. */
export function KitSection({
  tenant,
  item,
}: {
  tenant: string;
  item: { id: string; name: string };
}) {
  const [version, setVersion] = useState(0);
  const read = useRead(() => kits.list(tenant, item.id), [tenant, item.id, version]);
  const [rows, setRows] = useState<Row[]>([blank()]),
    [defining, setDefining] = useState(false),
    [location, setLocation] = useState(""),
    [quantity, setQuantity] = useState("1"),
    [pending, setPending] = useState<{ id: string; review: KitReview } | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const open = useRef<string | null>(null);
  useEffect(
    () => () => {
      if (open.current) void api.rejectProposal(tenant, open.current, null).catch(() => undefined);
    },
    [tenant],
  );
  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (failure) {
      setError(t((failure as Error).message));
    } finally {
      setBusy(false);
    }
  };
  const prepare = (body: Parameters<typeof kits.prepare>[1]) =>
    run(async () => {
      const proposal = await kits.prepare(tenant, body);
      open.current = proposal.id;
      setPending({ id: proposal.id, review: proposal.preview.kit });
    });
  const confirm = () =>
    run(async () => {
      if (!pending) return;
      await kits.confirm(tenant, pending.id);
      open.current = null;
      setPending(null);
      setDefining(false);
      setRows([blank()]);
      setVersion((value) => value + 1);
    });
  const discard = () => {
    if (open.current) void api.rejectProposal(tenant, open.current, null).catch(() => undefined);
    open.current = null;
    setPending(null);
  };

  const all = read.data?.rows || [];
  const own = all.find((kit) => kit.kit_item_id === item.id);
  const partOf = all.filter((kit) => kit.kit_item_id !== item.id);
  return (
    <section className="mt-4 text-sm" data-kit-section>
      <div className="flex items-center justify-between gap-2">
        <h4 className="font-semibold">{t("Kit")}</h4>
        {read.data && !own && !partOf.length && !defining && !pending && (
          <button className="br-btn" onClick={() => setDefining(true)}>
            {t("Define kit")}
          </button>
        )}
      </div>
      {!read.data && <ReadState loading={read.loading} error={read.error} retry={read.refresh} />}
      {read.data && !own && !partOf.length && !defining && (
        <div className="mt-2 text-fg-muted">{t("This item is not a kit.")}</div>
      )}
      {partOf.length > 0 && (
        <div className="mt-2 text-fg-muted">
          {t("Part of")}: {partOf.map((kit) => `${kit.sku} · ${kit.name}`).join(", ")}
        </div>
      )}
      {own && (
        <div className="mt-2 space-y-3">
          <ul className="divide-y divide-border-default rounded-lg border border-border-default">
            {own.components.map((part) => (
              <li key={part.item_id} className="flex flex-wrap justify-between gap-2 p-2">
                <span>
                  {part.sku} · {part.name}
                </span>
                <span className="text-fg-muted">
                  {formatQuantity(part.quantity)} {part.unit} {t("per kit")}
                  {part.share !== null && ` · ${t("Share")} ${formatQuantity(part.share)}`}
                </span>
              </li>
            ))}
          </ul>
          {own.availability.length === 0 ? (
            <div className="text-fg-muted">{t("No component is in stock yet.")}</div>
          ) : (
            <ul className="space-y-1" data-kit-availability>
              {own.availability.map((place) => (
                <li key={place.location_id}>
                  <strong>{place.location}</strong> · {t("Available")}{" "}
                  {formatQuantity(place.available)} ({t("on hand")}{" "}
                  {formatQuantity(place.kits_on_hand)}, {t("can be built")}{" "}
                  {formatQuantity(place.buildable)})
                  {place.limited_by.length > 0 &&
                    ` · ${t("Limited by")} ${place.limited_by.join(", ")}`}
                </li>
              ))}
            </ul>
          )}
          {!pending && (
            <form
              className="flex flex-wrap items-end gap-2"
              onSubmit={(event) => {
                event.preventDefault();
                prepare({
                  operation: "assemble",
                  kit_item_id: item.id,
                  location_id: location,
                  quantity,
                });
              }}
            >
              <label className="block">
                {t("Location")}
                <select
                  className="br-control mt-1"
                  aria-label={t("Location")}
                  required
                  value={location}
                  onChange={(event) => setLocation(event.target.value)}
                >
                  <option value="">{t("Choose a location")}</option>
                  {own.availability.map((place) => (
                    <option key={place.location_id} value={place.location_id}>
                      {place.location}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                {t("Kits")}
                <input
                  className="br-control mt-1 w-24 max-w-24"
                  aria-label={t("Kits")}
                  inputMode="numeric"
                  required
                  value={quantity}
                  onChange={(event) => setQuantity(event.target.value)}
                />
              </label>
              <button className="br-btn" disabled={busy || !location}>
                {t("Review assembly")}
              </button>
            </form>
          )}
        </div>
      )}
      {defining && !pending && (
        <form
          className="mt-2 space-y-2"
          onSubmit={(event) => {
            event.preventDefault();
            prepare({
              operation: "define",
              kit_item_id: item.id,
              components: rows.map((row) => ({
                item_id: row.itemId,
                quantity: row.quantity,
                ...(row.share ? { share: row.share } : {}),
              })),
            });
          }}
        >
          <div className="text-fg-muted">
            {t(
              "Name each component and how many one kit takes. Shares of the price are optional; state them for every component, adding up to 1.",
            )}
          </div>
          {rows.map((row, index) => (
            <ComponentRow
              key={index}
              tenant={tenant}
              row={row}
              change={(next) => setRows(rows.map((old, at) => (at === index ? next : old)))}
              remove={
                rows.length > 1 ? () => setRows(rows.filter((_, at) => at !== index)) : undefined
              }
            />
          ))}
          <div className="flex gap-2">
            <button type="button" className="br-btn" onClick={() => setRows([...rows, blank()])}>
              {t("Add component")}
            </button>
            <button className="br-btn br-btn-primary" disabled={busy}>
              {t("Review change")}
            </button>
            <button type="button" className="br-btn" onClick={() => setDefining(false)}>
              {t("Cancel")}
            </button>
          </div>
        </form>
      )}
      {pending && (
        <div className="mt-3 space-y-2 rounded-lg bg-surface-muted p-3" data-kit-review>
          {pending.review.operation === "define" ? (
            <>
              <div className="font-medium">
                {t("Components of")} {pending.review.sku} · {pending.review.name}
              </div>
              <ul>
                {pending.review.components.map((part) => (
                  <li key={part.item_id}>
                    {part.sku} · {formatQuantity(part.quantity)} {part.unit} {t("per kit")}
                    {part.share !== null && ` · ${t("Share")} ${formatQuantity(part.share)}`}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <>
              <div className="font-medium">
                {t("Assemble")} {formatQuantity(pending.review.quantity)} × {pending.review.sku} ·{" "}
                {pending.review.location}
              </div>
              <ul>
                {pending.review.consumes.map((part) => (
                  <li key={part.item_id}>
                    {part.sku} · {t("Takes")} {formatQuantity(part.quantity)} {part.unit} (
                    {t("Free stock")} {formatQuantity(part.free)})
                  </li>
                ))}
              </ul>
            </>
          )}
          <div className="flex gap-2">
            <button className="br-btn br-btn-primary" disabled={busy} onClick={confirm}>
              {t("Confirm")}
            </button>
            <button className="br-btn" disabled={busy} onClick={discard}>
              {t("Discard")}
            </button>
          </div>
        </div>
      )}
      {busy && <ReadLine />}
      {error && (
        <div role="alert" className="mt-2 text-danger">
          {error}
        </div>
      )}
    </section>
  );
}

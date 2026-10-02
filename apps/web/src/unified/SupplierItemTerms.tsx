import { useEffect, useRef, useState } from "react";
import { api, supplierItemTerms, workspaceApi, type ReferenceRow } from "../api";
import { formatQuantity, t } from "../localization";
import { ReadLine } from "./ReadState";
import { useRead } from "./useCompanyContext";

// Spec 310 (G06): a supplier's minimum order quantity and order multiple per item.
// Stating and withdrawing them are the shared reviewed tools; this section only
// prepares and confirms.

type Terms = { minimum_quantity: string | null; order_multiple: string | null } | null;
type Pending = { id: string; item: string; current: Terms; proposed: Terms };

const describe = (terms: Terms) =>
  terms
    ? [
        terms.minimum_quantity && `${t("Minimum")} ${formatQuantity(terms.minimum_quantity)}`,
        terms.order_multiple && `${t("Multiple of")} ${formatQuantity(terms.order_multiple)}`,
      ]
        .filter(Boolean)
        .join(" · ")
    : t("nothing stated");

export function SupplierItemTerms({ tenant, party }: { tenant: string; party: string }) {
  const [version, setVersion] = useState(0);
  const read = useRead(
    () => supplierItemTerms.list(tenant, { party_id: party }),
    [tenant, party, version],
  );
  const [minimum, setMinimum] = useState(""),
    [multiple, setMultiple] = useState(""),
    [query, setQuery] = useState(""),
    [items, setItems] = useState<ReferenceRow[]>([]),
    [itemId, setItemId] = useState(""),
    [pending, setPending] = useState<Pending | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const open = useRef<string | null>(null);

  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(() => {
      workspaceApi
        .references(tenant, "item", query, 1, false)
        .then((page) => active && setItems(page.items))
        .catch(() => undefined);
    }, 200);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [tenant, query]);

  // A review nobody confirmed is withdrawn when the section goes away.
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
  const prepare = (body: Parameters<typeof supplierItemTerms.prepare>[1], item: string) =>
    run(async () => {
      const proposal = await supplierItemTerms.prepare(tenant, body);
      const review = (proposal.preview.supplier_item_terms || {}) as {
        current?: Terms;
        proposed?: Terms;
      };
      open.current = proposal.id;
      setPending({
        id: proposal.id,
        item,
        current: review.current ?? null,
        proposed: review.proposed ?? null,
      });
    });
  const confirm = () =>
    run(async () => {
      if (!pending) return;
      await supplierItemTerms.confirm(tenant, pending.id);
      open.current = null;
      setPending(null);
      setMinimum("");
      setMultiple("");
      setItemId("");
      setVersion((value) => value + 1);
    });
  const discard = () => {
    if (open.current) void api.rejectProposal(tenant, open.current, null).catch(() => undefined);
    open.current = null;
    setPending(null);
  };

  const rows = read.data?.rows || [];
  const chosen = items.find((item) => item.id === itemId);
  return (
    <section className="mt-4 text-sm" data-supplier-item-terms>
      <div className="font-medium text-fg-strong">{t("Minimum quantities and pack sizes")}</div>
      {read.loading && !read.data ? (
        <ReadLine />
      ) : rows.length === 0 ? (
        <div className="mt-1 text-fg-muted">{t("No supplier terms stated.")}</div>
      ) : (
        <ul className="mt-1 space-y-1">
          {rows.map((row) => (
            <li key={row.id} className="flex flex-wrap items-center gap-2">
              <span className="font-medium">
                {row.sku ? `${row.sku} · ` : ""}
                {row.item}
              </span>
              <span className="text-fg-muted">
                {describe(row)} {row.unit}
              </span>
              <button
                className="br-btn"
                disabled={busy || !!pending}
                onClick={() =>
                  prepare({ operation: "remove", party_id: party, item_id: row.item_id }, row.item)
                }
              >
                {t("Remove")}
              </button>
            </li>
          ))}
        </ul>
      )}
      {pending ? (
        <div className="mt-3 space-y-2 rounded-lg bg-surface-muted p-3" data-supplier-terms-review>
          <div className="font-medium">{pending.item}</div>
          <div>
            {t("Now")}: {describe(pending.current)}
          </div>
          <div>
            {t("After confirming")}: {describe(pending.proposed)}
          </div>
          <div className="flex gap-2">
            <button className="br-btn br-btn-primary" disabled={busy} onClick={confirm}>
              {t("Confirm")}
            </button>
            <button className="br-btn" disabled={busy} onClick={discard}>
              {t("Discard")}
            </button>
          </div>
        </div>
      ) : (
        <form
          className="mt-3 grid gap-2 sm:grid-cols-2"
          onSubmit={(event) => {
            event.preventDefault();
            prepare(
              {
                operation: "set",
                party_id: party,
                item_id: itemId,
                ...(minimum ? { minimum_quantity: minimum } : {}),
                ...(multiple ? { order_multiple: multiple } : {}),
              },
              chosen?.name || itemId,
            );
          }}
        >
          <label className="block">
            {t("Search items")}
            <input
              className="br-control mt-1 w-full"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <label className="block">
            {t("Item")}
            <select
              className="br-control mt-1 w-full"
              required
              value={itemId}
              onChange={(event) => setItemId(event.target.value)}
            >
              <option value="">{t("Choose an item")}</option>
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.sku ? `${item.sku} · ` : ""}
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            {t("Minimum order quantity")}
            <input
              className="br-control mt-1 w-full"
              inputMode="decimal"
              value={minimum}
              onChange={(event) => setMinimum(event.target.value)}
            />
          </label>
          <label className="block">
            {t("Order multiple")}
            <input
              className="br-control mt-1 w-full"
              inputMode="decimal"
              value={multiple}
              onChange={(event) => setMultiple(event.target.value)}
            />
          </label>
          <button
            className="br-btn self-start"
            disabled={busy || !itemId || (!minimum && !multiple)}
          >
            {t("Review change")}
          </button>
        </form>
      )}
      {error && (
        <div role="alert" className="mt-2 text-danger">
          {error}
        </div>
      )}
    </section>
  );
}

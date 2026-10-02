import { useEffect, useRef, useState } from "react";
import { api, customerItemNumbers, workspaceApi, type ReferenceRow } from "../api";
import { t } from "../localization";
import { ReadLine } from "./ReadState";
import { useRead } from "./useCompanyContext";

// Spec 308 (M02): the customer's own article numbers for our items. Stating and
// withdrawing one are the shared reviewed tools; this section only prepares and confirms.

type Mapping = { item?: string; item_id?: string; customer_item_name?: string } | null;
type Pending = {
  id: string;
  number: string;
  current: Mapping;
  proposed: Mapping;
};

const describe = (mapping: Mapping) =>
  mapping
    ? `${mapping.item || mapping.item_id}${mapping.customer_item_name ? ` · ${mapping.customer_item_name}` : ""}`
    : t("nothing stated");

export function CustomerItemNumbers({ tenant, party }: { tenant: string; party: string }) {
  const [version, setVersion] = useState(0);
  const read = useRead(
    () => customerItemNumbers.list(tenant, { party_id: party }),
    [tenant, party, version],
  );
  const [number, setNumber] = useState(""),
    [name, setName] = useState(""),
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
  const prepare = (body: Parameters<typeof customerItemNumbers.prepare>[1]) =>
    run(async () => {
      const proposal = await customerItemNumbers.prepare(tenant, body);
      const preview = (proposal.preview.customer_item_number || {}) as {
        current?: Mapping;
        proposed?: Mapping;
      };
      open.current = proposal.id;
      setPending({
        id: proposal.id,
        number: body.customer_item_number,
        current: preview.current ?? null,
        proposed: preview.proposed ?? null,
      });
    });
  const confirm = () =>
    run(async () => {
      if (!pending) return;
      await customerItemNumbers.confirm(tenant, pending.id);
      open.current = null;
      setPending(null);
      setNumber("");
      setName("");
      setItemId("");
      setVersion((value) => value + 1);
    });
  const discard = () => {
    if (open.current) void api.rejectProposal(tenant, open.current, null).catch(() => undefined);
    open.current = null;
    setPending(null);
  };

  const rows = read.data?.rows || [];
  return (
    <section className="mt-4 text-sm" data-customer-item-numbers>
      <div className="font-medium text-fg-strong">{t("Customer item numbers")}</div>
      {read.loading && !read.data ? (
        <ReadLine />
      ) : rows.length === 0 ? (
        <div className="mt-1 text-fg-muted">{t("No customer item numbers stated.")}</div>
      ) : (
        <ul className="mt-1 space-y-1">
          {rows.map((row) => (
            <li key={row.id} className="flex flex-wrap items-center gap-2">
              <span className="font-medium">{row.customer_item_number}</span>
              <span className="text-fg-muted">
                {row.customer_item_name ? `${row.customer_item_name} · ` : ""}
                {row.sku ? `${row.sku} · ` : ""}
                {row.item}
              </span>
              <button
                className="br-btn"
                disabled={busy || !!pending}
                onClick={() =>
                  prepare({
                    operation: "remove",
                    party_id: party,
                    customer_item_number: row.customer_item_number,
                  })
                }
              >
                {t("Remove")}
              </button>
            </li>
          ))}
        </ul>
      )}
      {pending ? (
        <div className="mt-3 space-y-2 rounded-lg bg-surface-muted p-3" data-customer-item-review>
          <div>
            {t("Customer item no.")} <span className="font-medium">{pending.number}</span>
          </div>
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
            prepare({
              operation: "set",
              party_id: party,
              customer_item_number: number,
              item_id: itemId,
              customer_item_name: name,
            });
          }}
        >
          <label className="block">
            {t("Customer item no.")}
            <input
              className="br-control mt-1 w-full"
              required
              value={number}
              onChange={(event) => setNumber(event.target.value)}
            />
          </label>
          <label className="block">
            {t("Customer's name for it")}
            <input
              className="br-control mt-1 w-full"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </label>
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
          <button className="br-btn self-start" disabled={busy || !number.trim() || !itemId}>
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

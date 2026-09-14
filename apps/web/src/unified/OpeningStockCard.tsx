import { useEffect, useRef, useState } from "react";
import { APIError, api, deliveryActions, openingActions, type OpeningProposal } from "../api";
import { formatDateTime, formatQuantity, t } from "../localization";
import { ReadLine } from "./ReadState";
import { useRead } from "./useCompanyContext";
import { Inspector } from "./Inspector";

function StockReference({
  tenant,
  kind,
  label,
  value,
  change,
}: {
  tenant: string;
  kind: string;
  label: string;
  value: string;
  change: (id: string) => void;
}) {
  const [query, setQuery] = useState("");
  const read = useRead(() => api.suggestions(tenant, kind, query), [tenant, kind, query]);
  return (
    <div className="space-y-2">
      <label className="block text-sm">
        {t(label)}
        <input
          className="br-control mt-2 w-full"
          aria-label={`${t("Search")} ${t(label)}`}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select
          className="br-control mt-2 w-full"
          aria-label={t(label)}
          required
          value={value}
          onChange={(e) => change(e.target.value)}
        >
          <option value="">{t("Select a record")}</option>
          {value && !read.data?.items.some((row) => row.value === value) && (
            <option value={value}>{value}</option>
          )}
          {read.data?.items.map((row) => (
            <option key={row.value} value={row.value}>
              {row.label} · {row.description}
            </option>
          ))}
        </select>
      </label>
      {read.loading && <ReadLine />}
      {read.error && (
        <p role="alert">
          {read.error}{" "}
          <button type="button" className="br-btn" onClick={read.refresh}>
            {t("Retry")}
          </button>
        </p>
      )}
      {read.data && !read.data.items.length && (
        <p className="text-sm text-fg-muted">{t("No matching records")}</p>
      )}
      {(read.data?.items.length || 0) >= 20 && (
        <p className="text-sm text-fg-muted">{t("Refine your search to find more records.")}</p>
      )}
    </div>
  );
}

type Attempt = { request: string; args: Record<string, unknown> };
export function OpeningStockCard({
  tenant,
  proposalId = "",
  close,
  prepared,
  settled,
}: {
  tenant: string;
  proposalId?: string;
  close: () => void;
  prepared?: (id: string) => void;
  settled: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    alive = useRef(true);
  const storage = `reality:opening-stock:${tenant}`;
  const [attempt, setAttempt] = useState<Attempt | null>(() => {
    try {
      const value = JSON.parse(sessionStorage.getItem(storage) || "null");
      return value?.request && value?.args ? value : null;
    } catch {
      return null;
    }
  });
  const [item, setItem] = useState(""),
    [location, setLocation] = useState(""),
    [quantity, setQuantity] = useState(""),
    [occurred, setOccurred] = useState(""),
    [proposal, setProposal] = useState<OpeningProposal | null>(null),
    [busy, setBusy] = useState(false),
    [uncertain, setUncertain] = useState(false),
    [error, setError] = useState(""),
    [inspection, inspect] = useState<{ kind: string; id: string } | null>(null);
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
  useEffect(() => {
    let active = true;
    if (proposalId) {
      setBusy(true);
      openingActions
        .detail(tenant, proposalId)
        .then((value) => {
          if (active) {
            setProposal(value);
            setUncertain(value.status === "executing");
          }
        })
        .catch((reason) => {
          if (active) setError(reason.message);
        })
        .finally(() => {
          if (active) setBusy(false);
        });
    }
    return () => {
      active = false;
    };
  }, [tenant, proposalId]);
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
  const accept = (value: OpeningProposal) => {
    if (!alive.current) return;
    setProposal(value);
    setUncertain(value.status === "executing");
    if (value.status === "executed") settled();
  };
  const prepare = () =>
    run(async () => {
      const intent = attempt || {
        request: crypto.randomUUID(),
        args: {
          movement_type: "opening_stock",
          item_id: item,
          to_location_id: location,
          quantity,
          ...(occurred ? { occurred_at: new Date(occurred).toISOString() } : {}),
        },
      };
      // Save before transport, so a lost response can recover this exact request.
      sessionStorage.setItem(storage, JSON.stringify(intent));
      setAttempt(intent);
      try {
        const value = await openingActions.prepare(tenant, intent.request, intent.args);
        if (!alive.current) return;
        sessionStorage.removeItem(storage);
        setAttempt(null);
        accept(value);
        prepared?.(value.id);
      } catch (reason) {
        if (
          alive.current &&
          reason instanceof APIError &&
          reason.status >= 400 &&
          reason.status < 500
        ) {
          sessionStorage.removeItem(storage);
          setAttempt(null);
        }
        throw reason;
      }
    });
  const check = () =>
    run(async () => accept(await openingActions.detail(tenant, proposal?.id || proposalId)));
  const confirm = () =>
    run(async () => {
      if (!proposal?.review) return;
      setUncertain(true);
      try {
        await deliveryActions.confirm(tenant, proposal.id, proposal.review.token);
      } catch (reason) {
        if (
          alive.current &&
          reason instanceof APIError &&
          reason.status >= 400 &&
          reason.status < 500
        )
          setUncertain(false);
        throw reason;
      }
      if (alive.current) accept(await openingActions.detail(tenant, proposal.id));
    });
  const reject = () =>
    run(async () => {
      if (!proposal) return;
      setUncertain(true);
      await api.rejectProposal(tenant, proposal.id, null);
      if (alive.current) accept(await openingActions.detail(tenant, proposal.id));
    });
  const review = proposal?.review;
  const intent = review?.intent || proposal?.intent;
  return (
    <dialog
      ref={dialog}
      aria-labelledby="opening-title"
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else close();
      }}
      className="m-auto max-h-[90vh] w-[min(680px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <h2 id="opening-title" className="text-xl font-semibold text-fg-strong">
          {t("Record opening stock")}
        </h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </header>
      <p className="mb-5 rounded-lg bg-surface-muted p-3 text-sm text-fg-muted">
        {t("Opening stock adds to the recorded stock. It does not set a target balance.")}
      </p>
      {!proposal && !proposalId && !attempt && (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            void prepare();
          }}
        >
          <fieldset disabled={busy} className="space-y-4">
            <StockReference
              tenant={tenant}
              kind="items"
              label="Item"
              value={item}
              change={setItem}
            />
            <StockReference
              tenant={tenant}
              kind="locations"
              label="Location"
              value={location}
              change={setLocation}
            />
            <label className="block text-sm">
              {t("Quantity to add")}
              <input
                className="br-control mt-2 w-full"
                inputMode="decimal"
                required
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
              />
            </label>
            <label className="block text-sm">
              {t("Occurrence time (optional)")}
              <input
                className="br-control mt-2 w-full"
                type="datetime-local"
                value={occurred}
                onChange={(e) => setOccurred(e.target.value)}
              />
            </label>
            <p className="text-sm text-fg-muted">
              {t("Time uses this device’s timezone. Leave blank to use the booking time.")}
            </p>
            <p className="text-sm text-fg-muted">
              {t("For stocked items without lot or serial tracking.")}
            </p>
            <button className="br-btn br-btn-primary" type="submit">
              {t("Review change")}
            </button>
          </fieldset>
        </form>
      )}
      {!proposal && !proposalId && attempt && (
        <div className="space-y-4">
          <p role="status">
            {t("Preparation outcome is unknown. Recover the same request before starting another.")}
          </p>
          <button className="br-btn" disabled={busy} onClick={prepare}>
            {t("Recover review")}
          </button>
        </div>
      )}
      {!proposal && proposalId && (
        <button className="br-btn" disabled={busy} onClick={check}>
          {t("Check status")}
        </button>
      )}
      {proposal && (
        <div className="space-y-5">
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
            <dt>{t("Item")}</dt>
            <dd className="min-w-0 break-words">
              {[review?.state.item.sku, review?.state.item.name].filter(Boolean).join(" · ") ||
                String(intent?.item_id || "—")}
            </dd>
            <dt>{t("Location")}</dt>
            <dd className="min-w-0 break-words">
              {review?.state.location.name || String(intent?.to_location_id || "—")}
            </dd>
            <dt>{t("Quantity to add")}</dt>
            <dd>
              {formatQuantity(String(intent?.quantity || "0"))} {review?.state.item.unit}
            </dd>
            <dt>{t("Occurrence time")}</dt>
            <dd>
              {intent?.occurred_at
                ? formatDateTime(String(intent.occurred_at))
                : t("At confirmation")}
            </dd>
          </dl>
          {review && (
            <section className="rounded-xl border border-border-default p-4">
              <h3 className="mb-3 font-semibold">{t("Reviewed stock effect")}</h3>
              <div className="flex flex-wrap items-center gap-3 text-xl tabular-nums">
                <span>{formatQuantity(review.state.physical)}</span>
                <span>+</span>
                <span>{formatQuantity(review.effect.added)}</span>
                <span>=</span>
                <strong>
                  {formatQuantity(review.effect.physical_after)} {review.state.item.unit}
                </strong>
              </div>
              <p className="mt-3 text-sm text-fg-muted">
                {t("Reserved stock stays unchanged")}: {formatQuantity(review.state.reserved)}{" "}
                {review.state.item.unit}
              </p>
            </section>
          )}
          {proposal.status === "proposed" && !uncertain && (
            <div className="flex flex-wrap gap-3">
              {review ? (
                <button className="br-btn br-btn-primary" disabled={busy} onClick={confirm}>
                  {t("Confirm opening stock")}
                </button>
              ) : (
                <button
                  className="br-btn br-btn-primary"
                  disabled={busy}
                  onClick={() =>
                    run(async () => accept(await openingActions.review(tenant, proposal.id)))
                  }
                >
                  {t("Review change")}
                </button>
              )}
              <button className="br-btn" disabled={busy} onClick={reject}>
                {t("Discard proposal")}
              </button>
            </div>
          )}
          {(uncertain ||
            proposal.status === "executing" ||
            (proposal.status === "executed" && proposal.verification !== "verified")) && (
            <div className="space-y-3">
              <p role="status">{t("The outcome needs checking. Do not record the stock again.")}</p>
              <button className="br-btn" disabled={busy} onClick={check}>
                {t("Check status")}
              </button>
            </div>
          )}
          {proposal.status === "executing" && proposal.verification === "recorded_unsettled" && (
            <button
              className="br-btn"
              disabled={busy}
              onClick={() =>
                run(async () => accept(await openingActions.reconcile(tenant, proposal.id)))
              }
            >
              {t("Recover recorded result")}
            </button>
          )}
          {proposal.status === "rejected" && (
            <p role="status">{t("Proposal discarded. No stock was recorded.")}</p>
          )}
          {proposal.status === "executed" && proposal.verification === "verified" && (
            <section className="space-y-3">
              <p role="status" className="font-semibold">
                {t("Opening stock recorded")}
              </p>
              {proposal.observation && (
                <p className="text-sm">
                  {t("Current physical stock")}: {formatQuantity(proposal.observation.physical)}{" "}
                  {review?.state.item.unit}
                </p>
              )}
              <p className="text-sm text-fg-muted">
                {t("This is a manual declaration. Its movement and event provide the audit trail.")}
              </p>
              <div className="flex flex-wrap gap-3">
                {proposal.links.map((link) => (
                  <button key={link.id} className="br-btn" onClick={() => inspect(link)}>
                    {t(link.kind === "movement" ? "Inspect movement" : "Inspect event")}
                  </button>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
      {busy && (
        <p className="mt-4">
          <ReadLine />
        </p>
      )}
      {error && (
        <p role="alert" className="mt-4 text-critical-text">
          {error}
        </p>
      )}
      {inspection && <Inspector tenant={tenant} target={inspection} close={() => inspect(null)} />}
    </dialog>
  );
}

import { useEffect, useRef, useState } from "react";
import {
  APIError,
  api,
  customerHoldActions,
  deliveryActions,
  workspaceApi,
  type CustomerHoldProposal,
  type CustomerHoldTool,
  type CustomerHold,
} from "../api";
import { formatDateTime, t } from "../localization";
import { ReadLine } from "./ReadState";
import { holdReason } from "./holdLabels";
import { useRead } from "./useCompanyContext";
import { Inspector } from "./Inspector";

function HoldList({ holds }: { holds: CustomerHold[] }) {
  return (
    <div className="space-y-3">
      {holds.map((hold) => (
        <div key={hold.id} className="rounded-lg border border-border-default p-3 text-sm">
          <strong>{holdReason(hold.reason_code)}</strong>
          {hold.note && (
            <p data-original-content className="mt-2 whitespace-pre-wrap break-words">
              {hold.note}
            </p>
          )}
          <p className="mt-2 text-xs text-fg-muted">{formatDateTime(hold.created_at)}</p>
          <details className="mt-2 text-xs text-fg-muted">
            <summary>{t("Technical details")}</summary>
            <p className="mt-2 break-all">
              {hold.id} · {hold.reason_code}
            </p>
          </details>
        </div>
      ))}
    </div>
  );
}
type Attempt = { request: string; tool: CustomerHoldTool; args: Record<string, unknown> };
export function CustomerHoldCard({
  tenant,
  party = "",
  tool,
  proposalId = "",
  close,
  prepared,
  settled,
}: {
  tenant: string;
  party?: string;
  tool?: CustomerHoldTool;
  proposalId?: string;
  close: () => void;
  prepared?: (id: string) => void;
  settled: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    alive = useRef(true);
  const storage = `reality:customer-hold:${tenant}`;
  const [attempt, setAttempt] = useState<Attempt | null>(() => {
    try {
      const value = JSON.parse(sessionStorage.getItem(storage) || "null");
      return value?.request && value?.tool && value?.args ? value : null;
    } catch {
      return null;
    }
  });
  const [customer, setCustomer] = useState(party),
    [mode, setMode] = useState<CustomerHoldTool | undefined>(tool),
    [query, setQuery] = useState(""),
    [page, setPage] = useState(1),
    [reason, setReason] = useState(""),
    [note, setNote] = useState(""),
    [proposal, setProposal] = useState<CustomerHoldProposal | null>(null),
    [busy, setBusy] = useState(false),
    [uncertain, setUncertain] = useState(false),
    [error, setError] = useState(""),
    [inspection, inspect] = useState<{ kind: string; id: string } | null>(null);
  const choices = useRead(
    () =>
      !party && !proposal && !proposalId && !attempt
        ? workspaceApi.references(tenant, "customer", query, page, true, { size: 25 })
        : Promise.resolve(null),
    [tenant, party, query, page, proposal?.id, proposalId, attempt],
  );
  const context = useRead(
    () =>
      customer && !proposal && !proposalId && !attempt
        ? customerHoldActions.context(tenant, customer)
        : Promise.resolve(null),
    [tenant, customer, proposal?.id, proposalId, attempt],
  );
  const selectedTool =
    mode || (context.data?.holds.length ? "party_delivery_hold_release" : "party_delivery_hold");
  const placing = (proposal?.tool || selectedTool) === "party_delivery_hold";
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
      customerHoldActions
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
  const accept = (value: CustomerHoldProposal) => {
    if (!alive.current) return;
    setProposal(value);
    setUncertain(value.status === "executing");
    if (value.status === "executed") settled();
  };
  const prepare = () =>
    run(async () => {
      const intent = attempt || {
        request: crypto.randomUUID(),
        tool: selectedTool,
        args: { party_id: customer, ...(placing ? { reason_code: reason, note } : {}) },
      };
      sessionStorage.setItem(storage, JSON.stringify(intent));
      setAttempt(intent);
      try {
        const value = await customerHoldActions.prepare(
          tenant,
          intent.request,
          intent.tool,
          intent.args,
        );
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
    run(async () => accept(await customerHoldActions.detail(tenant, proposal?.id || proposalId)));
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
      if (alive.current) accept(await customerHoldActions.detail(tenant, proposal.id));
    });
  const reject = () =>
    run(async () => {
      if (!proposal) return;
      setUncertain(true);
      await api.rejectProposal(tenant, proposal.id, null);
      if (alive.current) accept(await customerHoldActions.detail(tenant, proposal.id));
    });
  const review = proposal?.review;
  const valid =
    context.data && (placing ? !context.data.holds.length && reason : !!context.data.holds.length);
  return (
    <dialog
      ref={dialog}
      aria-labelledby="customer-hold-title"
      onCancel={(e) => {
        if (busy) e.preventDefault();
        else close();
      }}
      className="m-auto max-h-[90vh] w-[min(680px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <h2 id="customer-hold-title" className="text-xl font-semibold text-fg-strong">
          {t(placing ? "Place customer delivery hold" : "Release customer delivery hold")}
        </h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </header>
      <section className="mb-5 space-y-2 rounded-lg bg-surface-muted p-3 text-sm text-fg-muted">
        <p>
          {t(
            placing
              ? "Pause shipments for this customer’s current and future deliveries."
              : "Release this customer’s shipment hold. Individual delivery holds still apply.",
          )}
        </p>
        <p>
          {t(
            "Existing reservations stay unchanged; new reservations remain allowed. Stock and money stay unchanged.",
          )}
        </p>
      </section>
      {!proposal && !proposalId && !attempt && (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            void prepare();
          }}
        >
          <fieldset className="space-y-4" disabled={busy}>
            {!party && (
              <div className="space-y-2">
                <label className="block text-sm">
                  {t("Customer")}
                  <input
                    className="br-control mt-2 w-full"
                    placeholder={t("Search")}
                    aria-label={t("Search customers")}
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      setPage(1);
                    }}
                  />
                  <select
                    className="br-control mt-2 w-full"
                    aria-label={t("Customer")}
                    required
                    value={customer}
                    onChange={(e) => {
                      setCustomer(e.target.value);
                      setReason("");
                      setNote("");
                    }}
                  >
                    <option value="">{t("Select a record")}</option>
                    {customer && !choices.data?.items.some((row) => row.id === customer) && (
                      <option value={customer}>{context.data?.party.name || customer}</option>
                    )}
                    {choices.data?.items.map((row) => (
                      <option key={row.id} value={row.id}>
                        {row.name} · {row.id}
                      </option>
                    ))}
                  </select>
                </label>
                {choices.loading && <ReadLine />}
                {choices.error && (
                  <p role="alert">
                    {choices.error}{" "}
                    <button type="button" className="br-btn" onClick={choices.refresh}>
                      {t("Retry")}
                    </button>
                  </p>
                )}
                {choices.data && !choices.data.items.length && (
                  <p className="text-sm text-fg-muted">{t("No matching records")}</p>
                )}
                {choices.data && choices.data.page.pages > 1 && (
                  <div className="flex items-center justify-between gap-3">
                    <button
                      className="br-btn"
                      type="button"
                      disabled={!choices.data.page.has_previous}
                      onClick={() => setPage(page - 1)}
                    >
                      {t("Previous")}
                    </button>
                    <span className="text-sm">
                      {choices.data.page.number} / {choices.data.page.pages}
                    </span>
                    <button
                      className="br-btn"
                      type="button"
                      disabled={!choices.data.page.has_next}
                      onClick={() => setPage(page + 1)}
                    >
                      {t("Next")}
                    </button>
                  </div>
                )}
              </div>
            )}
            {customer && context.loading && <ReadLine />}
            {context.error && (
              <p role="alert">
                {context.error}{" "}
                <button className="br-btn" type="button" onClick={context.refresh}>
                  {t("Retry")}
                </button>
              </p>
            )}
            {context.data && (
              <>
                <p className="font-semibold" data-original-content>
                  {context.data.party.name}
                </p>
                {!!context.data.holds.length && <HoldList holds={context.data.holds} />}
                {placing && context.data.holds.length > 0 && (
                  <div className="space-y-3">
                    <p>{t("This customer already has a delivery hold.")}</p>
                    <button
                      type="button"
                      className="br-btn"
                      onClick={() => setMode("party_delivery_hold_release")}
                    >
                      {t("Release customer delivery hold")}
                    </button>
                  </div>
                )}
                {!placing && !context.data.holds.length && (
                  <div className="space-y-3">
                    <p>{t("This customer has no active delivery hold.")}</p>
                    <button
                      type="button"
                      className="br-btn"
                      onClick={() => setMode("party_delivery_hold")}
                    >
                      {t("Place customer delivery hold")}
                    </button>
                  </div>
                )}
                {placing && !context.data.holds.length && (
                  <>
                    <label className="block text-sm">
                      {t("Hold reason")}
                      <select
                        className="br-control mt-2 w-full"
                        required
                        aria-label={t("Hold reason")}
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                      >
                        <option value="">{t("Select hold reason")}</option>
                        {context.data.reasons.map((code) => (
                          <option key={code} value={code}>
                            {holdReason(code)}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="block text-sm">
                      {t("Hold note (optional)")}
                      <textarea
                        className="br-control mt-2 w-full"
                        rows={3}
                        value={note}
                        onChange={(e) => setNote(e.target.value)}
                      />
                    </label>
                  </>
                )}
              </>
            )}
            <button className="br-btn br-btn-primary" disabled={!valid} type="submit">
              {t("Review change")}
            </button>
          </fieldset>
        </form>
      )}
      {!proposal && !proposalId && attempt && (
        <div className="space-y-3">
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
          <div>
            <p className="text-xs uppercase text-fg-muted">{t("Customer-wide hold")}</p>
            <h3 className="mt-2 text-xl font-semibold" data-original-content>
              {review?.state.party.name || String(proposal.intent.party_id)}
            </h3>
            <p className="mt-1 break-all text-xs text-fg-muted">
              {String(proposal.intent.party_id)}
            </p>
          </div>
          {review &&
            (placing ? (
              <div className="rounded-lg border border-border-default p-4">
                <strong>{holdReason(String(review.intent.reason_code))}</strong>
                {!!review.intent.note && (
                  <p data-original-content className="mt-3 whitespace-pre-wrap break-words">
                    {String(review.intent.note)}
                  </p>
                )}
              </div>
            ) : (
              <HoldList holds={review.state.holds} />
            ))}
          {proposal.status === "proposed" && !uncertain && (
            <div className="flex flex-wrap gap-3">
              {review ? (
                <button className="br-btn br-btn-primary" disabled={busy} onClick={confirm}>
                  {t(placing ? "Confirm customer hold" : "Confirm customer hold release")}
                </button>
              ) : (
                <button
                  className="br-btn br-btn-primary"
                  disabled={busy}
                  onClick={() =>
                    run(async () => accept(await customerHoldActions.review(tenant, proposal.id)))
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
              <p role="status">{t("The hold action needs checking. Do not repeat it.")}</p>
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
                run(async () => accept(await customerHoldActions.reconcile(tenant, proposal.id)))
              }
            >
              {t("Recover recorded result")}
            </button>
          )}
          {proposal.status === "rejected" && (
            <p role="status">{t("Proposal discarded. The hold was not changed.")}</p>
          )}
          {proposal.status === "executed" && proposal.verification === "verified" && (
            <section className="space-y-3">
              <p role="status" className="font-semibold">
                {t(placing ? "Customer hold recorded" : "Customer hold released")}
              </p>
              <div className="flex flex-wrap gap-3">
                {proposal.links.map((link) => (
                  <button key={link.id} className="br-btn" onClick={() => inspect(link)}>
                    {t(link.kind === "party" ? "Inspect customer" : "Inspect event")}
                  </button>
                ))}
              </div>
              <h3 className="font-semibold">{t("Current customer holds")}</h3>
              <p className="text-sm text-fg-muted">
                {t(
                  "The recorded result remains in history. Current holds may have changed since then.",
                )}
              </p>
              {proposal.observation ? (
                proposal.observation.holds.length ? (
                  <HoldList holds={proposal.observation.holds} />
                ) : (
                  <p>{t("This customer has no active delivery hold.")}</p>
                )
              ) : (
                <p>{t("Current observation unavailable")}</p>
              )}
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

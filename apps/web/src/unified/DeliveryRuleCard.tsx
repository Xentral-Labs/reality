import { useEffect, useRef, useState } from "react";
import {
  api,
  deliveryActions,
  deliveryRules,
  type DeliveryRule,
  type DeliveryRuleProposal,
} from "../api";
import { formatDateTime, formatQuantity, t } from "../localization";
import { ReadLine } from "./ReadState";
import { useRead } from "./useCompanyContext";

const rules: [DeliveryRule, string][] = [
  ["partial_allowed", "Partial delivery allowed"],
  ["ship_complete", "Ship complete"],
  ["no_backorders", "No backorders"],
];
export const deliveryRuleLabel = (code: string) =>
  t(rules.find(([value]) => value === code)?.[1] || code);
const sourceLabel = (source: string) =>
  t(
    source === "order"
      ? "stated for this order"
      : source === "customer"
        ? "stated for the customer"
        : "default",
  );

function useModal(busy: boolean, leave: () => void) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement,
      node = dialog.current;
    node?.showModal();
    return () => {
      node?.close();
      previous?.focus();
    };
  }, []);
  return {
    ref: dialog,
    onCancel: (event: React.SyntheticEvent) => {
      if (busy) event.preventDefault();
      else leave();
    },
  };
}

/**
 * Spec 306: state how a customer or one order is delivered.
 *
 * The server reviews the statement, shows the rule now and the open orders it
 * governs; nothing changes before the person confirms, and a review they walk
 * away from is withdrawn.
 */
export function DeliveryRuleCard({
  tenant,
  party,
  document: order,
  name,
  prefill,
  close,
  settled,
}: {
  tenant: string;
  party?: string;
  document?: string;
  name: string;
  prefill?: { rule?: DeliveryRule; reason?: string };
  close: () => void;
  settled: () => void;
}) {
  const alive = useRef(true),
    open = useRef<string | null>(null);
  const [rule, setRule] = useState<DeliveryRule>(prefill?.rule || "ship_complete"),
    [reason, setReason] = useState(prefill?.reason || ""),
    [proposal, setProposal] = useState<DeliveryRuleProposal | null>(null),
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
    return () => {
      alive.current = false;
      void withdraw();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const leave = () => {
    void withdraw();
    close();
  };
  const modal = useModal(busy, leave);
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
  const prepare = () =>
    !busy &&
    run(async () => {
      const value = await deliveryRules.prepare(tenant, {
        ...(party ? { party_id: party } : { document_id: order }),
        rule,
        reason,
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
  const confirm = () =>
    run(async () => {
      if (!proposal) return;
      open.current = null;
      await deliveryRules.confirm(tenant, proposal.id);
      if (!alive.current) return;
      setDone(true);
      settled();
    });
  const review = proposal?.preview.delivery_rule;
  return (
    <dialog
      {...modal}
      aria-labelledby="delivery-rule-title"
      className="m-auto max-h-[90vh] w-[min(600px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
      data-delivery-rule-card
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <h2 id="delivery-rule-title" className="text-xl font-semibold text-fg-strong">
          {t(party ? "Delivery rule for the customer" : "Delivery rule for this order")}
        </h2>
        <button className="br-btn" disabled={busy} onClick={leave}>
          {t("Close")}
        </button>
      </header>
      <div className="mb-5 rounded-lg bg-surface-muted p-3 text-sm text-fg-muted">
        {t(
          "An order's rule wins over its customer's. Ship complete holds every line back until the whole order can ship; no backorders reports what stays open after a shipment for cancelling. Nothing changes before you confirm.",
        )}
      </div>
      <div className="mb-4 text-sm">
        <strong>{name}</strong>
      </div>
      {!proposal && (
        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            void prepare();
          }}
        >
          <label className="block text-sm">
            {t("Delivery rule")}
            <select
              className="br-control mt-2 w-full"
              aria-label={t("Delivery rule")}
              value={rule}
              onChange={(event) => setRule(event.target.value as DeliveryRule)}
            >
              {rules.map(([value, label]) => (
                <option key={value} value={value}>
                  {t(label)}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            {t("Why")}
            <input
              className="br-control mt-2 w-full"
              aria-label={t("Why")}
              required
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            />
          </label>
          <div className="flex justify-end">
            <button className="br-btn br-btn-primary" disabled={busy || !reason.trim()}>
              {t("Review change")}
            </button>
          </div>
        </form>
      )}
      {review && (
        <section className="space-y-3 text-sm" data-delivery-rule-review>
          <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-2">
            <dt className="text-fg-muted">{t("Now")}</dt>
            <dd>{review.current ? deliveryRuleLabel(review.current.rule) : t("No rule stated")}</dd>
            <dt className="text-fg-muted">{t("After confirming")}</dt>
            <dd>
              {deliveryRuleLabel(review.proposed.rule)} · {review.proposed.reason}
            </dd>
          </dl>
          {!!review.orders.length && (
            <div>
              <div className="mb-1 text-fg-muted">{t("Open orders it governs")}</div>
              <ul className="space-y-1">
                {review.orders.map((row) => (
                  <li key={row.document_id}>
                    {row.number}: {deliveryRuleLabel(row.now)} → {deliveryRuleLabel(row.after)}
                  </li>
                ))}
              </ul>
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

/** The rule a customer or an order is delivered under, with its history and a change. */
export function DeliveryRuleSection({
  tenant,
  party,
  document: order,
  name,
}: {
  tenant: string;
  party?: string;
  document?: string;
  name: string;
}) {
  const [version, setVersion] = useState(0),
    [editing, setEditing] = useState(false);
  const read = useRead(
    () => deliveryRules.read(tenant, party ? { party_id: party } : { document_id: order! }),
    [tenant, party, order, version],
  );
  const answer = read.data;
  return (
    <section className="mt-4 text-sm" data-delivery-rule-section>
      <div className="font-medium text-fg-strong">{t("Delivery rule")}</div>
      {!answer ? (
        read.loading && <ReadLine />
      ) : (
        <>
          <div className="mt-1">
            {deliveryRuleLabel(answer.effective.rule)}{" "}
            <span className="text-fg-muted">
              ({sourceLabel(answer.effective.source)})
              {answer.effective.reason ? ` · ${answer.effective.reason}` : ""}
            </span>
          </div>
          {answer.history.length > 1 && (
            <details className="mt-1">
              <summary className="text-fg-muted">{t("Earlier statements")}</summary>
              <ul className="mt-1 space-y-1">
                {answer.history.slice(1).map((row) => (
                  <li key={row.source_record_id} className="text-fg-muted">
                    {formatDateTime(row.stated_at)}: {deliveryRuleLabel(row.rule)} · {row.reason}
                  </li>
                ))}
              </ul>
            </details>
          )}
          <button className="br-btn mt-2" onClick={() => setEditing(true)}>
            {t("Change delivery rule")}
          </button>
        </>
      )}
      {editing && (
        <DeliveryRuleCard
          tenant={tenant}
          party={party}
          document={order}
          name={name}
          close={() => setEditing(false)}
          settled={() => {
            setVersion((value) => value + 1);
            window.dispatchEvent(new Event("reality:delivery-settled"));
          }}
        />
      )}
    </section>
  );
}

/**
 * Spec 306 (M06): cancel an open rest the customer's rule says not to deliver.
 * The shared reviewed cancellation; the rule's reason is the default reason.
 */
export function BackorderCancelCard({
  tenant,
  commitment,
  quantity,
  reason: ruleReason,
  close,
  settled,
}: {
  tenant: string;
  commitment: string;
  quantity: string;
  reason: string;
  close: () => void;
  settled: () => void;
}) {
  const alive = useRef(true),
    requestId = useRef(crypto.randomUUID());
  const [reason, setReason] = useState(
    `${t("No backorders by the customer's rule")}${ruleReason ? `: ${ruleReason}` : ""}`,
  );
  const [review, setReview] = useState<{ id: string; token: string } | null>(null),
    [done, setDone] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const pending = useRef<string | null>(null);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      // A review nobody confirmed is withdrawn, also when the card goes away.
      const id = pending.current;
      pending.current = null;
      if (id) void api.rejectProposal(tenant, id, null).catch(() => undefined);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const leave = () => {
    const id = pending.current;
    pending.current = null;
    if (id) void api.rejectProposal(tenant, id, null).catch(() => undefined);
    close();
  };
  const modal = useModal(busy, leave);
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
  return (
    <dialog
      {...modal}
      aria-labelledby="backorder-cancel-title"
      className="m-auto max-h-[90vh] w-[min(520px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
      data-backorder-cancel-card
    >
      <header className="mb-5 flex items-center justify-between gap-4">
        <h2 id="backorder-cancel-title" className="text-xl font-semibold text-fg-strong">
          {t("Cancel the open rest")}
        </h2>
        <button className="br-btn" disabled={busy} onClick={leave}>
          {t("Close")}
        </button>
      </header>
      <p className="mb-4 text-sm">
        {t("Still open")}: {formatQuantity(quantity)}
      </p>
      <label className="block text-sm">
        {t("Why")}
        <input
          className="br-control mt-2 w-full"
          aria-label={t("Why")}
          disabled={busy || !!review}
          value={reason}
          onChange={(event) => setReason(event.target.value)}
        />
      </label>
      <div className="mt-4 flex justify-end gap-2">
        {done ? (
          <div role="status" className="font-medium">
            {t("Done.")}
          </div>
        ) : !review ? (
          <button
            className="br-btn br-btn-primary"
            disabled={busy || !reason.trim()}
            onClick={() =>
              run(async () => {
                const value = await deliveryActions.prepare(
                  tenant,
                  requestId.current,
                  "commitment_cancel",
                  { commitment_id: commitment, reason },
                );
                if (!alive.current) {
                  void api.rejectProposal(tenant, value.id, null).catch(() => undefined);
                  return;
                }
                if (value.review) {
                  pending.current = value.id;
                  setReview({ id: value.id, token: value.review.token });
                }
              })
            }
          >
            {t("Review change")}
          </button>
        ) : (
          <button
            className="br-btn br-btn-primary"
            disabled={busy}
            onClick={() =>
              run(async () => {
                pending.current = null;
                await deliveryActions.confirm(tenant, review.id, review.token);
                if (!alive.current) return;
                setDone(true);
                settled();
              })
            }
          >
            {t("Confirm")}
          </button>
        )}
      </div>
      {error && (
        <div role="alert" className="mt-4 text-sm text-danger">
          {error}
        </div>
      )}
    </dialog>
  );
}

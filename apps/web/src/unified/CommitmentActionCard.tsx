import { useEffect, useRef, useState } from "react";
import { deliveryActions, deliveryApi, type DeliveryProposal, type DeliveryRow } from "../api";
import { formatQuantity, t } from "../localization";
import type { DeliveryAction } from "./actionDiscovery";
import { Inspector } from "./Inspector";
import { ReadLine } from "./ReadState";
import { useProposalRecovery } from "./useProposal";

type RetainedChoice = {
  reservation_id: string;
  quantity: string;
  location_id: string;
  handling_unit_id?: string | null;
  lot_id?: string | null;
  serial_unit_id?: string | null;
};

type CommitmentProposal = Omit<DeliveryProposal, "review" | "observation"> & {
  review: null | {
    token: string;
    intent: Record<string, unknown>;
    effect: Record<string, unknown>;
    state: Record<string, unknown>;
  };
  observation: Record<string, unknown> | null;
};

export function CommitmentActionCard({
  tenant,
  commitment = "",
  proposalId = "",
  tool,
  close,
  prepared,
  settled,
}: {
  tenant: string;
  commitment?: string;
  proposalId?: string;
  tool: DeliveryAction;
  close: () => void;
  prepared?: (id: string) => void;
  settled: () => void;
}) {
  const revising = tool === "commitment_revise";
  const requestId = useRef(crypto.randomUUID());
  const [proposal, setProposal] = useState<CommitmentProposal | null>(null);
  const [rows, setRows] = useState<DeliveryRow[]>([]);
  const [target, setTarget] = useState(commitment);
  const [quantity, setQuantity] = useState("");
  const [dueAt, setDueAt] = useState("");
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");
  const [retained, setRetained] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [error, setError] = useState("");
  const [inspection, inspect] = useState<{ kind: string; id: string } | null>(null);

  useProposalRecovery(
    tenant,
    proposal?.id || proposalId,
    uncertain || proposal?.status === "executing",
    (value) => {
      setProposal(value as unknown as CommitmentProposal);
      setUncertain(false);
      if (value.status === "executed") settled();
    },
    setError,
  );

  useEffect(() => {
    let active = true;
    if (proposalId) {
      setBusy(true);
      deliveryActions
        .review(tenant, proposalId)
        .then((value) => {
          if (active) {
            setProposal(value as unknown as CommitmentProposal);
            setTarget(String(value.review?.intent.commitment_id || ""));
          }
        })
        .catch((reason) => active && setError(reason.message))
        .finally(() => active && setBusy(false));
    } else {
      setLoading(true);
      Promise.all([
        deliveryApi.register(tenant, "", 1, "open", "customer_delivery", ""),
        deliveryApi.register(tenant, "", 1, "open", "supplier_delivery", ""),
      ])
        .then(([customer, supplier]) => active && setRows([...customer.items, ...supplier.items]))
        .catch((reason) => active && setError(reason.message))
        .finally(() => active && setLoading(false));
    }
    return () => {
      active = false;
    };
  }, [tenant, proposalId]);

  const run = async (operation: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await operation();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const prepare = (withRetained = false) =>
    run(async () => {
      const currentIntent = proposal?.review?.intent || {};
      const args: Record<string, unknown> = revising
        ? {
            commitment_id: target || currentIntent.commitment_id,
            ...(quantity || currentIntent.quantity
              ? { quantity: quantity || currentIntent.quantity }
              : {}),
            ...(dueAt || currentIntent.due_at ? { due_at: dueAt || currentIntent.due_at } : {}),
            note: note || currentIntent.note || "",
            ...(withRetained
              ? {
                  retained_allocations: Object.entries(retained)
                    .filter(([, value]) => Number(value) > 0)
                    .map(([reservation_id, value]) => ({ reservation_id, quantity: value })),
                }
              : {}),
          }
        : { commitment_id: target, reason };
      const value = await deliveryActions.prepare(
        tenant,
        withRetained ? crypto.randomUUID() : requestId.current,
        tool,
        args,
      );
      setProposal(value as unknown as CommitmentProposal);
      prepared?.(value.id);
    });

  const confirm = () =>
    run(async () => {
      if (!proposal?.review) return;
      try {
        await deliveryActions.confirm(tenant, proposal.id, proposal.review.token);
      } catch (reason) {
        setUncertain(true);
        throw reason;
      }
      const value = await deliveryActions.detail(tenant, proposal.id);
      setProposal(value as unknown as CommitmentProposal);
      setUncertain(false);
      settled();
    });

  const choices = (proposal?.review?.state.eligible_retained_allocations || []) as RetainedChoice[];
  const selectionRequired = proposal?.review?.effect.selection_required === true;

  return (
    <dialog
      open
      aria-labelledby="commitment-action-title"
      className="m-auto max-h-[90vh] w-[min(620px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <header className="mb-6 flex items-center justify-between gap-4">
        <h2 id="commitment-action-title" className="text-xl font-semibold text-fg-strong">
          {t(revising ? "Revise commitment" : "Cancel commitment remainder")}
        </h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </header>

      {!proposal ? (
        <form
          className="flex flex-col gap-4"
          onSubmit={(event) => {
            event.preventDefault();
            void prepare();
          }}
        >
          <label className="br-label">
            {t("Delivery")}
            <select
              className="br-control mt-2 w-full"
              required
              disabled={busy || loading || Boolean(commitment)}
              value={target}
              onChange={(event) => {
                setTarget(event.target.value);
                requestId.current = crypto.randomUUID();
              }}
            >
              <option value="">{t("Choose a delivery")}</option>
              {rows.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.counterparty} · {row.item} · {formatQuantity(row.open)} {row.unit} · {row.id}
                </option>
              ))}
            </select>
          </label>
          {loading && <ReadLine />}
          {revising ? (
            <>
              <label className="br-label">
                {t("Quantity")}
                <input
                  className="br-control mt-2 w-full"
                  inputMode="decimal"
                  value={quantity}
                  onChange={(event) => setQuantity(event.target.value)}
                />
              </label>
              <label className="br-label">
                {t("Due date")}
                <input
                  className="br-control mt-2 w-full"
                  type="datetime-local"
                  value={dueAt}
                  onChange={(event) => setDueAt(event.target.value)}
                />
              </label>
              <label className="br-label">
                {t("Note")}
                <textarea
                  className="br-control mt-2 min-h-20 w-full"
                  value={note}
                  onChange={(event) => setNote(event.target.value)}
                />
              </label>
            </>
          ) : (
            <label className="br-label">
              {t("Reason")}
              <textarea
                className="br-control mt-2 min-h-20 w-full"
                required
                value={reason}
                onChange={(event) => setReason(event.target.value)}
              />
            </label>
          )}
          <p className="text-sm text-fg-muted">{t("Preparing a review does not change stock.")}</p>
          <button
            className="br-btn br-btn-primary self-start"
            disabled={
              busy || loading || !target || (revising ? !quantity && !dueAt : !reason.trim())
            }
          >
            {t("Review change")}
          </button>
        </form>
      ) : (
        <div className="space-y-5">
          {proposal.review && (
            <>
              <div className="rounded-lg bg-surface-muted p-4 text-sm">
                <p className="font-medium">{t("Current state")}</p>
                <dl className="mt-3 grid grid-cols-2 gap-2">
                  {Object.entries(proposal.review.state)
                    .filter(([, value]) => typeof value === "string")
                    .map(([key, value]) => (
                      <div key={key}>
                        <dt className="text-fg-muted">{key.replaceAll("_", " ")}</dt>
                        <dd className="break-all">{String(value)}</dd>
                      </div>
                    ))}
                </dl>
              </div>
              <div>
                <p className="font-medium">{t("Expected result")}</p>
                <dl className="mt-3 space-y-2 text-sm">
                  {Object.entries(proposal.review.effect).map(([key, value]) => (
                    <div key={key} className="flex justify-between gap-4">
                      <dt className="text-fg-muted">{key.replaceAll("_", " ")}</dt>
                      <dd>{String(value)}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            </>
          )}

          {selectionRequired && (
            <form
              className="space-y-3 rounded-lg border border-border-default p-4"
              onSubmit={(event) => {
                event.preventDefault();
                void prepare(true);
              }}
            >
              <p className="font-medium">{t("Choose retained reservations")}</p>
              <p className="text-sm text-fg-muted">
                {t("Enter only the quantities that should remain reserved.")}
              </p>
              {choices.map((choice) => (
                <label key={choice.reservation_id} className="br-label block">
                  <span className="break-all text-xs">
                    {choice.reservation_id} · {choice.location_id} · {choice.lot_id || "—"}
                  </span>
                  <input
                    className="br-control mt-2 w-full"
                    inputMode="decimal"
                    placeholder={`0 – ${choice.quantity}`}
                    value={retained[choice.reservation_id] || ""}
                    onChange={(event) =>
                      setRetained({ ...retained, [choice.reservation_id]: event.target.value })
                    }
                  />
                </label>
              ))}
              <button className="br-btn br-btn-primary" disabled={busy}>
                {t("Update review")}
              </button>
            </form>
          )}

          {proposal.status === "proposed" && !selectionRequired && (
            <div className="flex gap-3">
              <button
                className="br-btn br-btn-primary"
                disabled={busy}
                onClick={() => void confirm()}
              >
                {t("Confirm change")}
              </button>
              <button className="br-btn" disabled={busy} onClick={close}>
                {t("Cancel")}
              </button>
            </div>
          )}
          {proposal.status === "executing" && <p role="status">{t("Checking result")}</p>}
          {proposal.status === "executed" && (
            <div className="rounded-lg bg-positive-surface p-4">
              <p className="font-medium">{t("Change completed")}</p>
              {proposal.observation && (
                <pre className="mt-3 whitespace-pre-wrap text-xs">
                  {JSON.stringify(proposal.observation, null, 2)}
                </pre>
              )}
            </div>
          )}
          {proposal.links.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {proposal.links.map((link) => (
                <button
                  key={`${link.kind}:${link.id}`}
                  className="br-btn"
                  onClick={() => inspect(link)}
                >
                  {t("Explain")} · {link.kind}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
      {error && (
        <p role="alert" className="mt-5 text-critical-text">
          {error}
        </p>
      )}
      {inspection && <Inspector tenant={tenant} target={inspection} close={() => inspect(null)} />}
    </dialog>
  );
}

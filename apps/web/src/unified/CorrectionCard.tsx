import { useEffect, useRef, useState } from "react";
import {
  api,
  correctionActions,
  deliveryActions,
  operationsApi,
  type CorrectionProposal,
  type Page,
  type WarehouseRow,
} from "../api";
import { formatQuantity, t } from "../localization";
import { ReadLine } from "./ReadState";
import { Inspector } from "./Inspector";
import { useRead } from "./useCompanyContext";
import { useProposalRecovery } from "./useProposal";
const movementLabels: Record<string, string> = {
  receipt: "Receipt",
  shipment: "Shipment",
  transfer: "Transfer",
  return: "Customer return",
  supplier_return: "Supplier return",
  adjustment: "Adjustment",
  opening_stock: "Opening stock",
  correction: "Inverse movement",
};
const fields = [
  "type",
  "item_id",
  "quantity",
  "from_location_id",
  "to_location_id",
  "commitment_id",
  "source_record_id",
  "handling_unit_id",
  "lot_id",
  "serial_unit_id",
  "occurred_at",
  "reason",
];
export function CorrectionCard({
  tenant,
  movement = "",
  proposalId = "",
  close,
  prepared,
  settled,
}: {
  tenant: string;
  movement?: string;
  proposalId?: string;
  close: () => void;
  prepared?: (id: string) => void;
  settled: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    alive = useRef(true),
    request = useRef(crypto.randomUUID());
  const [proposal, setProposal] = useState<CorrectionProposal | null>(null),
    [editing, setEditing] = useState(false),
    [target, setTarget] = useState(movement),
    [query, setQuery] = useState(""),
    [page, setPage] = useState(1),
    [mode, setMode] = useState("reverse"),
    [quantity, setQuantity] = useState(""),
    [reason, setReason] = useState(""),
    [preset, setPreset] = useState<Record<string, unknown> | null>(null),
    [busy, setBusy] = useState(false),
    [uncertain, setUncertain] = useState(false),
    [error, setError] = useState(""),
    [inspection, inspect] = useState<{ kind: string; id: string } | null>(null);
  const list = useRead<{ items: WarehouseRow[]; page: Page } | null>(
    () =>
      !proposal && (!proposalId || editing)
        ? operationsApi.warehouse(tenant, "movements", movement || query, "", "", page)
        : Promise.resolve(null),
    [tenant, movement, query, page, proposal?.id, proposalId, editing],
  );
  const detail = useRead(
    () => (target && !proposal ? api.movementCorrection(tenant, target) : Promise.resolve(null)),
    [tenant, target, proposal?.id],
  );
  const original = detail.data
    ? detail.data.role === "replacement"
      ? detail.data.replacement
      : detail.data.original
    : null;
  const unsupported = Boolean(original?.resolves_movement_id || original?.return_announcement_id);
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
    if (proposalId && !editing) {
      setBusy(true);
      correctionActions
        .review(tenant, proposalId)
        .then((value) => {
          if (active) setProposal(value);
        })
        .catch((error) => {
          if (active) setError(error.message);
        })
        .finally(() => {
          if (active) setBusy(false);
        });
    }
    return () => {
      active = false;
    };
  }, [tenant, proposalId, editing]);
  useProposalRecovery(
    tenant,
    proposal?.id || proposalId,
    uncertain || proposal?.status === "executing",
    (value) => {
      setProposal(value);
      setUncertain(false);
      if (value.status === "executed") settled();
    },
    setError,
    correctionActions.detail,
  );
  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (error) {
      if (alive.current) setError((error as Error).message);
    } finally {
      if (alive.current) setBusy(false);
    }
  };
  const change = () => {
    request.current = crypto.randomUUID();
  };
  const prepare = () =>
    run(async () => {
      if (!original || !detail.data?.correctable)
        throw new Error(t("This movement cannot be corrected."));
      if (mode === "replace" && unsupported && !preset)
        throw new Error(
          t("This movement has return references. Use a dedicated return correction workflow."),
        );
      const replacement: Record<string, unknown> = {
        ...(preset ||
          Object.fromEntries(
            Object.entries(original).filter(
              ([key, value]) => fields.includes(key) && value !== null,
            ),
          )),
        quantity,
      };
      if (replacement.type === "adjustment") replacement.reason = reason;
      const result = await correctionActions.prepare(tenant, request.current, {
        movement_id: target,
        reason,
        ...(mode === "replace" ? { replacement } : {}),
      });
      if (alive.current) {
        setProposal(result);
        prepared?.(result.id);
      }
    });
  const refresh = async () => {
    if (proposal) {
      const result = await correctionActions.detail(tenant, proposal.id);
      if (alive.current) setProposal(result);
    }
  };
  const confirm = () =>
    run(async () => {
      if (!proposal?.review) return;
      let result;
      try {
        result = await deliveryActions.confirm(tenant, proposal.id, proposal.review.token);
      } catch (error) {
        if (alive.current) setUncertain(true);
        throw error;
      }
      if (!alive.current) return;
      setProposal({
        ...proposal,
        status: result.status,
        receipt: result.output,
        verification: "recorded",
        observation: null,
      });
      setUncertain(false);
      settled();
      try {
        await refresh();
      } catch (error) {
        setProposal((value) =>
          value ? { ...value, observation_error: t("Current observation unavailable") } : value,
        );
        throw error;
      }
    });
  const edit = () =>
    run(async () => {
      if (!proposal?.review) return;
      await api.rejectProposal(tenant, proposal.id, null);
      const intent = proposal.review.intent,
        replacement = (intent.replacement as Record<string, unknown> | undefined) || null;
      setTarget(String(intent.movement_id));
      setReason(String(intent.reason));
      setPreset(replacement);
      setMode(replacement ? "replace" : "reverse");
      setQuantity(String(replacement?.quantity || ""));
      change();
      setEditing(true);
      setProposal(null);
    });
  return (
    <dialog
      ref={dialog}
      aria-labelledby="correction-title"
      onCancel={(event) => {
        if (busy) event.preventDefault();
        else close();
      }}
      className="m-auto max-h-[90vh] w-[min(680px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <header className="mb-6 flex items-center justify-between gap-4">
        <h2 id="correction-title" className="text-xl font-semibold text-fg-strong">
          {t("Correct movement")}
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
          {!movement && (
            <label className="br-label">
              {t("Search movements")}
              <input
                className="br-control mt-2 w-full"
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setPage(1);
                  setTarget("");
                  setPreset(null);
                  change();
                }}
              />
            </label>
          )}
          <label className="br-label">
            {t("Movement")}
            <select
              aria-label={t("Movement")}
              className="br-control mt-2 w-full"
              required
              disabled={busy || list.loading}
              value={target}
              onChange={(event) => {
                setTarget(event.target.value);
                setPreset(null);
                setQuantity("");
                change();
              }}
            >
              <option value="">{t("Select movement")}</option>
              {list.data?.items.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.item} · {formatQuantity(row.quantity || "0")} {row.unit} ·{" "}
                  {row.from_location || row.to_location} · {row.id}
                </option>
              ))}
            </select>
          </label>
          {(list.loading || detail.loading) && <ReadLine />}
          {list.error && (
            <div role="alert">
              {list.error}
              <button type="button" className="br-btn" onClick={list.refresh}>
                {t("Retry")}
              </button>
            </div>
          )}
          {detail.error && (
            <div role="alert">
              {detail.error}
              <button type="button" className="br-btn" onClick={detail.refresh}>
                {t("Retry")}
              </button>
            </div>
          )}
          {list.data?.page && list.data.page.pages > 1 && !movement && (
            <div className="flex items-center justify-between gap-3 border-t border-border-default pt-3 text-sm">
              <button
                type="button"
                className="br-btn"
                disabled={!list.data.page.has_previous || list.loading}
                onClick={() => {
                  setPage(page - 1);
                  setTarget("");
                }}
              >
                {t("Previous")}
              </button>
              <span>
                {list.data.page.number} / {list.data.page.pages}
              </span>
              <button
                type="button"
                className="br-btn"
                disabled={!list.data.page.has_next || list.loading}
                onClick={() => {
                  setPage(page + 1);
                  setTarget("");
                }}
              >
                {t("Next")}
              </button>
            </div>
          )}
          {list.data && !list.data.items.length && <p role="status">{t("No matching records")}</p>}
          {detail.data && !detail.data.correctable && (
            <p role="alert">{t("This movement cannot be corrected.")}</p>
          )}
          <label className="br-label">
            {t("Correction type")}
            <select
              aria-label={t("Correction type")}
              className="br-control mt-2 w-full"
              disabled={busy}
              value={mode}
              onChange={(event) => {
                setMode(event.target.value);
                change();
              }}
            >
              <option value="reverse">{t("Reverse this movement")}</option>
              <option value="replace" disabled={unsupported && !preset}>
                {t("Replace with correct quantity")}
              </option>
            </select>
          </label>
          {unsupported && (
            <p className="text-sm text-fg-muted">
              {t(
                "This movement has return references. Use a dedicated return correction workflow.",
              )}
            </p>
          )}
          {mode === "replace" && (
            <label className="br-label">
              {t("Correct quantity")}
              <input
                aria-label={t("Correct quantity")}
                className="br-control mt-2 w-full"
                inputMode="decimal"
                value={quantity}
                required
                disabled={busy}
                onChange={(event) => {
                  setQuantity(event.target.value);
                  change();
                }}
              />
            </label>
          )}
          <label className="br-label">
            {t("Correction reason")}
            <textarea
              aria-label={t("Correction reason")}
              className="br-control mt-2 w-full"
              required
              value={reason}
              disabled={busy}
              onChange={(event) => {
                setReason(event.target.value);
                change();
              }}
            />
          </label>
          <p className="text-sm text-fg-muted">
            {t("The original stays in history. Consumed reservations are not restored.")}
          </p>
          <p className="text-sm text-fg-muted">{t("Preparing a review does not change stock.")}</p>
          <button
            className="br-btn br-btn-primary self-start"
            disabled={
              busy ||
              !detail.data?.correctable ||
              detail.loading ||
              !reason.trim() ||
              (mode === "replace" && !quantity)
            }
          >
            {t("Review change")}
          </button>
        </form>
      ) : (
        <div className="space-y-5">
          {proposal.review && (
            <>
              <p data-original-content className="whitespace-pre-wrap break-words">
                {String(proposal.review.intent.reason)}
              </p>
              <div className="grid gap-3 sm:grid-cols-3">
                {(
                  [
                    ["Original movement", proposal.review.state.correction.original],
                    ["Inverse movement", proposal.review.state.correction.compensation],
                    ["Replacement", proposal.review.state.correction.replacement],
                  ] as const
                ).map(([label, value]) => {
                  const pools = proposal.review!.state.pools;
                  const item = pools.find((pool) => pool.item_id === value?.item_id);
                  const location = (id: unknown) =>
                    pools.find((pool) => pool.item_id === value?.item_id && pool.location_id === id)
                      ?.location || "—";
                  return (
                    <div key={label} className="min-w-0 rounded-lg bg-surface-muted p-3">
                      <p className="text-xs text-fg-muted">{t(label)}</p>
                      <strong className="mt-2 block">
                        {value
                          ? `${formatQuantity(String(value.quantity))} ${item?.unit || ""}`
                          : t("None")}
                      </strong>
                      {value && (
                        <div className="mt-2 space-y-1 break-words text-xs text-fg-muted">
                          <p>{item?.item}</p>
                          <p>{t(movementLabels[String(value.type)] || "Movement")}</p>
                          <p>
                            {location(value.from_location_id)} → {location(value.to_location_id)}
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              {proposal.review.state.pools.map((pool) => (
                <div
                  key={`${pool.item_id}:${pool.location_id}`}
                  className="rounded-lg border border-border-default p-4"
                >
                  <p className="font-medium">
                    {pool.item} · {pool.location}
                  </p>
                  <p className="mt-2">
                    {t("Physical stock")}: {formatQuantity(pool.physical)} →{" "}
                    <strong>
                      {formatQuantity(pool.after)} {pool.unit}
                    </strong>
                  </p>
                  <p className="mt-2 text-sm text-fg-muted">
                    {t("Reserved")}: {formatQuantity(pool.reserved)} {pool.unit} ·{" "}
                    {t("Available after correction")}: {formatQuantity(pool.available_after)}{" "}
                    {pool.unit}
                  </p>
                </div>
              ))}
              <p className="text-sm text-fg-muted">
                {t("The original stays in history. Consumed reservations are not restored.")}
              </p>
            </>
          )}
          <p role="status">
            {t(
              proposal.status === "executed"
                ? "Recorded"
                : proposal.status === "rejected"
                  ? "Rejected"
                  : uncertain || proposal.status === "executing"
                    ? "Execution outcome is being checked. Do not repeat the action."
                    : "Review the exact change before confirming.",
            )}
          </p>
          {proposal.status === "proposed" && !uncertain && (
            <div className="flex flex-wrap gap-3">
              <button
                className="br-btn br-btn-primary"
                disabled={busy || !proposal.review}
                onClick={confirm}
              >
                {t("Confirm change")}
              </button>
              <button
                className="br-btn"
                disabled={busy}
                onClick={() =>
                  run(async () => {
                    await api.rejectProposal(tenant, proposal.id, null);
                    await refresh();
                  })
                }
              >
                {t("Reject")}
              </button>
              <button className="br-btn" disabled={busy} onClick={edit}>
                {t("Edit")}
              </button>
            </div>
          )}
          {(uncertain || ["executing", "executed"].includes(proposal.status)) && (
            <button
              className="br-btn"
              disabled={busy}
              onClick={() =>
                run(async () => {
                  const result = await correctionActions.reconcile(tenant, proposal.id);
                  if (alive.current) {
                    setProposal(result);
                    setUncertain(false);
                    if (result.status === "executed") settled();
                  }
                })
              }
            >
              {t("Check outcome")}
            </button>
          )}
          {proposal.status === "executed" &&
            !["verified", "recorded"].includes(proposal.verification) && (
              <p role="alert">{t("Recorded result is not yet verified.")}</p>
            )}
          {proposal.observation_error && (
            <p role="alert">
              {t("Recorded result is separate from the current observation.")}{" "}
              {proposal.observation_error}
            </p>
          )}
          {proposal.status === "executed" && proposal.observation && (
            <div className="space-y-2">
              <h3 className="font-medium">{t("Current physical stock")}</h3>
              {proposal.observation.pools.map((pool) => (
                <p key={`${pool.item_id}:${pool.location_id}`} className="text-sm">
                  {pool.item} · {pool.location}: {formatQuantity(pool.physical)} {pool.unit}
                </p>
              ))}
            </div>
          )}
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
          <details>
            <summary>{t("Technical details")}</summary>
            <pre
              data-original-content
              className="mt-3 overflow-auto whitespace-pre-wrap break-all text-xs"
            >
              {JSON.stringify(
                {
                  id: proposal.id,
                  review: proposal.review,
                  receipt: proposal.receipt,
                  verification: proposal.verification,
                  links: proposal.links,
                },
                null,
                2,
              )}
            </pre>
          </details>
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

import { CustomerHoldCard } from "./CustomerHoldCard";
import { OpeningStockCard } from "./OpeningStockCard";
import { CreditCard } from "./CreditCard";
import { FinancialReversalCard } from "./FinancialReversalCard";
import { RefundCard } from "./RefundCard";
import { PaymentCard } from "./PaymentCard";
import { InvoiceCard } from "./InvoiceCard";
import { OrderCard } from "./OrderCard";
import { CorrectionCard } from "./CorrectionCard";
import { holdReason } from "./holdLabels";
import { useRead } from "./useCompanyContext";
import type { DeliveryAction } from "./ActionLauncher";
import { ReferenceChoices } from "./ReferenceChoices";
import { useProposalRecovery } from "./useProposal";
import { Inspector } from "./Inspector";
import { DecisionActionBar } from "./DecisionReview";
import { useEffect, useRef, useState } from "react";
import {
  api,
  deliveryActions,
  deliveryApi,
  type DeliveryProposal,
  type DeliveryRow,
  operationsApi,
  type WarehouseRow,
  type Page,
} from "../api";
import { formatQuantity, t } from "../localization";
import { ReadLine } from "./ReadState";
import { ShipmentActions } from "./ShipmentActions";
import { CommitmentActionCard } from "./CommitmentActionCard";

function DeliveryActionCard({
  tenant,
  commitment = "",
  reservation = "",
  proposalId = "",
  tool = "reserve",
  close,
  prepared,
  settled,
}: {
  tenant: string;
  commitment?: string;
  reservation?: string;
  proposalId?: string;
  tool?: DeliveryAction;
  close: () => void;
  prepared?: (id: string) => void;
  settled: () => void;
}) {
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  const dialog = useRef<HTMLDialogElement>(null);
  const requestId = useRef(crypto.randomUUID());
  const [inspection, inspect] = useState<{ kind: string; id: string } | null>(null);
  const [activeTool, setActiveTool] = useState(tool);
  const [editing, setEditing] = useState(false);
  const [proposal, setProposal] = useState<DeliveryProposal | null>(null);
  const [rows, setRows] = useState<DeliveryRow[]>([]);
  const [target, setTarget] = useState(reservation || commitment);
  const [reservations, setReservations] = useState<WarehouseRow[]>([]);
  const [page, setPage] = useState(1);
  const [pager, setPager] = useState<Page | null>(null);
  const [loading, setLoading] = useState(false);
  const [retry, setRetry] = useState(0);
  const releasing = activeTool === "reservation_release";
  const receiving = activeTool === "receipt";
  const holding = activeTool === "commitment_hold" || activeTool === "commitment_hold_release";
  const placingHold = activeTool === "commitment_hold";
  const [reasonCode, setReasonCode] = useState("");
  const [note, setNote] = useState("");
  const holdRead = useRead(
    () =>
      holding && target && !proposal ? deliveryApi.detail(tenant, target) : Promise.resolve(null),
    [tenant, target, holding, proposal?.id, retry],
  );
  const [query, setQuery] = useState("");
  const [tracking, setTracking] = useState<Record<string, string>>({});
  const [quantity, setQuantity] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [uncertain, setUncertain] = useState(false);
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
  );
  const refresh = async (id = proposal?.id || proposalId) => {
    if (!id) return;
    const result = await deliveryActions.detail(tenant, id);
    if (!alive.current) return;
    setProposal(result);
    if (result.status === "executed" || result.status === "rejected") settled();
  };
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    const node = dialog.current;
    node?.showModal();
    return () => {
      node?.close();
      previous?.focus();
    };
  }, []);
  useEffect(() => {
    let active = true;
    if (proposalId && !editing) {
      setBusy(true);
      deliveryActions
        .review(tenant, proposalId)
        .then((result) => {
          if (active) {
            setProposal(result);
            setActiveTool(
              result.tool === "movement_create" && result.review?.intent.movement_type === "receipt"
                ? "receipt"
                : (result.tool as DeliveryAction),
            );
          }
        })
        .catch((reason) => {
          if (active) setError(reason.message);
        })
        .finally(() => {
          if (active) setBusy(false);
        });
    } else {
      setLoading(true);
      setError("");
      if (activeTool === "reservation_release") {
        operationsApi
          .warehouse(
            tenant,
            "reservations",
            reservation || query || (editing ? target : ""),
            "active",
            "",
            page,
          )
          .then((result) => {
            if (active) {
              setReservations(result.items);
              setPager(result.page);
            }
          })
          .catch((reason) => {
            if (active) setError(reason.message);
          })
          .finally(() => {
            if (active) setLoading(false);
          });
        return () => {
          active = false;
        };
      }
      const selectedCommitment = commitment || (editing ? target : "");
      const load = selectedCommitment
        ? deliveryApi.detail(tenant, selectedCommitment).then((result) => [result.case])
        : deliveryApi
            .register(
              tenant,
              query,
              page,
              "open",
              activeTool === "receipt" ? "supplier_delivery" : "customer_delivery",
              "",
            )
            .then((result) => {
              if (active) setPager(result.page);
              return result.items;
            });
      load
        .then((result) => {
          if (active) setRows(result);
        })
        .catch((reason) => {
          if (active) setError(reason.message);
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    }
    return () => {
      active = false;
    };
  }, [tenant, commitment, reservation, proposalId, query, page, activeTool, retry, editing]);
  const run = async (action: () => Promise<void>) => {
    setError("");
    setBusy(true);
    try {
      await action();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const prepare = () =>
    run(async () => {
      const detail = rows.find((row) => row.id === target);
      if (!releasing && !detail) throw new Error(t("Choose a delivery"));
      if (releasing && !reservations.some((row) => row.id === target))
        throw new Error(t("No active reservations."));
      const identities = Object.fromEntries(Object.entries(tracking).filter(([, value]) => value));
      const args = releasing
        ? { reservation_id: target }
        : holding
          ? { commitment_id: target, ...(placingHold ? { reason_code: reasonCode, note } : {}) }
          : activeTool === "reserve"
            ? { commitment_id: target, quantity, ...identities }
            : {
                movement_type: receiving ? "receipt" : "shipment",
                commitment_id: target,
                item_id: detail!.item_id,
                [receiving ? "to_location_id" : "from_location_id"]: detail!.location_id,
                quantity,
                ...identities,
              };
      const result = await deliveryActions.prepare(
        tenant,
        requestId.current,
        receiving ? "movement_create" : activeTool,
        args,
      );
      if (!alive.current) return;
      setProposal(result);
      prepared?.(result.id);
    });
  const confirm = () =>
    run(async () => {
      if (!proposal?.review) return;
      let result;
      try {
        result = await deliveryActions.confirm(tenant, proposal.id, proposal.review.token);
      } catch (reason) {
        if (alive.current) setUncertain(true);
        throw reason;
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
      } catch (reason) {
        if (alive.current)
          setProposal((value) =>
            value ? { ...value, observation_error: t("Current observation unavailable") } : value,
          );
        throw reason;
      }
    });
  const reject = () =>
    run(async () => {
      if (!proposal) return;
      await api.rejectProposal(tenant, proposal.id, null);
      await refresh();
    });
  return (
    <dialog
      ref={dialog}
      onCancel={(event) => {
        if (busy) event.preventDefault();
        else close();
      }}
      aria-labelledby="action-title"
      className="m-auto max-h-[90vh] w-[min(620px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <header className="mb-6 flex items-center justify-between gap-4">
        <h2 id="action-title" className="text-xl font-semibold text-fg-strong">
          {t(
            holding
              ? placingHold
                ? "Place delivery hold"
                : "Release delivery hold"
              : releasing
                ? "Release reservation"
                : receiving
                  ? "Receive goods"
                  : activeTool === "reserve"
                    ? "Reserve stock"
                    : "Record shipment",
          )}
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
          {!commitment && !reservation && (
            <label className="br-label">
              {t(releasing ? "Search reservations" : "Search deliveries")}
              <input
                className="br-control mt-2 w-full"
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setPage(1);
                  setTarget("");
                }}
              />
            </label>
          )}
          <label className="br-label">
            {t(releasing ? "Reservation" : "Delivery")}
            <select
              aria-label={t(releasing ? "Reservation" : "Delivery")}
              disabled={busy || loading}
              className="br-control mt-2 w-full"
              value={target}
              required
              onChange={(event) => {
                setTarget(event.target.value);
                setTracking({});
                requestId.current = crypto.randomUUID();
              }}
            >
              <option value="">{t(releasing ? "Select reservation" : "Choose a delivery")}</option>
              {releasing &&
                reservations.map((row) => (
                  <option key={row.id} value={row.id}>
                    {row.item} · {row.location} · {formatQuantity(row.quantity || "0")} {row.unit} ·{" "}
                    {row.id}
                  </option>
                ))}
              {!releasing &&
                rows.map((row) => (
                  <option key={row.id} value={row.id}>
                    {row.counterparty} · {row.item} · {row.location} · {formatQuantity(row.open)}{" "}
                    {row.unit} · {row.id}
                  </option>
                ))}
            </select>
          </label>
          {loading && <ReadLine />}
          {!loading && !(releasing ? reservations.length : rows.length) && (
            <p role="status">{t("No matching records")}</p>
          )}
          {error && (
            <button type="button" className="br-btn" onClick={() => setRetry(retry + 1)}>
              {t("Retry")}
            </button>
          )}
          {pager && pager.pages > 1 && !commitment && !reservation && (
            <div className="flex items-center justify-between gap-3 border-t border-border-default pt-3 text-sm text-fg-muted">
              <button
                type="button"
                className="br-btn"
                disabled={!pager.has_previous || loading}
                onClick={() => {
                  setPage(page - 1);
                  setTarget("");
                }}
              >
                {t("Previous")}
              </button>
              <span>
                {pager.number} / {pager.pages}
              </span>
              <button
                type="button"
                className="br-btn"
                disabled={!pager.has_next || loading}
                onClick={() => {
                  setPage(page + 1);
                  setTarget("");
                }}
              >
                {t("Next")}
              </button>
            </div>
          )}
          {holding ? (
            <>
              <p className="text-sm text-fg-muted">
                {t(
                  placingHold
                    ? "Pause this delivery with a reason."
                    : "Release this delivery’s own holds. Customer-wide holds still apply.",
                )}
              </p>
              {holdRead.loading && <ReadLine />}
              {holdRead.error && (
                <div role="alert">
                  {holdRead.error}
                  <button type="button" className="br-btn" onClick={holdRead.refresh}>
                    {t("Retry")}
                  </button>
                </div>
              )}
              {placingHold ? (
                <>
                  <label className="br-label">
                    {t("Hold reason")}
                    <select
                      aria-label={t("Hold reason")}
                      className="br-control mt-2 w-full"
                      required
                      disabled={busy || holdRead.loading || !holdRead.data}
                      value={reasonCode}
                      onChange={(event) => {
                        setReasonCode(event.target.value);
                        requestId.current = crypto.randomUUID();
                      }}
                    >
                      <option value="">{t("Select hold reason")}</option>
                      {holdRead.data?.hold_reasons?.map((code) => (
                        <option key={code} value={code}>
                          {holdReason(code)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="br-label">
                    {t("Hold note (optional)")}
                    <textarea
                      aria-label={t("Hold note (optional)")}
                      className="br-control mt-2 min-h-20 w-full"
                      disabled={busy}
                      value={note}
                      onChange={(event) => {
                        setNote(event.target.value);
                        requestId.current = crypto.randomUUID();
                      }}
                    />
                  </label>
                </>
              ) : (
                holdRead.data?.case.blockers
                  .filter((row) => row.scope === "commitment")
                  .map((row) => (
                    <div key={row.id} className="rounded-lg bg-surface-muted p-3 text-sm">
                      <strong>{holdReason(row.reason)}</strong>
                      {row.note && (
                        <p data-original-content className="mt-2 whitespace-pre-wrap break-words">
                          {row.note}
                        </p>
                      )}
                    </div>
                  ))
              )}
            </>
          ) : releasing ? (
            <p className="text-sm text-fg-muted">
              {t(
                "Releasing a reservation makes stock available again. The order and physical stock remain unchanged.",
              )}
            </p>
          ) : (
            <label className="br-label">
              {t("Quantity")}
              <input
                className="br-control mt-2 w-full"
                inputMode="decimal"
                disabled={busy}
                required
                value={quantity}
                onChange={(event) => {
                  setQuantity(event.target.value);
                  requestId.current = crypto.randomUUID();
                }}
              />
            </label>
          )}
          {target && !releasing && !holding && (
            <details>
              <summary>{t("Tracking references")}</summary>
              <div className="mt-3 space-y-4">
                {[
                  ["handling_unit", "Handling unit"],
                  ["lot", "Lot"],
                  ["serial_unit", "Serial unit"],
                ].map(([family, label]) => (
                  <ReferenceChoices
                    key={`${target}:${family}`}
                    tenant={tenant}
                    commitment={target}
                    family={family}
                    label={label}
                    value={tracking[`${family}_id`] || ""}
                    disabled={busy}
                    change={(value) => {
                      setTracking({ ...tracking, [`${family}_id`]: value });
                      requestId.current = crypto.randomUUID();
                    }}
                  />
                ))}
              </div>
            </details>
          )}
          <p className="text-sm text-fg-muted">{t("Preparing a review does not change stock.")}</p>
          <button
            className="br-btn br-btn-primary self-start"
            disabled={
              busy ||
              loading ||
              !target ||
              (holding
                ? holdRead.loading || !holdRead.data || (placingHold && !reasonCode)
                : !releasing && !quantity)
            }
          >
            {t("Review change")}
          </button>
        </form>
      ) : (
        <div className="space-y-5">
          {proposal.review && (
            <>
              <div className="rounded-lg bg-surface-muted p-4">
                <p className="font-medium">
                  {proposal.review.state.case.counterparty} · {proposal.review.state.case.item}
                </p>
                <p className="mt-1 text-sm text-fg-muted">{proposal.review.state.case.location}</p>
              </div>
              {releasing && (
                <p className="break-all text-sm">
                  {t("Reservation")} · {String(proposal.review.intent.reservation_id)}
                </p>
              )}
              {holding && (
                <div className="space-y-3 text-sm">
                  <p>
                    {t(
                      placingHold
                        ? "Pause this delivery with a reason."
                        : "Release this delivery’s own holds. Customer-wide holds still apply.",
                    )}
                  </p>
                  {(placingHold
                    ? [
                        {
                          id: "intent",
                          reason_code: String(proposal.review.intent.reason_code),
                          note: String(proposal.review.intent.note || ""),
                        },
                      ]
                    : proposal.review.state.holds || []
                  ).map((hold) => (
                    <div key={hold.id} className="rounded-lg bg-surface-muted p-3">
                      <strong>{holdReason(hold.reason_code)}</strong>
                      {hold.note && (
                        <p data-original-content className="mt-2 whitespace-pre-wrap break-words">
                          {hold.note}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
              <dl className="space-y-2">
                {Object.entries(proposal.review.effect).map(([key, value]) => (
                  <div key={key} className="flex justify-between gap-4">
                    <dt>
                      {t(
                        key === "holds_set"
                          ? "Delivery holds to set"
                          : key === "holds_released"
                            ? "Delivery holds to release"
                            : key === "released"
                              ? "Released"
                              : key === "received"
                                ? "Received"
                                : key === "applied"
                                  ? "Reserved"
                                  : key === "shipped"
                                    ? "Shipped"
                                    : key === "shortage"
                                      ? "Shortage"
                                      : "Requested",
                      )}
                    </dt>
                    <dd>
                      {formatQuantity(value)} {holding ? "" : proposal.review!.state.case.unit}
                    </dd>
                  </div>
                ))}
              </dl>
            </>
          )}
          {proposal.review &&
            Object.entries(proposal.review.intent)
              .filter(
                ([key, value]) =>
                  ["handling_unit_id", "lot_id", "serial_unit_id"].includes(key) && value,
              )
              .map(([key, value]) => (
                <p key={key} className="break-all text-sm">
                  <span className="text-fg-muted">
                    {t(
                      key === "lot_id"
                        ? "Lot"
                        : key === "serial_unit_id"
                          ? "Serial unit"
                          : "Handling unit",
                    )}
                  </span>{" "}
                  · {String(value)}
                </p>
              ))}
          <p role="status">
            {t(
              proposal.status === "executed"
                ? "Recorded"
                : proposal.status === "rejected"
                  ? "Rejected"
                  : proposal.status === "executing" || uncertain
                    ? "Execution outcome is being checked. Do not repeat the action."
                    : "Review the exact change before confirming.",
            )}
          </p>
          {proposal.status === "proposed" && !uncertain && (
            <DecisionActionBar
              busy={busy || !proposal.review}
              reject={reject}
              edit={() =>
                run(async () => {
                  await api.rejectProposal(tenant, proposal.id, null);
                  setRows([
                    {
                      ...proposal.review!.state.case,
                      location_id:
                        ((proposal.review!.intent.from_location_id ||
                          proposal.review!.intent.to_location_id) as string | undefined) ||
                        proposal.review!.state.case.location_id,
                    },
                  ]);
                  setTarget(
                    releasing
                      ? String(proposal.review!.intent.reservation_id)
                      : proposal.review!.state.case.id,
                  );
                  if (releasing)
                    setReservations([
                      {
                        id: String(proposal.review!.intent.reservation_id),
                        item: proposal.review!.state.case.item || "",
                        location: proposal.review!.state.case.location || "",
                        sku: "",
                        unit: proposal.review!.state.case.unit,
                        quantity: proposal.review!.effect.released,
                        status: "active",
                      },
                    ]);
                  setReasonCode(String(proposal.review!.intent.reason_code || ""));
                  setNote(String(proposal.review!.intent.note || ""));
                  setQuantity(
                    String(
                      proposal.review!.intent.quantity ??
                        proposal.review!.effect.requested ??
                        proposal.review!.state.case.open,
                    ),
                  );
                  setTracking(
                    Object.fromEntries(
                      Object.entries(proposal.review!.intent).filter(
                        ([key, value]) =>
                          ["handling_unit_id", "lot_id", "serial_unit_id"].includes(key) &&
                          typeof value === "string",
                      ),
                    ) as Record<string, string>,
                  );
                  requestId.current = crypto.randomUUID();
                  setProposal(null);
                  setEditing(true);
                })
              }
              confirm={confirm}
            />
          )}
          {(uncertain || proposal.status === "executing" || proposal.status === "executed") && (
            <button
              className="br-btn"
              disabled={busy}
              onClick={() =>
                run(async () => {
                  const result = await deliveryActions.reconcile(tenant, proposal.id);
                  if (!alive.current) return;
                  setProposal(result);
                  setUncertain(false);
                  if (result.status === "executed") settled();
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
          {!!proposal.links.length && (
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
      {inspection && <Inspector tenant={tenant} target={inspection} close={() => inspect(null)} />}
      {error && (
        <p role="alert" className="mt-5 text-critical-text">
          {error}
        </p>
      )}
    </dialog>
  );
}

export function ActionCard(
  props: Parameters<typeof DeliveryActionCard>[0] & {
    party?: string;
    movement?: string;
    direction?: string;
    postingGroup?: string;
    invoice?: string;
    creditNote?: string;
    order?: string;
    shipmentInput?: {
      counterparty_id: string;
      movements: Record<string, string>[];
    };
  },
) {
  const kind = useRead(
    () =>
      props.proposalId
        ? deliveryActions.detail(props.tenant, props.proposalId)
        : Promise.resolve(null),
    [props.tenant, props.proposalId],
  );
  if (props.proposalId && !kind.data)
    return (
      <dialog
        open
        className="m-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default"
      >
        {kind.error ? <p role="alert">{kind.error}</p> : <ReadLine />}
        {kind.error && (
          <button className="br-btn mt-3" onClick={kind.refresh}>
            {t("Retry")}
          </button>
        )}
        <button className="br-btn mt-3" onClick={props.close}>
          {t("Close")}
        </button>
      </dialog>
    );
  const activeTool = kind.data?.tool || props.tool;
  if (
    activeTool === "shipment_notice_record" ||
    activeTool === "shipment_dispatch" ||
    activeTool === "shipment_receive" ||
    activeTool === "shipment_event_record" ||
    activeTool === "shipment_event_supersede" ||
    activeTool === "return_disposition"
  )
    return <ShipmentActions {...props} tool={activeTool} />;
  if (activeTool === "party_delivery_hold" || activeTool === "party_delivery_hold_release")
    return <CustomerHoldCard {...props} tool={activeTool} />;
  if (activeTool === "commitment_revise" || activeTool === "commitment_cancel")
    return <CommitmentActionCard {...props} tool={activeTool} />;
  if (props.tool === "opening_stock" || kind.data?.movement_type === "opening_stock")
    return <OpeningStockCard {...props} />;
  if (activeTool === "customer_refund_post") return <RefundCard {...props} />;
  if (activeTool === "sales_credit_record") return <CreditCard {...props} />;
  if (activeTool === "ledger_reverse") return <FinancialReversalCard {...props} />;
  if (activeTool === "customer_payment_post" || activeTool === "supplier_payment_post")
    return <PaymentCard {...props} tool={activeTool} />;
  if (activeTool === "sales_invoice_record" || activeTool === "supplier_invoice_record")
    return <InvoiceCard {...props} tool={activeTool} />;
  if ((kind.data?.tool || props.tool) === "order_create") return <OrderCard {...props} />;
  return (kind.data?.tool || props.tool) === "movement_correct" ? (
    <CorrectionCard {...props} />
  ) : (
    <DeliveryActionCard {...props} />
  );
}

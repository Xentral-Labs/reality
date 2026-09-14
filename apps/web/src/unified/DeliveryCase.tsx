import { ContextActions } from "./ActionLauncher";
import { holdReason } from "./holdLabels";
import { ActionCard } from "./ActionCard";
import type { DeliveryAction } from "./ActionLauncher";
import { useState } from "react";
import { deliveryApi } from "../api";
import { formatQuantity, formatDateTime, t } from "../localization";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { Inspector } from "./Inspector";
import type { Selection } from "./routing";

export function DeliveryCase({
  tenant,
  id,
  navigate,
  receive,
}: {
  tenant: string;
  id: string;
  navigate: (changes: Partial<Selection>) => void;
  receive?: (id: string) => void;
}) {
  const { data, loading, error, refresh } = useRead(
    () => deliveryApi.detail(tenant, id),
    [tenant, id],
  );
  const [action, setAction] = useState<DeliveryAction | null>(null);
  const [target, setTarget] = useState<{ kind: string; id: string } | null>(null);
  const [cursor, setCursor] = useState("");
  const historyRead = useRead(() => deliveryApi.detail(tenant, id, cursor), [tenant, id, cursor]);
  if (!data)
    return (
      <div className="space-y-5">
        <button className="br-btn" onClick={() => navigate({ commitment: "" })}>
          {t("Back to commitments")}
        </button>
        <ReadState loading={loading} error={error} retry={refresh} />
      </div>
    );
  const detail = data.case;
  return (
    <div className="min-w-0">
      <section className="min-w-0 space-y-5">
        <button className="br-btn" onClick={() => navigate({ commitment: "" })}>
          {t("Back to commitments")}
        </button>
        <article className="rounded-xl border border-border-default bg-surface p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-fg-muted">
                {t(detail.type === "supplier_delivery" ? "Supplier delivery" : "Customer delivery")}
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-fg-strong">{detail.counterparty}</h2>
              <p className="mt-2 text-fg-muted">
                {detail.item} · {detail.location}
              </p>
            </div>
            <button className="br-btn" onClick={() => setTarget({ kind: "commitment", id })}>
              {t("Explain")}
            </button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {(
              [
                ["customer", detail.party_id, detail.counterparty],
                ["item", detail.item_id, detail.item],
                ["location", detail.location_id, detail.location],
              ] as const
            )
              .filter(([, id]) => id)
              .map(([family, record, label]) => (
                <button
                  key={family}
                  className="br-btn"
                  onClick={() =>
                    navigate({
                      route: "master-data",
                      family,
                      record: record!,
                      proposal: "",
                      q: "",
                      page: 1,
                    })
                  }
                >
                  {t("Details")} · {label}
                </button>
              ))}
          </div>
          <div className="my-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
            {(
              [
                ["Promised", detail.promised],
                ["Fulfilled", detail.fulfilled],
                ["Reserved", detail.reserved],
                ["Still open", detail.open],
              ] as const
            ).map(([label, value]) => (
              <button
                key={label}
                className="rounded-lg bg-surface-muted p-4 text-left"
                onClick={() => setTarget({ kind: "commitment", id })}
              >
                <span className="text-xs text-fg-muted">{t(label)}</span>
                <strong className="mt-2 block text-xl text-fg-strong">
                  {formatQuantity(value)}{" "}
                  <small className="text-xs font-normal">{detail.unit}</small>
                </strong>
              </button>
            ))}
          </div>
          <div className="flex flex-wrap gap-3">
            {detail.type === "customer_delivery" && (
              <ContextActions
                context="commitment.customer"
                onOpen={setAction}
                exclude={[
                  detail.blockers.some((row) => row.scope === "commitment")
                    ? "commitment_hold"
                    : "commitment_hold_release",
                  detail.blockers.some((row) => row.scope === "party")
                    ? "party_delivery_hold"
                    : "party_delivery_hold_release",
                ]}
              />
            )}
            {detail.type === "supplier_delivery" && detail.status === "open" && receive && (
              <ContextActions context="commitment.supplier" onOpen={() => receive(id)} />
            )}
            <button
              className="br-btn"
              onClick={() => window.dispatchEvent(new Event("reality:open-chat"))}
            >
              {t("Discuss with Reality")}
            </button>
          </div>
          {!!detail.blockers.length && (
            <div className="mt-5 rounded-lg bg-caution-bg p-4 text-caution-text">
              {detail.blockers.map((row) => (
                <div key={row.id} className="mb-3 last:mb-0">
                  <p className="font-semibold">
                    {t(row.scope === "party" ? "Customer-wide hold" : "Delivery hold")}
                  </p>
                  <p className="mt-1 text-sm">{holdReason(row.reason)}</p>
                  {row.note && (
                    <p
                      data-original-content
                      className="mt-2 whitespace-pre-wrap break-words text-sm"
                    >
                      {row.note}
                    </p>
                  )}
                  {row.scope === "party" && (
                    <p className="mt-2 text-sm">
                      {t("This customer-wide hold remains when a delivery hold is released.")}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </article>
        <article className="rounded-xl border border-border-default bg-surface p-6">
          <h3 className="font-semibold text-fg-strong">{t("Inventory at this location")}</h3>
          <a
            className="mt-3 inline-block text-sm text-accent underline"
            href={`/app/warehouse?${new URLSearchParams({ tenant, item: detail.item_id || "" })}`}
            onClick={(event) => {
              event.preventDefault();
              navigate({
                route: "warehouse",
                warehouseView: "stock",
                item: detail.item_id || "",
                entry: "",
                state: "",
                q: "",
                page: 1,
              });
            }}
          >
            {t("Open inventory")}
          </a>
          <div className="mt-4 grid grid-cols-3 gap-4">
            {(
              [
                ["Physical", data.inventory.physical],
                ["Reserved", data.inventory.reserved],
                ["Available", data.inventory.available],
              ] as const
            ).map(([label, value]) => (
              <div key={label}>
                <p className="text-xs text-fg-muted">{t(label)}</p>
                <p className="mt-2 font-semibold">
                  {formatQuantity(value)} {data.inventory.unit}
                </p>
              </div>
            ))}
          </div>
          <p className="mt-5 text-xs text-fg-muted">
            {formatDateTime(data.observation.observed_at)}
          </p>
        </article>
        <article className="rounded-xl border border-border-default bg-surface p-6">
          <h3 className="font-semibold text-fg-strong">{t("Evidence")}</h3>
          <div className="mt-4 flex flex-wrap gap-2">
            {data.links.map((link) => (
              <button
                key={`${link.kind}:${link.id}`}
                className="br-btn"
                onClick={() => setTarget(link)}
              >
                {link.label}
              </button>
            ))}
            {!data.links.length && (
              <p className="text-sm text-fg-muted">{t("No document evidence")}</p>
            )}
          </div>
        </article>
        <article className="rounded-xl border border-border-default bg-surface p-6">
          <h3 className="mb-4 font-semibold text-fg-strong">{t("Business history")}</h3>
          {!historyRead.data ? (
            <ReadState
              loading={historyRead.loading}
              error={historyRead.error}
              retry={historyRead.refresh}
            />
          ) : (
            <>
              <ul className="space-y-3">
                {historyRead.data.history.items.map((event) => (
                  <li key={event.id} className="flex flex-wrap justify-between gap-2 text-sm">
                    <button
                      className="text-accent"
                      onClick={() => setTarget({ kind: event.subject_type, id: event.subject_id })}
                    >
                      {event.type}
                    </button>
                    <time className="text-fg-muted">{formatDateTime(event.occurred_at)}</time>
                  </li>
                ))}
              </ul>
              {historyRead.data.history.has_more && (
                <button
                  className="br-btn mt-4"
                  onClick={() => setCursor(historyRead.data!.history.next_cursor!)}
                >
                  {t("Older events")}
                </button>
              )}
              {cursor && (
                <button className="br-btn mt-4" onClick={() => setCursor("")}>
                  {t("Latest events")}
                </button>
              )}
            </>
          )}
        </article>
        {action && (
          <ActionCard
            tenant={tenant}
            commitment={id}
            party={detail.party_id || ""}
            tool={action}
            close={() => setAction(null)}
            prepared={(proposal) => {
              setAction(null);
              navigate({ proposal });
            }}
            settled={() => window.dispatchEvent(new Event("reality:delivery-settled"))}
          />
        )}
        {target && <Inspector tenant={tenant} target={target} close={() => setTarget(null)} />}
      </section>
    </div>
  );
}

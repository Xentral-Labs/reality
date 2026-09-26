import { useState, type FormEvent } from "react";
import { APIError, api, type ResolvedPrice } from "../api";
import { formatDateTime, formatMoney, t } from "../localization";
import { useActionDiscovery } from "./ActionLauncher";
import { reasonText } from "./guidanceActions";
import { RecordReference } from "./RecordReference";

// How `resolve_price` found the price list (services/core.py).
const sourceLabels: Record<string, string> = {
  party: "Price list assigned to the business partner",
  group: "Price list of the business partner's group",
  default: "Default price list",
};

/**
 * Spec 279 FR-013: choose a business partner and an item and read the price through
 * the existing live price service. Reality selects the agreed price; it computes none.
 */
export function PriceResolution({ tenant }: { tenant: string }) {
  const catalog = useActionDiscovery()?.data?.resolution_guidance;
  const [party, setParty] = useState("");
  const [item, setItem] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [direction, setDirection] = useState<"sales" | "purchase">("sales");
  const [currency, setCurrency] = useState("EUR");
  const [unit, setUnit] = useState("");
  const [state, setState] = useState<
    | { kind: "idle" | "loading" }
    | { kind: "found"; price: ResolvedPrice }
    | { kind: "none" }
    | { kind: "error"; message: string }
  >({ kind: "idle" });
  const submit = (event: FormEvent) => {
    event.preventDefault();
    setState({ kind: "loading" });
    api
      .resolvePrice(tenant, { party_id: party, item_id: item, quantity, direction, currency, unit })
      .then((price) => setState({ kind: "found", price }))
      .catch((error) =>
        setState(
          error instanceof APIError && error.status === 404
            ? { kind: "none" }
            : { kind: "error", message: String(error.message || error) },
        ),
      );
  };
  const none = reasonText(catalog, "no_applicable_price");
  return (
    <form className="space-y-3" data-price-resolution onSubmit={submit}>
      <div className="grid gap-3 sm:grid-cols-2">
        <RecordReference
          tenant={tenant}
          kind="parties"
          label="Business partner"
          value={party}
          change={setParty}
        />
        <RecordReference tenant={tenant} kind="items" label="Item" value={item} change={setItem} />
      </div>
      <div className="grid gap-3 sm:grid-cols-4">
        <label className="block text-sm">
          {t("Quantity")}
          <input
            className="br-control mt-2 w-full"
            required
            inputMode="decimal"
            value={quantity}
            onChange={(event) => setQuantity(event.target.value)}
          />
        </label>
        <label className="block text-sm">
          {t("Unit")}
          <input
            className="br-control mt-2 w-full"
            required
            value={unit}
            onChange={(event) => setUnit(event.target.value)}
          />
        </label>
        <label className="block text-sm">
          {t("Currency")}
          <input
            className="br-control mt-2 w-full"
            required
            maxLength={3}
            value={currency}
            onChange={(event) => setCurrency(event.target.value.toUpperCase())}
          />
        </label>
        <label className="block text-sm">
          {t("Direction")}
          <select
            className="br-control mt-2 w-full"
            value={direction}
            onChange={(event) => setDirection(event.target.value as "sales" | "purchase")}
          >
            <option value="sales">{t("Sales")}</option>
            <option value="purchase">{t("Purchasing")}</option>
          </select>
        </label>
      </div>
      <button
        type="submit"
        className="br-btn br-btn-primary"
        disabled={!party || !item || state.kind === "loading"}
      >
        {t("Determine price")}
      </button>
      {state.kind === "found" && (
        <dl className="grid gap-3 sm:grid-cols-3" role="status" data-price-result>
          <div>
            <dt className="text-xs text-fg-muted">{t("Unit price")}</dt>
            <dd className="font-medium">
              {formatMoney(state.price.unit_price, state.price.currency)} / {state.price.unit}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-fg-muted">{t("Source")}</dt>
            <dd>
              {sourceLabels[state.price.source] ? (
                t(sourceLabels[state.price.source])
              ) : (
                <span data-localization="original">{state.price.source}</span>
              )}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-fg-muted">{t("Evaluated at")}</dt>
            <dd>{formatDateTime(state.price.evaluated_at)}</dd>
          </div>
        </dl>
      )}
      {state.kind === "none" && (
        <div role="status" data-resolution-guidance="no_applicable_price" className="text-sm">
          <div className="font-medium text-fg-strong">{none.label}</div>
          <div className="mt-1 text-fg-muted">{none.explanation}</div>
        </div>
      )}
      {state.kind === "error" && (
        <p role="alert" className="text-sm">
          {state.message}
        </p>
      )}
    </form>
  );
}

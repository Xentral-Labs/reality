import { useState } from "react";
import { deliveryActions } from "../api";
import { t } from "../localization";
import { ReadLine } from "./ReadState";
import { useRead } from "./useCompanyContext";
export function ReferenceChoices({
  tenant,
  commitment,
  family,
  label,
  value,
  change,
  disabled,
}: {
  tenant: string;
  commitment: string;
  family: string;
  label: string;
  value: string;
  change: (value: string) => void;
  disabled: boolean;
}) {
  const [query, setQuery] = useState("");
  const { data, error, loading } = useRead(
    () => deliveryActions.references(tenant, commitment, family, query),
    [tenant, commitment, family, query],
  );
  return (
    <fieldset className="space-y-2" disabled={disabled}>
      <legend className="br-label">{t(label)}</legend>
      <input
        className="br-control w-full"
        aria-label={`${t("Search")} · ${t(label)}`}
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />
      <select
        className="br-control w-full"
        aria-label={t(label)}
        value={value}
        onChange={(event) => change(event.target.value)}
      >
        <option value="">{t("Not selected")}</option>
        {value && !data?.items.some((row) => row.id === value) && (
          <option value={value}>{value}</option>
        )}
        {data?.items.map((row) => (
          <option key={row.id} value={row.id}>
            {row.label}
          </option>
        ))}
      </select>
      {loading && <ReadLine />}
      {error && <p role="alert">{error}</p>}
      {data?.has_more && (
        <p className="text-xs text-fg-muted">{t("Refine your search to see more matches.")}</p>
      )}
    </fieldset>
  );
}

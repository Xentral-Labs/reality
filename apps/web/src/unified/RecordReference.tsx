import { useState } from "react";
import { api } from "../api";
import { t } from "../localization";
import { ReadLine } from "./ReadState";
import { useRead } from "./useCompanyContext";

/** Search one tenant-scoped suggestion kind and choose a record by its opaque ID. */
export function RecordReference({
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

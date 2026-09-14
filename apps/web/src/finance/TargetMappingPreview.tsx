import { readSelection, selectionUrl } from "../unified/routing";
import { SourceResolutionView, resolutionLabels, type SourceResolution } from "./SourceMappings";
import { useEffect, useState } from "react";
import { t } from "../localization";
import { TargetPicker, targetCall } from "./TargetMappings";

type Destination = {
  status: string;
  mapping?: { id: string; revision: number };
  external_account?: { code: string; name: string };
  external_tax_code?: { code: string; name: string };
};
const statuses: Record<string, string> = {
  stale_assignment: "Assignment belongs to an earlier evidence version",
  resolved: "Mapping resolved",
  missing_case: "A declared case is required",
  missing_group: "A coding group is required",
  missing_mapping: "No matching target rule",
  ambiguous_mapping: "Multiple target rules match",
  blocked_target: "Accounting target is blocked",
  blocked_destination: "External destination is blocked",
  blocked_local_account: "Operational account is blocked",
  case_conflict: "Source and internal case conflict",
  group_conflict: "Source and internal group conflict",
};
function Result({ row }: { row: Destination }) {
  const field = row.status.startsWith("case_")
    ? "Case code"
    : row.status.startsWith("group_")
      ? "Coding group"
      : null;
  const issue = field ? row.status.slice(row.status.indexOf("_") + 1) : "";
  return (
    <div className="space-y-1">
      <p>
        {statuses[row.status]
          ? t(statuses[row.status])
          : field
            ? `${t(field)}: ${t(issue === "blocked" ? "Internal reference blocked" : resolutionLabels[issue] || "Classification needs review")}`
            : t("Classification needs review")}
      </p>
      {row.external_account && (
        <p>
          {t("External account")}:{" "}
          <span data-original>
            {row.external_account.code} · {row.external_account.name}
          </span>
        </p>
      )}
      {row.external_tax_code && (
        <p>
          {t("Tax code")}:{" "}
          <span data-original>
            {row.external_tax_code.code} · {row.external_tax_code.name}
          </span>
        </p>
      )}
      {row.mapping && (
        <p>
          {t("Mapping revision")}: {row.mapping.revision} ·{" "}
          <span data-original>{row.mapping.id}</span>
        </p>
      )}
    </div>
  );
}
export function TargetMappingPreview({
  tenantId,
  documentId,
  explain,
}: {
  tenantId: string;
  documentId: string;
  explain: (id: string) => void;
}) {
  const base = `/api/tenants/${encodeURIComponent(tenantId)}/finance`;
  const [target, setTarget] = useState("");
  const [offset, setOffset] = useState(0);
  const [reload, setReload] = useState(0);
  const [error, setError] = useState("");
  const [data, setData] = useState<{
    total: number;
    operational_legs_total: number;
    items: (Destination & {
      received: {
        label: string;
        source_resolution?: SourceResolution;
        document_line_id: string | null;
        current?: {
          revision: number;
          reason: string;
          references: { case: { name: string } | null; group: { name: string } | null };
        } | null;
        currency: string;
        amounts: Record<string, string | null>;
      };
    })[];
    operational_legs: (Destination & {
      entry_id: string;
      account: { code: string; name: string };
    })[];
  } | null>(null);
  useEffect(() => {
    let current = true;
    setData(null);
    setError("");
    if (target)
      targetCall<NonNullable<typeof data>>(
        `${base}/target-mappings/preview?${new URLSearchParams({ target_id: target, document_id: documentId, offset: String(offset), limit: "50" })}`,
      )
        .then((r) => {
          if (current) setData(r);
        })
        .catch((e) => {
          if (current) setError(e.message);
        });
    return () => {
      current = false;
    };
  }, [base, target, documentId, offset, reload]);
  return (
    <section
      aria-label={t("Mapping preview")}
      className="my-4 space-y-3 border-t border-border-default pt-4"
    >
      <h3 className="font-semibold">{t("Mapping preview")}</h3>
      <p>{t("Shows external destinations, not export completeness or external posting.")}</p>
      <a
        className="inline-block text-accent"
        href={selectionUrl({
          ...readSelection(new URL(window.location.href)),
          tenant: tenantId,
          route: "finance",
          financeView: "settings",
          financeSettings: "accounts",
        })}
        onClick={() => {
          sessionStorage.setItem(`finance-account-area:${tenantId}`, "external");
          if (target) sessionStorage.setItem(`finance-account-target:${tenantId}`, target);
        }}
      >
        {t("Configure accounts")}
      </a>
      <TargetPicker
        label={t("Accounting target")}
        url={`${base}/targets`}
        value={target}
        onChange={(id) => {
          setTarget(id);
          setOffset(0);
        }}
        optional
        allowBlocked
      />
      {error && (
        <p role="alert">
          {error}{" "}
          <button className="br-btn" onClick={() => setReload((x) => x + 1)}>
            {t("Retry")}
          </button>
        </p>
      )}
      {target && !error && !data && <p role="status">{t("Loading")}</p>}
      {data && (
        <>
          <h4>{t("Received components")}</h4>
          {data.items.map((row, index) => (
            <article key={index} className="rounded-lg border border-border-default p-3">
              <p data-original>{row.received.label}</p>
              <div className="flex flex-wrap gap-3">
                {Object.entries(row.received.amounts).map(([key, amount]) => (
                  <p key={key}>
                    {t(
                      (
                        {
                          net: "Net",
                          tax: "Tax",
                          gross: "Gross",
                          base: "Other received basis",
                        } as Record<string, string>
                      )[key],
                    )}
                    : {amount === null ? t("Unknown") : `${amount} ${row.received.currency}`}
                  </p>
                ))}
              </div>
              <SourceResolutionView value={row.received.source_resolution} tenantId={tenantId} />
              {row.received.current && (
                <p>
                  {t("Internal assignment")} · {t("Revision")} {row.received.current.revision}:{" "}
                  <span data-original>
                    {[
                      row.received.current.references.case?.name,
                      row.received.current.references.group?.name,
                      row.received.current.reason,
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  </span>
                </p>
              )}
              <Result row={row} />
              <button
                className="finance-row-button"
                onClick={() => explain(row.received.document_line_id || documentId)}
              >
                {t("Evidence")}
              </button>
            </article>
          ))}
          <h4>{t("Gross operational account references")}</h4>
          {data.operational_legs.map((row) => (
            <article key={row.entry_id} className="rounded-lg border border-border-default p-3">
              <p data-original>
                {row.account.code} · {row.account.name}
              </p>
              <Result row={row} />
            </article>
          ))}
          <div className="flex gap-2">
            <button
              className="br-btn"
              disabled={!offset}
              onClick={() => setOffset((x) => Math.max(0, x - 50))}
            >
              {t("Previous")}
            </button>
            <button
              className="br-btn"
              disabled={offset + 50 >= Math.max(data.total, data.operational_legs_total)}
              onClick={() => setOffset((x) => x + 50)}
            >
              {t("Next")}
            </button>
            <button className="br-btn" onClick={() => setReload((x) => x + 1)}>
              {t("Refresh")}
            </button>
          </div>
        </>
      )}
    </section>
  );
}

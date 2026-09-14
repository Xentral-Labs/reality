import { useState } from "react";
import { SettingsDialog } from "./SettingsDialog";
import { t } from "../localization";
import { ReadState } from "../unified/ReadState";
import { useRead } from "../unified/useCompanyContext";

type Leg = {
  side: "debit" | "credit";
  role: string;
  role_label: string;
  account: { id: string; code: string; name: string; revision: number } | null;
  status: "configured" | "missing" | "blocked" | "wrong_role";
};
type Matrix = {
  revision: number;
  operations: {
    transaction: string;
    label: string;
    basis: string;
    control_policy: string;
    legs: Leg[];
  }[];
};
const statusLabels = {
  configured: "Configured",
  missing: "Missing default",
  blocked: "Blocked",
  wrong_role: "Incompatible account role",
};
const policyLabels: Record<string, string> = {
  configured_default: "Configured default accounts",
  original_when_linked: "Original control account when linked",
  original_required: "Original invoice account required",
};
function MatrixBody({
  tenantId,
  revision,
  configure,
  canManage,
}: {
  tenantId: string;
  revision: number;
  configure: (role?: string) => void;
  canManage: boolean;
}) {
  const read = useRead<Matrix>(async () => {
    const response = await fetch(`/api/tenants/${encodeURIComponent(tenantId)}/finance/matrix`, {
      credentials: "include",
    });
    const value = await response.json();
    if (!response.ok)
      throw new Error(typeof value.detail === "string" ? value.detail : t("Request failed"));
    return value;
  }, [tenantId, revision]);
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  return (
    <div className="space-y-4">
      <p>
        {t(
          "These defaults apply to new transactions. Linked payments and corrections can retain the accounts of the original invoice.",
        )}
      </p>
      <p className="text-sm text-fg-muted">
        {t("Reversals retain original accounts and reverse the original group.")}
      </p>
      <p className="text-sm text-fg-muted">
        {t("Orders, reservations, stock movements and allocations do not add postings here.")}
      </p>
      <div className="flex flex-wrap gap-2">
        <button className="br-btn" type="button" onClick={() => configure()}>
          {t("Back to accounts")}
        </button>
        <button className="br-btn" type="button" disabled={read.loading} onClick={read.refresh}>
          {t("Refresh")}
        </button>
      </div>
      <div className="grid gap-3 lg:grid-cols-2">
        {read.data.operations.map((row) => (
          <article
            key={row.transaction}
            aria-label={t(row.label)}
            className="min-w-0 space-y-3 rounded-xl border border-border-default p-4"
          >
            <h3 className="font-semibold">{t(row.label)}</h3>
            <p className="text-sm">
              {t("Amount basis")}: {t(row.basis)}
            </p>
            <dl className="space-y-3 text-sm">
              {row.legs.map((leg) => (
                <div key={leg.side}>
                  <dt className="font-medium">
                    {t(leg.side === "debit" ? "Debit" : "Credit")} · {t(leg.role_label)}
                  </dt>
                  <dd className="break-words">
                    {leg.account && (
                      <span data-original="true">
                        {leg.account.code} · {leg.account.name} ·{" "}
                      </span>
                    )}
                    {t(statusLabels[leg.status])}
                    {canManage && (
                      <button
                        type="button"
                        className="finance-row-button ml-2"
                        onClick={() => configure(leg.role)}
                      >
                        {t("Change default")}
                      </button>
                    )}
                  </dd>
                </div>
              ))}
            </dl>
            <p className="text-sm text-fg-muted">{t(policyLabels[row.control_policy])}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
export function TransactionMatrix(props: {
  tenantId: string;
  revision: number;
  configure: (role?: string) => void;
  canManage: boolean;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button type="button" className="br-btn" onClick={() => setOpen(true)}>
        {t("View account usage")}
      </button>
      {open && (
        <SettingsDialog
          title={t("Accounts for business transactions")}
          description={t(
            "See which operational accounts each transaction uses. Change a role default when future transactions should use a different account.",
          )}
          close={() => setOpen(false)}
        >
          <MatrixBody
            {...props}
            configure={(role) => {
              setOpen(false);
              props.configure(role);
            }}
          />
        </SettingsDialog>
      )}
    </>
  );
}

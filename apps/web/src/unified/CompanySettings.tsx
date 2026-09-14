import { PageActionBar } from "./PageActionBar";
import { useState } from "react";
import { api, type Bootstrap, type Tenant } from "../api";
import { t } from "../localization";
import { CompanySetup } from "../components/CompanySetup";
import { CompanyDangerZone } from "./CompanyDangerZone";

export function CreateCompany({
  openCompany,
  close,
}: {
  openCompany: (data: Bootstrap, id: string) => void;
  close?: () => void;
}) {
  return (
    <CompanySetup
      first={!close}
      close={close}
      created={async (result) => {
        const data = await api.bootstrap();
        if (!data.tenants.some((row) => row.id === result.tenant_id))
          throw new Error("Company access unavailable");
        openCompany(data, result.tenant_id);
      }}
    />
  );
}

const companyStyles = {
  active: "border-accent bg-accent-soft",
  inactive: "border-border-default bg-surface",
  current: "rounded-full bg-surface px-3 py-1 text-sm font-medium text-accent",
  switch: "text-sm text-accent",
};
export function CompanySettings({
  company,
  companies,
  switchCompany,
  manageCompany,
  openCompany,
}: {
  company: Tenant;
  companies: Tenant[];
  switchCompany: (id: string) => void;
  manageCompany: (id: string, view: "access" | "agents" | "ai") => void;
  openCompany: (data: Bootstrap, id: string, options?: { announce?: boolean }) => void;
}) {
  const [create, setCreate] = useState(false);
  return (
    <div className="space-y-8">
      <section aria-label={t("Companies")} className="space-y-4">
        <PageActionBar
          actions={[{ key: "create", label: "New company", onClick: () => setCreate(true) }]}
        />
        <ul className="space-y-3">
          {companies.map((row) => {
            const current = row.id === company.id;
            const rowStyle = current ? companyStyles.active : companyStyles.inactive;
            const badgeStyle = current ? companyStyles.current : companyStyles.switch;
            return (
              <li
                key={row.id}
                data-company-card={row.id}
                className={`overflow-hidden rounded-xl border ${rowStyle}`}
              >
                <button
                  type="button"
                  aria-current={current ? "true" : undefined}
                  onClick={() => {
                    if (!current) {
                      setCreate(false);
                      switchCompany(row.id);
                    }
                  }}
                  className={`flex w-full flex-wrap items-center justify-between gap-4 p-4 text-left hover:bg-surface-muted`}
                >
                  <span className="min-w-0 space-y-1">
                    <span className="block break-words font-semibold" data-localization="original">
                      {row.name}
                    </span>
                    <span className="flex flex-wrap gap-2 py-1 text-xs font-medium">
                      <span className="rounded-full border border-border-default bg-surface px-2.5 py-1">
                        {t(
                          row.company_kind === "demo"
                            ? "Demo company"
                            : row.sandbox_run_id
                              ? "Sandbox"
                              : "Company",
                        )}
                      </span>
                      {row.demo_data_state && (
                        <span className="rounded-full border border-border-default bg-surface px-2.5 py-1">
                          {t("Live simulation")}:{" "}
                          {t(
                            {
                              running: "Running",
                              paused: "Paused",
                              stopped: "Stopped",
                              disconnected: "Disconnected",
                            }[row.demo_data_state],
                          )}
                        </span>
                      )}
                    </span>
                    <span
                      className="block break-all font-mono text-xs text-fg-muted"
                      data-localization="original"
                    >
                      {row.id}
                    </span>
                    <span className="block text-sm text-fg-muted">
                      {t("Your role")}: {t(row.role === "owner" ? "Owner" : "Member")}
                    </span>
                  </span>
                  <span className={badgeStyle}>
                    {t(current ? "Current company" : "Switch company")}
                  </span>
                </button>
                <div
                  data-company-actions={row.id}
                  className="border-t border-border-default bg-surface px-4 py-4"
                >
                  {row.role === "owner" ? (
                    <div className="space-y-3">
                      <p className="text-sm text-fg-muted">
                        {t("You own this company and manage its access.")}
                      </p>
                      <div className="flex flex-wrap gap-2">
                        <button className="br-btn" onClick={() => manageCompany(row.id, "access")}>
                          {t("Manage users")}
                        </button>
                        <button className="br-btn" onClick={() => manageCompany(row.id, "agents")}>
                          {t("Agents & API tokens")}
                        </button>
                        <button className="br-btn" onClick={() => manageCompany(row.id, "ai")}>
                          {t("AI configuration")}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-fg-muted">
                      {t("You are a member. Only company owners manage users and agent tokens.")}
                    </p>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      </section>
      {create && (
        <CreateCompany
          close={() => setCreate(false)}
          openCompany={(data, id) => {
            setCreate(false);
            openCompany(data, id);
          }}
        />
      )}
      <CompanyDangerZone company={company} companies={companies} openCompany={openCompany} />
    </div>
  );
}

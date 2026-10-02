import type { Tenant } from "../api";
import { t } from "../localization";

export function hasPlatformCompanyAccess(company: Tenant, platformAdmin: boolean): boolean {
  return (
    platformAdmin &&
    !company.role &&
    company.purpose !== "playground" &&
    !company.sandbox_run_id &&
    company.company_kind !== "sandbox"
  );
}

export function companyAccessLabel(company: Tenant, platformAdmin: boolean): string {
  if (company.role === "owner") return t("Owner");
  if (company.role === "member") return t("Member");
  if (hasPlatformCompanyAccess(company, platformAdmin)) return t("Platform admin access");
  return t("No company membership");
}

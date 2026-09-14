import { useState } from "react";
import { TargetMappings } from "./TargetMappings";
import { AccountSettings } from "./AccountSettings";
import { ReferenceSettings } from "./ReferenceSettings";
import { SourceMappings } from "./SourceMappings";
import { t } from "../localization";
import type { Selection } from "../unified/routing";
const areaStyles = {
  active: "bg-accent-soft text-accent",
  inactive: "text-fg-muted hover:bg-surface-muted hover:text-fg",
};
const areas = [
  ["accounts", "Accounts & account mapping"],
  ["cost-centers", "Cost centers"],
  ["classifications", "Case codes & coding groups"],
  ["source-mappings", "Source code mappings"],
] as const;
export function FinanceSettings({
  tenantId,
  canManage,
  area,
  selectArea,
}: {
  tenantId: string;
  canManage: boolean;
  area: Selection["financeSettings"];
  selectArea: (area: Selection["financeSettings"]) => void;
}) {
  const storage = `finance-account-area:${tenantId}`;
  const [external, changeExternal] = useState(() => sessionStorage.getItem(storage) === "external");
  const setExternal = (value: boolean) => {
    sessionStorage.setItem(storage, value ? "external" : "operational");
    changeExternal(value);
  };
  return (
    <section
      aria-label={t("Finance settings")}
      className="finance-settings grid min-w-0 gap-6 md:grid-cols-[220px_minmax(0,1fr)]"
    >
      <nav aria-label={t("Finance settings areas")} className="hidden self-start md:block">
        {areas.map(([key, label]) => (
          <button
            key={key}
            aria-current={area === key ? "page" : undefined}
            onClick={() => selectArea(key)}
            className={`mb-1 w-full rounded-lg px-3 py-3 text-left text-sm font-medium ${area === key ? areaStyles.active : areaStyles.inactive}`}
          >
            {t(label)}
          </button>
        ))}
      </nav>
      <label className="block md:hidden">
        {t("Settings area")}
        <select
          aria-label={t("Settings area")}
          className="br-control mt-2 w-full"
          value={area}
          onChange={(event) => selectArea(event.target.value as Selection["financeSettings"])}
        >
          {areas.map(([key, label]) => (
            <option key={key} value={key}>
              {t(label)}
            </option>
          ))}
        </select>
      </label>
      <div className="min-w-0">
        {area === "accounts" && (
          <div className="space-y-4">
            <nav aria-label={t("Account settings areas")} className="flex flex-wrap gap-2">
              <button
                className={`br-btn ${!external ? areaStyles.active : areaStyles.inactive}`}
                aria-current={!external ? "page" : undefined}
                onClick={() => setExternal(false)}
              >
                {t("Operational accounts")}
              </button>
              <button
                className={`br-btn ${external ? areaStyles.active : areaStyles.inactive}`}
                aria-current={external ? "page" : undefined}
                onClick={() => setExternal(true)}
              >
                {t("External accounting")}
              </button>
            </nav>
            {external ? (
              <TargetMappings key={tenantId} tenantId={tenantId} canManage={canManage} />
            ) : (
              <AccountSettings key={tenantId} embedded tenantId={tenantId} canManage={canManage} />
            )}
          </div>
        )}
        {(area === "cost-centers" || area === "classifications") && (
          <ReferenceSettings
            key={`${tenantId}:${area}`}
            embedded
            referenceArea={area}
            tenantId={tenantId}
            canManage={canManage}
          />
        )}
        {area === "source-mappings" && (
          <SourceMappings embedded tenantId={tenantId} canManage={canManage} />
        )}
      </div>
    </section>
  );
}

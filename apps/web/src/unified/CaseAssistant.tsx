import { useState } from "react";
import { ChatPage } from "./ChatPage";
import { t } from "../localization";
import type { Selection } from "./routing";
export function CaseAssistant({
  tenant,
  id,
  close,
  navigate,
}: {
  tenant: string;
  id: string;
  close: () => void;
  navigate: (value: Partial<Selection>) => void;
}) {
  const [session, setSession] = useState("");
  const assistNavigate = (changes: Partial<Selection>) => {
    if (changes.session !== undefined) setSession(changes.session);
    if (changes.route && changes.route !== "copilot") navigate(changes);
    else if (changes.proposal) navigate({ proposal: changes.proposal });
  };
  const selection: Selection = {
    tenant,
    importProposal: "",
    commitment: id,
    route: "copilot",
    settingsView: "personal",
    balanceSide: "customer",
    creditOnly: false,
    partyId: "",
    factSubjectType: "",
    factSubject: "",
    factSource: "",
    factTarget: "fact",
    tableSize: 50,
    tableSort: "",
    tableDirection: "asc",
    tableScope: "",
    ordersView: "deliveries",
    deliveryType: "customer_delivery",
    deliveryStatus: "open",
    order: "",
    family: "customer",
    record: "",
    active: false,
    dataView: "systems",
    sourceSystem: "",
    sourceRecord: "",
    evidenceType: "",
    financeSettings: "accounts",
    financeView: "open-items",
    flow: "receivable",
    financeStatus: "outstanding",
    direction: "",
    account: "",
    warehouseView: "stock",
    item: "",
    entry: "",
    state: "",
    severity: "",
    exception: "",
    proposal: "",
    session,
    page: 1,
    q: "",
  };
  return (
    <aside className="min-w-0 rounded-xl border border-border-default bg-surface p-4">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-semibold">{t("Ask Reality")}</h2>
        <button className="br-btn" onClick={close}>
          {t("Close")}
        </button>
      </div>
      <ChatPage selection={selection} navigate={assistNavigate} compact />
    </aside>
  );
}

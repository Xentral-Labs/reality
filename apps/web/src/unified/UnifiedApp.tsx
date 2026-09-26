import { CompanyChatPage } from "./CompanyChatPage";
import { EntryProgress } from "../components/EntryProgress";
import { TrialEntry, TrialProvider, TrialPrompt } from "./FreePlayground";
import { ActionDiscoveryProvider } from "./ActionLauncher";
import { CommitmentsPage } from "./CommitmentsPage";
import { DemoDataIntegration } from "../components/DemoDataIntegration";
import { RegisterHeader } from "./RegisterWorkbench";
import { CreateCompany } from "./CompanySettings";
import { TableProvider } from "./TableContext";
import { RealityInspectorPage } from "./RealityInspectorPage";
import { FactsPage } from "./FactsPage";
import { OrdersPage } from "./OrdersPage";
import { SettingsPage } from "./SettingsPage";
import { DataSourcesPage } from "./DataSourcesPage";
import { FinancePage } from "./FinancePage";
import { WarehousePage } from "./WarehousePage";
import { AttentionPage } from "./AttentionPage";
import { AnalyticsPage } from "./AnalyticsPage";
import { MasterDataPage } from "./MasterDataPage";
import { useEffect, useRef, useState } from "react";
import { ActionCard } from "./ActionCard";
import { ProposalReviewCard } from "./ProposalReviewCard";
import { proposalReviewLocation } from "./proposalRouting";
import type { DeliveryAction } from "./ActionLauncher";
import { DecisionsPage } from "./DecisionsPage";
import type { AuthUser, Bootstrap } from "../api";
import { t } from "../localization";
import { DeliveryWorkPage } from "./DeliveryWorkPage";
import { Shell } from "./Shell";
import { HomePage } from "./HomePage";
import { StorylinePage } from "./StorylinePage";
import { ReadState } from "./ReadState";
import { useCompanyContext } from "./useCompanyContext";

const chatContentClass = "flex min-h-0 flex-1 flex-col";

export default function UnifiedApp({
  user,
  updateUser,
}: {
  user: AuthUser;
  updateUser: (user: AuthUser) => void;
}) {
  const [actionTarget, setActionTarget] = useState<{
    postingGroup?: string;
    invoice?: string;
    creditNote?: string;
    commitment?: string;
    reservation?: string;
    movement?: string;
    direction?: string;
    order?: string;
    shipmentInput?: {
      counterparty_id: string;
      movements: Record<string, string>[];
    };
  }>({});
  const [action, setAction] = useState<DeliveryAction | null>(null);
  const [createdCompany, setCreatedCompany] = useState<string | null>(null);
  const context = useCompanyContext();
  const { bootstrap, error, selection, company, navigate, switchCompany } = context;
  const entryWasHome = useRef(
    !new URL(location.href).searchParams.has("tenant") && selection.route === "home",
  );
  // The notice about a company someone just set up sits in the page flow, aligned with the
  // content, and leaves on its own: after a short while or as soon as the person moves on.
  useEffect(() => {
    if (!createdCompany) return;
    const timer = window.setTimeout(() => setCreatedCompany(null), 8000);
    return () => window.clearTimeout(timer);
  }, [createdCompany]);
  const route = selection.route;
  const routeSeen = useRef(route);
  useEffect(() => {
    if (routeSeen.current !== route) setCreatedCompany(null);
    routeSeen.current = route;
  }, [route]);
  // A company someone set up is announced; a practice company a storyline opened is not,
  // the story itself says where the person is.
  const openCompany = (
    data: Bootstrap,
    id: string,
    options?: { announce?: boolean; home?: boolean },
  ) => {
    setAction(null);
    setActionTarget({});
    context.openCompany(data, id, options?.home ?? false);
    setCreatedCompany(options?.announce === false ? null : id);
  };
  if (!bootstrap)
    return error ? (
      <ReadState error={error} retry={() => location.reload()} />
    ) : (
      <EntryProgress title="Loading your workspace" />
    );
  if (!company)
    return (
      <TrialEntry
        autoEnter={entryWasHome.current}
        open={(data, id) => context.openCompany(data, id, true)}
      >
        {bootstrap.tenants.length === 0 ? (
          <CreateCompany openCompany={openCompany} />
        ) : (
          <div className="mx-auto max-w-xl p-8">
            <h1 className="text-2xl">
              {t(bootstrap.tenants.length ? "Company unavailable" : "Create your first company")}
            </h1>
            <p className="my-4">
              {t(
                bootstrap.tenants.length
                  ? "Choose an authorized company or create another."
                  : "Your company brings orders, stock and finance together.",
              )}
            </p>
            <div className="flex flex-wrap gap-3">
              {bootstrap.tenants.map((row) => (
                <button key={row.id} className="br-btn" onClick={() => switchCompany(row.id)}>
                  {row.name}
                </button>
              ))}
            </div>
            <div className="mt-6">
              <CreateCompany openCompany={openCompany} />
            </div>
          </div>
        )}
      </TrialEntry>
    );
  return (
    <TrialEntry
      autoEnter={entryWasHome.current}
      open={(data, id) => context.openCompany(data, id, true)}
    >
      <TrialProvider
        key={`${user.id}:${company.id}`}
        user={user.id}
        tenant={company.id}
        enabled={company.purpose === "playground"}
      >
        <ActionDiscoveryProvider
          key={company.id}
          tenant={company.id}
          user={user.id}
          companies={bootstrap.tenants}
          switchCompany={(id) => {
            setAction(null);
            setActionTarget({});
            switchCompany(id);
          }}
          companyName={company.name}
          selection={selection}
          owner={company.role === "owner"}
          demo={!!(company.company_kind === "demo" || company.demo_data_state)}
          navigate={navigate}
          open={(tool, target) => {
            navigate({ proposal: "" });
            setActionTarget(target || {});
            setAction(tool);
          }}
        >
          <Shell
            user={user}
            company={company}
            companies={bootstrap.tenants}
            selection={selection}
            navigate={navigate}
            switchCompany={(id) => {
              setAction(null);
              setActionTarget({});
              switchCompany(id);
            }}
            openAction={(tool) => {
              setActionTarget({});
              setAction(tool);
            }}
          >
            {createdCompany === company.id && (
              <div
                role="status"
                data-company-created={company.id}
                className="mb-4 flex items-center justify-between gap-3 rounded-xl border border-accent bg-accent-soft px-4 py-3 text-sm"
              >
                <p>
                  {t("Company created")}: <span data-localization="original">{company.name}</span>
                </p>
                <button className="br-btn" onClick={() => setCreatedCompany(null)}>
                  {t("Close")}
                </button>
              </div>
            )}
            <TrialPrompt />
            <TableProvider user={user.id} selection={selection} navigate={navigate}>
              <div
                key={`${user.id}:${company.id}`}
                className={selection.route === "chat" ? chatContentClass : undefined}
              >
                {selection.route === "inspector" ? (
                  <RealityInspectorPage
                    selection={selection}
                    navigate={navigate}
                    owner={company.role === "owner" || user.is_platform_admin === true}
                    companyName={company.name}
                    user={user.id}
                    openAction={(tool) => {
                      setActionTarget({});
                      setAction(tool);
                    }}
                  />
                ) : selection.route === "facts" ? (
                  <FactsPage selection={selection} navigate={navigate} />
                ) : selection.route === "orders-deliveries" &&
                  selection.ordersView === "commitments" ? (
                  <CommitmentsPage
                    selection={selection}
                    navigate={navigate}
                    receive={(id) => {
                      setActionTarget({ commitment: id });
                      setAction("receipt");
                    }}
                  />
                ) : selection.route === "orders-deliveries" ? (
                  <OrdersPage
                    prepareInvoice={(order) => {
                      setActionTarget({ order });
                      setAction("sales_invoice_record");
                    }}
                    prepareShipment={(shipmentInput) => {
                      setActionTarget({ shipmentInput });
                      setAction("shipment_dispatch");
                    }}
                    create={(direction) => {
                      setActionTarget({ direction });
                      setAction("order_create");
                    }}
                    selection={selection}
                    navigate={navigate}
                    receive={(id) => {
                      setActionTarget({ commitment: id });
                      setAction("receipt");
                    }}
                  />
                ) : selection.route === "settings" ? (
                  <SettingsPage
                    user={user}
                    updateUser={updateUser}
                    openCompany={openCompany}
                    companies={bootstrap.tenants}
                    switchCompany={(id) => {
                      setAction(null);
                      setActionTarget({});
                      switchCompany(id);
                    }}
                    company={company}
                    selection={selection}
                    navigate={(changes) => {
                      if (changes.tenant && changes.tenant !== company.id) {
                        setAction(null);
                        setActionTarget({});
                      }
                      navigate(changes);
                    }}
                  />
                ) : selection.route === "home" ? (
                  <HomePage
                    user={user.id}
                    tenant={company.id}
                    companyName={company.name}
                    owner={company.role === "owner"}
                    navigate={navigate}
                  />
                ) : selection.route === "analytics" ? (
                  <AnalyticsPage selection={selection} navigate={navigate} />
                ) : selection.route === "master-data" ? (
                  <MasterDataPage selection={selection} navigate={navigate} />
                ) : selection.route === "demo-data" ? (
                  <>
                    <RegisterHeader title="Demo Data" />
                    <DemoDataIntegration
                      tenantId={company.id}
                      showCompanyLink={
                        company.role === "owner" &&
                        !!(
                          company.sandbox_run_id ||
                          company.company_kind === "sandbox" ||
                          company.company_kind === "demo"
                        )
                      }
                    />
                  </>
                ) : selection.route === "data-sources" ? (
                  <DataSourcesPage
                    user={user.id}
                    company={company}
                    selection={selection}
                    navigate={navigate}
                  />
                ) : selection.route === "finance" ? (
                  <FinancePage
                    canManage={company.role === "owner"}
                    canAcceptReduction={company.role === "owner"}
                    refund={(id) => {
                      setActionTarget({ creditNote: id });
                      setAction("customer_refund_post");
                    }}
                    credit={(id) => {
                      setActionTarget({ invoice: id });
                      setAction("sales_credit_record");
                    }}
                    reverse={(id) => {
                      setActionTarget({ postingGroup: id });
                      setAction("ledger_reverse");
                    }}
                    recordPayment={() => {
                      setActionTarget({});
                      setAction(
                        selection.flow === "payable"
                          ? "supplier_payment_post"
                          : "customer_payment_post",
                      );
                    }}
                    selection={selection}
                    navigate={navigate}
                    create={() => {
                      setActionTarget({});
                      setAction(
                        selection.flow === "payable"
                          ? "supplier_invoice_record"
                          : "sales_invoice_record",
                      );
                    }}
                  />
                ) : selection.route === "warehouse" ? (
                  <WarehousePage
                    opening={() => {
                      setActionTarget({});
                      setAction("opening_stock");
                    }}
                    selection={selection}
                    navigate={navigate}
                    correct={(id) => {
                      setActionTarget({ movement: id });
                      setAction("movement_correct");
                    }}
                    release={(id) => {
                      setActionTarget({ reservation: id });
                      setAction("reservation_release");
                    }}
                  />
                ) : selection.route === "attention" ? (
                  <AttentionPage selection={selection} navigate={navigate} />
                ) : selection.route === "chat" ? (
                  <CompanyChatPage company={company} selection={selection} navigate={navigate} />
                ) : selection.route === "storyline" ? (
                  <StorylinePage
                    selection={selection}
                    navigate={navigate}
                    company={company}
                    openCompany={openCompany}
                  />
                ) : selection.route === "work" ? (
                  <DeliveryWorkPage selection={selection} navigate={navigate} />
                ) : selection.route === "copilot" ? (
                  <HomePage
                    user={user.id}
                    tenant={company.id}
                    companyName={company.name}
                    owner={company.role === "owner"}
                    navigate={navigate}
                  />
                ) : (
                  <DecisionsPage
                    tenant={company.id}
                    select={(proposal, reviewKind) =>
                      navigate(proposalReviewLocation(proposal, reviewKind))
                    }
                    view={selection.decisionsView || "pending"}
                    setView={(decisionsView) =>
                      navigate({ route: "decisions", decisionsView, proposal: "", page: 1 })
                    }
                    openDecision={(proposal) => navigate({ route: "decisions", proposal })}
                  />
                )}
              </div>
            </TableProvider>
            {action && (
              <ActionCard
                key={`${company.id}:${selection.proposal}`}
                tenant={company.id}
                commitment={action ? actionTarget.commitment || "" : selection.commitment}
                reservation={actionTarget.reservation}
                postingGroup={actionTarget.postingGroup}
                invoice={actionTarget.invoice}
                creditNote={actionTarget.creditNote}
                movement={actionTarget.movement}
                direction={actionTarget.direction}
                order={actionTarget.order}
                shipmentInput={actionTarget.shipmentInput}
                proposalId={selection.proposal}
                tool={action}
                close={() => {
                  setAction(null);
                  setActionTarget({});
                  navigate({ proposal: "" });
                }}
                prepared={(id) => navigate({ proposal: id })}
                settled={() => window.dispatchEvent(new Event("reality:delivery-settled"))}
              />
            )}
            {!action && selection.proposal && selection.route !== "master-data" && (
              <ProposalReviewCard
                tenant={company.id}
                proposalId={selection.proposal}
                close={() => navigate({ proposal: "" })}
              />
            )}
          </Shell>
        </ActionDiscoveryProvider>
      </TrialProvider>
    </TrialEntry>
  );
}

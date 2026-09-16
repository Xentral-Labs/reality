import { SidebarTooltip } from "./SidebarTooltip";
import { LiveSimulationIndicator } from "./LiveSimulationIndicator";
import { HeaderControls } from "./HeaderControls";
import { isPurchasing } from "./pageIntroduction";
import { PageActionTarget, PageCountTarget } from "./PageHeading";
import { pageIntroduction } from "./pageIntroduction";
import { dailyWork, isCommitmentsSelection } from "./dailyWork";
import { ProfileMenu } from "./ProfileMenu";
import { RegisterHeaderTarget } from "./RegisterWorkbench";
import { inspectorSections, inspectorSection, inspectorTabs } from "./inspectorSections";
const dockPanel =
  "fixed inset-x-0 bottom-0 top-[60px] z-20 flex min-w-0 flex-col border-l border-border-default bg-surface lg:sticky lg:top-[60px] lg:h-[calc(100dvh-60px)]";
const wideGrid = "lg:grid-cols-[var(--shell-navigation-width,200px)_minmax(0,1fr)]";
const dockGrid =
  "lg:grid-cols-[var(--shell-navigation-width,200px)_minmax(0,1fr)_360px] xl:grid-cols-[var(--shell-navigation-width,200px)_minmax(0,1fr)_400px] 2xl:grid-cols-[var(--shell-navigation-width,200px)_minmax(0,1fr)_440px]";
import { CompanySwitcher } from "./CompanySwitcher";
import { ChatPage } from "./ChatPage";
import { ActivityDrawer } from "./ActivityDrawer";
import { ActionLauncher, type DeliveryAction } from "./ActionLauncher";
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import {
  BookOpen,
  FileSearch,
  FileText,
  Waypoints,
  Zap,
  PackageCheck,
  Wallet,
  Boxes,
  TriangleAlert,
  ChartNoAxesCombined,
  LayoutGrid,
  CheckSquare,
  House,
  History,
  Menu,
  PanelLeft,
  MessageSquare,
  Settings,
  Database,
  X,
  Moon,
  Sun,
} from "lucide-react";
import type { AuthUser, Tenant } from "../api";
import { LogoMark } from "../components/LogoMark";
import {
  storeThemePreference,
  readThemePreference,
  resolveTheme,
  applyTheme,
  watchSystemTheme,
} from "../theme";
import { t } from "../localization";
import { selectionUrl, type Selection } from "./routing";

export function Shell({
  user,
  company,
  companies,
  selection,
  navigate,
  switchCompany,
  children,
  openAction,
}: {
  user: AuthUser;
  company: Tenant;
  companies: Tenant[];
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
  switchCompany: (id: string) => void;
  children: ReactNode;
  openAction: (tool: DeliveryAction) => void;
}) {
  const [chatOpen, setChatOpen] = useState(
    () => window.innerWidth >= 1024 || selection.route === "copilot",
  );
  useEffect(() => {
    if (selection.route === "copilot") setChatOpen(true);
  }, [selection.route]);
  useEffect(() => {
    const show = () => setChatOpen(true);
    window.addEventListener("reality:open-chat", show);
    return () => window.removeEventListener("reality:open-chat", show);
  }, []);
  // Storyline has its own protocol column; the chat dock stays closed there.
  const dockOpen = chatOpen && selection.route !== "storyline" && selection.route !== "chat";
  const [activityTenant, setActivityTenant] = useState<string | null>(null);
  useEffect(() => setActivityTenant(null), [company.id]);
  const [registerHeader, setRegisterHeader] = useState<HTMLDivElement | null>(null);
  const navigationRef = useRef<HTMLElement>(null);
  const [open, setOpen] = useState(false);
  const [navigationCollapsed, setNavigationCollapsed] = useState(() => {
    try {
      return localStorage.getItem("reality.navigation.collapsed") === "true";
    } catch {
      return false;
    }
  });
  const toggleNavigation = () => {
    const collapsed = !navigationCollapsed;
    setNavigationCollapsed(collapsed);
    try {
      localStorage.setItem("reality.navigation.collapsed", String(collapsed));
    } catch {
      // The current view remains usable when browser storage is unavailable.
    }
  };
  const [dark, setDark] = useState(resolveTheme(readThemePreference()) === "dark");
  useEffect(() => {
    const changed = () => {
      const preference = readThemePreference();
      applyTheme(preference);
      setDark(resolveTheme(preference) === "dark");
    };
    window.addEventListener("reality:theme-changed", changed);
    const stop = watchSystemTheme(changed);
    return () => {
      window.removeEventListener("reality:theme-changed", changed);
      stop();
    };
  }, []);
  const dailyIcons = [PackageCheck, TriangleAlert, CheckSquare];
  const inspectorIcons = [Waypoints, FileText, History, Zap];
  const destinations = [
    {
      label: "Home",
      target: { route: "home", proposal: "", page: 1, q: "" } as Partial<Selection>,
      Icon: House,
      active: selection.route === "home",
    },
    {
      label: "Chat",
      target: { route: "chat", commitment: "", proposal: "", page: 1, q: "" } as Partial<Selection>,
      Icon: MessageSquare,
      active: selection.route === "chat",
    },
    ...dailyWork.map((item, index) => ({
      label: item.label,
      target: item.selection,
      Icon: dailyIcons[index],
      active:
        item.label === "Commitments"
          ? isCommitmentsSelection(selection)
          : selection.route === item.selection.route,
    })),
  ];
  const introduction = pageIntroduction(selection);
  const contentTitle =
    selection.route === "inspector"
      ? inspectorTabs(selection.inspectorView || "overview").find(
          ([key]) =>
            key ===
            (selection.inspectorView === "records"
              ? "facts"
              : selection.inspectorView || "overview"),
        )?.[1] || "Reality Inspector"
      : selection.route === "warehouse"
        ? ({ stock: "Stock", reservations: "Reservations", movements: "Movements" } as const)[
            selection.warehouseView
          ]
        : selection.route === "finance"
          ? (
              {
                "open-items": "Open items",
                payments: "Payments",
                journal: "Journal",
                balances: "Balances",
                settings: "Finance settings",
              } as const
            )[selection.financeView]
          : selection.route === "master-data"
            ? (
                {
                  customer: "Customers",
                  supplier: "Suppliers",
                  item: "Items",
                  location: "Locations",
                } as const
              )[selection.family]
            : introduction.title;
  const ContentIcon =
    selection.route === "home"
      ? House
      : selection.route === "attention"
        ? TriangleAlert
        : selection.route === "decisions"
          ? CheckSquare
          : selection.route === "warehouse"
            ? Boxes
            : selection.route === "finance"
              ? Wallet
              : selection.route === "analytics"
                ? ChartNoAxesCombined
                : selection.route === "master-data"
                  ? LayoutGrid
                  : selection.route === "settings"
                    ? Settings
                    : selection.route === "data-sources" || selection.route === "demo-data"
                      ? Database
                      : selection.route === "orders-deliveries"
                        ? PackageCheck
                        : selection.route === "inspector"
                          ? inspectorIcons[
                              inspectorSections.indexOf(inspectorSection(selection.inspectorView))
                            ]
                          : FileSearch;
  const [pageCount, setPageCount] = useState<HTMLSpanElement | null>(null);
  const [pageActions, setPageActions] = useState<HTMLDivElement | null>(null);
  const shellRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLElement>(null);
  useLayoutEffect(() => {
    const header = headerRef.current;
    if (!header) return;
    const measure = () =>
      shellRef.current?.style.setProperty(
        "--app-header-height",
        `${header.getBoundingClientRect().height}px`,
      );
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(header);
    return () => observer.disconnect();
  }, []);
  const activeNavigation = "bg-accent-soft text-accent";
  return (
    <RegisterHeaderTarget.Provider value={registerHeader}>
      <PageActionTarget.Provider value={pageActions}>
        <PageCountTarget.Provider value={pageCount}>
          <div
            ref={shellRef}
            data-navigation-collapsed={navigationCollapsed}
            data-contained-chat={selection.route === "chat" || undefined}
            className="app-shell min-h-screen bg-bg text-fg-default"
          >
            <header
              ref={headerRef}
              data-shell-header
              data-chat-open={chatOpen ? "true" : "false"}
              className="sticky top-0 z-30 h-[60px] border-b border-border-default bg-surface"
            >
              <div className="shell-brand flex min-w-0 items-center gap-2">
                <button
                  type="button"
                  className="br-btn lg:hidden"
                  aria-label={t("Navigation")}
                  aria-expanded={open}
                  onClick={() => setOpen(!open)}
                >
                  <Menu size={19} />
                </button>
                <a
                  href={selectionUrl({ ...selection, route: "home" })}
                  className="shell-brand-home grid size-8 shrink-0 place-items-center rounded-lg bg-accent p-1.5"
                  aria-label="Reality"
                  title="Reality"
                  onClick={(e) => {
                    e.preventDefault();
                    navigate({ route: "home" });
                  }}
                >
                  <LogoMark />
                </a>
                <div className="shell-company min-w-0 flex-1">
                  <CompanySwitcher
                    company={company}
                    companies={companies}
                    switchCompany={switchCompany}
                  />
                </div>
              </div>
              <div className="shell-header-center">
                <div className="shell-page-heading" data-page-introduction>
                  <ContentIcon size={19} aria-hidden="true" />
                  <div className="shell-page-copy">
                    <h1 title={t(contentTitle)}>
                      <span className="shell-page-title">{t(contentTitle)}</span>
                      <span className="page-introduction-count" ref={setPageCount} />
                    </h1>
                    <p data-page-description title={t(introduction.description)}>
                      {t(introduction.description)}
                    </p>
                  </div>
                </div>
              </div>
              <HeaderControls
                identity={`${selection.route}:${contentTitle}:${company.id}`}
                indicator={
                  <LiveSimulationIndicator
                    key={company.id}
                    company={company}
                    selection={selection}
                    navigate={navigate}
                  />
                }
              >
                <div className="shell-utilities flex shrink-0 items-center gap-2 sm:gap-3">
                  <button
                    className="br-btn"
                    aria-label={t("Activity")}
                    onClick={() => setActivityTenant(company.id)}
                  >
                    <History size={17} />
                    <span className="hidden lg:inline">{t("Activity")}</span>
                  </button>
                  <ActionLauncher />
                  <button
                    className="br-btn hidden sm:inline-flex"
                    aria-label={t("Appearance")}
                    onClick={() => {
                      storeThemePreference(dark ? "light" : "dark");
                    }}
                  >
                    {dark ? <Sun size={17} /> : <Moon size={17} />}
                  </button>
                  <button
                    className="br-btn br-btn-primary"
                    aria-label={t(chatOpen ? "Hide chat" : "Show chat")}
                    aria-expanded={chatOpen}
                    aria-controls="global-chat"
                    onClick={() => setChatOpen(!chatOpen)}
                  >
                    <MessageSquare size={17} />
                    <span className="hidden sm:inline">{t("Ask Reality")}</span>
                  </button>
                </div>
              </HeaderControls>
            </header>
            <div data-shell-body className={`lg:grid ${dockOpen ? dockGrid : wideGrid}`}>
              {open && (
                <button
                  className="fixed inset-0 z-30 bg-black/30 lg:hidden"
                  aria-label={t("Close")}
                  onClick={() => setOpen(false)}
                />
              )}
              <aside
                data-primary-navigation
                ref={navigationRef}
                id="primary-navigation"
                className={`shell-navigation ${open ? "flex" : "hidden"} fixed inset-y-0 left-0 z-40 w-60 flex-col gap-4 overflow-y-auto border-r border-border-default bg-surface px-2 py-3 lg:sticky lg:top-[60px] lg:z-20 lg:flex lg:h-[calc(100dvh-60px)] lg:w-auto`}
              >
                <button
                  className="br-btn self-end lg:hidden"
                  aria-label={t("Close")}
                  onClick={() => setOpen(false)}
                >
                  <X size={18} />
                </button>
                <nav aria-label={t("Daily work")}>
                  <div className="shell-navigation-heading mb-1.5 flex items-center justify-between">
                    <p className="px-3 text-[10px] uppercase tracking-wider text-fg-muted">
                      {t("Daily work")}
                    </p>
                    <button
                      type="button"
                      data-navigation-toggle
                      className="hidden size-8 shrink-0 items-center justify-center rounded-md text-fg-muted hover:bg-surface-muted hover:text-fg-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent lg:flex"
                      aria-label={t(navigationCollapsed ? "Expand sidebar" : "Collapse sidebar")}
                      data-sidebar-tooltip={t(
                        navigationCollapsed ? "Expand sidebar" : "Collapse sidebar",
                      )}
                      aria-expanded={!navigationCollapsed}
                      aria-controls="primary-navigation"
                      onClick={toggleNavigation}
                    >
                      <PanelLeft size={18} />
                    </button>
                  </div>
                  <div className="space-y-0.5">
                    {destinations.map(({ label, target, Icon, active }) => (
                      <a
                        data-navigation-item
                        aria-label={t(label)}
                        data-sidebar-tooltip={t(label)}
                        key={label}
                        href={selectionUrl({ ...selection, ...target })}
                        aria-current={active ? "page" : undefined}
                        onClick={(e) => {
                          e.preventDefault();
                          navigate(target);
                          setOpen(false);
                        }}
                        className={`flex items-center gap-2 rounded-md px-3 py-2 text-[13px] leading-5 ${active ? activeNavigation : "hover:bg-surface-muted"}`}
                      >
                        <Icon size={17} />
                        <span data-navigation-label>{t(label)}</span>
                      </a>
                    ))}
                  </div>
                </nav>
                <nav aria-label={t("Workspaces")}>
                  <p className="mb-1.5 px-3 text-[10px] uppercase tracking-wider text-fg-muted">
                    {t("Workspaces")}
                  </p>
                  {([false, true] as const).map((purchasing) => {
                    const selected =
                      selection.route === "orders-deliveries" &&
                      !isCommitmentsSelection(selection) &&
                      isPurchasing(selection) === purchasing;
                    const destination: Partial<Selection> = {
                      route: "orders-deliveries",
                      ordersView: purchasing ? "supplier-orders" : "customer-orders",
                      deliveryType: purchasing ? "supplier_delivery" : "customer_delivery",
                      order: "",
                      commitment: "",
                      entry: "",
                      proposal: "",
                      q: "",
                      page: 1,
                    };
                    return (
                      <a
                        key={String(purchasing)}
                        data-navigation-item
                        aria-label={t(purchasing ? "Purchasing" : "Sales")}
                        data-sidebar-tooltip={t(purchasing ? "Purchasing" : "Sales")}
                        className={`flex items-center gap-2 rounded-md px-3 py-2 text-[13px] leading-5 ${selected ? activeNavigation : "hover:bg-surface-muted"}`}
                        href={selectionUrl({ ...selection, ...destination })}
                        aria-current={selected ? "page" : undefined}
                        onClick={(event) => {
                          event.preventDefault();
                          navigate(destination);
                          setOpen(false);
                        }}
                      >
                        <PackageCheck size={17} />
                        <span data-navigation-label>{t(purchasing ? "Purchasing" : "Sales")}</span>
                      </a>
                    );
                  })}
                  <a
                    data-navigation-item
                    aria-label={t("Warehouse")}
                    data-sidebar-tooltip={t("Warehouse")}
                    className={`flex items-center gap-2 rounded-md px-3 py-2 text-[13px] leading-5 ${selection.route === "warehouse" ? activeNavigation : "hover:bg-surface-muted"}`}
                    href={selectionUrl({
                      ...selection,
                      route: "warehouse",
                      proposal: "",
                      entry: "",
                    })}
                    aria-current={selection.route === "warehouse" ? "page" : undefined}
                    onClick={(event) => {
                      event.preventDefault();
                      navigate({
                        route: "warehouse",
                        proposal: "",
                        entry: "",
                        q: "",
                        page: 1,
                        state: "",
                      });
                      setOpen(false);
                    }}
                  >
                    <Boxes size={17} />
                    <span data-navigation-label>{t("Warehouse")}</span>
                  </a>
                  <a
                    data-navigation-item
                    aria-label={t("Finance")}
                    data-sidebar-tooltip={t("Finance")}
                    className={`flex items-center gap-2 rounded-md px-3 py-2 text-[13px] leading-5 ${selection.route === "finance" ? activeNavigation : "hover:bg-surface-muted"}`}
                    href={selectionUrl({
                      ...selection,
                      route: "finance",
                      proposal: "",
                      entry: "",
                      q: "",
                      page: 1,
                    })}
                    aria-current={selection.route === "finance" ? "page" : undefined}
                    onClick={(event) => {
                      event.preventDefault();
                      navigate({ route: "finance", proposal: "", entry: "", q: "", page: 1 });
                      setOpen(false);
                    }}
                  >
                    <Wallet size={17} />
                    <span data-navigation-label>{t("Finance")}</span>
                  </a>
                  <a
                    data-navigation-item
                    aria-label={t("Master data")}
                    data-sidebar-tooltip={t("Master data")}
                    className={`flex items-center gap-2 rounded-md px-3 py-2 text-[13px] leading-5 ${selection.route === "master-data" ? activeNavigation : "hover:bg-surface-muted"}`}
                    href={selectionUrl({ ...selection, route: "master-data" })}
                    aria-current={selection.route === "master-data" ? "page" : undefined}
                    onClick={(event) => {
                      event.preventDefault();
                      navigate({ route: "master-data", proposal: "", page: 1, q: "" });
                      setOpen(false);
                    }}
                  >
                    <LayoutGrid size={17} />
                    <span data-navigation-label>{t("Master data")}</span>
                  </a>
                </nav>
                <nav aria-labelledby="analytics-navigation-label">
                  <p
                    id="analytics-navigation-label"
                    data-localization="original"
                    className="mb-1.5 px-3 text-[10px] uppercase tracking-wider text-fg-muted"
                  >
                    Analytics
                  </p>
                  <a
                    data-navigation-item
                    aria-label={t("Reports")}
                    data-sidebar-tooltip={t("Reports")}
                    href={selectionUrl({ ...selection, route: "analytics" })}
                    className={`flex items-center gap-2 rounded-md px-3 py-2 text-[13px] leading-5 ${selection.route === "analytics" ? activeNavigation : "hover:bg-surface-muted"}`}
                    aria-current={selection.route === "analytics" ? "page" : undefined}
                    onClick={(event) => {
                      event.preventDefault();
                      navigate({ route: "analytics", proposal: "", page: 1, q: "" });
                      setOpen(false);
                    }}
                  >
                    <ChartNoAxesCombined size={17} />
                    <span data-navigation-label>{t("Reports")}</span>
                  </a>
                </nav>
                <nav aria-labelledby="inspector-navigation-label">
                  <p
                    id="inspector-navigation-label"
                    data-localization="original"
                    className="mb-1.5 px-3 text-[10px] uppercase tracking-wider text-fg-muted"
                  >
                    Reality Inspector
                  </p>
                  {inspectorSections.map((section, index) => {
                    const Icon = inspectorIcons[index];
                    return (
                      <a
                        key={section.label}
                        data-navigation-item
                        aria-label={t(section.label)}
                        data-sidebar-tooltip={t(section.label)}
                        href={selectionUrl({
                          ...selection,
                          route: "inspector",
                          inspectorView: section.tabs[0],
                          q: "",
                          page: 1,
                        })}
                        aria-current={
                          selection.route === "inspector" &&
                          inspectorSection(selection.inspectorView) === section
                            ? "page"
                            : undefined
                        }
                        className={`flex items-center gap-2 rounded-md px-3 py-2 text-[13px] leading-5 ${selection.route === "inspector" && inspectorSection(selection.inspectorView) === section ? activeNavigation : "hover:bg-surface-muted"}`}
                        onClick={(event) => {
                          event.preventDefault();
                          navigate({
                            route: "inspector",
                            inspectorView: section.tabs[0],
                            entry: "",
                            q: "",
                            page: 1,
                          });
                          setOpen(false);
                        }}
                      >
                        <Icon size={17} className="shrink-0" />
                        <span data-navigation-label>{t(section.label)}</span>
                      </a>
                    );
                  })}
                </nav>
                <nav aria-label={t("Company")}>
                  <p className="mb-1.5 px-3 text-[10px] uppercase tracking-wider text-fg-muted">
                    {t("Company")}
                  </p>

                  <a
                    data-navigation-item
                    aria-label={t("Integrations")}
                    data-sidebar-tooltip={t("Integrations")}
                    className={`flex items-center gap-2 rounded-md px-3 py-2 text-[13px] leading-5 ${selection.route === "data-sources" ? activeNavigation : "hover:bg-surface-muted"}`}
                    href={selectionUrl({
                      ...selection,
                      route: "data-sources",
                      entry: "",
                      proposal: "",
                      q: "",
                      page: 1,
                    })}
                    aria-current={selection.route === "data-sources" ? "page" : undefined}
                    onClick={(event) => {
                      event.preventDefault();
                      navigate({ route: "data-sources", entry: "", proposal: "", q: "", page: 1 });
                      setOpen(false);
                    }}
                  >
                    <Database size={17} />
                    <span data-navigation-label>{t("Integrations")}</span>
                  </a>
                  <a
                    data-navigation-item
                    aria-label={t("Companies")}
                    data-sidebar-tooltip={t("Companies")}
                    className={`flex items-center gap-2 rounded-md px-3 py-2 text-[13px] leading-5 ${selection.route === "settings" && selection.settingsView !== "personal" ? activeNavigation : "hover:bg-surface-muted"}`}
                    href={selectionUrl({
                      ...selection,
                      route: "settings",
                      settingsView: "company",
                      proposal: "",
                      q: "",
                      page: 1,
                    })}
                    aria-current={
                      selection.route === "settings" && selection.settingsView !== "personal"
                        ? "page"
                        : undefined
                    }
                    onClick={(event) => {
                      event.preventDefault();
                      navigate({
                        route: "settings",
                        settingsView: "company",
                        proposal: "",
                        q: "",
                        page: 1,
                      });
                      setOpen(false);
                    }}
                  >
                    <Settings size={17} />
                    <span data-navigation-label>{t("Companies")}</span>
                  </a>
                  <a
                    data-navigation-item
                    aria-label={t("Storyline")}
                    data-sidebar-tooltip={t("Storyline")}
                    className={`flex items-center gap-2 rounded-md px-3 py-2 text-[13px] leading-5 ${selection.route === "storyline" ? activeNavigation : "hover:bg-surface-muted"}`}
                    href={selectionUrl({
                      ...selection,
                      route: "storyline",
                      storylineChapter: "library",
                      page: 1,
                      q: "",
                    })}
                    aria-current={selection.route === "storyline" ? "page" : undefined}
                    onClick={(event) => {
                      event.preventDefault();
                      navigate({
                        route: "storyline",
                        storylineChapter: "library",
                        page: 1,
                        q: "",
                        proposal: "",
                      });
                      setOpen(false);
                    }}
                  >
                    <BookOpen size={17} />
                    <span data-navigation-label>{t("Storyline")}</span>
                  </a>
                  {(company.company_kind === "demo" || company.demo_data_state) && (
                    <a
                      data-navigation-item
                      aria-label={t("Demo Data")}
                      data-sidebar-tooltip={t("Demo Data")}
                      className={`flex items-center gap-2 rounded-md px-3 py-2 text-[13px] leading-5 ${selection.route === "demo-data" ? activeNavigation : "hover:bg-surface-muted"}`}
                      href={selectionUrl({ ...selection, route: "demo-data", page: 1, q: "" })}
                      aria-current={selection.route === "demo-data" ? "page" : undefined}
                      onClick={(event) => {
                        event.preventDefault();
                        navigate({ route: "demo-data", page: 1, q: "" });
                        setOpen(false);
                      }}
                    >
                      <Database size={17} />
                      <span data-navigation-label>{t("Demo Data")}</span>
                    </a>
                  )}
                </nav>
                <ProfileMenu
                  user={user}
                  selection={selection}
                  navigate={navigate}
                  closeNavigation={() => setOpen(false)}
                />
              </aside>
              <SidebarTooltip navigation={navigationRef} />
              <main id="main-content" className="min-w-0 px-4 py-5 lg:px-5 lg:py-6">
                <div className="page-view-tabs" data-page-tabs>
                  <div className="page-view-tabs-target" ref={setRegisterHeader} />
                  <div className="page-introduction-actions" ref={setPageActions} />
                </div>
                {children}
              </main>
              <aside
                id="global-chat"
                data-global-chat
                aria-label={t("Ask Reality")}
                hidden={!dockOpen}
                className={dockOpen ? dockPanel : "hidden"}
              >
                <div className="min-h-0 flex-1">
                  <ChatPage
                    key={company.id}
                    selection={selection}
                    navigate={navigate}
                    compact
                    dock
                    active={chatOpen}
                  />
                </div>
              </aside>
            </div>
            {activityTenant === company.id && (
              <ActivityDrawer
                key={company.id}
                tenant={company.id}
                companyName={company.name}
                close={() => setActivityTenant(null)}
              />
            )}
          </div>
        </PageCountTarget.Provider>
      </PageActionTarget.Provider>
    </RegisterHeaderTarget.Provider>
  );
}

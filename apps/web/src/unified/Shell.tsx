import { SidebarTooltip } from "./SidebarTooltip";
import { LiveSimulationIndicator } from "./LiveSimulationIndicator";
import { isPurchasing } from "./pageIntroduction";
import { PageActionTarget, PageCountTarget } from "./PageHeading";
import { pageIntroduction } from "./pageIntroduction";
import { dailyWork, isCommitmentsSelection } from "./dailyWork";
import { ProfileMenu } from "./ProfileMenu";
import { RegisterHeaderTarget } from "./RegisterWorkbench";
import { inspectorSections, inspectorSection, inspectorTabs } from "./inspectorSections";
import { CompanySwitcher } from "./CompanySwitcher";
import { ChatPage } from "./ChatPage";
import { ActionLauncher, type DeliveryAction } from "./ActionLauncher";
import { useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import {
  BookOpen,
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
  Database,
  X,
  Info,
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
  const [registerHeader, setRegisterHeader] = useState<HTMLDivElement | null>(null);
  const navigationRef = useRef<HTMLElement>(null);
  const [open, setOpen] = useState(false);
  const navigationOpener = useRef<HTMLButtonElement>(null);
  const wasNavigationOpen = useRef(false);
  useEffect(() => {
    if (wasNavigationOpen.current && !open && window.innerWidth < 1024)
      navigationOpener.current?.focus();
    wasNavigationOpen.current = open;
  }, [open]);
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
  const [pageCount, setPageCount] = useState<HTMLSpanElement | null>(null);
  const [pageActions, setPageActions] = useState<HTMLDivElement | null>(null);
  const shellRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLElement>(null);
  const descriptionId = useId();
  const descriptionRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    descriptionRef.current?.hidePopover();
  }, [selection.route, contentTitle, company.id]);
  useEffect(() => {
    const close = () => descriptionRef.current?.hidePopover();
    window.addEventListener("resize", close);
    return () => window.removeEventListener("resize", close);
  }, []);
  useEffect(() => {
    if (!open) return;
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !document.querySelector(":popover-open")) setOpen(false);
    };
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [open]);
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
  const activeNavigation = "shell-navigation-active";
  return (
    <RegisterHeaderTarget.Provider value={registerHeader}>
      <PageActionTarget.Provider value={pageActions}>
        <PageCountTarget.Provider value={pageCount}>
          <div
            ref={shellRef}
            data-navigation-collapsed={navigationCollapsed}
            data-contained-chat={selection.route === "chat" || undefined}
            data-dock-open={dockOpen}
            className="app-shell min-h-screen bg-bg text-fg-default"
          >
            <header ref={headerRef} data-shell-header className="shell-workspace-header">
              <button
                type="button"
                data-navigation-opener
                ref={navigationOpener}
                className="shell-icon-button lg:hidden"
                aria-label={t("Navigation")}
                aria-expanded={open}
                aria-controls="primary-navigation"
                onClick={() => setOpen(!open)}
              >
                <Menu size={18} />
              </button>
              <div className="shell-page-heading" data-page-introduction>
                <h1 title={t(contentTitle)}>
                  <span className="shell-page-title">{t(contentTitle)}</span>
                  <span className="page-introduction-count" ref={setPageCount} />
                </h1>
                <button
                  type="button"
                  data-page-description-trigger
                  className="shell-icon-button"
                  aria-label={t("About this page")}
                  popoverTarget={descriptionId}
                  aria-haspopup="dialog"
                  onClick={(event) => {
                    const rect = event.currentTarget.getBoundingClientRect();
                    if (descriptionRef.current) {
                      descriptionRef.current.style.left = `${Math.max(8, Math.min(rect.left, innerWidth - 336))}px`;
                      descriptionRef.current.style.top = `${rect.bottom + 8}px`;
                    }
                  }}
                >
                  <Info size={15} />
                </button>
                <div
                  ref={descriptionRef}
                  id={descriptionId}
                  popover="auto"
                  role="dialog"
                  aria-label={t("About this page")}
                  data-page-description
                  className="shell-description"
                >
                  {t(introduction.description)}
                </div>
              </div>
              {selection.route !== "chat" && selection.route !== "storyline" && (
                <button
                  className="shell-chat-toggle"
                  aria-label={t(dockOpen ? "Hide chat" : "Show chat")}
                  aria-expanded={dockOpen}
                  aria-controls="global-chat"
                  onClick={() => setChatOpen(!chatOpen)}
                >
                  <MessageSquare size={16} />
                  <span>{t("Ask Reality")}</span>
                </button>
              )}
            </header>
            <div data-shell-body>
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
                className={`shell-navigation ${open ? "flex" : "hidden"} lg:flex`}
              >
                <div className="shell-company-block">
                  <div className="shell-brand flex min-w-0 items-center gap-2">
                    <a
                      href={selectionUrl({ ...selection, route: "home" })}
                      className="shell-brand-home grid size-8 shrink-0 place-items-center rounded-lg bg-accent p-1.5"
                      aria-label="Reality"
                      title="Reality"
                      onClick={(e) => {
                        e.preventDefault();
                        setOpen(false);
                        navigate({ route: "home" });
                      }}
                    >
                      <LogoMark />
                    </a>
                    <div className="shell-company min-w-0 flex-1">
                      <CompanySwitcher
                        company={company}
                        companies={companies}
                        selection={selection}
                        navigate={(target) => {
                          setOpen(false);
                          navigate(target);
                        }}
                        switchCompany={(id) => {
                          setOpen(false);
                          switchCompany(id);
                        }}
                      />
                    </div>
                    <button
                      type="button"
                      data-navigation-close
                      className="shell-icon-button lg:hidden"
                      aria-label={t("Close")}
                      onClick={() => setOpen(false)}
                    >
                      <X size={18} />
                    </button>
                  </div>
                  <ActionLauncher key={company.id} onLaunch={() => setOpen(false)} />
                  <LiveSimulationIndicator
                    key={company.id}
                    company={company}
                    selection={selection}
                    navigate={(target) => {
                      setOpen(false);
                      navigate(target);
                    }}
                  />
                </div>
                <div className="shell-navigation-scroll">
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
                          <span data-navigation-label>
                            {t(purchasing ? "Purchasing" : "Sales")}
                          </span>
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
                    <a
                      data-navigation-item
                      aria-label={t("Analytics")}
                      data-sidebar-tooltip={t("Analytics")}
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
                      <span data-navigation-label>{t("Analytics")}</span>
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
                        navigate({
                          route: "data-sources",
                          entry: "",
                          proposal: "",
                          q: "",
                          page: 1,
                        });
                        setOpen(false);
                      }}
                    >
                      <Database size={17} />
                      <span data-navigation-label>{t("Integrations")}</span>
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
                  </nav>
                </div>
                <div className="shell-navigation-utilities">
                  <ProfileMenu
                    user={user}
                    selection={selection}
                    navigate={navigate}
                    closeNavigation={() => setOpen(false)}
                    dark={dark}
                    toggleAppearance={() => storeThemePreference(dark ? "light" : "dark")}
                  />
                </div>
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
                className={dockOpen ? "shell-chat-dock" : "hidden"}
              >
                <div className="min-h-0 flex-1">
                  <ChatPage
                    key={company.id}
                    selection={selection}
                    navigate={navigate}
                    compact
                    dock
                    active={chatOpen}
                    closeDock={() => setChatOpen(false)}
                  />
                </div>
              </aside>
            </div>
          </div>
        </PageCountTarget.Provider>
      </PageActionTarget.Provider>
    </RegisterHeaderTarget.Provider>
  );
}

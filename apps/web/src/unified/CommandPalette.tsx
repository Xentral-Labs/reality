import {
  Search,
  ArrowRight,
  FileText,
  Users,
  Package,
  MapPin,
  Zap,
  LayoutGrid,
  Star,
  Inbox,
  PackageCheck,
  Boxes,
  Wallet,
  ChartNoAxesCombined,
  MessageSquare,
  Waypoints,
  History,
  Database,
  BookOpen,
  Settings,
  Building2,
  Truck,
} from "lucide-react";
import { CommandSearchStatus } from "./CommandSearchStatus";
import { useEffect, useId, useMemo, useRef, useState, type RefObject } from "react";
import { languageHref } from "../../../shared/language";
import { graphApi } from "../api";
import { currentLanguage, t } from "../localization";
import type { DiscoveryContext } from "./ActionLauncher";
import { paletteEntries, type PaletteEntry } from "./commandPaletteEntries";
import { matchTier, comparePaletteEntries, palettePreview } from "./commandPaletteRanking";
import { paletteTargetSelection } from "./commandPaletteTargets";
import { ReadState } from "./ReadState";
import { usePalettePreferences } from "./usePalettePreferences";
import { searchFamilies, useCommandSearch } from "./useCommandSearch";
import { useRead } from "./useCompanyContext";

const groupLabels = {
  actions: "Actions",
  pages: "Pages",
  reports: "Reports",
  partners: "Business partners",
  items_locations: "Items and locations",
  orders: "Orders",
  finance: "Finance",
  shipping: "Shipping",
  reality: "Reality and evidence",
  companies: "Companies",
  help: "Help",
};
function PaletteIcon({ entry }: { entry: PaletteEntry }) {
  const target = entry.target;
  if (target.kind === "page") {
    const icons = {
      home: Inbox,
      orders: PackageCheck,
      purchases: PackageCheck,
      warehouse: Boxes,
      finance: Wallet,
      master: LayoutGrid,
      analytics: ChartNoAxesCombined,
      tools: Zap,
      chat: MessageSquare,
      facts: FileText,
      graph: Waypoints,
      activities: History,
      integrations: Database,
      storyline: BookOpen,
      members: Users,
      company: Settings,
      demo: Database,
      "outstanding-customers": Wallet,
      "outstanding-suppliers": Wallet,
      "overdue-customers": Wallet,
      "overdue-suppliers": Wallet,
      "open-outbound": PackageCheck,
      "open-inbound": PackageCheck,
    };
    const Icon = icons[target.id as keyof typeof icons] || LayoutGrid;
    return <Icon />;
  }
  if (target.kind === "record") {
    if (target.record_kind === "party") return <Users />;
    if (target.record_kind === "item") return <Package />;
    if (target.record_kind === "location") return <MapPin />;
    if (target.record_kind === "shipment") return <Truck />;
  }
  if (target.kind === "company") return <Building2 />;
  if (target.kind === "help") return <BookOpen />;
  return entry.group === "actions" ? <Zap /> : <FileText />;
}

export function CommandPalette({
  context,
  searchRef,
  close,
  onLaunch,
}: {
  context: DiscoveryContext;
  searchRef: RefObject<HTMLInputElement | null>;
  close: () => void;
  onLaunch: () => void;
}) {
  const [query, setQuery] = useState("");
  const [family, setFamily] = useState("");
  const [filter, setFilter] = useState("all");
  const [expanded, setExpanded] = useState("");
  const [page, setPage] = useState(0);
  const [active, setActive] = useState<string | null>(null);
  const activating = useRef(false);
  const id = useId();
  const language = currentLanguage();
  const templates = useRead(
    () => graphApi.templates(context.tenant, language),
    [context.tenant, language],
  );
  const records = useCommandSearch(context.tenant, query, language, filter, expanded, page, family);
  const localEntries = useMemo(
    () => paletteEntries(context.data, context, t, language, templates.data?.templates),
    [context.data, context.owner, context.demo, language, templates.data],
  );
  const preferences = usePalettePreferences(context.user, context.tenant, localEntries);
  const [manage, setManage] = useState(false);
  const entries: PaletteEntry[] = [
    ...context.companies.map((company): PaletteEntry => ({
      key: `company:${company.id}`,
      group: "companies",
      label: company.name,
      aliases: [],
      references: [],
      outcome: "Switch company",
      target: { kind: "company", id: company.id },
    })),
    {
      key: "help:docs",
      group: "help",
      label: t("Documentation"),
      aliases: ["Documentation", "Help"],
      references: [],
      outcome: "Open help",
      target: { kind: "help", id: "docs" },
    },
    ...context.contextual,
    ...localEntries.filter(
      (entry) => !context.contextual.some((contextual) => contextual.key === entry.key),
    ),
    ...Object.values(records.providers).flatMap((state) =>
      (state.data?.items || []).map((hit): PaletteEntry => ({
        key: hit.key,
        group: hit.group,
        label: hit.label,
        secondary: hit.secondary,
        aliases: [],
        references: [],
        tier: hit.tier,
        sortKey: hit.sort_key,
        outcome: hit.target.kind === "saved_report" ? "Open report" : "Open record",
        target:
          hit.target.kind === "saved_report"
            ? { kind: "saved_report", id: hit.target.id }
            : { ...hit.target, kind: "record", family: hit.family, roles: hit.roles },
      })),
    ),
  ];
  const matches = entries
    .flatMap((entry) => {
      if (
        filter !== "all" &&
        (filter === "records"
          ? ["actions", "pages", "reports", "help", "companies"].includes(entry.group)
          : entry.group !== filter)
      )
        return [];
      const vocabularyTier = matchTier(query, entry.synonyms || [], []);
      const tier =
        entry.tier ??
        (query.trim()
          ? (matchTier(query, [entry.label, ...entry.aliases], entry.references) ??
            (vocabularyTier === null ? null : Math.max(2, vocabularyTier)))
          : 2);
      return tier === null ? [] : [{ ...entry, tier }];
    })
    .sort(comparePaletteEntries);
  const preview = expanded
    ? [
        ...new Map(
          matches.filter((entry) => entry.group === expanded).map((entry) => [entry.key, entry]),
        ).values(),
      ].slice(page * 50, (page + 1) * 50)
    : palettePreview(matches);
  const emptySuggestions = [
    ...new Map(
      [
        ...preferences.favorites.slice(0, 4),
        ...preferences.recents.slice(0, 4),
        ...context.contextual.slice(0, 2),
        ...localEntries.filter((entry) => entry.group === "pages"),
      ].map((entry) => [entry.key, entry]),
    ).values(),
  ].slice(0, 10);
  const visible = preferences.expired
    ? []
    : !query.trim() && filter === "all"
      ? manage
        ? [
            ...new Map(
              [...preferences.favorites, ...preferences.recents].map((entry) => [entry.key, entry]),
            ).values(),
          ]
        : emptySuggestions
      : preview;
  const visibleKeys = visible.map((entry) => entry.key).join("|");
  useEffect(() => {
    if (active && !visible.some((entry) => entry.key === active)) setActive(null);
  }, [visibleKeys, active]);
  useEffect(() => {
    if (active) document.getElementById(`${id}-${active}`)?.scrollIntoView({ block: "nearest" });
  }, [active, id]);
  const activate = (entry: PaletteEntry) => {
    if (activating.current) return;
    activating.current = true;
    if (["page", "capability", "calculated_report"].includes(entry.target.kind))
      preferences.remember(entry);
    close();
    if (entry.target.kind === "action") context.open(entry.target.id, entry.target.prefill);
    else if (entry.target.kind === "company") {
      if (context.companies.some((company) => company.id === entry.target.id))
        context.switchCompany(entry.target.id);
    } else if (entry.target.kind === "help") {
      if (entry.target.id === "docs")
        window.open(languageHref(__DOCS_URL__, language, true), "_blank", "noopener,noreferrer");
    } else context.navigate(paletteTargetSelection(context.selection, entry.target));
    onLaunch();
  };
  const hiddenGroups = Object.keys(groupLabels).filter(
    (group) =>
      records.providers[group as keyof typeof records.providers]?.data?.has_more ||
      matches.filter((entry) => entry.group === group).length >
        visible.filter((entry) => entry.group === group).length,
  );
  return (
    <div data-command-palette className="command-palette">
      <div className="command-palette-header">
        <p className="mb-2 text-xs text-fg-muted" data-localization="original">
          {context.companyName}
        </p>
        <div className="command-palette-input">
          <Search aria-hidden="true" />
          <input
            ref={searchRef}
            autoFocus
            role="combobox"
            aria-autocomplete="list"
            aria-expanded="true"
            aria-controls={`${id}-results`}
            aria-activedescendant={active ? `${id}-${active}` : undefined}
            className="br-control w-full"
            type="search"
            aria-label={t("Search or start an action")}
            placeholder={t("Search or start an action")}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setActive(null);
              setPage(0);
            }}
            onKeyDown={(event) => {
              if (event.nativeEvent.isComposing || event.repeat) return;
              if (event.key === "ArrowDown" || event.key === "ArrowUp") {
                event.preventDefault();
                const index = visible.findIndex((entry) => entry.key === active);
                const next =
                  index < 0
                    ? event.key === "ArrowDown"
                      ? 0
                      : visible.length - 1
                    : (index + (event.key === "ArrowDown" ? 1 : -1) + visible.length) %
                      visible.length;
                setActive(visible[next]?.key || null);
              } else if (event.key === "Enter") {
                event.preventDefault();
                const selected = visible.find((entry) => entry.key === active);
                if (selected) activate(selected);
              }
            }}
          />
          <button className="command-palette-dismiss" onClick={close} aria-label={t("Close")}>
            <kbd>Esc</kbd>
          </button>
        </div>
        <div className="command-palette-filters" aria-label={t("Search filters")}>
          {[
            ["all", "All"],
            ["records", "Records"],
            ["actions", "Actions"],
            ["pages", "Pages"],
            ["reports", "Reports"],
          ].map(([key, label]) => (
            <button
              key={key}
              className="br-btn"
              aria-pressed={filter === key}
              onClick={() => {
                setFilter(key);
                setFamily("");
                setExpanded("");
                setPage(0);
                setActive(null);
              }}
            >
              {t(label)}
            </button>
          ))}
        </div>
      </div>
      <div className="command-palette-content">
        <CommandSearchStatus
          providers={records.providers}
          labels={groupLabels}
          retry={records.retry}
        />
        {templates.error && ["all", "reports"].includes(filter) && (
          <p role="status" className="text-xs text-fg-muted">
            {t("Report templates are unavailable.")}{" "}
            <button className="br-btn" onClick={templates.refresh}>
              {t("Retry")}
            </button>
          </p>
        )}
        {query.length > 500 && <p role="alert">{t("Search supports at most 500 characters.")}</p>}
        {filter === "records" && (
          <div className="command-palette-record-filter">
            <label>
              {t("Search in")}
              <select
                className="br-control"
                aria-describedby={`${id}-record-filter-hint`}
                value={family}
                onChange={(event) => {
                  setFamily(event.target.value);
                  setExpanded("");
                  setPage(0);
                  setActive(null);
                }}
              >
                <option value="">{t("All records")}</option>
                {Object.values(searchFamilies)
                  .flat()
                  .filter((value) => value !== "private_report")
                  .map((value) => (
                    <option key={value} value={value}>
                      {t(
                        value.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase()),
                      )}
                    </option>
                  ))}
              </select>
            </label>
            <p id={`${id}-record-filter-hint`}>{t("Filters the search above by record type.")}</p>
          </div>
        )}
        {!context.data && (
          <ReadState loading={context.loading} error={context.error} retry={context.refresh} />
        )}
        {expanded && (
          <button
            className="br-btn mb-2"
            onClick={() => {
              setExpanded("");
              setPage(0);
              setActive(null);
            }}
          >
            {t("Back")}
          </button>
        )}
        <div id={`${id}-results`} role="listbox" aria-label={t("Search results")}>
          {visible.map((entry) => (
            <div key={entry.key} role="presentation" className="command-palette-row">
              <div
                id={`${id}-${entry.key}`}
                role="option"
                data-palette-key={entry.key}
                aria-selected={active === entry.key}
                className="command-palette-option"
                onClick={() => activate(entry)}
              >
                <span className="command-palette-icon" aria-hidden="true">
                  <PaletteIcon entry={entry} />
                </span>
                <span className="command-palette-copy">
                  <span
                    className="command-palette-title"
                    data-localization={
                      entry.target.kind === "record" ||
                      entry.target.kind === "saved_report" ||
                      entry.target.kind === "company"
                        ? "original"
                        : undefined
                    }
                  >
                    {entry.label}
                  </span>
                  {entry.secondary && (
                    <span className="command-palette-secondary" data-localization="original">
                      {entry.secondary}
                    </span>
                  )}
                </span>
                <span className="command-palette-kind">
                  {t(groupLabels[entry.group])}
                  <span>{t(entry.outcome)}</span>
                </span>
                <ArrowRight className="command-palette-open" aria-hidden="true" />
              </div>
              <button
                className="command-palette-pin"
                aria-label={`${t(preferences.pinned(entry.key) ? "Unpin" : "Pin")} ${entry.label}`}
                aria-pressed={preferences.pinned(entry.key)}
                onClick={() => preferences.pin(entry)}
              >
                <Star aria-hidden="true" />
              </button>
            </div>
          ))}
        </div>
        {!query.trim() && (
          <div className="flex gap-2">
            <button className="br-btn" onClick={() => setManage(!manage)}>
              {t(manage ? "Back" : "Favorites and recent")}
            </button>
            {manage && (
              <button className="br-btn" onClick={preferences.clearHistory}>
                {t("Clear history")}
              </button>
            )}
            {manage && (
              <button className="br-btn" onClick={preferences.clear}>
                {t("Clear shortcuts")}
              </button>
            )}
          </div>
        )}
        {!preferences.persistent && (
          <p role="status">{t("Shortcuts are available for this session only.")}</p>
        )}
        <p role="status" aria-live="polite" className="px-3 py-2 text-xs text-fg-muted">
          {visible.length
            ? `${visible.length} ${t("Search results")}`
            : Object.values(records.providers).some((state) => state.loading)
              ? ""
              : Object.values(records.providers).some((state) => state.error)
                ? t("Search incomplete")
                : filter === "records" && !query.trim()
                  ? t("Type a name or number above to search.")
                  : t("No matching records")}
        </p>
        {!expanded &&
          hiddenGroups.map((group) => (
            <button
              key={group}
              className="br-btn m-1"
              onClick={() => {
                setExpanded(group);
                setActive(null);
                setPage(0);
              }}
            >
              {t("Show all")} · {t(groupLabels[group as keyof typeof groupLabels])}
            </button>
          ))}
        {expanded && (
          <div className="flex gap-2">
            <button
              className="br-btn"
              disabled={!page}
              onClick={() => {
                setPage(page - 1);
                setActive(null);
              }}
            >
              {t("Previous")}
            </button>
            <button
              className="br-btn"
              disabled={
                matches.filter((entry) => entry.group === expanded).length <= (page + 1) * 50
              }
              onClick={() => {
                setPage(page + 1);
                setActive(null);
              }}
            >
              {t("Next")}
            </button>
          </div>
        )}
      </div>
      <div className="command-palette-footer">
        <span className="command-palette-keys" aria-hidden="true">
          <kbd>↑</kbd>
          <kbd>↓</kbd>
          <span>{t("Navigate")}</span>
          <kbd>↵</kbd>
          <span>{t("Open")}</span>
        </span>
        <div className="command-palette-utilities">
          {active && visible.find((entry) => entry.key === active)?.target.kind === "record" && (
            <button
              className="br-btn mt-2 mr-2"
              onClick={() => {
                const selected = visible.find((entry) => entry.key === active);
                if (selected?.target.kind !== "record") return;
                const { record_kind, id } = selected.target;
                close();
                window.dispatchEvent(
                  new CustomEvent("reality:open-chat", {
                    detail: {
                      kind: "record-search",
                      tenant: context.tenant,
                      prompt: query,
                      target: { kind: "record", record_kind, id },
                    },
                  }),
                );
                onLaunch();
              }}
            >
              {t("Ask about selected record")}
            </button>
          )}
          {query.trim() && (
            <button
              className="br-btn mt-2 mr-2"
              disabled={query.length > 4000}
              onClick={() => {
                close();
                window.dispatchEvent(
                  new CustomEvent("reality:open-chat", {
                    detail: { kind: "tool-capability", tenant: context.tenant, prompt: query },
                  }),
                );
                onLaunch();
              }}
            >
              {t("Ask in chat")}
            </button>
          )}
          <button
            className="br-btn mt-2"
            onClick={() => {
              close();
              context.navigate({
                ...paletteTargetSelection(context.selection, { kind: "page", id: "tools" }),
                q: query,
              });
              onLaunch();
            }}
          >
            {t("Browse all tools")}
          </button>
        </div>
      </div>
    </div>
  );
}

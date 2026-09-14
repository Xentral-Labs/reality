<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from "vue";
import { useData } from "vitepress";
import DataModelExplorer from "./DataModelExplorer.vue";

type Kind =
  "command" | "tool" | "view" | "projection" | "action" | "exception" | "event" | "workspace";

interface Parameter {
  name: string;
  depth?: number;
  type: string;
  required: boolean;
  description: string;
  default?: unknown;
  enum?: string[];
}

interface Guidance {
  purpose?: string;
  use_when?: string[];
  do_not_use_when?: string[];
  preconditions?: string[];
  refusals?: { code: string; description: string }[];
  verification_reads?: { name: string; proves: string }[];
  limitations?: string[];
}

interface ReadMode {
  query: string;
  mode: string;
  default?: boolean;
}

interface Entry {
  read_modes?: ReadMode[];
  id: string;
  kind: Kind;
  key: string;
  label: string;
  area: string;
  summary: string;
  links: string[];
  label_de?: string;
  resources?: string[];
  // command
  mode?: string;
  adapters?: string[];
  reads?: string[];
  writes?: string[];
  confirmation?: string;
  tools?: string[];
  synopses?: string[];
  events?: string[];
  actions?: string[];
  guidance?: Guidance;
  // tool
  access?: string;
  synopsis?: string;
  parameters?: Parameter[];
  command?: string | null;
  projections?: string[];
  // view / projection / action / workspace
  route?: string;
  view_kind?: string;
  projection?: string | null;
  workspaces?: string[];
  consumers?: string[];
  outputs?: string[];
  target_route?: string;
  prerequisites?: string[];
  views?: string[];
  // exception
  owner?: string;
  clears_through?: string;
  severity?: string;
  record_type?: string;
  authority?: string;
  causes?: { id: string; label: string; authority: string }[];
  // event
  producer?: string;
  subject?: string;
  invalidates?: string[];
}

interface Localized {
  en: string;
  de: string;
}

interface Resource {
  key: string;
  label: Localized;
  subtitle: Localized;
  description: Localized;
  synonyms: string[];
  tables: string[];
  lists: string[];
  actions: string[];
  reads: string[];
  exceptions: string[];
  tools: string[];
  events: string[];
  workspace_actions: string[];
}

interface ProcessStep {
  title: Localized;
  resource: string;
  actions: string[];
  tools: string[];
  lists: string[];
  exceptions: string[];
}

interface Process {
  key: string;
  label: Localized;
  summary: Localized;
  playbook?: string;
  steps: ProcessStep[];
}

interface Model {
  read_mode_definitions: Record<string, { label: Localized; description: Localized }>;
  dataModels: InstanceType<typeof DataModelExplorer>["$props"]["models"];
  areas: { key: string; label: Localized }[];
  resources: Resource[];
  processes: Process[];
  entries: Entry[];
}

type Tab = "resources" | "processes" | "model" | "technical";

type Locale = "en" | "de";

const KIND_ORDER: Kind[] = [
  "command",
  "tool",
  "view",
  "projection",
  "action",
  "exception",
  "event",
  "workspace",
];

const PAGE_OF_KIND: Record<Kind, string> = {
  command: "commands",
  tool: "commands",
  workspace: "views",
  view: "views",
  action: "views",
  projection: "views",
  exception: "exceptions",
  event: "events",
};

const copy: Record<Locale, Record<string, string>> = {
  en: {
    loading: "Loading the catalog…",
    tabResources: "Resources",
    tabProcesses: "Processes",
    tabModel: "Data model",
    tabTechnical: "Technical",
    searchResources: "Find an object, list, action or exception: order, invoice, Skonto, stock…",
    lists: "Lists",
    actionsOf: "Actions",
    lookups: "Look up",
    exceptionsOf: "Exceptions to clear",
    inProcesses: "Appears in processes",
    technical: "Underneath",
    tables: "Tables",
    eventsOf: "Events",
    agentToolsOf: "Agent tools without a command",
    alsoCalled: "Also called",
    readPlaybook: "Read the playbook",
    step: "Step",
    object: "Business object",
    check: "Check afterwards",
    canLeave: "Can leave behind",
    back: "Back to",
    backShort: "Back",
    pickLeft: "pick one on the left.",
    pickResource: "Choose a business object on the left.",
    pickProcess: "Choose a process on the left.",
    matching: "Matching entries",
    countLists: "lists",
    countActions: "actions",
    countExceptions: "exceptions",
    steps: "steps",
    resourceOf: "Belongs to",
    search: "Search like apropos: key, label, parameter, table, tool…",
    searchHint: "Press / to search",
    all: "All",
    list: "List",
    tree: "Tree",
    results: "entries",
    empty: "Nothing matches. Clear a filter or search for another word.",
    pick: "Choose an entry on the left to read its manual page.",
    name: "Name",
    synopsis: "Synopsis",
    description: "Description",
    parameters: "Parameters",
    noParameters: "No parameters.",
    reach: "Reach via",
    confirmation: "Confirmation",
    access: "Access",
    mode: "Mode",
    useWhen: "Use when",
    doNotUseWhen: "Do not use when",
    preconditions: "Preconditions",
    refusals: "Refused when",
    effect: "Effect",
    reads: "Reads",
    writes: "Writes",
    emits: "Emits",
    verify: "Verify with",
    limitations: "Limitations",
    seeAlso: "See also",
    manualPage: "Open the manual page",
    permalink: "Copy link",
    copied: "Copied",
    required: "required",
    optional: "optional",
    default: "default",
    oneOf: "one of",
    route: "Route",
    kind: "Kind",
    projection: "Projection",
    workspaces: "Workspaces",
    views: "Views",
    actions: "Actions",
    consumers: "Consumers",
    outputs: "Outputs",
    command: "Command",
    targetRoute: "Lands on",
    prerequisites: "Prerequisites",
    owner: "Owner",
    clearsThrough: "Clears through",
    severity: "Severity",
    recordType: "Record type",
    authority: "Specification",
    causes: "Causes",
    producer: "Produced by",
    subject: "Subject",
    invalidates: "Invalidates",
    byWorkspace: "By workspace",
    byArea: "By business area",
    answers: "Answers",
    kind_command: "Commands",
    kind_tool: "Agent tools",
    kind_view: "Views",
    kind_projection: "Projections",
    kind_action: "Actions",
    kind_exception: "Exceptions",
    kind_event: "Events",
    kind_workspace: "Workspaces",
    one_command: "command",
    one_tool: "agent tool",
    one_view: "view",
    one_projection: "projection",
    one_action: "action",
    one_exception: "exception",
    one_event: "event",
    one_workspace: "workspace",
  },
  de: {
    loading: "Katalog wird geladen…",
    tabResources: "Ressourcen",
    tabProcesses: "Prozesse",
    tabModel: "Datenmodell",
    tabTechnical: "Technik",
    searchResources:
      "Objekt, Liste, Aktion oder Klärfall finden: Auftrag, Rechnung, Skonto, Bestand…",
    lists: "Listen",
    actionsOf: "Aktionen",
    lookups: "Nachschlagen",
    exceptionsOf: "Klärfälle",
    inProcesses: "Kommt vor in",
    technical: "Darunter",
    tables: "Tabellen",
    eventsOf: "Events",
    agentToolsOf: "Agenten-Tools ohne Geschäftsaktion",
    alsoCalled: "Auch genannt",
    readPlaybook: "Playbook lesen",
    step: "Schritt",
    object: "Geschäftsobjekt",
    check: "Danach prüfen",
    canLeave: "Kann hinterlassen",
    back: "Zurück zu",
    backShort: "Zurück",
    pickLeft: "links eines auswählen.",
    pickResource: "Links ein Fachobjekt wählen.",
    pickProcess: "Links einen Prozess wählen.",
    matching: "Passende Einträge",
    countLists: "Listen",
    countActions: "Aktionen",
    countExceptions: "Klärfälle",
    steps: "Schritte",
    resourceOf: "Gehört zu",
    search: "Suchen wie apropos: Schlüssel, Bezeichnung, Parameter, Tabelle, Tool…",
    searchHint: "/ drücken zum Suchen",
    all: "Alle",
    list: "Liste",
    tree: "Baum",
    results: "Einträge",
    empty: "Nichts gefunden. Filter zurücksetzen oder ein anderes Wort suchen.",
    pick: "Links einen Eintrag wählen, um seine Handbuchseite zu lesen.",
    name: "Name",
    synopsis: "Aufruf",
    description: "Beschreibung",
    parameters: "Parameter",
    noParameters: "Keine Parameter.",
    reach: "Erreichbar über",
    confirmation: "Bestätigung",
    access: "Zugriff",
    mode: "Modus",
    useWhen: "Verwenden, wenn",
    doNotUseWhen: "Nicht verwenden, wenn",
    preconditions: "Voraussetzungen",
    refusals: "Abgelehnt, wenn",
    effect: "Wirkung",
    reads: "Liest",
    writes: "Schreibt",
    emits: "Erzeugt",
    verify: "Prüfen mit",
    limitations: "Grenzen",
    seeAlso: "Siehe auch",
    manualPage: "Handbuchseite öffnen",
    permalink: "Link kopieren",
    copied: "Kopiert",
    required: "Pflicht",
    optional: "optional",
    default: "Standard",
    oneOf: "einer von",
    route: "Route",
    kind: "Art",
    projection: "Projection",
    workspaces: "Arbeitsbereiche",
    views: "Sichten",
    actions: "Aktionen",
    consumers: "Verbraucher",
    outputs: "Ausgaben",
    command: "Geschäftsaktion",
    targetRoute: "Landet auf",
    prerequisites: "Voraussetzungen",
    owner: "Verantwortlich",
    clearsThrough: "Aufgelöst durch",
    severity: "Schwere",
    recordType: "Datensatztyp",
    authority: "Spezifikation",
    causes: "Ursachen",
    producer: "Erzeugt von",
    subject: "Subjekt",
    invalidates: "Invalidiert",
    byWorkspace: "Nach Arbeitsbereich",
    byArea: "Nach Geschäftsbereich",
    answers: "Beantwortet",
    kind_command: "Geschäftsaktionen",
    kind_tool: "Agenten-Tools",
    kind_view: "Sichten",
    kind_projection: "Projections",
    kind_action: "Aktionen",
    kind_exception: "Ausnahmen",
    kind_event: "Events",
    kind_workspace: "Arbeitsbereiche",
    one_command: "Geschäftsaktion",
    one_tool: "Agenten-Tool",
    one_view: "Sicht",
    one_projection: "Projection",
    one_action: "Aktion",
    one_exception: "Ausnahme",
    one_event: "Event",
    one_workspace: "Arbeitsbereich",
  },
};

const { lang } = useData();
const locale = computed<Locale>(() => (lang.value.startsWith("de") ? "de" : "en"));
const t = computed(() => copy[locale.value]);
const pagePrefix = computed(() => (locale.value === "de" ? "/de/tool-usage/" : "/tool-usage/"));

const model = shallowRef<Model | null>(null);
const query = ref("");
const kind = ref<Kind | "">("");
const area = ref("");
const mode = ref<"list" | "tree">("list");
const selectedId = ref("");
const tab = ref<Tab>("resources");
const selectedModel = ref("");
const selectedResource = ref("");
const selectedProcess = ref("");
const selectedStep = ref(-1);
const navDirection = ref<"forward" | "back">("forward");
const copied = ref(false);
const searchBox = ref<HTMLInputElement | null>(null);
const detailPane = ref<HTMLElement | null>(null);
const listPane = ref<HTMLElement | null>(null);

const byId = computed(() => new Map((model.value?.entries || []).map((e) => [e.id, e])));

const searchText = computed(() => {
  const index = new Map<string, string>();
  for (const e of model.value?.entries || []) {
    const bits = [
      e.key,
      e.label,
      e.label_de || "",
      e.summary,
      ...(e.read_modes || []).flatMap((read) => [
        read.query,
        ...Object.values(model.value!.read_mode_definitions[read.mode].label),
      ]),
      e.area,
      ...(e.parameters || []).map((p) => `${p.name} ${p.description}`),
      ...(e.tools || []),
      ...(e.reads || []),
      ...(e.writes || []),
      ...(e.synopses || []),
      e.synopsis || "",
      e.route || "",
      e.command || "",
      e.projection || "",
      e.producer || "",
      e.owner || "",
    ];
    index.set(e.id, bits.join(" ").toLowerCase());
  }
  return index;
});

const tokens = computed(() =>
  query.value
    .toLowerCase()
    .split(/\s+/u)
    .filter((x) => x.length > 0),
);

const matchesQuery = (e: Entry) => {
  if (tokens.value.length === 0) return true;
  const text = searchText.value.get(e.id) || "";
  return tokens.value.every((token) => text.includes(token));
};

const areaLabel = (key: string) =>
  model.value?.areas.find((a) => a.key === key)?.label[locale.value] || key;

const kindCounts = computed(() => {
  const counts = new Map<Kind, number>();
  for (const e of model.value?.entries || []) {
    if (!matchesQuery(e) || (area.value && e.area !== area.value)) continue;
    counts.set(e.kind, (counts.get(e.kind) || 0) + 1);
  }
  return counts;
});

const areaCounts = computed(() => {
  const counts = new Map<string, number>();
  for (const e of model.value?.entries || []) {
    if (!matchesQuery(e) || (kind.value && e.kind !== kind.value)) continue;
    counts.set(e.area, (counts.get(e.area) || 0) + 1);
  }
  return counts;
});

const results = computed(() =>
  (model.value?.entries || [])
    .filter(
      (e) =>
        matchesQuery(e) &&
        (!kind.value || e.kind === kind.value) &&
        (!area.value || e.area === area.value),
    )
    .sort(
      (left, right) =>
        KIND_ORDER.indexOf(left.kind) - KIND_ORDER.indexOf(right.kind) ||
        left.area.localeCompare(right.area) ||
        left.label.localeCompare(right.label),
    ),
);

const selected = computed(() => byId.value.get(selectedId.value) || null);

const entriesOf = (kindOf: Kind, keys: string[] | undefined) =>
  (keys || []).map((k) => byId.value.get(`${kindOf}:${k}`)).filter((e): e is Entry => Boolean(e));

const workspaces = computed(() =>
  (model.value?.entries || []).filter((e) => e.kind === "workspace"),
);

const areaTree = computed(() =>
  (model.value?.areas || [])
    .map((a) => ({
      key: a.key,
      label: a.label[locale.value],
      kinds: KIND_ORDER.map((k) => ({
        kind: k,
        entries: (model.value?.entries || []).filter(
          (e) => e.kind === k && e.area === a.key && e.kind !== "workspace" && matchesQuery(e),
        ),
      })).filter((group) => group.entries.length > 0),
    }))
    .filter((a) => a.kinds.length > 0),
);

const name = (e: Entry | undefined) =>
  e ? (locale.value === "de" && e.label_de ? e.label_de : e.label) : "";
const loc = (value: Localized | undefined) => (value ? value[locale.value] || value.en : "");

const resourceByKey = computed(
  () => new Map((model.value?.resources || []).map((r) => [r.key, r])),
);
const currentResource = computed(() => resourceByKey.value.get(selectedResource.value) || null);
const currentProcess = computed(
  () => (model.value?.processes || []).find((p) => p.key === selectedProcess.value) || null,
);

const resourceMatches = (r: Resource) => {
  if (tokens.value.length === 0) return true;
  const text = [
    r.key,
    r.label.en,
    r.label.de,
    r.subtitle.en,
    r.subtitle.de,
    r.description.en,
    r.description.de,
    ...r.synonyms,
    ...r.tables,
  ]
    .join(" ")
    .toLowerCase();
  return tokens.value.every((token) => text.includes(token));
};

const visibleResources = computed(() => (model.value?.resources || []).filter(resourceMatches));

// In the resources tab a search also surfaces the business entries themselves, in ERP words,
// so "Skonto" finds the exception and "Zahlungseingang" the action without knowing its key.
const businessMatches = computed(() =>
  tokens.value.length === 0
    ? []
    : (model.value?.entries || [])
        .filter(
          (e) => ["command", "view", "projection", "exception"].includes(e.kind) && matchesQuery(e),
        )
        .slice(0, 40),
);

const processesOf = (resourceKey: string) =>
  (model.value?.processes || []).filter((p) => p.steps.some((s) => s.resource === resourceKey));

const entryList = (ids: string[]) =>
  ids.map((id) => byId.value.get(id)).filter((e): e is Entry => Boolean(e));

const playbookUrl = (p: Process) =>
  `${locale.value === "de" ? "/de" : ""}/agent-playbooks/${p.playbook}`;

// Navigation. The hash is the full address of what is open, context first:
// "resource:order", "process:order_to_cash/command:reserve", "command:reserve" (technical view).
// Every step pushes a history entry, so the browser's Back button, the Back button in the
// breadcrumb and the Escape key all walk the same trail.
let pushed = 0;

const currentHash = () => {
  if (tab.value === "model") return `model:${selectedModel.value}`;
  if (tab.value === "resources" && selectedResource.value)
    return `resource:${selectedResource.value}` + (selectedId.value ? `/${selectedId.value}` : "");
  if (tab.value === "processes" && selectedProcess.value)
    return `process:${selectedProcess.value}` + (selectedId.value ? `/${selectedId.value}` : "");
  return selectedId.value;
};

// Every step is a history entry pushed with a null state. VitePress ignores popstate events
// whose state is null, so walking Back stays inside this component: no page reload, no remount.
// The entry we leave remembers where the page and the list were scrolled, keyed by its hash,
// so Back lands exactly where the reader clicked.
const scrollMemory = new Map<string, { page: number; list: number }>();

const locationKey = () =>
  typeof window === "undefined" ? "" : decodeURIComponent(window.location.hash.replace(/^#/u, ""));

const rememberScroll = () => {
  scrollMemory.set(locationKey(), {
    page: window.scrollY,
    list: listPane.value?.scrollTop || 0,
  });
  // The first entry belongs to VitePress; keep its scroll position current for its own restore.
  if (window.history.state !== null)
    window.history.replaceState({ ...window.history.state, scrollPosition: window.scrollY }, "");
};

const commit = () => {
  if (typeof window === "undefined") return;
  const next = currentHash();
  const url = next ? `#${next}` : window.location.pathname + window.location.search;
  if (locationKey() === next) return;
  rememberScroll();
  window.history.pushState(null, "", url);
  pushed += 1;
};

const restoreScroll = async () => {
  const remembered = scrollMemory.get(locationKey());
  if (!remembered) return;
  await nextTick();
  window.requestAnimationFrame(() => {
    window.scrollTo(0, remembered.page);
    if (listPane.value) listPane.value.scrollTop = remembered.list;
  });
};

// Going forward: show the top of what just opened. On a narrow screen the detail pane sits
// below the list; on a wide one it only needs a nudge when the reader clicked far down.
const scrollDetail = () => {
  if (typeof window === "undefined") return;
  const pane = detailPane.value;
  if (!pane) return;
  const top = pane.getBoundingClientRect().top;
  const navHeight = 64;
  if (window.innerWidth < 960 || top < navHeight) {
    window.scrollTo({ top: window.scrollY + top - navHeight - 8, behavior: "smooth" });
  }
};

const openResource = (key: string) => {
  navDirection.value = "forward";
  selectedStep.value = -1;
  tab.value = "resources";
  selectedResource.value = key;
  selectedId.value = "";
  copied.value = false;
  commit();
  scrollDetail();
};

const openProcess = (key: string) => {
  navDirection.value = "forward";
  selectedStep.value = -1;
  tab.value = "processes";
  selectedProcess.value = key;
  selectedId.value = "";
  copied.value = false;
  commit();
  scrollDetail();
};

const openModel = (key: string) => {
  tab.value = "model";
  selectedModel.value = key;
  selectedId.value = "";
  query.value = "";
  commit();
  void nextTick(() =>
    document.querySelector(".model-detail")?.scrollIntoView({ block: "start", behavior: "smooth" }),
  );
};

const openModelAction = (id: string) => {
  tab.value = "technical";
  query.value = "";
  select(id);
  void nextTick(scrollDetail);
};

const switchTab = (next: Tab) => {
  tab.value = next;
  selectedId.value = "";
  commit();
};

const select = (id: string) => {
  navDirection.value = "forward";
  selectedId.value = id;
  copied.value = false;
  commit();
  scrollDetail();
};

// Where "Back" leads without browser history: the context the open entry was reached from.
const contextTarget = computed(() => {
  const resource = currentResource.value;
  const process = currentProcess.value;
  if (tab.value === "resources" && resource)
    return { label: loc(resource.label), go: () => openResource(resource.key) };
  if (tab.value === "processes" && process)
    return { label: loc(process.label), go: () => openProcess(process.key) };
  return null;
});

const canGoBack = computed(() =>
  Boolean(selectedId.value || contextTarget.value || tab.value === "model"),
);

const goBack = () => {
  navDirection.value = "back";
  if (typeof window !== "undefined" && pushed > 0) {
    window.history.back();
    return;
  }
  if (selectedId.value && contextTarget.value) {
    contextTarget.value.go();
    return;
  }
  selectedId.value = "";
  if (tab.value === "model") {
    if (selectedModel.value) selectedModel.value = "";
    else tab.value = "resources";
  }
  if (tab.value === "resources") selectedResource.value = "";
  if (tab.value === "processes") selectedProcess.value = "";
  commit();
};

// The left column drills down with the reader: inside a resource it lists that resource's
// entries, inside a process its steps, each with a way up.
const resourceSections = computed(() => {
  const resource = currentResource.value;
  if (!resource) return [];
  return [
    { key: "lists", title: t.value.lists, entries: entryList(resource.lists) },
    { key: "actions", title: t.value.actionsOf, entries: entryList(resource.actions) },
    { key: "reads", title: t.value.lookups, entries: entryList(resource.reads) },
    { key: "exceptions", title: t.value.exceptionsOf, entries: entryList(resource.exceptions) },
  ]
    .map((section) => ({ ...section, entries: section.entries.filter(matchesQuery) }))
    .filter((section) => section.entries.length > 0);
});

const paneKey = computed(() => {
  if (selectedId.value) return selectedId.value;
  if (tab.value === "resources") return `r:${selectedResource.value}`;
  if (tab.value === "processes") return `p:${selectedProcess.value}`;
  return "technical";
});

const stepElementId = (index: number) => `tool-usage-step-${index + 1}`;

const jumpToStep = (index: number) => {
  selectedStep.value = index;
  if (selectedId.value) {
    selectedId.value = "";
    navDirection.value = "back";
    commit();
  }
  void nextTick(() => {
    const element = document.getElementById(stepElementId(index));
    if (!element) return;
    const top = element.getBoundingClientRect().top + window.scrollY - 64 - 12;
    window.scrollTo({ top, behavior: "smooth" });
  });
};

const selectFromStep = (index: number, id: string) => {
  selectedStep.value = index;
  select(id);
};

const goRoot = () => {
  selectedId.value = "";
  if (tab.value === "resources") selectedResource.value = "";
  if (tab.value === "processes") selectedProcess.value = "";
  commit();
};

const crumbs = computed(() => {
  const trail: { label: string; go?: () => void }[] = [
    {
      label: t.value["tab" + tab.value.charAt(0).toUpperCase() + tab.value.slice(1)],
      go: goRoot,
    },
  ];
  if (contextTarget.value) trail.push(contextTarget.value);
  if (selected.value) trail.push({ label: name(selected.value) });
  return trail;
});

const manualUrl = (e: Entry) =>
  `${pagePrefix.value}${PAGE_OF_KIND[e.kind]}#${e.kind}-${e.key.replace(/\./gu, "-")}`;

const copyLink = async () => {
  if (typeof window === "undefined" || !selected.value) return;
  const url = `${window.location.origin}${window.location.pathname}#${selected.value.id}`;
  try {
    await navigator.clipboard.writeText(url);
    copied.value = true;
  } catch {
    copied.value = false;
  }
};

const onKey = (event: KeyboardEvent) => {
  const target = event.target as HTMLElement | null;
  const typing = target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName);
  if (event.key === "/" && !typing) {
    event.preventDefault();
    searchBox.value?.focus();
  } else if (event.key === "Escape" && target === searchBox.value) {
    query.value = "";
  } else if (event.key === "Escape" && !typing && canGoBack.value) {
    goBack();
  }
};

const applyHash = () => {
  const hash = decodeURIComponent(window.location.hash.replace(/^#/u, ""));
  const [context, entry] = hash.includes("/") ? hash.split("/", 2) : ["", hash];
  const head = context || entry;
  selectedId.value = "";
  if (head.startsWith("model:")) {
    tab.value = "model";
    selectedModel.value = model.value?.dataModels.some((m) => m.key === head.slice(6))
      ? head.slice(6)
      : "";
  } else if (head.startsWith("resource:") && resourceByKey.value.has(head.slice(9))) {
    tab.value = "resources";
    selectedResource.value = head.slice(9);
    if (context && byId.value.has(entry)) selectedId.value = entry;
  } else if (head.startsWith("process:")) {
    tab.value = "processes";
    selectedProcess.value = head.slice(8);
    if (context && byId.value.has(entry)) selectedId.value = entry;
  } else if (entry && byId.value.has(entry)) {
    tab.value = "technical";
    selectedId.value = entry;
  } else if (!hash) {
    tab.value = "resources";
    selectedModel.value = "";
    selectedResource.value = "";
    selectedProcess.value = "";
  } else {
    // A plain page anchor below the explorer: the explorer grows after its data loads, so scroll
    // to the anchor again once the layout has settled.
    const target = document.getElementById(hash);
    if (target)
      void nextTick(() =>
        window.requestAnimationFrame(() =>
          window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - 64 - 12 }),
        ),
      );
  }
};

const onPop = () => {
  navDirection.value = "back";
  pushed = Math.max(0, pushed - 1);
  applyHash();
  void restoreScroll();
};

onMounted(async () => {
  const loaded = (await import("../../data/tool-usage.json")) as { default: Model } | Model;
  model.value = "default" in loaded ? loaded.default : (loaded as Model);
  // Take over the entry we start on as well, so a Back to it also stays inside the component.
  window.history.replaceState(null, "", window.location.href);
  applyHash();
  await nextTick();
  if (tab.value === "model" && selectedModel.value && !scrollMemory.has(locationKey()))
    document.querySelector(".model-detail")?.scrollIntoView({ block: "start" });
  void restoreScroll();
  window.addEventListener("keydown", onKey);
  window.addEventListener("popstate", onPop);
  window.addEventListener("hashchange", applyHash);
});

onBeforeUnmount(() => {
  if (typeof window === "undefined") return;
  window.removeEventListener("keydown", onKey);
  window.removeEventListener("popstate", onPop);
  window.removeEventListener("hashchange", applyHash);
});

const formatDefault = (value: unknown) =>
  typeof value === "string" ? value : JSON.stringify(value);
const explorerIntro = computed(() => {
  const titles =
    locale.value === "de"
      ? {
          resources: [
            "Geschäftsobjekte",
            "Listen, Aktionen und Klärfälle – nach Geschäftsobjekten geordnet.",
          ],
          processes: [
            "Geschäftsprozesse",
            "Geschäftliche Abläufe Schritt für Schritt – mit passenden Aktionen und Prüfungen.",
          ],
          model: [
            "Datenstrukturen",
            "Datensätze, Felder und Beziehungen – vom Stammsatz bis zur Buchung.",
          ],
          technical: [
            "Tools und Schnittstellen",
            "Kommandos, Agenten-Tools, Sichten und Events mit ihren Schnittstellen.",
          ],
        }
      : {
          resources: [
            "Business objects",
            "Lists, actions and exceptions, organised by business object.",
          ],
          processes: [
            "Business processes",
            "Business workflows, step by step, with the relevant actions and checks.",
          ],
          model: [
            "Data structures",
            "Records, fields and relationships, from master data to financial postings.",
          ],
          technical: [
            "Tools and interfaces",
            "Commands, agent tools, views and events with their interfaces.",
          ],
        };
  return titles[tab.value];
});
</script>

<template>
  <div class="tool-usage">
    <p v-if="!model" class="tool-usage-loading">{{ t.loading }}</p>

    <template v-else>
      <div class="tool-usage-tabs" role="tablist">
        <button
          v-for="item in ['resources', 'processes', 'model', 'technical'] as Tab[]"
          :key="item"
          type="button"
          role="tab"
          :aria-selected="tab === item"
          :class="{ active: tab === item }"
          @click="switchTab(item)"
        >
          {{ t["tab" + item.charAt(0).toUpperCase() + item.slice(1)] }}
        </button>
      </div>

      <header class="explorer-intro">
        <h2>{{ explorerIntro[0] }}</h2>
        <p>{{ explorerIntro[1] }}</p>
      </header>
      <div class="tool-usage-toolbar">
        <label class="tool-usage-search">
          <span class="visually-hidden">{{ t.search }}</span>
          <input
            ref="searchBox"
            v-model="query"
            type="search"
            :placeholder="
              tab === 'model'
                ? locale === 'de'
                  ? 'Baustein oder Feld finden: Commitment, due_at, Menge…'
                  : 'Find a record or field: Commitment, due_at, quantity…'
                : tab === 'technical'
                  ? t.search
                  : t.searchResources
            "
            autocomplete="off"
            spellcheck="false"
          />
          <kbd>/</kbd>
        </label>
        <div v-if="tab === 'technical'" class="tool-usage-modes" role="tablist">
          <button
            type="button"
            role="tab"
            :aria-selected="mode === 'list'"
            :class="{ active: mode === 'list' }"
            @click="mode = 'list'"
          >
            {{ t.list }}
          </button>
          <button
            type="button"
            role="tab"
            :aria-selected="mode === 'tree'"
            :class="{ active: mode === 'tree' }"
            @click="mode = 'tree'"
          >
            {{ t.tree }}
          </button>
        </div>
      </div>

      <div v-if="tab === 'technical'" class="tool-usage-chips" aria-label="kind">
        <button
          class="explorer-filter"
          type="button"
          :class="{ active: kind === '' }"
          @click="kind = ''"
        >
          {{ t.all }}
        </button>
        <button
          class="explorer-filter"
          v-for="k in KIND_ORDER"
          :key="k"
          type="button"
          :class="{ active: kind === k }"
          :disabled="!kindCounts.get(k)"
          @click="kind = kind === k ? '' : k"
        >
          {{ t["kind_" + k] }} <span class="count">{{ kindCounts.get(k) || 0 }}</span>
        </button>
      </div>

      <div v-if="tab === 'technical'" class="tool-usage-chips tool-usage-areas" aria-label="area">
        <button
          class="explorer-filter"
          type="button"
          :class="{ active: area === '' }"
          @click="area = ''"
        >
          {{ t.all }}
        </button>
        <button
          class="explorer-filter"
          v-for="a in model.areas"
          :key="a.key"
          type="button"
          :class="{ active: area === a.key }"
          :disabled="!areaCounts.get(a.key)"
          @click="area = area === a.key ? '' : a.key"
        >
          {{ a.label[locale] }} <span class="count">{{ areaCounts.get(a.key) || 0 }}</span>
        </button>
      </div>

      <DataModelExplorer
        v-if="tab === 'model'"
        :models="model.dataModels"
        :selected-key="selectedModel"
        :locale="locale"
        :query="query"
        :entries="model.entries"
        @select="openModel"
        @action="openModelAction"
      />
      <div v-else class="tool-usage-body">
        <section ref="listPane" class="tool-usage-list explorer-surface" aria-live="polite">
          <template v-if="tab === 'resources'">
            <template v-if="currentResource">
              <div class="drill-head">
                <button type="button" class="drill-up" @click="goRoot">
                  ← {{ t.tabResources }}
                </button>
                <strong>{{ loc(currentResource.label) }}</strong>
              </div>
              <p v-if="resourceSections.length === 0" class="tool-usage-empty">{{ t.empty }}</p>
              <template v-for="section in resourceSections" :key="section.key">
                <h3 class="tree-heading">{{ section.title }}</h3>
                <ul>
                  <li v-for="e in section.entries" :key="e.id">
                    <button
                      type="button"
                      :class="['tool-usage-row', { active: e.id === selectedId }]"
                      @click="select(e.id)"
                    >
                      <span
                        v-if="section.key !== 'actions'"
                        :class="['badge', 'badge-' + e.kind]"
                        >{{ t["one_" + e.kind] }}</span
                      >
                      <span class="row-name">{{ name(e) }}</span>
                      <code class="row-key">{{ e.key }}</code>
                      <span v-if="e.severity" class="row-area">{{ e.severity }}</span>
                    </button>
                  </li>
                </ul>
              </template>
            </template>
            <template v-else>
              <ul class="resource-cards">
                <li v-for="r in visibleResources" :key="r.key">
                  <button
                    type="button"
                    class="resource-card explorer-card"
                    @click="openResource(r.key)"
                  >
                    <strong>{{ loc(r.label) }}</strong>
                    <span class="resource-subtitle">{{ loc(r.subtitle) }}</span>
                    <span class="resource-counts">
                      {{ r.lists.length }} {{ t.countLists }} · {{ r.actions.length }}
                      {{ t.countActions }} · {{ r.exceptions.length }} {{ t.countExceptions }}
                    </span>
                  </button>
                </li>
              </ul>
              <p
                v-if="visibleResources.length === 0 && businessMatches.length === 0"
                class="tool-usage-empty"
              >
                {{ t.empty }}
              </p>
              <template v-if="businessMatches.length">
                <h3 class="tree-heading">{{ t.matching }}</h3>
                <ul>
                  <li v-for="e in businessMatches" :key="e.id">
                    <button
                      type="button"
                      :class="['tool-usage-row', { active: e.id === selectedId }]"
                      @click="select(e.id)"
                    >
                      <span :class="['badge', 'badge-' + e.kind]">{{ t["one_" + e.kind] }}</span>
                      <span class="row-name">{{ name(e) }}</span>
                      <code class="row-key">{{ e.key }}</code>
                    </button>
                  </li>
                </ul>
              </template>
            </template>
          </template>

          <template v-else-if="tab === 'processes'">
            <template v-if="currentProcess">
              <div class="drill-head">
                <button type="button" class="drill-up" @click="goRoot">
                  ← {{ t.tabProcesses }}
                </button>
                <strong>{{ loc(currentProcess.label) }}</strong>
              </div>
              <ol class="drill-steps">
                <li v-for="(step, index) in currentProcess.steps" :key="index">
                  <button
                    type="button"
                    :class="['tool-usage-row', { active: index === selectedStep }]"
                    @click="jumpToStep(index)"
                  >
                    <span class="step-no">{{ index + 1 }}</span>
                    <span class="row-name">{{ loc(step.title) }}</span>
                  </button>
                </li>
              </ol>
            </template>
            <ul v-else class="resource-cards">
              <li v-for="p in model.processes" :key="p.key">
                <button
                  type="button"
                  class="resource-card explorer-card"
                  @click="openProcess(p.key)"
                >
                  <strong>{{ loc(p.label) }}</strong>
                  <span class="resource-subtitle">{{ loc(p.summary) }}</span>
                  <span class="resource-counts">{{ p.steps.length }} {{ t.steps }}</span>
                </button>
              </li>
            </ul>
          </template>

          <template v-else-if="mode === 'list'">
            <p class="tool-usage-count">{{ results.length }} {{ t.results }}</p>
            <p v-if="results.length === 0" class="tool-usage-empty">{{ t.empty }}</p>
            <ul v-else>
              <li v-for="e in results" :key="e.id">
                <button
                  type="button"
                  :class="['tool-usage-row', { active: e.id === selectedId }]"
                  @click="select(e.id)"
                >
                  <span :class="['badge', 'badge-' + e.kind]">{{ t["one_" + e.kind] }}</span>
                  <code>{{ e.key }}</code>
                  <span class="row-label">{{ name(e) !== e.key ? name(e) : "" }}</span>
                  <span class="row-area">{{ areaLabel(e.area) }}</span>
                </button>
              </li>
            </ul>
          </template>

          <template v-else>
            <h3 class="tree-heading">{{ t.byWorkspace }}</h3>
            <ul class="tree">
              <li v-for="w in workspaces" :key="w.id">
                <button type="button" class="tree-node" @click="select(w.id)">
                  <span class="badge badge-workspace">{{ t.one_workspace }}</span>
                  <code>{{ w.key }}</code> {{ w.label }}
                </button>
                <ul>
                  <li v-for="v in entriesOf('view', w.views)" :key="v.id">
                    <button type="button" class="tree-node" @click="select(v.id)">
                      <span class="badge badge-view">{{ t.one_view }}</span>
                      <code>{{ v.key }}</code>
                    </button>
                    <ul v-if="v.projection">
                      <li>
                        <button
                          type="button"
                          class="tree-node"
                          @click="select('projection:' + v.projection)"
                        >
                          <span class="badge badge-projection">{{ t.one_projection }}</span>
                          <code>{{ v.projection }}</code>
                        </button>
                      </li>
                    </ul>
                  </li>
                  <li v-for="a in entriesOf('action', w.actions)" :key="a.id">
                    <button type="button" class="tree-node" @click="select(a.id)">
                      <span class="badge badge-action">{{ t.one_action }}</span>
                      <code>{{ a.key }}</code>
                    </button>
                    <ul v-if="a.command">
                      <li>
                        <button
                          type="button"
                          class="tree-node"
                          @click="select('command:' + a.command)"
                        >
                          <span class="badge badge-command">{{ t.one_command }}</span>
                          <code>{{ a.command }}</code>
                        </button>
                        <ul>
                          <li
                            v-for="tool in entriesOf(
                              'tool',
                              byId.get('command:' + a.command)?.tools,
                            )"
                            :key="tool.id"
                          >
                            <button type="button" class="tree-node" @click="select(tool.id)">
                              <span class="badge badge-tool">{{ t.one_tool }}</span>
                              <code>{{ tool.key }}</code>
                            </button>
                          </li>
                        </ul>
                      </li>
                    </ul>
                  </li>
                </ul>
              </li>
            </ul>

            <h3 class="tree-heading">{{ t.byArea }}</h3>
            <ul class="tree">
              <li v-for="a in areaTree" :key="a.key">
                <span class="tree-area">{{ a.label }}</span>
                <ul>
                  <li v-for="group in a.kinds" :key="group.kind">
                    <span class="tree-kind">{{ t["kind_" + group.kind] }}</span>
                    <ul>
                      <li v-for="e in group.entries" :key="e.id">
                        <button type="button" class="tree-node" @click="select(e.id)">
                          <code>{{ e.key }}</code>
                          <span class="row-label">{{ name(e) !== e.key ? name(e) : "" }}</span>
                        </button>
                      </li>
                    </ul>
                  </li>
                </ul>
              </li>
            </ul>
          </template>
        </section>

        <article ref="detailPane" class="tool-usage-detail explorer-panel">
          <nav v-if="canGoBack" class="man-crumbs" aria-label="breadcrumb">
            <button type="button" class="crumb-back" @click="goBack">
              ← {{ t.backShort }} <kbd>Esc</kbd>
            </button>
            <ol>
              <li v-for="(crumb, index) in crumbs" :key="index">
                <button
                  v-if="crumb.go && index < crumbs.length - 1"
                  type="button"
                  class="linkish"
                  @click="crumb.go()"
                >
                  {{ crumb.label }}
                </button>
                <span v-else>{{ crumb.label }}</span>
              </li>
            </ol>
          </nav>
          <Transition :name="navDirection === 'back' ? 'drill-back' : 'drill'">
            <div :key="paneKey" class="detail-body">
              <template v-if="selected">
                <header class="man-header">
                  <span class="man-section">
                    {{ t["one_" + selected.kind] }} · {{ areaLabel(selected.area) }}
                  </span>
                  <div class="man-actions">
                    <a :href="manualUrl(selected)">{{ t.manualPage }}</a>
                    <button type="button" @click="copyLink">
                      {{ copied ? t.copied : t.permalink }}
                    </button>
                  </div>
                </header>

                <p v-if="selected.resources?.length" class="man-resources">
                  {{ t.resourceOf }}:
                  <button
                    v-for="key in selected.resources"
                    :key="key"
                    type="button"
                    class="linkish"
                    @click="openResource(key)"
                  >
                    {{ loc(resourceByKey.get(key)?.label) }}
                  </button>
                </p>

                <h3 class="man-title">{{ t.name }}</h3>
                <p>
                  <code>{{ selected.key }}</code>
                  <template v-if="name(selected) !== selected.key">
                    — {{ name(selected) }}</template
                  >
                </p>

                <template v-if="selected.synopses?.length || selected.synopsis">
                  <h3 class="man-title">{{ t.synopsis }}</h3>
                  <pre
                    class="man-synopsis"
                  ><code>{{ (selected.synopses?.length ? selected.synopses : [selected.synopsis]).join("\n") }}</code></pre>
                </template>

                <template v-if="selected.summary || selected.guidance?.purpose">
                  <h3 class="man-title">{{ t.description }}</h3>
                  <p v-if="selected.summary">{{ selected.summary }}</p>
                  <p v-if="selected.guidance?.purpose">{{ selected.guidance.purpose }}</p>
                </template>

                <section
                  v-if="selected.read_modes?.length"
                  class="read-execution"
                  data-read-execution
                >
                  <h3 class="man-title">
                    {{
                      locale === "de" ? "So wird diese Abfrage ausgeführt" : "How this query runs"
                    }}
                  </h3>
                  <div v-for="read in selected.read_modes" :key="read.query">
                    <p>
                      <code>{{ read.query }}</code>
                    </p>
                    <p>
                      <strong>{{ loc(model!.read_mode_definitions[read.mode].label) }}</strong
                      ><template v-if="read.default">
                        · {{ locale === "de" ? "Standard" : "Default" }}</template
                      >
                    </p>
                    <p>{{ loc(model!.read_mode_definitions[read.mode].description) }}</p>
                  </div>
                  <p>
                    <a :href="`${locale === 'de' ? '/de' : ''}/tool-usage/views#read-execution`">{{
                      locale === "de"
                        ? "Aktualisierung, Datenstand und Abfragevarianten"
                        : "Refresh, freshness and query variants"
                    }}</a>
                  </p>
                </section>

                <dl class="man-facts">
                  <template v-if="selected.adapters?.length">
                    <dt>{{ t.reach }}</dt>
                    <dd>{{ selected.adapters.join(" · ") }}</dd>
                  </template>
                  <template v-if="selected.mode">
                    <dt>{{ t.mode }}</dt>
                    <dd>
                      <code>{{ selected.mode }}</code>
                    </dd>
                  </template>
                  <template v-if="selected.access">
                    <dt>{{ t.access }}</dt>
                    <dd>
                      <code>{{ selected.access }}</code>
                    </dd>
                  </template>
                  <template v-if="selected.confirmation">
                    <dt>{{ t.confirmation }}</dt>
                    <dd>
                      <code>{{ selected.confirmation }}</code>
                    </dd>
                  </template>
                  <template v-if="selected.route">
                    <dt>{{ t.route }}</dt>
                    <dd>
                      <code>{{ selected.route }}</code>
                    </dd>
                  </template>
                  <template v-if="selected.view_kind">
                    <dt>{{ t.kind }}</dt>
                    <dd>
                      <code>{{ selected.view_kind }}</code>
                    </dd>
                  </template>
                  <template v-if="selected.target_route">
                    <dt>{{ t.targetRoute }}</dt>
                    <dd>
                      <code>{{ selected.target_route }}</code>
                    </dd>
                  </template>
                  <template v-if="selected.prerequisites?.length">
                    <dt>{{ t.prerequisites }}</dt>
                    <dd>
                      <code v-for="p in selected.prerequisites" :key="p">{{ p }}</code>
                    </dd>
                  </template>
                  <template v-if="selected.consumers?.length">
                    <dt>{{ t.consumers }}</dt>
                    <dd>{{ selected.consumers.join(", ") }}</dd>
                  </template>
                  <template v-if="selected.outputs?.length">
                    <dt>{{ t.outputs }}</dt>
                    <dd>
                      <code v-for="o in selected.outputs" :key="o">{{ o }}</code>
                    </dd>
                  </template>
                  <template v-if="selected.owner">
                    <dt>{{ t.owner }}</dt>
                    <dd>{{ selected.owner }}</dd>
                  </template>
                  <template v-if="selected.clears_through">
                    <dt>{{ t.clearsThrough }}</dt>
                    <dd>{{ selected.clears_through }}</dd>
                  </template>
                  <template v-if="selected.severity">
                    <dt>{{ t.severity }}</dt>
                    <dd>
                      <code>{{ selected.severity }}</code>
                    </dd>
                  </template>
                  <template v-if="selected.record_type">
                    <dt>{{ t.recordType }}</dt>
                    <dd>
                      <code>{{ selected.record_type }}</code>
                    </dd>
                  </template>
                  <template v-if="selected.authority">
                    <dt>{{ t.authority }}</dt>
                    <dd>
                      <code>{{ selected.authority }}</code>
                    </dd>
                  </template>
                  <template v-if="selected.producer">
                    <dt>{{ t.producer }}</dt>
                    <dd>
                      <code>{{ selected.producer }}</code>
                    </dd>
                  </template>
                  <template v-if="selected.subject">
                    <dt>{{ t.subject }}</dt>
                    <dd>
                      <code>{{ selected.subject }}</code>
                    </dd>
                  </template>
                  <template v-if="selected.invalidates?.length">
                    <dt>{{ t.invalidates }}</dt>
                    <dd>
                      <code v-for="i in selected.invalidates" :key="i">{{ i }}</code>
                    </dd>
                  </template>
                </dl>

                <template v-if="selected.guidance?.use_when?.length">
                  <h3 class="man-title">{{ t.useWhen }}</h3>
                  <ul>
                    <li v-for="x in selected.guidance.use_when" :key="x">{{ x }}</li>
                  </ul>
                </template>
                <template v-if="selected.guidance?.do_not_use_when?.length">
                  <h3 class="man-title">{{ t.doNotUseWhen }}</h3>
                  <ul>
                    <li v-for="x in selected.guidance.do_not_use_when" :key="x">{{ x }}</li>
                  </ul>
                </template>
                <template v-if="selected.guidance?.preconditions?.length">
                  <h3 class="man-title">{{ t.preconditions }}</h3>
                  <ul>
                    <li v-for="x in selected.guidance.preconditions" :key="x">{{ x }}</li>
                  </ul>
                </template>
                <template v-if="selected.guidance?.refusals?.length">
                  <h3 class="man-title">{{ t.refusals }}</h3>
                  <ul>
                    <li v-for="r in selected.guidance.refusals" :key="r.code">
                      <code>{{ r.code }}</code> — {{ r.description }}
                    </li>
                  </ul>
                </template>

                <template v-if="selected.kind === 'command' || selected.kind === 'tool'">
                  <h3 class="man-title">{{ t.parameters }}</h3>
                  <template v-if="selected.kind === 'tool'">
                    <p v-if="!selected.parameters?.length">{{ t.noParameters }}</p>
                    <ul v-else class="man-params">
                      <li
                        v-for="p in selected.parameters"
                        :key="p.name"
                        :class="{ nested: p.depth }"
                        :style="{ paddingLeft: (p.depth || 0) * 16 + 'px' }"
                      >
                        <div class="param-head">
                          <code>{{ p.name }}</code>
                          <span class="param-type">{{ p.type }}</span>
                          <span :class="['param-required', { yes: p.required }]">
                            {{ p.required ? t.required : t.optional }}
                          </span>
                        </div>
                        <p v-if="p.description">{{ p.description }}</p>
                        <p v-if="p.enum" class="param-extra">
                          {{ t.oneOf }} <code v-for="v in p.enum" :key="v">{{ v }}</code>
                        </p>
                        <p v-if="'default' in p && p.default !== ''" class="param-extra">
                          {{ t.default }} <code>{{ formatDefault(p.default) }}</code>
                        </p>
                      </li>
                    </ul>
                  </template>
                  <template v-else>
                    <p v-if="!selected.tools?.length">{{ t.noParameters }}</p>
                    <div
                      v-for="tool in entriesOf('tool', selected.tools)"
                      :key="tool.id"
                      class="man-tool"
                    >
                      <p v-if="(selected.tools?.length || 0) > 1" class="man-tool-name">
                        <button type="button" class="linkish" @click="select(tool.id)">
                          <code>{{ tool.key }}</code>
                        </button>
                      </p>
                      <p v-if="!tool.parameters?.length">{{ t.noParameters }}</p>
                      <ul v-else class="man-params">
                        <li
                          v-for="p in tool.parameters"
                          :key="p.name"
                          :class="{ nested: p.depth }"
                          :style="{ paddingLeft: (p.depth || 0) * 16 + 'px' }"
                        >
                          <div class="param-head">
                            <code>{{ p.name }}</code>
                            <span class="param-type">{{ p.type }}</span>
                            <span :class="['param-required', { yes: p.required }]">
                              {{ p.required ? t.required : t.optional }}
                            </span>
                          </div>
                          <p v-if="p.description">{{ p.description }}</p>
                          <p v-if="p.enum" class="param-extra">
                            {{ t.oneOf }} <code v-for="v in p.enum" :key="v">{{ v }}</code>
                          </p>
                          <p v-if="'default' in p && p.default !== ''" class="param-extra">
                            {{ t.default }} <code>{{ formatDefault(p.default) }}</code>
                          </p>
                        </li>
                      </ul>
                    </div>
                  </template>
                </template>

                <template
                  v-if="
                    selected.reads?.length || selected.writes?.length || selected.events?.length
                  "
                >
                  <h3 class="man-title">{{ t.effect }}</h3>
                  <dl class="man-facts">
                    <template v-if="selected.reads?.length">
                      <dt>{{ t.reads }}</dt>
                      <dd>
                        <code v-for="r in selected.reads" :key="r">{{ r }}</code>
                      </dd>
                    </template>
                    <template v-if="selected.writes?.length">
                      <dt>{{ t.writes }}</dt>
                      <dd>
                        <code v-for="w in selected.writes" :key="w">{{ w }}</code>
                      </dd>
                    </template>
                    <template v-if="selected.events?.length">
                      <dt>{{ t.emits }}</dt>
                      <dd>
                        <button
                          v-for="ev in selected.events"
                          :key="ev"
                          type="button"
                          class="linkish"
                          @click="select('event:' + ev)"
                        >
                          <code>{{ ev }}</code>
                        </button>
                      </dd>
                    </template>
                  </dl>
                </template>

                <template v-if="selected.guidance?.verification_reads?.length">
                  <h3 class="man-title">{{ t.verify }}</h3>
                  <ul>
                    <li v-for="r in selected.guidance.verification_reads" :key="r.name">
                      <button
                        v-if="byId.has('projection:' + r.name)"
                        type="button"
                        class="linkish"
                        @click="select('projection:' + r.name)"
                      >
                        <code>{{ r.name }}</code>
                      </button>
                      <code v-else>{{ r.name }}</code>
                      — {{ r.proves }}
                    </li>
                  </ul>
                </template>

                <template v-if="selected.guidance?.limitations?.length">
                  <h3 class="man-title">{{ t.limitations }}</h3>
                  <ul>
                    <li v-for="x in selected.guidance.limitations" :key="x">{{ x }}</li>
                  </ul>
                </template>

                <template v-if="selected.causes?.length">
                  <h3 class="man-title">{{ t.causes }}</h3>
                  <ul>
                    <li v-for="c in selected.causes" :key="c.id">
                      <code>{{ c.id }}</code> — {{ c.label }} (<code>{{ c.authority }}</code
                      >)
                    </li>
                  </ul>
                </template>

                <template v-if="selected.links.length">
                  <h3 class="man-title">{{ t.seeAlso }}</h3>
                  <ul class="man-links">
                    <li v-for="id in selected.links" :key="id">
                      <button type="button" class="tool-usage-row compact" @click="select(id)">
                        <span :class="['badge', 'badge-' + byId.get(id)?.kind]">
                          {{ t["one_" + byId.get(id)?.kind] }}
                        </span>
                        <code>{{ byId.get(id)?.key }}</code>
                        <span class="row-label">
                          {{ name(byId.get(id)) !== byId.get(id)?.key ? name(byId.get(id)) : "" }}
                        </span>
                      </button>
                    </li>
                  </ul>
                </template>
              </template>

              <template v-else-if="tab === 'resources'">
                <p v-if="!currentResource" class="tool-usage-empty">{{ t.pickResource }}</p>
                <template v-else>
                  <header class="resource-header">
                    <span class="man-section">{{ t.object }}</span>
                    <h3 class="resource-title">{{ loc(currentResource.label) }}</h3>
                    <p class="resource-subtitle">{{ loc(currentResource.subtitle) }}</p>
                  </header>
                  <p>{{ loc(currentResource.description) }}</p>
                  <p v-if="currentResource.synonyms.length" class="resource-synonyms">
                    {{ t.alsoCalled }}: {{ currentResource.synonyms.join(", ") }}
                  </p>

                  <p class="resource-counts resource-hint">
                    {{ currentResource.lists.length }} {{ t.countLists }} ·
                    {{ currentResource.actions.length }} {{ t.countActions }} ·
                    {{ currentResource.exceptions.length }} {{ t.countExceptions }} —
                    {{ t.pickLeft }}
                  </p>

                  <template v-if="processesOf(currentResource.key).length">
                    <h3 class="man-title">{{ t.inProcesses }}</h3>
                    <ul class="business-list">
                      <li v-for="p in processesOf(currentResource.key)" :key="p.key">
                        <button type="button" class="tool-usage-row" @click="openProcess(p.key)">
                          <span class="badge badge-process">{{ t.tabProcesses }}</span>
                          <span class="row-name">{{ loc(p.label) }}</span>
                        </button>
                      </li>
                    </ul>
                  </template>

                  <details class="resource-technical">
                    <summary>{{ t.technical }}</summary>
                    <dl class="man-facts">
                      <template v-if="currentResource.tables.length">
                        <dt>{{ t.tables }}</dt>
                        <dd>
                          <code v-for="x in currentResource.tables" :key="x">{{ x }}</code>
                        </dd>
                      </template>
                      <template v-if="currentResource.events.length">
                        <dt>{{ t.eventsOf }}</dt>
                        <dd>
                          <button
                            v-for="e in entryList(currentResource.events)"
                            :key="e.id"
                            type="button"
                            class="linkish"
                            @click="select(e.id)"
                          >
                            <code>{{ e.key }}</code>
                          </button>
                        </dd>
                      </template>
                      <template v-if="currentResource.tools.length">
                        <dt>{{ t.agentToolsOf }}</dt>
                        <dd>
                          <button
                            v-for="e in entryList(currentResource.tools)"
                            :key="e.id"
                            type="button"
                            class="linkish"
                            @click="select(e.id)"
                          >
                            <code>{{ e.key }}</code>
                          </button>
                        </dd>
                      </template>
                    </dl>
                  </details>
                </template>
              </template>

              <template v-else-if="tab === 'processes'">
                <p v-if="!currentProcess" class="tool-usage-empty">{{ t.pickProcess }}</p>
                <template v-else>
                  <header class="resource-header">
                    <span class="man-section">{{ t.tabProcesses }}</span>
                    <h3 class="resource-title">{{ loc(currentProcess.label) }}</h3>
                    <p class="resource-subtitle">{{ loc(currentProcess.summary) }}</p>
                  </header>
                  <p v-if="currentProcess.playbook">
                    <a :href="playbookUrl(currentProcess)">{{ t.readPlaybook }}</a>
                  </p>
                  <ol class="process-steps">
                    <li
                      v-for="(step, index) in currentProcess.steps"
                      :id="stepElementId(index)"
                      :key="index"
                      :class="{ 'step-current': index === selectedStep }"
                    >
                      <h4 class="step-title">{{ loc(step.title) }}</h4>
                      <p v-if="resourceByKey.get(step.resource)" class="step-object">
                        {{ t.object }}:
                        <button type="button" class="linkish" @click="openResource(step.resource)">
                          {{ loc(resourceByKey.get(step.resource)!.label) }}
                        </button>
                      </p>
                      <ul v-if="step.actions.length || step.tools.length" class="business-list">
                        <li v-for="e in entryList([...step.actions, ...step.tools])" :key="e.id">
                          <button
                            type="button"
                            class="tool-usage-row"
                            @click="selectFromStep(index, e.id)"
                          >
                            <span :class="['badge', 'badge-' + e.kind]">{{
                              t["one_" + e.kind]
                            }}</span>
                            <span class="row-name">{{ name(e) }}</span>
                            <code class="row-key">{{ e.key }}</code>
                          </button>
                        </li>
                      </ul>
                      <p v-if="step.lists.length" class="step-line">
                        <span class="step-label">{{ t.check }}:</span>
                        <button
                          v-for="e in entryList(step.lists)"
                          :key="e.id"
                          type="button"
                          class="linkish"
                          @click="selectFromStep(index, e.id)"
                        >
                          {{ name(e) }}
                        </button>
                      </p>
                      <p v-if="step.exceptions.length" class="step-line">
                        <span class="step-label">{{ t.canLeave }}:</span>
                        <button
                          v-for="e in entryList(step.exceptions)"
                          :key="e.id"
                          type="button"
                          class="linkish warn"
                          @click="selectFromStep(index, e.id)"
                        >
                          {{ name(e) }}
                        </button>
                      </p>
                    </li>
                  </ol>
                </template>
              </template>

              <p v-else class="tool-usage-empty">{{ t.pick }}</p>
            </div>
          </Transition>
        </article>
      </div>
    </template>
  </div>
</template>

<style scoped>
.tool-usage {
  margin: 24px 0;
  max-width: 100%;
}

.tool-usage-loading,
.tool-usage-empty,
.tool-usage-count {
  color: var(--vp-c-text-2);
  font-size: 14px;
}

.tool-usage-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.tool-usage-search {
  flex: 1 1 320px;
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  padding: 0 10px 0 12px;
  background: var(--vp-c-bg);
}

.tool-usage-search:focus-within {
  border-color: var(--vp-c-brand-1);
}

.tool-usage-search input {
  flex: 1;
  min-width: 0;
  border: 0;
  background: transparent;
  padding: 10px 0;
  font: inherit;
  color: var(--vp-c-text-1);
  outline: none;
}

.tool-usage-search kbd {
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  padding: 1px 6px;
  font-size: 12px;
  color: var(--vp-c-text-2);
  font-family: var(--vp-font-family-mono);
}

.tool-usage-modes {
  display: inline-flex;
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  overflow: hidden;
}

.tool-usage-modes button {
  padding: 8px 14px;
  font: inherit;
  font-size: 14px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-2);
  border: 0;
  cursor: pointer;
}

.tool-usage-modes button.active {
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
  font-weight: 600;
}

.tool-usage-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.tool-usage-chips button:disabled {
  opacity: 0.4;
  cursor: default;
}

.tool-usage-chips .count {
  color: var(--vp-c-text-2);
  font-size: 12px;
  margin-left: 2px;
}

.tool-usage {
  container-type: inline-size;
}

.tool-usage-body {
  display: grid;
  grid-template-columns: minmax(0, 5fr) minmax(0, 7fr);
  gap: 20px;
  margin-top: 18px;
  align-items: start;
}

@media (max-width: 959px) {
  .tool-usage-body {
    grid-template-columns: minmax(0, 1fr);
  }
}

@container (max-width: 820px) {
  .tool-usage-body {
    grid-template-columns: minmax(0, 1fr);
  }
}

.tool-usage-list {
  max-height: 72vh;
  overflow: auto;
}

.tool-usage-list ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.tool-usage-list ul ul {
  padding-left: 18px;
  border-left: 1px solid var(--vp-c-divider);
  margin-left: 8px;
}

.tool-usage-list li {
  margin: 0;
}

.tool-usage-row,
.tree-node {
  width: 100%;
  display: flex;
  align-items: baseline;
  gap: 8px;
  text-align: left;
  padding: 6px 8px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--vp-c-text-1);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
  min-width: 0;
}

/* Separate the business name from its technical key without truncating either. */
.tool-usage-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) fit-content(8rem);
  align-items: start;
  gap: 2px 12px;
  padding: 10px 12px;
  line-height: 1.5;
}

.tool-usage-row > .row-name,
.tool-usage-row > .row-label {
  grid-column: 1;
  grid-row: 1;
  font-weight: 600;
  font-size: 14px;
  color: var(--vp-c-text-1);
}

.tool-usage-row > code {
  grid-column: 1 / -1;
  grid-row: 2;
  max-width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
}

.tool-usage-row > .badge {
  grid-column: 2;
  grid-row: 1;
  justify-self: end;
  border: 1px solid currentColor;
  padding: 0 5px;
  min-width: 0;
  max-width: 8rem;
  text-align: center;
  white-space: normal;
  overflow-wrap: anywhere;
  font-size: 10px;
  line-height: 1.6;
}

.tool-usage-row > .row-area {
  grid-column: 1 / -1;
}

.tool-usage-list li + li:has(> .tool-usage-row),
.business-list li + li,
.man-links li + li {
  border-top: 1px solid var(--vp-c-divider);
}

.drill-steps .tool-usage-row {
  display: flex;
}

.tool-usage-row:hover,
.tree-node:hover {
  background: var(--vp-c-default-soft);
  box-shadow: inset 3px 0 var(--vp-c-brand-1);
}

.tool-usage-row.active {
  box-shadow: inset 3px 0 var(--vp-c-brand-1);
  background: var(--vp-c-brand-soft);
}

.tool-usage-row code,
.tree-node code,
.man-links code {
  font-size: 12.5px;
  padding: 0;
  background: transparent;
  color: var(--vp-c-text-1);
  white-space: normal;
  overflow-wrap: anywhere;
}

.tool-usage-row.active code {
  color: var(--vp-c-brand-1);
}

.row-label {
  flex: 1 1 auto;
  min-width: 0;
  color: var(--vp-c-text-2);
  white-space: normal;
  overflow-wrap: anywhere;
}

.row-area {
  flex: 0 0 auto;
  color: var(--vp-c-text-3, var(--vp-c-text-2));
  font-size: 11px;
}

@media (max-width: 600px) {
  .row-area {
    display: none;
  }
}

.badge {
  flex: 0 0 auto;
  font-size: 10px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 1px 6px;
  border-radius: 6px;
  border: 1px solid var(--vp-c-divider);
  color: var(--vp-c-text-2);
  min-width: 64px;
  text-align: center;
}

.badge-command {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}

.badge-tool {
  border-color: var(--vp-c-green-1, #2f9e44);
  color: var(--vp-c-green-1, #2f9e44);
}

.badge-exception {
  border-color: var(--vp-c-red-1, #c92a2a);
  color: var(--vp-c-red-1, #c92a2a);
}

.badge-view,
.badge-projection,
.badge-workspace {
  border-color: var(--vp-c-indigo-1, #4263eb);
  color: var(--vp-c-indigo-1, #4263eb);
}

.badge-action,
.badge-event {
  border-color: var(--vp-c-yellow-1, #b8860b);
  color: var(--vp-c-yellow-1, #b8860b);
}

.tree-heading {
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--vp-c-text-2);
  margin: 8px 8px 4px;
  border: 0;
  padding: 0;
}

.tree-heading + .tree {
  margin-bottom: 16px;
}

.tree-area,
.tree-kind {
  display: block;
  padding: 6px 8px 2px;
  font-size: 13px;
  font-weight: 600;
}

.tree-kind {
  font-weight: 500;
  color: var(--vp-c-text-2);
  font-size: 12px;
}

.tool-usage-detail {
  min-width: 0;
  overflow-wrap: anywhere;
}

.man-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
  font-size: 12px;
  color: var(--vp-c-text-2);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.man-actions {
  display: flex;
  gap: 12px;
  text-transform: none;
  letter-spacing: 0;
}

.man-actions a,
.man-actions button,
.linkish {
  font: inherit;
  font-size: 13px;
  color: var(--vp-c-brand-1);
  background: transparent;
  border: 0;
  padding: 0;
  cursor: pointer;
  text-decoration: none;
}

.man-actions a:hover,
.man-actions button:hover,
.linkish:hover {
  text-decoration: underline;
}

.linkish code {
  color: var(--vp-c-brand-1);
  background: transparent;
  padding: 0;
}

.man-title {
  margin: 18px 0 6px;
  padding: 0;
  border: 0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--vp-c-text-2);
}

.man-title:first-of-type {
  margin-top: 12px;
}

.tool-usage-detail p {
  margin: 4px 0;
  line-height: 1.55;
}

.tool-usage-detail ul {
  margin: 4px 0;
  padding-left: 20px;
}

.man-synopsis {
  margin: 4px 0;
  padding: 10px 14px;
  border-radius: 8px;
  background: var(--vp-code-block-bg, var(--vp-c-bg-alt));
  overflow-x: auto;
  max-width: 100%;
}

.man-synopsis code {
  font-size: 13px;
  background: transparent;
  padding: 0;
  color: var(--vp-c-text-1);
  white-space: pre;
}

.man-facts {
  display: grid;
  grid-template-columns: max-content minmax(0, 1fr);
  gap: 4px 16px;
  margin: 8px 0 0;
  font-size: 14px;
}

.man-facts dt {
  color: var(--vp-c-text-2);
}

.man-facts dd {
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 4px 6px;
  align-items: baseline;
}

.man-params {
  list-style: none;
  padding: 0;
  margin: 0;
}

.man-params li {
  padding: 8px 0;
  border-top: 1px solid var(--vp-c-divider);
}

.man-params li:first-child {
  border-top: 0;
}

.man-params li.nested {
  border-top-style: dashed;
}

.param-head {
  display: flex;
  gap: 10px;
  align-items: baseline;
  flex-wrap: wrap;
}

.param-type {
  font-family: var(--vp-font-family-mono);
  font-size: 12px;
  color: var(--vp-c-text-2);
}

.param-required {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--vp-c-text-3, var(--vp-c-text-2));
}

.param-required.yes {
  color: var(--vp-c-brand-1);
  font-weight: 600;
}

.param-extra {
  color: var(--vp-c-text-2);
  font-size: 13px;
}

.man-tool {
  margin-top: 8px;
}

.man-tool-name {
  font-weight: 600;
}

.man-links {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tool-usage-row.compact {
  padding: 4px 6px;
}

.tool-usage-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  border-bottom: 1px solid var(--vp-c-divider);
  margin-bottom: 14px;
}

.tool-usage-tabs button {
  padding: 10px 16px;
  font: inherit;
  font-size: 15px;
  font-weight: 600;
  background: transparent;
  color: var(--vp-c-text-2);
  border: 0;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  cursor: pointer;
}

.tool-usage-tabs button.active {
  color: var(--vp-c-brand-1);
  border-bottom-color: var(--vp-c-brand-1);
}

.resource-cards {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.resource-subtitle {
  color: var(--vp-c-text-2);
  font-size: 13px;
}

.resource-counts {
  color: var(--vp-c-text-3, var(--vp-c-text-2));
  font-size: 12px;
}

.resource-header {
  margin-bottom: 8px;
}

.resource-title {
  margin: 2px 0 0;
  padding: 0;
  border: 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.resource-header .resource-subtitle {
  margin: 2px 0 0;
  font-size: 14px;
}

.resource-synonyms {
  color: var(--vp-c-text-2);
  font-size: 13px;
}

.business-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.tool-usage-detail .business-list {
  padding-left: 0;
}

.row-name {
  flex: 0 1 auto;
  min-width: 0;
  white-space: normal;
  overflow-wrap: anywhere;
}

.row-key {
  flex: 1 1 auto;
  min-width: 0;
  color: var(--vp-c-text-2) !important;
  font-size: 11.5px !important;
  white-space: normal;
  overflow-wrap: anywhere;
}

.badge-process {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}

.resource-technical {
  margin-top: 18px;
  border-top: 1px solid var(--vp-c-divider);
  padding-top: 10px;
}

.resource-technical summary {
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--vp-c-text-2);
}

.process-steps {
  margin: 8px 0 0;
  padding-left: 22px;
}

.process-steps > li {
  margin: 0 0 16px;
  padding-left: 4px;
}

.step-title {
  margin: 0;
  padding: 0;
  border: 0;
  font-size: 15px;
  font-weight: 600;
}

.step-object,
.step-line {
  font-size: 13px;
  color: var(--vp-c-text-2);
}

.step-line .linkish {
  margin-right: 10px;
}

.step-label {
  margin-right: 6px;
}

.linkish.warn {
  color: var(--vp-c-red-1, #c92a2a);
}

.man-crumbs {
  position: sticky;
  top: calc(var(--vp-nav-height, 64px) + 8px);
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 12px;
  margin: -20px -20px 12px;
  padding: 10px 20px;
  background: var(--vp-c-bg);
  border-bottom: 1px solid var(--vp-c-divider);
  border-radius: 12px 12px 0 0;
  font-size: 13px;
}

.crumb-back {
  flex: 0 0 auto;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 4px 10px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-1);
  cursor: pointer;
}

.crumb-back:hover {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}

.man-crumbs ol {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 2px 6px;
  list-style: none;
  margin: 0;
  padding: 0;
  min-width: 0;
  line-height: 20px;
}

.man-crumbs li {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  color: var(--vp-c-text-2);
  line-height: 20px;
}

.man-crumbs li + li::before {
  content: "›";
  color: var(--vp-c-text-3, var(--vp-c-text-2));
}

.man-crumbs li:last-child span {
  color: var(--vp-c-text-1);
  font-weight: 600;
}

.man-crumbs li > span,
.man-crumbs li > .linkish {
  display: inline;
  margin: 0;
  padding: 0;
  font: inherit;
  font-size: 13px;
  line-height: 20px;
  vertical-align: baseline;
}

.man-crumbs li > .linkish {
  color: var(--vp-c-brand-1);
}

.man-resources {
  font-size: 13px;
  color: var(--vp-c-text-2);
}

.man-resources .linkish {
  margin-right: 8px;
}

.drill-head {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  padding: 2px 4px 12px;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--vp-c-divider);
}

.drill-head strong {
  font-size: 17px;
  line-height: 1.3;
  padding-left: 4px;
}

.drill-up {
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 6px 12px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  cursor: pointer;
}

.drill-up:hover {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}

.drill-steps {
  list-style: none;
  margin: 0;
  padding: 0;
}

.step-no {
  flex: 0 0 22px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1px solid var(--vp-c-divider);
  font-size: 11px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--vp-c-text-2);
  align-self: center;
}

.tool-usage-row.active .step-no {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}

.step-current {
  border-left: 2px solid var(--vp-c-brand-1);
  margin-left: -10px;
  padding-left: 12px !important;
}

.resource-hint {
  margin-top: 6px;
}

.crumb-back kbd {
  margin-left: 6px;
  padding: 0 5px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 5px;
  font-family: var(--vp-font-family-mono);
  font-size: 11px;
  font-weight: 500;
  color: var(--vp-c-text-2);
  background: var(--vp-c-bg);
}

@media (max-width: 600px) {
  .crumb-back kbd {
    display: none;
  }
}

.detail-body {
  min-width: 0;
}

.drill-enter-active,
.drill-back-enter-active {
  transition:
    opacity 0.16s ease-out,
    transform 0.16s ease-out;
}

.drill-enter-from {
  opacity: 0;
  transform: translateX(10px);
}

.drill-back-enter-from {
  opacity: 0;
  transform: translateX(-10px);
}

.drill-leave-active,
.drill-back-leave-active {
  display: none;
}

@media (prefers-reduced-motion: reduce) {
  .drill-enter-active,
  .drill-back-enter-active {
    transition: none;
  }
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

.tool-usage button:focus-visible,
.tool-usage input:focus-visible,
.tool-usage a:focus-visible {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: 2px;
}
</style>

<style scoped>
.read-execution code {
  overflow-wrap: anywhere;
  white-space: normal;
}
.read-execution > div + div {
  margin-top: 1.5rem;
}
</style>

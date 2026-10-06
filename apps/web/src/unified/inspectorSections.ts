export const inspectorSections = [
  { label: "Business Recorder", tabs: ["overview", "graph"] },
  { label: "Business Facts", tabs: ["facts", "rules"] },
  { label: "Activities", tabs: ["history", "live", "business"] },
  { label: "Tools", tabs: ["commands", "views"] },
];
const labels: Record<string, string> = {
  overview: "Timeline",
  graph: "Record graph",
  facts: "All records",
  rules: "Fact rules",
  exceptions: "Exception rules",
  views: "Calculated views",
  history: "History",
  live: "Live",
  business: "Business",
  commands: "Actions",
};
export const inspectorSection = (view = "overview") =>
  inspectorSections.find((section) => section.tabs.includes(view === "records" ? "facts" : view)) ||
  inspectorSections[0];
/** The engine room (spec 266) is for company owners only. */
export const inspectorTabs = (view: string, owner = true) =>
  ["commands", "views"].includes(view)
    ? [["commands", "Tools"] as const]
    : inspectorSection(view)
        .tabs.filter((key) => owner || !["live", "business"].includes(key))
        .map((key) => [key, labels[key]] as const);

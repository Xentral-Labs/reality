export const inspectorSections = [
  { label: "Context Graph", tabs: ["overview", "graph"] },
  { label: "Facts", tabs: ["facts", "views"] },
  { label: "Rules", tabs: ["rules", "exceptions"] },
  { label: "Actions", tabs: ["history", "commands"] },
];
const labels: Record<string, string> = {
  overview: "Timeline",
  graph: "Record graph",
  facts: "All records",
  rules: "Fact rules",
  exceptions: "Exception rules",
  views: "Calculated views",
  history: "Event history",
  commands: "Action catalog",
};
export const inspectorSection = (view = "overview") =>
  inspectorSections.find((section) => section.tabs.includes(view === "records" ? "facts" : view)) ||
  inspectorSections[0];
export const inspectorTabs = (view: string) =>
  inspectorSection(view).tabs.map((key) => [key, labels[key]] as const);

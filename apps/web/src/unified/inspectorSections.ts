export const inspectorSections = [
  { label: "Business Graph", tabs: ["overview", "graph"] },
  { label: "Business Facts", tabs: ["facts", "rules"] },
  { label: "Activities", tabs: ["history"] },
  { label: "Tools", tabs: ["commands", "views"] },
];
const labels: Record<string, string> = {
  overview: "Timeline",
  graph: "Record graph",
  facts: "All records",
  rules: "Fact rules",
  exceptions: "Exception rules",
  views: "Calculated views",
  history: "Activities",
  commands: "Actions",
};
export const inspectorSection = (view = "overview") =>
  inspectorSections.find((section) => section.tabs.includes(view === "records" ? "facts" : view)) ||
  inspectorSections[0];
export const inspectorTabs = (view: string) =>
  ["commands", "views"].includes(view)
    ? [["commands", "Tools"] as const]
    : inspectorSection(view).tabs.map((key) => [key, labels[key]] as const);

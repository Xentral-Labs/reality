import { readFileSync } from "node:fs";
// Test records are checked against canonical catalogs by the backend suite.
// Classification and entrypoints always use the actual shared production metadata.
const discovery = JSON.parse(
  readFileSync(
    new URL("../../../packages/reality-core/config/action_discovery.json", import.meta.url),
    "utf8",
  ),
);
// The command palette lists actions from `tool_catalog.entries`, which the server derives at
// runtime. Without it the palette finds no action at all. Each form entry of the production
// discovery catalog becomes the capability the server builds for it ("form:<key>"); other
// capability kinds are not needed by the browser fixtures.
const tool_catalog = {
  version: 1,
  topics: [],
  entries: discovery.entries
    .filter((entry) => entry.form)
    .map((entry) => ({
      id: `form:${entry.key}`,
      title: entry.label,
      labels: {},
      description: "",
      topic: "",
      purpose: "change",
      commands: entry.command ? [entry.command] : [],
      actions: entry.command ? [entry.command] : [],
      views: [],
      projections: [],
      mcp: [],
      discovery: [entry.key],
      related: [],
    })),
  mcp_tools: [],
};
export const reference = {
  ...JSON.parse(readFileSync(new URL("./fixtures/action-reference.json", import.meta.url), "utf8")),
  discovery,
  tool_catalog,
};

import { readFileSync } from "node:fs";
// Test records are checked against canonical catalogs by the backend suite.
// Classification and entrypoints always use the actual shared production metadata.
export const reference = {
  ...JSON.parse(readFileSync(new URL("./fixtures/action-reference.json", import.meta.url), "utf8")),
  discovery: JSON.parse(
    readFileSync(
      new URL("../../../packages/reality-core/config/action_discovery.json", import.meta.url),
      "utf8",
    ),
  ),
};

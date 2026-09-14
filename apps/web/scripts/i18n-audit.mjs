import path from "node:path";
import { fileURLToPath } from "node:url";

import { auditLocalization, formatResults } from "./i18n-audit-lib.mjs";

const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const results = auditLocalization({
  sourceRoot: path.join(frontendRoot, "src"),
  localizationFile: path.join(frontendRoot, "src", "localization.tsx"),
});

console.log(formatResults(results, frontendRoot));
if (results.some((result) => result.status === "fail")) process.exitCode = 1;

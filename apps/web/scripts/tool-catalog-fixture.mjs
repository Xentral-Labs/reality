import { execFileSync } from "node:child_process";
const root = new URL("../../../", import.meta.url).pathname;
// Always use the actual composed metadata, not a hand-maintained duplicate catalog.
export const reference = JSON.parse(
  execFileSync(
    `${root}.venv/bin/python`,
    [
      "-c",
      "import json; from reality.catalogs import runtime_application_catalog; print(json.dumps(runtime_application_catalog()))",
    ],
    {
      cwd: root,
      env: {
        ...process.env,
        PYTHONPATH: `${root}packages/reality-core/src`,
        REALITY_DATABASE_URL: "postgresql+psycopg://localhost/reality",
      },
      encoding: "utf8",
    },
  ),
);

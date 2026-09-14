# UI and existing API contract
Entry: /app/data-sources?tenant=...&data_view=systems&entry=<source-id|new>.
GET integrations reads registry; POST source-systems registers reviewed code/name/description; PATCH source-systems/{id}/active and source-capabilities/{id}/active set reviewed booleans. Read and mutation authorization remains server-owned.
Review/cancel/reload do not write. Unknown submission blocks all new writes until explicit GET current-state recovery. Matching code is used only to display existing registry state; never an attribution or operational identity proof.

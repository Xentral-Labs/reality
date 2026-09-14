import { useState, type ReactNode } from "react";
import { CatalogCodeDialog } from "./CatalogCodeDialog";
import type {
  CatalogCommand,
  CatalogContract,
  ProjectionDefinition,
  WorkspaceActionDefinition,
  WorkspaceViewDefinition,
} from "../api";
import { t } from "../localization";

const repository = "https://github.com/Xentral-Labs/reality/blob/main/";
function SourceLink({ path, children }: { path: string; children: ReactNode }) {
  if (
    !/^packages\/reality-core\/(src\/reality|config)\/[\w/.-]+\.(py|yaml)$/.test(path) ||
    path.split("/").includes("..")
  )
    return null;
  return (
    <a className="br-btn" href={`${repository}${path}`} target="_blank" rel="noopener noreferrer">
      {children} ↗
    </a>
  );
}
function Field({ label, value }: { label: string; value?: string | string[] }) {
  if (!value || (Array.isArray(value) && !value.length)) return null;
  return (
    <div className="border-b border-border-default py-2 last:border-0">
      <dt className="text-xs font-medium text-fg-muted">{t(label)}</dt>
      <dd className="mt-1 break-words text-sm" data-localization="original">
        {Array.isArray(value) ? value.join(", ") : value}
      </dd>
    </div>
  );
}
export function CatalogEntryDetails({
  tenant,
  kind,
  entry,
  command,
  projection,
  usedBy = [],
  actions,
}: {
  tenant: string;
  kind: "projection" | "view" | "action" | "command";
  entry:
    ProjectionDefinition | WorkspaceViewDefinition | WorkspaceActionDefinition | CatalogCommand;
  command?: CatalogCommand;
  projection?: ProjectionDefinition;
  usedBy?: string[];
  actions: ReactNode;
}) {
  const [codeOpen, setCodeOpen] = useState(false);
  const p = kind === "projection" ? (entry as ProjectionDefinition) : projection;
  const a = kind === "action" ? (entry as WorkspaceActionDefinition) : undefined;
  const v = kind === "view" ? (entry as WorkspaceViewDefinition) : undefined;
  const c = kind === "command" ? (entry as CatalogCommand) : command;
  const contracts: CatalogContract[] =
    (kind === "projection" || kind === "view" ? p?.contracts : c?.contracts) || [];
  const description =
    kind === "projection"
      ? p?.calculation
      : kind === "view"
        ? v?.description
        : kind === "action"
          ? a?.description
          : c?.effect;
  const catalogFile =
    kind === "projection"
      ? "projection_catalog.yaml"
      : kind === "command"
        ? "command_catalog.yaml"
        : "workspace_catalog.yaml";
  const entryKey =
    kind === "projection"
      ? (entry as ProjectionDefinition).materialized_as
      : kind === "command"
        ? (entry as CatalogCommand).service
        : (entry as WorkspaceViewDefinition | WorkspaceActionDefinition).key;
  return (
    <div className="my-3 space-y-3" data-catalog-explanation>
      {!description && (
        <p className="text-sm text-fg-muted">
          {kind === "projection"
            ? t(
                "Calculated overview: this combines existing records to answer a business question.",
              )
            : kind === "view"
              ? t(
                  "Application view: this presents records or a calculated overview as a screen you can work with.",
                )
              : kind === "action"
                ? t(
                    "Business task: this guides you through the information and confirmation needed to perform an operation.",
                  )
                : t(
                    "Application operation: this defines the inputs, processing and results behind a business task.",
                  )}
        </p>
      )}
      {description && (
        <p className="text-sm leading-6" data-localization="original">
          {description}
        </p>
      )}
      {(kind === "projection" || kind === "view") && (
        <p className="text-xs text-fg-muted">
          {p?.materialized_as === "price_resolution"
            ? t("Calculated for your inputs")
            : p
              ? t("Stored result")
              : t("Live view")}
          {p?.materialized_as === "price_resolution" &&
            ` · ${t("Price depends on customer, item, quantity and date.")}`}
        </p>
      )}
      <div className="flex flex-wrap items-center gap-2" data-catalog-actions>
        {actions}
      </div>
      <div className="space-y-3 border-t border-border-default pt-4" data-catalog-secondary>
        <div className="flex items-center justify-between gap-3">
          <span className="text-xs font-medium uppercase tracking-wide text-fg-muted">
            {t("Details")}
          </span>
          <button className="br-btn" onClick={() => setCodeOpen(true)}>
            {t("View code")}
          </button>
        </div>
        {(p?.materialized_as === "inventory" ||
          c?.service === "reserve" ||
          a?.command === "reserve") && (
          <details className="rounded-lg bg-surface-muted p-3 text-sm">
            <summary className="cursor-pointer font-medium">{t("Illustrative example")}</summary>
            <p className="mt-1">
              {p?.materialized_as === "inventory"
                ? t(
                    "100 units in stock minus 30 reserved gives 70 available. These are example numbers, not your company data.",
                  )
                : t(
                    "You confirm a reservation of 5 units for a delivery commitment. The operation creates the reservation; it does not record a shipment.",
                  )}
            </p>
          </details>
        )}
        {codeOpen && (
          <CatalogCodeDialog
            key={`${tenant}:${kind}:${entryKey}`}
            tenant={tenant}
            kind={kind}
            entryKey={entryKey}
            close={() => setCodeOpen(false)}
          />
        )}
        <details>
          <summary className="cursor-pointer text-sm font-medium">{t("How it works")}</summary>
          <dl className="mt-2">
            {v && (
              <>
                <Field label="Data source" value={v.projection || v.key} />
                <Field
                  label="Data basis"
                  value={v.projection ? t("Calculated projection") : t("Stored records")}
                />
              </>
            )}
            {a && (
              <>
                <Field label="Required context" value={a.prerequisites} />
                <Field label="Application command" value={a.command} />
                <Field
                  label="Confirmation"
                  value={
                    a.confirmation === "server_preview"
                      ? t("Review a server-generated preview before confirming.")
                      : t("Review the proposed change before confirming.")
                  }
                />
              </>
            )}
            <Field label="Reads from" value={p?.reads || c?.reads} />
            <Field label="Processing" value={p?.calculation || c?.effect} />
            <Field label="Result fields" value={p?.outputs} />
            <Field label="Writes to" value={c?.writes} />
            <Field label="Used by" value={usedBy} />
            <Field label="Updated after" value={p?.invalidated_by} />
          </dl>
          {contracts.map((contract) => (
            <details
              key={contract.service}
              className="mt-3 rounded border border-border-default p-3"
            >
              <summary className="cursor-pointer break-all text-sm" data-localization="original">
                {contract.service}
              </summary>
              <div className="mt-2 space-y-2">
                {contract.inputs.map((input) => (
                  <div key={input.name} className="border-b border-border-default py-2 text-sm">
                    <code>{input.name}</code> · {t(input.required ? "Required" : "Optional")}
                    <p data-localization="original" className="mt-1 text-fg-muted">
                      {input.description}
                    </p>
                    <p data-localization="original" className="mt-1 break-all text-xs">
                      {input.type} · {input.default}
                    </p>
                  </div>
                ))}
              </div>
              <dl>
                <Field label="Returns" value={contract.returns} />
              </dl>
              {contract.source && (
                <div className="mt-3 space-y-2">
                  <p className="break-all text-xs text-fg-muted" data-localization="original">
                    {contract.source.path} · {contract.source.function}
                  </p>
                  <SourceLink path={contract.source.path}>{t("View implementation")}</SourceLink>
                </div>
              )}
            </details>
          ))}
        </details>
        <details>
          <summary className="cursor-pointer text-sm">{t("Technical definition")}</summary>
          <pre
            data-localization="original"
            className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-all text-xs"
          >
            {JSON.stringify(entry, null, 2)}
          </pre>
          <div className="mt-3">
            <SourceLink path={`packages/reality-core/config/${catalogFile}`}>
              {t("View catalog source")}
            </SourceLink>
          </div>
        </details>
      </div>
    </div>
  );
}

import { useState } from "react";
import { languageHref, readLanguage } from "../../../shared/language";
import { t } from "../localization";
import { CatalogCodeDialog } from "./CatalogCodeDialog";
import type { Report } from "./reportCatalogEntries";

const textLink =
  "inline-flex items-center gap-1 rounded text-sm text-primary underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4";

function Definition({ label, value }: { label: string; value?: string | string[] }) {
  if (!value || (Array.isArray(value) && !value.length)) return null;
  return (
    <div>
      <dt className="text-xs font-medium text-fg-muted">{t(label)}</dt>
      <dd className="mt-1 break-words text-sm leading-6" data-localization="original">
        {Array.isArray(value) ? value.join(", ") : value}
      </dd>
    </div>
  );
}

/** Explain one report; workspace aliases are navigation, not extra definitions. */
export function ReportExplanation({
  report,
  tenant,
  workspaceLinks,
}: {
  report: Report;
  tenant: string;
  workspaceLinks: Array<{ label: string; href: string }>;
}) {
  const [codeOpen, setCodeOpen] = useState(false);
  const projection = report.projection;
  const view = report.views[0];
  const entryKey = projection?.materialized_as || view?.key;
  const links = workspaceLinks.filter(
    (link, index) => workspaceLinks.findIndex((other) => other.href === link.href) === index,
  );
  const explanation =
    report.target === "fulfillment_queue"
      ? "Each row groups open customer deliveries by their order or supporting evidence. Readiness reflects active reservations and delivery holds."
      : report.description;

  return (
    <div className="space-y-6" data-report-explanation>
      <p className="text-sm leading-6">{t(explanation)}</p>
      {report.target === "inventory" && (
        <p className="text-sm leading-6 text-fg-muted">
          {t(
            "100 units in stock minus 30 reserved gives 70 available. These are example numbers, not your company data.",
          )}
        </p>
      )}
      {!report.dataAvailable && (
        <p className="text-sm leading-6 text-fg-muted">
          {t(
            "This report needs a business partner and an item. See the details for its inputs and calculation.",
          )}
        </p>
      )}
      {links.length > 0 && (
        <nav aria-label={t("Open in application")}>
          <h3 className="mb-2 text-xs font-medium text-fg-muted">{t("Open in application")}</h3>
          <ul className="space-y-2">
            {links.map((link) => (
              <li key={link.href}>
                <a className={textLink} href={link.href}>
                  {t(link.label)} <span aria-hidden="true">→</span>
                </a>
              </li>
            ))}
          </ul>
        </nav>
      )}
      <a
        className={textLink}
        href={languageHref(
          `${__DOCS_URL__.replace(/\/+$/, "")}/catalogs/${projection ? "projections" : "workspaces"}`,
          readLanguage() ?? "en",
          true,
        )}
        target="_blank"
        rel="noopener noreferrer"
      >
        {t("Documentation")} <span aria-hidden="true">↗</span>
      </a>
      <details className="border-t border-border-default pt-4" data-report-technical>
        <summary className="cursor-pointer text-sm font-medium">{t("Technical details")}</summary>
        <div className="mt-4 space-y-5">
          <dl className="space-y-4">
            <Definition label="Processing" value={projection?.calculation || view?.description} />
            <Definition
              label="Data basis"
              value={t(
                report.target === "price_resolution"
                  ? "Calculated for your inputs"
                  : projection
                    ? "Stored result"
                    : "Live view",
              )}
            />
            <Definition label="Reads from" value={projection?.reads} />
            <Definition label="Result fields" value={projection?.outputs} />
            <Definition label="Updated after" value={projection?.invalidated_by} />
          </dl>
          {report.target === "price_resolution" &&
            projection?.contracts?.map((contract) => (
              <section key={contract.service} className="space-y-3">
                <h3 className="break-all font-mono text-xs" data-localization="original">
                  {contract.service}
                </h3>
                <dl className="space-y-3">
                  {contract.inputs.map((input) => (
                    <div key={input.name}>
                      <dt className="text-sm">
                        <code data-localization="original">{input.name}</code>
                        <span className="ml-2 text-xs text-fg-muted">
                          {t(input.required ? "Required" : "Optional")}
                        </span>
                      </dt>
                      <dd className="mt-1 text-sm leading-6" data-localization="original">
                        {input.description}
                        <span className="mt-1 block break-all font-mono text-xs text-fg-muted">
                          {input.type} · {input.default}
                        </span>
                      </dd>
                    </div>
                  ))}
                  <Definition label="Returns" value={contract.returns} />
                </dl>
              </section>
            ))}
          {entryKey && (
            <button type="button" className={textLink} onClick={() => setCodeOpen(true)}>
              {t("View code")}
            </button>
          )}
          <details>
            <summary className="cursor-pointer text-sm">{t("Technical definition")}</summary>
            <pre
              className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-all text-xs leading-5"
              data-localization="original"
              tabIndex={0}
              aria-label={t("Technical definition")}
            >
              {JSON.stringify({ projection, views: report.views }, null, 2)}
            </pre>
          </details>
        </div>
      </details>
      {codeOpen && entryKey && (
        <CatalogCodeDialog
          tenant={tenant}
          kind={projection ? "projection" : "view"}
          entryKey={entryKey}
          close={() => setCodeOpen(false)}
        />
      )}
    </div>
  );
}

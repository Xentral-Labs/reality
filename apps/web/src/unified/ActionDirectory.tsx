import { languageHref, readLanguage } from "../../../shared/language";
import { useActionDiscovery } from "./ActionLauncher";
import { useState } from "react";
import { ChevronDown, ChevronRight, Folder, FolderOpen } from "lucide-react";
import type { ApplicationReference, CatalogCommand } from "../api";
import { t } from "../localization";
import { CatalogEntryDetails } from "./CatalogEntryDetails";
import { RegisterToolbar } from "./RegisterWorkbench";
import {
  directoryEntries,
  groupDirectory,
  isActionForm,
  supportedEntries,
  type DeliveryAction,
  type DirectoryEntry,
} from "./actionDiscovery";

const branchStyles = {
  category: "border-b border-border-default last:border-0",
  group: "ml-3 border-l border-border-default pl-3 sm:ml-6",
};

export function ActionDirectory({
  reference,
  tenant,
  openAction,
}: {
  reference: ApplicationReference;
  tenant: string;
  openAction: (form: DeliveryAction) => void;
}) {
  const context = useActionDiscovery();
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const entries = directoryEntries(reference);
  const groups = groupDirectory(reference, entries, query, t);
  const searching = !!query.trim();
  const toggle = (id: string) =>
    setExpanded((previous) => {
      const next = new Set(previous);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  const visible = groups.flatMap((c) => c.groups.flatMap((g) => g.entries));
  const count = (values: DirectoryEntry[]) =>
    `${values.filter((e) => e.kind === "action").length} ${t("Actions")} · ${values.filter((e) => e.kind === "command").length} ${t("Commands")}`;
  const branch = (
    id: string,
    label: string,
    values: DirectoryEntry[],
    level: "category" | "group",
    children: React.ReactNode,
  ) => {
    const open = searching || expanded.has(id);
    return (
      <section key={id} className={branchStyles[level]} data-directory-branch={id}>
        <button
          type="button"
          className="flex w-full min-w-0 items-center gap-2 rounded-lg px-2 py-3 text-left hover:bg-surface-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
          aria-expanded={open}
          aria-controls={`branch-${id}`}
          onClick={() => {
            if (!searching) toggle(id);
          }}
        >
          {open ? (
            <ChevronDown size={16} className="shrink-0" />
          ) : (
            <ChevronRight size={16} className="shrink-0" />
          )}
          {level === "category" &&
            (open ? (
              <FolderOpen size={18} className="shrink-0 text-accent" />
            ) : (
              <Folder size={18} className="shrink-0 text-accent" />
            ))}
          <span className="min-w-0 flex-1 font-medium">{t(label)}</span>
          <span className="text-right text-xs text-fg-muted">{count(values)}</span>
        </button>
        <div id={`branch-${id}`} hidden={!open}>
          {children}
        </div>
      </section>
    );
  };
  return (
    <section className="register-surface overflow-hidden" data-action-directory>
      <RegisterToolbar
        count={visible.length}
        countDescription={count(visible)}
        search={
          <input
            type="search"
            className="br-control"
            aria-label={t("Search action catalog")}
            placeholder={t("Search action catalog")}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        }
        submit={
          query ? (
            <button className="br-btn" onClick={() => setQuery("")}>
              {t("Clear search")}
            </button>
          ) : undefined
        }
        filters={
          <>
            <button
              className="br-btn"
              disabled={searching}
              onClick={() =>
                setExpanded(new Set(groups.flatMap((c) => [c.key, ...c.groups.map((g) => g.key)])))
              }
            >
              {t("Expand all")}
            </button>
            <button className="br-btn" disabled={searching} onClick={() => setExpanded(new Set())}>
              {t("Collapse all")}
            </button>
          </>
        }
      />
      <div className="py-4">
        {!visible.length && (
          <p role="status" className="p-4 text-sm text-fg-muted">
            {t("No matching records")}
          </p>
        )}
        {groups.map((c) =>
          branch(
            c.key,
            c.label,
            c.groups.flatMap((g) => g.entries),
            "category",
            c.groups.map((g) =>
              branch(
                g.key,
                g.label,
                g.entries,
                "group",
                g.entries.map((e) => {
                  const command = reference.commands?.find((c) => c.service === e.command);
                  const forms = supportedEntries(reference, e.command, context || undefined);
                  return (
                    <details
                      key={e.id}
                      className="ml-3 border-l border-border-default pl-3 sm:ml-6"
                      data-directory-entry={e.id}
                    >
                      <summary className="cursor-pointer rounded-lg px-2 py-3 text-sm hover:bg-surface-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent">
                        <span className="ml-1">{t(e.label)}</span>{" "}
                        <span className="ml-2 rounded bg-surface-muted px-2 py-0.5 text-xs text-fg-muted">
                          {t(e.kind === "action" ? "Action" : "Command")}
                        </span>
                        {e.kind === "command" && (
                          <span className="ml-2 text-xs text-fg-muted">
                            {t(
                              (e.entry as CatalogCommand).mode !== "mutation"
                                ? "Read only"
                                : "Mutation",
                            )}
                          </span>
                        )}
                      </summary>
                      <div className="min-w-0 px-2 pb-4">
                        <CatalogEntryDetails
                          tenant={tenant}
                          kind={e.kind}
                          entry={e.entry}
                          command={e.kind === "action" ? command : undefined}
                          usedBy={
                            e.kind === "command"
                              ? entries
                                  .filter((a) => a.kind === "action" && a.command === e.command)
                                  .map((a) => a.label)
                              : undefined
                          }
                          actions={
                            <>
                              {forms.map((form) => (
                                <button
                                  key={form.key}
                                  className="br-btn"
                                  onClick={() => {
                                    if (form.form && isActionForm(form.form)) openAction(form.form);
                                    else if (form.destination)
                                      context?.navigate({
                                        ...form.destination,
                                        q: "",
                                        entry: "",
                                        record: "",
                                        proposal: "",
                                        page: 1,
                                      });
                                  }}
                                >
                                  {t(form.label)}
                                </button>
                              ))}
                              {!forms.length && (
                                <p className="text-sm text-fg-muted">
                                  {t(
                                    command?.mode !== "mutation"
                                      ? "Read-only command. See the supported adapters."
                                      : "No Web form is registered here. See the command’s supported adapters.",
                                  )}
                                </p>
                              )}
                              {!!forms.length && e.command === "record_movement" && (
                                <p className="text-sm text-fg-muted">
                                  {t("These forms cover opening stock, receipts and shipments.")}
                                </p>
                              )}
                              <a
                                className="br-btn"
                                href={languageHref(
                                  `${__DOCS_URL__.replace(/\/+$/, "")}/catalogs/${e.kind === "action" ? "workspaces" : "commands"}`,
                                  readLanguage() ?? "en",
                                  true,
                                )}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                {t("Documentation")} ↗
                              </a>
                            </>
                          }
                        />
                      </div>
                    </details>
                  );
                }),
              ),
            ),
          ),
        )}
      </div>
    </section>
  );
}

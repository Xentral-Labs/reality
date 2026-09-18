import type { ApplicationReference, GraphTemplate, SearchProvider } from "../api";
import { menuEntries, isActionForm, type DeliveryAction } from "./actionDiscovery.ts";
import { buildReports } from "./reportCatalogEntries.ts";
import {
  palettePages,
  type PaletteTarget,
  type PaletteActionTarget,
} from "./commandPaletteTargets.ts";

export type PaletteEntry = {
  key: string;
  group: "actions" | "pages" | "reports" | SearchProvider | "companies" | "help";
  tier?: number;
  secondary?: string;
  sortKey?: [number, number, number, number, string, string, string];
  label: string;
  aliases: string[];
  synonyms?: string[];
  references: string[];
  outcome: string;
  target:
    | PaletteTarget
    | { kind: "action"; id: DeliveryAction; prefill?: PaletteActionTarget }
    | { kind: "company"; id: string }
    | { kind: "help"; id: string };
};

/** Compose executable catalogs; a capability without a Web form opens its explanation. */
export function paletteEntries(
  reference: ApplicationReference | undefined,
  access: { owner: boolean; demo: boolean },
  translate: (label: string) => string,
  language: string,
  templates: GraphTemplate[] = [],
): PaletteEntry[] {
  const entries: PaletteEntry[] = palettePages(access).map((page) => ({
    key: `page:${page.key}`,
    group: "pages",
    label: translate(page.label),
    aliases: [page.label],
    references: [],
    outcome: "Open page",
    target: { kind: "page", id: page.key },
  }));
  if (!reference) return entries;
  const vocabulary = (references: string[], views: string[] = [], projections: string[] = []) =>
    (reference.search_vocabulary || [])
      .filter(
        (resource) =>
          references.some((value) => resource.match && new RegExp(resource.match).test(value)) ||
          views.some((value) => resource.views.includes(value)) ||
          projections.some((value) => resource.projections.includes(value)),
      )
      .flatMap((resource) => [...Object.values(resource.labels), ...resource.synonyms]);
  const forms = menuEntries(reference, "global", access);
  const reports = buildReports(reference);
  for (const capability of reference.tool_catalog?.entries || []) {
    const form = forms.find(
      (entry) => capability.discovery.includes(entry.key) && entry.form && isActionForm(entry.form),
    );
    const report = reports.find(
      (entry) =>
        capability.projections.includes(entry.target) ||
        capability.id === `report:${entry.target}` ||
        entry.views.some((view) => capability.views.includes(view.key)),
    );
    if (report && !form) continue;
    // Restricted navigation entries must not reappear as unfiltered capability shortcuts.
    if (capability.purpose === "navigate") continue;
    const label = form
      ? translate(form.label)
      : capability.labels[language] || translate(capability.title);
    entries.push({
      key: form ? `action:${form.form}` : `capability:${capability.id}`,
      group: "actions",
      label,
      aliases: [capability.title, ...Object.values(capability.labels)],
      synonyms: vocabulary(capability.commands, capability.views, capability.projections),
      references: [...capability.commands, ...capability.mcp],
      outcome: form ? "Open form" : "Show capability",
      target: form
        ? { kind: "action", id: form.form as DeliveryAction }
        : { kind: "capability", id: capability.id },
    });
  }
  for (const report of reports)
    entries.push({
      key: `calculated_report:${report.target}`,
      group: "reports",
      label: translate(report.title),
      aliases: [report.title, ...report.views.map((view) => view.label)],
      synonyms: vocabulary(
        [],
        report.views.map((view) => view.key),
        [report.target],
      ),
      references: [report.target],
      outcome: report.dataAvailable ? "Open report" : "Show details",
      target: { kind: "calculated_report", id: report.target },
    });
  for (const template of templates)
    entries.push({
      key: `template:${template.key}`,
      group: "reports",
      label: template.label,
      aliases: [],
      references: [template.key],
      outcome: "Use a template",
      target: { kind: "template", id: template.key },
    });
  return [...new Map(entries.map((entry) => [entry.key, entry])).values()];
}

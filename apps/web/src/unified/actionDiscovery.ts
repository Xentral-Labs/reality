import type { ApplicationReference, CatalogCommand, WorkspaceActionDefinition } from "../api";
import type { Selection } from "./routing";

export const formKeys = [
  "reserve",
  "movement_create",
  "receipt",
  "opening_stock",
  "party_delivery_hold",
  "party_delivery_hold_release",
  "reservation_release",
  "commitment_hold",
  "commitment_hold_release",
  "movement_correct",
  "shipment_notice_record",
  "shipment_dispatch",
  "shipment_receive",
  "shipment_event_record",
  "shipment_event_supersede",
  "return_disposition",
  "order_create",
  "sales_invoice_record",
  "sales_credit_record",
  "supplier_invoice_record",
  "customer_refund_post",
  "customer_payment_post",
  "supplier_payment_post",
  "ledger_reverse",
] as const;
export type DeliveryAction = (typeof formKeys)[number];
export const isActionForm = (value: string): value is DeliveryAction =>
  (formKeys as readonly string[]).includes(value);
export type DiscoveryEntry = {
  key: string;
  label: string;
  command?: string;
  commands?: string[];
  form?: string;
  group?: string;
  destination?: Partial<Selection>;
  placements: string[];
  access?: "owner" | "demo";
};
export type ActionDiscovery = {
  categories: { key: string; label: string; groups: { key: string; label: string }[] }[];
  command_groups: Record<string, string>;
  entries: DiscoveryEntry[];
};
export type DirectoryEntry = {
  id: string;
  label: string;
  kind: "action" | "command";
  command: string;
  group: string;
  entry: CatalogCommand | WorkspaceActionDefinition;
};
export function primaryCommand(reference: ApplicationReference, service: string) {
  return reference.commands?.find((c) =>
    [c.service, ...(c.related_services || [])].includes(service),
  );
}
export function directoryEntries(reference: ApplicationReference): DirectoryEntry[] {
  const actions = [
    ...new Map(reference.workspaces.flatMap((w) => w.actions).map((a) => [a.key, a])).values(),
  ];
  const group = (service: string) => reference.discovery?.command_groups[service] || "unclassified";
  return [
    ...actions.map((a) => ({
      id: `action:${a.key}`,
      label: a.label,
      kind: "action" as const,
      command: a.command,
      group: group(a.command),
      entry: a,
    })),
    ...(reference.commands || []).map((c) => ({
      id: `command:${c.service}`,
      label: c.name || c.service,
      kind: "command" as const,
      command: c.service,
      group: group(c.service),
      entry: c,
    })),
  ];
}
export function groupDirectory(
  reference: ApplicationReference,
  entries: DirectoryEntry[],
  query: string,
  translate: (s: string) => string,
) {
  const knownGroups = new Set(
    reference.discovery?.categories.flatMap((c) => c.groups.map((g) => g.key)) || [],
  );
  const categories = [
    ...(reference.discovery?.categories || []),
    {
      key: "unclassified",
      label: "Unclassified",
      groups: [{ key: "unclassified", label: "Unclassified" }],
    },
  ];
  const q = query.trim().toLocaleLowerCase();
  return categories
    .map((c) => ({
      ...c,
      groups: c.groups
        .map((g) => ({
          ...g,
          entries: entries.filter((e) => {
            const group = knownGroups.has(e.group) ? e.group : "unclassified";
            const text = [
              c.label,
              g.label,
              e.label,
              translate(c.label),
              translate(g.label),
              translate(e.label),
              JSON.stringify(e.entry),
            ]
              .join(" ")
              .toLocaleLowerCase();
            return group === g.key && (!q || text.includes(q));
          }),
        }))
        .filter((g) => g.entries.length),
    }))
    .filter((c) => c.groups.length);
}
export function menuEntries(
  reference: ApplicationReference | undefined,
  context: string,
  access = { owner: false, demo: false },
): DiscoveryEntry[] {
  return (reference?.discovery?.entries || []).filter((e) => {
    if (
      !e.placements.some(
        (p) => p === context || (p === "finance.journal" && context.startsWith("finance.journal.")),
      )
    )
      return false;
    if (e.access && !access[e.access]) return false;
    if (e.destination) return true;
    const command = reference && primaryCommand(reference, e.command || "");
    return (
      !!e.form &&
      isActionForm(e.form) &&
      command?.mode === "mutation" &&
      command.adapters.includes("Web")
    );
  });
}
export function entryGroup(reference: ApplicationReference, entry: DiscoveryEntry) {
  return (
    entry.group ||
    reference.discovery?.command_groups[
      primaryCommand(reference, entry.command || "")?.service || ""
    ] ||
    "unclassified"
  );
}
export function supportedEntries(
  reference: ApplicationReference,
  command: string,
  access = { owner: false, demo: false },
) {
  return menuEntries(reference, "global", access).filter((e) =>
    e.destination
      ? e.commands?.includes(command)
      : e.form && primaryCommand(reference, e.command || "")?.service === command,
  );
}

export function financeContext(selection: Pick<Selection, "financeView" | "flow" | "direction">) {
  const flow =
    selection.financeView === "payments" && selection.direction
      ? selection.direction === "outgoing"
        ? "payable"
        : "receivable"
      : selection.flow;
  return `finance.${selection.financeView}.${flow}`;
}

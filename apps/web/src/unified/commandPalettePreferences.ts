import type { PaletteEntry } from "./commandPaletteEntries";
import { isActionForm } from "./actionDiscovery.ts";
export type PaletteReference = Pick<PaletteEntry, "key" | "target">;
export type PalettePreferences = { favorites: PaletteReference[]; recents: PaletteReference[] };
type StorageLike = Pick<Storage, "getItem" | "setItem" | "removeItem" | "key" | "length">;
const memory = new Map<string, PalettePreferences>();
const prefix = "reality:command-palette:v1:";
const empty = (): PalettePreferences => ({ favorites: [], recents: [] });
const recordKinds = new Set([
  "party",
  "item",
  "location",
  "document",
  "source_record",
  "commitment",
  "reservation",
  "movement",
  "fact",
  "ledger_entry",
  "payment",
  "shipment",
]);
function reference(value: unknown): PaletteReference | null {
  if (!value || typeof value !== "object") return null;
  const row = value as Record<string, unknown>,
    target = row.target as Record<string, unknown> | undefined;
  if (
    typeof row.key !== "string" ||
    row.key.length > 512 ||
    !target ||
    typeof target.id !== "string" ||
    !target.id ||
    target.id.length > 256
  )
    return null;
  if (target.kind === "record") {
    if (
      typeof target.record_kind !== "string" ||
      !recordKinds.has(target.record_kind) ||
      typeof target.family !== "string" ||
      target.family.length > 64
    )
      return null;
    return {
      key: row.key,
      target: {
        kind: "record",
        id: target.id,
        record_kind: target.record_kind as "party",
        family: target.family,
      },
    };
  }
  if (target.kind === "action" && isActionForm(target.id))
    return { key: row.key, target: { kind: "action", id: target.id } };
  if (
    ["page", "capability", "calculated_report", "saved_report", "template"].includes(
      String(target.kind),
    )
  )
    return { key: row.key, target: { kind: target.kind as "page", id: target.id } };
  return null;
}
function clean(value: unknown): PalettePreferences {
  if (!value || typeof value !== "object") return empty();
  const row = value as Record<string, unknown>;
  const list = (name: string) =>
    Array.isArray(row[name])
      ? [
          ...new Map(
            (row[name] as unknown[])
              .map(reference)
              .filter((item): item is PaletteReference => !!item)
              .map((item) => [item.key, item]),
          ).values(),
        ].slice(0, 20)
      : [];
  return { favorites: list("favorites"), recents: list("recents") };
}
const scope = (user: string, tenant: string) =>
  prefix + encodeURIComponent(user) + ":" + encodeURIComponent(tenant);
export function readPalettePreferences(
  storage: StorageLike,
  user: string,
  tenant: string,
): PalettePreferences {
  try {
    const raw = storage.getItem(scope(user, tenant));
    if (!raw) return memory.get(scope(user, tenant)) || empty();
    const parsed = JSON.parse(raw);
    return parsed?.version === 1 ? clean(parsed) : empty();
  } catch {
    return memory.get(scope(user, tenant)) || empty();
  }
}
export function writePalettePreferences(
  storage: StorageLike,
  user: string,
  tenant: string,
  value: PalettePreferences,
): boolean {
  memory.set(scope(user, tenant), clean(value));
  try {
    storage.setItem(scope(user, tenant), JSON.stringify({ version: 1, ...clean(value) }));
    return true;
  } catch {
    return false;
  }
}
export function clearPalettePreferences(storage: StorageLike): void {
  memory.clear();
  try {
    for (let i = storage.length - 1; i >= 0; i--) {
      const key = storage.key(i);
      if (key?.startsWith(prefix)) storage.removeItem(key);
    }
  } catch {
    /* Clearing rendered state is independent of browser storage availability. */
  }
}

import { useEffect, useState } from "react";
import { searchApi, type SearchRecordTarget } from "../api";
import type { PaletteEntry } from "./commandPaletteEntries";
import {
  clearPalettePreferences,
  readPalettePreferences,
  writePalettePreferences,
  type PalettePreferences,
  type PaletteReference,
} from "./commandPalettePreferences";

export function usePalettePreferences(user: string, tenant: string, entries: PaletteEntry[]) {
  const [value, setValue] = useState<PalettePreferences>(() => {
    try {
      return readPalettePreferences(localStorage, user, tenant);
    } catch {
      return { favorites: [], recents: [] };
    }
  });
  const [persistent, setPersistent] = useState(true);
  const [resolved, setResolved] = useState<PaletteEntry[]>([]);
  const [expired, setExpired] = useState(false);
  useEffect(() => {
    const clear = () => {
      try {
        clearPalettePreferences(localStorage);
      } catch {
        /* Rendered state still clears. */
      }
      setExpired(true);
      setResolved([]);
      setValue({ favorites: [], recents: [] });
    };
    const storage = (event: StorageEvent) => {
      if (event.key === "reality:logout") clear();
    };
    window.addEventListener("reality:session-expired", clear);
    window.addEventListener("storage", storage);
    return () => {
      window.removeEventListener("reality:session-expired", clear);
      window.removeEventListener("storage", storage);
    };
  }, []);
  const references = [...value.favorites, ...value.recents];
  const signature = JSON.stringify(references);
  useEffect(() => {
    setResolved([]);
    const controller = new AbortController();
    const targets: SearchRecordTarget[] = references.flatMap<SearchRecordTarget>((entry) =>
      entry.target.kind === "record"
        ? [{ kind: "record", record_kind: entry.target.record_kind, id: entry.target.id }]
        : entry.target.kind === "saved_report"
          ? [{ kind: "saved_report", record_kind: "analytics_report", id: entry.target.id }]
          : [],
    );
    if (targets.length && !expired)
      searchApi
        .resolve(tenant, targets, controller.signal)
        .then(({ items }) => {
          if (!controller.signal.aborted)
            setResolved(
              items.map((hit) => ({
                key: hit.key,
                group: hit.group,
                label: hit.label,
                secondary: hit.secondary,
                aliases: [],
                references: [],
                outcome: hit.target.kind === "saved_report" ? "Open report" : "Open record",
                target:
                  hit.target.kind === "saved_report"
                    ? { kind: "saved_report", id: hit.target.id }
                    : { ...hit.target, kind: "record", family: hit.family, roles: hit.roles },
              })),
            );
        })
        .catch(() => {
          if (!controller.signal.aborted) setResolved([]);
        });
    return () => controller.abort();
  }, [user, tenant, signature, expired]);
  const save = (next: PalettePreferences) => {
    if (expired) return;
    setValue(next);
    try {
      setPersistent(writePalettePreferences(localStorage, user, tenant, next));
    } catch {
      setPersistent(false);
    }
  };
  const resolvedEntries = new Map([...entries, ...resolved].map((entry) => [entry.key, entry]));
  const resolve = (refs: PaletteReference[]) =>
    expired
      ? []
      : refs.flatMap((ref) => {
          const entry = resolvedEntries.get(ref.key);
          return entry ? [entry] : [];
        });
  return {
    expired,
    persistent,
    favorites: resolve(value.favorites),
    recents: resolve(value.recents),
    pinned: (key: string) => value.favorites.some((entry) => entry.key === key),
    pin: (entry: PaletteEntry) =>
      save({
        ...value,
        favorites: value.favorites.some((ref) => ref.key === entry.key)
          ? value.favorites.filter((ref) => ref.key !== entry.key)
          : [{ key: entry.key, target: entry.target }, ...value.favorites].slice(0, 20),
      }),
    remember: (entry: PaletteEntry) => {
      if (entry.target.kind !== "action")
        save({
          ...value,
          recents: [
            { key: entry.key, target: entry.target },
            ...value.recents.filter((ref) => ref.key !== entry.key),
          ].slice(0, 20),
        });
    },
    clearHistory: () => save({ ...value, recents: [] }),
    clear: () => save({ favorites: [], recents: [] }),
  };
}

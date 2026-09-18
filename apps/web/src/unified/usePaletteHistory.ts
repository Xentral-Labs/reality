import { useEffect } from "react";
import type { SearchRecordTarget } from "../api";
import { palettePages } from "./commandPaletteTargets";
import {
  readPalettePreferences,
  writePalettePreferences,
  type PaletteReference,
} from "./commandPalettePreferences";
import type { Selection } from "./routing";

export function usePaletteHistory(
  user: string,
  tenant: string,
  selection: Selection,
  access: { owner: boolean; demo: boolean },
) {
  const remember = (reference: PaletteReference) => {
    try {
      const value = readPalettePreferences(localStorage, user, tenant);
      writePalettePreferences(localStorage, user, tenant, {
        ...value,
        recents: [reference, ...value.recents.filter((row) => row.key !== reference.key)].slice(
          0,
          20,
        ),
      });
    } catch {
      /* History is optional when browser storage is unavailable. */
    }
  };
  useEffect(() => {
    const page = palettePages(access).find((entry) =>
      Object.entries(entry.destination).every(
        ([key, value]) => selection[key as keyof Selection] === value,
      ),
    );
    if (page) remember({ key: `page:${page.key}`, target: { kind: "page", id: page.key } });
  }, [
    user,
    tenant,
    selection.route,
    selection.ordersView,
    selection.financeView,
    selection.warehouseView,
    selection.inspectorView,
  ]);
  useEffect(() => {
    const opened = (event: Event) => {
      const detail = (event as CustomEvent).detail as {
        tenant: string;
        kind: SearchRecordTarget["record_kind"];
        id: string;
      };
      if (detail?.tenant !== tenant || !detail.id) return;
      const physical = detail.kind === "payment" ? "ledger_entry" : detail.kind;
      remember({
        key: `${physical}:${detail.id}`,
        target:
          detail.kind === "analytics_report"
            ? { kind: "saved_report", id: detail.id }
            : { kind: "record", record_kind: detail.kind, id: detail.id, family: detail.kind },
      });
    };
    window.addEventListener("reality:record-opened", opened);
    return () => {
      window.removeEventListener("reality:record-opened", opened);
    };
  }, [user, tenant]);
}

export function recordOpened(tenant: string, kind: string, id: string) {
  if (
    [
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
      "analytics_report",
    ].includes(kind)
  )
    window.dispatchEvent(
      new CustomEvent("reality:record-opened", { detail: { tenant, kind, id } }),
    );
}

import { useEffect, useState } from "react";
import { api } from "../api";
import { t } from "../localization";
import type { GraphTarget } from "./ObjectGraph";

const entries = [
  { label: "Delivery", kind: "commitment", query: "customer_delivery" },
  { label: "Order", kind: "document", query: "sales_order" },
  { label: "Item", kind: "item", query: "" },
  { label: "Customer", kind: "party", query: "customer" },
  { label: "Fact", kind: "fact", query: "" },
];
export function useGraphStartingPoint(tenant: string, initialRoot: GraphTarget | null = null) {
  const [root, setRoot] = useState(initialRoot);
  const [start, setStart] = useState<string | null>(initialRoot ? null : "auto");
  const [revision, retry] = useState(0);
  const [label, setLabel] = useState("");
  const [loading, setLoading] = useState(!initialRoot);
  const [error, setError] = useState<string>();
  const [empty, setEmpty] = useState(false);
  const manual = () => {
    setStart(null);
    setLoading(false);
    setError(undefined);
    setEmpty(false);
    setLabel("");
  };
  useEffect(() => {
    if (!start) return;
    let current = true;
    setLoading(true);
    setError(undefined);
    setEmpty(false);
    setRoot(null);
    setLabel("");
    const load = async () => {
      for (const entry of entries.filter((entry) => start === "auto" || entry.kind === start)) {
        const data = await api.explorer(tenant, entry.query, entry.kind);
        if (!current) return;
        const candidates = data.sections
          .flatMap((section) => section.collections.flatMap((collection) => collection.records))
          .slice(0, 3);
        if (!candidates.length) continue;
        const details = await Promise.all(
          candidates.map((record) => api.inspector(tenant, entry.kind, record.id)),
        );
        if (!current) return;
        const links = (value: (typeof details)[number]) =>
          new Set(
            value.sections.flatMap((section) =>
              section.rows.flatMap((row) => (row.link ? [`${row.link.kind}:${row.link.id}`] : [])),
            ),
          ).size;
        const chosen = details.reduce((best, value) => (links(value) > links(best) ? value : best));
        setRoot({ kind: chosen.kind, id: chosen.id });
        setLabel(chosen.title);
        setLoading(false);
        return;
      }
      if (current) {
        setLoading(false);
        setEmpty(true);
      }
    };
    load().catch((error) => {
      if (current) {
        setError(String(error.message));
        setLoading(false);
      }
    });
    return () => {
      current = false;
    };
  }, [tenant, start, revision]);
  const choose = (kind: string) => {
    setStart(kind);
    retry((value) => value + 1);
  };
  return {
    root,
    setRoot,
    start,
    label,
    loading,
    error,
    empty,
    manual,
    choose,
    retry: () => retry((value) => value + 1),
  };
}

export function GraphStartingPoints({
  start,
  root,
  choose,
}: {
  start: string | null;
  root: GraphTarget | null;
  choose: (kind: string) => void;
}) {
  return (
    <nav className="flex flex-wrap gap-2" aria-label={t("Graph starting points")}>
      {entries.map((entry) => (
        <button
          key={entry.kind}
          className="br-btn aria-pressed:border-accent aria-pressed:bg-accent-soft"
          aria-pressed={start === entry.kind || (start === "auto" && root?.kind === entry.kind)}
          onClick={() => {
            choose(entry.kind);
          }}
        >
          {t(entry.label)}
        </button>
      ))}
    </nav>
  );
}

import { useEffect, useState } from "react";
import { GraphStartingPoints, useGraphStartingPoint } from "./graphStartingPoints";
import { t } from "../localization";
import { GraphRecordInput } from "./GraphRecordInput";
import { ObjectGraph, type GraphTarget } from "./ObjectGraph";
import { ReadState } from "./ReadState";

const kinds = [
  "fact",
  "commitment",
  "reservation",
  "movement",
  "document",
  "document_line",
  "source_record",
  "party",
  "item",
  "location",
  "ledger_entry",
  "payment",
  "business_event",
];

export function RecordGraphPage({
  tenant,
  initialRoot,
  onRootChange,
}: {
  tenant: string;
  initialRoot: GraphTarget | null;
  onRootChange: (root: GraphTarget | null) => void;
}) {
  const seed = useGraphStartingPoint(tenant, initialRoot);
  const { root, setRoot, label, loading, error, empty, manual } = seed;
  const [kind, setKind] = useState(initialRoot?.kind || "commitment");
  const [recordId, setRecordId] = useState(initialRoot?.id || "");
  useEffect(() => {
    onRootChange(root);
    if (root) {
      setKind(root.kind);
      setRecordId(root.id);
    }
  }, [root, onRootChange]);
  return (
    <div className="space-y-4">
      <GraphStartingPoints
        {...seed}
        choose={(kind) => {
          setKind(kind);
          setRecordId("");
          seed.choose(kind);
        }}
      />
      <form
        className="flex flex-wrap items-end gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          if (recordId.trim()) {
            manual();
            setRoot({ kind, id: recordId.trim() });
          }
        }}
      >
        <label className="text-sm">
          {t("Record type")}
          <select
            className="br-control"
            value={kind}
            onChange={(event) => {
              manual();
              setKind(event.target.value);
              setRecordId("");
              setRoot(null);
            }}
          >
            {kinds.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <GraphRecordInput
          key={`${tenant}:${kind}`}
          tenant={tenant}
          kind={kind}
          value={recordId}
          onChange={(value) => {
            manual();
            setRecordId(value);
          }}
          onSelect={(id) => {
            manual();
            setRoot({ kind, id });
          }}
        />
        <button className="br-btn" disabled={!recordId.trim()}>
          {t("Open")}
        </button>
      </form>
      {label && (
        <p className="text-sm text-fg-muted" data-graph-start>
          {t("Starting point")}:{" "}
          <strong className="text-fg" data-localization="original">
            {label}
          </strong>
        </p>
      )}
      {loading || error ? (
        <ReadState loading={loading} error={error} retry={seed.retry} />
      ) : root ? (
        <ObjectGraph key={`${tenant}:${root.kind}:${root.id}`} tenant={tenant} root={root} />
      ) : (
        <p className="rounded-xl border border-border-default bg-surface p-4 text-sm text-fg-muted">
          {t(
            empty
              ? "No records are available for this starting point yet."
              : "Choose a starting point or search for a record.",
          )}
        </p>
      )}
    </div>
  );
}

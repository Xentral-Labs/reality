import { TargetMappingPreview } from "./TargetMappingPreview";
import { SourceResolutionView, type SourceResolution } from "./SourceMappings";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { formatMoney, t } from "../localization";
import { useRead } from "../unified/useCompanyContext";
import { ReadState } from "../unified/ReadState";

type Reference = { id: string; code: string; name: string };
type Part = { cost_center_reference_id: string; amount: string };
type Assignment = {
  id?: string;
  component_id: string | null;
  revision: number;
  basis: string;
  basis_amount: string | null;
  assigned: string;
  unassigned: string | null;
  currency: string;
  case_reference_id: string | null;
  group_reference_id: string | null;
  parts: Part[];
  references: {
    case: Reference | null;
    group: Reference | null;
    centers: Record<string, Reference>;
  };
  reason: string;
  action_id?: string;
  actor_id?: string | null;
  created_at?: string;
};
type Component = {
  document_id: string;
  document_line_id: string | null;
  source_record_id: string | null;
  label: string;
  currency: string;
  amounts: Record<string, string | null>;
  source_codes: unknown;
  source_resolution?: SourceResolution;
  evidence_hash: string;
  component_id?: string | null;
  current?: Assignment | null;
};
type Context = {
  document_id: string;
  number: string;
  summary: Component;
  line_scope: boolean;
  total: number;
  revision: number;
  items: Component[];
  references: Record<string, { total: number; items: Reference[] }>;
};
type Review = { received: Component; before: Assignment | null; after: Assignment };
type Pending = { id: string; preview: { assignment: Review } };
type History = { total: number; items: Assignment[] };
const basisLabels: Record<string, string> = {
  net: "Net",
  gross: "Gross",
  base: "Other received basis",
  tax: "Tax",
};
async function call<T>(url: string, body?: unknown): Promise<T> {
  const response = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...(body === undefined ? {} : { method: "POST", body: JSON.stringify(body) }),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(typeof data.detail === "string" ? data.detail : t("Request failed"));
  return data;
}
function amount(value: string | null, currency: string) {
  return value === null ? t("Unknown") : formatMoney(value, currency);
}
function AssignmentView({ value }: { value: Assignment | null }) {
  if (!value) return <p>{t("No internal attribution")}</p>;
  return (
    <div className="space-y-2 rounded-lg border border-border-default p-3 text-sm">
      <p>
        {t("Revision")}: {value.revision} · {t(basisLabels[value.basis])}:{" "}
        {amount(value.basis_amount, value.currency)}
      </p>
      <p>
        {t("Assigned")}: {amount(value.assigned, value.currency)} · {t("Unassigned")}:{" "}
        {amount(value.unassigned, value.currency)}
      </p>
      <p>
        {t("Case code")}:{" "}
        {value.references.case
          ? `${value.references.case.code} · ${value.references.case.name}`
          : t("None")}
      </p>
      <p>
        {t("Coding group")}:{" "}
        {value.references.group
          ? `${value.references.group.code} · ${value.references.group.name}`
          : t("None")}
      </p>
      <ul>
        {value.parts.map((part) => (
          <li key={part.cost_center_reference_id}>
            {value.references.centers[part.cost_center_reference_id]?.code} ·{" "}
            {value.references.centers[part.cost_center_reference_id]?.name}:{" "}
            {amount(part.amount, value.currency)}
          </li>
        ))}
      </ul>
      <p>
        {t("Reason")}: {value.reason}
      </p>
      {value.action_id && (
        <p className="break-all">
          {t("Action")}: {value.action_id} · {t("Actor")}: {value.actor_id || t("Unknown")} ·{" "}
          {value.created_at}
        </p>
      )}
    </div>
  );
}
function ReferenceSelect({
  label,
  value,
  options,
  selected,
  onChange,
  optional = true,
}: {
  label: string;
  value: string;
  options: Reference[];
  selected?: Reference | null;
  onChange: (value: string) => void;
  optional?: boolean;
}) {
  const values =
    selected && !options.some((row) => row.id === selected.id) ? [selected, ...options] : options;
  return (
    <label>
      {t(label)}
      <select
        className="br-control w-full"
        aria-label={t(label)}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required={!optional}
      >
        <option value="">{t(optional ? "None" : "Select cost center")}</option>
        {value && !values.some((row) => row.id === value) && <option value={value}>{value}</option>}
        {values.map((row) => (
          <option key={row.id} value={row.id}>
            {row.code} · {row.name}
          </option>
        ))}
      </select>
    </label>
  );
}
function AssignmentForm({
  item,
  context,
  busy,
  submit,
}: {
  item: Component;
  context: Context;
  busy: boolean;
  submit: (values: Record<string, unknown>) => Promise<void>;
}) {
  const [basis, setBasis] = useState(
    item.current?.basis || (item.amounts.net === null ? "gross" : "net"),
  );
  const [caseId, setCase] = useState(item.current?.case_reference_id || "");
  const [groupId, setGroup] = useState(item.current?.group_reference_id || "");
  const [parts, setParts] = useState<Part[]>(item.current?.parts || []);
  async function prepare(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    await submit({
      document_id: item.document_id,
      document_line_id: item.document_line_id,
      basis,
      case_reference_id: caseId || null,
      group_reference_id: groupId || null,
      parts,
      reason: fields.get("reason"),
      expected_evidence_hash: item.evidence_hash,
      expected_revision: context.revision,
    });
  }
  return (
    <form onSubmit={(event) => void prepare(event)}>
      <fieldset className="space-y-4" disabled={busy}>
        <h3 className="font-semibold">{t("Internal attribution")}</h3>
        <label>
          {t("Attribution basis")}
          <select
            className="br-control w-full"
            aria-label={t("Attribution basis")}
            value={basis}
            onChange={(e) => setBasis(e.target.value)}
          >
            {["net", "gross", "base"].map((key) => (
              <option key={key} value={key}>
                {t(basisLabels[key])} · {amount(item.amounts[key], item.currency)}
              </option>
            ))}
          </select>
        </label>
        <div className="grid gap-3 sm:grid-cols-2">
          <ReferenceSelect
            label="Case code"
            value={caseId}
            onChange={setCase}
            options={context.references.case_code.items}
            selected={item.current?.references.case}
          />
          <ReferenceSelect
            label="Coding group"
            value={groupId}
            onChange={setGroup}
            options={context.references.coding_group.items}
            selected={item.current?.references.group}
          />
        </div>
        <p className="text-sm text-fg-muted">
          {t("Enter explicit shares. Empty shares leave the amount unassigned.")}
        </p>
        {parts.map((part, index) => (
          <div
            key={index}
            className="grid gap-2 rounded-lg border border-border-default p-3 sm:grid-cols-3"
          >
            <ReferenceSelect
              label="Cost center"
              optional={false}
              value={part.cost_center_reference_id}
              options={context.references.cost_center.items}
              selected={item.current?.references.centers[part.cost_center_reference_id]}
              onChange={(value) =>
                setParts((rows) =>
                  rows.map((row, i) =>
                    i === index ? { ...row, cost_center_reference_id: value } : row,
                  ),
                )
              }
            />
            <label>
              {t("Share amount")} · {item.currency}
              <input
                aria-label={t("Share amount")}
                className="br-control w-full"
                inputMode="decimal"
                required
                value={part.amount}
                onChange={(event) =>
                  setParts((rows) =>
                    rows.map((row, i) =>
                      i === index ? { ...row, amount: event.target.value } : row,
                    ),
                  )
                }
              />
            </label>
            <button
              className="br-btn self-end"
              type="button"
              onClick={() => setParts((rows) => rows.filter((_, i) => i !== index))}
            >
              {t("Remove share")}
            </button>
          </div>
        ))}
        <div className="flex flex-wrap gap-2">
          <button
            className="br-btn"
            type="button"
            disabled={parts.length >= 100}
            onClick={() =>
              setParts((rows) => [...rows, { cost_center_reference_id: "", amount: "" }])
            }
          >
            {t("Add cost-center share")}
          </button>
          <button
            className="br-btn"
            type="button"
            onClick={() => {
              setParts([]);
              setCase("");
              setGroup("");
            }}
          >
            {t("Clear internal attribution")}
          </button>
        </div>
        <label className="block">
          {t("Reason")}
          <input className="br-control w-full" name="reason" required maxLength={4000} />
        </label>
        <button className="br-btn br-btn-primary">{t("Review attribution")}</button>
      </fieldset>
    </form>
  );
}
export function FinancialComponents({
  tenant,
  documentId,
  canManage,
  close,
  explain,
}: {
  tenant: string;
  documentId: string;
  canManage: boolean;
  close: () => void;
  explain: (id: string) => void;
}) {
  const base = `/api/tenants/${encodeURIComponent(tenant)}`;
  const storage = `reality:attribution:${tenant}:${documentId}`;
  const dialog = useRef<HTMLDialogElement>(null);
  const [offset, setOffset] = useState(0);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState<Assignment | null>(null);
  const [history, setHistory] = useState<History | null>(null);
  const [historyOffset, setHistoryOffset] = useState(0);
  const [pending, setPending] = useState<Pending | null>(() => {
    try {
      const saved = JSON.parse(sessionStorage.getItem(storage) || "null");
      return saved?.preview?.assignment?.received?.document_id === documentId ? saved : null;
    } catch {
      return null;
    }
  });
  const read = useRead<Context>(
    () =>
      call(
        `${base}/finance/components/context/${encodeURIComponent(documentId)}?${new URLSearchParams({ limit: "50", offset: String(offset), reference_query: query })}`,
      ),
    [base, documentId, offset, query],
  );
  useEffect(() => {
    const node = dialog.current;
    const previous = document.activeElement as HTMLElement;
    node?.showModal();
    return () => {
      node?.close();
      previous?.focus();
    };
  }, []);
  useEffect(() => {
    if (pending) sessionStorage.setItem(storage, JSON.stringify(pending));
    else sessionStorage.removeItem(storage);
  }, [pending, storage]);
  const data = read.data;
  const item =
    data?.items.find((row) => (row.document_line_id || row.document_id) === selected) ||
    data?.items[0];
  async function prepare(values: Record<string, unknown>) {
    setError("");
    setBusy(true);
    setReceipt(null);
    try {
      setPending(
        await call(`${base}/finance/components/proposals`, {
          tool: "finance.component.assign",
          arguments: values,
        }),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  async function decide(approve: boolean) {
    if (!pending) return;
    setError("");
    setBusy(true);
    try {
      const result = await call<{ output: Assignment }>(
        `${base}/change-proposals/${pending.id}/${approve ? "approve" : "reject"}`,
        {},
      );
      setPending(null);
      setHistory(null);
      if (approve) setReceipt(result.output);
      read.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  async function loadHistory(next = 0) {
    if (!item?.component_id) return;
    setError("");
    setBusy(true);
    try {
      setHistory(
        await call(
          `${base}/finance/components/${item.component_id}/history?limit=50&offset=${next}`,
        ),
      );
      setHistoryOffset(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <dialog
      ref={dialog}
      aria-label={t("Financial detail")}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) close();
      }}
      className="m-auto max-h-[90dvh] w-[min(56rem,calc(100vw-2rem))] overflow-y-auto rounded-xl border border-border-default bg-surface p-5 text-fg shadow-xl backdrop:bg-black/40"
    >
      <header className="mb-4 flex items-start justify-between gap-3">
        <h2 className="text-xl font-semibold">
          {t("Financial detail")}
          {data ? ` · ${data.number}` : ""}
        </h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </header>
      <TargetMappingPreview
        key={`${tenant}:${documentId}`}
        tenantId={tenant}
        documentId={documentId}
        explain={explain}
      />
      {error && (
        <p role="alert" className="mb-4">
          {error}
        </p>
      )}
      {(!data || read.error) && (
        <ReadState loading={read.loading} error={read.error} retry={read.refresh} />
      )}
      {receipt && (
        <section role="status" className="mb-4">
          <h3 className="font-semibold">{t("Attribution saved")}</h3>
          <AssignmentView value={receipt} />
        </section>
      )}
      {pending ? (
        <section aria-label={t("Confirm attribution")} className="space-y-4">
          <p>
            {pending.preview.assignment.received.label} ·{" "}
            {pending.preview.assignment.received.currency}
          </p>
          <h3>{t("Before")}</h3>
          <AssignmentView value={pending.preview.assignment.before} />
          <h3>{t("After")}</h3>
          <AssignmentView value={pending.preview.assignment.after} />
          <button
            className="br-btn br-btn-primary"
            disabled={busy || !canManage}
            onClick={() => void decide(true)}
          >
            {t("Confirm attribution")}
          </button>
          <button
            className="br-btn"
            disabled={busy || !canManage}
            onClick={() => void decide(false)}
          >
            {t("Cancel")}
          </button>
        </section>
      ) : (
        data && (
          <div className="space-y-5">
            <section className="space-y-2">
              <h3 className="font-semibold">{t("Received document summary")}</h3>
              <div className="flex flex-wrap gap-3">
                {["gross", "net", "tax", "base"].map((key) => (
                  <p key={key}>
                    {t(basisLabels[key])}:{" "}
                    {amount(data.summary.amounts[key], data.summary.currency)}
                  </p>
                ))}
              </div>
              <p className="text-sm text-fg-muted">
                {t(
                  data.line_scope
                    ? "Assign individual lines. The document summary is not added again."
                    : "This document has no lines. Attribution uses its received amounts.",
                )}
              </p>
              <button className="br-btn" onClick={() => explain(documentId)}>
                {t("Inspect document")}
              </button>
            </section>
            <label className="block">
              {t("Select financial component")}
              <select
                className="br-control w-full"
                aria-label={t("Select financial component")}
                disabled={busy}
                value={item ? item.document_line_id || item.document_id : ""}
                onChange={(event) => {
                  setSelected(event.target.value);
                  setHistory(null);
                  setReceipt(null);
                }}
              >
                {data.items.map((row) => (
                  <option
                    key={row.document_line_id || row.document_id}
                    value={row.document_line_id || row.document_id}
                  >
                    {row.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex items-center gap-2">
              <span>
                {t("Components")}: {data.total}
              </span>
              <button
                className="br-btn"
                disabled={busy || offset === 0}
                onClick={() => {
                  setOffset((v) => Math.max(0, v - 50));
                  setSelected("");
                  setHistory(null);
                }}
              >
                {t("Previous")}
              </button>
              <button
                className="br-btn"
                disabled={busy || offset + 50 >= data.total}
                onClick={() => {
                  setOffset((v) => v + 50);
                  setSelected("");
                  setHistory(null);
                }}
              >
                {t("Next")}
              </button>
            </div>
            {item && (
              <>
                <section className="space-y-2">
                  <h3 className="font-semibold">{t("Received component")}</h3>
                  <div className="flex flex-wrap gap-3">
                    {["gross", "net", "tax", "base"].map((key) => (
                      <p key={key}>
                        {t(basisLabels[key])}: {amount(item.amounts[key], item.currency)}
                      </p>
                    ))}
                  </div>
                  <SourceResolutionView value={item.source_resolution} tenantId={tenant} />
                  <details>
                    <summary>{t("Original source codes")}</summary>
                    <pre className="overflow-x-auto whitespace-pre-wrap break-all text-sm">
                      {JSON.stringify(item.source_codes, null, 2)}
                    </pre>
                  </details>
                  <div className="flex flex-wrap gap-2">
                    {item.document_line_id && (
                      <button className="br-btn" onClick={() => explain(item.document_line_id!)}>
                        {t("Inspect line")}
                      </button>
                    )}
                    {item.source_record_id && (
                      <button className="br-btn" onClick={() => explain(item.source_record_id!)}>
                        {t("Inspect source")}
                      </button>
                    )}
                  </div>
                </section>
                <section>
                  <h3 className="mb-2 font-semibold">{t("Current attribution")}</h3>
                  <AssignmentView value={item.current || null} />
                  {item.component_id && (
                    <button
                      className="br-btn mt-2"
                      disabled={busy}
                      onClick={() => void loadHistory()}
                    >
                      {t("Attribution history")}
                    </button>
                  )}
                </section>
                {canManage && (
                  <>
                    <label className="block">
                      {t("Find classification references")}
                      <input
                        className="br-control w-full"
                        value={query}
                        disabled={busy}
                        onChange={(e) => setQuery(e.target.value)}
                      />
                    </label>
                    {Object.values(data.references).some(
                      (page) => page.total > page.items.length,
                    ) && <p>{t("Refine the reference search to find more entries.")}</p>}
                    <AssignmentForm
                      key={`${item.document_line_id || item.document_id}:${item.current?.revision || 0}`}
                      item={item}
                      context={data}
                      busy={busy || read.loading}
                      submit={prepare}
                    />
                  </>
                )}
                {history && (
                  <section aria-label={t("Attribution history")} className="space-y-3">
                    <h3 className="font-semibold">{t("Attribution history")}</h3>
                    {history.items.map((value) => (
                      <AssignmentView key={value.id} value={value} />
                    ))}
                    <button
                      className="br-btn"
                      disabled={busy || historyOffset === 0}
                      onClick={() => void loadHistory(Math.max(0, historyOffset - 50))}
                    >
                      {t("Previous")}
                    </button>
                    <button
                      className="br-btn"
                      disabled={busy || historyOffset + 50 >= history.total}
                      onClick={() => void loadHistory(historyOffset + 50)}
                    >
                      {t("Next")}
                    </button>
                  </section>
                )}
              </>
            )}
          </div>
        )
      )}
    </dialog>
  );
}

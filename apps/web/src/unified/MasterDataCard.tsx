import { Fragment, useEffect, useRef, useState } from "react";
import {
  api,
  workspaceApi,
  type ReferenceDetail,
  type ReferenceFamily,
  type ReferenceProposal,
  type SuggestionRow,
} from "../api";
import { t } from "../localization";
import { ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";

export type ReferenceDraft = {
  family: ReferenceFamily;
  operation: "create" | "update";
  record: Record<string, unknown>;
  request_id: string;
};
type Option = { value: string; label: string };
export type ReferenceField = {
  key: string;
  label: string;
  group: "Identity" | "Commercial defaults" | "Inventory behaviour" | "Hierarchy" | "Source";
  kind: "text" | "code" | "choice" | "roles" | "flag" | "record" | "decimal" | "count";
  required?: boolean;
  /** Tenant-scoped suggestion kind for codes and records. */
  choices?: string;
  options?: Option[];
};
export const roleOptions: Option[] = [
  { value: "company", label: "Company" },
  { value: "customer", label: "Customer" },
  { value: "supplier", label: "Supplier" },
];
const itemTypeOptions: Option[] = [
  { value: "stocked", label: "Stocked" },
  { value: "service", label: "Service" },
  { value: "charge", label: "Charge" },
];
const trackingOptions: Option[] = [
  { value: "none", label: "No tracking" },
  { value: "lot", label: "Lot" },
  { value: "serial", label: "Serial" },
];
const locationTypeOptions: Option[] = [
  "warehouse",
  "store",
  "returns",
  "virtual",
  "bin",
  "zone",
].map((value) => ({ value, label: value }));
const provenance: ReferenceField[] = [
  {
    key: "source_system",
    label: "Source system",
    group: "Source",
    kind: "code",
    choices: "source-system-codes",
  },
  { key: "external_id", label: "External ID", group: "Source", kind: "text" },
];
// Every operational field the shared create/update services accept, per family.
// Lossless external evidence is deliberately absent; it is never edited here.
const partyFields: ReferenceField[] = [
  { key: "name", label: "Name", group: "Identity", kind: "text", required: true },
  { key: "type", label: "Type", group: "Identity", kind: "choice", options: roleOptions },
  { key: "roles", label: "Roles", group: "Identity", kind: "roles", options: roleOptions },
  { key: "accounting_code", label: "Accounting code", group: "Commercial defaults", kind: "text" },
  {
    key: "payment_term_code",
    label: "Payment term",
    group: "Commercial defaults",
    kind: "code",
    choices: "payment-terms",
  },
  {
    key: "default_currency",
    label: "Default currency",
    group: "Commercial defaults",
    kind: "code",
    choices: "currencies",
    required: true,
  },
  { key: "credit_limit", label: "Credit limit", group: "Commercial defaults", kind: "decimal" },
  { key: "tax_identifier", label: "Tax identifier", group: "Commercial defaults", kind: "text" },
  ...provenance,
];
const itemFields: ReferenceField[] = [
  { key: "sku", label: "SKU", group: "Identity", kind: "text", required: true },
  { key: "name", label: "Name", group: "Identity", kind: "text", required: true },
  { key: "unit", label: "Unit", group: "Identity", kind: "code", choices: "units", required: true },
  {
    key: "item_type",
    label: "Item type",
    group: "Inventory behaviour",
    kind: "choice",
    options: itemTypeOptions,
  },
  {
    key: "tracking_type",
    label: "Tracking",
    group: "Inventory behaviour",
    kind: "choice",
    options: trackingOptions,
  },
  {
    key: "default_location_id",
    label: "Default location",
    group: "Inventory behaviour",
    kind: "record",
    choices: "locations",
  },
  {
    key: "purchase_unit",
    label: "Purchase unit",
    group: "Inventory behaviour",
    kind: "code",
    choices: "units",
  },
  {
    key: "conversion_factor",
    label: "Conversion factor",
    group: "Inventory behaviour",
    kind: "decimal",
  },
  { key: "lead_time_days", label: "Lead time (days)", group: "Inventory behaviour", kind: "count" },
  ...provenance,
];
const locationFields: ReferenceField[] = [
  { key: "name", label: "Name", group: "Identity", kind: "text", required: true },
  {
    key: "type",
    label: "Type",
    group: "Identity",
    kind: "code",
    options: locationTypeOptions,
    required: true,
  },
  {
    key: "parent_location_id",
    label: "Parent location",
    group: "Hierarchy",
    kind: "record",
    choices: "locations",
  },
  { key: "allows_stock", label: "Allows physical stock", group: "Hierarchy", kind: "flag" },
  ...provenance,
];
export function referenceFields(family: ReferenceFamily): ReferenceField[] {
  return family === "item" ? itemFields : family === "location" ? locationFields : partyFields;
}
const flagLabel = "flex items-center gap-2 self-end text-sm";
const blockLabel = "block text-sm";
const groups: ReferenceField["group"][] = [
  "Identity",
  "Commercial defaults",
  "Inventory behaviour",
  "Hierarchy",
  "Source",
];
export const fieldLabels: Record<string, string> = {
  id: "Record ID",
  expected_revision: "Reviewed revision",
  ...Object.fromEntries(
    [...partyFields, ...itemFields, ...locationFields].map((field) => [field.key, field.label]),
  ),
};
const valueOptions: Record<string, Option[]> = {
  type: roleOptions,
  roles: roleOptions,
  item_type: itemTypeOptions,
  tracking_type: trackingOptions,
};
export function displayValue(key: string, value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.map((entry) => displayValue(key, entry)).join(", ");
  if (typeof value === "boolean") return t(value ? "Yes" : "No");
  if (typeof value === "object") return JSON.stringify(value);
  const option = valueOptions[key]?.find((entry) => entry.value === String(value));
  return option ? t(option.label) : String(value);
}
export function RecordSummary({
  record,
  omit = [],
}: {
  record: Record<string, unknown>;
  omit?: string[];
}) {
  return (
    <dl className="mt-3 space-y-2 text-sm">
      {Object.entries(record)
        .filter(([key]) => !omit.includes(key))
        .map(([key, value]) => (
          <div key={key} className="grid grid-cols-[minmax(90px,1fr)_2fr] gap-3">
            <dt className="break-words text-fg-muted">{t(fieldLabels[key] || key)}</dt>
            <dd className="break-all">{displayValue(key, value)}</dd>
          </div>
        ))}
    </dl>
  );
}
const createDefaults = (family: ReferenceFamily): Record<string, unknown> =>
  family === "item"
    ? {
        unit: "pcs",
        item_type: "stocked",
        tracking_type: "none",
        conversion_factor: "1",
        lead_time_days: "0",
      }
    : family === "location"
      ? { type: "warehouse", allows_stock: true }
      : { type: family, roles: [family], default_currency: "EUR", credit_limit: "0" };
function initialValues(
  family: ReferenceFamily,
  detail: ReferenceDetail | undefined,
  saved: ReferenceDraft | null,
): Record<string, unknown> {
  const values: Record<string, unknown> = { ...createDefaults(family) };
  const source = saved?.record || detail;
  if (source)
    for (const field of referenceFields(family)) {
      const value = source[field.key];
      values[field.key] =
        field.kind === "flag"
          ? Boolean(value)
          : field.kind === "roles"
            ? Array.isArray(value)
              ? value
              : [family]
            : value === null || value === undefined
              ? ""
              : String(value);
    }
  if (family !== "item" && family !== "location") {
    const roles = values.roles as string[];
    if (!roles.includes(family)) values.roles = [...roles, family];
  }
  return values;
}
export const draftKey = (tenant: string) => `reality:reference-draft:${tenant}`;
export function savedReferenceDraft(tenant: string): ReferenceDraft | null {
  try {
    const raw = sessionStorage.getItem(draftKey(tenant));
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
function receiptUrl(
  tenant: string,
  proposal: ReferenceProposal,
  link: { family: string; id: string },
  index: number,
): string {
  const record = proposal.input.records[index] || {};
  const roles = Array.isArray(record.roles) ? record.roles : [record.type];
  const family =
    link.family === "party"
      ? roles.includes("customer")
        ? "customer"
        : roles.includes("supplier")
          ? "supplier"
          : ""
      : link.family;
  return family
    ? `/app/master-data?${new URLSearchParams({ tenant, family, record: link.id })}`
    : `/app/inspector?${new URLSearchParams({ tenant, inspector_view: "records", q: link.id })}`;
}
function FieldInput({
  field,
  family,
  value,
  set,
  choices,
  detail,
  listId,
}: {
  field: ReferenceField;
  family: ReferenceFamily;
  value: unknown;
  set: (value: unknown) => void;
  choices: SuggestionRow[] | undefined;
  detail?: ReferenceDetail;
  listId: string;
}) {
  const text = value === null || value === undefined ? "" : String(value);
  if (field.kind === "roles") {
    const roles = Array.isArray(value) ? (value as string[]) : [];
    return (
      <fieldset className="mt-2 flex flex-wrap gap-4">
        <legend className="sr-only">{t(field.label)}</legend>
        {(field.options || []).map((option) => (
          <label key={option.value} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={roles.includes(option.value)}
              disabled={option.value === family}
              onChange={(event) =>
                set(
                  event.target.checked
                    ? [...roles, option.value]
                    : roles.filter((role) => role !== option.value),
                )
              }
            />
            {t(option.label)}
          </label>
        ))}
      </fieldset>
    );
  }
  if (field.kind === "flag")
    return (
      <input
        type="checkbox"
        className="mt-2"
        checked={Boolean(value)}
        onChange={(event) => set(event.target.checked)}
      />
    );
  if (field.kind === "choice")
    return (
      <select
        className="br-control mt-2 w-full"
        value={text}
        onChange={(event) => set(event.target.value)}
      >
        {(field.options || []).map((option) => (
          <option key={option.value} value={option.value}>
            {t(option.label)}
          </option>
        ))}
      </select>
    );
  if (field.kind === "record") {
    const rows = (choices || []).filter((row) => row.value !== detail?.id);
    const keepCurrent = field.key === "default_location_id" && Boolean(detail?.[field.key]);
    return (
      <select
        className="br-control mt-2 w-full"
        value={text}
        required={keepCurrent}
        onChange={(event) => set(event.target.value)}
      >
        {!keepCurrent && <option value="">{t("None")}</option>}
        {text && !rows.some((row) => row.value === text) && <option value={text}>{text}</option>}
        {rows.map((row) => (
          <option key={row.value} value={row.value}>
            {row.label} · {row.description}
          </option>
        ))}
      </select>
    );
  }
  const options =
    field.options || (choices || []).map((row) => ({ value: row.value, label: row.label }));
  return (
    <>
      <input
        className="br-control mt-2 w-full"
        required={field.required}
        maxLength={500}
        inputMode={
          field.kind === "decimal" ? "decimal" : field.kind === "count" ? "numeric" : undefined
        }
        list={field.kind === "code" ? listId : undefined}
        value={text}
        onChange={(event) => set(event.target.value)}
      />
      {field.kind === "code" && (
        <datalist id={listId}>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label === option.value ? undefined : option.label}
            </option>
          ))}
        </datalist>
      )}
    </>
  );
}
export function MasterDataCard({
  tenant,
  family,
  detail,
  proposalId,
  close,
  prepared,
  settled,
}: {
  tenant: string;
  family: ReferenceFamily;
  detail?: ReferenceDetail;
  proposalId?: string;
  close: () => void;
  prepared: (id: string) => void;
  settled: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const saved = useRef(savedReferenceDraft(tenant));
  const fields = referenceFields(family);
  const [values, setValues] = useState(() => initialValues(family, detail, saved.current));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [uncertain, setUncertain] = useState(false);
  const [draft, setDraft] = useState<ReferenceDraft | null>(saved.current);
  const [choices, setChoices] = useState<Record<string, SuggestionRow[]>>({});
  const [choiceError, setChoiceError] = useState("");
  const [choiceRound, retryChoices] = useState(0);
  const read = useRead(
    () => (proposalId ? workspaceApi.proposal(tenant, proposalId) : Promise.resolve(null)),
    [tenant, proposalId],
  );
  const [result, setResult] = useState<ReferenceProposal | null>(null);
  const proposal = result || read.data;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    const node = dialog.current;
    node?.showModal();
    return () => {
      node?.close();
      previous?.focus();
    };
  }, []);
  useEffect(() => {
    if (proposalId) return;
    const kinds = [...new Set(referenceFields(family).map((field) => field.choices))].filter(
      (kind): kind is string => Boolean(kind),
    );
    let current = true;
    setChoiceError("");
    Promise.all(
      kinds.map((kind) =>
        api.suggestions(tenant, kind).then((data) => [kind, data.items] as const),
      ),
    )
      .then((rows) => {
        if (current) setChoices(Object.fromEntries(rows));
      })
      .catch((reason) => {
        if (current) setChoiceError((reason as Error).message);
      });
    return () => {
      current = false;
    };
  }, [tenant, family, proposalId, choiceRound]);
  async function prepare() {
    setBusy(true);
    setError("");
    const operation = saved.current?.operation || (detail ? "update" : "create");
    const record: Record<string, unknown> = {};
    for (const field of fields) {
      const value = values[field.key];
      record[field.key] =
        field.kind === "flag"
          ? Boolean(value)
          : field.kind === "roles"
            ? Array.isArray(value)
              ? value
              : [family]
            : value === null || value === undefined
              ? ""
              : String(value);
    }
    if (operation === "update") {
      const reviewed = saved.current?.operation === "update" ? saved.current.record : detail;
      record.id = reviewed?.id;
      record.expected_revision = reviewed?.expected_revision;
    }
    const intent: ReferenceDraft = draft || {
      family,
      operation,
      request_id: crypto.randomUUID(),
      record,
    };
    try {
      sessionStorage.setItem(draftKey(tenant), JSON.stringify(intent));
      setDraft(intent);
      const next = await workspaceApi.prepare(
        tenant,
        intent.family,
        intent.operation,
        intent.record,
        intent.request_id,
      );
      sessionStorage.removeItem(draftKey(tenant));
      setResult(next);
      prepared(next.id);
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function confirm() {
    if (!proposal) return;
    setBusy(true);
    setError("");
    setUncertain(true);
    try {
      const next = await workspaceApi.confirm(tenant, proposal.id);
      setResult(next);
      setUncertain(false);
      settled();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function check() {
    if (!proposal) return;
    setBusy(true);
    setError("");
    try {
      const next = await workspaceApi.proposal(tenant, proposal.id);
      setResult(next);
      setUncertain(false);
      if (next.status === "executed") settled();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function reject() {
    if (!proposal) return;
    setBusy(true);
    setError("");
    setUncertain(true);
    try {
      await api.rejectProposal(tenant, proposal.id, null);
      await check();
      settled();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <dialog
      ref={dialog}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) close();
      }}
      aria-label={t("Master data action")}
      className="m-auto max-h-[90vh] w-[min(760px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-accent">{t("Master data")}</p>
          <h2 className="mt-2 text-xl font-semibold text-fg-strong">
            {t(proposal ? "Review proposed changes" : detail ? "Edit details" : "Create a record")}
          </h2>
        </div>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </div>
      {error && (
        <p role="alert" className="my-4 rounded-lg bg-caution-bg p-4 text-caution-text">
          {error}
        </p>
      )}
      {proposalId && !proposal ? (
        <ReadState loading={read.loading} error={read.error} retry={read.refresh} />
      ) : proposal ? (
        <>
          <p className="mb-4 font-medium">
            {t(
              proposal.status === "executed"
                ? "Change recorded"
                : proposal.status === "rejected"
                  ? "Rejected"
                  : proposal.status === "executing" || uncertain
                    ? "Outcome not yet verified"
                    : "Ready for your confirmation",
            )}
          </p>
          <p className="mb-4 text-sm text-fg-muted">
            {t(
              proposal.status === "executed"
                ? "Recorded intent and receipt. Current details may have changed since execution."
                : "Check the exact fields below. Confirmation records this change.",
            )}
          </p>
          <div className="space-y-4">
            {proposal.input.records.map((record, index) => (
              <div key={index} className="rounded-lg border border-border-default p-4">
                <strong>{String(record.name || record.id || index + 1)}</strong>
                <RecordSummary record={record} omit={["expected_revision"]} />
              </div>
            ))}
          </div>
          {proposal.status === "proposed" && proposal.output.records && (
            <details className="my-4">
              <summary>{t("Field changes")}</summary>
              <pre className="mt-3 overflow-auto whitespace-pre-wrap text-xs">
                {JSON.stringify(proposal.output.records, null, 2)}
              </pre>
            </details>
          )}
          <div className="mt-5 flex flex-wrap gap-3">
            {proposal.status === "proposed" && !uncertain && (
              <>
                <button className="br-btn br-btn-primary" disabled={busy} onClick={confirm}>
                  {t("Confirm change")}
                </button>
                <button className="br-btn" disabled={busy} onClick={reject}>
                  {t("Reject")}
                </button>
              </>
            )}
            {(uncertain || proposal.status === "executing") && (
              <button className="br-btn" disabled={busy} onClick={check}>
                {t("Check outcome")}
              </button>
            )}
          </div>
          {proposal.status === "executed" && (
            <div className="mt-5 rounded-lg bg-positive-bg p-4 text-positive-text">
              <p>{t("Recorded reference IDs")}</p>
              {proposal.links.map((link, index) => (
                <a
                  key={link.id}
                  className="mt-2 block break-all text-sm underline"
                  href={receiptUrl(tenant, proposal, link, index)}
                >
                  {t("Open record")} · {link.id}
                </a>
              ))}
            </div>
          )}
          <p className="mt-5 break-all text-xs text-fg-muted">{proposal.id}</p>
        </>
      ) : (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void prepare();
          }}
          className="space-y-4"
        >
          <p className="text-sm text-fg-muted">
            {t("Prepare a change, review it, then confirm. Nothing is recorded yet.")}
          </p>
          {draft ? (
            <>
              <p>{t("A prepared request is saved. Check it before starting another change.")}</p>
              <RecordSummary record={draft.record} omit={["expected_revision"]} />
            </>
          ) : (
            <>
              {choiceError && (
                <p role="status" className="text-sm text-fg-muted">
                  {t("Choices could not be loaded.")}{" "}
                  <button
                    type="button"
                    className="br-btn"
                    onClick={() => retryChoices((round) => round + 1)}
                  >
                    {t("Retry")}
                  </button>
                </p>
              )}
              {groups
                .filter((group) => fields.some((field) => field.group === group))
                .map((group) => (
                  <fieldset key={group} className="rounded-lg border border-border-default p-4">
                    <legend className="px-1 text-sm font-semibold">{t(group)}</legend>
                    <div className="grid gap-4 sm:grid-cols-2">
                      {fields
                        .filter((field) => field.group === group)
                        .map((field) => (
                          <Fragment key={field.key}>
                            <label className={field.kind === "flag" ? flagLabel : blockLabel}>
                              {field.kind === "flag" ? null : t(field.label)}
                              <FieldInput
                                field={field}
                                family={family}
                                value={values[field.key]}
                                set={(value) =>
                                  setValues((current) => ({ ...current, [field.key]: value }))
                                }
                                choices={field.choices ? choices[field.choices] : undefined}
                                detail={detail}
                                listId={`reference-${family}-${field.key}`}
                              />
                              {field.kind === "flag" ? t(field.label) : null}
                            </label>
                          </Fragment>
                        ))}
                    </div>
                  </fieldset>
                ))}
            </>
          )}
          <div className="flex flex-wrap gap-3">
            <button className="br-btn br-btn-primary" disabled={busy} type="submit">
              {t(draft ? "Check prepared request" : "Prepare change")}
            </button>
            {draft && (
              <button
                className="br-btn"
                type="button"
                disabled={busy}
                onClick={() => {
                  sessionStorage.removeItem(draftKey(tenant));
                  setDraft(null);
                  setError("");
                }}
              >
                {t("Edit request")}
              </button>
            )}
          </div>
        </form>
      )}
    </dialog>
  );
}

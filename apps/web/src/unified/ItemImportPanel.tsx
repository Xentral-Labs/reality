import { useEffect, useRef, useState } from "react";
import {
  api,
  APIError,
  deliveryActions,
  itemImports,
  type ItemImportArtifact,
  type ItemImportConfig,
  type ItemImportProposal,
} from "../api";
import { formatNumber, t } from "../localization";
import { Inspector } from "./Inspector";

function importError(message: string): string {
  const exists = /^Row (\d+): SKU (.*) already exists in this company\.$/.exec(message);
  if (exists)
    return `${t("Row")} ${exists[1]} · ${exists[2]}: ${t("This SKU already exists in this company.")}`;
  const duplicate = /^Row (\d+): duplicate SKU (.*) in this file\.$/.exec(message);
  if (duplicate)
    return `${t("Row")} ${duplicate[1]} · ${duplicate[2]}: ${t("Duplicate SKU in this file.")}`;
  const required =
    /^Row (\d+): (sku|name|unit) is required and must be at most 500 characters\.$/.exec(message);
  if (required)
    return `${t("Row")} ${required[1]} · ${t(({ sku: "SKU", name: "Name", unit: "Unit" } as Record<string, string>)[required[2]] || required[2])}: ${t("Required field is empty or too long.")}`;
  const ragged = /^Row (\d+): the number of fields differs from the header\.$/.exec(message);
  if (ragged) return `${t("Row")} ${ragged[1]}: ${t("Field count differs from the header.")}`;
  return t(message);
}

type Attempt = { id: string; config: ItemImportConfig };
export function ItemImportPanel({
  tenant,
  proposalId = "",
  selectProposal,
  close,
}: {
  tenant: string;
  proposalId?: string;
  selectProposal: (id: string) => void;
  close: () => void;
}) {
  const storageKey = `reality.item-import.prepare:${tenant}`;
  const [attempt, setAttempt] = useState<Attempt | null>(() => {
    try {
      return JSON.parse(sessionStorage.getItem(storageKey) || "null");
    } catch {
      return null;
    }
  });
  const [file, setFile] = useState<File | null>(null);
  const [artifact, setArtifact] = useState<ItemImportArtifact | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [source, setSource] = useState("manual_upload");
  const [unit, setUnit] = useState("pcs");
  const [proposal, setProposal] = useState<ItemImportProposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [error, setError] = useState("");
  const [inspection, inspect] = useState<{ kind: string; id: string } | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const lock = useRef(false);
  const active = useRef(true);
  const reviewRef = useRef<HTMLElement>(null);
  useEffect(() => {
    active.current = true;
    const trigger = document.activeElement as HTMLElement | null;
    const element = dialog.current!;
    element.showModal();
    return () => {
      active.current = false;
      element.close();
      trigger?.focus();
    };
  }, []);
  useEffect(() => {
    if (!proposalId) return;
    let current = true;
    itemImports
      .detail(tenant, proposalId)
      .then((value) => {
        if (current) {
          setProposal(value);
          setUncertain(value.status === "executing");
        }
      })
      .catch((reason) => {
        if (current) setError(reason.message);
      });
    return () => {
      current = false;
    };
  }, [tenant, proposalId]);
  useEffect(() => {
    if (proposal) reviewRef.current?.focus();
  }, [proposal?.id]);
  const run = async (work: () => Promise<void>) => {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      await work();
    } catch (reason) {
      if (active.current) setError((reason as Error).message);
    } finally {
      lock.current = false;
      if (active.current) setBusy(false);
    }
  };
  const stage = () =>
    run(async () => {
      if (!file) return;
      if (file.size > 2 * 1024 * 1024) throw new Error("CSV must be at most 2 MiB.");
      const value = await itemImports.stage(tenant, file);
      if (active.current) {
        setArtifact(value);
        setMapping(value.mapping);
      }
    });
  const prepare = () =>
    run(async () => {
      const pending = attempt || {
        id: crypto.randomUUID(),
        config: {
          artifact_id: artifact!.id,
          source_system: source,
          mapping: Object.fromEntries(Object.entries(mapping).filter(([, value]) => !!value)),
          default_unit: unit,
        },
      };
      sessionStorage.setItem(storageKey, JSON.stringify(pending));
      setAttempt(pending);
      try {
        const value = await itemImports.prepare(tenant, pending.id, pending.config);
        sessionStorage.removeItem(storageKey);
        if (active.current) {
          setAttempt(null);
          setProposal(value);
          selectProposal(value.id);
        }
      } catch (reason) {
        if (reason instanceof APIError && reason.status >= 400 && reason.status < 500) {
          sessionStorage.removeItem(storageKey);
          if (active.current) setAttempt(null);
        }
        throw reason;
      }
    });
  const check = () =>
    run(async () => {
      const value = await itemImports.detail(tenant, proposal?.id || proposalId);
      if (active.current) {
        setProposal(value);
        setUncertain(value.status === "executing");
      }
    });
  const confirm = () =>
    run(async () => {
      if (!proposal || uncertain) return;
      setUncertain(true);
      try {
        await deliveryActions.confirm(tenant, proposal.id, proposal.review.token);
        const value = await itemImports.detail(tenant, proposal.id);
        if (active.current) {
          setProposal(value);
          setUncertain(value.status === "executing");
          window.dispatchEvent(new Event("reality:delivery-settled"));
        }
      } catch (reason) {
        throw reason;
      }
    });
  const reject = () =>
    run(async () => {
      if (!proposal || uncertain) return;
      setUncertain(true);
      await api.rejectProposal(tenant, proposal.id, null);
      const value = await itemImports.detail(tenant, proposal.id);
      if (active.current) {
        setProposal(value);
        setUncertain(false);
      }
    });
  const reconcile = () =>
    run(async () => {
      if (!proposal) return;
      await deliveryActions.reconcile(tenant, proposal.id);
      const value = await itemImports.detail(tenant, proposal.id);
      if (active.current) {
        setProposal(value);
        setUncertain(value.status === "executing");
      }
    });
  const creation = proposal?.review.state.creation;
  return (
    <dialog
      ref={dialog}
      onCancel={(event) => {
        event.preventDefault();
        if (event.target === event.currentTarget && !busy) close();
      }}
      className="m-auto max-h-[90dvh] w-[min(1100px,94vw)] overflow-auto space-y-5 rounded-xl border border-border-default bg-surface p-5 text-fg shadow-xl backdrop:bg-black/30 sm:p-7"
      aria-label={t("Import items")}
    >
      <header className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">{t("Import items")}</h2>
          <p className="mt-2 text-sm text-fg-muted">{t("CSV → Map columns → Review → Confirm")}</p>
        </div>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </header>
      <p className="text-sm text-fg-muted">
        {t("New items only. Maximum 500 rows and 2 MiB. Existing items are never overwritten.")}
      </p>
      {error && (
        <p role="alert" className="break-words rounded-lg bg-surface-muted p-4 text-sm">
          {importError(error)}
        </p>
      )}
      {proposalId && !proposal && (
        <button className="br-btn" disabled={busy} onClick={() => void check()}>
          {t("Check import status")}
        </button>
      )}
      {!proposalId && !proposal && !artifact && !attempt && (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            void stage();
          }}
        >
          <label className="block text-sm">
            {t("CSV file")}
            <input
              className="br-control mt-2 w-full"
              type="file"
              accept=".csv,text/csv"
              disabled={busy}
              required
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </label>
          <button className="br-btn br-btn-primary" disabled={busy || !file}>
            {t(busy ? "Loading…" : "Upload and check")}
          </button>
        </form>
      )}
      {attempt && !proposal && (
        <div className="space-y-3">
          <p className="text-sm">
            {t(
              busy
                ? "Preparing import review…"
                : "The review result needs checking. Recover the same request before starting another.",
            )}
          </p>
          <button className="br-btn" disabled={busy} onClick={() => void prepare()}>
            {t("Recover import review")}
          </button>
        </div>
      )}
      {artifact && !proposal && !attempt && (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            void prepare();
          }}
        >
          <p className="break-all text-sm">
            {artifact.filename} · {formatNumber(artifact.row_count)} {t("Rows")}
          </p>
          <fieldset disabled={busy} className="grid min-w-0 gap-4 sm:grid-cols-2">
            <label className="block text-sm">
              {t("Source code")}
              <input
                className="br-control mt-2 w-full"
                value={source}
                maxLength={100}
                required
                pattern="[a-z0-9][a-z0-9_.\-]{0,99}"
                onChange={(e) => setSource(e.target.value)}
              />
            </label>
            <label className="block text-sm">
              {t("Default unit")}
              <input
                className="br-control mt-2 w-full"
                value={unit}
                maxLength={500}
                required
                onChange={(e) => setUnit(e.target.value)}
              />
            </label>
            {(
              [
                ["sku", "SKU column"],
                ["name", "Name column"],
                ["unit", "Unit column"],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className="block min-w-0 text-sm">
                {t(label)}
                <select
                  className="br-control mt-2 w-full"
                  aria-label={t(label)}
                  required={key !== "unit"}
                  value={mapping[key] || ""}
                  onChange={(e) => setMapping({ ...mapping, [key]: e.target.value })}
                >
                  <option value="">
                    {t(key === "unit" ? "Use default unit" : "Select a column")}
                  </option>
                  {artifact.columns.map((column) => (
                    <option key={column} value={column}>
                      {column}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </fieldset>
          <p className="text-sm text-fg-muted">
            {t("The default unit applies when no unit column is selected or a unit cell is empty.")}
          </p>
          <button className="br-btn br-btn-primary" disabled={busy}>
            {t("Review import")}
          </button>
        </form>
      )}
      {proposal && creation && (
        <section
          ref={reviewRef}
          tabIndex={-1}
          className="space-y-4"
          aria-label={t("Import review")}
        >
          <h3 className="font-semibold">
            {proposal.verification === "verified" ? t("Items imported") : t("Import review")}
          </h3>
          <p className="break-words text-sm">
            {creation.artifact.filename} · {creation.source_system} ·{" "}
            {formatNumber(creation.rows.length)} {t("Items")}
          </p>
          <p className="text-sm text-fg-muted">
            {t("Default unit")}: {creation.default_unit}
          </p>
          <a className="br-btn" href={itemImports.original(tenant, creation.artifact.id)}>
            {t("Download original CSV")}
          </a>
          <div className="max-h-96 overflow-auto rounded-lg border border-border-default">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 bg-surface-muted">
                <tr>
                  {["SKU", "Name", "Unit"].map((label) => (
                    <th key={label} className="h-11 px-3 font-medium">
                      {t(label)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {creation.rows.map((row, index) => (
                  <tr key={row.sku} className="h-11 border-t border-border-default">
                    <td className="max-w-40 truncate px-3" title={row.sku}>
                      {proposal.verification === "verified" && proposal.receipt ? (
                        <button
                          className="text-accent underline"
                          onClick={() =>
                            inspect({ kind: "item", id: proposal.receipt!.item_ids[index] })
                          }
                        >
                          {row.sku}
                        </button>
                      ) : (
                        row.sku
                      )}
                    </td>
                    <td className="max-w-80 truncate px-3" title={row.name}>
                      {row.name}
                    </td>
                    <td className="max-w-24 truncate px-3" title={row.unit}>
                      {row.unit}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {proposal.verification === "verified" && proposal.receipt && (
            <div className="space-y-3">
              <p role="status">
                {t("All items were recorded. Reopening this result does not import them again.")}
              </p>
              <button
                className="br-btn"
                onClick={() =>
                  inspect({ kind: "source_record", id: proposal.receipt!.source_record_id })
                }
              >
                {t("Inspect source")}
              </button>
            </div>
          )}
          {proposal.status === "proposed" && (
            <div className="flex flex-wrap gap-3">
              <button
                className="br-btn br-btn-primary"
                disabled={busy || uncertain}
                onClick={() => void confirm()}
              >
                {t("Confirm import")}
              </button>
              <button className="br-btn" disabled={busy || uncertain} onClick={() => void reject()}>
                {t("Cancel import")}
              </button>
            </div>
          )}
          {proposal.status === "rejected" && (
            <p role="status">{t("Import cancelled. No items were created.")}</p>
          )}
          {(uncertain ||
            proposal.status === "executing" ||
            (proposal.status === "executed" && proposal.verification !== "verified")) && (
            <div className="space-y-3">
              <p className="text-sm">
                {t("Check the recorded result before taking another action.")}
              </p>
              <button className="br-btn" disabled={busy} onClick={() => void check()}>
                {t("Check import status")}
              </button>
              {proposal.verification === "recorded_unsettled" && (
                <button className="br-btn" disabled={busy} onClick={() => void reconcile()}>
                  {t("Recover recorded result")}
                </button>
              )}
            </div>
          )}
        </section>
      )}
      {inspection && <Inspector tenant={tenant} target={inspection} close={() => inspect(null)} />}
    </dialog>
  );
}

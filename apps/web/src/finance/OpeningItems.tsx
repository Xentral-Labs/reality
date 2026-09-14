import { useEffect, useRef, useState, type FormEvent } from "react";
import { formatMoney, t } from "../localization";
import { useRead } from "../unified/useCompanyContext";
import { ReadState } from "../unified/ReadState";

type Context = {
  revision: number;
  counterpart: { state: string } | null;
  parties: { id: string; name: string }[];
  more_parties: boolean;
};
type Item = {
  direction: string;
  currency: string;
  amount: string;
  reference: string;
  party?: string;
  document_id?: string;
  due_date?: string | null;
};
type Review = {
  source_namespace: string;
  snapshot_key: string;
  cutover_date: string;
  coverage_kind: string;
  reason: string;
  counterpart_account_code: string;
  unknown_due_dates: number;
  totals: Item[];
  items: Item[];
};
type Pending = { id: string; preview: { opening: Review } };
const directions = [
  "customer_debt",
  "customer_credit",
  "supplier_debt",
  "supplier_credit",
] as const;
const labels: Record<string, string> = {
  customer_debt: "Customer opening debt",
  customer_credit: "Customer opening credit",
  supplier_debt: "Supplier opening debt",
  supplier_credit: "Supplier opening credit",
};
async function request<T>(url: string, body?: unknown): Promise<T> {
  const response = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...(body === undefined ? {} : { method: "POST", body: JSON.stringify(body) }),
  });
  const result = await response.json();
  if (!response.ok)
    throw new Error(typeof result.detail === "string" ? result.detail : t("Request failed"));
  return result;
}
export function OpeningItems({
  tenant,
  close,
  explain,
}: {
  tenant: string;
  close: () => void;
  explain: (id: string) => void;
}) {
  const base = `/api/tenants/${encodeURIComponent(tenant)}`;
  const key = `reality:opening:${tenant}`;
  const dialog = useRef<HTMLDialogElement>(null);
  const next = useRef(1);
  const [rows, setRows] = useState([0]);
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState<Review | null>(null);
  const [pending, setPending] = useState<Pending | null>(() => {
    try {
      const saved = JSON.parse(sessionStorage.getItem(key) || "null");
      return typeof saved?.id === "string" && saved?.preview?.opening ? saved : null;
    } catch {
      return null;
    }
  });
  const read = useRead<Context>(
    () => request(`${base}/finance/opening/context?query=${encodeURIComponent(query)}`),
    [tenant, query],
  );
  const data = read.data;
  // Keep selected opaque party identities available when a subsequent search narrows choices.
  const [parties, setParties] = useState<Context["parties"]>([]);
  useEffect(() => {
    if (!data) return;
    const selected = new Set(
      Array.from(
        dialog.current?.querySelectorAll<HTMLSelectElement>("select[data-opening-party]") || [],
      ).map((element) => element.value),
    );
    setParties((old) => [
      ...new Map(
        [...old.filter((party) => selected.has(party.id)), ...data.parties].map((party) => [
          party.id,
          party,
        ]),
      ).values(),
    ]);
  }, [data]);
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  async function prepare(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!data || busy || read.loading) return;
    const form = new FormData(event.currentTarget);
    const get = (name: string) => String(form.get(name) || "");
    const values = {
      expected_revision: data.revision,
      source_namespace: get("namespace"),
      snapshot_key: get("snapshot"),
      cutover_date: get("cutover"),
      coverage_kind: get("coverage"),
      reason: get("reason"),
      items: rows.map((id) => ({
        party_id: get(`${id}:party`),
        direction: get(`${id}:direction`),
        currency: get(`${id}:currency`),
        amount: get(`${id}:amount`),
        external_item_key: get(`${id}:key`),
        reference: get(`${id}:reference`),
        original_document_date: get(`${id}:date`) || null,
        due_date: get(`${id}:due`) || null,
        original_total: get(`${id}:total`) || null,
        source_record_id: get(`${id}:source`) || null,
      })),
    };
    setBusy(true);
    setError("");
    try {
      const proposal = await request<Pending>(`${base}/finance/opening/proposals`, {
        tool: "finance.opening.import",
        arguments: values,
      });
      setPending(proposal);
      sessionStorage.setItem(key, JSON.stringify(proposal));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function decide(approve: boolean) {
    if (!pending || busy) return;
    setBusy(true);
    setError("");
    try {
      const result = await request<{ output: Review }>(
        `${base}/change-proposals/${pending.id}/${approve ? "approve" : "reject"}`,
        {},
      );
      sessionStorage.removeItem(key);
      setPending(null);
      if (approve) {
        setReceipt(result.output);
        window.dispatchEvent(new Event("reality:delivery-settled"));
      } else read.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const field = (
    name: string,
    label: string,
    required = false,
    type = "text",
    initial?: string,
  ) => (
    <label className="grid min-w-0 gap-1">
      {t(label)}
      <input
        className="br-control w-full min-w-0"
        name={name}
        type={type}
        required={required}
        defaultValue={initial}
      />
    </label>
  );
  const review = receipt || pending?.preview.opening;
  return (
    <dialog
      ref={dialog}
      aria-labelledby="opening-title"
      className="m-auto max-h-[90vh] w-[min(820px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) close();
      }}
    >
      <div className="mb-4 flex justify-between gap-3">
        <h2 id="opening-title" className="text-lg font-semibold">
          {t("Import opening positions")}
        </h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </div>
      <p className="mb-4 text-sm text-fg-muted">
        {t(
          "Enter outstanding amounts from the previous system. Opening positions create no payment, revenue or tax.",
        )}
      </p>
      {error && (
        <p role="alert" className="mb-4 text-red-600">
          {error}
        </p>
      )}
      {review ? (
        <>
          {receipt && (
            <p role="status" className="mb-4">
              {t("Opening positions recorded")}
            </p>
          )}
          <p>
            {review.source_namespace} · {review.snapshot_key} · {review.cutover_date}
          </p>
          <p className="my-3 whitespace-pre-wrap">{review.reason}</p>
          <p className="mb-3">
            {t("Opening coverage")}:{" "}
            {t(
              review.coverage_kind === "summary"
                ? "Summary per party and direction"
                : "Individual positions",
            )}
          </p>
          <p className="mb-3">
            {t("Neutral opening counterpart")}: {review.counterpart_account_code}
          </p>
          <p className="mb-3">
            {t("Unknown due dates")}: {review.unknown_due_dates}
          </p>
          <ul className="mb-4 grid gap-2">
            {review.totals.map((item) => (
              <li key={`${item.direction}:${item.currency}`}>
                {t(labels[item.direction])}: {formatMoney(item.amount, item.currency)}
              </li>
            ))}
          </ul>
          <ul className="mb-4 grid gap-2">
            {review.items.map((item, i) => (
              <li key={i} className="rounded border border-border-default p-3">
                <p>
                  {item.reference} · {item.party} · {t(labels[item.direction])} ·{" "}
                  {formatMoney(item.amount, item.currency)}
                </p>
                {!receipt && (
                  <p className="text-sm text-fg-muted">
                    {t("Due date")}: {item.due_date || t("Unknown")}
                  </p>
                )}
                {item.document_id && (
                  <button className="br-btn mt-2" onClick={() => explain(item.document_id!)}>
                    {t("Explain")}
                  </button>
                )}
              </li>
            ))}
          </ul>
          {!receipt && (
            <div className="flex flex-wrap gap-2">
              <button className="br-btn" disabled={busy} onClick={() => void decide(true)}>
                {t("Confirm opening positions")}
              </button>
              <button className="br-btn" disabled={busy} onClick={() => void decide(false)}>
                {t("Reject")}
              </button>
            </div>
          )}
        </>
      ) : !data ? (
        <ReadState loading={read.loading} error={read.error} retry={read.refresh} rows={5} />
      ) : (
        <form onSubmit={prepare} className="grid gap-4">
          {(!data.counterpart || data.counterpart.state !== "active") && (
            <p role="status">
              {t("Configure an active opening counterpart in company account settings first.")}
            </p>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            {field("namespace", "Previous system", true)}
            {field("snapshot", "Snapshot reference", true)}
            {field("cutover", "Cutover date", true, "date")}
            <label className="grid gap-1">
              {t("Opening coverage")}
              <select
                aria-label={t("Opening coverage")}
                name="coverage"
                className="br-control w-full"
              >
                <option value="individual">{t("Individual positions")}</option>
                <option value="summary">{t("Summary per party and direction")}</option>
              </select>
            </label>
          </div>
          <label className="grid gap-1">
            {t("Explanation")}
            <textarea name="reason" className="br-control w-full" required />
          </label>
          <label className="grid gap-1">
            {t("Find party")}
            <input
              className="br-control w-full"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          {data.more_parties && (
            <p className="text-sm text-fg-muted">{t("Refine the search to find more parties.")}</p>
          )}
          {rows.map((id, index) => (
            <fieldset key={id} className="grid gap-4 rounded-lg border border-border-default p-4">
              <legend>
                {t("Opening position")} {index + 1}
              </legend>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="grid min-w-0 gap-1">
                  {t("Party")}
                  <select
                    data-opening-party
                    aria-label={t("Party")}
                    name={`${id}:party`}
                    className="br-control w-full min-w-0"
                    required
                    defaultValue=""
                  >
                    <option value="">{t("Select party")}</option>
                    {parties.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="grid gap-1">
                  {t("Opening direction")}
                  <select
                    aria-label={t("Opening direction")}
                    name={`${id}:direction`}
                    className="br-control w-full"
                  >
                    {directions.map((d) => (
                      <option key={d} value={d}>
                        {t(labels[d])}
                      </option>
                    ))}
                  </select>
                </label>
                {field(`${id}:amount`, "Outstanding amount at cutover", true)}
                {field(`${id}:currency`, "Currency", true, "text", "EUR")}
                {field(`${id}:key`, "Stable original item reference", true)}
                {field(`${id}:reference`, "Document reference")}
              </div>
              <details>
                <summary>{t("Original evidence (optional)")}</summary>
                <div className="mt-3 grid gap-4 sm:grid-cols-2">
                  {field(`${id}:date`, "Original document date", false, "date")}
                  {field(`${id}:due`, "Original due date", false, "date")}
                  {field(`${id}:total`, "Original total")}
                  {field(`${id}:source`, "Source record ID")}
                </div>
              </details>
              <button
                type="button"
                className="br-btn justify-self-start"
                disabled={rows.length === 1 || busy}
                onClick={() => setRows(rows.filter((row) => row !== id))}
              >
                {t("Remove")}
              </button>
            </fieldset>
          ))}
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="br-btn"
              disabled={rows.length >= 100 || busy}
              onClick={() => setRows([...rows, next.current++])}
            >
              {t("Add opening position")}
            </button>
            <button
              className="br-btn"
              disabled={busy || read.loading || data.counterpart?.state !== "active"}
            >
              {t("Review opening positions")}
            </button>
            <button type="button" className="br-btn" disabled={busy} onClick={read.refresh}>
              {t("Reload")}
            </button>
          </div>
        </form>
      )}
    </dialog>
  );
}

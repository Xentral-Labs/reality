import { useEffect, useRef, useState } from "react";
import { formatExactDecimal, formatMoney, t } from "../localization";
import { ReadState } from "../unified/ReadState";
import { useRead } from "../unified/useCompanyContext";

// Spec 295: one company schedule, a reviewed run and the handover to collection.
// Every number here comes from the shared run preview; nothing is derived in the page.

type Level = { level: number; wait_days: number; fee_amount: string };
type Schedule = { revision: number; levels: Level[]; source_record_id: string | null };
type Item = {
  invoice_id: string;
  number: string;
  party_id: string;
  party: string;
  currency: string;
  open: string;
  days_overdue: number;
  previous_level: number | null;
  previous_notice_date: string | null;
  wait_days?: number;
  code?: string;
  eligible_on?: string;
};
type Notice = {
  party_id: string;
  party: string;
  currency: string;
  level: number;
  fee_amount: string;
  items: Item[];
};
type Context = {
  revision: number;
  run_date: string;
  schedule_source_record_id: string;
  notices: Notice[];
  ready_for_collection: Item[];
  left_out: Item[];
};
type Pending =
  | { kind: "schedule"; id: string; levels: Level[] }
  | {
      kind: "run";
      id: string;
      notices: Notice[];
      notSelected: string[];
      willSkip: { invoice_id: string; code: string }[];
    }
  | { kind: "collection"; id: string; party: string; items: Item[]; hold: string };
type Receipt = { notices: { id: string }[]; skipped: { invoice_id: string; code: string }[] };

function tf(source: string, values: Record<string, string | number>): string {
  return Object.entries(values).reduce(
    (text, [key, value]) => text.replaceAll(`{${key}}`, String(value)),
    t(source),
  );
}

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

// The clerk's calendar day, not the UTC one: a run just after midnight is today's.
function localToday(): string {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

const LEFT_OUT: Record<string, string> = {
  waiting: "Waiting period not over",
  credit_available: "Customer credit available; settle it first",
  in_collection: "In collection",
};
const SKIPPED: Record<string, string> = {
  paid: "Paid since the review",
  level_changed: "Reminded or reversed since the review",
  not_due: "No longer overdue or not in this run",
  in_collection: "In collection",
  credit_available: "Customer credit available; settle it first",
};

export function DunningRun({ tenant, close }: { tenant: string; close: () => void }) {
  const base = `/api/tenants/${encodeURIComponent(tenant)}`;
  const dialog = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [runDate, setRunDate] = useState(localToday);
  const [context, setContext] = useState<Context | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [pending, setPending] = useState<Pending | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [handoverParty, setHandoverParty] = useState("");
  const schedule = useRead<Schedule>(() => call(`${base}/finance/dunning/schedule`), [tenant]);

  useEffect(() => {
    const node = dialog.current;
    const previous = document.activeElement as HTMLElement;
    node?.showModal();
    return () => {
      node?.close();
      previous?.focus();
    };
  }, []);

  async function run<T>(action: () => Promise<T>): Promise<T | undefined> {
    if (busy) return undefined;
    setBusy(true);
    setError("");
    try {
      return await action();
    } catch (e) {
      setError(String((e as Error).message));
      return undefined;
    } finally {
      setBusy(false);
    }
  }

  function propose(tool: string, args: unknown) {
    return call<{ id: string; preview: Record<string, any> }>(
      `${base}/finance/commercial/proposals`,
      { tool, arguments: args },
    );
  }

  async function prepareRun(keepReceipt = false) {
    const read = await run(() =>
      call<Context>(`${base}/finance/dunning/run-context?run_date=${encodeURIComponent(runDate)}`),
    );
    if (!read) return;
    setContext(read);
    if (!keepReceipt) setReceipt(null);
    setSelected(new Set(read.notices.flatMap((n) => n.items.map((i) => i.invoice_id))));
  }

  async function reviewSchedule(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!schedule.data) return;
    const fields = new FormData(event.currentTarget);
    const levels = [1, 2, 3].map((level) => ({
      level,
      wait_days: String(fields.get(`wait-${level}`) || "0"),
      fee_amount: String(fields.get(`fee-${level}`) || "0"),
    }));
    const proposal = await run(() =>
      propose("finance.dunning.schedule.set", {
        expected_revision: schedule.data!.revision,
        levels,
      }),
    );
    if (proposal)
      setPending({
        kind: "schedule",
        id: proposal.id,
        levels: proposal.preview.dunning_schedule.proposed,
      });
  }

  async function reviewRun() {
    if (!context) return;
    const items = context.notices.flatMap((notice) =>
      notice.items
        .filter((item) => selected.has(item.invoice_id))
        .map((item) => ({ invoice_id: item.invoice_id, level: notice.level })),
    );
    const proposal = await run(() =>
      propose("finance.dunning.run", {
        schedule_source_record_id: context.schedule_source_record_id,
        run_date: context.run_date,
        items,
      }),
    );
    if (proposal)
      setPending({
        kind: "run",
        id: proposal.id,
        notices: proposal.preview.dunning_run.notices,
        notSelected: proposal.preview.dunning_run.not_selected,
        willSkip: proposal.preview.dunning_run.will_skip,
      });
  }

  async function reviewHandover(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!context || !schedule.data) return;
    const items = context.ready_for_collection.filter((i) => i.party_id === handoverParty);
    const fields = new FormData(event.currentTarget);
    const proposal = await run(() =>
      propose("finance.dunning.collection.handover", {
        expected_revision: context.revision,
        invoice_ids: items.map((item) => item.invoice_id),
        handover_date: context.run_date,
        reason: String(fields.get("reason") || ""),
      }),
    );
    if (proposal)
      setPending({
        kind: "collection",
        id: proposal.id,
        party: items[0]?.party ?? "",
        items,
        hold: proposal.preview.collection_handover.delivery_hold,
      });
  }

  async function decide(approve: boolean) {
    if (!pending) return;
    const decided = await run(() =>
      call<{ output?: Receipt }>(
        `${base}/change-proposals/${pending.id}/${approve ? "approve" : "reject"}`,
        {},
      ),
    );
    if (decided === undefined) return;
    const kind = pending.kind;
    setPending(null);
    setHandoverParty("");
    if (!approve) return;
    window.dispatchEvent(new Event("reality:delivery-settled"));
    if (kind === "schedule") {
      setEditing(false);
      setContext(null);
      schedule.refresh();
      return;
    }
    if (kind === "run" && decided.output) setReceipt(decided.output);
    schedule.refresh();
    await prepareRun(true);
  }

  const levels = schedule.data?.levels ?? [];
  const numberOf = (id: string) =>
    [
      ...(context?.notices.flatMap((n) => n.items) ?? []),
      ...(context?.ready_for_collection ?? []),
      ...(context?.left_out ?? []),
    ].find((item) => item.invoice_id === id)?.number ?? id;
  const collectionParties = [
    ...new Map((context?.ready_for_collection ?? []).map((i) => [i.party_id, i.party])),
  ];

  return (
    <dialog
      ref={dialog}
      aria-label={t("Dunning run")}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) close();
      }}
      className="m-auto max-h-[90vh] w-[min(820px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <div className="mb-5 flex justify-between gap-3">
        <h2 className="text-lg font-semibold">{t("Dunning run")}</h2>
        <button className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </div>
      {error && <p className="mb-4 text-red-600">{error}</p>}

      {pending ? (
        <section aria-label={t("Review")}>
          {pending.kind === "schedule" && (
            <>
              <h3 className="mb-3 font-semibold">{t("Review dunning schedule")}</h3>
              <ScheduleTable levels={pending.levels} />
            </>
          )}
          {pending.kind === "run" && (
            <>
              <h3 className="mb-3 font-semibold">{t("Review dunning run")}</h3>
              <p className="mb-2">
                {tf("{count} notices will be recorded.", { count: pending.notices.length })}
              </p>
              <NoticeList notices={pending.notices} />
              {pending.willSkip.map((item) => (
                <p key={item.invoice_id} className="text-sm text-fg-muted">
                  {numberOf(item.invoice_id)}: {t(SKIPPED[item.code] ?? item.code)}
                </p>
              ))}
              {pending.notSelected.length > 0 && (
                <p className="mb-3 text-sm text-fg-muted">
                  {tf("Not selected: {numbers}", {
                    numbers: pending.notSelected.map(numberOf).join(", "),
                  })}
                </p>
              )}
              <p className="mb-4 text-sm text-fg-muted">
                {t(
                  "Items paid, reminded or handed over since this review are skipped and named. No email is sent automatically.",
                )}
              </p>
            </>
          )}
          {pending.kind === "collection" && (
            <>
              <h3 className="mb-3 font-semibold">{t("Review handover to collection")}</h3>
              <p className="mb-2">
                {pending.party}: {pending.items.map((item) => item.number).join(", ")}
              </p>
              <p className="mb-4 text-sm text-fg-muted">
                {pending.hold === "placed"
                  ? t("The customer gets a delivery hold with the reason Collection.")
                  : t("The customer's active delivery hold is kept.")}
              </p>
            </>
          )}
          <p className="mb-4 text-sm text-fg-muted">
            {t("An authenticated company owner must approve or reject this finance proposal.")}
          </p>
          <div className="flex gap-2">
            <button className="br-btn" disabled={busy} onClick={() => void decide(true)}>
              {t("Confirm")}
            </button>
            <button className="br-btn" disabled={busy} onClick={() => void decide(false)}>
              {t("Reject")}
            </button>
          </div>
        </section>
      ) : !schedule.data ? (
        <ReadState
          loading={schedule.loading}
          error={schedule.error}
          retry={schedule.refresh}
          rows={4}
        />
      ) : editing || levels.length === 0 ? (
        <form className="grid gap-3" onSubmit={reviewSchedule} aria-label={t("Dunning schedule")}>
          <h3 className="font-semibold">{t("Dunning schedule")}</h3>
          <p className="text-sm text-fg-muted">
            {t(
              "Level 1 waits for days overdue; levels 2 and 3 wait for days since the last notice. The fee is fixed per level.",
            )}
          </p>
          {[1, 2, 3].map((level) => {
            const current = levels.find((row) => row.level === level);
            return (
              <div key={level} className="grid grid-cols-3 items-end gap-3">
                <span className="font-medium">
                  {t("Dunning level")} {level}
                </span>
                <label>
                  {t("Waiting days")}
                  <input
                    className="br-control mt-1 w-full"
                    name={`wait-${level}`}
                    inputMode="numeric"
                    defaultValue={current?.wait_days ?? (level === 1 ? 7 : 14)}
                    required
                  />
                </label>
                <label>
                  {t("Dunning fee")}
                  <input
                    className="br-control mt-1 w-full"
                    name={`fee-${level}`}
                    inputMode="decimal"
                    defaultValue={current ? Number(current.fee_amount) : 0}
                    required
                  />
                </label>
              </div>
            );
          })}
          <div className="flex gap-2">
            <button className="br-btn" disabled={busy}>
              {t("Review dunning schedule")}
            </button>
            {levels.length > 0 && (
              <button type="button" className="br-btn" onClick={() => setEditing(false)}>
                {t("Cancel")}
              </button>
            )}
          </div>
        </form>
      ) : (
        <>
          <section className="mb-5" aria-label={t("Dunning schedule")}>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="font-semibold">{t("Dunning schedule")}</h3>
              <button className="br-btn" onClick={() => setEditing(true)}>
                {t("Change schedule")}
              </button>
            </div>
            <ScheduleTable levels={levels} />
          </section>
          <div className="mb-5 flex items-end gap-3">
            <label>
              {t("Run date")}
              <input
                className="br-control mt-1"
                type="date"
                value={runDate}
                onChange={(event) => setRunDate(event.target.value)}
              />
            </label>
            <button className="br-btn" disabled={busy} onClick={() => void prepareRun()}>
              {t("Prepare dunning run")}
            </button>
          </div>
          {receipt && (
            <section
              className="mb-5 rounded-lg border border-border-default p-3"
              aria-live="polite"
            >
              <p>{tf("{count} notices recorded.", { count: receipt.notices.length })}</p>
              {receipt.skipped.map((item) => (
                <p key={item.invoice_id} className="text-sm text-fg-muted">
                  {numberOf(item.invoice_id)}: {t(SKIPPED[item.code] ?? item.code)}
                </p>
              ))}
            </section>
          )}
          {context && (
            <>
              <section className="mb-5" aria-label={t("Proposed notices")}>
                <h3 className="mb-2 font-semibold">{t("Proposed notices")}</h3>
                {context.notices.length === 0 ? (
                  <p className="text-sm text-fg-muted">{t("No item is due for a notice.")}</p>
                ) : (
                  <NoticeList
                    notices={context.notices}
                    selected={selected}
                    toggle={(id) =>
                      setSelected((current) => {
                        const next = new Set(current);
                        if (next.has(id)) next.delete(id);
                        else next.add(id);
                        return next;
                      })
                    }
                  />
                )}
                {context.notices.length > 0 && (
                  <button
                    className="br-btn"
                    disabled={busy || selected.size === 0}
                    onClick={() => void reviewRun()}
                  >
                    {t("Review dunning run")}
                  </button>
                )}
              </section>
              {collectionParties.length > 0 && (
                <section className="mb-5" aria-label={t("Ready for collection")}>
                  <h3 className="mb-2 font-semibold">{t("Ready for collection")}</h3>
                  {collectionParties.map(([party, name]) => (
                    <div key={party} className="mb-3">
                      <p>
                        {name}:{" "}
                        {context.ready_for_collection
                          .filter((item) => item.party_id === party)
                          .map(
                            (item) => `${item.number} (${formatMoney(item.open, item.currency)})`,
                          )
                          .join(", ")}
                      </p>
                      {handoverParty === party ? (
                        <form className="mt-2 flex items-end gap-2" onSubmit={reviewHandover}>
                          <label className="grow">
                            {t("Reason")}
                            <input className="br-control mt-1 w-full" name="reason" required />
                          </label>
                          <button className="br-btn" disabled={busy}>
                            {t("Review handover to collection")}
                          </button>
                        </form>
                      ) : (
                        <button className="br-btn mt-1" onClick={() => setHandoverParty(party)}>
                          {t("Hand over to collection")}
                        </button>
                      )}
                    </div>
                  ))}
                </section>
              )}
              {context.left_out.length > 0 && (
                <section aria-label={t("Left out")}>
                  <h3 className="mb-2 font-semibold">{t("Left out")}</h3>
                  <ul className="text-sm">
                    {context.left_out.map((item) => (
                      <li key={item.invoice_id}>
                        {item.party} · {item.number}:{" "}
                        {t(LEFT_OUT[item.code ?? ""] ?? item.code ?? "")}
                        {item.code === "waiting" && item.eligible_on
                          ? ` (${tf("due on {date}", { date: item.eligible_on })})`
                          : ""}
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </>
          )}
        </>
      )}
    </dialog>
  );
}

// The schedule states a bare fee; each notice charges it in its own currency.
function ScheduleTable({ levels }: { levels: Level[] }) {
  return (
    <table className="mb-3 w-full text-sm">
      <thead>
        <tr className="text-left text-fg-muted">
          <th>{t("Dunning level")}</th>
          <th>{t("Waiting days")}</th>
          <th>{t("Dunning fee")}</th>
        </tr>
      </thead>
      <tbody>
        {levels.map((level) => (
          <tr key={level.level}>
            <td>{level.level}</td>
            <td>{level.wait_days}</td>
            <td>{formatExactDecimal(level.fee_amount)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function NoticeList({
  notices,
  selected,
  toggle,
}: {
  notices: Notice[];
  selected?: Set<string>;
  toggle?: (id: string) => void;
}) {
  return (
    <div className="mb-3 grid gap-3">
      {notices.map((notice) => (
        <div
          key={`${notice.party_id}:${notice.currency}:${notice.level}`}
          className="rounded-lg border border-border-default p-3"
        >
          <div className="mb-1 font-medium">
            {notice.party} · {t("Dunning level")} {notice.level} · {t("Dunning fee")}{" "}
            {formatMoney(notice.fee_amount, notice.currency)}
          </div>
          {notice.items.map((item) => (
            <label key={item.invoice_id} className="flex items-center gap-2 text-sm">
              {toggle && (
                <input
                  type="checkbox"
                  checked={selected?.has(item.invoice_id) ?? false}
                  onChange={() => toggle(item.invoice_id)}
                />
              )}
              <span>
                {item.number} · {formatMoney(item.open, item.currency)} ·{" "}
                {tf("{days} days overdue", { days: item.days_overdue })}
                {item.previous_level
                  ? ` · ${tf("last notice level {level} on {date}", {
                      level: item.previous_level,
                      date: item.previous_notice_date ?? "",
                    })}`
                  : ""}
              </span>
            </label>
          ))}
        </div>
      ))}
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { api, companyCurrencyApi } from "../api";
import { t } from "../localization";
import { useRead } from "../unified/useCompanyContext";

// Spec 309: the currency the company keeps its books in. Stating it is the shared
// reviewed tool; it is refused once the company has posted anything.
export function CompanyCurrencySection({
  tenantId,
  canManage,
}: {
  tenantId: string;
  canManage: boolean;
}) {
  const [version, setVersion] = useState(0);
  const read = useRead(() => companyCurrencyApi.read(tenantId), [tenantId, version]);
  const [currency, setCurrency] = useState(""),
    [pending, setPending] = useState<{ id: string; current: string; proposed: string } | null>(
      null,
    ),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const open = useRef<string | null>(null);
  useEffect(
    () => () => {
      if (open.current)
        void api.rejectProposal(tenantId, open.current, null).catch(() => undefined);
    },
    [tenantId],
  );
  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (failure) {
      setError(t((failure as Error).message));
    } finally {
      setBusy(false);
    }
  };
  const state = read.data;
  return (
    <section className="rounded-lg border border-border-default p-4 text-sm" data-company-currency>
      <div className="font-medium text-fg-strong">{t("Company currency")}</div>
      <div className="mt-1">
        <strong>{state?.currency ?? "…"}</strong>{" "}
        <span className="text-fg-muted">
          {state?.has_postings
            ? t("Fixed: the company has posted in it.")
            : t("Can be changed until the first posting.")}
        </span>
      </div>
      {canManage && state && !state.has_postings && !pending && (
        <form
          className="mt-3 flex flex-wrap items-end gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            void run(async () => {
              const proposal = await companyCurrencyApi.prepare(tenantId, currency);
              const review = proposal.preview.company_currency as {
                current: string;
                proposed: string;
              };
              open.current = proposal.id;
              setPending({ id: proposal.id, ...review });
            });
          }}
        >
          <label className="block">
            {t("Currency code")}
            <input
              className="br-control mt-1 w-28"
              required
              maxLength={3}
              value={currency}
              onChange={(event) => setCurrency(event.target.value.toUpperCase())}
            />
          </label>
          <button className="br-btn" disabled={busy || currency.length !== 3}>
            {t("Review change")}
          </button>
        </form>
      )}
      {pending && (
        <div className="mt-3 space-y-2 rounded-lg bg-surface-muted p-3">
          <div>
            {pending.current} → <strong>{pending.proposed}</strong>
          </div>
          <div className="flex gap-2">
            <button
              className="br-btn br-btn-primary"
              disabled={busy}
              onClick={() =>
                void run(async () => {
                  await companyCurrencyApi.confirm(tenantId, pending.id);
                  open.current = null;
                  setPending(null);
                  setCurrency("");
                  setVersion((value) => value + 1);
                })
              }
            >
              {t("Confirm")}
            </button>
            <button
              className="br-btn"
              disabled={busy}
              onClick={() => {
                if (open.current)
                  void api.rejectProposal(tenantId, open.current, null).catch(() => undefined);
                open.current = null;
                setPending(null);
              }}
            >
              {t("Discard")}
            </button>
          </div>
        </div>
      )}
      {error && (
        <div role="alert" className="mt-2 text-danger">
          {error}
        </div>
      )}
    </section>
  );
}

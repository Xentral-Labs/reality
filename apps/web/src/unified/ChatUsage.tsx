import { useId, useRef, useState } from "react";
import { api, type ManagedAllowance, type UsageGrant } from "../api";
import { t, formatDateTime } from "../localization";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import type { Selection } from "./routing";

function UsageDetails({ allowance }: { allowance: ManagedAllowance }) {
  return (
    <div className="space-y-3 text-sm" data-usage-details>
      <p className="font-medium text-fg-strong">{t("Included AI questions")}</p>
      <p>
        {t("{used} of {limit} used")
          .replace("{used}", String(Math.min(allowance.used, allowance.limit)))
          .replace("{limit}", String(allowance.limit))}
      </p>
      <progress
        className="h-2 w-full accent-accent"
        value={Math.min(allowance.used, allowance.limit)}
        max={Math.max(1, allowance.limit)}
        aria-label={t("Usage")}
      />
      <p>
        {t("{remaining} of {limit} AI questions left")
          .replace(
            "{remaining}",
            String(allowance.base_remaining ?? Math.min(allowance.remaining, allowance.limit)),
          )
          .replace("{limit}", String(allowance.limit))}
      </p>
      {!!allowance.bonus_questions && (
        <p>{t("Total questions used today: {used}").replace("{used}", String(allowance.used))}</p>
      )}
      {!!allowance.bonus_questions && (
        <p>
          {t("{remaining} extra test questions left").replace(
            "{remaining}",
            String(allowance.bonus_remaining ?? 0),
          )}
        </p>
      )}
      <p className="text-xs text-fg-muted">
        {t("Resets at")} {formatDateTime(allowance.resets_at)}
      </p>
    </div>
  );
}

export function ChatUsage({
  allowance,
  navigate,
}: {
  allowance?: ManagedAllowance | null;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const id = useId();
  const panel = useRef<HTMLDivElement>(null);
  if (!allowance) return null;
  return (
    <div data-chat-usage>
      <button
        type="button"
        popoverTarget={id}
        aria-haspopup="dialog"
        className="whitespace-nowrap rounded-full border border-border-default px-3 py-1.5 text-xs text-fg-muted hover:bg-surface-muted hover:text-fg-strong"
        onClick={(event) => {
          const rect = event.currentTarget.getBoundingClientRect();
          if (panel.current) {
            panel.current.style.left = `${Math.max(8, Math.min(rect.right - 288, innerWidth - 296))}px`;
            panel.current.style.top = `${rect.bottom + 8}px`;
          }
        }}
      >
        {t("Usage")} · {t("{remaining} left").replace("{remaining}", String(allowance.remaining))}
      </button>
      <div
        ref={panel}
        id={id}
        popover="auto"
        role="dialog"
        aria-label={t("Usage")}
        className="fixed m-0 w-72 max-w-[calc(100vw-1rem)] rounded-xl border border-border-default bg-surface p-4 text-fg-strong shadow-xl"
      >
        <UsageDetails allowance={allowance} />
        <button
          className="br-btn mt-4 w-full"
          onClick={() => {
            panel.current?.hidePopover();
            navigate({ route: "settings", settingsView: "usage" });
          }}
        >
          {t("View usage")}
        </button>
      </div>
    </div>
  );
}

export function UsageSettings({ tenant }: { tenant: string }) {
  const [recipient, setRecipient] = useState("");
  const [email, setEmail] = useState("");
  const [mode, setMode] = useState<"self" | "admin">("self");
  const [questions, setQuestions] = useState(20);
  const [reason, setReason] = useState("");
  const [preview, setPreview] = useState<UsageGrant | null>(null);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const { data, loading, error, refresh } = useRead(
    () => api.usageStatus(tenant, recipient),
    [tenant, recipient],
  );
  const confirm = async () => {
    if (!preview || busy) return;
    setBusy(true);
    setFailure("");
    try {
      await api.grantUsage({ ...preview, confirmed: true });
      setPreview(null);
      window.dispatchEvent(new CustomEvent("reality:ai-usage-changed"));
      refresh();
    } catch (error) {
      setFailure((error as Error).message);
    } finally {
      setBusy(false);
    }
  };
  if (!data || loading)
    return (
      <div>
        <ReadState loading={loading} error={error} retry={refresh} />
        {recipient && (
          <button
            className="br-btn mt-3"
            onClick={() => {
              setRecipient("");
              setEmail("");
              setMode("self");
              setPreview(null);
            }}
          >
            {t("Cancel")}
          </button>
        )}
      </div>
    );
  const canSelf =
    !recipient && data.self_extensions_remaining > 0 && data.allowance?.remaining === 0;
  return (
    <section className="max-w-2xl space-y-6" data-usage-settings>
      {data.can_admin_grant && (
        <form
          className="flex flex-wrap items-end gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            setRecipient(email.trim());
            setMode(email.trim() ? "admin" : "self");
            setPreview(null);
            setFailure("");
          }}
        >
          <label className="flex-1 text-sm">
            {t("Recipient email (empty for your account)")}
            <input
              type="email"
              className="br-control mt-1 w-full"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              disabled={busy}
            />
          </label>
          <button className="br-btn" disabled={busy}>
            {t("View usage")}
          </button>
        </form>
      )}
      <p className="text-sm text-fg-muted" data-original-content>
        {data.recipient.name || data.recipient.email}
      </p>
      {data.allowance ? (
        <UsageDetails allowance={data.allowance} />
      ) : (
        <p className="text-sm text-fg-muted">
          {t("No included AI allowance is active for this company.")}
        </p>
      )}
      {data.allowance && (
        <div className="space-y-3 rounded-xl border border-border-default p-4" data-usage-extension>
          <h3 className="font-semibold">{t("Keep testing")}</h3>
          <p className="text-sm text-fg-muted">
            {t("{remaining} of 3 one-time extensions left").replace(
              "{remaining}",
              String(data.self_extensions_remaining),
            )}
          </p>
          <p className="text-sm text-fg-muted">
            {t("Extra questions expire at the next daily reset.")}
          </p>
          {data.can_admin_grant && !preview && (
            <label className="block text-sm">
              {t("Extension type")}
              <select
                className="br-control ml-2"
                aria-label={t("Extension type")}
                value={mode}
                onChange={(event) => setMode(event.target.value as "self" | "admin")}
              >
                {!recipient && <option value="self">{t("Self-service extension")}</option>}
                <option value="admin">{t("Admin grant")}</option>
              </select>
            </label>
          )}
          {mode === "admin" && data.can_admin_grant && !preview && (
            <div className="space-y-3">
              <label className="block text-sm">
                {t("Extra questions")}
                <select
                  className="br-control ml-2"
                  aria-label={t("Extra questions")}
                  value={questions}
                  onChange={(event) => setQuestions(Number(event.target.value))}
                >
                  <option value={20}>20</option>
                  <option value={100}>100</option>
                </select>
              </label>
              <label className="block text-sm">
                {t("Reason")}
                <input
                  className="br-control mt-1 w-full"
                  value={reason}
                  maxLength={500}
                  onChange={(event) => setReason(event.target.value)}
                />
              </label>
            </div>
          )}
          {preview ? (
            <div className="space-y-3" data-usage-confirmation>
              <p>
                {t("Add {count} test questions?").replace("{count}", String(preview.questions))}
              </p>
              <p className="text-sm text-fg-muted">
                {t("Expires")} {formatDateTime(data.allowance.resets_at)}
              </p>
              <p className="text-sm" data-original-content>
                {data.recipient.email} ·{" "}
                {preview.mode === "self" ? t("Continued testing") : preview.reason}
              </p>
              <div className="flex gap-2">
                <button
                  className="br-btn br-btn-primary"
                  disabled={busy}
                  onClick={() => void confirm()}
                >
                  {t("Confirm")}
                </button>
                <button
                  className="br-btn"
                  disabled={busy}
                  onClick={() => {
                    setPreview(null);
                    setFailure("");
                  }}
                >
                  {t("Cancel")}
                </button>
              </div>
            </div>
          ) : (
            <button
              className="br-btn"
              disabled={
                loading || (mode === "self" ? !canSelf : !data.can_admin_grant || !reason.trim())
              }
              onClick={() =>
                setPreview({
                  tenant_id: tenant,
                  request_key: crypto.randomUUID(),
                  confirmed: false,
                  mode,
                  questions: mode === "self" ? data.self_extension_questions : questions,
                  reason: mode === "self" ? "" : reason.trim(),
                  recipient_email: recipient,
                })
              }
            >
              {mode === "self" ? t("Get 20 more questions") : t("Review grant")}
            </button>
          )}
          {failure && (
            <p role="alert" className="text-sm text-critical-text">
              {failure}
            </p>
          )}
        </div>
      )}
      <div className="space-y-3" data-usage-history>
        <h3 className="font-semibold">{t("Extension history")}</h3>
        {!data.history.length && <p className="text-sm text-fg-muted">{t("No extensions yet.")}</p>}
        {data.history.map((row) => (
          <article key={row.id} className="rounded-lg border border-border-default p-3 text-sm">
            <p>
              <strong>+{row.questions}</strong> ·{" "}
              <span title={row.actor_user_id} data-original-content>
                {row.actor_name}
              </span>{" "}
              · {t(row.mode === "self" ? "Self-service extension" : "Admin grant")}
            </p>
            <p className="text-fg-muted">
              {formatDateTime(row.occurred_at)} · {t("Expires")} {formatDateTime(row.expires_at)}
            </p>
            <p data-original-content>{row.mode === "self" ? t("Continued testing") : row.reason}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

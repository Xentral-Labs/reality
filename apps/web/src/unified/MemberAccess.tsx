import { useEffect, useRef, useState } from "react";
import { api, APIError, type CompanyAccess } from "../api";
import { formatDateTime, t } from "../localization";
import { ReadState } from "./ReadState";

type Action = { kind: "invite" | "resend" | "revoke" | "remove"; email: string; id?: string };
const titles = {
  invite: "Review invitation",
  resend: "Resend",
  revoke: "Revoke",
  remove: "Remove",
};
const descriptions = {
  invite: "Send an invitation to this email address? Access starts only after acceptance.",
  resend: "Send a new invitation link? The previous link will stop working.",
  revoke: "Revoke this invitation? Its link will stop working.",
  remove: "Remove this member's access to this company? Their other companies remain accessible.",
};
function statusLabel(status: string) {
  const labels: Record<string, string> = {
    pending: "Pending",
    expired: "Expired",
    processing: "Sending invitation",
    delivered: "Invitation delivered",
    retry: "Delivery retry scheduled",
    failed: "Failed",
  };
  return t(labels[status] || "Unknown");
}
export function MemberAccess({
  tenant,
  companyName,
  onBusyChange,
}: {
  tenant: string;
  companyName: string;
  onBusyChange?: (blocked: boolean) => void;
}) {
  const [data, setData] = useState<CompanyAccess | null>(null);
  const [readError, setReadError] = useState("");
  const [revision, setRevision] = useState(0);
  const [email, setEmail] = useState("");
  const [action, setAction] = useState<Action | null>(null);
  const [busy, setBusy] = useState(false);
  const [unknown, setUnknown] = useState(false);
  const [message, setMessage] = useState("");
  const [notice, setNotice] = useState("");
  useEffect(() => {
    onBusyChange?.(busy || unknown);
  }, [busy, unknown, onBusyChange]);
  const lock = useRef(false);
  const reviewPanel = useRef<HTMLElement>(null);
  useEffect(() => {
    if (action) reviewPanel.current?.focus();
  }, [action]);
  useEffect(() => {
    let active = true;
    setReadError("");
    api
      .companyAccess(tenant)
      .then((result) => {
        if (active) setData(result);
      })
      .catch((error) => {
        if (active) setReadError(error.message);
      });
    return () => {
      active = false;
    };
  }, [tenant, revision]);
  const select = (next: Action) => {
    setAction(next);
    setMessage("");
    setNotice("");
  };
  const recover = async () => {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    try {
      const result = await api.companyAccess(tenant);
      setData(result);
      setUnknown(false);
      setAction(null);
      setMessage("");
      setNotice("Current access loaded. Review the list before another action.");
    } catch {
      setMessage("Could not check current access. Try checking again.");
    } finally {
      lock.current = false;
      setBusy(false);
    }
  };
  const execute = async () => {
    if (!action || lock.current || unknown) return;
    lock.current = true;
    setBusy(true);
    setMessage("");
    let accepted = false;
    try {
      if (action.kind === "invite") await api.inviteMember(tenant, action.email);
      if (action.kind === "resend") await api.resendInvitation(tenant, action.id!);
      if (action.kind === "revoke") await api.revokeInvitation(tenant, action.id!);
      if (action.kind === "remove") await api.removeMember(tenant, action.id!);
      accepted = true;
      const result = await api.companyAccess(tenant);
      setData(result);
      setAction(null);
      setEmail("");
      setNotice(
        action.kind === "invite" || action.kind === "resend"
          ? "Invitation request accepted. Check delivery status below."
          : "Company access updated.",
      );
    } catch (error) {
      if (!accepted && error instanceof APIError && error.status >= 400 && error.status < 500)
        setMessage(error.message);
      else {
        setUnknown(true);
        setMessage("The result needs checking. Check current access before another action.");
      }
    } finally {
      lock.current = false;
      setBusy(false);
    }
  };
  if (!data)
    return (
      <ReadState
        loading={!readError}
        error={readError}
        retry={() => setRevision((value) => value + 1)}
      />
    );
  return (
    <div className="space-y-6">
      <form
        className="space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          select({ kind: "invite", email: email.trim() });
        }}
      >
        <label className="block text-sm">
          {t("Work email")}
          <input
            type="email"
            required
            maxLength={320}
            className="br-control mt-2 w-full"
            value={email}
            disabled={!!action || busy}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <button className="br-btn br-btn-primary" disabled={!!action || busy || !email.trim()}>
          {t("Review invitation")}
        </button>
      </form>
      {action && (
        <section
          ref={reviewPanel}
          tabIndex={-1}
          aria-label={t(titles[action.kind])}
          className="space-y-4 rounded-lg border border-accent bg-accent-soft p-4"
        >
          <h3 className="font-semibold">{t(titles[action.kind])}</h3>
          <p className="break-words text-sm">{companyName}</p>
          <p className="break-all font-medium">{action.email}</p>
          <p className="text-sm">{t(descriptions[action.kind])}</p>
          {message && (
            <p role="alert" className="break-words text-sm">
              {t(message)}
            </p>
          )}
          <div className="flex flex-wrap gap-3">
            <button
              className="br-btn br-btn-primary"
              disabled={busy || unknown}
              onClick={() => void execute()}
            >
              {t(busy ? "Saving…" : "Confirm")}
            </button>
            <button
              className="br-btn"
              disabled={busy || unknown}
              onClick={() => {
                setAction(null);
                setMessage("");
              }}
            >
              {t("Cancel")}
            </button>
            {unknown && (
              <button className="br-btn" disabled={busy} onClick={() => void recover()}>
                {t("Check current access")}
              </button>
            )}
          </div>
        </section>
      )}
      {notice && (
        <p role="status" className="text-sm text-fg-muted">
          {t(notice)}
        </p>
      )}
      <p className="text-sm text-fg-muted">
        {t("This view shows up to 500 members and 500 invitations.")}
      </p>
      <div>
        <h3 className="font-medium">{t("Active members")}</h3>
        {data.members.length ? (
          <ul className="mt-3 divide-y divide-border-default">
            {data.members.map((member) => (
              <li
                key={member.id}
                className="flex flex-wrap items-center justify-between gap-3 py-3 text-sm"
              >
                <div className="min-w-0">
                  <p className="break-words font-medium">{member.display_name || member.email}</p>
                  <p className="break-all text-fg-muted">{member.email}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-fg-muted">
                    {t(member.role === "owner" ? "Owner" : "Member")}
                  </span>
                  {member.role !== "owner" && (
                    <button
                      className="br-btn"
                      disabled={!!action || busy}
                      onClick={() => select({ kind: "remove", email: member.email, id: member.id })}
                    >
                      {t("Remove")}
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-fg-muted">{t("No active members.")}</p>
        )}
      </div>
      <div>
        <h3 className="font-medium">{t("Invitations")}</h3>
        {data.invitations.length ? (
          <ul className="mt-3 divide-y divide-border-default">
            {data.invitations.map((invite) => (
              <li key={invite.id} className="space-y-2 py-3 text-sm">
                <p className="break-all font-medium">{invite.email}</p>
                <p className="text-fg-muted">
                  {t("Status")}: {statusLabel(invite.status)} · {t("Invitation delivery")}:{" "}
                  {statusLabel(invite.delivery_status)}
                </p>
                <p className="text-fg-muted">
                  {t("Expires")}: {formatDateTime(invite.expires_at)}
                </p>
                <div className="flex flex-wrap gap-3">
                  {["pending", "expired"].includes(invite.status) && (
                    <button
                      className="br-btn"
                      disabled={!!action || busy}
                      onClick={() => select({ kind: "resend", email: invite.email, id: invite.id })}
                    >
                      {t("Resend")}
                    </button>
                  )}
                  {invite.status === "pending" && (
                    <button
                      className="br-btn"
                      disabled={!!action || busy}
                      onClick={() => select({ kind: "revoke", email: invite.email, id: invite.id })}
                    >
                      {t("Revoke")}
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-fg-muted">{t("No invitations.")}</p>
        )}
      </div>
    </div>
  );
}

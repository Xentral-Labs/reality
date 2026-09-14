import {
  readLanguage,
  rememberLanguage,
  languageHref,
  setLanguageFallback,
} from "../../shared/language";
import { type FormEvent, type ReactNode, useEffect, useState } from "react";
import { ArrowRight, Check, Clock3, LogOut, ShieldCheck } from "lucide-react";
import { api, type AuthUser, type PlatformOverview } from "./api";
import { LogoMark } from "./components/LogoMark";
import { LocalizationProvider, type Language } from "./localization";
import { accountDestination, resolveEntry, rememberAccountDestination } from "./entryRouting";
import "./auth.css";
import "./access-capacity.css";

const publicLocales = { en: "en-GB", de: "de-DE", nl: "nl-NL", es: "es-ES" } as const;

function rememberPreferences(user: AuthUser) {
  setLanguageFallback(user.language);
  const effective = { ...user, language: readLanguage() ?? user.language };
  return effective;
}

function localizedAccountDestination(fallback: string): string {
  const destination = new URL(accountDestination(fallback), location.origin);
  return languageHref(destination.href, readLanguage() ?? "en");
}

function invitationToken() {
  const fromFragment = new URLSearchParams(location.hash.replace(/^#/, "")).get("token");
  if (fromFragment) {
    sessionStorage.setItem("reality.invitationToken", fromFragment);
    history.replaceState(null, "", "/invitation");
  }
  return fromFragment || sessionStorage.getItem("reality.invitationToken") || "";
}

function LocalizedAuth({ user, children }: { user?: AuthUser; children: ReactNode }) {
  const language: Language = readLanguage() ?? user?.language ?? "en";
  return (
    <LocalizationProvider
      preferences={{
        language,
        locale: user?.locale ?? publicLocales[language],
        timezone: user?.timezone ?? "UTC",
      }}
    >
      {children}
    </LocalizationProvider>
  );
}

export function AuthGate({
  children,
}: {
  children: (user: AuthUser, updated: (user: AuthUser) => void) => ReactNode;
}) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    api
      .me()
      .then((value) => {
        setUser(rememberPreferences(value));
      })
      .catch(() => setUser(null))
      .finally(() => setReady(true));
  }, []);
  if (!ready) return <AuthLoading />;
  const path = location.pathname;
  if (!user) rememberAccountDestination();
  if (
    resolveEntry(new URL(location.href)).kind === "retired" &&
    (user?.status === "active" || user?.status === "pending_approval")
  )
    return <>{children(user, setUser)}</>;
  const inviteToken = path === "/invitation" ? invitationToken() : "";
  if (path === "/invitation" && user)
    return (
      <LocalizedAuth user={user}>
        <InvitationAcceptance token={inviteToken} />
      </LocalizedAuth>
    );
  if (path === "/invitation" && !user)
    return (
      <LocalizedAuth>
        <InvitationEntry token={inviteToken} />
      </LocalizedAuth>
    );
  if (user?.status === "active") {
    if (path === "/profile") {
      location.replace(
        languageHref(
          new URL("/app/settings?settings_view=personal", location.origin).href,
          readLanguage() ?? user.language,
        ),
      );
      return <AuthLoading />;
    }
    if (path === "/admin" && user.is_platform_admin) return <PlatformAdmin user={user} />;
    if (path === "/admin/access" && user.is_platform_admin) return <AccessAdmin user={user} />;
    if (["/signup", "/login", "/verify-email", "/access-pending"].includes(path)) {
      location.replace(localizedAccountDestination("/app"));
      return <AuthLoading />;
    }
    return (
      <>
        {children(user, (value) => {
          rememberLanguage(value.language);
          setUser(value);
        })}
      </>
    );
  }
  if (user?.status === "pending_approval")
    return (
      <LocalizedAuth user={user}>
        <Pending user={user} changed={setUser} />
      </LocalizedAuth>
    );
  if (resolveEntry(new URL(location.href)).kind === "retired" && !user)
    return (
      <LocalizedAuth>
        <Login complete={setUser} />
      </LocalizedAuth>
    );
  if (path === "/verify-email")
    return (
      <LocalizedAuth>
        <Verify complete={setUser} />
      </LocalizedAuth>
    );
  if (
    path === "/login" ||
    path === "/app" ||
    path.startsWith("/app/") ||
    (path !== "/" && resolveEntry(new URL(location.href)).kind === "redirect")
  )
    return (
      <LocalizedAuth>
        <Login complete={setUser} />
      </LocalizedAuth>
    );
  return (
    <LocalizedAuth>
      <Signup />
    </LocalizedAuth>
  );
}

function Brand() {
  const siteHref = languageHref(__SITE_URL__, readLanguage() ?? "en");
  return (
    <a className="auth-brand" href={siteHref}>
      <span>
        <LogoMark />
      </span>
      <strong>Reality</strong>
    </a>
  );
}
function AuthLoading() {
  return (
    <div className="auth-loading">
      <span />
    </div>
  );
}

function AuthShell({
  eyebrow,
  title,
  detail,
  live,
  children,
}: {
  eyebrow: string;
  title: string;
  detail: string;
  live?: boolean;
  children: ReactNode;
}) {
  return (
    <main className="auth-page">
      <Brand />
      <section className="auth-story">
        <p>{eyebrow}</p>
        <h1>
          Let agents run the business.
          <br />
          <em>Stay in control.</em>
        </h1>
        <span>One operational core for facts, decisions and accountable automation.</span>
      </section>
      <section className="auth-card">
        <p className="auth-eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        <p role={live ? "status" : undefined}>{detail}</p>
        {children}
      </section>
    </main>
  );
}

function Signup() {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [invitedEmail, setInvitedEmail] = useState("");
  useEffect(() => {
    const token = sessionStorage.getItem("reality.invitationToken") || "";
    if (!token) return;
    void api
      .inspectInvitation(token)
      .then((result) => setInvitedEmail(result.status === "pending" ? result.email || "" : ""))
      .catch(() => setInvitedEmail(""));
  }, []);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);
    try {
      const email = String(data.get("email"));
      const token = sessionStorage.getItem("reality.invitationToken") || "";
      const result = token
        ? await api.invitationSignup(token, email, String(data.get("password")))
        : await api.signup(email, String(data.get("password")));
      sessionStorage.setItem("reality.signupEmail", email);
      if (result.verification_code)
        sessionStorage.setItem("reality.localVerificationCode", result.verification_code);
      location.href = "/verify-email";
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <AuthShell
      eyebrow="Create account"
      title="Start with Reality"
      detail="Create your account. We review every new workspace personally."
    >
      <form onSubmit={submit} className="auth-form">
        <label>
          Work email
          <input
            name="email"
            type="email"
            autoComplete="email"
            defaultValue={invitedEmail}
            key={invitedEmail}
            readOnly={Boolean(invitedEmail)}
            required
          />
          {invitedEmail && <small>Your invitation is bound to this address.</small>}
        </label>
        <label>
          Password
          <input
            name="password"
            type="password"
            autoComplete="new-password"
            minLength={10}
            required
          />
          <small>At least 10 characters.</small>
        </label>
        {error && <div className="auth-error">{error}</div>}
        <label className="auth-check">
          <input type="checkbox" required />I agree to the Terms and Privacy Policy.
        </label>
        <button disabled={busy}>
          {busy ? "Creating account…" : "Continue"}
          <ArrowRight size={17} />
        </button>
      </form>
      <p className="auth-alternative">
        Already have an account? <a href="/login">Sign in</a>
      </p>
    </AuthShell>
  );
}

function Verify({ complete }: { complete: (user: AuthUser) => void }) {
  const [code, setCode] = useState(
    () => sessionStorage.getItem("reality.localVerificationCode") || "",
  );
  const [error, setError] = useState("");
  const email = sessionStorage.getItem("reality.signupEmail") || "";
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      const token = sessionStorage.getItem("reality.invitationToken") || "";
      const user = await api.verifyEmail(email, code, token || undefined);
      rememberPreferences(user);
      complete(user);
      location.href = token
        ? "/invitation"
        : localizedAccountDestination(user.status === "active" ? "/app" : "/access-pending");
    } catch (reason) {
      setError((reason as Error).message);
    }
  };
  return (
    <AuthShell
      eyebrow="Verify email"
      title="Check your inbox"
      detail={`Enter the six-digit code sent to ${email}.`}
    >
      <form onSubmit={submit} className="auth-form">
        <label>
          Verification code
          <input
            className="auth-code"
            inputMode="numeric"
            maxLength={6}
            pattern="[0-9]{6}"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            autoFocus
            required
          />
        </label>
        {error && <div className="auth-error">{error}</div>}
        <button>
          Verify email
          <ArrowRight size={17} />
        </button>
      </form>
    </AuthShell>
  );
}

function Login({ complete }: { complete: (user: AuthUser) => void }) {
  const [error, setError] = useState("");
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    try {
      const user = await api.login(String(data.get("email")), String(data.get("password")));
      rememberPreferences(user);
      complete(user);
      location.href = sessionStorage.getItem("reality.invitationToken")
        ? "/invitation"
        : localizedAccountDestination(user.status === "active" ? "/app" : "/access-pending");
    } catch (reason) {
      setError((reason as Error).message);
    }
  };
  return (
    <AuthShell eyebrow="Welcome back" title="Sign in" detail="Continue to your Reality workspace.">
      <form onSubmit={submit} className="auth-form">
        <label>
          Email
          <input name="email" type="email" autoComplete="email" required />
        </label>
        <label>
          Password
          <input name="password" type="password" autoComplete="current-password" required />
        </label>
        {error && <div className="auth-error">{error}</div>}
        <button>
          Sign in
          <ArrowRight size={17} />
        </button>
      </form>
      <p className="auth-alternative">
        New to Reality? <a href="/signup">Create account</a>
      </p>
    </AuthShell>
  );
}

type InvitationState =
  | { status: "loading" }
  | { status: "pending"; company: string; email: string }
  | { status: "unavailable" };

function InvitationEntry({ token }: { token: string }) {
  const [state, setState] = useState<InvitationState>({ status: "loading" });
  useEffect(() => {
    if (!token) {
      setState({ status: "unavailable" });
      return;
    }
    void api
      .inspectInvitation(token)
      .then((result) =>
        setState(
          result.status === "pending"
            ? {
                status: "pending",
                company: result.company_name || "",
                email: result.email || "",
              }
            : { status: "unavailable" },
        ),
      )
      .catch(() => setState({ status: "unavailable" }));
  }, [token]);
  const title =
    state.status === "loading"
      ? "Checking invitation…"
      : state.status === "unavailable"
        ? "Invitation unavailable"
        : state.company
          ? `Join ${state.company}`
          : "Join this company";
  const detail =
    state.status === "loading"
      ? "One moment while we check your invitation link."
      : state.status === "unavailable"
        ? "This invitation is no longer valid. Ask a company owner to send you a new one."
        : "Sign in or create an account with the invited email. Membership is granted only after you accept.";
  return (
    <AuthShell eyebrow="Company invitation" title={title} detail={detail} live>
      {state.status === "pending" && state.email && (
        <p className="auth-invited-as">
          Invited as <strong>{state.email}</strong>
        </p>
      )}
      {state.status !== "loading" && (
        <>
          <a className="auth-submit" href="/login">
            Sign in
          </a>
          {state.status === "pending" && (
            <a className="auth-secondary" href="/signup">
              Create account
            </a>
          )}
          <button
            className="auth-text-button"
            onClick={() => {
              sessionStorage.removeItem("reality.invitationToken");
              location.href = "/login";
            }}
          >
            Cancel invitation
          </button>
        </>
      )}
    </AuthShell>
  );
}

function InvitationAcceptance({ token }: { token: string }) {
  const [error, setError] = useState("");
  return (
    <AuthShell
      eyebrow="Company invitation"
      title="Accept invitation"
      detail="Confirm that you want to join this company."
    >
      {error && (
        <div className="auth-error" role="alert">
          {error}
        </div>
      )}
      <button
        className="auth-submit"
        onClick={async () => {
          try {
            const result = await api.acceptInvitation(token);
            sessionStorage.removeItem("reality.invitationToken");
            localStorage.setItem("reality.tenant", result.company.id);
            location.href = `/app?tenant=${encodeURIComponent(result.company.id)}`;
          } catch (reason) {
            setError((reason as Error).message);
          }
        }}
      >
        Accept invitation
      </button>
      <button
        className="auth-text-button"
        onClick={() => {
          sessionStorage.removeItem("reality.invitationToken");
          location.href = "/app";
        }}
      >
        Cancel
      </button>
    </AuthShell>
  );
}

function Pending({ user, changed }: { user: AuthUser; changed: (user: AuthUser | null) => void }) {
  const [saved, setSaved] = useState(false);
  const app = user.application;
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    const next = await api.updateApplication({
      ...data,
      language: user.language,
      locale: user.locale,
      timezone: user.timezone,
    });
    changed(next);
    setSaved(true);
  };
  return (
    <AuthShell
      eyebrow="Access requested"
      title="You’re on the list"
      detail="Tell us where you want to use Reality. You’ll receive access after a personal review."
    >
      <div className="pending-state">
        <Clock3 />
        <div>
          <strong>Review pending</strong>
          <span>We will email you when your workspace is unlocked.</span>
        </div>
      </div>
      <form onSubmit={submit} className="auth-form compact">
        <label>
          Your name
          <input name="display_name" defaultValue={user.display_name} />
        </label>
        <label>
          Company
          <input name="company_name" defaultValue={app?.company_name} />
        </label>
        <label>
          Company website
          <input
            name="company_website"
            defaultValue={app?.company_website}
            placeholder="https://"
          />
        </label>
        <label>
          Orders per day
          <select name="orders_per_day" defaultValue={app?.orders_per_day}>
            <option value="">Select volume</option>
            <option>Under 1,000</option>
            <option>1,000–5,000</option>
            <option>5,000–20,000</option>
            <option>20,000+</option>
          </select>
        </label>
        <button>
          {saved ? (
            <>
              <Check size={17} />
              Saved
            </>
          ) : (
            "Save details"
          )}
        </button>
      </form>
      <button
        className="auth-text-button"
        onClick={async () => {
          await api.logout();
          changed(null);
          location.href = "/login";
        }}
      >
        <LogOut size={16} />
        Sign out
      </button>
    </AuthShell>
  );
}

function AccessAdmin({ user }: { user: AuthUser }) {
  const [rows, setRows] = useState<AuthUser[] | null>(null);
  const [capacity, setCapacity] = useState<{ used: number; limit: number } | null>(null);
  const load = () =>
    Promise.all([api.accessApplications().then(setRows), api.accessCapacity().then(setCapacity)]);
  useEffect(() => {
    void load();
  }, []);
  return (
    <AdminShell
      user={user}
      active="access"
      title="Access applications"
      lead="The first verified accounts are admitted automatically. After that, applications wait for your decision."
    >
      {capacity && capacity.limit > 0 && (
        <div className="access-capacity">
          <strong>
            {capacity.used} of {capacity.limit}
          </strong>
          <span>automatic access slots used</span>
          <i style={{ width: `${Math.min(100, (capacity.used / capacity.limit) * 100)}%` }} />
        </div>
      )}
      <div className="application-list">
        {rows?.map((row) => (
          <article key={row.id}>
            <div>
              <strong>{row.display_name || row.email}</strong>
              <span>
                {row.application?.company_name || "No company details"} ·{" "}
                {row.application?.orders_per_day || "Volume unknown"}
              </span>
              <small>{row.email}</small>
            </div>
            <em className={`status-${row.application?.status}`}>{row.application?.status}</em>
            {row.application?.status === "pending" && (
              <div>
                <button
                  onClick={async () => {
                    await api.reviewAccess(row.application!.id, "reject");
                    load();
                  }}
                >
                  Reject
                </button>
                <button
                  className="approve"
                  onClick={async () => {
                    await api.reviewAccess(row.application!.id, "approve");
                    load();
                  }}
                >
                  <ShieldCheck size={16} />
                  Approve
                </button>
              </div>
            )}
          </article>
        ))}
      </div>
    </AdminShell>
  );
}

function AdminShell({
  user,
  active,
  title,
  lead,
  children,
}: {
  user: AuthUser;
  active: "overview" | "access";
  title: string;
  lead: string;
  children: ReactNode;
}) {
  return (
    <main className="admin-page">
      <header>
        <Brand />
        <div>
          <a href="/app">Workspace</a>
          <a href="/profile">{user.email}</a>
        </div>
      </header>
      <section>
        <p className="auth-eyebrow">Platform administration</p>
        <h1>{title}</h1>
        <p>{lead}</p>
        <nav className="admin-nav">
          <a className={active === "overview" ? "current" : ""} href="/admin">
            Overview
          </a>
          <a className={active === "access" ? "current" : ""} href="/admin/access">
            Access applications
          </a>
        </nav>
        {children}
      </section>
    </main>
  );
}

const adminTime = new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" });

function stamp(value: string | null) {
  return value ? adminTime.format(new Date(value)) : "—";
}

function elapsed(value: string | null) {
  if (!value) return "—";
  const days = Math.floor((Date.now() - new Date(value).getTime()) / 86400000);
  return days <= 0 ? "today" : `${days} d ago`;
}

function Panel({ title, hint, children }: { title: string; hint: string; children: ReactNode }) {
  return (
    <article className="admin-panel">
      <h2>{title}</h2>
      <p>{hint}</p>
      {children}
    </article>
  );
}

function Stat({ label, value, tone }: { label: string; value: number | string; tone?: string }) {
  return (
    <div className={tone ? `admin-stat ${tone}` : "admin-stat"}>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function DeploymentPanel({ deployment }: { deployment: PlatformOverview["deployment"] }) {
  const schema = deployment.migrations_current
    ? `current · ${deployment.database_revision}`
    : `behind head · ${deployment.database_revision ?? "unknown"} → ${deployment.expected_revision ?? "unknown"}`;
  const mail = `${deployment.email_provider} · sender ${
    deployment.email_sender_configured ? "set" : "missing"
  } · credential ${deployment.email_credential_configured ? "set" : "missing"}`;
  const flags = [
    { label: "Database schema", value: schema, tone: deployment.migrations_current ? "" : "bad" },
    {
      label: "Master key",
      value: deployment.master_key_configured
        ? "configured"
        : "missing — encrypted credentials stay unreadable",
      tone: deployment.master_key_configured ? "" : "bad",
    },
    {
      label: "Authentication",
      value: deployment.auth_mode,
      tone: deployment.auth_mode === "enabled" ? "" : "warn",
    },
    {
      label: "Session cookies",
      value: deployment.cookie_secure === "true" ? "secure" : "not marked secure",
      tone: deployment.cookie_secure === "true" ? "" : "warn",
    },
    {
      label: "Verification codes",
      value: deployment.auth_expose_codes === "true" ? "returned by the API" : "kept private",
      tone: deployment.auth_expose_codes === "true" ? "warn" : "",
    },
    { label: "Artifact storage", value: deployment.artifact_storage, tone: "" },
    {
      label: "Transactional email",
      value: mail,
      tone:
        deployment.email_sender_configured && deployment.email_credential_configured ? "" : "warn",
    },
    {
      label: "Automatic admission",
      value: `${deployment.automatic_access_used} of ${deployment.automatic_access_limit} slots used`,
      tone: "",
    },
  ];
  return (
    <Panel
      title="Deployment"
      hint="How this instance is configured. Secrets appear as presence only, never as values."
    >
      <dl className="admin-flags">
        {flags.map((flag) => (
          <div key={flag.label} className={flag.tone ? `admin-flag ${flag.tone}` : "admin-flag"}>
            <dt>{flag.label}</dt>
            <dd>{flag.value}</dd>
          </div>
        ))}
      </dl>
    </Panel>
  );
}

function PeoplePanel({ people }: { people: PlatformOverview["people"] }) {
  const status = (key: string) => people.by_status[key] ?? 0;
  return (
    <Panel
      title="People"
      hint="Every account on this platform. Company access is granted separately by membership."
    >
      <div className="admin-stats">
        <Stat label="accounts" value={people.total} />
        <Stat label="active" value={status("active")} />
        <Stat
          label="awaiting approval"
          value={people.pending_applications}
          tone={people.pending_applications > 0 ? "warn" : ""}
        />
        <Stat label="email unverified" value={status("email_unverified")} />
        <Stat label="rejected" value={status("rejected")} />
        <Stat label="oldest application" value={elapsed(people.oldest_pending_at)} />
      </div>
      <div className="admin-table">
        <table>
          <thead>
            <tr>
              <th>Account</th>
              <th>Status</th>
              <th>Companies</th>
              <th>Sessions</th>
              <th>Last login</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {people.users.map((row) => (
              <tr key={row.id}>
                <td>
                  <strong>{row.display_name || row.email}</strong>
                  <small>
                    {row.email}
                    {row.is_platform_admin && <em className="admin-badge">platform admin</em>}
                    {!row.email_verified_at && <em className="admin-badge warn">unverified</em>}
                  </small>
                </td>
                <td>
                  <em className={`status-${row.status}`}>{row.status}</em>
                </td>
                <td>
                  {row.companies.length === 0
                    ? "—"
                    : row.companies
                        .map((company) => `${company.name} (${company.role})`)
                        .join(", ")}
                </td>
                <td>{row.active_sessions}</td>
                <td>{elapsed(row.last_login_at)}</td>
                <td>{stamp(row.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function CompaniesPanel({ companies }: { companies: PlatformOverview["companies"] }) {
  return (
    <Panel
      title="Companies"
      hint="Tenant shape and liveness. Business content stays inside each company."
    >
      <div className="admin-stats">
        <Stat label="companies" value={companies.total} />
        <Stat label="archived" value={companies.archived} />
      </div>
      <div className="admin-table">
        <table>
          <thead>
            <tr>
              <th>Company</th>
              <th>Owners</th>
              <th>Members</th>
              <th>Open invitations</th>
              <th>Business events</th>
              <th>Last activity</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {companies.rows.map((row) => (
              <tr key={row.id}>
                <td>
                  <strong>{row.name}</strong>
                  <small>
                    {row.id}
                    {row.archived_at && <em className="admin-badge warn">archived</em>}
                  </small>
                </td>
                <td>{row.owners}</td>
                <td>{row.members}</td>
                <td>{row.open_invitations}</td>
                <td>{row.business_events}</td>
                <td>{elapsed(row.last_event_at)}</td>
                <td>{stamp(row.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function OperationsPanel({ operations }: { operations: PlatformOverview["operations"] }) {
  const jobs = (key: string) => operations.import_jobs[key] ?? 0;
  const delivery = (key: string) => operations.invitation_deliveries[key] ?? 0;
  const stuckDeliveries = delivery("failed") + delivery("retry");
  return (
    <Panel
      title="Operations"
      hint="The work that stops without anyone noticing: intake, projections and invitation email."
    >
      <div className="admin-stats">
        <Stat label="imports pending" value={jobs("pending")} />
        <Stat
          label="imports failed"
          value={jobs("failed")}
          tone={jobs("failed") > 0 ? "bad" : ""}
        />
        <Stat
          label="projections not ready"
          value={operations.projections_failed}
          tone={operations.projections_failed > 0 ? "bad" : ""}
        />
        <Stat
          label="invitation mail stuck"
          value={stuckDeliveries}
          tone={stuckDeliveries > 0 ? "warn" : ""}
        />
        <Stat label="delivered invitations" value={delivery("delivered")} />
        <Stat label="active agent tokens" value={operations.active_agent_tokens} />
      </div>
    </Panel>
  );
}

function SecurityPanel({ security }: { security: PlatformOverview["security"] }) {
  return (
    <Panel title="Security trail" hint="The most recent privileged events, newest first.">
      <div className="admin-trail">
        {security.length === 0 && <p>No recorded events yet.</p>}
        {security.map((event) => (
          <div key={event.id}>
            <strong>{event.event_type}</strong>
            <span>
              {event.actor ? `by ${event.actor}` : "by the system"}
              {event.subject && ` · ${event.subject}`}
              {event.outcome && ` · ${event.outcome}`}
            </span>
            <small>{stamp(event.occurred_at)}</small>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function PlatformAdmin({ user }: { user: AuthUser }) {
  const [overview, setOverview] = useState<PlatformOverview | null>(null);
  const [failure, setFailure] = useState("");
  useEffect(() => {
    api
      .platformOverview()
      .then(setOverview)
      .catch((error: Error) => setFailure(error.message));
  }, []);
  return (
    <AdminShell
      user={user}
      active="overview"
      title="Platform overview"
      lead="What this deployment knows about itself: configuration, accounts, companies and the work that can silently stop."
    >
      {failure && <p className="admin-failure">{failure}</p>}
      {!overview && !failure && <p>Loading platform state…</p>}
      {overview && (
        <div className="admin-panels">
          <DeploymentPanel deployment={overview.deployment} />
          <PeoplePanel people={overview.people} />
          <CompaniesPanel companies={overview.companies} />
          <OperationsPanel operations={overview.operations} />
          <SecurityPanel security={overview.security} />
          <p className="admin-generated">Generated {stamp(overview.generated_at)}</p>
        </div>
      )}
    </AdminShell>
  );
}

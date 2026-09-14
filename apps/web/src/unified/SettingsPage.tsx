import { RegisterHeader } from "./RegisterWorkbench";
import { AISettings } from "./AISettings";
import { CompanySettings } from "./CompanySettings";
import { MemberAccess } from "./MemberAccess";
import { useEffect, useRef, useState } from "react";
import { api, APIError, type AuthUser, type Tenant, type Bootstrap } from "../api";
import { t } from "../localization";
import { readThemePreference, storeThemePreference, type ThemePreference } from "../theme";
import { type Selection } from "./routing";

type Preferences = Pick<AuthUser, "display_name" | "language" | "locale" | "timezone">;
const preferences = (user: AuthUser): Preferences => ({
  display_name: user.display_name || "",
  language: user.language,
  locale: user.locale,
  timezone: user.timezone,
});

export function SettingsPage({
  user,
  updateUser,
  openCompany,
  companies,
  switchCompany,
  company,
  selection,
  navigate,
}: {
  openCompany: (data: Bootstrap, id: string, options?: { announce?: boolean }) => void;
  user: AuthUser;
  updateUser: (user: AuthUser) => void;
  company: Tenant;
  companies: Tenant[];
  switchCompany: (id: string) => void;
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const view = selection.settingsView;
  const [management, setManagement] = useState<{ id: string; view: ManagementView } | null>(null);
  const target =
    management ||
    (view === "access" || view === "agents" || view === "ai" ? { id: company.id, view } : null);
  const managedCompany = target ? companies.find((row) => row.id === target.id) : undefined;
  return (
    <div className="mx-auto max-w-6xl space-y-7">
      <RegisterHeader title={view === "personal" ? "Profile & preferences" : "Companies"} />
      <section
        data-settings-view={view}
        className="min-w-0 rounded-xl border border-border-default bg-surface p-5 sm:p-7"
      >
        {view === "personal" ? (
          <PersonalPreferences user={user} updateUser={updateUser} />
        ) : (
          <CompanySettings
            company={company}
            companies={companies}
            switchCompany={switchCompany}
            openCompany={openCompany}
            openSimulation={(id) =>
              navigate({ tenant: id, route: "demo-data", page: 1, q: "", proposal: "" })
            }
            manageCompany={(id, task) => setManagement({ id, view: task })}
          />
        )}
      </section>
      {view !== "personal" && target && managedCompany && (
        <CompanyManagementDialog
          key={managedCompany.id + target.view}
          company={managedCompany}
          view={target.view}
          close={() => {
            setManagement(null);
            if (view !== "company") navigate({ settingsView: "company" });
          }}
        />
      )}
    </div>
  );
}

type ManagementView = "access" | "agents" | "ai";
function CompanyManagementDialog({
  company,
  view,
  close,
}: {
  company: Tenant;
  view: ManagementView;
  close: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [blocked, setBlocked] = useState(false);
  const title =
    view === "access"
      ? "Manage users"
      : view === "agents"
        ? "Agents & API tokens"
        : "AI configuration";
  useEffect(() => {
    const trigger = document.activeElement as HTMLElement | null;
    const node = dialog.current!;
    node.showModal();
    return () => {
      node.close();
      trigger?.focus();
    };
  }, []);
  return (
    <dialog
      ref={dialog}
      aria-label={t(title)}
      onCancel={(event) => {
        event.preventDefault();
        if (!blocked) close();
      }}
      className="m-auto max-h-[90dvh] w-[min(900px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <header className="mb-6 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-xl font-semibold">{t(title)}</h2>
          <p className="mt-2 break-words font-medium" data-localization="original">
            {company.name}
          </p>
          <p
            className="mt-1 break-all font-mono text-xs text-fg-muted"
            data-localization="original"
          >
            {company.id}
          </p>
        </div>
        <button className="br-btn" disabled={blocked} onClick={close}>
          {t("Close")}
        </button>
      </header>
      {company.role !== "owner" ? (
        <p className="text-fg-muted">{t("Only company owners can view these settings.")}</p>
      ) : view === "access" ? (
        <MemberAccess tenant={company.id} companyName={company.name} onBusyChange={setBlocked} />
      ) : (
        <AISettings tenant={company.id} tokensOnly={view === "agents"} onBusyChange={setBlocked} />
      )}
    </dialog>
  );
}

function PersonalPreferences({
  user,
  updateUser,
}: {
  user: AuthUser;
  updateUser: (user: AuthUser) => void;
}) {
  const [draft, setDraft] = useState<Preferences>(() => preferences(user));
  const [theme, setTheme] = useState(readThemePreference);
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const [attempt, setAttempt] = useState<Preferences | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState(false);
  useEffect(() => {
    const changed = () => setTheme(readThemePreference());
    window.addEventListener("reality:theme-changed", changed);
    return () => window.removeEventListener("reality:theme-changed", changed);
  }, []);
  const change = (key: keyof Preferences, value: string) => {
    setDraft({ ...draft, [key]: value });
    setMessage("");
  };
  const save = async () => {
    if (lock.current || attempt) return;
    lock.current = true;
    setBusy(true);
    setMessage("");
    setError(false);
    const submitted = { ...draft };
    try {
      const saved = await api.updateProfile(submitted);
      updateUser(saved);
      setDraft(preferences(saved));
      setMessage("Preferences saved.");
    } catch (reason) {
      setError(true);
      if (reason instanceof APIError && reason.status >= 400 && reason.status < 500) {
        setMessage("Preferences were not saved. Check your entries and try again.");
      } else {
        setAttempt(submitted);
        setMessage("The save result is unknown. Check saved preferences before trying again.");
      }
    } finally {
      lock.current = false;
      setBusy(false);
    }
  };
  const recover = async () => {
    if (lock.current || !attempt) return;
    lock.current = true;
    setBusy(true);
    try {
      const current = await api.me();
      const expected = { ...attempt, display_name: attempt.display_name.trim() };
      const matches = (Object.keys(expected) as (keyof Preferences)[]).every(
        (key) => expected[key] === current[key],
      );
      updateUser(current);
      setAttempt(null);
      setError(!matches);
      if (matches) setDraft(preferences(current));
      setMessage(
        matches
          ? "Preferences saved."
          : "Saved preferences differ from your draft. Review it before saving again.",
      );
    } catch {
      setError(true);
      setMessage("Could not check saved preferences. Try checking again.");
    } finally {
      lock.current = false;
      setBusy(false);
    }
  };
  return (
    <div className="space-y-7">
      <div>
        <p className="mt-2 text-sm text-fg-muted">
          {t("These preferences apply to your account across all companies.")}
        </p>
        <p className="mt-2 break-all text-sm text-fg-muted">{user.email}</p>
      </div>
      <form
        id="personal-preferences-form"
        onSubmit={(e) => {
          e.preventDefault();
          void save();
        }}
        className="space-y-5"
      >
        <fieldset
          disabled={busy || !!attempt}
          className="grid min-w-0 gap-5 sm:grid-cols-2 disabled:opacity-60"
        >
          <label className="block text-sm sm:col-span-2">
            {t("Display name")}
            <input
              className="br-control mt-2 w-full"
              name="display_name"
              maxLength={150}
              autoComplete="name"
              value={draft.display_name}
              onChange={(e) => change("display_name", e.target.value)}
            />
          </label>
          <label className="block min-w-0 text-sm">
            {t("Language")}
            <select
              name="language"
              aria-label={t("Language")}
              className="br-control mt-2 w-full"
              value={draft.language}
              onChange={(e) => change("language", e.target.value)}
            >
              <option value="en">English</option>
              <option value="de">Deutsch</option>
              <option value="nl">Nederlands</option>
              <option value="es">Español</option>
            </select>
          </label>
          <label className="block min-w-0 text-sm">
            {t("Number and date format")}
            <select
              name="locale"
              aria-label={t("Number and date format")}
              className="br-control mt-2 w-full"
              value={draft.locale}
              onChange={(e) => change("locale", e.target.value)}
            >
              <option value="en-GB">1,234.56 · 07/09/2026</option>
              <option value="de-DE">1.234,56 · 07.09.2026</option>
              <option value="nl-NL">1.234,56 · 07-09-2026</option>
              <option value="es-ES">1234,56 · 7/9/2026</option>
            </select>
          </label>
          <label className="block text-sm sm:col-span-2">
            {t("Time zone")}
            <select
              className="br-control mt-2 w-full"
              name="timezone"
              aria-label={t("Time zone")}
              required
              value={draft.timezone}
              onChange={(e) => change("timezone", e.target.value)}
            >
              {Array.from(
                new Set([
                  "UTC",
                  "Europe/Berlin",
                  "Europe/Rome",
                  "Europe/Amsterdam",
                  "Europe/Madrid",
                  "Europe/London",
                  "America/New_York",
                  draft.timezone,
                  ...((
                    Intl as typeof Intl & { supportedValuesOf?: (key: string) => string[] }
                  ).supportedValuesOf?.("timeZone") || []),
                ]),
              )
                .sort((a, b) => {
                  if (a === "UTC") return -1;
                  if (b === "UTC") return 1;
                  return a.split("/").at(-1)!.localeCompare(b.split("/").at(-1)!);
                })
                .map((zone) => (
                  <option key={zone} value={zone} data-localization="original">
                    {zone === "UTC"
                      ? "UTC"
                      : `${zone.split("/").at(-1)!.replaceAll("_", " ")} — ${zone.split("/").slice(0, -1).join(" / ").replaceAll("_", " ")}`}
                  </option>
                ))}
            </select>
          </label>
        </fieldset>
        {message && (
          <p role={error ? "alert" : "status"} className="rounded-lg bg-surface-muted p-4 text-sm">
            {t(message)}
          </p>
        )}
        <div className="flex flex-wrap gap-3">
          <button
            form="personal-preferences-form"
            type="submit"
            className="br-btn br-btn-primary"
            disabled={busy || !!attempt}
          >
            {t(busy && !attempt ? "Saving…" : "Save preferences")}
          </button>
          {attempt && (
            <button type="button" className="br-btn" disabled={busy} onClick={() => void recover()}>
              {t("Check saved preferences")}
            </button>
          )}
        </div>
      </form>
      <div className="border-t border-border-default pt-6">
        <label className="block text-sm">
          {t("Appearance")}
          <select
            className="br-control mt-2 w-full sm:w-64"
            aria-label={t("Appearance")}
            value={theme}
            onChange={(e) => storeThemePreference(e.target.value as ThemePreference)}
          >
            <option value="light">{t("Light")}</option>
            <option value="dark">{t("Dark")}</option>
            <option value="system">{t("System")}</option>
          </select>
        </label>
        <p className="mt-3 text-sm text-fg-muted">
          {t("Appearance is saved in this browser. System follows your device.")}
        </p>
      </div>
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import { Check, LoaderCircle, ShieldCheck } from "lucide-react";

import { api, type OAuthAuthorizationInteraction } from "./api";
import { CompanySetup } from "./components/CompanySetup";
import { t } from "./localization";

type State =
  | { kind: "loading" }
  | { kind: "ready"; interaction: OAuthAuthorizationInteraction }
  | { kind: "error"; message: string };

export function OAuthAuthorization({ interaction }: { interaction: string }) {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [company, setCompany] = useState("");
  const [tools, setTools] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [showCompanySetup, setShowCompanySetup] = useState(false);

  const loadInteraction = async (preferredCompany = "") => {
    const value = await api.oauthInteraction(interaction);
    if (value.status !== "pending")
      throw new Error(t("This authorization is no longer available."));
    setState({ kind: "ready", interaction: value });
    setCompany(
      value.companies.some((item) => item.id === preferredCompany)
        ? preferredCompany
        : value.companies[0]?.id || "",
    );
    setTools(new Set(value.selected_tools));
  };

  useEffect(() => {
    void loadInteraction().catch((reason) =>
      setState({
        kind: "error",
        message: reason instanceof Error ? reason.message : t("Authorization could not be loaded."),
      }),
    );
  }, [interaction]);

  const selected = useMemo(() => [...tools], [tools]);
  const finish = (path: string) => location.assign(path);
  const approve = async () => {
    if (!company || !selected.length || state.kind !== "ready") return;
    setBusy(true);
    try {
      finish((await api.approveOAuthInteraction(interaction, company, selected)).completion_path);
    } catch (reason) {
      setState({
        kind: "error",
        message:
          reason instanceof Error ? reason.message : t("Authorization could not be completed."),
      });
      setBusy(false);
    }
  };
  const deny = async () => {
    setBusy(true);
    try {
      finish((await api.denyOAuthInteraction(interaction)).completion_path);
    } catch (reason) {
      setState({
        kind: "error",
        message:
          reason instanceof Error ? reason.message : t("Authorization could not be cancelled."),
      });
      setBusy(false);
    }
  };

  if (state.kind === "loading")
    return (
      <main className="mx-auto flex min-h-screen max-w-xl items-center justify-center p-6">
        <p role="status" className="flex items-center gap-3 text-sm text-[var(--text-muted)]">
          <LoaderCircle className="animate-spin motion-reduce:animate-none" aria-hidden="true" />
          {t("Loading authorization…")}
        </p>
      </main>
    );
  if (state.kind === "error")
    return (
      <main className="mx-auto min-h-screen max-w-xl p-8 pt-24">
        <h1 className="text-2xl font-semibold">{t("Authorization unavailable")}</h1>
        <p className="mt-4 text-[var(--text-muted)]" role="alert">
          {state.message}
        </p>
      </main>
    );

  const value = state.interaction;
  return (
    <main className="mx-auto min-h-screen max-w-2xl p-6 py-16">
      <section className="rounded-2xl border border-[var(--border-default)] bg-[var(--surface)] p-7 shadow-lg">
        <ShieldCheck className="text-[#635bff]" aria-hidden="true" />
        <p className="mt-4 text-xs font-bold uppercase tracking-widest text-[#635bff]">
          {t("Connected client")}
        </p>
        <h1 className="mt-2 text-3xl font-semibold">
          {t("Authorize {client}").replace("{client}", value.client.name)}
        </h1>
        <p className="mt-3 text-[var(--text-muted)]">
          {t(
            "Choose one company and the exact tools this client may use. This does not approve any business change.",
          )}
        </p>

        <label className="mt-7 grid gap-2 text-sm font-semibold">
          {t("Company")}
          <select
            className="h-12 rounded-lg border border-[var(--border-strong)] bg-[var(--surface)] px-3"
            value={company}
            onChange={(event) => setCompany(event.target.value)}
          >
            <option value="">{t("Choose a company")}</option>
            {value.companies.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>

        <fieldset className="mt-7 grid gap-3">
          <legend className="mb-2 font-semibold">{t("Allowed tools")}</legend>
          {value.eligible_tools.map((tool) => (
            <label
              key={tool.name}
              className="flex gap-3 rounded-lg border border-[var(--border-default)] p-3"
            >
              <input
                type="checkbox"
                checked={tools.has(tool.name)}
                onChange={(event) => {
                  const next = new Set(tools);
                  event.target.checked ? next.add(tool.name) : next.delete(tool.name);
                  setTools(next);
                }}
              />
              <span>
                <strong>{tool.label}</strong>
                <small className="ml-2 text-[var(--text-muted)]">{t(tool.access)}</small>
              </span>
            </label>
          ))}
        </fieldset>

        {!value.companies.length && (
          <div className="mt-6 rounded-lg bg-[var(--surface-sunken)] p-4">
            <p role="status">
              {t("No ready company is available. Create or finish setting up a company first.")}
            </p>
            {value.company_setup.eligible && (
              <button
                className="auth-secondary mt-4"
                disabled={busy}
                onClick={() => setShowCompanySetup(true)}
              >
                {t("Create company")}
              </button>
            )}
          </div>
        )}
        <div className="mt-8 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            className="auth-secondary sm:w-auto sm:px-6"
            disabled={busy}
            onClick={() => void deny()}
          >
            {t("Cancel authorization")}
          </button>
          <button
            className="auth-submit m-0 sm:w-auto sm:px-6"
            disabled={busy || !company || !selected.length}
            onClick={() => void approve()}
          >
            {busy ? (
              <LoaderCircle
                className="animate-spin motion-reduce:animate-none"
                aria-hidden="true"
              />
            ) : (
              <Check aria-hidden="true" />
            )}
            {t("Allow selected access")}
          </button>
        </div>
      </section>
      {showCompanySetup && (
        <CompanySetup
          close={() => setShowCompanySetup(false)}
          created={async (result) => {
            await loadInteraction(result.tenant_id);
            setShowCompanySetup(false);
          }}
        />
      )}
    </main>
  );
}

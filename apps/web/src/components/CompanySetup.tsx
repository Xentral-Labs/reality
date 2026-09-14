import { useEffect, useRef, useState } from "react";
import {
  api,
  type CompanySetupChoices,
  type CompanySetupOptions,
  type CompanySetupRequest,
  type CompanySetupResult,
} from "../api";
import { t } from "../localization";
import { CompanySetupForm } from "./CompanySetupForm";

export function CompanySetup({
  first = false,
  close,
  created,
}: {
  first?: boolean;
  close?: () => void;
  created?: (result: CompanySetupResult) => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (!first) dialog.current?.showModal();
    return () => dialog.current?.close();
  }, [first]);
  const [options, setOptions] = useState<CompanySetupOptions>();
  const [pending, setPending] = useState<CompanySetupRequest>();
  const [result, setResult] = useState<CompanySetupResult>();
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const attemptedOpen = useRef<string | undefined>(undefined);
  const storageKey = (actor: string) => `reality.company-setup.${actor}`;
  useEffect(() => {
    let active = true;
    void api
      .companySetupOptions()
      .then(async (value) => {
        if (!active) return;
        setOptions(value);
        const saved = sessionStorage.getItem(storageKey(value.actor_id));
        if (saved) {
          const request = JSON.parse(saved) as CompanySetupRequest;
          setPending(request);
          try {
            const recovered = await api.companySetupRequest(request.request_key);
            if (active) setResult(recovered);
          } catch {
            /* Retain the exact request for an explicit retry after a lost response. */
          }
        }
      })
      .catch(() => {
        if (active) setError(t("Company setup could not be loaded. Reload to retry."));
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, []);
  async function submit(choices: CompanySetupChoices | CompanySetupRequest) {
    if (!options || busy) return;
    const request: CompanySetupRequest =
      "request_key" in choices
        ? choices
        : { ...choices, request_key: crypto.randomUUID(), confirmed: true };
    sessionStorage.setItem(storageKey(options.actor_id), JSON.stringify(request));
    setPending(request);
    setBusy(true);
    setError("");
    try {
      setResult(await api.companySetup(request));
    } catch {
      setError(t("Creation could not be confirmed. Retry the same request to recover safely."));
    } finally {
      setBusy(false);
    }
  }
  async function open() {
    if (!result?.destination || !options) return;
    setBusy(true);
    setError("");
    try {
      if (created) await created(result);
      else window.location.assign(result.destination);
      sessionStorage.removeItem(storageKey(options.actor_id));
    } catch {
      setError(t("Company setup could not be loaded. Reload to retry."));
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    if (
      result?.status !== "ready" ||
      !options ||
      busy ||
      attemptedOpen.current === result.tenant_id
    )
      return;
    attemptedOpen.current = result.tenant_id;
    void open();
  }, [result, options, busy]);
  const body = (
    <section className="onboarding-card" aria-labelledby="company-setup-title" aria-busy={busy}>
      <h1 id="company-setup-title">
        {t(
          result?.status === "ready"
            ? "Company created"
            : first
              ? "Create your first company"
              : "Create company",
        )}
      </h1>
      {result?.status !== "ready" && (
        <p>
          {t(
            first
              ? "Your access request has not created a company. Choose how this company should start."
              : "Choose how this company should start.",
          )}
        </p>
      )}
      {error && <p role="alert">{error}</p>}
      {result?.status === "ready" ? (
        <div role="status">
          <p>
            <span data-localization="original">{result.name}</span> — {t("Ready")}
          </p>
          <p>{t("Company created. Opening your company…")}</p>
          {error && (
            <button className="primary-button" disabled={busy} onClick={() => void open()}>
              {t("Retry opening")}
            </button>
          )}
        </div>
      ) : pending ? (
        <div aria-live="polite">
          <p data-localization="original">{pending.name}</p>
          <p>
            {t(
              "Keep this request while setup is pending. Retrying will not create another company.",
            )}
          </p>
          <button className="primary-button" disabled={busy} onClick={() => void submit(pending)}>
            {t("Retry company setup")}
          </button>
        </div>
      ) : (
        options && (
          <CompanySetupForm
            options={options}
            initialName={first ? options.suggested_name : ""}
            busy={busy}
            submit={submit}
            cancel={close}
          />
        )
      )}
      {busy && <p role="status">{t("Loading…")}</p>}
    </section>
  );
  return first ? (
    <main className="state-screen onboarding-screen">{body}</main>
  ) : (
    <dialog
      ref={dialog}
      className="company-setup-dialog"
      aria-labelledby="company-setup-title"
      onCancel={(event) => {
        if (busy || pending) event.preventDefault();
        else close?.();
      }}
    >
      {body}
    </dialog>
  );
}

import { Building2 } from "lucide-react";
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
import { SetupSteps } from "./EntryProgress";
import {
  followSetup,
  presentReadySetup,
  setupProgress,
  setupSteps,
  type SetupStep,
} from "../unified/setupProgress";

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
  const [apiKey, setApiKey] = useState("");
  const [steps, setSteps] = useState<SetupStep[] | null>(null);
  const attemptedOpen = useRef<string | undefined>(undefined);
  const mounted = useRef(true);
  useEffect(() => {
    // Set on mount as well: a remount must not leave the screen marked as gone.
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const storageKey = (actor: string) => `reality.company-setup.${actor}`;
  async function settle(receipt: CompanySetupResult | null) {
    if (!receipt || !mounted.current) return;
    if (receipt.status === "ready") {
      await presentReadySetup(setSteps, () => mounted.current);
    }
    if (mounted.current) setResult(receipt);
  }
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
            if (active && setupProgress(recovered) === "waiting") {
              setResult(recovered);
              setSteps(setupSteps(recovered));
            }
            if (active && setupProgress(recovered) === "waiting") {
              const settled = await followSetup(
                () => api.companySetupRequest(request.request_key),
                () => active && mounted.current,
                {
                  observe: (receipt) => {
                    if (active && mounted.current) setSteps(setupSteps(receipt));
                  },
                },
              );
              if (active && settled) await settle(settled);
            } else if (active) {
              await settle(recovered);
            }
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
      // Feature 199: creation answers once the company exists; its profile is seeded
      // by the worker, so the receipt is followed until it is ready or fails.
      const created = await api.companySetup(request);
      if (setupProgress(created) === "waiting") {
        setResult(created);
        setSteps(setupSteps(created));
        const settled = await followSetup(
          () => api.companySetupRequest(request.request_key),
          () => mounted.current,
          {
            observe: (receipt) =>
              mounted.current && receipt?.status !== "ready" && setSteps(setupSteps(receipt)),
          },
        );
        if (settled) await settle(settled);
      } else {
        await settle(created);
      }
    } catch {
      setError(t("Creation could not be confirmed. Retry the same request to recover safely."));
    } finally {
      if (mounted.current) setBusy(false);
    }
  }
  async function retry() {
    if (!pending || busy) return;
    setBusy(true);
    setError("");
    try {
      const recovered = await api.companySetupRetry(pending.request_key);
      if (setupProgress(recovered) === "waiting") {
        setResult(recovered);
        setSteps(setupSteps(recovered));
        const settled = await followSetup(
          () => api.companySetupRequest(pending.request_key),
          () => mounted.current,
          {
            observe: (receipt) =>
              mounted.current && receipt?.status !== "ready" && setSteps(setupSteps(receipt)),
          },
        );
        if (settled) await settle(settled);
      } else {
        await settle(recovered);
      }
    } catch {
      setError(t("Company setup could not be completed. Retry when you are ready."));
    } finally {
      if (mounted.current) setBusy(false);
    }
  }
  async function open() {
    if (!result?.destination || !options) return;
    setBusy(true);
    setError("");
    try {
      if (apiKey.trim()) {
        await api.saveAISettings(result.tenant_id, {
          provider_preset: "anthropic",
          api_key: apiKey.trim(),
        });
        setApiKey("");
      }
      // Readiness is authoritative at this point. Clear the recovery marker before
      // yielding to a caller that may navigate immediately (for example OAuth consent).
      sessionStorage.removeItem(storageKey(options.actor_id));
      if (created) await created(result);
      else window.location.assign(result.destination);
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
    <section
      className="onboarding-card company-setup-card"
      aria-labelledby="company-setup-title"
      aria-busy={busy}
    >
      <div className="company-setup-symbol" aria-hidden="true">
        <Building2 />
      </div>
      <p className="company-setup-brand">Reality</p>
      <h1 id="company-setup-title">
        {t(
          result?.status === "ready"
            ? "Company created"
            : busy
              ? pending
                ? "Preparing your company"
                : "Loading your workspace"
              : pending
                ? "Continue company setup"
                : first
                  ? "Create your first company"
                  : "Create company",
        )}
      </h1>
      {!busy && !pending && result?.status !== "ready" && (
        <p className="company-setup-description">{t("Choose how this company should start.")}</p>
      )}
      {busy && (
        <div role="status" aria-live="polite" className="company-setup-progress">
          {(pending?.name || result?.name) && (
            <p className="company-setup-name" data-localization="original">
              {pending?.name || result?.name}
            </p>
          )}
          <p>{t("You can watch each step. Your company opens automatically when it is ready.")}</p>
          {steps && <SetupSteps steps={steps} />}
          {result?.preparation === "retrying" && (
            <p className="company-setup-retry-status">
              <span>{t("Automatic retry")}</span>
              {result.preparation_attempt && result.preparation_max_attempts && (
                <span>
                  {t("Attempt")} {result.preparation_attempt} / {result.preparation_max_attempts}
                </span>
              )}
              {result.preparation_next_attempt_at && (
                <span>
                  {t("Next attempt:")}{" "}
                  {new Date(result.preparation_next_attempt_at).toLocaleTimeString()}
                </span>
              )}
            </p>
          )}
        </div>
      )}
      {error && <p role="alert">{error}</p>}
      {busy ? null : result?.status === "ready" ? (
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
        <div aria-live="polite" className="company-setup-recovery">
          <p className="company-setup-name" data-localization="original">
            {pending.name}
          </p>
          <p>{t("Your setup is saved. Continue with the same company.")}</p>
          <button className="primary-button" disabled={busy} onClick={() => void retry()}>
            {t("Retry company setup")}
          </button>
        </div>
      ) : (
        options && (
          <CompanySetupForm
            options={options}
            initialName={first ? options.suggested_name : ""}
            busy={busy}
            apiKey={apiKey}
            setApiKey={setApiKey}
            submit={submit}
            cancel={close}
          />
        )
      )}
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

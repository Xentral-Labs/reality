import { useRef, useState } from "react";
import type { CompanySetupChoices, CompanySetupOptions } from "../api";
import { t } from "../localization";

export function CompanySetupForm({
  options,
  initialName,
  busy,
  submit,
  cancel,
}: {
  options: CompanySetupOptions;
  initialName: string;
  busy: boolean;
  submit: (choices: CompanySetupChoices) => Promise<void>;
  cancel?: () => void;
}) {
  const [name, setName] = useState(initialName);
  const nameInput = useRef<HTMLInputElement>(null);
  const [nameError, setNameError] = useState(false);
  const [choice, setChoice] = useState<"business" | "sandbox" | "demo">(
    options.environments.includes("business") ? "business" : "sandbox",
  );
  const [liveSimulation, setLiveSimulation] = useState(false);
  const choices = [
    {
      value: "business" as const,
      label: t("Start your own company"),
      description: t("Start empty and add your own data or integrations."),
      allowed: options.environments.includes("business"),
    },
    {
      value: "sandbox" as const,
      label: t("Create an empty Sandbox"),
      description: t("Experiment without preset data in a clearly labelled test environment."),
      allowed: options.environments.includes("sandbox"),
    },
    {
      value: "demo" as const,
      label: t("Try demo data"),
      description: t(
        "Explore international products, warehouses, customers and twelve weeks of order history in a Sandbox.",
      ),
      allowed: options.practice_enabled && options.environments.includes("sandbox"),
    },
  ].filter((item) => item.allowed);
  return (
    <form
      className="onboarding-form"
      aria-busy={busy}
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        if (busy || !options.environments.length) return;
        if (!name.trim()) {
          setNameError(true);
          nameInput.current?.focus();
          nameInput.current?.scrollIntoView({ block: "center" });
          return;
        }
        void submit({
          name: name.trim(),
          environment: choice === "business" ? "business" : "sandbox",
          content: choice === "demo" ? "international_demo" : "empty",
          live_simulation: choice === "demo" && liveSimulation,
        });
      }}
    >
      <label htmlFor="setup-company-name">{t("Company name (required)")}</label>
      <input
        id="setup-company-name"
        ref={nameInput}
        aria-invalid={nameError}
        aria-describedby={[
          "setup-company-name-help",
          ...(nameError ? ["setup-company-name-error"] : []),
        ].join(" ")}
        value={name}
        onChange={(event) => {
          setName(event.target.value);
          if (event.target.value.trim()) setNameError(false);
        }}
        required
        maxLength={120}
        autoFocus
        disabled={busy}
      />
      <p id="setup-company-name-help" className="text-sm text-fg-muted">
        {t("Choose a name for this company or Sandbox so you can find it later.")}
      </p>
      {nameError && (
        <p
          id="setup-company-name-error"
          role="alert"
          className="text-sm font-medium text-red-600 dark:text-red-400"
        >
          {t("Enter a company name to continue.")}
        </p>
      )}
      <fieldset disabled={busy}>
        <legend>{t("How would you like to start?")}</legend>
        {choices.map((item) => (
          <div key={item.value}>
            <label>
              <input
                type="radio"
                name="company-start"
                value={item.value}
                checked={choice === item.value}
                onChange={() => {
                  setChoice(item.value);
                  setLiveSimulation(false);
                }}
                aria-describedby={`setup-${item.value}-description`}
              />
              {item.label}
            </label>
            <p id={`setup-${item.value}-description`}>{item.description}</p>
          </div>
        ))}
        {choice === "demo" && (
          <>
            <label>
              <input
                type="checkbox"
                checked={liveSimulation}
                onChange={(event) => setLiveSimulation(event.target.checked)}
                aria-describedby="setup-live-description"
              />
              {t("Enable live simulation")}
            </label>
            <p id="setup-live-description">
              {t(
                "Receive 60 new demo orders per hour. The demo integration is set up automatically. You can pause it anytime.",
              )}
            </p>
          </>
        )}
      </fieldset>
      <div className="onboarding-actions">
        {cancel && (
          <button type="button" className="secondary-button" disabled={busy} onClick={cancel}>
            {t("Cancel")}
          </button>
        )}
        <button className="primary-button" disabled={busy || !options.environments.length}>
          {busy ? t("Creating…") : t("Create company")}
        </button>
      </div>
    </form>
  );
}

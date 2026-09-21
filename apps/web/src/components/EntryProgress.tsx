import { Check, LoaderCircle } from "lucide-react";
import { t } from "../localization";
import type { SetupStep } from "../unified/setupProgress";

/** Feature 201: the steps a company setup is actually at, shared by both screens. */
export function SetupSteps({ steps }: { steps: SetupStep[] }) {
  return (
    <ol className="setup-steps" data-setup-steps>
      {steps.map((step) => (
        <li
          key={step.key}
          className="setup-step"
          data-setup-step={step.key}
          data-state={step.state}
          aria-current={step.state === "current" ? "step" : undefined}
        >
          <span
            className="setup-step-marker"
            aria-hidden="true"
          >
            {step.state === "done" ? (
              <Check className="h-4 w-4 text-accent" />
            ) : step.state === "current" ? (
              <LoaderCircle className="h-4 w-4 animate-spin motion-reduce:animate-none text-accent" />
            ) : null}
          </span>
          <span>{t(step.label)}</span>
        </li>
      ))}
    </ol>
  );
}

/** Immediate feedback while no workspace is available yet. */
export function EntryProgress({
  title = "Loading your access",
  detail = "Please wait. You will continue automatically.",
  steps = null,
}: {
  title?: string;
  detail?: string;
  /** Feature 201: real steps when the receipt reports them, a spinner otherwise. */
  steps?: SetupStep[] | null;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-surface p-8">
      <section
        className="w-full max-w-md space-y-5 text-center"
        role="status"
        aria-live="polite"
        aria-busy="true"
      >
        <p className="text-sm font-semibold text-fg-muted">Reality</p>
        {!steps && (
          <LoaderCircle
            className="mx-auto h-8 w-8 animate-spin motion-reduce:animate-none text-accent"
            aria-hidden="true"
          />
        )}
        <h1 className="text-2xl font-semibold">{t(title)}</h1>
        <p className="text-fg-muted">{t(detail)}</p>
        {steps && <SetupSteps steps={steps} />}
      </section>
    </main>
  );
}

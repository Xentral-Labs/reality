import { useEffect, useRef } from "react";
import { Check } from "lucide-react";
import { recordsChanged, type ResolutionGuidance as Guidance } from "../api";
import { t } from "../localization";
import { useActionDiscovery } from "./ActionLauncher";
import { isActionForm } from "./actionDiscovery";
import { prepareChat, reasonText, stepBarrier } from "./guidanceActions";
import type { Destination } from "./routing";
import { paletteActionPrefill, type PaletteActionTarget } from "./commandPaletteTargets";

/**
 * Spec 279: why a value is missing and the ordered steps that would make it available.
 * The shared services decide the steps and their order; this only renders them and
 * routes each open step to a path that already exists.
 */
export function ResolutionGuidance({
  guidance,
  scopeLabel,
  refresh,
}: {
  guidance: Guidance;
  /** Names the scope in a prepared chat request, e.g. "Bike Light (BIKE-LIGHT)". */
  scopeLabel: string;
  /** Re-read the service after any write, so a step is never marked done locally. */
  refresh?: () => void;
}) {
  const context = useActionDiscovery();
  const catalog = context?.data?.resolution_guidance;
  const reread = useRef(refresh);
  reread.current = refresh;
  useEffect(() => {
    const changed = () => reread.current?.();
    window.addEventListener(recordsChanged, changed);
    return () => window.removeEventListener(recordsChanged, changed);
  }, []);
  const reason = reasonText(catalog, guidance.reason_code);
  const firstOpen = guidance.steps.findIndex((step) => step.state === "open");
  return (
    <div data-resolution-guidance={guidance.reason_code} className="space-y-2 text-sm">
      <div>
        <div className="font-semibold text-fg-strong">{reason.label}</div>
        <div className="mt-1 text-fg-muted">{reason.explanation}</div>
      </div>
      {guidance.steps.length > 0 && (
        <ol className="mt-4" aria-label={t("Steps to a proven value")}>
          {guidance.steps.map((step, index) => {
            const entry = catalog?.steps[step.code];
            const barrier = stepBarrier(step, guidance, { owner: !!context?.owner });
            const emphasized = index === firstOpen;
            return (
              <li
                key={`${step.code}:${index}`}
                data-guidance-step={step.code}
                data-guidance-state={step.state}
                data-guidance-first={emphasized}
                className="group grid grid-cols-[2rem_minmax(0,1fr)] gap-x-3 pb-5 last:pb-0 data-[guidance-state=blocked]:text-fg-muted"
              >
                <div className="relative flex min-h-full justify-center" aria-hidden="true">
                  {index < guidance.steps.length - 1 && (
                    <span
                      data-guidance-connector
                      className="absolute top-8 -bottom-5 w-0.5 bg-border-default"
                    />
                  )}
                  <span
                    data-guidance-marker
                    data-marker-state={step.state === "done" || emphasized ? "active" : "inactive"}
                    className="relative z-10 grid size-8 shrink-0 place-items-center rounded-full border-2 text-sm font-semibold data-[marker-state=active]:border-accent data-[marker-state=active]:bg-accent data-[marker-state=active]:text-fg-inverse data-[marker-state=inactive]:border-border-strong data-[marker-state=inactive]:bg-surface data-[marker-state=inactive]:text-fg-muted"
                  >
                    {step.state === "done" ? <Check size={16} strokeWidth={2.5} /> : index + 1}
                  </span>
                </div>
                <div className="min-w-0 pt-1">
                  <div className="text-base group-data-[guidance-first=true]:font-semibold group-data-[guidance-first=true]:text-fg-strong">
                    {entry ? t(entry.label) : t("Further step")}
                    {step.target_count > 1 && (
                      <span className="text-fg-muted"> ({step.target_count})</span>
                    )}
                  </div>
                  <span className="sr-only">
                    {t(
                      step.state === "done"
                        ? "Step done"
                        : step.state === "open"
                          ? "Step open"
                          : "Step waits for the one before",
                    )}
                  </span>
                  {barrier && <div className="mt-1 text-fg-muted">{barrier}</div>}
                  {step.state === "open" && !barrier && entry && context && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      <StepControl
                        action={entry}
                        proposal={step.proposal_id}
                        scopeLabel={scopeLabel}
                        primary={emphasized}
                      />
                      {entry.alternative && (
                        <StepControl
                          action={entry.alternative}
                          scopeLabel={scopeLabel}
                          label={t(entry.alternative.label)}
                        />
                      )}
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}

function StepControl({
  action,
  proposal,
  scopeLabel,
  primary = false,
  label,
  prefill,
}: {
  action: { path: string; form?: string; page?: string; chat_prompt?: string };
  proposal?: string;
  scopeLabel: string;
  primary?: boolean;
  label?: string;
  /** Record the form may preselect; only fields the form accepts pass through. */
  prefill?: PaletteActionTarget;
}) {
  const context = useActionDiscovery();
  if (!context) return null;
  const className = `br-btn${primary ? " br-btn-primary" : ""}`;
  const button = (text: string, run: () => void, marker: string) => (
    <button type="button" className={className} data-guidance-action={marker} onClick={run}>
      {label || text}
    </button>
  );
  const form = action.form || "";
  if (action.path === "web_form" && isActionForm(form))
    return button(
      t("Open form"),
      () => context.open(form, prefill ? paletteActionPrefill(form, prefill) : undefined),
      action.path,
    );
  if (action.path === "chat" && action.chat_prompt)
    return button(
      t("Prepare with Reality"),
      () => prepareChat(action.chat_prompt!, scopeLabel),
      action.path,
    );
  if (action.path === "decision_review")
    return button(
      t("Review in Decisions"),
      () => context.navigate({ route: "decisions", proposal: proposal || "" }),
      action.path,
    );
  if (action.path === "system_status")
    return button(t("Open system status"), () => context.navigate({ route: "home" }), action.path);
  if (action.path === "page" && action.page)
    return button(
      t("Open page"),
      () => context.navigate({ route: action.page as Destination }),
      action.path,
    );
  return null;
}

/**
 * Spec 279 FR-014: what resolves each delivery blocker, with the existing form that
 * addresses it. Blockers are static codes, so their wording and step come from the
 * catalog; whether the order is blocked is decided by the readiness service.
 */
export function BlockerGuidance({ codes, commitment }: { codes: string[]; commitment?: string }) {
  const catalog = useActionDiscovery()?.data?.resolution_guidance;
  if (!catalog || !codes.length) return null;
  return (
    <div data-blocker-guidance className="mb-4 space-y-2 text-sm">
      <div className="font-semibold text-fg-strong">{t("What resolves it")}</div>
      <ul className="space-y-2">
        {codes.map((code) => {
          const reason = reasonText(catalog, code);
          const entry = catalog.steps[catalog.blockers[code] || ""];
          return (
            <li key={code} data-blocker={code} className="rounded-lg bg-surface p-2">
              <div className="font-medium">{reason.label}</div>
              <div className="text-fg-muted">{reason.explanation}</div>
              {entry && (
                <div className="mt-2">
                  <StepControl
                    action={entry}
                    scopeLabel=""
                    label={t(entry.label)}
                    prefill={
                      // Only forms that act on this customer delivery take it; a receipt
                      // form's commitment is a supplier delivery, never this one.
                      commitment &&
                      ["reserve", "commitment_hold_release"].includes(entry.form || "")
                        ? { commitment }
                        : undefined
                    }
                  />
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

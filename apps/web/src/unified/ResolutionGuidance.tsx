import { useEffect, useRef } from "react";
import { CheckCircle2, Circle, CircleDot } from "lucide-react";
import { recordsChanged, type ResolutionGuidance as Guidance } from "../api";
import { t } from "../localization";
import { useActionDiscovery } from "./ActionLauncher";
import { isActionForm } from "./actionDiscovery";
import { prepareChat, reasonText, stepBarrier } from "./guidanceActions";
import type { Destination } from "./routing";

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
        <ol className="space-y-2" aria-label={t("Steps to a proven value")}>
          {guidance.steps.map((step, index) => {
            const entry = catalog?.steps[step.code];
            const barrier = stepBarrier(step, guidance, { owner: !!context?.owner });
            const emphasized = index === firstOpen;
            const Icon =
              step.state === "done" ? CheckCircle2 : step.state === "open" ? CircleDot : Circle;
            return (
              <li
                key={`${step.code}:${index}`}
                data-guidance-step={step.code}
                data-guidance-state={step.state}
                data-guidance-first={emphasized}
                className="group flex flex-wrap items-start gap-2 rounded-lg p-2 data-[guidance-first=true]:bg-surface data-[guidance-first=true]:ring-1 data-[guidance-first=true]:ring-border-default data-[guidance-state=blocked]:text-fg-muted"
              >
                <Icon size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
                <div className="min-w-0 flex-1">
                  <div className="group-data-[guidance-first=true]:font-medium group-data-[guidance-first=true]:text-fg-strong">
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
}: {
  action: { path: string; form?: string; page?: string; chat_prompt?: string };
  proposal?: string;
  scopeLabel: string;
  primary?: boolean;
  label?: string;
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
    return button(t("Open form"), () => context.open(form), action.path);
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

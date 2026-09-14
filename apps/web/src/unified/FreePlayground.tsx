import { EntryProgress } from "../components/EntryProgress";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, type Bootstrap } from "../api";
import { t } from "../localization";
import type { Selection } from "./routing";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import {
  promptKey,
  resultCompletesTask,
  starterSelection,
  type ActiveTask,
  type StarterTask,
} from "./trialJourney";

export function TrialEntry(props: {
  autoEnter: boolean;
  open: (data: Bootstrap, id: string) => void;
  children: ReactNode;
}) {
  return props.autoEnter ? <TrialEntryRequest {...props} /> : props.children;
}

function TrialEntryRequest({
  open,
  children,
  autoEnter,
}: {
  autoEnter: boolean;
  open: (data: Bootstrap, id: string) => void;
  children: ReactNode;
}) {
  const state = useRead(api.playgroundEntry, []);
  const [failure, setFailure] = useState("");
  const [finished, setFinished] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const requested =
    autoEnter &&
    !finished &&
    state.data?.requested &&
    !state.data.archived &&
    state.data.receipt?.status !== "ready" &&
    state.data.enabled &&
    state.data.eligible;
  useEffect(() => {
    if (!requested) return;
    let current = true;
    setFailure("");
    api
      .enterPlayground()
      .then(async (result) => {
        if (result.status !== "ready")
          throw new Error(
            t("Your demo is not ready yet. Retry to continue with the same company."),
          );
        const data = await api.bootstrap();
        if (current) {
          setFinished(true);
          open(data, result.tenant_id);
        }
      })
      .catch((error) => {
        if (current) setFailure(String(error.message));
      });
    return () => {
      current = false;
    };
  }, [requested, attempt]);
  if (state.loading) return <EntryProgress />;
  if (state.error) return <ReadState error={state.error} retry={state.refresh} />;
  if (!requested) return children;
  if (!failure)
    return (
      <EntryProgress
        title="Preparing your demo company"
        detail="Orders, deliveries and invoices are being prepared for you to explore."
      />
    );
  return (
    <section className="mx-auto max-w-xl space-y-4 p-8" aria-live="polite">
      <h1 className="text-2xl font-semibold">{t("Preparing your demo company")}</h1>
      <p>{t("Orders, deliveries and invoices are being prepared for you to explore.")}</p>
      <ReadState
        loading={!failure}
        error={failure}
        retry={() => setAttempt((value) => value + 1)}
      />
    </section>
  );
}

type TrialContext = {
  active: ActiveTask;
  start: (task: StarterTask) => void;
  complete: () => void;
  available: boolean;
  visible: boolean;
  dismiss: () => void;
};
const Trial = createContext<TrialContext | null>(null);
export function TrialProvider({
  user,
  tenant,
  enabled,
  children,
}: {
  user: string;
  tenant: string;
  enabled: boolean;
  children: ReactNode;
}) {
  const [active, setActive] = useState<ActiveTask>(null);
  const [completed, setCompleted] = useState(false);
  const [dismissed, setDismissed] = useState(() => {
    try {
      return localStorage.getItem(promptKey(user)) === "true";
    } catch {
      return false;
    }
  });
  useEffect(() => {
    const changed = (event: StorageEvent) => {
      if (event.key === promptKey(user)) setDismissed(event.newValue === "true");
    };
    window.addEventListener("storage", changed);
    return () => window.removeEventListener("storage", changed);
  }, [user]);
  const dismiss = () => {
    setDismissed(true);
    try {
      localStorage.setItem(promptKey(user), "true");
    } catch {
      /* Optional browser preference. */
    }
  };
  return (
    <Trial.Provider
      value={{
        active,
        available: enabled,
        start: (task) => setActive({ task, tenant }),
        complete: () => {
          setCompleted(true);
          setActive(null);
        },
        visible: enabled && completed && !dismissed,
        dismiss,
      }}
    >
      {children}
    </Trial.Provider>
  );
}
export function useTrialResult(task: StarterTask, tenant: string, ready: boolean) {
  const trial = useContext(Trial);
  useEffect(() => {
    if (trial && resultCompletesTask(trial.active, task, tenant, ready)) trial.complete();
  }, [trial?.active, task, tenant, ready]);
}
export function TrialTasks({
  tenant,
  navigate,
}: {
  tenant: string;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const trial = useContext(Trial);
  if (!trial?.available) return null;
  return (
    <section className="space-y-3" data-trial-tasks>
      <h2 className="text-xl font-semibold">{t("Try these three questions")}</h2>
      <p className="text-sm text-fg-muted">
        {t("Explore the records directly. These tasks use no AI questions.")}
      </p>
      <div className="grid gap-3 md:grid-cols-3">
        {(
          [
            ["attention", "Which orders need attention?"],
            ["delivery", "Why is this order not fully delivered?"],
            ["invoices", "Which invoices remain open?"],
          ] as const
        ).map(([task, label]) => (
          <button
            key={task}
            className="br-btn h-auto min-h-20 whitespace-normal p-4 text-left"
            onClick={() => {
              trial.start(task);
              navigate(starterSelection(task, tenant));
            }}
          >
            {t(label)}
          </button>
        ))}
      </div>
    </section>
  );
}
export function TrialPrompt() {
  const trial = useContext(Trial);
  if (!trial?.visible) return null;
  return (
    <aside
      className="mb-4 flex flex-wrap items-center gap-3 rounded-xl border border-accent bg-accent-soft p-4"
      data-trial-github
    >
      <p className="mr-auto text-sm">
        {t("Was that useful? Support Reality with a star on GitHub.")}
      </p>
      <a
        className="br-btn"
        href="https://github.com/Xentral-Labs/reality"
        target="_blank"
        rel="noreferrer"
        onClick={trial.dismiss}
      >
        {t("Star on GitHub")}
      </a>
      <button className="br-btn" onClick={trial.dismiss}>
        {t("Keep exploring")}
      </button>
    </aside>
  );
}

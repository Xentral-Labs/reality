import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { api, APIError, type RealityGapDetail, type RealityGapSimulation } from "../api";
import { t } from "../localization";
import { RuleDraftEditor, RuleDefinition } from "./RuleDraftEditor";
import { RuleEvidence, type PrepareRuleChange } from "./RuleEvidence";
import { RuleChangeSummary, SimulationResults } from "./RuleResults";
import {
  draftForRule,
  emptyDraft,
  initialRuleDraft,
  ruleSentence,
  validateDraft,
  type RuleDraft,
} from "./guidedRuleDraft";
import {
  latestDraft,
  resumeStage,
  ruleStarters,
  wizardStages,
  type WizardStage,
} from "./ruleWizardState";

type Review = {
  label: string;
  body: unknown;
  run: () => Promise<unknown>;
  next?: WizardStage;
  saveDraft?: boolean;
};
export function FactRuleWizard({
  tenant,
  owner,
  initial,
  onSaved,
  onBusy,
  onUncertain,
  onClose,
}: {
  tenant: string;
  owner: boolean;
  initial: RealityGapDetail | null;
  onSaved: (detail: RealityGapDetail) => void;
  onBusy: (busy: boolean) => void;
  onUncertain: () => void;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState(initial);
  const [stage, setStage] = useState<WizardStage>(() => resumeStage(initial));
  const [question, setQuestion] = useState(initial?.gap.question || "");
  const [purpose, setPurpose] = useState(initial?.gap.intended_use || "");
  const [draft, setDraft] = useState<RuleDraft>(() =>
    initial ? initialRuleDraft(initial) : emptyDraft(),
  );
  const [dirty, setDirty] = useState(false);
  const [selectedStarter, setSelectedStarter] = useState("");
  const [review, setReview] = useState<Review | null>(null);
  const [busy, setBusy] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [error, setError] = useState("");
  const [invalid, setInvalid] = useState<"question" | "purpose" | null>(null);
  const [simulation, setSimulation] = useState<{ id: string; result: RealityGapSimulation } | null>(
    null,
  );
  const mounted = useRef(true),
    lock = useRef(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const reviewHeading = useRef<HTMLHeadingElement>(null);
  const questionInput = useRef<HTMLInputElement>(null),
    purposeInput = useRef<HTMLTextAreaElement>(null);
  const body = useRef<HTMLDivElement>(null);
  const rule = latestDraft(detail);
  const activeRule = detail?.rules.find((r) => r.status === "active");
  const handoff = [...(detail?.entries || [])]
    .reverse()
    .find(
      (entry) =>
        entry.type === "implementation_result" && entry.payload.kind === "developer_package",
    );
  const tested = !!rule && !dirty && simulation?.id === rule.id;
  const disabled = !owner || busy || uncertain;
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useLayoutEffect(() => {
    (review ? reviewHeading : heading).current?.focus();
    body.current?.scrollTo({ top: 0 });
  }, [stage, review, activeRule?.id]);
  const changeDraft = (value: RuleDraft) => {
    setDraft(value);
    setDirty(true);
    setSimulation(null);
    setReview(null);
  };
  const navigate = (value: WizardStage) => {
    if (busy || review) return;
    setError("");
    setStage(value);
  };
  const prepare: PrepareRuleChange = (label, body, run) => {
    if (disabled || lock.current) return;
    setError("");
    setReview({ label, body, run });
  };
  const confirm = async () => {
    if (!review || disabled || lock.current) return;
    lock.current = true;
    setBusy(true);
    onBusy(true);
    setError("");
    try {
      const value = await review.run();
      if (!mounted.current) return;
      const saved = value as RealityGapDetail;
      if (!saved?.gap || !Array.isArray(saved.rules))
        throw new Error("This rule could not be loaded. Close the dialog and try again.");
      setDetail(saved);
      onSaved(saved);
      setReview(null);
      if (review.next === 1)
        setDraft((current) => ({ ...current, logical_name: saved.gap.question }));
      if (review.saveDraft) {
        setDraft(initialRuleDraft(saved));
        setDirty(false);
        setSimulation(null);
      }
      if (review.next !== undefined) setStage(review.next);
      else if (review.label === "Choose interpretation" && saved.gap.destination === "fact")
        setStage(2);
    } catch (reason) {
      if (!mounted.current) return;
      setError(t(reason instanceof Error ? reason.message : String(reason)));
      if (!(reason instanceof APIError) || reason.status >= 500) {
        setUncertain(true);
        setReview(null);
        onUncertain();
      }
    } finally {
      lock.current = false;
      if (mounted.current) {
        setBusy(false);
        onBusy(false);
      }
    }
  };
  const reviewGoal = () => {
    if (disabled) return;
    if (!question.trim() || !purpose.trim()) {
      const field = !question.trim() ? "question" : "purpose";
      setInvalid(field);
      (field === "question" ? questionInput.current : purposeInput.current)?.focus();
      return;
    }
    setInvalid(null);
    const payload = {
      question: question.trim(),
      intended_use: purpose.trim(),
      origin: "web",
      idempotency_key: crypto.randomUUID(),
    };
    setReview({
      label: "Create documented question",
      body: payload,
      run: () => api.createRealityGap(tenant, payload),
      next: 1,
    });
  };
  const reviewDraft = () => {
    if (!detail || disabled) return;
    try {
      const payload = { expected_revision: detail.gap.revision, draft: validateDraft(draft) };
      setError("");
      setReview({
        label: "Prepare rule draft",
        body: payload,
        run: () => api.prepareRealityGap(tenant, detail.gap.id, payload),
        next: 3,
        saveDraft: true,
      });
    } catch (reason) {
      setError(t(reason instanceof Error ? reason.message : String(reason)));
      body.current?.scrollTo({ top: 0 });
    }
  };
  const testRule = async () => {
    if (!detail || !rule || dirty || disabled || lock.current) return;
    lock.current = true;
    setBusy(true);
    onBusy(true);
    setError("");
    setSimulation(null);
    try {
      const result = await api.simulateRealityGapRule(tenant, detail.gap.id, rule.id);
      if (mounted.current) setSimulation({ id: rule.id, result });
    } catch (reason) {
      if (mounted.current) setError(t(reason instanceof Error ? reason.message : String(reason)));
    } finally {
      lock.current = false;
      if (mounted.current) {
        setBusy(false);
        onBusy(false);
      }
    }
  };
  const confirmationLabel = (label: string) =>
    ({
      "Create documented question": "Save goal and continue",
      "Add evidence": "Save this example",
      "Create recommendation": "Request recommendation",
      "Choose interpretation": "Confirm interpretation",
      "Prepare rule draft": "Save draft and continue",
      "Activate rule": "Confirm activation",
      "Prepare implementation package": "Confirm implementation package",
    })[label] || "Confirm";
  const milestone = activeRule
    ? "Your rule is active"
    : handoff
      ? "Implementation package prepared"
      : rule
        ? "Draft saved. It is not active yet."
        : detail
          ? "Goal saved. No rule is active yet."
          : "Nothing has been saved yet.";
  return (
    <div className="flex min-h-0 flex-1 flex-col" data-fact-rule-wizard data-stage={stage}>
      <nav
        aria-label={t("Rule setup progress")}
        className="shrink-0 border-b border-border-default bg-surface-muted/40 px-5 py-3"
      >
        <ol className="grid grid-cols-5 gap-2">
          {wizardStages.map((label, index) => (
            <li
              key={label}
              aria-current={stage === index ? "step" : undefined}
              className="min-w-0 text-center text-xs text-fg-muted aria-[current=step]:font-semibold aria-[current=step]:text-accent"
            >
              <span
                data-current={stage === index}
                className="mx-auto mb-1 flex size-7 items-center justify-center rounded-full border border-border-default data-[current=true]:border-accent data-[current=true]:bg-accent data-[current=true]:text-white"
              >
                {index + 1}
              </span>
              <span className="sr-only sm:not-sr-only sm:block">{t(label)}</span>
            </li>
          ))}
        </ol>
        <p className="mt-2 text-center text-sm sm:hidden">{t(wizardStages[stage])}</p>
      </nav>
      <div
        ref={body}
        className="min-h-0 space-y-5 overflow-y-auto p-5 sm:p-6"
        data-rule-dialog-body
      >
        {error && (
          <p
            role="alert"
            className="rounded-lg border border-caution-text p-3 text-sm text-caution-text"
          >
            {error}
          </p>
        )}
        {uncertain && (
          <p role="alert">
            {t(
              "The result is uncertain. Reload and inspect the current state before another change.",
            )}
          </p>
        )}
        {activeRule ? (
          <section className="space-y-4" role="status">
            <h2 ref={heading} tabIndex={-1} className="text-xl font-semibold">
              {t("Your rule is active")}
            </h2>
            <p>
              {t("It will apply to future matching data. Existing records have not been replayed.")}
            </p>
            <RuleDefinition draft={draftForRule(activeRule, detail!.entries)} />
          </section>
        ) : (
          <>
            {review && (
              <section className="space-y-4" aria-label={t("Review change")}>
                <h2 ref={reviewHeading} tabIndex={-1} className="text-xl font-semibold">
                  {t(review.label)}
                </h2>
                <RuleChangeSummary body={review.body} />
                {review.saveDraft && (
                  <RuleDefinition draft={(review.body as { draft: RuleDraft }).draft} />
                )}
                {review.label === "Activate rule" && rule && (
                  <>
                    <RuleDefinition draft={draftForRule(rule, detail!.entries)} />
                    {simulation && <SimulationResults result={simulation.result} tenant={tenant} />}
                  </>
                )}
                <p className="rounded-lg bg-accent-soft p-4 text-sm">
                  {t(
                    review.label === "Activate rule"
                      ? "It will apply to future matching data. Existing records have not been replayed."
                      : "This saves the reviewed setup step. It does not activate a rule or create Facts.",
                  )}
                </p>
              </section>
            )}
            <div hidden={!!review} className="space-y-5">
              <div>
                <h2 ref={heading} tabIndex={-1} className="text-xl font-semibold">
                  {t(wizardStages[stage])}
                </h2>
                <p className="mt-2 text-sm text-fg-muted">
                  {t(
                    [
                      "A Fact rule remembers a property stated in your data, so your team can find it on the right business record.",
                      "Find an order you know. Choose the field that contains the information you want to remember.",
                      "Describe when the rule applies and what it should remember. Start simple; add conditions only if you need them.",
                      "Test the saved version before activation. This preview does not change business data.",
                      "Check the meaning and the test results. Activation applies to future matching data; historical replay is a separate action.",
                    ][stage],
                  )}
                </p>
              </div>
              <fieldset disabled={disabled} className="min-w-0 space-y-5">
                {stage === 0 &&
                  (detail ? (
                    <div className="space-y-3">
                      <RuleChangeSummary
                        body={{
                          question: detail.gap.question,
                          intended_use: detail.gap.intended_use,
                        }}
                      />
                      <p className="text-sm text-fg-muted">
                        {t(
                          "This goal is already saved. Continue with your example; going back does not create another question.",
                        )}
                      </p>
                    </div>
                  ) : (
                    <>
                      <div className="grid gap-3 sm:grid-cols-3">
                        {ruleStarters.map((starter) => (
                          <button
                            key={starter.title}
                            type="button"
                            aria-label={t(starter.title)}
                            aria-pressed={selectedStarter === starter.title}
                            className="rounded-xl border border-border-default p-4 text-left hover:border-accent aria-pressed:border-accent aria-pressed:bg-accent-soft"
                            onClick={() => {
                              const previous = ruleStarters.find(
                                (item) => item.title === selectedStarter,
                              );
                              setSelectedStarter(starter.title);
                              if (!question || question === t(previous?.question || ""))
                                setQuestion(t(starter.question));
                              if (!purpose || purpose === t(previous?.purpose || ""))
                                setPurpose(t(starter.purpose));
                              setDraft((current) =>
                                !current.predicate || current.predicate === previous?.predicate
                                  ? { ...current, predicate: starter.predicate }
                                  : current,
                              );
                              questionInput.current?.focus();
                            }}
                          >
                            <span className="block font-semibold">{t(starter.title)}</span>
                            <span className="mt-2 block text-sm text-fg-muted">
                              {t(starter.description)}
                            </span>
                          </button>
                        ))}
                      </div>
                      <p className="text-xs text-fg-muted">
                        {t(
                          "Examples are starting points. The next step checks the data actually available in your company.",
                        )}
                      </p>
                      <label className="block text-sm font-medium">
                        {t("What should Reality remember?")}
                        <input
                          ref={questionInput}
                          className="br-control mt-2"
                          value={question}
                          aria-invalid={invalid === "question"}
                          aria-describedby="wizard-question-help"
                          onChange={(e) => {
                            setQuestion(e.target.value);
                            setInvalid(null);
                          }}
                        />
                      </label>
                      <p
                        id="wizard-question-help"
                        className={`text-sm ${invalid === "question" ? "text-caution-text" : "text-fg-muted"}`}
                      >
                        {t(
                          invalid === "question"
                            ? "Describe the information you want to remember."
                            : "For example: What delivery instruction was stated on this order?",
                        )}
                      </p>
                      <label className="block text-sm font-medium">
                        {t("How will this help your team?")}
                        <textarea
                          ref={purposeInput}
                          className="br-control mt-2 resize-y py-3"
                          rows={2}
                          value={purpose}
                          aria-invalid={invalid === "purpose"}
                          aria-describedby="wizard-purpose-help"
                          onChange={(e) => {
                            setPurpose(e.target.value);
                            setInvalid(null);
                          }}
                        />
                      </label>
                      <p
                        id="wizard-purpose-help"
                        className={`text-sm ${invalid === "purpose" ? "text-caution-text" : "text-fg-muted"}`}
                      >
                        {t(
                          invalid === "purpose"
                            ? "Explain what your team will use this information for."
                            : "For example: Help the warehouse follow the customer's delivery instructions.",
                        )}
                      </p>
                    </>
                  ))}
                {detail && (
                  <div hidden={stage !== 1} className="space-y-5">
                    <RuleEvidence
                      tenant={tenant}
                      detail={detail}
                      disabled={disabled}
                      prepare={prepare}
                      guided
                      seed={(example, candidate) => {
                        if (!mounted.current) return;
                        setDraft((current) =>
                          current.source_system || current.output_path
                            ? current
                            : {
                                ...current,
                                logical_name: detail.gap.question,
                                source_system: example.source_system,
                                source_type: example.source_type,
                                output_path: candidate.path,
                                value_path: candidate.path,
                                value_type: candidate.value_type,
                              },
                        );
                        setDirty(true);
                        setSimulation(null);
                      }}
                    />
                    {detail.gap.destination && detail.gap.destination !== "fact" && (
                      <div className="space-y-3 rounded-lg bg-surface-muted p-4">
                        <p>
                          {t(
                            "This outcome is not a Fact rule. Keep the reviewed result or prepare the existing implementation handoff.",
                          )}
                        </p>
                        <RuleChangeSummary body={{ destination: detail.gap.destination }} />
                        {handoff ? (
                          <section className="space-y-3" role="status">
                            <h3 className="font-semibold">
                              {t("Implementation package prepared")}
                            </h3>
                            <RuleChangeSummary body={handoff.payload} />
                            {Array.isArray(handoff.payload.requirements) && (
                              <ul className="list-disc pl-5 text-sm" data-localization="original">
                                {handoff.payload.requirements.map((item, index) => (
                                  <li key={index}>{String(item)}</li>
                                ))}
                              </ul>
                            )}
                          </section>
                        ) : (
                          <button
                            className="br-btn"
                            onClick={() => {
                              const payload = { expected_revision: detail.gap.revision };
                              prepare("Prepare implementation package", payload, () =>
                                api.prepareRealityGap(tenant, detail.gap.id, payload),
                              );
                            }}
                          >
                            {t("Prepare implementation package")}
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                )}
                {stage === 2 && detail && (
                  <>
                    <div
                      className="rounded-xl border border-accent/20 bg-accent-soft p-4"
                      data-rule-sentence
                    >
                      <p className="mb-2 text-xs font-semibold text-accent">
                        {t("Your rule in words")}
                      </p>
                      <p className="break-words">{ruleSentence(draft, t)}</p>
                    </div>
                    <RuleDraftEditor tenant={tenant} draft={draft} change={changeDraft} guided />
                  </>
                )}
                {stage === 3 && rule && (
                  <>
                    <p className="text-sm">
                      {t("Version")} {rule.version} · {t("Draft saved. It is not active yet.")}
                    </p>
                    <p className="text-sm text-fg-muted">
                      {t(
                        "The supporting example does not limit the test. Reality checks up to 100 matching sources already held by this company.",
                      )}
                    </p>
                    <button className="br-btn" disabled={disabled || dirty} onClick={testRule}>
                      {t(busy ? "Loading" : "Test saved draft")}
                    </button>
                    {dirty && <p>{t("Save your changes before testing this version.")}</p>}
                    {tested && simulation && (
                      <>
                        <SimulationResults tenant={tenant} result={simulation.result} />
                        {simulation.result.matches === 0 && (
                          <p className="text-sm text-caution-text">
                            {t(
                              "No matching examples were found. Check the source and conditions before deciding to activate.",
                            )}
                          </p>
                        )}
                        {!!(
                          simulation.result.invalid_values +
                          simulation.result.ambiguous_subjects +
                          simulation.result.conflicts
                        ) && (
                          <p className="text-sm text-caution-text">
                            {t(
                              "Some sources need attention. Review the problems above or go back and adjust your rule.",
                            )}
                          </p>
                        )}
                      </>
                    )}
                    {!tested && (
                      <p className="text-sm text-fg-muted">
                        {t("Run the test to make activation review available.")}
                      </p>
                    )}
                  </>
                )}
                {stage === 4 && rule && (
                  <>
                    <p className="text-sm">
                      {t("Version")} {rule.version}
                    </p>
                    <p className="rounded-xl bg-accent-soft p-4 break-words">
                      {ruleSentence(draftForRule(rule, detail!.entries), t)}
                    </p>
                    <RuleDefinition draft={draftForRule(rule, detail!.entries)} />
                    {simulation && <SimulationResults tenant={tenant} result={simulation.result} />}
                  </>
                )}
              </fieldset>
            </div>
          </>
        )}
      </div>
      <footer
        className="shrink-0 space-y-2 border-t border-border-default bg-surface px-5 py-3"
        data-wizard-footer
      >
        <p className="text-xs text-fg-muted" role="status">
          {t(milestone)}{" "}
          {!activeRule && t("Closing keeps saved steps; unsaved changes will be lost.")}
        </p>
        <div className="flex flex-wrap items-center justify-end gap-2">
          {activeRule ? (
            <button className="br-btn br-btn-primary" onClick={onClose}>
              {t("Done")}
            </button>
          ) : review ? (
            <>
              <button className="br-btn" disabled={busy} onClick={() => setReview(null)}>
                {t("Back to editing")}
              </button>
              <button
                className="br-btn br-btn-primary"
                data-wizard-confirm
                disabled={disabled}
                onClick={confirm}
              >
                {t(confirmationLabel(review.label))}
              </button>
            </>
          ) : (
            <>
              {stage > 0 && (
                <button
                  className="br-btn mr-auto"
                  disabled={busy}
                  onClick={() => navigate((stage - 1) as WizardStage)}
                >
                  {t("Back")}
                </button>
              )}
              <button className="br-btn" disabled={busy} onClick={onClose}>
                {t("Cancel")}
              </button>
              {stage === 0 && (
                <button
                  className="br-btn br-btn-primary"
                  disabled={disabled}
                  onClick={detail ? () => navigate(1) : reviewGoal}
                >
                  {t(detail ? "Find an example" : "Review goal")}
                </button>
              )}
              {stage === 1 && detail?.gap.destination === "fact" && (
                <button
                  className="br-btn br-btn-primary"
                  disabled={disabled}
                  onClick={() => navigate(2)}
                >
                  {t("Describe the rule")}
                </button>
              )}
              {stage === 2 && (
                <button
                  className="br-btn br-btn-primary"
                  disabled={disabled}
                  onClick={!dirty && rule ? () => navigate(3) : reviewDraft}
                >
                  {t(!dirty && rule ? "Test with existing data" : "Review draft")}
                </button>
              )}
              {stage === 3 && (
                <button
                  className="br-btn br-btn-primary"
                  disabled={disabled || !tested}
                  onClick={() => navigate(4)}
                >
                  {t("Review activation")}
                </button>
              )}
              {stage === 4 && rule && detail && (
                <button
                  className="br-btn br-btn-primary"
                  disabled={disabled || !tested}
                  onClick={() =>
                    prepare("Activate rule", { rule: rule.id, version: rule.version }, () =>
                      api.activateRealityGapRule(tenant, detail.gap.id, rule.id),
                    )
                  }
                >
                  {t("Activate rule")}
                </button>
              )}
            </>
          )}
        </div>
      </footer>
    </div>
  );
}

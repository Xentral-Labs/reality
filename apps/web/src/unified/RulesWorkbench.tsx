import { FactRuleWizard } from "./FactRuleWizard";
import { usesWizard } from "./ruleWizardState";
import { RuleDraftEditor, RuleDefinition } from "./RuleDraftEditor";
import { RuleEvidence } from "./RuleEvidence";
import {
  SimulationResults,
  ExecutionResults,
  RuleMetrics,
  RuleChangeSummary,
  type ReplayResult,
} from "./RuleResults";
import {
  emptyDraft,
  initialRuleDraft,
  ruleSentence,
  draftForRule,
  validateDraft,
  readDraft,
  type RuleDraft,
} from "./guidedRuleDraft";
import { RegisterWorkbench, RegisterToolbar } from "./RegisterWorkbench";
import { PageActionBar } from "./PageActionBar";
import { RegisterTable } from "./RegisterTable";
import { FilterChip } from "./FilterChip";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { api, APIError, type RealityGapSimulation, type RealityGapDetail } from "../api";
import { formatDateTime, t } from "../localization";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
export function RulesWorkbench({ tenant, owner }: { tenant: string; owner: boolean }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [wizard, setWizard] = useState(false);
  const draftEditor = useRef<HTMLDivElement>(null);
  const hydrated = useRef("");
  const reviewHeading = useRef<HTMLHeadingElement>(null);
  const [pageSize, setPageSize] = useState(50);
  const [ruleStatus, setRuleStatus] = useState("");
  const [page, setPage] = useState(1),
    [query, setQuery] = useState("");
  const list = useRead(
    () => api.realityGaps(tenant, { lifecycle: "all", page, size: pageSize, query, ruleStatus }),
    [tenant, page, pageSize, query, ruleStatus],
  );
  const [id, setId] = useState("");
  const [savedDetail, setSavedDetail] = useState<RealityGapDetail | null>(null);
  const detail = useRead(
    () => (id ? api.realityGap(tenant, id) : Promise.resolve(null)),
    [tenant, id],
  );
  const [question, setQuestion] = useState(""),
    [purpose, setPurpose] = useState("");
  const [payload, setPayload] = useState('{"text":""}');
  const [draft, setDraft] = useState(JSON.stringify(emptyDraft(), null, 2));
  const [result, setResult] = useState<unknown>(null),
    [error, setError] = useState("");
  const [uncertain, setUncertain] = useState(false),
    [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const [simulated, setSimulated] = useState("");
  const [simulation, setSimulation] = useState<RealityGapSimulation | null>(null);
  const [replay, setReplay] = useState<{ rule: string; result: ReplayResult } | null>(null);
  const [review, setReview] = useState<{
    label: string;
    body: unknown;
    run: () => Promise<unknown>;
  } | null>(null);
  const loadedGap = detail.data?.gap.id === id ? detail.data : undefined;
  const gap =
    savedDetail?.gap.id === id && (!loadedGap || savedDetail.gap.revision > loadedGap.gap.revision)
      ? savedDetail
      : loadedGap;
  useLayoutEffect(() => {
    if (!editorOpen || !gap || hydrated.current === id) return;
    hydrated.current = id;
    setDraft(JSON.stringify(initialRuleDraft(gap), null, 2));
  }, [editorOpen, id, gap]);
  useEffect(() => {
    if (review) reviewHeading.current?.focus();
  }, [review]);
  useEffect(() => {
    if (!editorOpen) return;
    const previous = document.activeElement as HTMLElement | null;
    const node = dialog.current;
    node?.showModal();
    return () => {
      node?.close();
      previous?.focus();
    };
  }, [editorOpen]);
  const openEditor = (target: string, statuses: string[] = []) => {
    if (busy || uncertain) return;
    if (!target) {
      setRuleStatus("");
      setQuery("");
      setPage(1);
    }
    hydrated.current = "";
    setWizard(owner && usesWizard(statuses));
    setId(target);
    setSavedDetail((current) => (current?.gap.id === target ? current : null));
    setQuestion("");
    setPurpose("");
    setPayload('{"text":""}');
    setDraft(JSON.stringify(emptyDraft(), null, 2));
    setResult(null);
    setReview(null);
    setError("");
    setSimulated("");
    setSimulation(null);
    setReplay(null);
    setEditorOpen(true);
  };
  const confirm = async () => {
    if (!review || !owner || lock.current || uncertain) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      const value = await review.run();
      setResult(value);
      setReview(null);
      if (value && typeof value === "object" && "gap" in value) {
        setId((value as RealityGapDetail).gap.id);
        setSavedDetail(value as RealityGapDetail);
      }
      detail.refresh();
      list.refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
      if (!(reason instanceof APIError) || reason.status >= 500) {
        setUncertain(true);
        setReview(null);
      }
    } finally {
      lock.current = false;
      setBusy(false);
    }
  };
  const prepare = (label: string, body: unknown, run: () => Promise<unknown>) => {
    setError("");
    if (!owner || busy || uncertain) return;
    setReview({ label, body, run });
  };
  const json = (value: string) => {
    const parsed: unknown = JSON.parse(value);
    if (!parsed || Array.isArray(parsed) || typeof parsed !== "object")
      throw new Error("Expected a JSON object");
    return parsed as Record<string, unknown>;
  };
  const parseAction = (action: () => void) => {
    try {
      action();
    } catch (reason) {
      setError(t(reason instanceof Error ? reason.message : String(reason)));
    }
  };
  return (
    <RegisterWorkbench>
      {!owner && (
        <p className="mb-3 text-sm text-fg-muted">
          {t("Rule changes require company owner or platform administrator access.")}
        </p>
      )}
      {uncertain && !editorOpen && (
        <p role="alert">
          {t(
            "The result is uncertain. Reload and inspect the current state before another change.",
          )}
        </p>
      )}
      <section className="register-surface" data-rules-register>
        <RegisterToolbar
          search={
            <>
              {" "}
              <input
                className="br-control"
                aria-label={t("Search")}
                placeholder={t("Search")}
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setPage(1);
                }}
              />
            </>
          }
          filters={
            <>
              {" "}
              <div className="contents">
                <FilterChip
                  label={t("Rule status")}
                  select={
                    <select
                      disabled={busy || uncertain}
                      aria-label={t("Rule status")}
                      value={ruleStatus}
                      onChange={(event) => {
                        setRuleStatus(event.target.value);
                        setPage(1);
                        setId("");
                        setResult(null);
                        setReview(null);
                      }}
                    >
                      <option value="">{t("All")}</option>
                      <option value="active">{t("Active")}</option>
                      <option value="draft">{t("Draft")}</option>
                      <option value="disabled">{t("Disabled")}</option>
                    </select>
                  }
                />
              </div>
            </>
          }
          count={list.data?.total}
        />
        <PageActionBar
          actions={[
            {
              key: "create",
              label: "New rule",
              disabled: !owner || busy || uncertain,
              onClick: () => openEditor(""),
            },
          ]}
        />
        {!list.data ? (
          <ReadState loading={list.loading} error={list.error} retry={list.refresh} rows={8} />
        ) : (
          <>
            <div className="register-table-inset">
              <RegisterTable
                busy={list.loading}
                empty={{ hint: t("Adjust your search or create the first record.") }}
                cursorView={{ id: "inspector:rules", widths: [240, 200, 140, 130, 60] }}
                footer={
                  <>
                    <label className="flex items-center gap-2 whitespace-nowrap">
                      {t("Rows per page")}
                      <select
                        className="br-control !w-auto min-w-20"
                        value={pageSize}
                        onChange={(event) => {
                          setPageSize(Number(event.target.value));
                          setPage(1);
                        }}
                      >
                        {[25, 50, 100].map((size) => (
                          <option key={size} value={size}>
                            {size}
                          </option>
                        ))}
                      </select>
                    </label>
                    {list.data.total > pageSize && (
                      <>
                        <button
                          className="br-btn"
                          disabled={page === 1}
                          onClick={() => setPage(page - 1)}
                        >
                          {t("Previous")}
                        </button>
                        <span>
                          {page} / {Math.ceil(list.data.total / pageSize)}
                        </span>
                        <button
                          className="br-btn"
                          disabled={page * pageSize >= list.data.total}
                          onClick={() => setPage(page + 1)}
                        >
                          {t("Next")}
                        </button>
                      </>
                    )}
                  </>
                }
              >
                <thead>
                  <tr>
                    <th>{t("Business question")}</th>
                    <th>{t("Intended use")}</th>
                    <th>{t("Rule status")}</th>
                    <th>{t("Updated at")}</th>
                    <th>{t("Actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {list.data.items.map((row) => (
                    <tr key={row.id}>
                      <td data-localization="original">{row.question}</td>
                      <td data-localization="original">{row.intended_use}</td>
                      <td>
                        {(row.rule_statuses || [])
                          .map((state) =>
                            t(
                              state === "active"
                                ? "Active"
                                : state === "draft"
                                  ? "Draft"
                                  : "Disabled",
                            ),
                          )
                          .join(" · ") || "—"}
                      </td>
                      <td>{row.updated_at ? formatDateTime(row.updated_at) : "—"}</td>
                      <td>
                        <button
                          className="br-btn"
                          disabled={busy || uncertain}
                          aria-label={`${t(owner ? "Edit" : "Open")}: ${row.question}`}
                          onClick={() => openEditor(row.id, row.rule_statuses || [])}
                        >
                          {t(owner ? "Edit" : "Open")}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </RegisterTable>
            </div>
          </>
        )}
      </section>
      {editorOpen && (
        <dialog
          ref={dialog}
          aria-label={t(
            id ? (wizard || (gap && !gap.rules.length) ? "Set up rule" : "Edit rule") : "New rule",
          )}
          onCancel={(event) => {
            event.preventDefault();
            if (!busy) setEditorOpen(false);
          }}
          className="m-auto max-h-[90dvh] w-[min(960px,94vw)] overflow-hidden rounded-xl border border-border-default bg-surface text-fg-default backdrop:bg-black/30 open:flex open:flex-col"
        >
          <div className="flex shrink-0 items-center justify-between gap-3 border-b border-border-default px-5 py-3">
            <span className="font-semibold">
              {t(
                id
                  ? wizard || (gap && !gap.rules.length)
                    ? "Set up rule"
                    : "Edit rule"
                  : "New rule",
              )}
            </span>
            <button className="br-btn" disabled={busy} onClick={() => setEditorOpen(false)}>
              {t("Close")}
            </button>
          </div>
          {wizard ? (
            id && !gap ? (
              <div className="p-5">
                <ReadState loading={detail.loading} error={detail.error} retry={detail.refresh} />
              </div>
            ) : (
              <FactRuleWizard
                tenant={tenant}
                owner={owner}
                initial={gap || null}
                onSaved={(value) => {
                  setSavedDetail(value);
                  setId(value.gap.id);
                  list.refresh();
                }}
                onBusy={setBusy}
                onUncertain={() => setUncertain(true)}
                onClose={() => setEditorOpen(false)}
              />
            )
          ) : (
            <>
              <div className="min-h-0 space-y-5 overflow-y-auto p-5 sm:p-6" data-rule-dialog-body>
                {error && (
                  <p role="alert" className="text-caution-text">
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
                {!owner && (
                  <p className="text-sm text-fg-muted">
                    {t("Rule changes require company owner or platform administrator access.")}
                  </p>
                )}
                {!id ? (
                  <fieldset disabled={!owner || busy || uncertain} className="space-y-3">
                    <h2 className="font-semibold">{t("New rule")}</h2>
                    <label className="block text-sm">
                      {t("Business question")}
                      <input
                        className="br-control mt-1"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                      />
                    </label>
                    <label className="block text-sm">
                      {t("Intended use")}
                      <textarea
                        className="br-control mt-1"
                        value={purpose}
                        onChange={(e) => setPurpose(e.target.value)}
                      />
                    </label>
                    <button
                      className="br-btn br-btn-primary"
                      disabled={!question.trim() || !purpose.trim()}
                      onClick={() => {
                        const body = {
                          question,
                          intended_use: purpose,
                          origin: "web",
                          idempotency_key: crypto.randomUUID(),
                        };
                        prepare("Create documented question", body, () =>
                          api.createRealityGap(tenant, body),
                        );
                      }}
                    >
                      {t("Review change")}
                    </button>
                  </fieldset>
                ) : !gap ? (
                  <ReadState loading={detail.loading} error={detail.error} retry={detail.refresh} />
                ) : (
                  <>
                    <h2 className="font-semibold" data-localization="original">
                      {gap.gap.question}
                    </h2>
                    {!gap.rules.length && (
                      <p className="text-sm text-fg-muted">
                        {t(
                          "The question is recorded. Set up when this observation should be remembered.",
                        )}
                      </p>
                    )}
                    {gap.gap.destination === "fact" && (
                      <div
                        className="rounded-xl border border-accent/20 bg-accent-soft p-4"
                        data-rule-sentence
                      >
                        <p className="mb-1 text-xs font-medium text-accent">
                          {t("Your rule in words")}
                        </p>
                        <p className="text-base leading-relaxed">
                          {(() => {
                            try {
                              return ruleSentence(readDraft(draft), t);
                            } catch {
                              return t("Complete the rule below.");
                            }
                          })()}
                        </p>
                      </div>
                    )}
                    <fieldset disabled={!owner || busy || uncertain} className="space-y-3">
                      {gap.gap.destination === "fact" && (
                        <div ref={draftEditor}>
                          {(() => {
                            try {
                              const value = readDraft(draft);
                              return (
                                <RuleDraftEditor
                                  tenant={tenant}
                                  draft={value}
                                  change={(value) => setDraft(JSON.stringify(value, null, 2))}
                                />
                              );
                            } catch {
                              return (
                                <p role="alert">
                                  {t(
                                    "This rule could not be loaded. Close the dialog and try again.",
                                  )}
                                </p>
                              );
                            }
                          })()}
                        </div>
                      )}
                      <section
                        className="space-y-4 rounded-xl border border-border-default p-4"
                        data-rule-step="test"
                      >
                        <h3 className="flex items-center gap-3 font-semibold">
                          <span className="flex size-7 items-center justify-center rounded-full bg-accent-soft text-sm text-accent">
                            3
                          </span>
                          {t("Check with examples")}
                        </h3>
                        <RuleEvidence
                          key={`${tenant}:${id}`}
                          tenant={tenant}
                          detail={gap}
                          disabled={!owner || busy || uncertain}
                          prepare={prepare}
                          seed={(example, candidate) => {
                            setDraft((current) => {
                              let value: RuleDraft;
                              try {
                                value = JSON.parse(current) as RuleDraft;
                              } catch {
                                return current;
                              }
                              if (!value || typeof value !== "object") return current;
                              if (value.source_system || value.output_path) return current;
                              return JSON.stringify(
                                {
                                  ...value,
                                  logical_name: gap.gap.question,
                                  source_system: example.source_system,
                                  source_type: example.source_type,
                                  output_path: candidate.path,
                                  value_path: candidate.path,
                                  value_type: candidate.value_type,
                                },
                                null,
                                2,
                              );
                            });
                          }}
                        />
                        <p className="text-sm text-fg-muted">
                          {t(
                            gap.rules.length
                              ? "Tests use a saved version. Review and save your changes before testing them."
                              : "Review and save a draft first. Then test it with the sources already in Reality.",
                          )}
                        </p>
                        {gap.rules
                          .filter((rule) => !ruleStatus || rule.status === ruleStatus)
                          .map((rule) => (
                            <section
                              key={rule.id}
                              data-rule-version={rule.id}
                              className="rounded border border-border-default p-3"
                            >
                              <div className="flex items-center justify-between gap-3">
                                <h3 className="font-semibold">
                                  {t("Version")} {rule.version}
                                </h3>
                                <span className="rounded bg-accent-soft px-2 py-1 text-xs">
                                  {t(
                                    rule.status === "active"
                                      ? "Active"
                                      : rule.status === "draft"
                                        ? "Draft"
                                        : "Disabled",
                                  )}
                                </span>
                              </div>
                              <p className="my-2 text-sm text-fg-muted">
                                {t(
                                  rule.status === "active"
                                    ? "This version is active and is applied to matching data."
                                    : rule.status === "draft"
                                      ? "This draft is not applied. Simulate it before activation."
                                      : "This version is disabled and retained for history.",
                                )}
                              </p>
                              <details className="my-3">
                                <summary className="cursor-pointer text-sm">
                                  {t("Rule details")}
                                </summary>
                                <RuleDefinition draft={draftForRule(rule, gap.entries)} />
                              </details>
                              <ExecutionResults rule={rule} tenant={tenant} />
                              <div className="flex flex-wrap gap-2">
                                <button
                                  className="br-btn"
                                  onClick={() => {
                                    if (draftEditor.current) {
                                      draftEditor.current.scrollIntoView({ block: "start" });
                                      draftEditor.current.querySelector("input")?.focus();
                                    }
                                    setDraft(
                                      JSON.stringify(draftForRule(rule, gap.entries), null, 2),
                                    );
                                  }}
                                >
                                  {t("Use as draft")}
                                </button>
                                <button
                                  className="br-btn"
                                  disabled={busy}
                                  onClick={async () => {
                                    if (lock.current) return;
                                    lock.current = true;
                                    setBusy(true);
                                    try {
                                      setSimulated("");
                                      setSimulation(null);
                                      const preview = await api.simulateRealityGapRule(
                                        tenant,
                                        id,
                                        rule.id,
                                      );
                                      setSimulation(preview);
                                      setSimulated(rule.id);
                                    } catch (reason) {
                                      setError(
                                        t(
                                          reason instanceof Error ? reason.message : String(reason),
                                        ),
                                      );
                                    } finally {
                                      lock.current = false;
                                      setBusy(false);
                                    }
                                  }}
                                >
                                  {t("Simulate rule")}
                                </button>
                                {rule.status === "draft" && (
                                  <button
                                    disabled={simulated !== rule.id}
                                    className="br-btn"
                                    onClick={() =>
                                      prepare(
                                        "Activate rule",
                                        { rule: rule.id, version: rule.version },
                                        () => api.activateRealityGapRule(tenant, id, rule.id),
                                      )
                                    }
                                  >
                                    {t("Activate rule")}
                                  </button>
                                )}
                                {rule.status === "active" && (
                                  <button
                                    className="br-btn"
                                    onClick={() => {
                                      const cursor =
                                        replay?.rule === rule.id ? replay.result.next_cursor : null;
                                      prepare(
                                        cursor ? "Continue replay" : "Replay history",
                                        { rule: rule.id, cursor },
                                        async () => {
                                          const value = await api.replayRealityGapRule(
                                            tenant,
                                            id,
                                            rule.id,
                                            cursor,
                                          );
                                          setReplay({ rule: rule.id, result: value });
                                          return value;
                                        },
                                      );
                                    }}
                                  >
                                    {t(
                                      replay?.rule === rule.id && !replay.result.complete
                                        ? "Continue replay"
                                        : "Replay history",
                                    )}
                                  </button>
                                )}
                                {rule.status === "active" && (
                                  <button
                                    className="br-btn"
                                    onClick={() =>
                                      prepare("Disable rule", { rule: rule.id }, () =>
                                        api.disableRealityGapRule(tenant, id, rule.id),
                                      )
                                    }
                                  >
                                    {t("Disable rule")}
                                  </button>
                                )}
                              </div>
                              {simulation && simulated === rule.id && (
                                <div className="mt-4">
                                  <SimulationResults result={simulation} tenant={tenant} />
                                </div>
                              )}
                              {replay?.rule === rule.id && (
                                <section
                                  className="mt-4 space-y-3"
                                  aria-label={t("Historical replay")}
                                >
                                  <h4 className="font-semibold">
                                    {t(
                                      replay.result.complete
                                        ? "Replay complete"
                                        : "More sources remain",
                                    )}
                                  </h4>
                                  <RuleMetrics counts={replay.result.cumulative} />
                                </section>
                              )}
                            </section>
                          ))}
                      </section>
                      <details data-rule-support open={!gap.gap.destination}>
                        <summary className="cursor-pointer font-medium">
                          {t("Further details")}
                        </summary>
                        <div className="mt-3 space-y-4">
                          {" "}
                          <details>
                            <summary className="cursor-pointer text-sm">
                              {t("Add evidence or context")}
                            </summary>
                            <textarea
                              aria-label={t("Context JSON")}
                              rows={6}
                              className="br-control rule-context-editor mt-2 font-mono"
                              value={payload}
                              onChange={(e) => setPayload(e.target.value)}
                            />
                            <button
                              className="br-btn mt-2"
                              onClick={() =>
                                parseAction(() => {
                                  const body = {
                                    entry_type: "context",
                                    payload: json(payload),
                                    expected_revision: gap.gap.revision,
                                  };
                                  prepare("Add context", body, () =>
                                    api.addRealityGapEntry(tenant, id, body),
                                  );
                                })
                              }
                            >
                              {t("Review change")}
                            </button>
                          </details>
                          <details>
                            <summary className="cursor-pointer text-sm">
                              {t("Supporting records and history")}
                            </summary>
                            <pre
                              className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-all text-xs"
                              data-localization="original"
                            >
                              {JSON.stringify(gap.entries, null, 2)}
                            </pre>
                          </details>
                        </div>
                      </details>
                      {gap.gap.destination && gap.gap.destination !== "fact" && (
                        <button
                          className="br-btn"
                          onClick={() => {
                            const body = { expected_revision: gap.gap.revision };
                            prepare("Prepare implementation package", body, () =>
                              api.prepareRealityGap(tenant, id, body),
                            );
                          }}
                        >
                          {t("Prepare implementation package")}
                        </button>
                      )}
                    </fieldset>
                  </>
                )}
                {review && (
                  <section
                    className="space-y-3 rounded-lg border border-accent p-4"
                    aria-label={t("Review change")}
                  >
                    <h3 ref={reviewHeading} tabIndex={-1} className="font-semibold">
                      {t(review.label)}
                    </h3>
                    <RuleChangeSummary body={review.body} />
                    {review.label === "Activate rule" && simulation && (
                      <RuleMetrics
                        counts={{
                          expected_facts: simulation.expected_facts,
                          invalid_values: simulation.invalid_values,
                          ambiguous_subjects: simulation.ambiguous_subjects,
                          conflicts: simulation.conflicts,
                        }}
                      />
                    )}
                    {["Replay history", "Continue replay"].includes(review.label) && (
                      <p className="text-sm text-fg-muted">
                        {t("This processes one batch of historical sources and may create Facts.")}
                      </p>
                    )}
                    {!!review.body && typeof review.body === "object" && "draft" in review.body && (
                      <RuleDefinition draft={(review.body as { draft: RuleDraft }).draft} />
                    )}
                    <p className="text-sm">
                      {t("Confirm this change for the selected company and rule.")}
                    </p>
                  </section>
                )}
                {result != null && (
                  <details>
                    <summary>{t("Result")}</summary>
                    <pre
                      data-localization="original"
                      className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap break-all text-xs"
                    >
                      {JSON.stringify(result, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
              <footer
                className="flex shrink-0 flex-wrap items-center justify-end gap-2 border-t border-border-default bg-surface px-5 py-3"
                data-rule-footer
              >
                {review ? (
                  <>
                    {" "}
                    <button className="br-btn" disabled={busy} onClick={() => setReview(null)}>
                      {t("Cancel")}
                    </button>
                    <button
                      className="br-btn br-btn-primary"
                      disabled={busy || uncertain}
                      onClick={confirm}
                    >
                      {t("Confirm")}
                    </button>
                  </>
                ) : (
                  <>
                    <button className="br-btn" disabled={busy} onClick={() => setEditorOpen(false)}>
                      {t("Cancel")}
                    </button>
                    {gap?.gap.destination === "fact" && (
                      <button
                        className="br-btn br-btn-primary"
                        disabled={!owner || busy || uncertain}
                        onClick={() =>
                          parseAction(() => {
                            const body = {
                              expected_revision: gap.gap.revision,
                              draft: validateDraft(readDraft(draft)),
                            };
                            prepare("Prepare rule draft", body, () =>
                              api.prepareRealityGap(tenant, id, body),
                            );
                          })
                        }
                      >
                        {t("Review changes")}
                      </button>
                    )}
                  </>
                )}
              </footer>
            </>
          )}
        </dialog>
      )}
    </RegisterWorkbench>
  );
}

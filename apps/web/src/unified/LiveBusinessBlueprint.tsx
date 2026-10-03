import { LoaderCircle, Code2 } from "lucide-react";
import { useEffect, useRef, useState, useId } from "react";
import { api } from "../api";
import { SourceEvidence } from "./SourceEvidence";
import { t, currentLanguage } from "../localization";
import {
  diagram,
  sourceRanges,
  type BusinessBlueprint,
  type LogicComparison,
} from "../../../shared/businessBlueprint";

export function LiveBusinessBlueprint({
  tenant,
  kind,
  entryKey,
}: {
  tenant: string;
  kind: string;
  entryKey: string;
}) {
  const [data, setData] = useState<BusinessBlueprint | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const flowId = useId();
  useEffect(() => {
    if (!loading) return;
    const started = Date.now();
    setElapsed(0);
    const timer = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(timer);
  }, [loading]);
  const [selected, setSelected] = useState("");
  const [selectedTest, setSelectedTest] = useState("");
  const [comparison, setComparison] = useState<LogicComparison | null>(null);
  const [facts, setFacts] = useState<Record<string, string>>({});
  const [source, setSource] = useState("");
  const [sourceRule, setSourceRule] = useState("");
  const [activeTab, setActiveTab] = useState("rules");
  const sequence = useRef(0);
  const comparisonSequence = useRef(0);
  const [recordKind, setRecordKind] = useState("party");
  const [recordId, setRecordId] = useState("");
  useEffect(() => {
    sequence.current++;
    setActiveTab("rules");
    setSourceRule("");
    setLoading(false);
    setFacts({});
    setRecordId("");
    setData(null);
    setSelected("");
    setSelectedTest("");
    setComparison(null);
    setSource("");
    setError("");
  }, [kind, entryKey, tenant]);
  useEffect(() => {
    comparisonSequence.current++;
    setComparison(null);
  }, [facts, selectedTest, recordId, recordKind, tenant]);
  const read = async (brief = true) => {
    const request = ++sequence.current;
    const priorTest = selectedTest;
    setData(null);
    setComparison(null);
    setSelectedTest("");
    setLoading(true);
    setError("");
    try {
      const value = await api.businessLogic(tenant, kind, entryKey, currentLanguage(), brief);
      if (request !== sequence.current) return;
      setSelectedTest("");
      setComparison(null);
      setFacts({});
      setData(value);
      setSelectedTest(
        value.scenarios.some((s) => s.id === priorTest) ? priorTest : value.scenarios[0]?.id || "",
      );
      setSelected(value.nodes.find((n) => n.durable)?.function || value.nodes[0]?.function || "");
      setSource("");
    } catch {
      if (request === sequence.current) setError(t("Live business logic is unavailable."));
    } finally {
      if (request === sequence.current) setLoading(false);
    }
  };
  const nodes = data?.nodes.filter((n) => n.function === selected) || [];
  const layout = diagram(nodes, data?.edges || []);
  const businessNodes = (data?.business?.steps || []).map((n) => ({
    ...n,
    expression: "",
    evidence_id: n.evidence_ids[0],
    context: [],
  }));
  const phrase = (en: string, de: string) => (currentLanguage() === "de" ? de : en);
  const test = data?.scenarios.find((s) => s.id === selectedTest);
  const compare = async () => {
    const sourceRequest = sequence.current;
    const comparisonRequest = ++comparisonSequence.current;
    setComparison(null);
    setError("");
    try {
      const parsed = Object.entries(facts)
        .filter(
          ([name, value]) => value !== "" && !name.endsWith(":currency") && !name.endsWith(":unit"),
        )
        .map(([name, value]) => ({
          name,
          value,
          currency: facts[name + ":currency"] || null,
          unit: facts[name + ":unit"] || null,
        }));
      const result = await api.businessLogicCompare(tenant, {
        kind,
        key: entryKey,
        evidence_digest: data?.evidence_digest,
        scenario_ids: selectedTest ? [selectedTest] : [],
        ...(recordId ? { record: { kind: recordKind, id: recordId } } : { facts: parsed }),
      });
      if (sourceRequest === sequence.current && comparisonRequest === comparisonSequence.current)
        setComparison(result);
    } catch {
      if (sourceRequest === sequence.current && comparisonRequest === comparisonSequence.current)
        setError(t("Case comparison is unavailable."));
    }
  };
  return (
    <section
      className="my-4 space-y-3 rounded-lg border border-border-default p-4"
      data-live-blueprint
    >
      <h3 className="font-semibold">{t("Business logic")}</h3>
      <button type="button" className="br-btn" onClick={() => read(true)} disabled={loading}>
        {t(data ? "Refresh live logic" : "Read live logic")}
      </button>
      {data && (
        <button
          type="button"
          className="br-btn"
          disabled={loading}
          onClick={() => read(false)}
          data-localization="original"
        >
          {phrase("Detailed explanation and test cases", "Ausführliche Erklärung und Testfälle")}
        </button>
      )}
      {loading && (
        <div
          role="status"
          aria-live="polite"
          className="flex gap-3 rounded-lg bg-surface-subtle p-4"
          data-localization="original"
        >
          <LoaderCircle
            className="mt-1 h-5 w-5 shrink-0 animate-spin motion-reduce:animate-none"
            aria-hidden="true"
          />
          <div>
            <p className="font-medium">
              {phrase(
                "Reading current source and tests…",
                "Aktueller Quellcode und Tests werden gelesen…",
              )}
            </p>
            <p className="mt-2 text-sm">
              {phrase(
                "Reading English descriptions directly from current source. No AI generation.",
                "Englische Beschreibungen werden direkt aus dem aktuellen Quelltext gelesen. Ohne KI-Generierung.",
              )}
            </p>
            <p className="mt-2 text-xs" aria-live="off">
              {elapsed} {phrase("seconds elapsed", "Sekunden vergangen")}
            </p>
            {elapsed >= 60 && (
              <p className="mt-2 text-sm">
                {phrase(
                  "Still waiting for the live response. No result is available yet.",
                  "Die Live-Antwort steht noch aus. Es liegt noch kein Ergebnis vor.",
                )}
              </p>
            )}
          </div>
        </div>
      )}
      {error && <p role="alert">{error}</p>}
      {data && (
        <>
          <div
            role="tablist"
            aria-label={phrase("Read business logic", "Geschäftslogik lesen")}
            className="flex flex-wrap gap-2 border-b border-border-default pb-3"
          >
            {["rules", "tests", "technical"].map((tab, index) => (
              <button
                key={tab}
                type="button"
                role="tab"
                id={`${flowId}-tab-${tab}`}
                aria-controls={`${flowId}-panel-${tab}`}
                aria-selected={activeTab === tab}
                tabIndex={activeTab === tab ? 0 : -1}
                className="rounded-md px-4 py-2 text-sm font-medium hover:bg-surface-subtle data-[selected=true]:bg-indigo-100 dark:data-[selected=true]:bg-indigo-950"
                data-selected={activeTab === tab}
                onClick={() => setActiveTab(tab)}
                onKeyDown={(event) => {
                  const tabs = ["rules", "tests", "technical"];
                  let next = index;
                  if (event.key === "ArrowRight") next = (index + 1) % 3;
                  else if (event.key === "ArrowLeft") next = (index + 2) % 3;
                  else if (event.key === "Home") next = 0;
                  else if (event.key === "End") next = 2;
                  else return;
                  event.preventDefault();
                  setActiveTab(tabs[next]);
                  document.getElementById(`${flowId}-tab-${tabs[next]}`)?.focus();
                }}
                data-localization="original"
              >
                {tab === "rules"
                  ? phrase("Steps", "Schritte")
                  : tab === "tests"
                    ? `${phrase("Test cases", "Testfälle")} (${data.scenarios.length})`
                    : phrase("Technical evidence", "Technische Nachweise")}
              </button>
            ))}
          </div>
          <div
            data-business-reading-view
            className="space-y-4"
            hidden={activeTab !== "rules"}
            role="tabpanel"
            id={`${flowId}-panel-rules`}
            aria-labelledby={`${flowId}-tab-rules`}
          >
            <h4 className="font-medium" data-localization="original">
              {data.business?.heading || phrase("Business explanation", "Fachliche Erklärung")}
            </h4>
            <p className="text-sm text-fg-muted" data-localization="original">
              {data.business?.mode === "llm"
                ? phrase(
                    "Selected steps explained from current code; interpretation needs review.",
                    "Ausgewählte Schritte aus aktuellem Code erklärt; die Interpretation muss geprüft werden.",
                  )
                : data.business?.notice ||
                  phrase(
                    "Business interpretation unavailable. Original evidence remains in Technical evidence.",
                    "Fachliche Erklärung nicht verfügbar. Die Originalnachweise stehen unter Technische Nachweise.",
                  )}
            </p>
            {data.business?.overview && (
              <div>
                <p className="text-sm font-medium" data-localization="original">
                  {data.business.overview.text}
                </p>
                <details>
                  <summary
                    className="inline-flex cursor-pointer list-none items-center gap-2 rounded-md border border-border-default px-3 py-1.5 text-xs"
                    data-localization="original"
                  >
                    <Code2 size={14} aria-hidden="true" />
                    {phrase("Show referenced source", "Markierte Quellstelle anzeigen")}
                  </summary>
                  {data.sources
                    .filter((e) => data.business?.overview?.evidence_ids.includes(e.id))
                    .map((e) => (
                      <div key={e.id}>
                        <SourceEvidence source={e} ranges={[]} />
                      </div>
                    ))}
                </details>
              </div>
            )}
            <ol className="list-none space-y-4" aria-label={t("Business steps")}>
              {businessNodes.map((step, index) => (
                <li
                  key={step.id}
                  className="rounded-lg border border-border-default bg-surface-subtle p-4"
                >
                  <span className="text-xs font-semibold" data-localization="original">
                    {phrase("Step", "Schritt")} {index + 1}
                  </span>
                  <p
                    className="my-3 whitespace-pre-line text-base leading-relaxed"
                    data-localization="original"
                  >
                    {step.text}
                  </p>
                  <details>
                    <summary
                      className="inline-flex cursor-pointer list-none items-center gap-2 rounded-md border border-border-default px-3 py-1.5 text-xs"
                      data-localization="original"
                    >
                      <Code2 size={14} aria-hidden="true" />
                      {phrase("Show referenced source", "Markierte Quellstelle anzeigen")}
                    </summary>
                    {data.sources
                      .filter((e) => step.evidence_ids.includes(e.id))
                      .map((e) => (
                        <div key={e.id}>
                          <SourceEvidence
                            source={e}
                            ranges={sourceRanges(e, data.nodes, step.rule_ids, step.line)}
                          />
                        </div>
                      ))}
                  </details>
                </li>
              ))}
            </ol>
          </div>
          <section
            hidden={activeTab !== "technical"}
            role="tabpanel"
            id={`${flowId}-panel-technical`}
            aria-labelledby={`${flowId}-tab-technical`}
            className="space-y-4"
          >
            <h4 className="font-semibold" data-localization="original">
              {phrase("Technical evidence", "Technische Nachweise")}
            </h4>
            <p className="text-sm" data-localization="original">
              {data.business?.notice}
            </p>
            <p className="text-xs text-fg-muted" data-localization="original">
              {data.release.version} ·{" "}
              {data.release.commit || data.release.source_digest.slice(0, 16)} · {data.status}
            </p>
            <p className="text-sm" data-localization="original">
              {data.purpose}
            </p>
            <p className="text-xs">
              {t("English explanation from the running source; source identifiers stay exact.")}
            </p>
            {!!data.limitations.length && (
              <details open>
                <summary>{t("Limits of the explanation")}</summary>
                <ul>
                  {data.limitations.map((l, i) => (
                    <li key={i} data-localization="original" className="break-words text-sm">
                      {l}
                    </li>
                  ))}
                </ul>
              </details>
            )}
            <details>
              <summary>{t("Source constants and bindings")}</summary>
              <dl>
                {Object.entries(data.runtime_values || {}).map(([name, value]) => (
                  <div key={name}>
                    <dt data-localization="original">{name}</dt>
                    <dd data-localization="original">
                      {Array.isArray(value) ? value.join(", ") : String(value)}
                    </dd>
                  </div>
                ))}
              </dl>
            </details>
            <details>
              <summary>{t("Inputs and prerequisites")}</summary>
              <p data-localization="original">
                {[...data.inputs, ...data.prerequisites].join(" · ") || t("None specified")}
              </p>
            </details>
            {!!data.nodes.length && (
              <>
                <label className="block text-sm">
                  {t("Logic section")}
                  <select
                    className="br-control mt-1 w-full"
                    value={selected}
                    onChange={(e) => setSelected(e.target.value)}
                    data-localization="original"
                  >
                    {[...new Set(data.nodes.map((n) => n.function))].map((f) => (
                      <option key={f} value={f}>
                        {f.split(".").at(-1)?.replaceAll("_", " ")}
                      </option>
                    ))}
                  </select>
                </label>
                <ol className="list-decimal space-y-3 pl-6" aria-label={t("Business steps")}>
                  {nodes.map((n) => (
                    <li key={n.id}>
                      <p data-localization="original" className="break-words text-sm">
                        {n.text}
                      </p>
                      {!!n.context.length && (
                        <p className="text-xs text-fg-muted" data-localization="original">
                          {n.context.join(" → ")}
                        </p>
                      )}
                      <button
                        className="text-xs underline"
                        type="button"
                        onClick={() => {
                          setSource(n.evidence_id);
                          setSourceRule(n.id);
                        }}
                        data-localization="original"
                      >
                        {n.id} · {n.line}
                      </button>
                    </li>
                  ))}
                </ol>
                <details>
                  <summary>{t("Flow diagram")}</summary>
                  <div className="max-h-96 overflow-auto">
                    <svg
                      role="img"
                      aria-label={t("Flow diagram")}
                      viewBox={`0 0 760 ${layout.height}`}
                      width="100%"
                      style={{ minWidth: 620 }}
                    >
                      {layout.edges.map((e, i) => (
                        <g key={i}>
                          <path
                            d={`M 700 ${e.from} L ${e.to < e.from ? 750 : 725} ${e.from} L ${e.to < e.from ? 750 : 725} ${e.to} L 700 ${e.to}`}
                            fill="none"
                            stroke="currentColor"
                          />
                          <text x="704" y={(e.from + e.to) / 2} fontSize="10">
                            {e.outcome}
                          </text>
                          <path
                            d={`M 706 ${e.to - 4} L 700 ${e.to} L 706 ${e.to + 4}`}
                            fill="none"
                            stroke="currentColor"
                          />
                        </g>
                      ))}
                      {layout.nodes.map((n) => (
                        <g key={n.id}>
                          <rect
                            x="5"
                            y={n.y}
                            width="690"
                            height="55"
                            rx={n.kind === "decision" ? 20 : 5}
                            fill="none"
                            stroke="currentColor"
                          />
                          <text x="15" y={n.y + 20} fontSize="12">
                            {n.kind} · {n.id.slice(-65)}
                          </text>
                          <text x="15" y={n.y + 40} fontSize="11">
                            {n.text.length > 100 ? n.text.slice(0, 100) + "…" : n.text}
                          </text>
                          <title>{n.text}</title>
                        </g>
                      ))}
                    </svg>
                  </div>
                </details>
              </>
            )}
            {source && (
              <details open>
                <summary>{t("Source evidence")}</summary>
                {data.sources
                  .filter((s) => s.id === source)
                  .map((s) => (
                    <div key={s.id}>
                      <SourceEvidence
                        source={s}
                        ranges={sourceRanges(s, data.nodes, sourceRule ? [sourceRule] : [])}
                      />
                    </div>
                  ))}
              </details>
            )}
            <details>
              <summary>
                {t("Test evidence gaps")} ({data.test_gaps.length})
              </summary>
              <p className="text-sm">
                {t(
                  "No branch execution is inferred from a related test. Unproven branches remain explicit.",
                )}
              </p>
              <ul>
                {data.test_gaps.map((id) => (
                  <li key={id} className="break-all text-xs" data-localization="original">
                    {id}
                  </li>
                ))}
              </ul>
            </details>
          </section>
          <section
            hidden={activeTab !== "tests"}
            role="tabpanel"
            id={`${flowId}-panel-tests`}
            aria-labelledby={`${flowId}-tab-tests`}
            className="space-y-4"
          >
            <h4 className="font-semibold">
              {t("Existing executable test cases")} ({data.scenarios.length})
            </h4>
            <p className="text-sm text-fg-muted" data-localization="original">
              {phrase(
                "Choose a reference case. Test presence does not establish a passing run. Original names appear when a business explanation is not yet available.",
                "Wähle einen Referenzfall. Ein vorhandener Test belegt keinen erfolgreichen Lauf. Ohne fachliche Erklärung wird der Originalname angezeigt.",
              )}
            </p>
            {!data.scenarios.length && <p>{t("No matching test evidence is available.")}</p>}
            <div
              className="grid max-h-80 gap-3 overflow-auto sm:grid-cols-2"
              aria-label={phrase("Choose a test case", "Testfall auswählen")}
            >
              {data.scenarios.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  className="rounded-lg border border-border-default p-3 text-left text-sm data-[selected=true]:border-indigo-500 data-[selected=true]:bg-indigo-50 dark:data-[selected=true]:bg-indigo-950"
                  data-selected={selectedTest === s.id}
                  aria-pressed={selectedTest === s.id}
                  onClick={() => {
                    setSelectedTest(s.id);
                    setFacts({});
                    setRecordId("");
                    setComparison(null);
                  }}
                  data-localization="original"
                >
                  {data.business?.scenarios.find((item) => item.id === s.id)?.title || s.name}
                </button>
              ))}
            </div>
            {data.scenarios
              .filter((s) => s.id === selectedTest)
              .map((s) => (
                <article key={s.id} className="rounded-lg border border-border-default p-4">
                  <h5 className="mb-3 font-semibold" data-localization="original">
                    {!data.business?.scenarios.some((item) => item.id === s.id) && (
                      <div
                        className="mb-4 rounded-md bg-surface-subtle p-3 text-sm"
                        data-localization="original"
                      >
                        <p>
                          {phrase(
                            "This test was found in code but has not yet been explained in business terms.",
                            "Dieser Test wurde im Code gefunden, ist aber noch nicht fachlich erklärt.",
                          )}
                        </p>
                        <button
                          type="button"
                          className="br-btn mt-2"
                          disabled={loading}
                          onClick={() => read(false)}
                        >
                          {phrase("Load business explanation", "Fachliche Erklärung laden")}
                        </button>
                      </div>
                    )}
                    {data.business?.scenarios.find((item) => item.id === s.id)?.title || s.name}
                  </h5>

                  {data.business?.scenarios
                    .filter((item) => item.id === s.id)
                    .map((item) => (
                      <div key={item.id} data-business-test>
                        {[
                          [phrase("Given", "Gegeben"), item.given],
                          [phrase("When", "Wenn"), item.when],
                          [phrase("Then", "Dann"), item.then],
                        ].map(([title, values]) => (
                          <div key={title as string}>
                            <h5 className="mt-2 text-sm font-medium" data-localization="original">
                              {title as string}
                            </h5>
                            <ul>
                              {(values as string[]).map((value, i) => (
                                <li key={i} data-localization="original" className="text-sm">
                                  {value}
                                </li>
                              ))}
                            </ul>
                          </div>
                        ))}
                        <p className="text-xs" data-localization="original">
                          {item.notice}
                        </p>
                        {item.unexplained_assertions > 0 && (
                          <p className="text-xs" data-localization="original">
                            {phrase(
                              "Additional test assertions not explained:",
                              "Weitere Testprüfungen noch nicht fachlich erklärt:",
                            )}{" "}
                            {item.unexplained_assertions}
                          </p>
                        )}
                      </div>
                    ))}
                  <details>
                    <summary>
                      {phrase("Technical test evidence", "Technischer Testnachweis")}
                    </summary>
                    <p className="break-all text-xs" data-localization="original">
                      {s.id} · {s.relationship} · {s.run.outcome} ·{" "}
                      {s.run.revision_match
                        ? t("Matching release")
                        : t("Unverified for this release")}
                    </p>
                    {[
                      ["Test setup", s.setup],
                      ["Test action", s.action],
                      ["Asserted expectations", s.expectations],
                      ["Unknown assumptions", s.assumptions],
                    ].map(([title, items]) => (
                      <div key={title as string}>
                        <h5 className="mt-2 text-sm font-medium">{t(title as string)}</h5>
                        <ul>
                          {(items as string[]).map((v, i) => (
                            <li
                              className="break-words text-sm"
                              key={i}
                              data-localization="original"
                            >
                              {v}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </details>
                  <details>
                    <summary>{t("Test source")}</summary>
                    <pre
                      className="max-h-80 overflow-auto whitespace-pre-wrap break-words text-xs"
                      data-localization="original"
                    >
                      {s.code}
                    </pre>
                    {s.helpers.map((h) => (
                      <details key={h.id}>
                        <summary data-localization="original">
                          {h.function} · {h.path}
                        </summary>
                        <pre
                          className="max-h-64 overflow-auto whitespace-pre-wrap text-xs"
                          data-localization="original"
                        >
                          {h.code}
                        </pre>
                      </details>
                    ))}
                  </details>
                </article>
              ))}
            {test && (
              <details>
                <summary>{t("Compare my case")}</summary>
                <p className="text-sm">
                  {t("Enter the conditions of your case. Leave unknown values blank.")}
                </p>
                {[...new Set(test.facts.map((f) => f.name))].map((name) => (
                  <label key={name} className="block text-sm" data-localization="original">
                    {name.replaceAll("_", " ")}
                    <input
                      className="br-control mt-1 w-full"
                      value={facts[name] || ""}
                      onChange={(e) => setFacts({ ...facts, [name]: e.target.value })}
                    />
                    {test.facts.some((f) => f.name === name && f.currency) && (
                      <span>
                        {t("Currency")}
                        <input
                          className="br-control"
                          value={facts[name + ":currency"] || ""}
                          onChange={(e) =>
                            setFacts({ ...facts, [name + ":currency"]: e.target.value })
                          }
                          maxLength={3}
                        />
                      </span>
                    )}
                    {test.facts.some((f) => f.name === name && f.unit) && (
                      <span>
                        {t("Unit")}
                        <input
                          className="br-control"
                          value={facts[name + ":unit"] || ""}
                          onChange={(e) => setFacts({ ...facts, [name + ":unit"]: e.target.value })}
                        />
                      </span>
                    )}
                  </label>
                ))}
                <details>
                  <summary>{t("Use an existing record")}</summary>
                  <label>
                    {t("Record type")}
                    <select
                      className="br-control"
                      value={recordKind}
                      onChange={(e) => setRecordKind(e.target.value)}
                    >
                      <option value="party">{t("Business partner")}</option>
                      <option value="order">{t("Sales order")}</option>
                      <option value="commitment">{t("Commitment")}</option>
                    </select>
                  </label>
                  <label>
                    {t("Record ID")}
                    <input
                      className="br-control"
                      value={recordId}
                      onChange={(e) => setRecordId(e.target.value)}
                    />
                  </label>
                </details>
                <button type="button" className="br-btn" onClick={compare}>
                  {t("Compare conditions")}
                </button>
                {comparison && (
                  <>
                    <p>
                      {t(
                        comparison.context === "current_state"
                          ? "Current state"
                          : "Supplied case facts",
                      )}
                    </p>
                    <p>
                      {t(
                        "Historical rule version is unknown unless recorded evidence identifies it.",
                      )}
                    </p>
                    {comparison.links.map((l) => (
                      <p key={l.kind + l.id} data-localization="original">
                        {l.kind} · {l.id}
                      </p>
                    ))}
                    <details>
                      <summary>{t("Case values")}</summary>
                      <dl>
                        {comparison.case_facts?.map((f) => (
                          <div key={f.name}>
                            <dt data-localization="original">{f.name.replaceAll("_", " ")}</dt>
                            <dd data-localization="original">
                              {String(f.value ?? "unknown")} {f.currency} {f.unit}
                            </dd>
                          </div>
                        ))}
                      </dl>
                    </details>
                    {comparison.recorded_decisions?.map((d) => (
                      <details key={d.event_id}>
                        <summary>
                          {t("Recorded decision")} · {d.recorded_at}
                        </summary>
                        <p data-localization="original">
                          {d.event_id} · {d.rule_version}
                        </p>
                        <dl>
                          {Object.entries(d.facts || {}).map(([name, value]) => (
                            <div key={name}>
                              <dt data-localization="original">{name.replaceAll("_", " ")}</dt>
                              <dd data-localization="original">
                                {typeof value === "object"
                                  ? JSON.stringify(value)
                                  : String(value ?? "unknown")}
                              </dd>
                            </div>
                          ))}
                        </dl>
                      </details>
                    ))}
                    {comparison.comparisons.map((c) => (
                      <div key={c.scenario_id}>
                        <p className="break-all text-xs" data-localization="original">
                          {c.scenario_id}
                        </p>
                        <table className="w-full text-sm">
                          <thead>
                            <tr>
                              <th>{t("Condition")}</th>
                              <th>{t("Test value")}</th>
                              <th>{t("Comparison")}</th>
                            </tr>
                          </thead>
                          <tbody>
                            {c.conditions.map((f, i) => (
                              <tr key={i}>
                                <td data-localization="original">{f.name}</td>
                                <td data-localization="original">{f.test_values.join(" / ")}</td>
                                <td data-localization="original">{f.status}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        <ul>
                          {[...c.unknown_assumptions, ...c.untested_aspects].map((l, i) => (
                            <li key={i} data-localization="original">
                              {l}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </>
                )}
              </details>
            )}
          </section>
        </>
      )}
    </section>
  );
}

import { cloneElement, useId, type ReactElement } from "react";
import { sourceWorkspaceApi, type RealityGapCondition } from "../api";
import { useRead } from "./useCompanyContext";
import { t } from "../localization";
import { operators, operandText, valueTypes, type RuleDraft } from "./guidedRuleDraft";
export function RuleField({
  label,
  children,
}: {
  label: string;
  children: ReactElement<{ id?: string }>;
}) {
  const id = useId();
  return (
    <div className="grid min-w-0 gap-1.5 text-sm">
      <label htmlFor={id} className="font-medium">
        {t(label)}
      </label>
      {cloneElement(children, { id })}
    </div>
  );
}
const control = "br-control w-full min-w-0";
const emptyCondition = (): RealityGapCondition => ({
  path: "",
  scope: "source",
  operator: "equals",
  value_type: "string",
  operand: "",
});
function Conditions({
  mode,
  nodes,
  change,
  depth = 1,
}: {
  mode: "all" | "any";
  nodes: RealityGapCondition[];
  change: (mode: "all" | "any", nodes: RealityGapCondition[]) => void;
  depth?: number;
}) {
  const replace = (index: number, node?: RealityGapCondition) =>
    change(
      mode,
      nodes.flatMap((n, i) => (i === index ? (node ? [node] : []) : [n])),
    );
  return (
    <div
      className="min-w-0 space-y-3 rounded-lg border border-border-default bg-surface-muted/40 p-3"
      data-condition-group
    >
      {nodes.length > 1 && (
        <RuleField label="Condition group mode">
          <select
            className={control}
            value={mode}
            onChange={(e) => change(e.target.value as "all" | "any", nodes)}
          >
            <option value="all">{t("All conditions")}</option>
            <option value="any">{t("Any condition")}</option>
          </select>
        </RuleField>
      )}
      {nodes.map((node, i) => (
        <div
          key={i}
          className="min-w-0 space-y-2 rounded-lg border border-border-default bg-surface p-3"
        >
          {"mode" in node ? (
            <Conditions
              mode={node.mode}
              nodes={node.conditions}
              depth={depth + 1}
              change={(mode, conditions) => replace(i, { mode, conditions })}
            />
          ) : (
            <div className="grid min-w-0 gap-3 sm:grid-cols-2">
              <RuleField label="Field">
                <input
                  className={control}
                  value={node.path}
                  onChange={(e) => replace(i, { ...node, path: e.target.value })}
                />
              </RuleField>
              <RuleField label="Comparison">
                <select
                  className={control}
                  value={node.operator}
                  onChange={(e) => replace(i, { ...node, operator: e.target.value })}
                >
                  {Object.entries(operators).map(([key, label]) => (
                    <option key={key} value={key}>
                      {t(label)}
                    </option>
                  ))}
                </select>
              </RuleField>
              {!["exists", "not_exists"].includes(node.operator) && (
                <RuleField label="Value">
                  <input
                    className={control}
                    value={operandText(node.operand)}
                    onChange={(e) => replace(i, { ...node, operand: e.target.value })}
                  />
                </RuleField>
              )}
              <details className="sm:col-span-2">
                <summary className="cursor-pointer text-xs text-fg-muted">
                  {t("Advanced settings")}
                </summary>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  {" "}
                  <RuleField label="Field scope">
                    <select
                      className={control}
                      value={node.scope}
                      onChange={(e) =>
                        replace(i, { ...node, scope: e.target.value as "source" | "element" })
                      }
                    >
                      <option value="source">{t("Whole source")}</option>
                      <option value="element">{t("Current line")}</option>
                    </select>
                  </RuleField>
                  <RuleField label="Condition value type">
                    <select
                      className={control}
                      value={node.value_type}
                      onChange={(e) => replace(i, { ...node, value_type: e.target.value })}
                    >
                      {valueTypes.map((v) => (
                        <option key={v} value={v}>
                          {v}
                        </option>
                      ))}
                    </select>
                  </RuleField>
                </div>
              </details>
            </div>
          )}
          <button type="button" className="br-btn" onClick={() => replace(i)}>
            {t("Remove")}
          </button>
        </div>
      ))}
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className="br-btn"
          onClick={() => change(mode, [...nodes, emptyCondition()])}
        >
          {t("Add condition")}
        </button>
        {depth < 3 && (
          <button
            type="button"
            className="br-btn"
            onClick={() =>
              change(mode, [...nodes, { mode: "all", conditions: [emptyCondition()] }])
            }
          >
            {t("Add group")}
          </button>
        )}
      </div>
      {depth === 1 && nodes.length > 1 && (
        <p className="text-xs text-fg-muted">
          {t("Groups are limited to three levels and 20 conditions.")}
        </p>
      )}
    </div>
  );
}
export function RuleDraftEditor({
  tenant,
  draft,
  change,
  guided = false,
}: {
  tenant: string;
  draft: RuleDraft;
  change: (draft: RuleDraft) => void;
  guided?: boolean;
}) {
  const sourceList = useId();
  const sources = useRead(() => sourceWorkspaceApi.systems(tenant, "", 1), [tenant]);
  const set = (key: keyof RuleDraft, value: unknown) => change({ ...draft, [key]: value });
  const input = (label: string, key: keyof RuleDraft) => (
    <RuleField label={label}>
      <input
        className={control}
        list={key === "source_system" ? sourceList : undefined}
        value={String(draft[key] ?? "")}
        onChange={(e) => set(key, e.target.value)}
      />
    </RuleField>
  );
  return (
    <div className="space-y-5" data-guided-rule-editor>
      <datalist id={sourceList}>
        {sources.data?.items.map((source) => (
          <option key={source.id} value={source.code}>
            {source.name}
          </option>
        ))}
      </datalist>
      <section
        className="space-y-4 rounded-xl border border-border-default p-4"
        data-rule-step="when"
      >
        <h3 className="flex items-center gap-3 font-semibold">
          {!guided && (
            <span className="flex size-7 items-center justify-center rounded-full bg-accent-soft text-sm text-accent">
              1
            </span>
          )}
          {t("When does the rule apply?")}
        </h3>
        <div className="grid items-start gap-3 sm:grid-cols-2">
          {input("Source", "source_system")}
          {input("Record type", "source_type")}
        </div>
        {guided && (
          <p className="text-sm text-fg-muted">
            {t(
              "Without conditions, the rule applies to every matching source type. Add a condition to limit it, for example to a stated priority flag.",
            )}
          </p>
        )}
        <Conditions
          mode={draft.conditions_mode}
          nodes={draft.conditions}
          change={(conditions_mode, conditions) =>
            change({ ...draft, conditions_mode, conditions })
          }
        />
      </section>
      <section
        className="space-y-4 rounded-xl border border-border-default p-4"
        data-rule-step="remember"
      >
        <h3 className="flex items-center gap-3 font-semibold">
          {!guided && (
            <span className="flex size-7 items-center justify-center rounded-full bg-accent-soft text-sm text-accent">
              2
            </span>
          )}
          {t("What should be remembered?")}
        </h3>
        <div className="grid items-start gap-3 sm:grid-cols-2">
          <div className="space-y-2">
            {input("Characteristic", "predicate")}
            {guided && (
              <p className="text-xs text-fg-muted">
                {t(
                  "Give this property a stable name, for example order.delivery_instruction. This labels the observation; it does not change the order.",
                )}
              </p>
            )}
          </div>
          <RuleField label="Value comes from">
            <select
              className={control}
              value={draft.output_mode}
              onChange={(e) => set("output_mode", e.target.value)}
            >
              <option value="source_path">{t("Read a source field")}</option>
              <option value="constant">{t("Use a fixed value")}</option>
            </select>
          </RuleField>
          {draft.output_mode === "source_path" ? (
            input("Source field", "output_path")
          ) : (
            <RuleField label="Value">
              {draft.value_type === "boolean" ? (
                <select
                  className={control}
                  value={String(draft.constant_value).toLowerCase()}
                  onChange={(e) => set("constant_value", e.target.value)}
                >
                  <option value="">{t("Choose a value")}</option>
                  <option value="true">{t("Yes")}</option>
                  <option value="false">{t("No")}</option>
                </select>
              ) : (
                <input
                  className={control}
                  value={String(draft.constant_value ?? "")}
                  onChange={(e) => set("constant_value", e.target.value)}
                />
              )}
            </RuleField>
          )}
          <RuleField label="Applies to">
            <select
              className={control}
              value={draft.subject_resolver}
              onChange={(e) => set("subject_resolver", e.target.value)}
            >
              <option value="source_document_commitments">{t("Delivery commitment")}</option>
              <option value="source_document_lines">{t("Each matching order line")}</option>
            </select>
          </RuleField>
        </div>
        {guided && (
          <p className="text-sm text-fg-muted">
            {t(
              "The source field and value type come from your example. The rule must link to an existing delivery commitment or order line. Line mapping and other options are under Advanced settings.",
            )}
          </p>
        )}
        <details data-rule-advanced>
          <summary className="cursor-pointer text-sm text-fg-muted">
            {t("Advanced settings")}
          </summary>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {input("Rule name", "logical_name")}
            <RuleField label="Value type">
              <select
                className={control}
                value={draft.value_type}
                onChange={(e) => set("value_type", e.target.value)}
              >
                {valueTypes.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </RuleField>
            <RuleField label="Output scope">
              <select
                className={control}
                value={draft.output_scope}
                onChange={(e) => set("output_scope", e.target.value)}
              >
                <option value="source">{t("Whole source")}</option>
                <option value="element">{t("Current line")}</option>
              </select>
            </RuleField>
            {draft.subject_resolver === "source_document_lines" && (
              <>
                {input("Iteration path", "iteration_path")}
                {input("Source line ID path", "source_line_id_path")}
              </>
            )}
            <RuleField label="Allowed values (comma-separated)">
              <input
                className={control}
                value={draft.allowed_values.join(",")}
                onChange={(e) =>
                  set("allowed_values", e.target.value ? e.target.value.split(",") : [])
                }
              />
            </RuleField>
            <RuleField label="Observation time">
              <select
                className={control}
                value={draft.observed_at_mode}
                onChange={(e) => set("observed_at_mode", e.target.value)}
              >
                <option value="source_received_at">{t("When the source was received")}</option>
                <option value="source_path">{t("Read a source field")}</option>
              </select>
            </RuleField>
            {draft.observed_at_mode === "source_path" &&
              input("Observation time path", "observed_at_path")}
          </div>
        </details>
      </section>
    </div>
  );
}

export function RuleDefinition({ draft }: { draft: RuleDraft }) {
  const condition = (n: RealityGapCondition): string =>
    "mode" in n
      ? `(${n.conditions.map(condition).join(n.mode === "all" ? ` ${t("All conditions")} ` : ` ${t("Any condition")} `)})`
      : `${t(n.scope === "element" ? "Current line" : "Whole source")}: ${n.path} ${t(operators[n.operator as keyof typeof operators] || n.operator)} ${operandText(n.operand)}`;
  return (
    <dl
      className="grid min-w-0 gap-3 rounded-lg bg-surface-muted p-4 text-sm sm:grid-cols-2"
      data-rule-definition
    >
      {[
        ["Rule name", draft.logical_name],
        ["Source", `${draft.source_system} · ${draft.source_type}`],
        ["Value type", draft.value_type],
        ["Output scope", t(draft.output_scope === "element" ? "Current line" : "Whole source")],
        ...(draft.subject_resolver === "source_document_lines"
          ? [
              ["Iteration path", draft.iteration_path],
              ["Source line ID path", draft.source_line_id_path],
            ]
          : []),
        ...(draft.allowed_values.length
          ? [["Allowed values (comma-separated)", draft.allowed_values.join(", ")]]
          : []),
        [
          "Apply the Fact to",
          t(
            draft.subject_resolver === "source_document_lines"
              ? "Each matching order line"
              : "The order commitment",
          ),
        ],
        [
          "Fact",
          `${draft.predicate} = ${draft.output_mode === "constant" ? operandText(draft.constant_value) : draft.output_path || draft.value_path}`,
        ],
        [
          "Conditions",
          draft.conditions.length
            ? draft.conditions
                .map(condition)
                .join(
                  draft.conditions_mode === "all"
                    ? ` ${t("All conditions")} `
                    : ` ${t("Any condition")} `,
                )
            : t("All sources matching the source type"),
        ],
        [
          "Observation time",
          draft.observed_at_mode === "source_path"
            ? draft.observed_at_path
            : t("When the source was received"),
        ],
      ].map(([label, value]) => (
        <div key={label}>
          <dt className="text-xs text-fg-muted">{t(label!)}</dt>
          <dd className="mt-1 whitespace-pre-wrap break-words" data-localization="original">
            {value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

import { useState } from "react";
import {
  storylineApi,
  type StorylineDelta,
  type StorylineToolReference,
  type StorylineTraceItem,
} from "../api";
import { formatDateTime, t } from "../localization";
import { languageHref, readLanguage } from "../../../shared/language";
import { pickText, recordRoute } from "./storylineState";
import type { Selection } from "./routing";

const panel = "rounded-xl border border-border-default bg-surface";
const accessClass: Record<string, string> = {
  read: "bg-surface-muted text-fg-muted",
  propose: "bg-accent-soft text-accent",
  confirm: "bg-positive-bg text-positive-text",
};

function docsUrl(path: string): string {
  const base = (typeof __DOCS_URL__ === "string" ? __DOCS_URL__ : "").replace(/\/+$/, "");
  return languageHref(`${base}${path}`, readLanguage() ?? "en", true);
}

function Json({ value }: { value: unknown }) {
  if (value === null || value === undefined) return null;
  return (
    <pre
      className="max-h-48 overflow-auto whitespace-pre-wrap break-all rounded-md bg-surface-sunken p-2 font-mono text-[11.5px] leading-snug text-fg-default"
      data-localization="original"
    >
      {JSON.stringify(value, null, 1)}
    </pre>
  );
}

function TraceEntry({
  tenant,
  item,
  onPick,
  picked,
}: {
  tenant: string;
  item: StorylineTraceItem;
  onPick?: (item: StorylineTraceItem) => void;
  picked?: boolean;
}) {
  const [reference, setReference] = useState<StorylineToolReference | null | "loading">(null);
  const name = item.kind === "view" ? `view:${item.name}` : item.name;
  const load = async () => {
    if (reference) return;
    setReference("loading");
    try {
      setReference(
        await storylineApi.toolReference(
          tenant,
          item.kind === "view" ? "view:" + viewKey(item.name) : item.name,
        ),
      );
    } catch {
      setReference(null);
    }
  };
  return (
    <details
      className="overflow-hidden bg-surface"
      data-storyline-call={item.kind}
      data-storyline-ordinal={item.ordinal}
      data-picked={picked ? "true" : undefined}
      onToggle={(event) => {
        if ((event.currentTarget as HTMLDetailsElement).open) void load();
      }}
    >
      <summary className="grid cursor-pointer grid-cols-[58px_1fr_auto] items-center gap-2 px-2.5 py-1.5 hover:bg-surface-sunken">
        <span
          className={`rounded px-1.5 py-0.5 text-center text-[10px] font-semibold uppercase tracking-wider ${accessClass[item.access] || accessClass.read}`}
        >
          {item.kind === "error" ? t("error") : item.access}
        </span>
        <span
          className="truncate font-mono text-[12.5px] text-fg-strong"
          data-localization="original"
        >
          {name}
          <span className="ml-1.5 font-sans text-[11px] text-fg-muted">
            {actorLabel(item.actor)}
          </span>
        </span>
        <span className="font-mono text-[11px] text-fg-quiet">
          {item.duration_ms !== null ? `${item.duration_ms} ms` : ""}
        </span>
      </summary>
      <div className="grid gap-2 border-t border-border-subtle bg-surface-sunken/60 px-2.5 py-2">
        {onPick && item.marker && (
          <button
            type="button"
            className="br-btn justify-self-start"
            data-storyline-action="pick-call"
            aria-pressed={picked}
            onClick={() => onPick(item)}
          >
            {t("What it added")}
          </button>
        )}
        {item.input !== null && item.input !== undefined && (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-fg-muted">
              {t("Input")}
            </p>
            <Json value={item.input} />
          </div>
        )}
        {item.result !== null && item.result !== undefined && (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-fg-muted">
              {item.kind === "error" ? t("Error") : t("Result")}
            </p>
            <Json value={item.result} />
          </div>
        )}
        {reference && reference !== "loading" && (
          <div
            className="grid gap-1 border-l-2 pl-2 text-[12.5px]"
            style={{ borderColor: "var(--lane-evidence)" }}
            data-storyline-reference
          >
            <p className="font-semibold text-fg-strong">
              {pickText(reference.label) || reference.key}
            </p>
            <p className="text-fg-muted" data-localization="original">
              {reference.description}
            </p>
            {reference.parameters && reference.parameters.length > 0 && (
              <ul className="list-disc pl-4 text-[12px] text-fg-muted">
                {reference.parameters.slice(0, 12).map((parameter) => (
                  <li key={parameter.name} data-localization="original">
                    <code>{parameter.name}</code>
                    {parameter.required ? " *" : ""}
                  </li>
                ))}
              </ul>
            )}
            {reference.projections && reference.projections.length > 0 && (
              <p className="text-fg-muted">
                {t("Writes to")}:{" "}
                <span data-localization="original">{reference.projections.join(", ")}</span>
              </p>
            )}
            <a
              className="text-accent underline-offset-2 hover:underline"
              href={docsUrl(reference.docs_path)}
              target="_blank"
              rel="noreferrer"
            >
              {t("Open in Tool Usage")}
            </a>
          </div>
        )}
      </div>
    </details>
  );
}

function viewKey(route: string): string {
  const last = route.split("/").filter(Boolean).pop() || route;
  return last.replaceAll("-", "_");
}

function actorLabel(actor: string): string {
  return actor === "storyline" ? t("story") : actor === "person" ? t("you") : actor;
}

export function StorylineProtocol({
  tenant,
  items,
  delta,
  loading,
  navigate,
  mode = "chapter",
  onPick,
  picked,
}: {
  tenant: string;
  items: StorylineTraceItem[];
  delta: StorylineDelta | null;
  loading: boolean;
  navigate: (changes: Partial<Selection>) => void;
  /** Free play lists the calls outside the story and lets one be picked (FR-011). */
  mode?: "chapter" | "free";
  onPick?: (item: StorylineTraceItem) => void;
  picked?: number | null;
}) {
  const open = (recordType: string, recordId: string) =>
    navigate(recordRoute(recordType, recordId));
  const heading = mode === "free" ? t("Calls outside the storyline") : t("Calls in this step");
  const emptyText =
    mode === "free"
      ? t("Nothing has been done outside the storyline yet.")
      : t("Nothing has been called for this step yet.");
  const deltaEmptyText =
    mode === "free"
      ? t("Pick a confirmed call to see what it added.")
      : t("Once you confirm, the events, facts, records and findings of this step appear here.");
  const valueOf = (value: unknown) =>
    typeof value === "object" ? JSON.stringify(value) : String(value);
  return (
    <div className={`${panel} flex min-w-0 flex-col`} data-storyline-protocol data-mode={mode}>
      <section className="flex flex-col gap-2 p-3" aria-label={heading}>
        <div className="flex items-baseline justify-between">
          <h3 className="text-[13px] font-semibold text-fg-strong">{heading}</h3>
          <span className="font-mono text-[11px] text-fg-quiet">
            {items.length} {t("calls")}
          </span>
        </div>
        {items.length === 0 ? (
          <p className="text-[12.5px] text-fg-quiet">{loading ? t("Loading…") : emptyText}</p>
        ) : (
          <div className="divide-y divide-border-subtle overflow-hidden rounded-lg border border-border-default">
            {items.map((item) => (
              <TraceEntry
                key={item.id}
                tenant={tenant}
                item={item}
                onPick={onPick}
                picked={picked != null && picked === item.ordinal}
              />
            ))}
          </div>
        )}
      </section>
      <section
        className="flex flex-col gap-2 border-t border-border-subtle p-3"
        aria-label={t("What was added")}
        data-storyline-delta
      >
        <div className="flex items-baseline justify-between">
          <h3 className="text-[13px] font-semibold text-fg-strong">{t("What was added")}</h3>
          {delta && (
            <span className="font-mono text-[11px] text-fg-quiet">
              #{delta.range.after_sequence + 1} … #{delta.range.latest_sequence}
            </span>
          )}
        </div>
        {!delta ? (
          <p className="text-[12.5px] text-fg-quiet">{deltaEmptyText}</p>
        ) : (
          <>
            <Group title={t("Events")} lane="var(--lane-events)" count={`+${delta.events.length}`}>
              {delta.events.map((event) => (
                <Row
                  key={event.id}
                  label={<code className="text-[11.5px]">{event.type}</code>}
                  detail={`#${event.sequence}`}
                  onClick={() => open(event.subject_type, event.subject_id)}
                />
              ))}
            </Group>
            <Group title={t("Facts")} lane="var(--lane-evidence)" count={`+${delta.facts.length}`}>
              {delta.facts.map((fact) => (
                <Row
                  key={fact.id}
                  label={
                    <>
                      <span data-localization="original">{fact.subject_type}</span>{" "}
                      <code className="text-[11.5px]">{fact.predicate}</code>
                    </>
                  }
                  detail={`= ${valueOf(fact.value)}`}
                  onClick={() => open("fact", fact.id)}
                />
              ))}
            </Group>
            <Group
              title={t("Records")}
              lane="var(--lane-reality)"
              count={`+${delta.records.length}`}
            >
              {delta.records.map((record) => (
                <Row
                  key={`${record.record_type}:${record.record_id}`}
                  label={<span data-localization="original">{record.record_type}</span>}
                  detail={record.record_id}
                  onClick={() => open(record.record_type, record.record_id)}
                />
              ))}
            </Group>
            <Group
              title={t("Findings")}
              lane="var(--caution-text)"
              count={`+${delta.exceptions.raised.length} / −${delta.exceptions.cleared.length}`}
            >
              {delta.exceptions.raised.map((finding) => (
                <Row
                  key={finding.id}
                  tone="raised"
                  label={`▲ ${pickText(finding.label) || finding.class_id}`}
                  detail={finding.impact || ""}
                  wrap
                  onClick={() =>
                    navigate({ route: "attention", exception: finding.id, q: "", page: 1 })
                  }
                />
              ))}
              {delta.exceptions.cleared.map((finding) => (
                <Row
                  key={finding.id}
                  tone="cleared"
                  label={pickText(finding.label) || finding.class_id}
                  detail="✓"
                  onClick={() => navigate({ route: "attention", q: finding.class_id, page: 1 })}
                />
              ))}
            </Group>
            {delta.graph.nodes.length > 0 && (
              <Group
                title={t("Context Graph")}
                lane="var(--lane-reference)"
                count={`${delta.graph.nodes.length}`}
              >
                <Graph graph={delta.graph} open={open} />
              </Group>
            )}
          </>
        )}
      </section>
      {delta && (
        <p className="border-t border-border-subtle px-3 py-2 text-[11px] text-fg-quiet">
          {t("Recorded")} {formatDateTime(delta.range.after_at || new Date().toISOString())}
        </p>
      )}
    </div>
  );
}

/** One frame per group: a header row, then rows divided by hairlines. */
function Group({
  title,
  lane,
  count,
  children,
}: {
  title: string;
  lane: string;
  count: string;
  children: React.ReactNode;
}) {
  const empty = Array.isArray(children) ? children.length === 0 : !children;
  if (empty) return null;
  return (
    <div className="overflow-hidden rounded-lg border border-border-default" data-storyline-group>
      <div className="flex items-center gap-2 bg-surface-sunken px-2.5 py-1.5 text-[12px] font-semibold text-fg-muted">
        <span className="size-2 shrink-0 rounded-sm" style={{ background: lane }} />
        {title}
        <span className="font-mono text-[11px] font-normal text-fg-quiet">{count}</span>
      </div>
      <div className="divide-y divide-border-subtle">{children}</div>
    </div>
  );
}

const toneClasses: Record<string, string> = {
  raised: "border-l-2 border-caution-text text-caution-text",
  cleared: "text-fg-muted line-through",
  plain: "",
};

function Row({
  label,
  detail,
  tone,
  wrap,
  onClick,
}: {
  label: React.ReactNode;
  detail: string;
  tone?: "raised" | "cleared";
  /** The detail takes a second line so the label keeps its room (findings). */
  wrap?: boolean;
  onClick: () => void;
}) {
  const toneClass = toneClasses[tone || "plain"];
  const detailNode = (
    <span
      className={`font-mono text-[11px] text-fg-muted ${wrap ? "whitespace-normal" : "truncate"}`}
      data-localization="original"
    >
      {detail}
    </span>
  );
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex w-full flex-col gap-0.5 px-2.5 py-1.5 text-left text-[12.5px] hover:bg-surface-muted ${toneClass}`}
    >
      {wrap ? (
        <>
          <span className="w-full">{label}</span>
          {detail && detailNode}
        </>
      ) : (
        <span className="grid w-full grid-cols-[1fr_auto] items-baseline gap-3">
          <span className="truncate">{label}</span>
          {detailNode}
        </span>
      )}
    </button>
  );
}

const strokeColors: Record<string, string> = { new: "var(--accent)", old: "var(--border-strong)" };
const nodeColors: Record<string, string> = {
  new: "var(--lane-reality)",
  old: "var(--lane-reference)",
};

function Graph({
  graph,
  open,
}: {
  graph: StorylineDelta["graph"];
  open: (recordType: string, recordId: string) => void;
}) {
  const nodes = graph.nodes.slice(0, 8);
  const width = 300;
  const positions = new Map(
    nodes.map((node, index) => [
      `${node.record_type}:${node.record_id}`,
      {
        x: 36 + (index % 4) * ((width - 72) / 3),
        y: 28 + Math.floor(index / 4) * 56,
      },
    ]),
  );
  const height = 28 + Math.ceil(nodes.length / 4) * 56 + 8;
  return (
    <figure className="px-2 pt-1.5 pb-1" data-storyline-graph>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="block h-auto w-full"
        role="img"
        aria-label={t("Context Graph")}
      >
        {graph.edges.map((edge, index) => {
          const from = positions.get(edge.from),
            to = positions.get(edge.to);
          if (!from || !to) return null;
          return (
            <line
              key={index}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke={strokeColors[edge.new ? "new" : "old"]}
              strokeWidth={edge.new ? 2 : 1.2}
              strokeDasharray={edge.new ? undefined : "3 3"}
            />
          );
        })}
        {nodes.map((node) => {
          const point = positions.get(`${node.record_type}:${node.record_id}`)!;
          return (
            <g
              key={`${node.record_type}:${node.record_id}`}
              className="cursor-pointer"
              onClick={() => open(node.record_type, node.record_id)}
            >
              <circle
                cx={point.x}
                cy={point.y}
                r={node.primary ? 8 : 6}
                fill={nodeColors[node.new ? "new" : "old"]}
                stroke="var(--surface)"
                strokeWidth={2}
              />
              <text
                x={point.x}
                y={point.y + 20}
                textAnchor="middle"
                fontSize="10"
                fontFamily="var(--font-mono, monospace)"
                fill="var(--text-secondary)"
              >
                {node.record_type}
              </text>
            </g>
          );
        })}
      </svg>
      <figcaption className="px-1 pb-1 text-[11px] text-fg-muted">
        {t("Context Graph")} · {t("solid lines are new links")}
      </figcaption>
    </figure>
  );
}

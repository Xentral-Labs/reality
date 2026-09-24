import { inspectorRowText, inspectorValue } from "./inspectorFormat";
import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { t } from "../localization";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { Inspector } from "./Inspector";
import { connectionTraceLayout } from "./connectionTraceLayout";
export type GraphTarget = { kind: string; id: string };
export function ObjectGraph({
  tenant,
  root,
  onNavigate,
  variant = "standard",
}: {
  tenant: string;
  root: GraphTarget;
  onNavigate?: (target: GraphTarget) => void;
  variant?: "standard" | "trace";
}) {
  const container = useRef<HTMLElement>(null);
  const [width, setWidth] = useState(760);
  useEffect(() => {
    const element = container.current!;
    const resize = () =>
      setWidth(Math.max(280, Math.min(variant === "trace" ? 900 : 760, element.clientWidth - 34)));
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(element);
    return () => observer.disconnect();
  }, [variant]);
  const [target, setTarget] = useState(root);
  const [history, setHistory] = useState<GraphTarget[]>([]);
  const [inspect, setInspect] = useState(false);
  const [zoom, setZoom] = useState(1);
  const read = useRead(
    () => api.inspector(tenant, target.kind, target.id),
    [tenant, target.kind, target.id],
  );
  const linkRows =
    read.data?.sections.flatMap((section) =>
      section.rows.filter((row) => row.link).map((row) => ({ ...row, section: section.title })),
    ) || [];
  const links = [
    ...new Map(linkRows.map((row) => [`${row.link!.kind}:${row.link!.id}`, row])).values(),
  ];
  const shown = links.slice(0, 20);
  const stacked = width < 640;
  const height = stacked
    ? Math.max(200, 140 + shown.length * 120)
    : Math.max(200, shown.length * 90);
  const rootX = stacked ? (width - 225) / 2 : 5;
  const rootY = stacked ? 10 : height / 2 - 40;
  const nodeX = stacked ? (width - 260) / 2 : width - 270;
  const nodeY = (index: number) => (stacked ? 150 + index * 120 : index * 90 + 5);
  const trace = connectionTraceLayout(
    shown.map((row) => row.link!.kind),
    width,
  );
  const graphColor = (kind: string) => {
    const lane = ["party", "item", "location"].includes(kind)
      ? "reference"
      : kind === "source_record"
        ? "source"
        : ["document", "document_line"].includes(kind)
          ? "evidence"
          : kind === "business_event"
            ? "events"
            : "reality";
    return `var(--lane-${lane})`;
  };
  return (
    <section
      ref={container}
      className={`min-w-0 rounded-xl border border-border-default bg-surface ${variant === "trace" ? "p-3" : "p-4"}`}
    >
      <div className="flex flex-wrap items-center gap-2">
        {history.length > 0 && (
          <button
            className="br-btn"
            onClick={() => {
              setTarget(history[history.length - 1]);
              onNavigate?.(history[history.length - 1]);
              setHistory(history.slice(0, -1));
            }}
          >
            {t("Back")}
          </button>
        )}
        {variant === "standard" && (
          <button className="br-btn" onClick={() => setInspect(true)}>
            {t("Inspect")}
          </button>
        )}
        <button
          className="br-btn"
          aria-label={t("Zoom out")}
          onClick={() => setZoom(Math.max(0.5, zoom - 0.25))}
        >
          −
        </button>
        <button
          className="br-btn"
          aria-label={t("Zoom in")}
          onClick={() => setZoom(Math.min(2, zoom + 0.25))}
        >
          +
        </button>
        <span className="text-xs text-fg-muted" data-compact-caption={variant === "trace"}>
          {t("Direct links from the selected record. Open a node to continue.")}
        </span>
      </div>
      {!read.data || read.data.id !== target.id || read.data.kind !== target.kind ? (
        <ReadState loading={read.loading} error={read.error} retry={read.refresh} />
      ) : (
        <>
          {(links.length > 20 ||
            read.data.coverage?.movements_has_more ||
            read.data.coverage?.reservations_has_more) && (
            <p className="my-3 text-sm text-caution-text">
              {t("More records are available in the workspace.")}
            </p>
          )}
          {variant === "trace" ? (
            <div
              className="mt-3 overflow-auto rounded-xl border border-border-default bg-surface-muted/40"
              data-object-graph
              data-connection-trace
            >
              <svg
                width={trace.width * zoom}
                height={trace.height * zoom}
                viewBox={`0 0 ${trace.width} ${trace.height}`}
                role="group"
                aria-label={t("Relationship trace")}
              >
                <text x="24" y="26" fill="var(--color-fg-muted)" fontSize="11">
                  {t("Evidence and origin")}
                </text>
                <text
                  x={trace.width - 24}
                  y="26"
                  fill="var(--color-fg-muted)"
                  fontSize="11"
                  textAnchor="end"
                >
                  {t("Operational consequences")}
                </text>
                {shown.map((row, index) => {
                  const position = trace.nodes[index];
                  const fromX =
                    position.side === "left"
                      ? position.x + trace.nodeWidth
                      : trace.root.x + trace.nodeWidth;
                  const toX = position.side === "left" ? trace.root.x : position.x;
                  const fromY =
                    position.side === "left"
                      ? position.y + trace.nodeHeight / 2
                      : trace.root.y + trace.nodeHeight / 2;
                  const toY =
                    position.side === "left"
                      ? trace.root.y + trace.nodeHeight / 2
                      : position.y + trace.nodeHeight / 2;
                  return (
                    <g key={`edge:${row.link!.kind}:${row.link!.id}:${index}`}>
                      <path
                        d={`M ${fromX} ${fromY} C ${(fromX + toX) / 2} ${fromY}, ${(fromX + toX) / 2} ${toY}, ${toX} ${toY}`}
                        stroke={graphColor(row.link!.kind)}
                        strokeWidth="1.5"
                        opacity="0.45"
                        fill="none"
                      />
                    </g>
                  );
                })}
                {shown.map((row, index) => {
                  const position = trace.nodes[index];
                  return (
                    <g
                      key={`${row.link!.kind}:${row.link!.id}:${index}`}
                      data-trace-side={position.side}
                      className="transition-transform duration-500 motion-reduce:transition-none"
                      style={{ transform: `translate(${position.x}px, ${position.y}px)` }}
                    >
                      <foreignObject width={trace.nodeWidth} height={trace.nodeHeight}>
                        <button
                          className="flex h-full w-full flex-col justify-center rounded-lg border-2 bg-surface px-3 text-left text-[10px] shadow-sm transition hover:border-accent hover:bg-accent-soft focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent motion-reduce:transition-none"
                          style={{ borderColor: graphColor(row.link!.kind) }}
                          onClick={() => {
                            setHistory([...history, target]);
                            setTarget(row.link!);
                            onNavigate?.(row.link!);
                          }}
                          title={`${t(row.label)} · ${inspectorRowText(row)}`}
                        >
                          <strong
                            className="block max-w-full truncate"
                            data-localization="original"
                          >
                            {row.link!.kind}
                          </strong>
                          <span
                            className="mt-1 block max-w-full truncate text-fg-muted"
                            data-localization="original"
                          >
                            {inspectorRowText(row)}
                          </span>
                        </button>
                      </foreignObject>
                    </g>
                  );
                })}
                <g
                  className="transition-transform duration-500 motion-reduce:transition-none"
                  style={{
                    transform: `translate(${trace.root.x}px, ${trace.root.y}px)`,
                  }}
                >
                  <foreignObject width={trace.nodeWidth} height={trace.nodeHeight}>
                    <button
                      className="flex h-full w-full flex-col justify-center rounded-lg border-2 border-accent bg-accent-soft px-3 text-left text-[10px] shadow-md"
                      onClick={() => setInspect(true)}
                    >
                      <strong className="block max-w-full truncate" data-localization="original">
                        {inspectorValue(read.data.title, read.data.title_parts)}
                      </strong>
                      <span
                        className="mt-1 block max-w-full truncate text-fg-muted"
                        data-localization="original"
                      >
                        {target.kind}
                      </span>
                    </button>
                  </foreignObject>
                </g>
              </svg>
            </div>
          ) : (
            <div className="mt-3 max-h-[600px] overflow-auto" data-object-graph>
              <svg
                width={width * zoom}
                height={height * zoom}
                viewBox={`0 0 ${width} ${height}`}
                role="group"
                aria-label={t("Record graph")}
              >
                {shown.map((row, i) => (
                  <g key={`${row.link!.kind}:${row.link!.id}:${i}`}>
                    <path
                      d={
                        stacked
                          ? `M ${rootX} ${rootY + 40} H 10 V ${nodeY(i) + 39} H ${nodeX}`
                          : `M 230 ${height / 2} C ${(230 + nodeX) / 2} ${height / 2}, ${(230 + nodeX) / 2} ${nodeY(i) + 39}, ${nodeX} ${nodeY(i) + 39}`
                      }
                      stroke="var(--color-border-strong)"
                      fill="none"
                    />
                    <text
                      x={stacked ? nodeX : (230 + nodeX) / 2 - 50}
                      y={stacked ? nodeY(i) - 8 : nodeY(i) + 27}
                      fill="var(--color-fg-muted)"
                      fontSize="11"
                    >
                      {t(row.label).slice(0, stacked ? 36 : 24)}
                    </text>
                    <foreignObject x={nodeX} y={nodeY(i)} width="260" height="78">
                      <button
                        className="h-full w-full rounded-lg border border-border-default bg-surface-muted px-3 text-left text-xs hover:border-accent"
                        onClick={() => {
                          setHistory([...history, target]);
                          setTarget(row.link!);
                          onNavigate?.(row.link!);
                        }}
                      >
                        <span className="block font-semibold" data-localization="original">
                          {row.link!.kind}
                        </span>
                        <span className="block truncate" data-localization="original">
                          {inspectorRowText(row)}
                        </span>
                        <span className="block truncate text-fg-muted" data-localization="original">
                          {row.link!.id}
                        </span>
                      </button>
                    </foreignObject>
                  </g>
                ))}
                <foreignObject x={rootX} y={rootY} width="225" height="80">
                  <button
                    className="h-full w-full rounded-lg border border-accent bg-accent-soft px-3 text-left text-sm"
                    onClick={() => setInspect(true)}
                  >
                    <strong className="block truncate" data-localization="original">
                      {inspectorValue(read.data.title, read.data.title_parts)}
                    </strong>
                    <span className="block truncate text-xs" data-localization="original">
                      {target.kind} · {target.id}
                    </span>
                  </button>
                </foreignObject>
              </svg>
            </div>
          )}
          {!shown.length && (
            <p className="mt-3 text-sm text-fg-muted">{t("No linked records returned.")}</p>
          )}
        </>
      )}
      {inspect && <Inspector tenant={tenant} target={target} close={() => setInspect(false)} />}
    </section>
  );
}

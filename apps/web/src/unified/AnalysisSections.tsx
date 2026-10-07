import { useId, type ReactNode, type Ref } from "react";

export function AnalysisMetricGroup({
  title,
  period,
  children,
}: {
  title: ReactNode;
  period: string;
  children: ReactNode;
}) {
  const id = useId();
  return (
    <section className="cockpit-metric-group" data-metric-period={period} aria-labelledby={id}>
      <h3 id={id}>{title}</h3>
      {children}
    </section>
  );
}

export function AnalysisPlot({
  title,
  kind,
  plotRef,
  className = "",
  children,
}: {
  title: ReactNode;
  kind: string;
  plotRef?: Ref<HTMLElement>;
  className?: string;
  children: ReactNode;
}) {
  const id = useId();
  return (
    <figure
      className={`cockpit-analysis-plot ${className}`}
      ref={plotRef}
      data-analysis-kind={kind}
      aria-labelledby={id}
    >
      <figcaption>
        <h4 id={id}>{title}</h4>
      </figcaption>
      {children}
    </figure>
  );
}

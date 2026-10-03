import { useEffect, useRef, useState } from "react";
import {
  sourceExcerpt,
  type LogicSource,
  type SourceRange,
} from "../../../shared/businessBlueprint";
import { currentLanguage } from "../localization";

export function SourceEvidence({ source, ranges }: { source: LogicSource; ranges: SourceRange[] }) {
  const [full, setFull] = useState(false);
  const code = useRef<HTMLPreElement>(null);
  const excerpt = sourceExcerpt(source, ranges, full);
  const phrase = (en: string, de: string) => (currentLanguage() === "de" ? de : en);
  useEffect(() => {
    const panel = code.current;
    const target = panel?.querySelector<HTMLElement>("[data-source-highlight]");
    if (full && panel && target)
      panel.scrollTop = Math.max(
        0,
        target.getBoundingClientRect().top -
          panel.getBoundingClientRect().top +
          panel.scrollTop -
          40,
      );
  }, [full, source.id]);
  return (
    <div className="mt-3 min-w-0" data-localization="original">
      <p className="break-all text-xs">
        {source.path} · {source.function}
      </p>
      <p className="my-2 text-xs text-fg-muted">
        {excerpt.focusAvailable
          ? phrase(
              "Highlighted lines identify the cited code location.",
              "Markierte Zeilen zeigen die zitierte Quellstelle.",
            )
          : phrase(
              "No exact line reference is available for this source.",
              "Für diesen Quelltext liegt kein genauer Zeilenverweis vor.",
            )}
      </p>
      <button
        type="button"
        className="br-btn mb-2 text-xs"
        aria-pressed={full}
        onClick={() => setFull(!full)}
      >
        {full
          ? phrase("Show excerpt", "Ausschnitt anzeigen")
          : phrase("Full function", "Ganze Funktion anzeigen")}
      </button>
      <pre
        ref={code}
        className="relative max-h-80 overflow-auto rounded-md border border-border-default bg-surface-subtle py-2 text-xs leading-relaxed"
        aria-label={phrase(
          "Source code with referenced lines highlighted",
          "Quellcode mit markierten Bezugszeilen",
        )}
      >
        <code>
          {excerpt.lines.map((line) => (
            <span
              key={line.number}
              className="flex min-w-max border-l-4 border-transparent data-[source-highlight]:bg-indigo-100 data-[source-highlight]:border-indigo-500 dark:data-[source-highlight]:bg-indigo-950"
              data-source-highlight={line.highlighted ? "" : undefined}
            >
              <span
                className="w-14 shrink-0 select-none px-3 text-right text-fg-muted"
                aria-hidden="true"
              >
                {line.number}
              </span>
              <span className="whitespace-pre pr-3">{line.text || " "}</span>
            </span>
          ))}
        </code>
      </pre>
    </div>
  );
}

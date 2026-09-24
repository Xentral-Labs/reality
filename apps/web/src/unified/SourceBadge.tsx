import { ExternalLink } from "lucide-react";
import { t } from "../localization";
import type { DecisionAttribution } from "./decisionTrail";

export type RecordOrigin =
  | { kind: "application"; actor?: string; decision?: DecisionAttribution }
  | {
      kind: "source";
      system_code: string;
      system_name: string;
      source_type: string;
      external_id: string;
      source_version: number;
      received_at: string | null;
      source_record_id: string;
      superseded: boolean;
      url: string | null;
    };

function host(url: string): string {
  try {
    return new URL(url).host;
  } catch {
    return url;
  }
}

/** Where one record came from. Never renders empty: a record with no source says so. */
export function SourceBadge({
  origin,
  inspect,
  showLink = true,
}: {
  origin?: RecordOrigin | null;
  inspect?: (target: { kind: string; id: string }) => void;
  showLink?: boolean;
}) {
  if (!origin || origin.kind === "application")
    return (
      <span className="text-fg-muted" data-source-origin="application">
        {origin?.kind === "application" && origin.actor
          ? `${t("Created here")} · ${origin.actor}`
          : t("Created here")}
      </span>
    );
  const reference = origin.external_id || origin.source_record_id;
  // Real external references are not short: demo intake carries a scheduler run
  // identity of seventy characters. Bound the rendered width and keep the exact
  // value in the title, so a register row stays one line and nothing is lost.
  const label = `${origin.system_name} · ${reference}`;
  return (
    <span
      className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1"
      data-source-origin="source"
      data-source-system={origin.system_code}
    >
      {inspect ? (
        <button
          type="button"
          className="block max-w-full truncate text-left underline decoration-dotted underline-offset-2 hover:text-fg-strong"
          data-action-meaning="navigate"
          data-source-reference={reference}
          onClick={() => inspect({ kind: "source_record", id: origin.source_record_id })}
          title={`${t("Show the original source")} · ${label}`}
        >
          {label}
        </button>
      ) : (
        <span className="block max-w-full truncate" title={label}>
          {label}
        </span>
      )}
      {origin.superseded && (
        <span className="text-fg-muted" data-source-superseded>
          {t("A newer source version exists")}
        </span>
      )}
      {showLink && origin.url && (
        <a
          className="inline-flex items-center gap-1 text-fg-muted hover:text-fg-strong"
          href={origin.url}
          target="_blank"
          rel="noopener noreferrer"
          data-source-link={host(origin.url)}
          title={`${t("Open in source system")} · ${host(origin.url)}`}
        >
          <ExternalLink size={13} aria-hidden />
          <span className="sr-only">{`${t("Open in source system")} · ${host(origin.url)}`}</span>
        </a>
      )}
    </span>
  );
}

/** Disclosed only where a record's observations came from more than one system. */
export function ContributingSystems({ systems }: { systems?: string[] | null }) {
  if (!systems || systems.length < 2) return null;
  return (
    <p className="mt-2 text-fg-muted" data-contributing-systems={systems.length}>
      {`${t("Several systems contributed to this record")}: ${systems.join(", ")}`}
    </p>
  );
}

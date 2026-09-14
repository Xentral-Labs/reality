import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { ArrowRight, ChevronDown, ChevronRight, ListFilter, Pencil, Play } from "lucide-react";
import { api } from "../api";
import { t } from "../localization";
import { Inspector, InspectorContent } from "./Inspector";
import { ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";

export type ActionMeaning = "navigate" | "filter" | "edit" | "work";

export function ActionIcon({ meaning }: { meaning: ActionMeaning }) {
  return meaning === "filter" ? (
    <ListFilter size={15} aria-hidden="true" />
  ) : meaning === "edit" ? (
    <Pencil size={15} aria-hidden="true" />
  ) : meaning === "work" ? (
    <Play size={15} aria-hidden="true" />
  ) : (
    <ArrowRight size={15} aria-hidden="true" />
  );
}

export function PreviewButton({
  open,
  toggle,
  controls,
  label,
}: {
  open: boolean;
  toggle: () => void;
  controls: string;
  label: string;
}) {
  const ref = useRef<HTMLButtonElement>(null);
  const wasOpen = useRef(open);
  useEffect(() => {
    if (wasOpen.current && !open) ref.current?.focus({ preventScroll: true });
    wasOpen.current = open;
  }, [open]);
  return (
    <button
      ref={ref}
      type="button"
      className="erp-preview-trigger"
      data-action-meaning="preview"
      aria-expanded={open}
      aria-controls={controls}
      aria-label={`${t(open ? "Close preview" : "Preview")} · ${label}`}
      title={t(open ? "Close preview" : "Preview")}
      onClick={toggle}
    >
      {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
      <span className="sr-only">{t(open ? "Close preview" : "Preview")}</span>
    </button>
  );
}

export function WorkPreview({
  id,
  open,
  children,
}: {
  id: string;
  open: boolean;
  children: ReactNode;
}) {
  if (!open) return null;
  return (
    <div
      id={id}
      role="region"
      className="border-b border-border-default bg-surface-muted/60 px-5 py-5"
    >
      {children}
    </div>
  );
}

export function TablePreview({
  id,
  open,
  columns,
  children,
}: {
  id: string;
  open: boolean;
  columns: number;
  children: ReactNode;
}) {
  if (!open) return null;
  return (
    <tr data-inline-preview>
      <td colSpan={columns} className="bg-surface-muted/60 p-0">
        <div id={id} role="region" className="p-5 sm:p-6">
          {children}
        </div>
      </td>
    </tr>
  );
}

export function InlineInspector({
  tenant,
  target,
  openFull,
  children,
}: {
  tenant: string;
  target: { kind: string; id: string };
  openFull?: () => void;
  children?: ReactNode;
}) {
  const [full, setFull] = useState(false);
  const read = useRead(
    () => api.inspector(tenant, target.kind, target.id),
    [tenant, target.kind, target.id],
  );
  const generated = useId();
  if (!read.data)
    return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  return (
    <div data-inline-inspector={generated} className="w-full">
      <InspectorContent data={read.data} selectedKind={target.kind} compact />
      <div className="mt-5 flex flex-wrap justify-end gap-2">
        <button className="br-btn" onClick={openFull || (() => setFull(true))}>
          {t("Open full explanation")}
        </button>
        {children}
      </div>
      {full && <Inspector tenant={tenant} target={target} close={() => setFull(false)} />}
    </div>
  );
}

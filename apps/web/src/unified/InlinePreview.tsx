import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { ArrowRight, ChevronDown, ChevronRight, ListFilter, Pencil, Play } from "lucide-react";
import { recordOpened } from "./usePaletteHistory";
import { api, type InspectorData } from "../api";
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
        <div
          id={id}
          role="region"
          className="record-preview-content sticky left-0 max-w-[100cqw] p-5 sm:p-6"
        >
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
  reveal = false,
  supplement,
  followActions,
  children,
}: {
  tenant: string;
  target: { kind: string; id: string };
  openFull?: () => void;
  reveal?: boolean;
  supplement?: (detail: InspectorData) => ReactNode;
  followActions?: (target: { kind: string; id: string }, close: () => void) => ReactNode;
  children?: ReactNode;
}) {
  const [full, setFull] = useState<{ kind: string; id: string } | null>(null);
  const read = useRead(
    () =>
      api
        .inspector(tenant, target.kind, target.id, true)
        .then((data) => ({ data, kind: target.kind, id: target.id })),
    [tenant, target.kind, target.id],
  );
  const detail =
    read.data?.kind === target.kind && read.data?.id === target.id ? read.data.data : undefined;
  useEffect(() => {
    if (detail && !read.loading && !read.error) recordOpened(tenant, target.kind, target.id);
  }, [read.data, read.loading, read.error, tenant, target.kind, target.id]);
  const content = useRef<HTMLDivElement>(null);
  const ready = !!detail;
  useEffect(() => {
    if (reveal && ready) content.current?.scrollIntoView({ block: "start", behavior: "instant" });
  }, [reveal, ready, target.id, target.kind]);
  const generated = useId();
  if (!detail) return <ReadState loading={read.loading} error={read.error} retry={read.refresh} />;
  return (
    <div
      ref={content}
      data-inline-inspector={generated}
      className="w-full max-w-[calc(100vw-5rem)] md:max-w-none"
    >
      <InspectorContent data={detail} selectedKind={target.kind} follow={setFull} compact />
      {supplement?.(detail)}
      <div className="mt-5 flex flex-wrap justify-end gap-2">
        <button className="br-btn" onClick={openFull || (() => setFull(target))}>
          {t("Open full explanation")}
        </button>
        {children}
      </div>
      {full && (
        <Inspector
          tenant={tenant}
          target={full}
          close={() => setFull(null)}
          actions={followActions ? (shown) => followActions(shown, () => setFull(null)) : undefined}
        />
      )}
    </div>
  );
}

import { PageCount } from "./PageHeading";
import { PageActionBar, type PageAction } from "./PageActionBar";
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { ChevronDown, ChevronRight, Search, X } from "lucide-react";
import type { Page, ProjectionMetadata } from "../api";
import { formatNumber, t } from "../localization";
import { mergeWorkRows } from "./workRows";

export function useWorkList<T extends { id: string }>(
  identity: string,
  load: (page: number) => Promise<{ items: T[]; page: Page; metadata?: ProjectionMetadata }>,
) {
  const loader = useRef(load);
  loader.current = load;
  const [revision, setRevision] = useState(0);
  const [requested, setRequested] = useState({ identity, page: 1 });
  const number = requested.identity === identity ? requested.page : 1;
  const [state, setState] = useState<{
    identity: string;
    items: T[];
    page?: Page;
    /** Freshness of the stored generation the rows came from, when the read is stored. */
    metadata?: ProjectionMetadata;
    loading: boolean;
    error?: string;
  }>({ identity, items: [], loading: true });
  useEffect(() => {
    let current = true;
    if (requested.identity !== identity) setRequested({ identity, page: 1 });
    setState((old) => ({
      identity,
      items: old.identity === identity ? old.items : [],
      page: old.identity === identity ? old.page : undefined,
      metadata: old.identity === identity ? old.metadata : undefined,
      loading: true,
    }));
    loader
      .current(number)
      .then((result) => {
        if (current)
          setState((old) => ({
            identity,
            items: mergeWorkRows(number === 1 ? [] : old.items, result.items),
            page: result.page,
            metadata: result.metadata,
            loading: false,
          }));
      })
      .catch((error) => {
        if (current) setState((old) => ({ ...old, loading: false, error: String(error.message) }));
      });
    return () => {
      current = false;
    };
  }, [identity, number, revision]);
  const refresh = () => {
    setRequested({ identity, page: 1 });
    setRevision((value) => value + 1);
  };
  useEffect(() => {
    const settled = () => {
      setRequested({ identity, page: 1 });
      setRevision((value) => value + 1);
    };
    window.addEventListener("reality:delivery-settled", settled);
    return () => window.removeEventListener("reality:delivery-settled", settled);
  }, [identity]);
  return {
    ...(state.identity === identity
      ? state
      : {
          items: [] as T[],
          loading: true,
          page: undefined,
          metadata: undefined,
          error: undefined,
        }),
    refresh,
    retry: () => setRevision((value) => value + 1),
    more: () => setRequested({ identity, page: (state.page?.number || 1) + 1 }),
  };
}
export function WorkHeader({
  title,
  total,
  actions = [],
}: {
  title: string;
  total?: number;
  actions?: PageAction[];
}) {
  return (
    <>
      <PageCount>
        {total !== undefined && (
          <span
            data-page-record-count
            className="rounded-full bg-surface-muted px-3 py-1 text-sm font-normal tabular-nums text-fg-muted"
          >
            {formatNumber(total)} <span className="sr-only">{t("open")}</span>
          </span>
        )}
      </PageCount>
      <PageActionBar actions={actions} />
    </>
  );
}
export function WorkSearch({
  value,
  change,
  label,
}: {
  value: string;
  change: (value: string) => void;
  label: string;
}) {
  const [draft, setDraft] = useState(value);
  const commit = useRef(change);
  commit.current = change;
  useEffect(() => setDraft(value), [value]);
  useEffect(() => {
    if (draft === value) return;
    const timeout = window.setTimeout(() => commit.current(draft), 300);
    return () => window.clearTimeout(timeout);
  }, [draft, value]);
  return (
    <label className="relative block min-w-0 flex-1">
      <Search size={16} className="pointer-events-none absolute left-3 top-3 text-fg-muted" />
      <span className="sr-only">{t(label)}</span>
      <input
        className="br-control w-full !pl-9"
        value={draft}
        maxLength={500}
        placeholder={t(label)}
        onChange={(event) => setDraft(event.target.value)}
      />
    </label>
  );
}
export function WorkRow({
  title,
  context,
  meta,
  icon,
  selected,
  open,
  previewId,
}: {
  title: ReactNode;
  context?: ReactNode;
  meta?: ReactNode;
  icon: ReactNode;
  selected?: boolean;
  open: () => void;
  previewId?: string;
}) {
  return (
    <button
      type="button"
      data-work-row
      aria-pressed={selected}
      aria-expanded={selected}
      aria-controls={previewId}
      onClick={open}
      className="work-row flex w-full items-center gap-3 text-left hover:bg-surface-muted focus-visible:relative focus-visible:z-10 aria-pressed:bg-accent-soft"
    >
      <span className="shrink-0 text-fg-muted">{icon}</span>
      <span className="work-row-content min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-fg-strong">{title}</span>
        {context && (
          <span className="work-row-context block truncate text-xs text-fg-muted">{context}</span>
        )}
      </span>
      <span className="work-row-meta text-right text-xs tabular-nums text-fg-muted">{meta}</span>
      {selected ? (
        <ChevronDown size={16} className="shrink-0 text-accent" />
      ) : (
        <ChevronRight size={16} className="shrink-0 text-fg-muted" />
      )}
    </button>
  );
}
export function WorkFooter({
  list,
}: {
  list: {
    items: unknown[];
    page?: Page;
    loading: boolean;
    error?: string;
    more: () => void;
    retry: () => void;
  };
}) {
  return (
    <div
      className="flex flex-wrap items-center justify-between gap-3 p-4 text-sm text-fg-muted"
      aria-live="polite"
    >
      <span>
        {list.page
          ? `${formatNumber(list.items.length)} / ${formatNumber(list.page.total)}`
          : t("Loading…")}
      </span>
      {list.error ? (
        <button className="br-btn" onClick={list.retry}>
          {t("Retry")}
        </button>
      ) : (
        list.page?.has_next && (
          <button className="br-btn" disabled={list.loading} onClick={list.more}>
            {t(list.loading ? "Loading…" : "Load more")}
          </button>
        )
      )}
      {list.error && (
        <p role="alert" className="basis-full">
          {t("Could not load this view")}
        </p>
      )}
    </div>
  );
}
export function WorkDrawer({
  title,
  close,
  children,
}: {
  title: string;
  close: () => void;
  children: ReactNode;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const previous = useRef(document.activeElement as HTMLElement);
  useLayoutEffect(() => {
    const node = dialog.current;
    node?.showModal();
    return () => {
      node?.close();
      previous.current?.focus({ preventScroll: true });
    };
  }, []);
  return (
    <dialog
      ref={dialog}
      aria-label={t(title)}
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
      className="fixed inset-y-0 left-auto right-0 m-0 h-dvh max-h-dvh w-full max-w-[660px] overflow-y-auto border-l border-border-default bg-surface p-5 text-fg-default shadow-xl backdrop:bg-black/20 sm:p-6"
    >
      <div className="mb-5 flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold">{t(title)}</h2>
        <button className="br-btn" aria-label={t("Close")} onClick={close}>
          <X size={18} />
        </button>
      </div>
      {children}
    </dialog>
  );
}

import { useEffect, useId, useRef, type ReactNode } from "react";
import { t } from "../localization";

// Match the native modal used by Company settings and operational entry dialogs.
export function SettingsDialog({
  title,
  description,
  busy = false,
  error,
  close,
  children,
}: {
  title: string;
  description?: string;
  busy?: boolean;
  error?: string;
  close: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const trigger = document.activeElement as HTMLElement | null;
    const node = ref.current!;
    node.showModal();
    node
      .querySelector<HTMLElement>(
        "input:not(:disabled), select:not(:disabled), textarea:not(:disabled)",
      )
      ?.focus();
    return () => {
      node.close();
      if (trigger?.isConnected) trigger.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      aria-busy={busy}
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) close();
      }}
      className="m-auto max-h-[90dvh] w-[min(760px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-6 text-fg-default backdrop:bg-black/30"
    >
      <header className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h2 id={titleId} className="text-xl font-semibold text-fg-strong">
            {title}
          </h2>
          {description && <p className="mt-2 text-sm text-fg-muted">{description}</p>}
        </div>
        <button type="button" className="br-btn" disabled={busy} onClick={close}>
          {t("Close")}
        </button>
      </header>
      {error && (
        <p role="alert" className="mb-4 rounded-lg border border-border-default p-3 text-sm">
          {error}
        </p>
      )}
      {children}
    </dialog>
  );
}
export function ReviewNotice({ open }: { open: () => void }) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg bg-surface-muted p-3 text-sm">
      <p>{t("A prepared change is waiting for your confirmation.")}</p>
      <button className="br-btn" onClick={open}>
        {t("Continue review")}
      </button>
    </div>
  );
}

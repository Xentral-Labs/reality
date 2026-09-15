import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { MoreHorizontal } from "lucide-react";
import { t } from "../localization";

export function HeaderControls({
  children,
  identity,
  indicator,
}: {
  children: ReactNode;
  identity: string;
  indicator?: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const id = useId();
  useEffect(() => setOpen(false), [identity]);
  useEffect(() => {
    if (!open) return;
    const outside = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    const escape = (event: KeyboardEvent) => {
      if (
        event.key === "Escape" &&
        !event.defaultPrevented &&
        !document.querySelector(":popover-open")
      ) {
        setOpen(false);
        trigger.current?.focus();
      }
    };
    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("pointerdown", outside);
      document.removeEventListener("keydown", escape);
    };
  }, [open]);
  return (
    <div className="shell-controls" ref={root}>
      {indicator}
      <button
        type="button"
        ref={trigger}
        className="br-btn shell-controls-trigger"
        data-header-controls-button
        aria-label={t("More options")}
        title={t("More options")}
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((value) => !value)}
      >
        <MoreHorizontal size={20} aria-hidden="true" />
      </button>
      <div id={id} className="shell-controls-panel" data-open={open}>
        {children}
      </div>
    </div>
  );
}

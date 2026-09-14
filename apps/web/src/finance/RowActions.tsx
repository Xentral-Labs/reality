import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { MoreHorizontal } from "lucide-react";
import { t } from "../localization";

export function RowActions({ disabled, children }: { disabled: boolean; children: ReactNode }) {
  const id = useId();
  const trigger = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState({ left: 0, top: 0 });
  useEffect(() => {
    if (disabled) panel.current?.hidePopover();
  }, [disabled]);
  function place() {
    const anchor = trigger.current!.getBoundingClientRect();
    const height = panel.current?.getBoundingClientRect().height || 96;
    setPosition({
      left: Math.max(12, Math.min(anchor.right - 224, window.innerWidth - 236)),
      top: Math.max(12, Math.min(anchor.bottom + 4, window.innerHeight - height - 12)),
    });
  }
  return (
    <>
      <button
        ref={trigger}
        type="button"
        className="finance-row-button finance-row-more"
        disabled={disabled}
        aria-label={t("More actions")}
        title={t("More actions")}
        aria-expanded={open}
        aria-controls={id}
        popoverTarget={id}
        onClick={place}
      >
        <MoreHorizontal size={16} aria-hidden="true" />
      </button>
      <div
        id={id}
        ref={panel}
        popover="auto"
        className="finance-row-menu"
        style={position}
        onToggle={() => {
          const showing = panel.current?.matches(":popover-open") || false;
          setOpen(showing);
          if (showing) {
            place();
            panel.current?.querySelector<HTMLButtonElement>("button:not(:disabled)")?.focus();
          }
        }}
        onClick={(event) => {
          if ((event.target as Element).closest("button:not(:disabled)")) {
            panel.current?.hidePopover();
            trigger.current?.focus();
          }
        }}
      >
        {children}
      </div>
    </>
  );
}

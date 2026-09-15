import { useEffect, useId, useRef, useState, type RefObject } from "react";
import { createPortal } from "react-dom";

/** One tooltip outside the scrolling sidebar, shared by its existing controls. */
export function SidebarTooltip({ navigation }: { navigation: RefObject<HTMLElement | null> }) {
  const id = useId();
  const target = useRef<HTMLElement | null>(null);
  const timer = useRef<number | undefined>(undefined);
  const [hint, setHint] = useState<{ label: string; left: number; top: number } | null>(null);
  const cancelHide = () => window.clearTimeout(timer.current);
  const hide = () => {
    cancelHide();
    if (target.current?.getAttribute("aria-describedby") === id)
      target.current.removeAttribute("aria-describedby");
    target.current = null;
    setHint(null);
  };
  const hideSoon = () => {
    cancelHide();
    timer.current = window.setTimeout(hide, 100);
  };
  useEffect(() => {
    const root = navigation.current;
    if (!root) return;
    const show = (event: Event) => {
      if (!window.matchMedia("(min-width: 1024px)").matches) return;
      if (event instanceof PointerEvent && event.pointerType === "touch") return;
      const element = (event.target as Element).closest<HTMLElement>("[data-sidebar-tooltip]");
      if (!element || !root.contains(element)) return;
      const collapsed =
        root.closest(".app-shell")?.getAttribute("data-navigation-collapsed") === "true";
      if (!collapsed && !element.hasAttribute("data-navigation-toggle")) return;
      cancelHide();
      if (target.current === element) return;
      hide();
      const rect = element.getBoundingClientRect();
      target.current = element;
      element.setAttribute("aria-describedby", id);
      setHint({
        label: element.dataset.sidebarTooltip!,
        left: rect.right + 10,
        top: Math.max(24, Math.min(innerHeight - 24, rect.top + rect.height / 2)),
      });
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") hide();
    };
    root.addEventListener("pointerover", show);
    root.addEventListener("focusin", show);
    root.addEventListener("pointerout", hideSoon);
    root.addEventListener("focusout", hide);
    root.addEventListener("click", hide);
    window.addEventListener("keydown", escape);
    window.addEventListener("scroll", hide, true);
    window.addEventListener("resize", hide);
    return () => {
      cancelHide();
      if (target.current?.getAttribute("aria-describedby") === id)
        target.current.removeAttribute("aria-describedby");
      root.removeEventListener("pointerover", show);
      root.removeEventListener("focusin", show);
      root.removeEventListener("pointerout", hideSoon);
      root.removeEventListener("focusout", hide);
      root.removeEventListener("click", hide);
      window.removeEventListener("keydown", escape);
      window.removeEventListener("scroll", hide, true);
      window.removeEventListener("resize", hide);
    };
  }, [navigation, id]);
  return hint
    ? createPortal(
        <div
          id={id}
          role="tooltip"
          className="sidebar-tooltip"
          style={{ left: hint.left, top: hint.top }}
          onPointerEnter={cancelHide}
          onPointerLeave={hideSoon}
        >
          {hint.label}
        </div>,
        document.body,
      )
    : null;
}

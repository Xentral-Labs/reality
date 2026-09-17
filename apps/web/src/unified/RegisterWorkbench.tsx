import { PageRecordCount } from "./PageHeading";
import { createPortal } from "react-dom";
import { filterChips } from "./FilterChip";
import {
  Children,
  cloneElement,
  isValidElement,
  createContext,
  useContext,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { ChevronDown, MoreHorizontal, Search } from "lucide-react";
import { t } from "../localization";
export const RegisterHeaderTarget = createContext<{
  target: HTMLDivElement | null;
  setHasTabs: (value: boolean) => void;
  setTabCount: (node: HTMLSpanElement | null) => void;
} | null>(null);
const ToolsContext = createContext<{
  target: HTMLDivElement | null;
  setTarget: (node: HTMLDivElement | null) => void;
} | null>(null);
export const useRegisterTools = () => useContext(ToolsContext);
export function RegisterWorkbench({ children }: { children: ReactNode }) {
  const [target, setTarget] = useState<HTMLDivElement | null>(null);
  return (
    <ToolsContext.Provider value={{ target, setTarget }}>
      <div className="register-workbench w-full min-w-0">{children}</div>
    </ToolsContext.Provider>
  );
}
export function RegisterHeader({
  children,
}: {
  title: string;
  children?: ReactNode;
  originalTitle?: boolean;
}) {
  const layout = useContext(RegisterHeaderTarget);
  const target = layout?.target;
  const group = isValidElement<{ children?: ReactNode }>(children) ? children : null;
  const tabs = Children.toArray(group?.props.children);
  const multiple =
    tabs.filter((tab) => isValidElement(tab) && (tab.type === "button" || tab.type === "a"))
      .length > 1;
  const activeKey = tabs.find(
    (tab) =>
      isValidElement<{ "aria-pressed"?: boolean; "aria-current"?: string }>(tab) &&
      (tab.props["aria-pressed"] === true || tab.props["aria-current"] === "page"),
  );
  const selectedKey = isValidElement(activeKey) ? activeKey.key : null;
  useLayoutEffect(() => {
    if (!multiple) return;
    const selected = target?.querySelector<HTMLElement>(
      '[aria-pressed="true"], [aria-current="page"]',
    );
    const strip = selected?.closest<HTMLElement>(".register-tabs");
    if (!selected || !strip) return;
    const count = target?.querySelector<HTMLElement>(".shell-tab-count");
    const keepVisible = () => {
      const tab = selected.getBoundingClientRect();
      const viewport = strip.getBoundingClientRect();
      if (!viewport.width) return;
      const right = count?.childElementCount ? count.getBoundingClientRect().right : tab.right;
      if (tab.left < viewport.left) strip.scrollLeft += tab.left - viewport.left;
      else if (right > viewport.right)
        strip.scrollLeft += Math.min(tab.left - viewport.left, right - viewport.right);
    };
    keepVisible();
    const observer = new ResizeObserver(keepVisible);
    observer.observe(strip);
    if (count) observer.observe(count);
    return () => observer.disconnect();
  }, [target, multiple, selectedKey]);
  useLayoutEffect(() => {
    if (!multiple || !layout) return;
    layout.setHasTabs(true);
    return () => layout.setHasTabs(false);
  }, [multiple, layout?.setHasTabs]);
  if (!target || !children) return null;
  if (!multiple || !group || !layout) return createPortal(children, target);
  const content = tabs.flatMap<ReactNode>((tab) => {
    const active =
      isValidElement<{ "aria-pressed"?: boolean; "aria-current"?: string }>(tab) &&
      (tab.props["aria-pressed"] === true || tab.props["aria-current"] === "page");
    return active
      ? [
          tab,
          <span
            key="active-count"
            className="page-introduction-count shell-tab-count"
            ref={layout.setTabCount}
          />,
        ]
      : [tab];
  });
  return createPortal(cloneElement(group, { children: content }), target);
}
export function RegisterToolbar({
  search,
  submit,
  filters,
  count,
  countDescription,
  countPlacement = "page",
}: {
  search: ReactNode;
  submit?: ReactNode;
  filters?: ReactNode;
  count?: number;
  countDescription?: string;
  countPlacement?: "page" | "local";
}) {
  const tools = useRegisterTools();
  return (
    <div className="register-toolbar-block">
      <div className="register-toolbar">
        <div className="register-search">
          <Search size={16} className="register-search-icon" />
          {search}
        </div>
        {submit}
      </div>
      <div className="register-filter-row">
        {filterChips(filters)}
        <div className="register-tools-slot" ref={tools?.setTarget} />
      </div>
      <PageRecordCount count={count} description={countDescription} placement={countPlacement} />
    </div>
  );
}
export function RegisterActions({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    const dismiss = (event: PointerEvent) => {
      if (
        ref.current?.open &&
        !ref.current.contains(event.target as Node) &&
        !(event.target as Element).closest?.("dialog")
      )
        ref.current.open = false;
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, []);
  return (
    <details
      className="register-actions"
      ref={ref}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          ref.current!.open = false;
          ref.current?.querySelector("summary")?.focus();
        }
      }}
    >
      <summary className="br-btn" aria-label={t("Table actions")}>
        <span className="register-actions-label">{t("More actions")}</span>
        <ChevronDown size={15} />
        <MoreHorizontal size={16} className="register-actions-compact-icon" />
      </summary>
      <div className="register-action-menu">{children}</div>
    </details>
  );
}

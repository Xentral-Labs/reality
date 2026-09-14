import { PageRecordCount } from "./PageHeading";
import { createPortal } from "react-dom";
import { filterChips } from "./FilterChip";
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { ChevronDown, Search } from "lucide-react";
import { t } from "../localization";
export const RegisterHeaderTarget = createContext<HTMLDivElement | null>(null);
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
  const target = useContext(RegisterHeaderTarget);
  return target && children ? createPortal(children, target) : null;
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
        {t("More actions")}
        <ChevronDown size={15} />
      </summary>
      <div className="register-action-menu">{children}</div>
    </details>
  );
}

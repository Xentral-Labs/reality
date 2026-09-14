import { createContext, useContext, type ReactNode } from "react";
import { formatNumber, t } from "../localization";
import { createPortal } from "react-dom";

export const PageActionTarget = createContext<HTMLDivElement | null | undefined>(undefined);

// Standalone dialogs keep local actions; application pages use the shared header.
export function PageActions({ children }: { children: ReactNode }) {
  const target = useContext(PageActionTarget);
  if (target === undefined) return <>{children}</>;
  return target ? createPortal(children, target) : null;
}

export const PageCountTarget = createContext<HTMLSpanElement | null | undefined>(undefined);
export function PageCount({ children }: { children: ReactNode }) {
  const target = useContext(PageCountTarget);
  return target ? createPortal(children, target) : null;
}

export function PageRecordCount({
  count,
  placement = "page",
  description,
}: {
  count?: number;
  placement?: "page" | "local";
  description?: string;
}) {
  const target = useContext(PageCountTarget);
  if (count === undefined) return null;
  if (placement === "local" || target === undefined)
    return (
      <p className="register-count">
        {formatNumber(count)} {t("records")}
      </p>
    );
  return (
    <PageCount>
      <span
        data-page-record-count
        title={description}
        className="rounded-full bg-surface-muted px-3 py-1 text-sm font-normal tabular-nums text-fg-muted"
      >
        {formatNumber(count)} <span className="sr-only">{t("records")}</span>
      </span>
    </PageCount>
  );
}

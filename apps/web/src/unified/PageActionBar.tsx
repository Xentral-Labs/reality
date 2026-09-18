import type { ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import { PageActions } from "./PageHeading";
import { RegisterActions } from "./RegisterWorkbench";
import { t } from "../localization";

export type PageAction = {
  key: string;
  label: string;
  onClick: (element: HTMLElement) => void;
  disabled?: boolean;
  icon?: ReactNode;
  expanded?: boolean;
};

// Page actions share one header slot. Menus are the default; chat exposes its primary actions.
export function PageActionBar({
  actions,
  presentation = "menu",
}: {
  actions: (PageAction | false | null | undefined)[];
  presentation?: "menu" | "inline";
}) {
  const available = actions.filter((action): action is PageAction => !!action);
  if (!available.length) return null;
  const button = (action: PageAction) => (
    <button
      key={action.key}
      type="button"
      data-page-action={presentation}
      aria-expanded={action.expanded}
      className="br-btn"
      disabled={action.disabled}
      onClick={(event) => action.onClick(event.currentTarget)}
    >
      {action.icon}
      <span>{t(action.label)}</span>
      {action.expanded !== undefined && <ChevronDown size={14} />}
    </button>
  );
  return (
    <PageActions>
      {presentation === "inline" ? (
        <div className="page-inline-actions">{available.map(button)}</div>
      ) : (
        <RegisterActions>{available.map(button)}</RegisterActions>
      )}
    </PageActions>
  );
}

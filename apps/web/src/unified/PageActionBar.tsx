import { PageActions } from "./PageHeading";
import { RegisterActions } from "./RegisterWorkbench";
import { t } from "../localization";

export type PageAction = {
  key: string;
  label: string;
  onClick: (element: HTMLElement) => void;
  disabled?: boolean;
};

// The one way a page reaches the header slot: every page action folds into one predictable
// More actions disclosure. No actions, no bar.
export function PageActionBar({ actions }: { actions: (PageAction | false | null | undefined)[] }) {
  const available = actions.filter((action): action is PageAction => !!action);
  if (!available.length) return null;
  const button = (action: PageAction) => (
    <button
      key={action.key}
      type="button"
      data-page-action="menu"
      className="br-btn"
      disabled={action.disabled}
      onClick={(event) => action.onClick(event.currentTarget)}
    >
      {t(action.label)}
    </button>
  );
  return (
    <PageActions>
      <RegisterActions>{available.map(button)}</RegisterActions>
    </PageActions>
  );
}

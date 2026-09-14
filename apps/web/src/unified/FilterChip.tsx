import {
  Children,
  Fragment,
  cloneElement,
  isValidElement,
  type ReactElement,
  type ReactNode,
  type SelectHTMLAttributes,
} from "react";
import { ChevronDown, SlidersHorizontal } from "lucide-react";
type Select = ReactElement<SelectHTMLAttributes<HTMLSelectElement>>;
export function FilterChip({ label, select }: { label: string; select: Select }) {
  const selected = Children.toArray(select.props.children)
    .flatMap((child): ReactElement<{ value?: string; children?: ReactNode }>[] =>
      isValidElement(child)
        ? [child as ReactElement<{ value?: string; children?: ReactNode }>]
        : [],
    )
    .find((child) => String(child.props.value ?? "") === String(select.props.value ?? ""));
  // Options from mapped arrays are already flattened by Children.toArray.
  return (
    <label className="register-filter-chip">
      <SlidersHorizontal size={14} aria-hidden="true" />
      <span aria-hidden="true">
        {label}: <strong>{selected?.props.children || String(select.props.value || "—")}</strong>
      </span>
      <ChevronDown size={14} aria-hidden="true" />
      {cloneElement(select, {
        "aria-label": select.props["aria-label"] || label,
        className: "register-chip-select",
        style: undefined,
      })}
    </label>
  );
}
function plain(node: ReactNode): string {
  return Children.toArray(node)
    .map((child) =>
      isValidElement<{ children?: ReactNode }>(child) ? plain(child.props.children) : String(child),
    )
    .join(" ")
    .trim();
}
export function filterChips(children: ReactNode): ReactNode {
  return Children.map(children, (child) => {
    if (!isValidElement<{ children?: ReactNode; "aria-label"?: string }>(child)) return child;
    if (child.type === Fragment) return <>{filterChips(child.props.children)}</>;
    if (child.type === "select")
      return <FilterChip label={child.props["aria-label"] || ""} select={child as Select} />;
    if (child.type === "label") {
      const contents = Children.toArray(child.props.children);
      const select = contents.find((node) => isValidElement(node) && node.type === "select") as
        Select | undefined;
      if (select)
        return (
          <FilterChip
            label={select.props["aria-label"] || plain(contents.filter((node) => node !== select))}
            select={select}
          />
        );
    }
    return child;
  });
}

import { cloneElement, type ReactElement, type ReactNode } from "react";
import { workCountBadge } from "./dailyWork";

/**
 * A register tab followed by the open work behind it (spec 254).
 *
 * The open tab shows its own register count, so the work count appears only
 * while the tab is inactive, and never at zero. The count is described to
 * assistive technology on the tab itself. A warning count states a signal
 * rather than the length of the list the tab opens; an accent count is the one
 * the sidebar badge repeats.
 */
export function withWorkCount(
  tab: ReactElement<{ "aria-describedby"?: string }>,
  {
    count,
    active,
    description,
    tone,
  }: {
    count: number | null;
    active: boolean;
    description: string;
    tone?: "warning" | "accent";
  },
): ReactNode[] {
  const badge = workCountBadge(count);
  if (active || !badge) return [tab];
  const id = `work-count-${String(tab.key)}`;
  return [
    cloneElement(tab, { "aria-describedby": id }),
    <span key={`${String(tab.key)}-work-count`} className="shell-tab-work-count" aria-hidden="true">
      <span data-tab-work-count data-tone={tone}>
        {badge}
      </span>
      <span id={id} hidden>
        {`${description}: ${badge}`}
      </span>
    </span>,
  ];
}

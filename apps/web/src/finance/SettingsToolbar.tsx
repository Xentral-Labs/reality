import type { ReactNode } from "react";

// Shared list actions use the same alignment in every Finance settings area.
export function SettingsToolbar({ children }: { children: ReactNode }) {
  return (
    <div
      data-settings-toolbar
      className="flex min-w-0 flex-wrap items-end justify-between gap-3 [&>.br-btn-primary]:ml-auto [&>.br-btn]:self-end"
    >
      {children}
    </div>
  );
}

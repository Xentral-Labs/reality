import { useId, type ReactNode } from "react";
import { ChevronDown, ChevronRight, Folder, FolderOpen } from "lucide-react";

const branchStyles = {
  category: "border-b border-border-default last:border-0",
  group: "ml-3 border-l border-border-default pl-3 sm:ml-6",
};

/** Shared folder hierarchy for the Tools directories. */
export function DirectoryBranch({
  id,
  label,
  count,
  level = "category",
  open,
  toggle,
  children,
}: {
  id: string;
  label: string;
  count: ReactNode;
  level?: "category" | "group";
  open: boolean;
  toggle: () => void;
  children: ReactNode;
}) {
  const contentId = useId();
  return (
    <section className={branchStyles[level]} data-directory-branch={id}>
      <button
        type="button"
        className="flex w-full min-w-0 items-center gap-2 rounded-lg px-2 py-3 text-left hover:bg-surface-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
        aria-expanded={open}
        aria-controls={contentId}
        onClick={toggle}
      >
        {open ? (
          <ChevronDown size={16} className="shrink-0" />
        ) : (
          <ChevronRight size={16} className="shrink-0" />
        )}
        {level === "category" &&
          (open ? (
            <FolderOpen size={18} className="shrink-0 text-accent" />
          ) : (
            <Folder size={18} className="shrink-0 text-accent" />
          ))}
        <span className="min-w-0 flex-1 font-medium">{label}</span>
        <span className="text-right text-xs text-fg-muted">{count}</span>
      </button>
      <div id={contentId} hidden={!open}>
        {children}
      </div>
    </section>
  );
}

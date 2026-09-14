import { LoaderCircle } from "lucide-react";
import { t } from "../localization";

/** Immediate feedback while no workspace is available yet. */
export function EntryProgress({
  title = "Loading your access",
  detail = "Please wait. You will continue automatically.",
}: {
  title?: string;
  detail?: string;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-surface p-8">
      <section
        className="w-full max-w-md space-y-5 text-center"
        role="status"
        aria-live="polite"
        aria-busy="true"
      >
        <p className="text-sm font-semibold text-fg-muted">Reality</p>
        <LoaderCircle
          className="mx-auto h-8 w-8 animate-spin motion-reduce:animate-none text-accent"
          aria-hidden="true"
        />
        <h1 className="text-2xl font-semibold">{t(title)}</h1>
        <p className="text-fg-muted">{t(detail)}</p>
      </section>
    </main>
  );
}

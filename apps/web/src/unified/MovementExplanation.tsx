import { api } from "../api";
import { t } from "../localization";
import { useRead } from "./useCompanyContext";

export function MovementExplanation({
  tenant,
  movementId,
}: {
  tenant: string;
  movementId: string;
}) {
  const read = useRead(() => api.movementExplanation(tenant, movementId), [tenant, movementId]);
  if (read.loading && !read.data)
    return <p className="text-sm text-fg-muted">{t("Loading explanation…")}</p>;
  if (read.error)
    return (
      <p role="alert" className="text-sm text-danger">
        {read.error}
      </p>
    );
  if (!read.data) return null;
  return (
    <section className="mb-4 rounded-xl border border-border-default bg-surface-muted p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-fg-muted">
        {t("Why did this happen?")}
      </p>
      <p className="mt-2 text-sm text-fg-strong">{t(read.data.summary)}</p>
      {read.data.reason && <p className="mt-1 text-sm text-fg-muted">{read.data.reason}</p>}
      {!read.data.explained && (
        <p role="alert" className="mt-2 text-sm text-warning">
          {t(
            "This movement has no linked business reason. It remains visible as an operational exception.",
          )}
        </p>
      )}
      {read.data.links.length > 0 && (
        <dl className="mt-3 grid gap-2 text-sm">
          {read.data.links.map((link) => (
            <div key={`${link.kind}:${link.id}`} className="flex justify-between gap-4">
              <dt className="text-fg-muted">{t(link.label)}</dt>
              <dd className="font-mono text-xs text-fg-strong">{link.id}</dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}

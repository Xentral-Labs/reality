import { useEffect, useId, useRef, useState } from "react";
import { api } from "../api";
import { t } from "../localization";
import { ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";

export function CatalogCodeDialog({
  tenant,
  kind,
  entryKey,
  close,
}: {
  tenant: string;
  kind: string;
  entryKey: string;
  close: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const [selected, setSelected] = useState(0);
  const read = useRead(() => api.catalogCode(tenant, kind, entryKey), [tenant, kind, entryKey]);
  useEffect(() => {
    const trigger = document.activeElement as HTMLElement | null;
    const node = dialog.current!;
    node.showModal();
    return () => {
      node.close();
      trigger?.focus();
    };
  }, []);
  const source = read.data?.sources[selected] || read.data?.sources[0];
  return (
    <dialog
      ref={dialog}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
      className="m-auto max-h-[90dvh] w-[min(1200px,94vw)] overflow-auto rounded-xl border border-border-default bg-surface p-5 text-fg shadow-xl backdrop:bg-black/30"
    >
      <header className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 id={titleId} className="text-lg font-semibold">
            {t("Python code")}
          </h2>
          <p className="mt-1 break-all text-sm text-fg-muted" data-localization="original">
            {entryKey}
          </p>
        </div>
        <button className="br-btn" onClick={close}>
          {t("Close")}
        </button>
      </header>
      {!read.data ? (
        <ReadState loading={read.loading} error={read.error} retry={read.refresh} />
      ) : (
        <>
          <p className="mb-4 text-sm text-fg-muted">
            {read.data.relationship === "action_command"
              ? t(
                  "This action uses the following Python command. The code is shown for reading, not execution.",
                )
              : read.data.relationship === "view_projection"
                ? t(
                    "This view uses the following projection. These Python functions read and calculate its data.",
                  )
                : read.data.relationship === "view_reader"
                  ? t(
                      "This view reads a register directly. This is its Python read endpoint, not the screen layout.",
                    )
                  : t(
                      "Python functions from the running application. This view does not execute or change the code.",
                    )}
          </p>
          {read.data.sources.length > 1 && (
            <label className="mb-4 block text-sm">
              {t("Function")}
              <select
                aria-label={t("Function")}
                className="br-control mt-1 w-full"
                value={selected}
                onChange={(event) => setSelected(Number(event.target.value))}
              >
                {read.data.sources.map((item, index) => (
                  <option key={`${item.path}:${item.function}`} value={index}>
                    {item.function}
                  </option>
                ))}
              </select>
            </label>
          )}
          {source ? (
            <>
              <p
                className="mb-3 break-all font-mono text-xs text-fg-muted"
                data-localization="original"
              >
                {source.path} · {source.function}
              </p>
              {source.truncated && (
                <p role="status" className="mb-3 text-sm">
                  {t("Code preview truncated to 600 lines or 64 KiB.")}
                </p>
              )}
              <pre
                className="max-h-[60dvh] overflow-auto rounded-lg border border-border-default bg-surface-muted p-4 text-xs leading-6"
                tabIndex={0}
                aria-label={t("Python source code")}
                data-localization="original"
              >
                <code>{source.code}</code>
              </pre>
            </>
          ) : (
            <p>{t("No results")}</p>
          )}
        </>
      )}
    </dialog>
  );
}

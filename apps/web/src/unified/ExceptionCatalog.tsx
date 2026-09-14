import { InspectorDisclosure } from "./InspectorCatalog";
import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { api } from "../api";
import { t } from "../localization";
import { label } from "./ExceptionRulesRegister";
import { ReadLine } from "./ReadState";

/** The catalog as a dialog: every possible finding type, opened from the Exceptions page. */
export default function ExceptionCatalog({ onClose }: { onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [catalog, setCatalog] = useState<Awaited<ReturnType<typeof api.exceptionCatalog>> | null>(
    null,
  );
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  const [search, setSearch] = useState("");
  useEffect(() => {
    const element = dialog.current!;
    element.showModal();
    return () => element.close();
  }, []);
  useEffect(() => {
    let current = true;
    setError(false);
    setCatalog(null);
    api
      .exceptionCatalog()
      .then((result) => {
        if (current) setCatalog(result);
      })
      .catch(() => {
        if (current) setError(true);
      });
    return () => {
      current = false;
    };
  }, [retry]);
  const rows =
    catalog?.classes.filter((row) =>
      [label(row), row.label, row.description, row.owner, row.id]
        .join(" ")
        .toLocaleLowerCase()
        .includes(search.toLocaleLowerCase()),
    ) ?? [];
  const content = (
    <>
      <header className="flex items-center justify-between gap-4 text-sm font-semibold">
        <h2 id="exception-catalog-title">{t("Exception catalog")}</h2>
        <button
          className="secondary-button"
          aria-label={t("Close")}
          onClick={() => dialog.current?.close()}
        >
          <X size={18} />
        </button>
      </header>
      <p className="br-help">
        {t(
          "These are the possible finding types in Reality, not your company’s active findings. Each type requires matching records. Descriptions use the catalog’s original language.",
        )}
      </p>
      <label className="br-field">
        <span className="br-label">{t("Search")}</span>
        <input
          className="br-control"
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </label>
      {error ? (
        <div role="alert">
          <p>{t("Could not load the exception catalog.")}</p>
          <button className="secondary-button" onClick={() => setRetry((value) => value + 1)}>
            {t("Retry")}
          </button>
        </div>
      ) : !catalog ? (
        <ReadLine />
      ) : (
        <>
          <p className="br-help">
            {rows.length} / {catalog.classes.length}
          </p>
          {!rows.length && <p role="status">{t("No matching exception classes.")}</p>}
          {rows.map((row) => (
            <InspectorDisclosure key={row.id}>
              <summary className="cursor-pointer font-semibold">{label(row)}</summary>
              <p className="mt-3 text-sm leading-6">{row.description}</p>
              <dl className="mt-3 grid gap-2 text-sm">
                <div>
                  <dt className="font-semibold">{t("Responsible area")}</dt>
                  <dd>{row.owner}</dd>
                </div>
                <div>
                  <dt className="font-semibold">{t("How it clears")}</dt>
                  <dd>{row.clears_through}</dd>
                </div>
              </dl>
              <p className="br-help mt-3">
                {row.id} · {row.severity}
              </p>
            </InspectorDisclosure>
          ))}
        </>
      )}
    </>
  );
  return (
    <dialog
      ref={dialog}
      className="br-exception-catalog"
      aria-labelledby="exception-catalog-title"
      onClose={(event) => {
        if (!event.currentTarget.open) onClose();
      }}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          event.stopPropagation();
          dialog.current?.close();
        }
      }}
    >
      {content}
    </dialog>
  );
}

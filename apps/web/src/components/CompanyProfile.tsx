import { useState } from "react";
import { api, type CompanySetupResult, type CompanyProfileManifest } from "../api";
import { formatDateTime, t } from "../localization";
import { Inspector } from "../unified/Inspector";

export function CompanyProfile({
  requestKey,
  result,
}: {
  requestKey: string;
  result: CompanySetupResult;
}) {
  const [manifest, setManifest] = useState<CompanyProfileManifest>();
  const [selected, setSelected] = useState<string>();
  const [execution, setExecution] = useState<CompanySetupResult>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const load = async () => {
    if (manifest || busy) return;
    setBusy(true);
    setError(false);
    try {
      setManifest(await api.companySetupProfile(requestKey));
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  };
  return (
    <details
      className="company-profile"
      onToggle={(event) => {
        if (event.currentTarget.open) void load();
      }}
    >
      <summary>{t("Demo profile and practice cases")}</summary>
      {error && (
        <p role="alert">
          {t("Could not load this view")} <button onClick={() => void load()}>{t("Retry")}</button>
        </p>
      )}
      {busy && <p role="status">{t("Loading…")}</p>}
      {manifest && (
        <>
          <p>
            {t("Comparison periods")}: {formatDateTime(manifest.windows.prior_start)} —{" "}
            {formatDateTime(manifest.windows.current_start)} —{" "}
            {formatDateTime(manifest.windows.end)}
          </p>
          <p>
            {t(
              "Amounts are booked gross values by currency. Costs and promotions are not provided.",
            )}
          </p>
          <ul>
            {Object.entries(manifest.cases)
              .filter(([, value]) => value.document_id)
              .map(([key, value]) => (
                <li key={key}>
                  <button
                    className="secondary-button"
                    onClick={() => setSelected(value.document_id)}
                  >
                    <span data-localization="original">{key}</span> · {t("Open order")}
                  </button>
                </li>
              ))}
          </ul>
          {selected && (
            <Inspector
              key={selected}
              tenant={result.tenant_id}
              target={{ kind: "document", id: selected }}
              close={() => setSelected(undefined)}
            />
          )}
          {result.profile?.key === "international_demo" && (
            <section>
              <p>
                {t(
                  "Create a separate company with one reservable unit and a blocked case. No reservation is executed during setup.",
                )}
              </p>
              <button
                className="secondary-button"
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  setError(false);
                  const storage = `reality.execution.${result.tenant_id}`;
                  const saved = sessionStorage.getItem(storage);
                  const body = saved
                    ? JSON.parse(saved)
                    : {
                        request_key: crypto.randomUUID(),
                        name: `${result.name.slice(0, 90)} · Reservation practice`,
                        confirmed: true,
                      };
                  sessionStorage.setItem(storage, JSON.stringify(body));
                  try {
                    setExecution(await api.companySetupExecution(requestKey, body));
                    sessionStorage.removeItem(storage);
                  } catch {
                    setError(true);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                {t("Create reservation practice")}
              </button>
              {execution?.destination && (
                <a className="primary-button" href={execution.destination}>
                  {t("Open company")}
                </a>
              )}
            </section>
          )}
        </>
      )}
    </details>
  );
}

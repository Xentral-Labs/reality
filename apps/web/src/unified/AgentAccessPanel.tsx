import { useEffect, useState } from "react";
import { cockpitApi } from "../api";
import { formatZonedDateTime as formatDateTime, formatNumber, t } from "../localization";
import { useCockpitLiveRead } from "./useCockpitLiveRead";
import { ReadState } from "./ReadState";
import type { AgentAccess } from "./cockpitModel";

export function AgentAccessPanel({ tenant }: { tenant: string }) {
  const [expanded, setExpanded] = useState(false),
    [scope, setScope] = useState("active"),
    [after, setAfter] = useState("");
  const [selected, setSelected] = useState<AgentAccess | null>(null);
  const state = useCockpitLiveRead(`${tenant}:agents:${scope}:${after}:${expanded}`, (signal) =>
    cockpitApi.agents(tenant, scope, after, expanded ? 50 : 6, signal),
  );
  const value = state.data;
  useEffect(() => {
    if (state.status === "denied") {
      setSelected(null);
    }
  }, [state.status]);
  useEffect(() => {
    setSelected(null);
    setAfter("");
    setExpanded(false);
    setScope("active");
  }, [tenant]);
  if (state.status === "denied")
    return (
      <section className="cockpit-card" data-agent-access>
        <h2>{t("Agents & connections")}</h2>
        <p className="cockpit-note">{t("Agent access overview is restricted to company owners")}</p>
      </section>
    );
  return (
    <section className="cockpit-card" data-agent-access aria-labelledby="agents-title">
      <div className="cockpit-card-heading">
        <div>
          <span className="cockpit-eyebrow">{t("Registered access")}</span>
          <h2 id="agents-title">{t("Agents & connections")}</h2>
        </div>
        <button
          className="br-btn"
          onClick={() => {
            setExpanded(!expanded);
            setAfter("");
          }}
        >
          {t(expanded ? "Compact view" : "View all accesses")}
        </button>
      </div>
      {expanded && (
        <label className="br-field cockpit-access-filter">
          {t("Access state")}
          <select
            className="br-control"
            value={scope}
            onChange={(event) => {
              setScope(event.target.value);
              setAfter("");
            }}
          >
            {["active", "inactive", "revoked", "all"].map((key) => (
              <option key={key} value={key}>
                {t(key)}
              </option>
            ))}
          </select>
        </label>
      )}
      {state.status === "stale" && (
        <p className="cockpit-note" role="status">
          {t("Previous observation — refresh failed")}
        </p>
      )}
      {!value && (
        <ReadState
          loading={!state.error}
          error={state.error instanceof Error ? state.error.message : undefined}
        />
      )}
      {value && (
        <>
          <p className="cockpit-note">
            {t("Matching access records")}: {formatNumber(value.total)} · {t(value.scope)}
          </p>
          <p className="cockpit-note">
            {t("Data observed at")}:{" "}
            {value.observed_at ? (
              <time data-observed-at dateTime={value.observed_at}>
                {formatDateTime(value.observed_at)}
              </time>
            ) : (
              t("Unknown")
            )}
          </p>
          <ul className="cockpit-agent-list">
            {value.items.map((row) => (
              <li key={row.identity}>
                <button onClick={() => setSelected(row)}>
                  <span className="cockpit-agent-avatar">{row.name.slice(0, 1).toUpperCase()}</span>
                  <span>
                    <strong>{row.name}</strong>
                    <small>
                      {row.connection_kind === "oauth" ? "OAuth" : "MCP"} · {t(row.access_state)}
                      {row.access_reason ? ` · ${t(row.access_reason)}` : ""}
                    </small>
                    <small>
                      {row.last_used_at
                        ? `${t("Last used")}: ${formatDateTime(row.last_used_at)}`
                        : t("No use recorded")}
                    </small>
                    {row.observed_action && (
                      <small>
                        {row.observed_action.operation} · {t(row.observed_action.outcome)}
                      </small>
                    )}
                  </span>
                </button>
              </li>
            ))}
          </ul>
          {value.total === 0 && (
            <p className="cockpit-note">{t("No access records match this filter")}</p>
          )}
          {expanded && (
            <div className="cockpit-pagination cockpit-pagination-actions">
              <button className="br-btn" disabled={!after} onClick={() => setAfter("")}>
                {t("First page")}
              </button>
              <button
                className="br-btn"
                disabled={!value.has_more}
                onClick={() => setAfter(value.next_after || "")}
              >
                {t("Next page")}
              </button>
            </div>
          )}
          <p className="cockpit-footnote">
            {t(
              "Access authorization and last use do not establish that an external Agent is connected or working now.",
            )}
          </p>
          {selected && (
            <div className="cockpit-basis">
              <button className="br-btn" onClick={() => setSelected(null)}>
                {t("Close")}
              </button>
              <h3>{selected.name}</h3>
              <p>{t("External runtime state is unknown")}</p>
              <p>
                {t("Permitted tools")}: {selected.permitted_tools.join(", ")}
              </p>
              {selected.observed_action && (
                <p>
                  {t("Observed action")}: {selected.observed_action.operation} ·{" "}
                  {t(selected.observed_action.outcome)} ·{" "}
                  {formatDateTime(selected.observed_action.recorded_at)}
                </p>
              )}
            </div>
          )}
        </>
      )}
    </section>
  );
}

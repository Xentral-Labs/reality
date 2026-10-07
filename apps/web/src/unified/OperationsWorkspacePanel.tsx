import { useState, type ReactNode } from "react";
import { t } from "../localization";

const views = [
  { key: "responsibility", label: "Responsibility", title: "Cases & takeover" },
  { key: "activity", label: "Live event log", title: "Recorded business activity" },
  { key: "agents", label: "Registered Agents", title: "Agents & connections" },
] as const;
type WorkspaceView = (typeof views)[number]["key"];

export function OperationsWorkspacePanel({
  responsibility,
  activity,
  agents,
}: {
  responsibility: ReactNode;
  activity: ReactNode;
  agents: ReactNode;
}) {
  const [selected, setSelected] = useState<WorkspaceView>("responsibility");
  const panels = { responsibility, activity, agents };
  return (
    <section
      className="cockpit-card cockpit-operations-workspace"
      aria-labelledby="workspace-heading"
      data-operations-workspace
    >
      <header className="cockpit-card-heading">
        <div>
          <span className="cockpit-eyebrow">{t("Operations workspace")}</span>
          <h2 id="workspace-heading">{t(views.find((view) => view.key === selected)!.title)}</h2>
        </div>
        <label className="br-field cockpit-workspace-selector">
          {t("Workspace view")}
          <select
            className="br-control"
            value={selected}
            onChange={(event) => setSelected(event.target.value as WorkspaceView)}
            aria-controls={`cockpit-workspace-${selected}`}
          >
            {views.map(({ key, label }) => (
              <option key={key} value={key}>
                {t(label)}
              </option>
            ))}
          </select>
        </label>
      </header>
      {views.map(({ key, label }) => (
        <div
          key={key}
          id={`cockpit-workspace-${key}`}
          className="cockpit-workspace-pane"
          data-workspace-view={key}
          hidden={selected !== key}
          role="region"
          aria-label={t(label)}
        >
          {panels[key]}
        </div>
      ))}
    </section>
  );
}

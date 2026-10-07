import type { ReactNode } from "react";

export function OperationsWorkspacePanel({
  activity,
  agents,
}: {
  activity: ReactNode;
  agents: ReactNode;
}) {
  return (
    <div className="cockpit-monitoring-stack" data-operations-workspace>
      {activity}
      {agents}
    </div>
  );
}

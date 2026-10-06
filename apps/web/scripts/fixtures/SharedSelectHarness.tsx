import React from "react";
import { createRoot } from "react-dom/client";
import { ChevronDown } from "lucide-react";
import { applyTheme } from "../../src/theme";
import "../../src/tailwind.css";
import "../../src/unified/operationsCockpit.css";

applyTheme(new URLSearchParams(location.search).get("theme") === "dark" ? "dark" : "light");
const options = (
  <>
    <option value="first">Today · follows the company business day</option>
    <option value="second">All dispatch sites</option>
  </>
);
function Field({
  label,
  className = "br-control",
  disabled = false,
}: {
  label: string;
  className?: string;
  disabled?: boolean;
}) {
  return (
    <label className="br-field">
      <span className="br-label">{label}</span>
      <select aria-label={label} className={className} disabled={disabled} data-shared-select>
        {options}
      </select>
    </label>
  );
}
createRoot(document.getElementById("root")!).render(
  <main
    style={{
      padding: 20,
      maxWidth: 900,
      margin: "auto",
      display: "grid",
      gridTemplateColumns: "minmax(0, 1fr)",
      gap: 20,
    }}
  >
    <h1>Shared native select fields</h1>
    <Field label="Standard form" />
    <div className="settings-form">
      <Field label="Settings" className="" />
    </div>
    <div className="master-edit-fields">
      <Field label="Master data" className="" />
    </div>
    <div className="header-select">
      <Field label="Header filter" className="" />
    </div>
    <div className="cockpit-filters">
      <Field label="Business day" />
    </div>
    <div className="cockpit-access-filter">
      <Field label="Agent filter" />
    </div>
    <Field label="Legacy filter" className="select-control" />
    <Field label="Unavailable selection" disabled />
    <div className="erp-pagination-tools">
      <label>
        Rows per page
        <select className="br-control" data-shared-select defaultValue="100">
          <option>50</option>
          <option>100</option>
        </select>
      </label>
    </div>
    <label className="register-filter-chip">
      <span>Row density</span>
      <ChevronDown size={14} aria-hidden />
      <select className="register-chip-select" aria-label="Row density">
        <option>Normal rows</option>
        <option>Compact rows</option>
      </select>
    </label>
    <label>
      Native multiple
      <select className="br-control" multiple aria-label="Native multiple">
        {options}
      </select>
    </label>
    <label>
      Native listbox
      <select className="br-control" size={2} aria-label="Native listbox">
        {options}
      </select>
    </label>
  </main>,
);

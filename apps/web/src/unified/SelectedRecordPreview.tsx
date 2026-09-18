import type { ReactNode } from "react";
import { X } from "lucide-react";
import { t } from "../localization";

/** An exact selection outside the loaded page is a preview, not a register toolbar. */
export function SelectedRecordPreview({
  kind,
  close,
  children,
}: {
  kind: "order" | "master";
  close: () => void;
  children: ReactNode;
}) {
  return (
    <section
      className="selected-record-preview"
      {...(kind === "order"
        ? { "data-selected-order-detail": true }
        : { "data-selected-master-detail": true })}
    >
      <div className="selected-record-preview-toolbar">
        <button type="button" className="br-btn" aria-label={t("Close")} onClick={close}>
          <X size={16} aria-hidden="true" />
          {t("Close")}
        </button>
      </div>
      {children}
    </section>
  );
}

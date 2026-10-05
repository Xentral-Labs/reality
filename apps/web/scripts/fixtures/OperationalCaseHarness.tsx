import React from "react";
import { createRoot } from "react-dom/client";
import { OperationalCaseDetail } from "../../src/unified/OperationalCaseDetail";

createRoot(document.getElementById("root")!).render(
  <OperationalCaseDetail
    tenant="cases"
    documentId={new URL(location.href).searchParams.get("document") || undefined}
  />,
);

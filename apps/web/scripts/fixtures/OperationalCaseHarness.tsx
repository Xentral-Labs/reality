import React from "react";
import { createRoot } from "react-dom/client";
import "../../src/tailwind.css";
import { LocalizationProvider, type Language } from "../../src/localization";
import { applyTheme } from "../../src/theme";
import { OperationalCaseDetail } from "../../src/unified/OperationalCaseDetail";

applyTheme(new URL(location.href).searchParams.get("theme") === "dark" ? "dark" : "light");

const language = (new URL(location.href).searchParams.get("language") || "en") as Language;
createRoot(document.getElementById("root")!).render(
  <LocalizationProvider
    preferences={{
      language,
      locale: { en: "en-GB", de: "de-DE", nl: "nl-NL", es: "es-ES" }[language],
      timezone: "UTC",
    }}
  >
    <OperationalCaseDetail
      tenant="cases"
      documentId={new URL(location.href).searchParams.get("document") || undefined}
    />
  </LocalizationProvider>,
);

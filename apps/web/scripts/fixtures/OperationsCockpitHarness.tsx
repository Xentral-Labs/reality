import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { OperationsCockpitPage } from "../../src/unified/OperationsCockpitPage";
import { readSelection, navigationSelection, selectionUrl } from "../../src/unified/routing";
import { LocalizationProvider, type Language } from "../../src/localization";
import { applyTheme } from "../../src/theme";
import "../../src/tailwind.css";

function Harness() {
  const [selection, setSelection] = useState(() =>
    readSelection(new URL("http://localhost/app/cockpit?tenant=cockpit")),
  );
  const navigate = (changes: Parameters<typeof navigationSelection>[1]) => {
    const next = navigationSelection(selection, changes);
    history.replaceState(null, "", selectionUrl(next));
    setSelection(next);
  };
  Object.assign(window, { __cockpitNavigate: navigate });
  const [query] = useState(() => new URLSearchParams(window.location.search));
  const language = (query.get("language") || "en") as Language;
  applyTheme(query.get("theme") === "dark" ? "dark" : "light");
  return (
    <LocalizationProvider
      preferences={{
        language,
        locale:
          query.get("locale") ||
          (language === "de"
            ? "de-DE"
            : language === "nl"
              ? "nl-NL"
              : language === "es"
                ? "es-ES"
                : "en-GB"),
        timezone: query.get("timezone") || "UTC",
      }}
    >
      {selection.route === "cockpit" ? (
        <OperationsCockpitPage selection={selection} navigate={navigate} />
      ) : (
        <p data-home-fallback>Home</p>
      )}
    </LocalizationProvider>
  );
}
createRoot(document.getElementById("root")!).render(<Harness />);

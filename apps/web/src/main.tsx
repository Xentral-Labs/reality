import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { applyTheme, readThemePreference } from "./theme";
import App from "./App";

// Resolve the theme before the first paint so the app never flashes light.
applyTheme(readThemePreference());

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

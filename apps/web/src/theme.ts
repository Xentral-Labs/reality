export type ThemePreference = "light" | "dark" | "system";

const STORAGE_KEY = "reality.theme";
const PREFERENCES: ThemePreference[] = ["light", "dark", "system"];

const systemQuery = () => window.matchMedia("(prefers-color-scheme: dark)");

export const readThemePreference = (): ThemePreference => {
  const stored = localStorage.getItem(STORAGE_KEY);
  return PREFERENCES.includes(stored as ThemePreference) ? (stored as ThemePreference) : "system";
};

export const resolveTheme = (preference: ThemePreference): "light" | "dark" =>
  preference === "system" ? (systemQuery().matches ? "dark" : "light") : preference;

export const applyTheme = (preference: ThemePreference) => {
  document.documentElement.dataset.theme = resolveTheme(preference);
};

export const storeThemePreference = (preference: ThemePreference) => {
  localStorage.setItem(STORAGE_KEY, preference);
  applyTheme(preference);
  window.dispatchEvent(new Event("reality:theme-changed"));
};

/** Keeps a "system" preference in step with the OS while the tab stays open. */
export const watchSystemTheme = (onChange: () => void) => {
  const query = systemQuery();
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
};

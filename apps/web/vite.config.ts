import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

declare const process: { env: Record<string, string | undefined> };

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const apiTarget =
    process.env.VITE_API_PROXY_TARGET || env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000";
  return {
    plugins: [react(), tailwindcss()],
    define: {
      __DOCS_URL__: JSON.stringify(process.env.DOCS_URL || env.DOCS_URL || "http://localhost:8083"),
      __SITE_URL__: JSON.stringify(process.env.SITE_URL || env.SITE_URL || "http://localhost:8082"),
    },
    server: {
      port: 5173,
      proxy: { "/api": apiTarget, "/healthz": apiTarget },
    },
  };
});

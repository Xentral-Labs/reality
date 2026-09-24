import { EntryProgress } from "./components/EntryProgress";
import { lazy, Suspense } from "react";
import { AuthGate } from "./Auth";
import { LocalizationProvider, t } from "./localization";
import { resolveEntry } from "./entryRouting";
import { oauthInteraction } from "./entryRouting";
import { OAuthAuthorization } from "./OAuthAuthorization";
import "./tailwind.css";

const UnifiedApp = lazy(() => import("./unified/UnifiedApp"));

export default function App() {
  return (
    <AuthGate>
      {(user, updateUser) => (
        <LocalizationProvider preferences={user}>
          <Suspense fallback={<EntryProgress title="Loading your workspace" />}>
            <Entry user={user} updateUser={updateUser} />
          </Suspense>
        </LocalizationProvider>
      )}
    </AuthGate>
  );
}
function Entry(props: {
  user: import("./api").AuthUser;
  updateUser: (user: import("./api").AuthUser) => void;
}) {
  const result = resolveEntry(new URL(location.href));
  if (result.kind === "redirect") {
    history.replaceState(null, "", result.href);
    return <UnifiedApp {...props} />;
  }
  if (result.kind === "app") return <UnifiedApp {...props} />;
  if (result.kind === "oauth")
    return <OAuthAuthorization interaction={oauthInteraction(new URL(location.href))!} />;
  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="text-xl font-semibold">
        {t(result.kind === "retired" ? "Playground has been retired" : "Page unavailable")}
      </h1>
      <p className="my-4">
        {t(
          result.kind === "retired"
            ? "Use the Reality app for your work. Existing records have been preserved."
            : "This address no longer has a workspace. Open the app to continue.",
        )}
      </p>
      <a className="br-btn" href="/app">
        {t("Open app")}
      </a>
    </main>
  );
}

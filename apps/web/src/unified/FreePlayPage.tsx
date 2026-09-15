import { useState } from "react";
import { api, storylineApi, type Bootstrap } from "../api";
import { t } from "../localization";
import { companySelection, type Selection } from "./routing";
import { ChatPage } from "./ChatPage";
import { StorylineChatEvidence } from "./StorylineChatEvidence";
import { ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";

export function FreePlayPage({
  selection,
  bootstrap,
  navigate,
  openCompany,
}: {
  selection: Selection;
  bootstrap: Bootstrap;
  navigate: (changes: Partial<Selection>) => void;
  openCompany: (data: Bootstrap, id: string, options?: { announce?: boolean }) => void;
}) {
  const { data, loading, error, refresh } = useRead(() => storylineApi.freePlayEntry(), []);
  const [picked, setPicked] = useState(selection.tenant);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const selected = bootstrap.tenants.find((company) => company.id === picked);
  const current = bootstrap.tenants.find((company) => company.id === selection.tenant);
  const chatting = selection.freePlayChat && !!current;
  const isSandbox = (company: Bootstrap["tenants"][number]) =>
    company.company_kind === "sandbox" ||
    company.purpose === "playground" ||
    !!company.sandbox_run_id;
  const open = (tenant: string, updated = bootstrap) => {
    if (!updated.tenants.some((company) => company.id === tenant)) return;
    openCompany(updated, tenant, { announce: false });
    navigate({ ...companySelection(selection, tenant), route: "free-play", freePlayChat: true });
  };
  const start = async () => {
    setBusy(true);
    setFailure("");
    try {
      const result = await storylineApi.startFreePlay();
      if (result.status === "ready") open(result.tenant_id, await api.bootstrap());
      else {
        if (result.status !== "archived") setFailure(t("Sandbox setup is not ready. Try again."));
        refresh();
      }
    } catch (error) {
      setFailure((error as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section
      className="mx-auto flex h-[calc(100dvh-8rem)] min-h-[32rem] max-w-5xl flex-col overflow-hidden rounded-xl border border-border-default bg-surface"
      data-independent-free-play
    >
      <header className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-border-default p-4">
        <div>
          <h2 className="font-semibold">{t("Free play")}</h2>
          {chatting && (
            <p className="mt-1 text-sm text-fg-muted">
              {current.name} · {t(isSandbox(current) ? "Sandbox" : "Company")}
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {chatting && (
            <button
              className="br-btn"
              data-free-play-choose
              onClick={() => {
                setPicked(selection.tenant);
                navigate({ freePlayChat: false, session: "" });
              }}
            >
              {t("Choose company")}
            </button>
          )}
          <button
            className="br-btn"
            onClick={() =>
              navigate({ route: "storyline", storylineChapter: "library", freePlayChat: false })
            }
          >
            {t("Storylines")}
          </button>
        </div>
      </header>
      {failure && (
        <p role="alert" className="p-4 text-sm text-critical-text">
          {failure}
        </p>
      )}
      {chatting ? (
        <>
          {!isSandbox(current) && (
            <p className="px-4 pt-3 text-sm text-fg-muted" data-free-play-real-data>
              {t("You are working with this company's real data. Changes require confirmation.")}
            </p>
          )}
          <ChatPage
            key={selection.tenant}
            selection={{ ...selection, commitment: "" }}
            navigate={navigate}
            dock
            compact
            renderMessageEvidence={(messageId) => (
              <StorylineChatEvidence
                key={messageId}
                tenant={selection.tenant}
                messageId={messageId}
                navigate={navigate}
              />
            )}
          />
        </>
      ) : (
        <div className="overflow-y-auto p-6">
          <p className="mb-6 text-fg-muted">
            {t("Choose an existing company or create a Sandbox with sample data.")}
          </p>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="flex flex-col items-start gap-4 rounded-xl border border-border-default p-5">
              <label htmlFor="free-play-company" className="font-semibold">
                {t("Choose company")}
              </label>
              <select
                id="free-play-company"
                data-free-play-company
                className="w-full min-w-0 rounded-lg border border-border-default bg-surface p-3 text-fg"
                value={picked}
                onChange={(event) => setPicked(event.target.value)}
                disabled={busy}
              >
                {bootstrap.tenants.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.name} · {t(isSandbox(company) ? "Sandbox" : "Company")}
                  </option>
                ))}
              </select>
              {selected && !isSandbox(selected) && (
                <p className="text-sm text-fg-muted" data-free-play-real-data>
                  {t(
                    "You are working with this company's real data. Changes require confirmation.",
                  )}
                </p>
              )}
              <button
                className="br-btn br-btn-primary"
                data-free-play-open
                disabled={!selected || busy}
                onClick={() => selected && open(selected.id)}
              >
                {t("Open company chat")}
              </button>
            </div>
            <div className="flex flex-col items-start gap-4 rounded-xl border border-border-default p-5">
              <h3 className="font-semibold">{t("Sandbox with sample data")}</h3>
              <p className="text-sm text-fg-muted">
                {t("Explore freely in your own Sandbox with sample data.")}
              </p>
              {!data ? (
                <ReadState loading={loading} error={error} retry={refresh} />
              ) : data.available && data.status === "ready" ? (
                <button className="br-btn" disabled={busy} onClick={() => open(data.tenant_id)}>
                  {t("Open Free Play Sandbox")}
                </button>
              ) : data.available && data.status === "archived" ? (
                <p>{t("This Sandbox is archived. Restore it under Companies.")}</p>
              ) : (
                <button
                  className="br-btn"
                  disabled={busy || loading}
                  onClick={() => void start()}
                  data-free-play-start
                >
                  {busy ? t("Loading…") : t("Create Sandbox and start")}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

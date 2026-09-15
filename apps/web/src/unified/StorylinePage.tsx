import { useCallback, useEffect, useRef, useState } from "react";
import {
  APIError,
  api,
  storylineApi,
  type Bootstrap,
  type StorylineChapterDetail,
  type StorylineDelta,
  type StorylineImportError,
  type StorylineLibraryItem,
  type StorylineState,
  type StorylineStep,
  type StorylineTraceItem,
  type Tenant,
  type StorylineRun,
} from "../api";
import { t } from "../localization";
import type { Selection } from "./routing";
import { ArrowLeft, MoreHorizontal, Upload } from "lucide-react";
import { ReadState } from "./ReadState";
import { ChatPage } from "./ChatPage";
import { StorylineChatEvidence } from "./StorylineChatEvidence";
import { StorylineNarrator } from "./StorylineNarrator";
import { StorylineStage } from "./StorylineStage";
import { StorylineProtocol } from "./StorylineProtocol";
import {
  FREE_PLAY,
  LIBRARY,
  nextPresentationAction,
  phaseOf,
  pickText,
  PRESENTATION_BEATS,
  presentationPace,
  requestKey,
} from "./storylineState";

const panel = "rounded-xl border border-border-default bg-surface";

/**
 * Storyline (spec 182): narrator, the view a chapter names, and the protocol of
 * calls and delta. A company without a run shows the library; starting a run
 * creates a practice company and opens it.
 */
export function StorylinePage({
  selection,
  navigate,
  company,
  openCompany,
}: {
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
  company: Tenant;
  openCompany: (data: Bootstrap, id: string, options?: { announce?: boolean }) => void;
}) {
  const tenant = company.id;
  const [state, setState] = useState<StorylineState | null>(null);
  const [mode, setMode] = useState<"loading" | "library" | "play" | "error">("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const loadState = useCallback(async () => {
    try {
      const next = await storylineApi.state(tenant);
      setState(next);
      setMode("play");
    } catch (error) {
      if (error instanceof APIError && error.status === 404) setMode("library");
      else {
        setLoadError(error instanceof Error ? error.message : String(error));
        setMode("error");
      }
    }
  }, [tenant]);
  useEffect(() => {
    setState(null);
    setMode("loading");
    void loadState();
  }, [loadState]);
  if (mode === "loading") return <ReadState loading error={undefined} retry={loadState} />;
  if (mode === "error")
    return <ReadState loading={false} error={loadError || undefined} retry={loadState} />;
  if (mode === "library" || !state)
    return <Library openCompany={openCompany} navigate={navigate} />;
  if (selection.storylineChapter === LIBRARY)
    return (
      <Library
        openCompany={openCompany}
        navigate={navigate}
        backToStory={() => navigate({ storylineChapter: state.current_chapter || "" })}
      />
    );
  return (
    <Player
      key={state.run_id}
      tenant={tenant}
      state={state}
      reload={loadState}
      selection={selection}
      navigate={navigate}
      openCompany={openCompany}
    />
  );
}

function Library({
  openCompany,
  navigate,
  backToStory,
}: {
  openCompany: (data: Bootstrap, id: string, options?: { announce?: boolean }) => void;
  navigate: (changes: Partial<Selection>) => void;
  /** Set when the library was opened from a running storyline (browse other ones). */
  backToStory?: () => void;
}) {
  const [items, setItems] = useState<StorylineLibraryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [problems, setProblems] = useState<StorylineImportError[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [replace, setReplace] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const load = useCallback(() => {
    storylineApi
      .library()
      .then((result) => setItems(result.items))
      .catch((failure) => setError(failure instanceof Error ? failure.message : String(failure)));
  }, []);
  useEffect(load, [load]);
  const open = async (key: string, work: () => Promise<StorylineRun>) => {
    setBusy(key);
    setError(null);
    try {
      const run = await work();
      if (!run.tenant_id) throw new Error(t("The storyline sandbox could not be prepared."));
      openCompany(await api.bootstrap(), run.tenant_id, { announce: false });
      navigate({ route: "storyline", tenant: run.tenant_id, storylineChapter: "" });
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      setBusy(null);
    }
  };
  const start = (item: StorylineLibraryItem) =>
    open(item.key, async () =>
      item.run
        ? { ...item.run, key: item.key, version: item.version, error: null }
        : storylineApi.start(item.key, item.version, requestKey(item.key)),
    );
  const startOver = (item: StorylineLibraryItem) =>
    item.run &&
    open(item.key, () => storylineApi.restart(item.run!.tenant_id, requestKey("restart")));
  const importFile = async (file: File | null) => {
    if (!file) return;
    setBusy("import");
    setError(null);
    setProblems([]);
    setNotice(null);
    try {
      const result = await storylineApi.importPackage(file, replace);
      setNotice(
        `${t("Imported")}: ${pickText(result.title) || result.key} (${result.chapters} ${t("steps")})`,
      );
      if (result.warnings.length) setProblems(result.warnings);
      load();
    } catch (failure) {
      const detail = failure as APIError & { errors?: StorylineImportError[] };
      setError(detail.message);
      if (detail.errors) setProblems(detail.errors);
    } finally {
      setBusy(null);
    }
  };
  const remove = async (item: StorylineLibraryItem) => {
    setBusy(item.key);
    setError(null);
    try {
      await storylineApi.deletePackage(item.key, item.version);
      load();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      setBusy(null);
    }
  };
  if (!items) return <ReadState loading={!error} error={error || undefined} retry={load} />;
  return (
    <section className="mx-auto flex max-w-4xl flex-col gap-5" data-storyline-library>
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div className="max-w-2xl">
          <h2 className="text-lg font-semibold text-fg-strong">{t("Storylines")}</h2>
          <p className="mt-1 text-sm text-fg-muted">
            {t(
              "Guided business flows. Each one plays in a sandbox of its own, step by step, with the calls and the recorded changes beside it. Nothing here touches a real company.",
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {backToStory && (
            <button
              type="button"
              className="br-btn"
              data-storyline-action="back-to-story"
              onClick={backToStory}
            >
              <ArrowLeft size={15} />
              {t("Back to the storyline")}
            </button>
          )}
          <button
            type="button"
            className="br-btn"
            data-storyline-action="import"
            aria-expanded={importOpen}
            aria-controls="storyline-import"
            onClick={() => setImportOpen((value) => !value)}
          >
            <Upload size={15} />
            {t("Import")}
          </button>
        </div>
      </header>
      {error && (
        <p role="alert" className="rounded-md bg-critical-bg px-3 py-2 text-sm text-critical-text">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="rounded-md bg-positive-bg px-3 py-2 text-sm text-positive-text">
          {notice}
        </p>
      )}
      {problems.length > 0 && (
        <ul
          className="rounded-md border border-border-default bg-surface px-3 py-2 text-[12.5px]"
          data-storyline-import-problems
        >
          {problems.map((problem, index) => (
            <li key={index} className="grid grid-cols-[max-content_1fr] gap-x-3 py-0.5">
              <code className="text-[11.5px]">{problem.code}</code>
              <span data-localization="original">
                {problem.path ? `${problem.path}: ` : ""}
                {problem.detail}
              </span>
            </li>
          ))}
        </ul>
      )}
      {importOpen && (
        <form
          id="storyline-import"
          className={`${panel} grid gap-3 p-4 md:grid-cols-[minmax(0,1fr)_auto] md:items-end`}
          data-storyline-import
          onSubmit={(event) => event.preventDefault()}
        >
          <label className="text-sm">
            {t("Package file (YAML or JSON)")}
            <input
              id="storyline-import-file"
              type="file"
              accept=".yaml,.yml,.json,application/yaml,application/json"
              className="br-control mt-2 block w-full"
              disabled={busy !== null}
              onChange={(event) => void importFile(event.target.files?.[0] || null)}
            />
          </label>
          <label className="flex items-center gap-2 pb-2 text-sm">
            <input
              id="storyline-import-replace"
              type="checkbox"
              checked={replace}
              onChange={(event) => setReplace(event.target.checked)}
            />
            {t("Replace the same key and version")}
          </label>
          <p className="text-[12px] text-fg-muted md:col-span-2">
            {t(
              "A package file someone sent you. It is checked against the catalogs before anything is stored, and it runs under exactly the rules a built-in storyline runs under.",
            )}
          </p>
        </form>
      )}
      <div className="grid gap-4 md:grid-cols-2">
        {items.map((item) => (
          <StorylineCard
            key={`${item.key}:${item.version}`}
            item={item}
            busy={busy !== null}
            start={() => void start(item)}
            startOver={() => void startOver(item)}
            remove={() => void remove(item)}
          />
        ))}
      </div>
    </section>
  );
}

/** One storyline: what it is, where the person is in it, one primary action, the rest folded. */
function StorylineCard({
  item,
  busy,
  start,
  startOver,
  remove,
}: {
  item: StorylineLibraryItem;
  busy: boolean;
  start: () => void;
  startOver: () => void;
  remove: () => void;
}) {
  const run = item.run;
  const total = run?.total || item.chapters;
  const position = typeof run?.position === "number" ? run.position : null;
  const done = run?.done ?? 0;
  const finished = !!run && position === null && done >= total;
  const percent = run ? Math.min(100, Math.round((100 * done) / Math.max(total, 1))) : 0;
  return (
    <article className={`${panel} flex flex-col gap-3 p-4`} data-storyline-item={item.key}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-wider text-fg-muted">
            {item.chapters} {t("steps")}
            {item.origin === "import" ? ` · ${t("imported")}` : ""}
          </p>
          <h3 className="mt-0.5 text-base font-semibold text-fg-strong">{pickText(item.title)}</h3>
        </div>
        <CardMenu label={pickText(item.title)}>
          <a
            className="br-btn"
            href={storylineApi.exportUrl(item.key, item.version, "yaml")}
            data-storyline-download={item.key}
            download={`${item.key}.storyline.yaml`}
          >
            {t("Download")}
          </a>
          {run && (
            <a
              className="br-btn"
              href={storylineApi.draftUrl(run.run_id)}
              data-storyline-draft={item.key}
              download={`${item.key}-draft.storyline.yaml`}
              title={t(
                "Everything confirmed in this run, in order, as a storyline file with its texts still to be written.",
              )}
            >
              {t("Export as storyline draft")}
            </a>
          )}
          {run && (
            <button
              type="button"
              className="br-btn"
              data-storyline-start-over={item.key}
              disabled={busy}
              title={t("Opens a new sandbox at step 1. The current one stays as it is.")}
              onClick={startOver}
            >
              {t("Start over in a new sandbox")}
            </button>
          )}
          {item.origin === "import" && (
            <button
              type="button"
              className="br-btn"
              data-storyline-remove={item.key}
              disabled={busy}
              onClick={remove}
            >
              {t("Remove from library")}
            </button>
          )}
        </CardMenu>
      </div>
      <p className="text-sm text-fg-default">{pickText(item.summary)}</p>
      <div className="mt-auto flex flex-col gap-2 border-t border-border-subtle pt-3">
        {run ? (
          <>
            <div className="flex items-baseline justify-between gap-3 text-[12px] text-fg-muted">
              <span>
                {finished
                  ? t("Played to the end")
                  : position
                    ? `${t("Step")} ${position} / ${total}`
                    : t("In progress")}
              </span>
              {run.company_name && (
                <span className="truncate">
                  {t("Sandbox")}: <span data-localization="original">{run.company_name}</span>
                </span>
              )}
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-sunken">
              <div className="h-full rounded-full bg-accent" style={{ width: `${percent}%` }} />
            </div>
          </>
        ) : (
          <p className="text-[12px] text-fg-muted">{t("Opens a sandbox of its own for you.")}</p>
        )}
        <div>
          <button
            type="button"
            className="br-btn br-btn-primary"
            data-storyline-start={item.key}
            disabled={busy}
            onClick={start}
          >
            {run ? (finished ? t("Open") : t("Continue")) : t("Start")}
          </button>
        </div>
      </div>
    </article>
  );
}

function Player({
  tenant,
  state,
  reload,
  selection,
  navigate,
  openCompany,
}: {
  tenant: string;
  state: StorylineState;
  reload: () => Promise<void>;
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
  openCompany: (data: Bootstrap, id: string, options?: { announce?: boolean }) => void;
}) {
  const free = selection.storylineChapter === FREE_PLAY;
  const [freeDraft, setFreeDraft] = useState("");
  const chapterKey =
    (selection.storylineChapter && state.chapters.some((c) => c.key === selection.storylineChapter)
      ? selection.storylineChapter
      : state.current_chapter) || state.chapters[0]?.key;
  const [detail, setDetail] = useState<StorylineChapterDetail | null>(null);
  const [step, setStep] = useState<StorylineStep | null>(null);
  const [trace, setTrace] = useState<StorylineTraceItem[]>([]);
  const [delta, setDelta] = useState<StorylineDelta | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const generation = useRef(0);

  const loadChapter = useCallback(async () => {
    if (!chapterKey) return;
    const current = ++generation.current;
    try {
      const next = await storylineApi.chapter(tenant, chapterKey);
      if (current !== generation.current) return;
      setDetail(next);
      setStep(next.step);
      const stepId = next.step?.step_id;
      const [traceResult, deltaResult] = await Promise.all([
        storylineApi
          .trace(tenant, stepId)
          .catch(() => ({ items: [] as StorylineTraceItem[], has_more: false })),
        stepId && next.step && next.step.status !== "pending"
          ? storylineApi.delta(tenant, stepId).catch(() => null)
          : Promise.resolve(null),
      ]);
      if (current !== generation.current) return;
      setTrace(stepId ? traceResult.items : []);
      setDelta(deltaResult);
    } catch (failure) {
      if (current === generation.current)
        setError(failure instanceof Error ? failure.message : String(failure));
    }
  }, [tenant, chapterKey]);
  useEffect(() => {
    setDetail(null);
    setStep(null);
    setTrace([]);
    setDelta(null);
    setError(null);
    void loadChapter();
  }, [loadChapter]);

  // While a chapter is prepared, the protocol keeps up with what the person does
  // elsewhere; the HomePulse guards keep polling cheap and silent.
  useEffect(() => {
    if (phaseOf(step) !== "preview") return;
    let disposed = false,
      running = false;
    const refresh = async () => {
      if (disposed || running || document.hidden || !step?.step_id) return;
      running = true;
      try {
        const page = await storylineApi.trace(tenant, step.step_id);
        if (!disposed) setTrace(page.items);
      } catch {
        /* the next tick retries */
      }
      running = false;
    };
    const timer = window.setInterval(() => void refresh(), 10000);
    return () => {
      disposed = true;
      window.clearInterval(timer);
    };
  }, [tenant, step]);

  // Free play: the person works in the ordinary app; the protocol lists what they did
  // outside any chapter and shows what one confirmation added (FR-011).
  const [freeTrace, setFreeTrace] = useState<StorylineTraceItem[] | null>(null);
  const [picked, setPicked] = useState<StorylineTraceItem | null>(null);
  const [freeDelta, setFreeDelta] = useState<StorylineDelta | null>(null);
  useEffect(() => {
    if (!free) return;
    let disposed = false,
      running = false;
    const refresh = async () => {
      if (disposed || running || document.hidden) return;
      running = true;
      try {
        const page = await storylineApi.freeTrace(tenant);
        if (!disposed) setFreeTrace(page.items);
      } catch {
        if (!disposed) setFreeTrace((items) => items || []);
      }
      running = false;
    };
    void refresh();
    const timer = window.setInterval(() => void refresh(), 10000);
    return () => {
      disposed = true;
      window.clearInterval(timer);
    };
  }, [tenant, free]);
  useEffect(() => {
    if (!picked?.marker) {
      setFreeDelta(null);
      return;
    }
    let disposed = false;
    storylineApi
      .deltaAt(tenant, picked.ordinal)
      .then((result) => {
        if (!disposed) setFreeDelta(result);
      })
      .catch(() => {
        if (!disposed) setFreeDelta(null);
      });
    return () => {
      disposed = true;
    };
  }, [tenant, picked]);

  const act = async (work: () => Promise<StorylineStep | void>) => {
    setBusy(true);
    setError(null);
    try {
      await work();
      // Stay on the chapter that just ran so its explanation is read before the
      // story moves on; "Next step" is the only way forward.
      if (chapterKey && selection.storylineChapter !== chapterKey)
        navigate({ storylineChapter: chapterKey });
      await reload();
      await loadChapter();
      setRevision((value) => value + 1);
      window.dispatchEvent(new Event("reality:delivery-settled"));
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      setBusy(false);
    }
  };
  // Presentation mode (FR-013): the same prepare, confirm, branch and next calls a
  // person would click, on a timer; any interaction outside its own control pauses it,
  // and so does an error, so nothing is retried behind the presenter's back.
  const [presentation, setPresentation] = useState<"off" | "playing">("off");
  const [presentationNote, setPresentationNote] = useState<string | null>(null);
  const [autoplayPending, setAutoplayPending] = useState<{
    id: number;
    kind: "prepare" | "confirm" | "branch" | "next";
    ms: number;
  } | null>(null);
  const chosenBranch = detail ? state.branches[detail.chapter.key] || null : null;
  useEffect(() => {
    if (presentation !== "playing") return;
    if (error) {
      setPresentation("off");
      setPresentationNote("error");
      return;
    }
    const action = nextPresentationAction({
      detail,
      step,
      currentChapter: state.current_chapter,
      chosenBranch,
      busy,
    });
    if (!action) return;
    if (action.kind === "end") {
      setPresentation("off");
      setPresentationNote(action.reason);
      return;
    }
    const ms = PRESENTATION_BEATS[action.kind] * presentationPace();
    setAutoplayPending({ id: Date.now(), kind: action.kind, ms });
    const timer = window.setTimeout(() => {
      setAutoplayPending(null);
      if (action.kind === "prepare" && chapterKey)
        void act(() => storylineApi.prepare(tenant, chapterKey, requestKey(chapterKey)));
      else if (action.kind === "confirm" && step?.preview_revision && chapterKey)
        void act(() =>
          storylineApi.confirm(tenant, chapterKey, step.step_id, step.preview_revision!),
        );
      else if (action.kind === "branch" && chapterKey)
        void act(async () => {
          const result = await storylineApi.branch(tenant, chapterKey, action.branch);
          if (result.current_chapter) navigate({ storylineChapter: result.current_chapter });
        });
      else if (action.kind === "next") navigate({ storylineChapter: action.chapter });
    }, ms);
    return () => {
      window.clearTimeout(timer);
      setAutoplayPending(null);
    };
    // `act` is recreated every render; the inputs that matter are listed.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [presentation, detail, step, busy, error, state.current_chapter, chosenBranch, chapterKey]);
  useEffect(() => {
    if (presentation !== "playing") return;
    const pause = (event: Event) => {
      const target = event.target as Element | null;
      if (target?.closest?.("[data-storyline-presentation]")) return;
      setPresentation("off");
      setPresentationNote(null);
    };
    document.addEventListener("pointerdown", pause, true);
    document.addEventListener("keydown", pause, true);
    return () => {
      document.removeEventListener("pointerdown", pause, true);
      document.removeEventListener("keydown", pause, true);
    };
  }, [presentation]);
  const presentationNotes: Record<string, string> = {
    finished: t("The storyline has been played to the end."),
    blocked: t("Autoplay stopped: this step cannot run yet."),
    unresolved: t("Autoplay stopped: the outcome of a step is unknown."),
    later: t("Autoplay stopped: this step comes later in the storyline."),
    error: t("Autoplay stopped at an error."),
  };

  const chapter = detail?.chapter;
  const newIds = new Set([
    ...(delta?.records.map((record) => record.record_id) || []),
    ...(delta?.facts.map((fact) => fact.id) || []),
  ]);
  const backToStory = () =>
    navigate({ storylineChapter: state.current_chapter || state.chapters[0]?.key || "" });
  if (free) {
    const waiting = state.chapters.find((entry) => entry.key === state.current_chapter);
    return (
      <div
        className="grid gap-4 lg:h-[calc(100dvh-8.5rem)] lg:min-h-[40rem] lg:grid-cols-[minmax(0,1.25fr)_minmax(0,0.9fr)]"
        data-storyline-page
        data-storyline-run={state.run_id}
        data-storyline-free-play
      >
        <section className="flex h-[min(850px,85dvh)] min-h-[32rem] min-w-0 flex-col overflow-hidden rounded-xl border border-border-default bg-surface lg:h-auto lg:min-h-0">
          <header className="shrink-0 border-b border-border-default p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-semibold">{t("Free play")}</h2>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  className="br-btn"
                  data-storyline-action="back-to-story"
                  onClick={backToStory}
                >
                  {t("Back to the storyline")}
                </button>
                <button
                  type="button"
                  className="br-btn"
                  data-storyline-action="open-company"
                  onClick={() => navigate({ route: "home" })}
                >
                  {t("Open the company")}
                </button>
              </div>
            </div>
            {waiting && (
              <p className="mt-2 text-xs text-fg-muted">
                {t("The storyline waits at step")} “{pickText(waiting.title)}”.
              </p>
            )}
          </header>
          <ChatPage
            key={tenant}
            selection={{ ...selection, commitment: "" }}
            navigate={navigate}
            dock
            compact
            initialDraft={freeDraft}
            onInitialDraftUsed={() => setFreeDraft("")}
            renderMessageEvidence={(messageId) => (
              <StorylineChatEvidence
                key={messageId}
                tenant={tenant}
                messageId={messageId}
                navigate={navigate}
              />
            )}
          />
        </section>
        <div className="min-h-0 min-w-0 overflow-y-auto">
          <StorylineProtocol
            tenant={tenant}
            items={freeTrace || []}
            delta={freeDelta}
            loading={freeTrace === null}
            navigate={navigate}
            mode="free"
            onPick={setPicked}
            picked={picked?.ordinal ?? null}
          />
        </div>
      </div>
    );
  }
  return (
    <div
      /* The conversation is the widest column and runs the height of the screen;
         the view and the protocol stack beside it, so neither stands half empty. */
      className="grid gap-4 lg:h-[calc(100vh-8.5rem)] lg:min-h-[40rem] lg:grid-cols-[minmax(24rem,0.9fr)_minmax(0,1.25fr)]"
      data-storyline-page
      data-storyline-run={state.run_id}
    >
      <StorylineNarrator
        chapters={state.chapters}
        detail={detail}
        step={step}
        delta={delta}
        busy={busy}
        error={error}
        chosenBranch={chapter ? state.branches[chapter.key] || null : null}
        select={(key) => navigate({ storylineChapter: key })}
        prepare={() =>
          chapterKey &&
          void act(() => storylineApi.prepare(tenant, chapterKey, requestKey(chapterKey)))
        }
        confirm={() =>
          step?.preview_revision &&
          chapterKey &&
          void act(() =>
            storylineApi.confirm(tenant, chapterKey, step.step_id, step.preview_revision!),
          )
        }
        reject={() =>
          step &&
          chapterKey &&
          void act(() => storylineApi.reject(tenant, chapterKey, step.step_id))
        }
        chooseBranch={(branch) =>
          chapterKey &&
          void act(async () => {
            const result = await storylineApi.branch(tenant, chapterKey, branch);
            if (result.current_chapter) navigate({ storylineChapter: result.current_chapter });
          })
        }
        next={() => state.current_chapter && navigate({ storylineChapter: state.current_chapter })}
        freePlay={(draft = "") => {
          setFreeDraft(draft);
          navigate({ storylineChapter: FREE_PLAY });
        }}
        autoplay={presentation === "playing"}
        autoplayPending={presentation === "playing" ? autoplayPending : null}
        library={() => navigate({ storylineChapter: LIBRARY })}
        autoplayNote={presentationNote ? presentationNotes[presentationNote] || null : null}
        toggleAutoplay={() => {
          setPresentationNote(null);
          if (presentation === "playing") setPresentation("off");
          else {
            setError(null);
            setPresentation("playing");
          }
        }}
        restart={() =>
          void act(async () => {
            const run = await storylineApi.restart(tenant, requestKey("restart"));
            if (run.tenant_id) {
              openCompany(await api.bootstrap(), run.tenant_id, { announce: false });
              navigate({ route: "storyline", tenant: run.tenant_id, storylineChapter: "" });
            }
          })
        }
      />
      <div className="flex min-h-0 min-w-0 flex-col gap-4">
        <StorylineStage
          tenant={tenant}
          view={chapter?.view || null}
          label={chapter ? pickText(chapter.title) : ""}
          newIds={newIds}
          revision={revision}
          selection={selection}
          navigate={navigate}
        />
        <div className="min-h-0 shrink-0 overflow-y-auto">
          <StorylineProtocol
            tenant={tenant}
            items={trace}
            delta={delta}
            loading={!detail}
            navigate={navigate}
          />
        </div>
      </div>
    </div>
  );
}

/** The secondary actions of one card, folded behind one button; closes on outside click. */
function CardMenu({ label, children }: { label: string; children: React.ReactNode }) {
  const ref = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    const dismiss = (event: PointerEvent) => {
      if (ref.current?.open && !ref.current.contains(event.target as Node))
        ref.current.open = false;
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, []);
  return (
    <details ref={ref} className="relative shrink-0" data-storyline-menu>
      <summary
        className="grid size-8 cursor-pointer list-none place-items-center rounded-md text-fg-muted hover:bg-surface-muted [&::-webkit-details-marker]:hidden"
        aria-label={`${t("More actions")}: ${label}`}
        title={t("More actions")}
      >
        <MoreHorizontal size={17} />
      </summary>
      <div className="absolute right-0 top-full z-30 mt-1.5 flex min-w-56 flex-col gap-0.5 rounded-lg border border-border-default bg-surface p-1.5 shadow-lg [&>.br-btn]:justify-start [&>.br-btn]:border-transparent [&>.br-btn]:bg-transparent [&>.br-btn]:text-left">
        {children}
      </div>
    </details>
  );
}

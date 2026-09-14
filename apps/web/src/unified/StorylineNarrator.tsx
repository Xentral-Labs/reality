import type {
  StorylineChapterDetail,
  StorylineChapterEntry,
  StorylineDelta,
  StorylineStep,
} from "../api";
import { BookOpen, Infinity, Pause, Play } from "lucide-react";
import { useEffect, useRef } from "react";
import { formatDateTime, t } from "../localization";
import { compareFindings, phaseOf, pickText } from "./storylineState";

const panel = "rounded-xl border border-border-default bg-surface";
const toolState: Record<string, string> = { on: "bg-accent-soft text-accent", off: "" };
const toolButton =
  "flex flex-col items-center gap-1 rounded-lg px-2 py-2 text-[11.5px] leading-none text-fg-default hover:bg-surface-muted disabled:opacity-50 disabled:hover:bg-transparent";

export function StorylineNarrator({
  chapters,
  detail,
  step,
  delta,
  busy,
  error,
  chosenBranch,
  select,
  prepare,
  confirm,
  reject,
  chooseBranch,
  next,
  restart,
  freePlay,
  autoplay,
  autoplayNote,
  autoplayPending,
  toggleAutoplay,
  library,
}: {
  chapters: StorylineChapterEntry[];
  detail: StorylineChapterDetail | null;
  step: StorylineStep | null;
  delta: StorylineDelta | null;
  busy: boolean;
  error: string | null;
  chosenBranch: string | null;
  select: (key: string) => void;
  prepare: () => void;
  confirm: () => void;
  reject: () => void;
  chooseBranch: (branch: string) => void;
  next: () => void;
  restart: () => void;
  freePlay: () => void;
  /** Autoplay for a presentation (FR-013): the same calls, on a timer, until a click. */
  autoplay: boolean;
  autoplayNote: string | null;
  /** The move autoplay will make next and how long it waits, for the progress bar. */
  autoplayPending: {
    id: number;
    kind: "prepare" | "confirm" | "branch" | "next";
    ms: number;
  } | null;
  toggleAutoplay: () => void;
  library: () => void;
}) {
  const upNext: Record<"prepare" | "confirm" | "branch" | "next", string> = {
    prepare: t("Prepare this step"),
    confirm: t("Confirm"),
    branch: t("Take the default branch"),
    next: t("Next step"),
  };
  const chapter = detail?.chapter;
  const phase = phaseOf(step);
  const position = chapters.findIndex((entry) => entry.key === chapter?.key);
  const current = chapters.find((entry) => entry.status === "current");
  const isCurrent = !!chapter && current?.key === chapter.key;
  const expectations = chapter ? compareFindings(chapter.expect, delta?.exceptions || null) : null;
  const missing = detail?.preconditions.filter((check) => !check.holds) || [];
  const list = useRef<HTMLOListElement>(null);
  useEffect(() => {
    list.current?.querySelector('[aria-current="step"]')?.scrollIntoView({ block: "nearest" });
  }, [chapter?.key]);
  return (
    <div className="flex min-w-0 flex-col gap-3" data-storyline-narrator>
      {chapter && (
        <section className={`${panel} flex flex-col overflow-hidden`} data-storyline-chapter-card>
          {/* The content scrolls inside a fixed height; the actions below never move. */}
          <div
            className="flex h-[min(50vh,30rem)] flex-col gap-3 overflow-y-auto p-4"
            data-storyline-chapter-content
          >
            <p className="text-[11px] uppercase tracking-wider text-fg-muted">
              {t("Step")} {position + 1} / {chapters.length}
            </p>
            <h2 className="text-base font-semibold text-fg-strong">{pickText(chapter.title)}</h2>
            <p className="text-sm" data-storyline-situation>
              {pickText(chapter.situation)}
            </p>
            {error && (
              <p
                role="alert"
                className="rounded-md bg-critical-bg px-3 py-2 text-sm text-critical-text"
              >
                {error}
              </p>
            )}
            {phase === "idle" && isCurrent && missing.length > 0 && (
              <div
                className="rounded-md bg-caution-bg px-3 py-2 text-sm text-caution-text"
                data-storyline-missing
              >
                <p>{t("This step cannot run yet. Missing:")}</p>
                <ul className="mt-1 list-disc pl-5">
                  {missing.map((check) => (
                    <li key={check.kind + check.name} data-localization="original">
                      {check.kind === "reference" ? check.name : `${check.kind}: ${check.name}`}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {phase === "idle" && !isCurrent && (
              <p className="text-sm text-fg-muted">
                {position >= 0 && current && position > chapters.indexOf(current)
                  ? t("This step comes later in the storyline.")
                  : t("This step has not been played.")}
              </p>
            )}
            {phase === "preview" && step && (
              <div
                className="flex flex-col gap-2 rounded-lg border border-dashed border-accent bg-accent-soft p-3"
                data-storyline-preview
              >
                <p className="text-[11px] uppercase tracking-wider text-accent">
                  {t("Preview · nothing has happened yet")}
                </p>
                <dl
                  className="grid grid-cols-[max-content_minmax(0,1fr)] gap-x-3 gap-y-1 text-[13px]"
                  data-storyline-arguments
                >
                  {Object.entries(step.arguments || {})
                    .filter(([key]) => !key.startsWith("_"))
                    .map(([key, value]) => (
                      <div key={key} className="contents">
                        <dt className="text-fg-muted" data-localization="original">
                          {key}
                        </dt>
                        <dd
                          className="min-w-0 truncate font-mono text-[12px] text-fg-strong"
                          data-localization="original"
                        >
                          <ArgumentValue value={value} />
                        </dd>
                      </div>
                    ))}
                </dl>
              </div>
            )}
            {phase === "unresolved" && step?.error && (
              <div className="rounded-md bg-caution-bg px-3 py-2 text-sm text-caution-text">
                <p>
                  {t(
                    "The outcome of this step is unknown. Inspect the proposal before continuing.",
                  )}
                </p>
                <p className="mt-1 font-mono text-[12px]" data-localization="original">
                  {step.error.detail}
                </p>
              </div>
            )}
            {(phase === "done" || phase === "refused") && (
              <>
                {phase === "refused" && step?.refused && (
                  <div
                    className="rounded-md border-l-2 border-critical bg-critical-bg px-3 py-2 text-sm"
                    data-storyline-refused
                  >
                    <p className="font-medium text-critical-text">{t("Refused by the system")}</p>
                    <p className="mt-1 text-fg-default" data-localization="original">
                      {step.refused.detail}
                    </p>
                  </div>
                )}
                <div className="border-l-2 border-positive-text pl-3 text-[13.5px]">
                  <p className="mb-1 text-[11px] uppercase tracking-wider text-fg-muted">
                    {t("What happened")}
                  </p>
                  <p data-storyline-explain>{pickText(chapter.explain)}</p>
                </div>
                {expectations &&
                  (expectations.raised.length > 0 || expectations.cleared.length > 0) && (
                    <ul className="flex flex-col gap-1 text-[12.5px]" data-storyline-expectations>
                      {expectations.raised.map((item) => (
                        <li key={`r-${item.id}`} className="flex items-center gap-2">
                          <span className={item.met ? "text-positive-text" : "text-caution-text"}>
                            {item.met ? "✓" : "?"}
                          </span>
                          <span>{t("Expected to be raised")}:</span>
                          <code className="text-[11.5px]">{item.id}</code>
                        </li>
                      ))}
                      {expectations.cleared.map((item) => (
                        <li key={`c-${item.id}`} className="flex items-center gap-2">
                          <span className={item.met ? "text-positive-text" : "text-caution-text"}>
                            {item.met ? "✓" : "?"}
                          </span>
                          <span>{t("Expected to be cleared")}:</span>
                          <code className="text-[11.5px]">{item.id}</code>
                        </li>
                      ))}
                    </ul>
                  )}
                {chapter.branches.length > 0 && (
                  <div className="grid gap-1.5" data-storyline-branches>
                    <p className="text-[11px] uppercase tracking-wider text-fg-muted">
                      {t("How does it continue?")}
                    </p>
                    {chapter.branches.map((branch) => (
                      <button
                        key={branch.key}
                        type="button"
                        data-storyline-branch={branch.key}
                        aria-pressed={
                          (chosenBranch || defaultBranch(chapter.branches)) === branch.key
                        }
                        disabled={busy}
                        onClick={() => chooseBranch(branch.key)}
                        className="rounded-lg border border-border-default px-3 py-2 text-left text-[13px] hover:border-accent aria-pressed:border-accent aria-pressed:bg-accent-soft"
                      >
                        {pickText(branch.label)}
                      </button>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
          {/* The action panel: one place for the next move, whatever the step shows above. */}
          <div
            className="flex flex-col gap-2 border-t border-border-subtle bg-surface-sunken/60 px-4 py-3"
            data-storyline-actions
          >
            <div className="flex min-h-9 flex-wrap items-center gap-2">
              {phase === "idle" && isCurrent && missing.length === 0 && (
                <button
                  type="button"
                  className="br-btn br-btn-primary"
                  data-storyline-action="prepare"
                  disabled={busy}
                  onClick={prepare}
                >
                  {chapter.kind === "read" ? t("Read") : t("Prepare this step")}
                </button>
              )}
              {phase === "idle" && isCurrent && missing.length > 0 && (
                <button
                  type="button"
                  className="br-btn"
                  data-storyline-action="restart"
                  onClick={restart}
                >
                  {t("Start over in a new sandbox")}
                </button>
              )}
              {phase === "idle" && !isCurrent && current && (
                <button
                  type="button"
                  className="br-btn"
                  data-storyline-action="go-current"
                  onClick={() => select(current.key)}
                >
                  {t("Go to the current step")}
                </button>
              )}
              {phase === "preview" && step && (
                <>
                  <button
                    type="button"
                    className="br-btn br-btn-primary"
                    data-storyline-action="confirm"
                    disabled={busy}
                    onClick={confirm}
                  >
                    {t("Confirm")}
                  </button>
                  <button
                    type="button"
                    className="br-btn"
                    data-storyline-action="reject"
                    disabled={busy}
                    onClick={reject}
                  >
                    {t("Discard")}
                  </button>
                </>
              )}
              {(phase === "done" || phase === "refused") &&
                current &&
                current.key !== chapter.key && (
                  <button
                    type="button"
                    className="br-btn br-btn-primary"
                    data-storyline-action="next"
                    onClick={next}
                  >
                    {t("Next step")}
                  </button>
                )}
              {(phase === "done" || phase === "refused") && !current && (
                <button
                  type="button"
                  className="br-btn"
                  data-storyline-action="restart"
                  onClick={restart}
                >
                  {t("Start over in a new sandbox")}
                </button>
              )}
            </div>
          </div>
        </section>
      )}
      {/* Transport controls: one box, same size buttons, the running state visible. */}
      <div className={`${panel} flex flex-col`} data-storyline-toolbar>
        <div className="grid grid-cols-3 gap-1 p-1.5">
          <button
            type="button"
            className={`${toolButton} ${toolState[autoplay ? "on" : "off"]}`}
            data-storyline-action={autoplay ? "pause" : "present"}
            data-storyline-presentation={autoplay ? "playing" : "off"}
            data-storyline-presentation-note={autoplayNote ? "" : undefined}
            aria-pressed={autoplay}
            disabled={!current}
            title={autoplay ? t("Stop autoplay") : t("Play automatically")}
            onClick={toggleAutoplay}
          >
            {autoplay ? <Pause size={17} /> : <Play size={17} />}
            <span>{autoplay ? t("Stop") : t("Autoplay")}</span>
          </button>
          <button
            type="button"
            className={toolButton}
            data-storyline-action="free-play"
            title={t("You are working in the sandbox itself.")}
            onClick={freePlay}
          >
            <Infinity size={17} />
            <span>{t("Free play")}</span>
          </button>
          <button
            type="button"
            className={toolButton}
            data-storyline-action="library"
            title={t("Other storylines")}
            onClick={library}
          >
            <BookOpen size={17} />
            <span>{t("Library")}</span>
          </button>
        </div>
        {autoplay && autoplayPending && (
          <div
            className="flex flex-col gap-1 border-t border-border-subtle px-2.5 pt-1.5 pb-2"
            data-storyline-autoplay-progress={autoplayPending.kind}
          >
            <div className="flex items-baseline justify-between gap-2 text-[11.5px]">
              <span className="text-fg-muted">{t("Up next")}</span>
              <span className="font-medium text-fg-strong">{upNext[autoplayPending.kind]}</span>
            </div>
            <div className="h-1 w-full overflow-hidden rounded-full bg-surface-sunken">
              <div
                key={autoplayPending.id}
                className="storyline-fill h-full w-full origin-left rounded-full bg-accent"
                style={{ animationDuration: `${autoplayPending.ms}ms` }}
              />
            </div>
          </div>
        )}
        {autoplay && !autoplayPending && (
          <p className="border-t border-border-subtle px-2.5 py-1.5 text-[11.5px] text-fg-muted">
            {t("Runs on its own. Any click stops it.")}
          </p>
        )}
        {!autoplay && autoplayNote && (
          <p className="border-t border-border-subtle px-2.5 py-1.5 text-[11.5px] text-fg-muted">
            {autoplayNote}
          </p>
        )}
      </div>
      <nav aria-label={t("Steps")} className={`${panel} p-2`}>
        {/* About five rows; the current chapter is rolled into view (owner review). */}
        <ol ref={list} className="flex max-h-[13.25rem] flex-col gap-0.5 overflow-y-auto">
          {chapters.map((entry, index) => (
            <li key={entry.key}>
              <button
                type="button"
                data-storyline-chapter={entry.key}
                data-status={entry.status}
                aria-current={entry.key === chapter?.key ? "step" : undefined}
                onClick={() => select(entry.key)}
                className="grid w-full grid-cols-[22px_1fr_auto] items-center gap-2 rounded-md px-2 py-1.5 text-left text-[13px] text-fg-muted hover:bg-surface-muted aria-[current=step]:bg-accent-soft aria-[current=step]:font-medium aria-[current=step]:text-fg-strong"
              >
                <span
                  data-done={entry.status === "done"}
                  className="grid size-5 place-items-center rounded-full border border-border-strong font-mono text-[11px] data-[done=true]:border-transparent data-[done=true]:bg-positive-text data-[done=true]:text-white"
                >
                  {entry.status === "done" ? "✓" : index + 1}
                </span>
                <span className="truncate">{pickText(entry.title)}</span>
                <span className="text-[11px] text-fg-quiet">
                  {entry.kind === "read" ? t("read") : ""}
                </span>
              </button>
            </li>
          ))}
        </ol>
      </nav>
    </div>
  );
}

function defaultBranch(branches: Array<{ key: string; default: boolean }>): string | null {
  return branches.find((branch) => branch.default)?.key || null;
}

const ISO_INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/;

/** One argument, kept to one line: instants formatted, nested values behind a summary. */
function ArgumentValue({ value }: { value: unknown }) {
  if (value === null || value === undefined) return <span className="text-fg-quiet">–</span>;
  if (Array.isArray(value) || typeof value === "object") {
    const count = Array.isArray(value) ? value.length : Object.keys(value as object).length;
    return (
      <details className="inline-block max-w-full align-top">
        <summary className="cursor-pointer text-accent">
          {count} {Array.isArray(value) ? t("entries") : t("fields")}
        </summary>
        <pre className="mt-1 max-h-32 overflow-auto whitespace-pre-wrap break-all rounded-md bg-surface-sunken p-2 text-[11px] leading-snug">
          {JSON.stringify(value, null, 1)}
        </pre>
      </details>
    );
  }
  if (typeof value === "string" && ISO_INSTANT.test(value)) {
    const parsed = new Date(value);
    if (!Number.isNaN(parsed.getTime())) return <span title={value}>{formatDateTime(value)}</span>;
  }
  return <span title={String(value)}>{String(value)}</span>;
}

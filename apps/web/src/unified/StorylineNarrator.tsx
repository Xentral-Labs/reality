import type {
  StorylineChapterDetail,
  StorylineChapterEntry,
  StorylineDelta,
  StorylineStep,
  StorylineText,
} from "../api";
import { BookOpen, Infinity, List, Pause, Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { formatDateTime, t } from "../localization";
import { compareFindings, phaseOf, pickText } from "./storylineState";

const panel = "rounded-xl border border-border-default bg-surface";
const toolState: Record<string, string> = { on: "bg-accent-soft text-accent", off: "" };
const toolButton =
  "grid size-8 place-items-center rounded-lg text-fg-muted hover:bg-surface-muted hover:text-fg-default disabled:opacity-40 disabled:hover:bg-transparent";
/** What the person says sits on the right; what Reality answers on the left. */
const mine =
  "max-w-[85%] self-end rounded-xl rounded-br-sm border border-accent/40 bg-accent-soft px-3 py-2 text-[13.5px] text-fg-strong";
const theirs =
  "flex max-w-[92%] flex-col gap-1.5 self-start rounded-xl rounded-bl-sm bg-surface-muted px-3 py-2 text-[13.5px]";
const exitButton =
  "inline-flex items-center gap-1.5 rounded-lg border border-border-default px-2.5 py-1.5 text-[12.5px] text-fg-muted hover:border-border-strong hover:text-fg-default";
const findingTone: Record<string, string> = {
  met: "bg-positive-bg text-positive-text",
  open: "bg-caution-bg text-caution-text",
};

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
  freePlay: (draft?: string) => void;
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
  const thread = useRef<HTMLDivElement>(null);
  // The composer holds the suggested line. Changing it is leaving the script.
  const suggested = chapter ? spokenLine(chapter.say, chapter.title) : "";
  const [typed, setTyped] = useState("");
  const own = typed.trim().length > 0;
  const composing = phase === "idle" && isCurrent && missing.length === 0;
  useEffect(() => {
    setTyped("");
  }, [chapter?.key]);
  useEffect(() => {
    list.current?.querySelector('[aria-current="step"]')?.scrollIntoView({ block: "nearest" });
  }, [chapter?.key]);
  // A conversation is read from the bottom: the newest turn is the one in hand.
  useEffect(() => {
    const node = thread.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [chapter?.key, phase]);

  // Everything played so far, the step in hand, and an upcoming chapter somebody
  // opened from the list. The selected turn is the one told in full.
  const told = chapters.filter((entry) => entry.status === "done" || entry.key === chapter?.key);

  return (
    <div
      className="flex min-h-0 min-w-0 flex-col gap-3 lg:h-full"
      data-storyline-narrator
      data-storyline-current-chapter={current?.key || undefined}
    >
      {chapter && (
        <section
          className={`${panel} flex min-h-0 flex-1 flex-col overflow-hidden`}
          data-storyline-chapter-card
        >
          {/* One header for where you are, the transport and the chapter list. */}
          <div className="flex flex-col border-b border-border-subtle">
            <div className="flex items-center gap-2 px-4 py-2">
              <p className="shrink-0 text-[11px] uppercase tracking-wider text-fg-muted">
                {t("Step")} {position + 1} / {chapters.length}
              </p>
              <h2 className="min-w-0 truncate text-[13.5px] font-semibold text-fg-strong">
                {pickText(chapter.title)}
              </h2>
              <div className="ml-auto flex shrink-0 items-center gap-0.5">
                <button
                  type="button"
                  className={`${toolButton} ${toolState[autoplay ? "on" : "off"]}`}
                  data-storyline-action={autoplay ? "pause" : "present"}
                  data-storyline-presentation={autoplay ? "playing" : "off"}
                  data-storyline-presentation-note={autoplayNote ? "" : undefined}
                  aria-pressed={autoplay}
                  aria-label={autoplay ? t("Stop autoplay") : t("Play automatically")}
                  disabled={!current}
                  title={autoplay ? t("Stop autoplay") : t("Play automatically")}
                  onClick={toggleAutoplay}
                >
                  {autoplay ? <Pause size={16} /> : <Play size={16} />}
                </button>
                <ChapterMenu chapters={chapters} open={chapter.key} select={select} list={list} />
              </div>
            </div>
            {autoplay && autoplayPending && (
              <div
                className="flex flex-col gap-1 border-t border-border-subtle px-4 pt-1.5 pb-2"
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
              <p className="border-t border-border-subtle px-4 py-1.5 text-[11.5px] text-fg-muted">
                {t("Runs on its own. Any click stops it.")}
              </p>
            )}
            {!autoplay && autoplayNote && (
              <p className="border-t border-border-subtle px-4 py-1.5 text-[11.5px] text-fg-muted">
                {autoplayNote}
              </p>
            )}
          </div>
          {/* The conversation scrolls inside a fixed height; the composer never moves. */}
          <div
            className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4"
            data-storyline-chapter-content
            ref={thread}
          >
            {told.map((entry) =>
              entry.key === chapter.key ? (
                <div key={entry.key} className="flex flex-col gap-2" data-storyline-turn="open">
                  {phase !== "idle" && <p className={mine}>{suggested}</p>}
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
                            {check.kind === "reference"
                              ? check.name
                              : `${check.kind}: ${check.name}`}
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
                      className="flex max-w-[92%] flex-col gap-2 self-start rounded-xl rounded-bl-sm border border-dashed border-accent bg-accent-soft p-3"
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
                      <div
                        className={
                          phase === "refused"
                            ? `${theirs} bg-critical-bg text-critical-text`
                            : theirs
                        }
                        data-storyline-refused={phase === "refused" ? "" : undefined}
                      >
                        <p className="font-medium">
                          {phase === "refused" ? t("Refused by the system") : t("Recorded")}
                        </p>
                        {phase === "refused" && step?.refused && (
                          <p data-localization="original">{step.refused.detail}</p>
                        )}
                        {expectations &&
                          (expectations.raised.length > 0 || expectations.cleared.length > 0) && (
                            <ul
                              className="flex flex-wrap gap-1.5 text-[12px]"
                              data-storyline-expectations
                            >
                              {expectations.raised.map((item) => (
                                <Finding key={`r-${item.id}`} id={item.id} met={item.met} raised />
                              ))}
                              {expectations.cleared.map((item) => (
                                <Finding key={`c-${item.id}`} id={item.id} met={item.met} />
                              ))}
                            </ul>
                          )}
                      </div>
                      <Why text={pickText(chapter.explain)} open />
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
              ) : (
                <PastTurn
                  key={entry.key}
                  entry={entry}
                  position={chapters.indexOf(entry) + 1}
                  select={select}
                />
              ),
            )}
          </div>
          {/* The composer: the line to send, and whatever the step asks for next. */}
          <div
            className="flex flex-col gap-2 border-t border-border-subtle bg-surface-sunken/60 px-4 py-3"
            data-storyline-actions
          >
            {composing && (
              <>
                {/* Somebody beside you, telling you what to ask. Take it and it
                    goes up into the conversation as your own message. */}
                <div
                  className="flex flex-col gap-2 rounded-lg border border-dashed border-border-strong p-3"
                  data-storyline-suggestion
                >
                  <p className="text-[11px] uppercase tracking-wider text-fg-muted">
                    {t("You could say")}
                  </p>
                  <p className="text-[12.5px] text-fg-muted" data-storyline-situation>
                    {pickText(chapter.situation)}
                  </p>
                  <div className="flex flex-wrap items-center justify-end gap-2">
                    <p className={`${mine} self-stretch border-dashed opacity-80`}>{suggested}</p>
                    <button
                      type="button"
                      className="br-btn br-btn-primary"
                      data-storyline-action="prepare"
                      disabled={busy}
                      onClick={prepare}
                    >
                      {t("Use this")}
                    </button>
                  </div>
                </div>
                <div className="flex items-end gap-2">
                  <label className="sr-only" htmlFor="storyline-say">
                    {t("Your message")}
                  </label>
                  <textarea
                    id="storyline-say"
                    rows={1}
                    spellCheck={false}
                    value={typed}
                    disabled={busy}
                    placeholder={t("Write your own message")}
                    onChange={(event) => setTyped(event.target.value)}
                    data-storyline-say
                    className="min-w-0 flex-1 resize-none rounded-lg border border-border-default bg-surface-muted px-3 py-2 text-[13.5px] text-fg-strong placeholder:text-fg-quiet focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
                  />
                  <button
                    type="button"
                    className="br-btn"
                    data-storyline-action="own-words"
                    disabled={!own}
                    onClick={() => freePlay(typed)}
                  >
                    {t("Send")}
                  </button>
                </div>
                {own && (
                  <p className="text-[11.5px] text-fg-muted" data-storyline-say-hint="true">
                    {t("Your own words. Continue in the sandbox itself.")}
                  </p>
                )}
              </>
            )}
            <div className="flex min-h-9 flex-wrap items-center gap-2">
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
              {/* The ways out, named rather than hidden behind an icon. */}
              <div className="ms-auto flex items-center gap-1">
                <button
                  type="button"
                  className={exitButton}
                  data-storyline-action="free-play"
                  title={t("You are working in the sandbox itself.")}
                  onClick={() => freePlay()}
                >
                  <Infinity size={14} />
                  {t("Free play")}
                </button>
                <button
                  type="button"
                  className={exitButton}
                  data-storyline-action="library"
                  title={t("Other storylines")}
                  onClick={library}
                >
                  <BookOpen size={14} />
                  {t("Library")}
                </button>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

/** The chapter list, folded away. The conversation shows what already happened;
 *  this is for jumping to a chapter that has not been played yet. */
function ChapterMenu({
  chapters,
  open,
  select,
  list,
}: {
  chapters: StorylineChapterEntry[];
  open: string;
  select: (key: string) => void;
  list: React.RefObject<HTMLOListElement | null>;
}) {
  const box = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    const dismiss = (event: PointerEvent) => {
      if (box.current?.open && !box.current.contains(event.target as Node))
        box.current.open = false;
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, []);
  return (
    <details ref={box} className="relative" data-storyline-chapters>
      <summary
        className={`${toolButton} cursor-pointer list-none`}
        aria-label={t("Steps")}
        title={t("Steps")}
      >
        <List size={16} />
      </summary>
      <nav
        aria-label={t("Steps")}
        className="absolute end-0 z-20 mt-1 w-[19rem] max-w-[80vw] rounded-xl border border-border-default bg-surface p-2 shadow-lg"
      >
        <ol ref={list} className="flex max-h-[19rem] flex-col gap-0.5 overflow-y-auto">
          {chapters.map((entry, index) => (
            <li key={entry.key}>
              <button
                type="button"
                data-storyline-chapter={entry.key}
                data-status={entry.status}
                aria-current={entry.key === open ? "step" : undefined}
                onClick={() => {
                  if (box.current) box.current.open = false;
                  select(entry.key);
                }}
                className="grid w-full grid-cols-[22px_1fr_auto] items-center gap-2 rounded-md px-2 py-1.5 text-left text-[13px] text-fg-muted hover:bg-surface-muted aria-[current=step]:bg-accent-soft aria-[current=step]:font-medium aria-[current=step]:text-fg-strong"
              >
                <span
                  data-done={entry.status === "done"}
                  className="grid size-5 place-items-center rounded-full border border-border-strong font-mono text-[11px] data-[done=true]:border-transparent data-[done=true]:bg-positive-text data-[done=true]:text-white"
                >
                  {entry.status === "done" ? "\u2713" : index + 1}
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
    </details>
  );
}

/** A turn that already happened: what was said, how it ended, why on request. */
function PastTurn({
  entry,
  position,
  select,
}: {
  entry: StorylineChapterEntry;
  position: number;
  select: (key: string) => void;
}) {
  const refused = entry.step_status === "refused";
  if (!entry.step_id) return null;
  return (
    <div className="flex flex-col gap-1.5 opacity-80" data-storyline-turn="past">
      <p className={mine}>{spokenLine(entry.say, entry.title)}</p>
      <div className={refused ? `${theirs} bg-critical-bg text-critical-text` : theirs}>
        <button
          type="button"
          onClick={() => select(entry.key)}
          data-storyline-turn-open={entry.key}
          className="text-left font-medium hover:underline"
        >
          {refused ? t("Refused by the system") : t("Recorded")}
        </button>
      </div>
      <Why text={pickText(entry.explain)} position={position} />
    </div>
  );
}

/** The explanation. Long enough that a conversation keeps it one click away. */
function Why({ text, open, position }: { text: string; open?: boolean; position?: number }) {
  if (!text) return null;
  return (
    <details
      open={open}
      className="max-w-[92%] self-start rounded-xl border border-border-subtle px-3 py-2"
      data-storyline-why={position ? String(position) : undefined}
    >
      <summary className="cursor-pointer text-[11px] uppercase tracking-wider text-fg-muted">
        {t("What happened")}
      </summary>
      <p className="mt-1 text-[13px]" data-storyline-explain>
        {text}
      </p>
    </details>
  );
}

function Finding({ id, met, raised }: { id: string; met: boolean; raised?: boolean }) {
  return (
    <li
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 ${findingTone[met ? "met" : "open"]}`}
    >
      {/* The tick answers one question: did what the chapter announced happen? */}
      <span aria-hidden="true">{met ? "✓" : "?"}</span>
      <span className="sr-only">
        {raised ? t("Expected to be raised") : t("Expected to be cleared")}
      </span>
      <code className="text-[11px]">{id}</code>
    </li>
  );
}

/** What the person says. Without a `say` line the chapter title has to do. */
function spokenLine(say: StorylineText | null | undefined, title: StorylineText): string {
  return pickText(say) || pickText(title);
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

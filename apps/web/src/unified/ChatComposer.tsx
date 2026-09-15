import {
  useEffect,
  useRef,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from "react";
import { ArrowUp, Mic, Paperclip, Square } from "lucide-react";
import type { ManagedAllowance } from "../api";
import { formatDateTime, t } from "../localization";

type Recognition = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onresult:
    | ((event: {
        resultIndex?: number;
        results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }>;
      }) => void)
    | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};
export function ChatComposer({
  id,
  value,
  change,
  sending,
  active,
  send,
  allowance,
  disclaimerAction,
}: {
  id: string;
  value: string;
  change: Dispatch<SetStateAction<string>>;
  sending: boolean;
  active: boolean;
  send: () => void;
  allowance?: ManagedAllowance | null;
  disclaimerAction?: ReactNode;
}) {
  const exhausted = allowance?.remaining === 0;
  const fileInput = useRef<HTMLInputElement>(null);
  const draftValue = useRef(value);
  draftValue.current = value;
  const tooLong = Array.from(value).length > 4000;
  const recognition = useRef<Recognition | null>(null);
  const generation = useRef(0);
  const [listening, setListening] = useState(false);
  const [reading, setReading] = useState(false);
  const [notice, setNotice] = useState("");
  const stop = () => {
    recognition.current?.stop();
  };
  useEffect(() => {
    const current = ++generation.current;
    if (!active || sending) {
      recognition.current?.abort();
      setListening(false);
    }
    return () => {
      if (generation.current === current) generation.current++;
      const speech = recognition.current;
      if (speech) {
        speech.onstart = speech.onend = speech.onerror = speech.onresult = null;
        speech.abort();
        recognition.current = null;
      }
    };
  }, [active, sending]);
  const dictate = () => {
    if (listening) {
      stop();
      return;
    }
    setNotice("");
    const browser = window as typeof window & {
      SpeechRecognition?: new () => Recognition;
      webkitSpeechRecognition?: new () => Recognition;
    };
    const Native = browser.SpeechRecognition || browser.webkitSpeechRecognition;
    if (!Native) {
      setNotice(t("Voice input is unavailable in this browser."));
      return;
    }
    const speech = new Native();
    recognition.current = speech;
    speech.lang = document.documentElement.lang || "en";
    speech.continuous = true;
    speech.interimResults = false;
    speech.onstart = () => setListening(true);
    speech.onend = () => setListening(false);
    speech.onerror = () => {
      setListening(false);
      setNotice(t("Voice input stopped. Check microphone access or type your message."));
    };
    speech.onresult = (event) => {
      const parts: string[] = [];
      for (let i = event.resultIndex || 0; i < event.results.length; i++)
        if (event.results[i].isFinal) parts.push(event.results[i][0].transcript);
      if (parts.length) change((previous) => [previous, parts.join(" ")].filter(Boolean).join(" "));
    };
    try {
      speech.start();
    } catch {
      setNotice(t("Voice input could not start."));
    }
  };
  return (
    <div className="shrink-0 px-4 pb-3 pt-2">
      <AllowanceNotice allowance={allowance} />
      {tooLong && (
        <p role="alert" className="mb-2 text-xs text-critical-text">
          {t("Keep the message within 4,000 characters.")}
        </p>
      )}
      {notice && (
        <p role="alert" className="mb-2 text-xs text-critical-text">
          {notice}
        </p>
      )}
      {listening && (
        <p role="status" className="mb-2 text-xs text-accent">
          {t("Listening… Your words will appear in the draft.")}
        </p>
      )}
      <form
        className="reality-chat-composer"
        onSubmit={(event) => {
          event.preventDefault();
          if (!exhausted && !reading && !sending && !tooLong && value.trim()) {
            stop();
            send();
          }
        }}
      >
        <label htmlFor={id} className="sr-only">
          {t("Ask about your company")}
        </label>
        <textarea
          id={id}
          value={value}
          readOnly={sending}
          aria-busy={sending}
          placeholder={t("Put Reality to work…")}
          onChange={(event) => change(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
              event.preventDefault();
              if (!exhausted && !reading && !sending && !tooLong && value.trim()) {
                stop();
                send();
              }
            }
          }}
        />
        <div className="flex items-center justify-between px-3 pb-3">
          <button
            type="button"
            className="reality-chat-icon"
            aria-label={t("Attach text file")}
            title={t("Attach a text, Markdown, CSV or JSON file (up to 64 KiB)")}
            disabled={sending || reading}
            onClick={() => fileInput.current?.click()}
          >
            <Paperclip size={21} />
          </button>
          <input
            ref={fileInput}
            type="file"
            className="hidden"
            accept=".txt,.md,.csv,.json,text/plain,text/markdown,text/csv,application/json"
            onChange={async (event) => {
              const file = event.target.files?.[0];
              event.target.value = "";
              if (!file) return;
              setNotice("");
              if (!/\.(txt|md|csv|json)$/i.test(file.name) || file.size > 65536) {
                setNotice(t("Choose a text, Markdown, CSV or JSON file up to 64 KiB."));
                return;
              }
              const current = generation.current;
              setReading(true);
              try {
                const text = new TextDecoder("utf-8", { fatal: true }).decode(
                  await file.arrayBuffer(),
                );
                if (generation.current !== current) return;
                if (text.includes("\u0000")) throw new Error("Binary content");
                const candidate = `${draftValue.current}${draftValue.current ? "\n\n" : ""}${file.name}\n${text}`;
                if (Array.from(candidate).length > 4000) {
                  setNotice(t("This file would exceed the 4,000-character message limit."));
                  return;
                }
                change((previous) => `${previous}${previous ? "\n\n" : ""}${file.name}\n${text}`);
              } catch {
                if (generation.current === current)
                  setNotice(t("This file could not be read as UTF-8 text."));
              } finally {
                setReading(false);
              }
            }}
          />
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="reality-chat-icon"
              aria-label={t(listening ? "Stop dictation" : "Dictate")}
              aria-pressed={listening}
              title={t("Dictate using your browser's speech service")}
              disabled={sending}
              onClick={dictate}
            >
              {listening ? <Square size={18} className="text-accent" /> : <Mic size={21} />}
            </button>
            <button
              type="submit"
              className="reality-chat-send"
              aria-label={t("Send question")}
              disabled={exhausted || sending || reading || tooLong || !value.trim()}
            >
              <ArrowUp size={23} />
            </button>
          </div>
        </div>
      </form>
      <div className="mt-3 flex flex-wrap items-center justify-center gap-2 px-2 text-center text-xs leading-5 text-fg-muted">
        <span>{t("Reality can make mistakes. Check important information.")}</span>
        {disclaimerAction}
      </div>
    </div>
  );
}

export function AllowanceNotice({ allowance }: { allowance?: ManagedAllowance | null }) {
  if (!allowance || allowance.remaining !== 0) return null;
  const count = t("{remaining} of {limit} AI questions left")
    .replace("{remaining}", String(allowance.remaining))
    .replace("{limit}", String(allowance.limit));
  const reset = (
    <p className="mt-2">
      {t("Resets at")} {formatDateTime(allowance.resets_at)}
    </p>
  );
  return (
    <div className="mb-3 text-xs text-fg-muted" data-ai-allowance>
      <div
        role="status"
        className="rounded-xl border border-border-default bg-surface-muted px-3 py-2"
      >
        <p className="font-medium text-fg-strong">{count}</p>
        <p className="mt-1">
          {t(
            "Your daily AI allowance is used. Keep exploring the records or return after the reset.",
          )}
        </p>
        {reset}
      </div>
    </div>
  );
}

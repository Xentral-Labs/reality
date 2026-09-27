import { useEffect, useState, type FormEvent } from "react";

import {
  journeyProposalApi,
  type JourneyProposal,
  type JourneyProposalInput,
  type JourneyProposalPreview,
} from "../api";
import { t } from "../localization";

const empty: JourneyProposalInput = {
  title: "",
  business_question: "",
  expected_outcome: "",
  process_area: "receiving",
  business_context: "",
  confirmed: false,
};

export function JourneySuggestions() {
  const [rows, setRows] = useState<JourneyProposal[]>([]);
  const [form, setForm] = useState(empty);
  const [preview, setPreview] = useState<JourneyProposalPreview | null>(null);
  const [message, setMessage] = useState("");

  const refresh = () =>
    journeyProposalApi
      .list()
      .then(setRows)
      .catch(() => setMessage(t("Suggestions could not be loaded.")));
  useEffect(() => void refresh(), []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      const result = await journeyProposalApi.submit({ ...form, confirmed: preview !== null });
      if (!preview && "requires_confirmation" in result) {
        setPreview(result);
        setMessage(t("Review the proposal, then confirm submission."));
        return;
      }
      setForm(empty);
      setPreview(null);
      setMessage(t("Suggestion submitted for review."));
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t("Suggestion could not be submitted."));
    }
  }

  async function vote(row: JourneyProposal) {
    if (!window.confirm(t(row.voted ? "Withdraw your vote?" : "Confirm your vote?"))) return;
    try {
      const updated = await (row.voted
        ? journeyProposalApi.withdrawVote(row.id)
        : journeyProposalApi.vote(row.id));
      setRows((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setPreview((current) =>
        current
          ? {
              ...current,
              proposal_matches: current.proposal_matches.map((item) =>
                item.id === updated.id
                  ? { ...updated, similarity_score: item.similarity_score }
                  : item,
              ),
            }
          : null,
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t("Vote could not be changed."));
    }
  }

  return (
    <section
      id="journey-suggestions"
      className="space-y-5"
      aria-labelledby="journey-suggestions-title"
    >
      <div>
        <h2 id="journey-suggestions-title" className="text-lg font-semibold">
          {t("Business Journey suggestions")}
        </h2>
        <p className="mt-1 text-sm text-fg-muted">
          {t(
            "Describe a missing business situation without customer names, contact details or secrets. Suggestions are reviewed and are not a roadmap promise.",
          )}
        </p>
      </div>
      <form className="grid gap-3" onSubmit={submit} onChange={() => setPreview(null)}>
        <input
          className="br-input"
          required
          minLength={3}
          maxLength={200}
          placeholder={t("Short title")}
          value={form.title}
          onChange={(event) => setForm({ ...form, title: event.target.value })}
        />
        <textarea
          className="br-input"
          required
          minLength={3}
          maxLength={1000}
          placeholder={t("What should Reality handle?")}
          value={form.business_question}
          onChange={(event) => setForm({ ...form, business_question: event.target.value })}
        />
        <textarea
          className="br-input"
          required
          minLength={3}
          maxLength={2000}
          placeholder={t("What outcome do you expect?")}
          value={form.expected_outcome}
          onChange={(event) => setForm({ ...form, expected_outcome: event.target.value })}
        />
        <select
          className="br-input"
          value={form.process_area}
          onChange={(event) => setForm({ ...form, process_area: event.target.value })}
        >
          {[
            "orders",
            "availability",
            "payments",
            "shipping",
            "invoicing",
            "returns",
            "purchasing",
            "receiving",
            "payables",
            "warehouse",
            "products",
            "commerce",
            "b2b",
            "finance",
            "master_data",
            "sources",
            "time",
            "combined",
          ].map((area) => (
            <option key={area}>{area}</option>
          ))}
        </select>
        <textarea
          className="br-input"
          maxLength={1000}
          placeholder={t("Optional business context (visible only to reviewers)")}
          value={form.business_context}
          onChange={(event) => setForm({ ...form, business_context: event.target.value })}
        />
        <button className="br-btn w-fit" type="submit">
          {t(preview ? "Confirm submission" : "Review suggestion")}
        </button>
      </form>
      {preview && (preview.proposal_matches.length > 0 || preview.journey_matches.length > 0) && (
        <section className="rounded-lg border border-border-default p-4" aria-live="polite">
          <h3 className="font-medium">{t("Possible existing matches")}</h3>
          <p className="mt-1 text-sm text-fg-muted">
            {t("Review these matches before creating another suggestion.")}
          </p>
          {preview.proposal_matches.map((match) => (
            <div key={match.id} className="mt-3 flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium">{match.title}</p>
                <p className="text-xs text-fg-muted">
                  {match.status} · {match.similarity_score}% {t("similar")}
                </p>
              </div>
              <button className="br-btn" type="button" onClick={() => void vote(match)}>
                {t(match.voted ? "Withdraw vote" : "Vote")} · {match.vote_count}
              </button>
            </div>
          ))}
          {preview.journey_matches.map((match) => (
            <p key={match.id} className="mt-3 text-sm">
              <span className="font-medium">
                {match.id}: {match.title}
              </span>{" "}
              <span className="text-fg-muted">· {match.status}</span>
            </p>
          ))}
        </section>
      )}
      {message && (
        <p role="status" className="text-sm">
          {message}
        </p>
      )}
      <div className="space-y-3">
        {rows.map((row) => (
          <article key={row.id} className="rounded-lg border border-border-default p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-medium">{row.title}</h3>
                <p className="mt-1 text-sm text-fg-muted">{row.business_question}</p>
              </div>
              <span className="text-xs text-fg-muted">{row.status}</span>
            </div>
            <button
              className="br-btn mt-3"
              type="button"
              onClick={() => void vote(row)}
              aria-pressed={row.voted}
            >
              {t(row.voted ? "Withdraw vote" : "Vote")} · {row.vote_count}
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}

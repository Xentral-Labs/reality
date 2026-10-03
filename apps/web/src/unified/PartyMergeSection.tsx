import { useEffect, useRef, useState } from "react";
import {
  api,
  partyMerges,
  workspaceApi,
  type PartyMergeReview,
  type ReferenceFamily,
  type ReferenceRow,
} from "../api";
import { formatDateTime, t } from "../localization";
import { ReadLine, ReadState } from "./ReadState";
import { useRead } from "./useCompanyContext";

// Spec 339: merging a duplicate business partner into this one. The server
// reviews the merge; nothing changes until the person confirms. The
// duplicate's history keeps naming it and reads under this partner.

export function PartyMergeSection({
  tenant,
  family,
  party,
}: {
  tenant: string;
  family: ReferenceFamily;
  party: { id: string; name: string; isActive: boolean };
}) {
  const [version, setVersion] = useState(0);
  const read = useRead(() => partyMerges.list(tenant, party.id), [tenant, party.id, version]);
  const [merging, setMerging] = useState(false),
    [query, setQuery] = useState(""),
    [candidates, setCandidates] = useState<ReferenceRow[]>([]),
    [duplicate, setDuplicate] = useState(""),
    [reason, setReason] = useState(""),
    [pending, setPending] = useState<{ id: string; review: PartyMergeReview } | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const open = useRef<string | null>(null);
  useEffect(
    () => () => {
      if (open.current) void api.rejectProposal(tenant, open.current, null).catch(() => undefined);
    },
    [tenant],
  );
  useEffect(() => {
    if (!merging) return;
    let active = true;
    const timer = window.setTimeout(() => {
      workspaceApi
        .references(tenant, family, query, 1, false)
        .then((page) => active && setCandidates(page.items.filter((row) => row.id !== party.id)))
        .catch(() => undefined);
    }, 200);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [tenant, family, query, merging, party.id]);
  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (failure) {
      setError(t((failure as Error).message));
    } finally {
      setBusy(false);
    }
  };
  const prepare = () =>
    run(async () => {
      const proposal = await partyMerges.prepare(tenant, {
        duplicate_party_id: duplicate,
        surviving_party_id: party.id,
        reason,
      });
      open.current = proposal.id;
      setPending({ id: proposal.id, review: proposal.preview.party_merge });
    });
  const confirm = () =>
    run(async () => {
      if (!pending) return;
      await partyMerges.confirm(tenant, pending.id);
      open.current = null;
      setPending(null);
      setMerging(false);
      setDuplicate("");
      setReason("");
      setVersion((value) => value + 1);
    });
  const discard = () => {
    if (open.current) void api.rejectProposal(tenant, open.current, null).catch(() => undefined);
    open.current = null;
    setPending(null);
  };
  const rows = read.data?.rows ?? [];
  const absorbed = rows.filter((row) => row.surviving_party_id === party.id);
  const mergedInto = rows.find((row) => row.duplicate_party_id === party.id);
  const side = (label: string, value: PartyMergeReview["duplicate"]) => (
    <li>
      {label}: <span data-localization="original">{value.name}</span> · {value.documents}{" "}
      {t("documents")} · {value.commitments} {t("commitments")} · {value.ledger_entries}{" "}
      {t("ledger entries")}
    </li>
  );
  return (
    <section className="mt-4 text-sm" data-party-merge-section>
      <div className="flex items-center justify-between gap-2">
        <div className="font-medium">{t("Merged business partners")}</div>
        {!mergedInto && party.isActive && !merging && (
          <button className="br-btn" onClick={() => setMerging(true)}>
            {t("Merge a duplicate into this partner")}
          </button>
        )}
      </div>
      {!read.data && <ReadState loading={read.loading} error={read.error} retry={read.refresh} />}
      {mergedInto && (
        <div data-party-merged-into>
          {t("Merged into")} <span data-localization="original">{mergedInto.survivor}</span> ·{" "}
          {formatDateTime(mergedInto.merged_at)} ·{" "}
          <span data-localization="original">{mergedInto.reason}</span>
        </div>
      )}
      {read.data && !mergedInto && absorbed.length === 0 && !merging && (
        <div className="text-muted">{t("No duplicate was merged into this partner.")}</div>
      )}
      {absorbed.length > 0 && (
        <ul data-party-merges>
          {absorbed.map((row) => (
            <li key={row.id}>
              <span data-localization="original">{row.duplicate}</span> ·{" "}
              {formatDateTime(row.merged_at)} ·{" "}
              <span data-localization="original">{row.reason}</span>
            </li>
          ))}
        </ul>
      )}
      {merging && !pending && (
        <form
          className="mt-2 grid gap-2"
          data-party-merge-form
          onSubmit={(event) => {
            event.preventDefault();
            prepare();
          }}
        >
          <input
            className="br-control"
            aria-label={t("Search business partners")}
            placeholder={t("Search business partners")}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <select
            className="br-control"
            aria-label={t("Duplicate")}
            required
            value={duplicate}
            onChange={(event) => setDuplicate(event.target.value)}
          >
            <option value="">{t("Choose the duplicate")}</option>
            {candidates.map((row) => (
              <option key={row.id} value={row.id}>
                {row.accounting_code ? `${row.accounting_code} · ` : ""}
                {row.name}
              </option>
            ))}
          </select>
          <input
            className="br-control"
            aria-label={t("Reason")}
            placeholder={t("Why the two are one business partner")}
            required
            maxLength={500}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
          <div className="flex gap-2">
            <button className="br-btn br-btn-primary" disabled={busy || !duplicate || !reason}>
              {t("Review merge")}
            </button>
            <button type="button" className="br-btn" onClick={() => setMerging(false)}>
              {t("Cancel")}
            </button>
          </div>
        </form>
      )}
      {pending && (
        <div className="mt-2 grid gap-2" data-party-merge-review>
          <ul>
            {side(t("Duplicate"), pending.review.duplicate)}
            {side(t("Survivor"), pending.review.survivor)}
          </ul>
          <div>
            {t(
              "The duplicate's history stays as stated and reads under the survivor; the duplicate becomes inactive.",
            )}
          </div>
          <div className="flex gap-2">
            <button className="br-btn br-btn-primary" disabled={busy} onClick={confirm}>
              {t("Confirm")}
            </button>
            <button className="br-btn" disabled={busy} onClick={discard}>
              {t("Discard")}
            </button>
          </div>
        </div>
      )}
      {busy && <ReadLine />}
      {error && (
        <div role="alert" className="mt-2 text-danger">
          {error}
        </div>
      )}
    </section>
  );
}

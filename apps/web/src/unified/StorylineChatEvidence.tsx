import { useState } from "react";
import { APIError, storylineApi, type StorylineTraceItem } from "../api";
import { t } from "../localization";
import type { Selection } from "./routing";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { StorylineProtocol } from "./StorylineProtocol";

type Props = { tenant: string; messageId: string; navigate: (changes: Partial<Selection>) => void };

export function StorylineChatEvidence(props: Props) {
  const [open, setOpen] = useState(false);
  return (
    <details
      className="mt-3 min-w-0"
      onToggle={(event) => setOpen(event.currentTarget.open)}
      data-chat-evidence={props.messageId}
    >
      <summary className="cursor-pointer text-xs font-medium text-fg-muted">
        {t("What happened")}
      </summary>
      {open && <Evidence {...props} />}
    </details>
  );
}

function Evidence({ tenant, messageId, navigate }: Props) {
  const { data, loading, error, refresh } = useRead(
    () =>
      storylineApi.chatEvidence(tenant, messageId).catch((error) => {
        if (error instanceof APIError && error.status === 404)
          return { available: false, items: [], has_more: false };
        throw error;
      }),
    [tenant, messageId],
  );
  const [picked, setPicked] = useState<StorylineTraceItem | null>(null);
  const result = useRead(
    () => (picked?.marker ? storylineApi.deltaAt(tenant, picked.ordinal) : Promise.resolve(null)),
    [tenant, picked?.ordinal],
  );
  if (!data) return <ReadState loading={loading} error={error} retry={refresh} />;
  if (!data.available)
    return (
      <p className="mt-2 text-sm text-fg-muted">
        {t("Recorded evidence is unavailable for this reply.")}
      </p>
    );
  return (
    <div className="mt-2">
      {data.has_more && (
        <p className="mb-2 text-sm text-fg-muted">
          {t("Some recorded calls are not included in this view.")}
        </p>
      )}
      {result.error && <ReadState loading={false} error={result.error} retry={result.refresh} />}
      {picked?.marker && (
        <p className="mb-2 text-xs text-fg-muted">
          {t("Changes since this call can include later activity in this Sandbox.")}
        </p>
      )}
      <StorylineProtocol
        tenant={tenant}
        items={data.items}
        delta={result.data || null}
        loading={loading || result.loading}
        navigate={navigate}
        mode="chat"
        onPick={setPicked}
        picked={picked?.ordinal}
      />
    </div>
  );
}

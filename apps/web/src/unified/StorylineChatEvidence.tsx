import { useState } from "react";
import { APIError, storylineApi, type ChatAnswerBasis, type StorylineTraceItem } from "../api";
import { currentLanguage, formatExactDecimal, t } from "../localization";
import type { Selection } from "./routing";
import { recordRoute } from "./storylineState";
import { useRead } from "./useCompanyContext";
import { ReadState } from "./ReadState";
import { StorylineProtocol } from "./StorylineProtocol";

type Props = { tenant: string; messageId: string; navigate: (changes: Partial<Selection>) => void };

const unavailable = {
  available: false,
  items: [],
  has_more: false,
  basis: { available: false, rows: [], additional_count: 0, calls: 0, has_more: false },
};

function formatBasisValue(value: string): string {
  const unit = currentLanguage() === "de" ? "Stk." : currentLanguage() === "nl" ? "st." : "pcs";
  return value.replace(/(-?\d+(?:\.\d+)?)\s+pcs\b/g, (_, quantity: string) => {
    return `${formatExactDecimal(quantity)} ${unit}`;
  });
}

export function StorylineChatEvidence(props: Props) {
  const { data, loading } = useRead(
    () =>
      storylineApi.chatEvidence(props.tenant, props.messageId).catch((error) => {
        if (error instanceof APIError && error.status === 404) return unavailable;
        throw error;
      }),
    [props.tenant, props.messageId],
  );
  const [open, setOpen] = useState(false);
  if (!data) return null;
  if (!data.basis.available && !data.available) return null;
  return (
    <details
      className="mt-3 min-w-0"
      onToggle={(event) => setOpen(event.currentTarget.open)}
      data-chat-evidence={props.messageId}
    >
      <summary className="cursor-pointer text-xs font-medium text-fg-muted">
        {t(data.basis.available ? "Basis for this answer" : "Technical activity")}
      </summary>
      {open && (
        <Evidence
          {...props}
          basis={data.basis}
          traceAvailable={data.available}
          items={data.items}
          hasMore={data.has_more}
          loading={loading}
        />
      )}
    </details>
  );
}

function Evidence({
  tenant,
  navigate,
  basis,
  traceAvailable,
  items,
  hasMore,
  loading,
}: Props & {
  basis: ChatAnswerBasis;
  traceAvailable: boolean;
  items: StorylineTraceItem[];
  hasMore: boolean;
  loading: boolean;
}) {
  const [picked, setPicked] = useState<StorylineTraceItem | null>(null);
  const result = useRead(
    () => (picked?.marker ? storylineApi.deltaAt(tenant, picked.ordinal) : Promise.resolve(null)),
    [tenant, picked?.ordinal],
  );
  return (
    <div className="mt-2 grid gap-2" data-answer-basis>
      {basis.available && (
        <div className="overflow-hidden rounded-lg border border-border-default bg-surface">
          <dl className="divide-y divide-border-subtle">
            {basis.rows.map((row, index) => {
              const value = (
                <span className="flex min-w-0 items-center justify-end gap-1.5 text-right text-fg-strong">
                  <span className="truncate" data-localization="original">
                    {formatBasisValue(row.value)}
                  </span>
                  {row.status && <span className="text-fg-muted">· {t(row.status)}</span>}
                </span>
              );
              return (
                <div
                  className="grid grid-cols-[minmax(5.5rem,0.7fr)_minmax(0,1.3fr)] gap-3 px-3 py-2 text-xs"
                  data-basis-role={row.role}
                  key={`${row.label}-${row.record_id || index}`}
                >
                  <dt
                    className="text-fg-muted data-[basis-label-role=derived]:font-medium data-[basis-label-role=derived]:text-accent"
                    data-basis-label-role={row.role}
                  >
                    {t(row.label)}
                  </dt>
                  <dd className="min-w-0">
                    {row.record_type && row.record_id ? (
                      <button
                        type="button"
                        className="block w-full text-right underline-offset-2 hover:text-accent hover:underline"
                        onClick={() => navigate(recordRoute(row.record_type!, row.record_id!))}
                      >
                        {value}
                      </button>
                    ) : (
                      value
                    )}
                  </dd>
                </div>
              );
            })}
          </dl>
          {(basis.additional_count > 0 || basis.has_more) && (
            <p className="border-t border-border-subtle px-3 py-2 text-xs text-fg-muted">
              {t("Additional supporting records are not shown in this compact view.")}
            </p>
          )}
        </div>
      )}
      {traceAvailable && (
        <details className="text-xs text-fg-muted" data-technical-activity>
          <summary className="cursor-pointer">{t("Technical activity")}</summary>
          <div className="mt-2">
            {hasMore && (
              <p className="mb-2 text-sm text-fg-muted">
                {t("Some recorded calls are not included in this view.")}
              </p>
            )}
            {result.error && (
              <ReadState loading={false} error={result.error} retry={result.refresh} />
            )}
            {picked?.marker && (
              <p className="mb-2 text-xs text-fg-muted">
                {t("Changes since this call can include later activity in this Sandbox.")}
              </p>
            )}
            <StorylineProtocol
              tenant={tenant}
              items={items}
              delta={result.data || null}
              loading={loading || result.loading}
              navigate={navigate}
              mode="chat"
              onPick={setPicked}
              picked={picked?.ordinal}
            />
          </div>
        </details>
      )}
    </div>
  );
}

import { useState } from "react";
import { useActionDiscovery } from "../ActionLauncher";
import { reasonText } from "../guidanceActions";
import { graphApi, type GraphAnswer, type GraphQuestion } from "../../api";
import { formatDateTime, formatNumber, t } from "../../localization";
import { ReadState } from "../ReadState";
import { useRead } from "../useCompanyContext";
import { CostExplanationFrame } from "../CostExplanation";

type Context = NonNullable<GraphQuestion["contribution_cost_context"]>;

export function InventoryValuationSelector(props: {
  tenant: string;
  contribution?: boolean;
  context?: Context;
  capturedContext?: NonNullable<GraphQuestion["captured_cost_context"]>;
  companyContext?: NonNullable<GraphQuestion["company_cost_context"]>;
  disabled: boolean;
  select: (context?: Context) => void;
  selectCaptured: (context?: NonNullable<GraphQuestion["captured_cost_context"]>) => void;
  selectCompany: (context?: NonNullable<GraphQuestion["company_cost_context"]>) => void;
}) {
  const [cursor, setCursor] = useState<string | undefined>();
  return (
    <section
      className="my-3 rounded-xl border border-border-default bg-surface-muted p-4 text-fg"
      aria-label={
        props.contribution ? t("Confirmed contribution") : t("Confirmed inventory valuation")
      }
    >
      <h3>
        {props.contribution ? t("Confirmed contribution") : t("Confirmed inventory valuation")}
      </h3>
      <p>
        {t(
          "Choose a confirmed historical valuation. Its availability is checked when the report runs.",
        )}
      </p>
      {props.contribution && props.context && (
        <label className="my-2 flex items-center gap-2">
          <input
            type="checkbox"
            disabled={props.disabled}
            checked={props.context.mode === "current"}
            onChange={(event) =>
              props.select({
                ...props.context!,
                mode: event.target.checked ? "current" : "historical",
              })
            }
          />
          {t("Require unchanged data since confirmation")}
        </label>
      )}
      <InventoryValuationPage
        key={`${props.tenant}:${cursor ?? ""}`}
        {...props}
        cursor={cursor}
        page={setCursor}
      />
      <CapturedValuationPage {...props} />
      <CompanyValuationPage {...props} />
    </section>
  );
}

function CompanyValuationPage(props: {
  tenant: string;
  contribution?: boolean;
  companyContext?: NonNullable<GraphQuestion["company_cost_context"]>;
  disabled: boolean;
  selectCompany: (context?: NonNullable<GraphQuestion["company_cost_context"]>) => void;
}) {
  const family = props.contribution ? "contribution" : "inventory";
  const read = useRead(
    () => graphApi.companyGeneration(props.tenant, family),
    [props.tenant, family],
  );
  const option = read.data?.item;
  // Spec 279 FR-014: say why the list is empty and who builds valuations.
  const unavailable = reasonText(
    useActionDiscovery()?.data?.resolution_guidance,
    "inventory_valuation_unavailable",
  );
  return (
    <label className="mt-3 flex flex-col gap-1">
      <span>{t("Financial company generation")}</span>
      <select
        className="br-control min-w-0 max-w-full"
        value={props.companyContext?.generation_id ?? ""}
        disabled={props.disabled || read.loading}
        onChange={(event) =>
          props.selectCompany(
            event.target.value ? { generation_id: event.target.value } : undefined,
          )
        }
      >
        <option value="">{t("Select a financial company generation…")}</option>
        {props.companyContext && option?.generation_id !== props.companyContext.generation_id && (
          <option value={props.companyContext.generation_id}>
            {t("Selected company generation is no longer current")}
          </option>
        )}
        {option && (
          <option value={option.generation_id}>
            {formatDateTime(option.effective_at)} · {formatNumber(option.subject_count)}{" "}
            {props.contribution ? t("positions") : t("articles")} · {t(option.state)}
          </option>
        )}
      </select>
      {read.error && <ReadState loading={false} error={read.error} retry={read.refresh} />}
      {read.data && !read.data.item && (
        <small className="text-fg-muted" data-valuation-unavailable>
          {unavailable.label}. {unavailable.explanation}
        </small>
      )}
    </label>
  );
}

function CapturedValuationPage(props: {
  tenant: string;
  contribution?: boolean;
  capturedContext?: NonNullable<GraphQuestion["captured_cost_context"]>;
  disabled: boolean;
  selectCaptured: (context?: NonNullable<GraphQuestion["captured_cost_context"]>) => void;
}) {
  const family = props.contribution ? "contribution" : "inventory";
  const read = useRead(
    () => graphApi.capturedReports(props.tenant, family),
    [props.tenant, family],
  );
  return (
    <label className="mt-3 flex flex-col gap-1">
      <span>{t("Captured review selection")}</span>
      <select
        className="br-control min-w-0 max-w-full"
        value={props.capturedContext?.generation_id ?? ""}
        disabled={props.disabled || read.loading}
        onChange={(event) =>
          props.selectCaptured(
            event.target.value ? { generation_id: event.target.value } : undefined,
          )
        }
      >
        <option value="">{t("Select a captured review selection…")}</option>
        {props.capturedContext &&
          !read.data?.items.some(
            (item) => item.generation_id === props.capturedContext?.generation_id,
          ) && (
            <option value={props.capturedContext.generation_id}>
              {t("Selected captured report (outside this page)")}
            </option>
          )}
        {read.data?.items.map((item) => (
          <option key={item.generation_id} value={item.generation_id}>
            {formatDateTime(item.effective_at)} ·{" "}
            {formatNumber(props.contribution ? item.contribution_count : item.inventory_count)}{" "}
            {props.contribution ? t("positions") : t("articles")} · {t(item.freshness)}
          </option>
        ))}
      </select>
      {read.error && <ReadState loading={false} error={read.error} retry={read.refresh} />}
    </label>
  );
}

function InventoryValuationPage({
  tenant,
  contribution = false,
  context,
  disabled,
  select,
  cursor,
  page,
}: {
  tenant: string;
  contribution?: boolean;
  context?: Context;
  disabled: boolean;
  select: (context?: Context) => void;
  cursor?: string;
  page: (cursor?: string) => void;
}) {
  const read = useRead(async () => {
    if (!contribution) return graphApi.inventoryReviews(tenant, cursor);
    const result = await graphApi.contributionReviews(tenant, cursor);
    return {
      ...result,
      items: result.items.map((item) => ({ ...item, item_count: item.position_count })),
    };
  }, [tenant, cursor, contribution]);
  return (
    <>
      {(read.loading || read.error) && (
        <ReadState loading={read.loading} error={read.error} retry={read.refresh} />
      )}
      {read.data && !read.loading && (
        <>
          <label className="flex flex-col gap-1">
            <span>{t("Valuation basis")}</span>
            <select
              className="br-control min-w-0 max-w-full"
              aria-label={t("Valuation basis")}
              value={context?.action_id ?? ""}
              disabled={disabled}
              onChange={(event) =>
                select(
                  event.target.value
                    ? {
                        action_id: event.target.value,
                        mode: contribution ? (context?.mode ?? "historical") : "historical",
                      }
                    : undefined,
                )
              }
            >
              <option value="">{t("Select a confirmed valuation…")}</option>
              {context && !read.data.items.some((item) => item.action_id === context.action_id) && (
                <option value={context.action_id}>
                  {t("Selected valuation (outside this page)")}
                </option>
              )}
              {read.data.items.map((item) => (
                <option key={item.action_id} value={item.action_id}>
                  {formatDateTime(item.effective_at)} · {item.owner_name} · {item.currency} ·{" "}
                  {formatNumber(item.item_count)} {contribution ? t("positions") : t("articles")} ·{" "}
                  {t("Knowledge cutoff")}: {formatDateTime(item.knowledge_at)}
                </option>
              ))}
            </select>
          </label>
          {!read.data.items.length && (
            <p>
              {contribution
                ? t("No confirmed joint contribution valuations on this page.")
                : t("No confirmed joint inventory valuations on this page.")}
            </p>
          )}
          <div className="mt-2 flex flex-wrap gap-2">
            <button className="br-btn" onClick={read.refresh}>
              {t("Refresh")}
            </button>
            {cursor && (
              <button className="br-btn" onClick={() => page()}>
                {t("Newest valuations")}
              </button>
            )}
            {read.data.next_cursor && (
              <button className="br-btn" onClick={() => page(read.data!.next_cursor ?? undefined)}>
                {t("Older valuations")}
              </button>
            )}
          </div>
        </>
      )}
      {context && (
        <button className="br-btn" disabled={disabled} onClick={() => select()}>
          {t("Clear valuation selection")}
        </button>
      )}
    </>
  );
}

export function InventoryValuationBasis({
  tenant,
  basis,
}: {
  tenant: string;
  basis: NonNullable<GraphAnswer["cost_basis"]>;
}) {
  if (basis.kind === "financial_company_generation") {
    const contribution = basis.coverage.expected_positions !== undefined;
    const expected = contribution
      ? basis.coverage.expected_positions
      : basis.coverage.expected_items;
    const available = contribution
      ? basis.coverage.available_positions
      : basis.coverage.available_items;
    return (
      <section className="my-3 rounded-xl border border-border-default bg-surface-muted p-4 text-fg">
        <h3>{t("Financial company generation")}</h3>
        <p>
          {t(
            "One fixed verified company generation over independent member reviews. Missing values remain outside final totals.",
          )}
        </p>
        <dl className="grid gap-2 sm:grid-cols-3">
          <div>
            <dt>{t("Valuation cutoff")}</dt>
            <dd>{formatDateTime(basis.context.effective_at)}</dd>
          </div>
          <div>
            <dt>{t("Coverage")}</dt>
            <dd>
              {formatNumber(available ?? 0)} / {formatNumber(expected ?? 0)}
            </dd>
          </div>
          <div>
            <dt>{t("Calculation reference")}</dt>
            <dd>
              <code>{basis.generation_id}</code>
            </dd>
          </div>
        </dl>
        {basis.freshness.state === "pending" && (
          <p>
            {t(
              "New company data exists after this fixed calculation. Its values remain historical until a new generation is published.",
            )}
          </p>
        )}
      </section>
    );
  }
  if (basis.kind === "captured_review_selection_v1") {
    return (
      <section className="my-3 rounded-xl border border-border-default bg-surface-muted p-4 text-fg">
        <h3>{t("Captured review selection")}</h3>
        <p>
          {t(
            "Known subtotals from one fixed captured review selection. This is not a complete company valuation or financial approval.",
          )}
        </p>
        <dl className="grid gap-2 sm:grid-cols-3">
          <div>
            <dt>{t("Valuation cutoff")}</dt>
            <dd>{formatDateTime(basis.context.effective_at)}</dd>
          </div>
          <div>
            <dt>{t("Captured at")}</dt>
            <dd>{formatDateTime(basis.context.observed_at ?? "")}</dd>
          </div>
          <div>
            <dt>{t("Calculation reference")}</dt>
            <dd>
              <code>{basis.generation_id}</code>
            </dd>
          </div>
        </dl>
      </section>
    );
  }
  const contribution = basis.kind === "contribution";
  const reference = (kind: string, id: string) =>
    `/app/inspector?${new URLSearchParams({
      tenant,
      inspector_view: "records",
      inspector_target_kind: kind,
      inspector_target_id: id,
    })}`;
  return (
    <CostExplanationFrame title={t("Historical valuation basis")}>
      <h3>{t("Historical valuation basis")}</h3>
      <dl className="grid gap-2 sm:grid-cols-3">
        <div>
          <dt>{t("Valuation cutoff")}</dt>
          <dd>{formatDateTime(basis.context.effective_at)}</dd>
        </div>
        <div>
          <dt>{t("Knowledge cutoff")}</dt>
          <dd>{formatDateTime(basis.context.knowledge_at)}</dd>
        </div>
        <div>
          <dt>{contribution ? t("Loaded positions") : t("Covered articles")}</dt>
          <dd>
            {formatNumber(
              (contribution
                ? basis.coverage.available_positions
                : basis.coverage.available_items) ?? 0,
            )}{" "}
            /{" "}
            {formatNumber(
              (contribution ? basis.coverage.expected_positions : basis.coverage.expected_items) ??
                0,
            )}
          </dd>
        </div>
      </dl>
      <p>
        {contribution
          ? t(
              "Historical contribution for the selected positions. Missing costs leave final margins unknown; coverage counts show which positions are complete.",
            )
          : t("Acquisition value for the selected historical scope; no carrying value assessment.")}
      </p>
      {contribution && basis.freshness.state === "ready" && (
        <p>
          {t(
            "No newer company data at read time. The selected scope and valuation cutoff remain unchanged.",
          )}
        </p>
      )}
      <details>
        <summary>{t("Valuation references")}</summary>
        <dl className="break-all">
          <dt>{t("Confirmation")}</dt>
          <dd>
            <a className="underline" href={reference("action", basis.action_id!)}>
              {basis.action_id}
            </a>
          </dd>
          <dt>{t("Economic owner")}</dt>
          <dd>
            <code>{basis.context.owner_party_id}</code>
          </dd>
          <dt>{t("Valuation reviews")}</dt>
          <dd>
            {basis.context.review_ids?.map((id) => (
              <div key={id}>
                <a
                  className="underline"
                  href={reference(
                    contribution ? "cost_contribution_review" : "cost_inventory_review",
                    id,
                  )}
                >
                  {id}
                </a>
              </div>
            ))}
          </dd>
          <dt>{t("Calculation references")}</dt>
          <dd>
            {basis.generation_ids?.map((id) => (
              <div key={id}>
                <code>{id}</code>
              </div>
            ))}
          </dd>
        </dl>
      </details>
    </CostExplanationFrame>
  );
}

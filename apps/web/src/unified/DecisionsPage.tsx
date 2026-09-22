import { useEffect, useRef, useState } from "react";
import { CheckSquare, X } from "lucide-react";
import { api, type CopilotProposal, type ProposalReviewKind } from "../api";
import { formatDateTime, t } from "../localization";
import { ReadState } from "./ReadState";
import { WorkFooter, WorkHeader, WorkRow, WorkSearch, useWorkList } from "./WorkList";
import { WorkPreview } from "./InlinePreview";
const actionLabels: Record<string, string> = {
  reserve: "Reserve stock",
  reservation_release: "Release reservation",
  commitment_hold: "Hold commitment",
  commitment_hold_release: "Release commitment hold",
  party_delivery_hold: "Place customer delivery hold",
  party_delivery_hold_release: "Release customer delivery hold",
  movement_create: "Record movement",
  movement_correct: "Correct movement",
  ledger_reverse: "Reverse posting",
  order_create: "Create order",
  sales_invoice_record: "Record sales invoice",
  supplier_invoice_record: "Record supplier invoice",
  sales_credit_record: "Record sales credit",
  customer_refund_post: "Record refund",
  customer_payment_post: "Record customer payment",
  supplier_payment_post: "Record supplier payment",
  party_create: "Create party",
  party_update: "Update party",
  item_create: "Create item",
  item_update: "Update item",
  location_create: "Create location",
  location_update: "Update location",
};
const proposalFields: Record<string, string> = {
  name: "Name",
  sku: "SKU",
  number: "Number",
  reference: "Reference",
  quantity: "Quantity",
  unit: "Unit",
  amount: "Amount",
  currency: "Currency",
  note: "Note",
  reason: "Reason",
};
function statedFields(proposal: CopilotProposal) {
  return Object.entries(proposal.input).filter(
    ([key, value]) =>
      key in proposalFields &&
      (typeof value === "string" || typeof value === "number") &&
      value !== "",
  );
}
function DecisionHelp({ close }: { close: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    dialog.current?.showModal();
    return () => previous?.focus();
  }, []);
  return (
    <dialog
      ref={dialog}
      aria-labelledby="decision-help-title"
      className="br-exception-catalog"
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
    >
      <div className="mb-5 flex items-center justify-between gap-4">
        <h2 id="decision-help-title" className="text-lg font-semibold">
          {t("How does a decision arise?")}
        </h2>
        <button className="br-btn" aria-label={t("Close")} onClick={close}>
          <X size={18} />
        </button>
      </div>
      <div className="space-y-4 text-sm leading-6 text-fg-muted">
        <p>
          {t(
            "Reality never writes on its own. Every change is proposed first, and a proposal waits here until a person decides on it.",
          )}
        </p>
        <p>
          {t(
            "A connected agent proposes a change but cannot carry it out. An action you start in a workspace is also proposed first, and stays here if you leave before deciding.",
          )}
        </p>
        <p className="rounded-lg border border-border-default bg-surface-muted p-4 text-fg-default">
          {t(
            "A pending decision has changed nothing yet. Rejecting one leaves your records exactly as they are.",
          )}
        </p>
        <section className="space-y-3 border-t border-border-default pt-4">
          <h3 className="font-semibold text-fg-strong">{t("Try it with an external agent")}</h3>
          <ol className="list-decimal space-y-2 pl-5">
            <li>{t("Connect an MCP client to Reality and let it read the current company.")}</li>
            <li>
              {t(
                "Ask it to inspect open commitments, inventory or blockers before suggesting a change.",
              )}
            </li>
            <li>
              {t(
                "Ask it to prepare, not execute, a proposal. The proposal then appears here for human review.",
              )}
            </li>
            <li>
              {t(
                "Open the decision, verify its evidence and exact effect, then approve or reject it.",
              )}
            </li>
          </ol>
          <p className="font-medium text-fg-strong">{t("Example: understand what is open")}</p>
          <pre className="overflow-auto whitespace-pre-wrap rounded-lg bg-surface-muted p-4 text-xs text-fg-default">
            {t(
              "Use Reality MCP in read-only mode. List open customer commitments and fulfillment blockers. Explain what is open and why, using the opaque record IDs and available evidence. Do not propose or execute a change yet.",
            )}
          </pre>
          <p className="font-medium text-fg-strong">{t("Example: prepare a human decision")}</p>
          <pre className="overflow-auto whitespace-pre-wrap rounded-lg bg-surface-muted p-4 text-xs text-fg-default">
            {t(
              "For commitment <opaque commitment ID>, use Reality MCP to prepare a reservation proposal for <quantity>. Do not approve or execute it. Return the proposal ID and explain the expected effect so a person can review it in Decisions.",
            )}
          </pre>
          <p>
            {t(
              "Under the hood, an agent can use commitments_list or fulfillment_blockers to read, business_records_discover to resolve opaque records, and reservation_propose to prepare this example. Approval remains a separate human step.",
            )}
          </p>
        </section>
        <section className="rounded-lg border border-border-default p-4">
          <h3 className="font-semibold text-fg-strong">{t("Possible future direction")}</h3>
          <p className="mt-2">
            {t(
              "Reality may eventually let companies create and configure agents inside the product. That direction is exploratory and is not a committed part of the project; Reality may instead remain the governed business system used by external agents through MCP.",
            )}
          </p>
        </section>
      </div>
    </dialog>
  );
}
export function DecisionsPage({
  tenant,
  select,
}: {
  tenant: string;
  select: (id: string, reviewKind: ProposalReviewKind) => void;
}) {
  const [query, setQuery] = useState("");
  const [tool, setTool] = useState("");
  const [selected, setSelected] = useState<CopilotProposal | null>(null);
  const [aboutOpen, setAboutOpen] = useState(false);
  const list = useWorkList<CopilotProposal>(JSON.stringify([tenant, query, tool]), (page) =>
    api.changeProposals(tenant, "pending", page, query, 50, tool),
  );
  const title = (proposal: CopilotProposal) =>
    proposal.input.import_file
      ? t("Import items")
      : t(actionLabels[proposal.tool] || proposal.review_label);
  const origin = (proposal: CopilotProposal) =>
    t(
      proposal.actor_type === "agent"
        ? "Proposed by an agent"
        : proposal.actor_type === "human"
          ? "Prepared by someone in this company"
          : "Prepared outside daily work",
    );
  const review = (proposal: CopilotProposal) => {
    setSelected(null);
    select(proposal.id, proposal.review_kind);
  };
  return (
    <div className="mx-auto max-w-[1200px] space-y-3" data-work-list="decisions">
      <WorkHeader title="Decisions" total={list.page?.total} />
      <div className="work-list-toolbar grid gap-2">
        <WorkSearch
          value={query}
          change={(value) => {
            setQuery(value);
            setSelected(null);
          }}
          label="Search proposed changes"
        />
        <div className="work-list-filters flex min-w-0 flex-wrap items-center gap-2">
          <select
            className="br-control min-w-0 flex-1"
            aria-label={t("Action type")}
            value={tool}
            onChange={(event) => {
              setTool(event.target.value);
              setSelected(null);
            }}
          >
            <option value="">{t("All actions")}</option>
            {Object.entries(actionLabels).map(([key, label]) => (
              <option key={key} value={key}>
                {t(label)}
              </option>
            ))}
          </select>
          <button type="button" className="br-btn shrink-0" onClick={() => setAboutOpen(true)}>
            {t("How does a decision arise?")}
          </button>
        </div>
      </div>
      {aboutOpen && <DecisionHelp close={() => setAboutOpen(false)} />}
      <section
        className="overflow-hidden rounded-xl border border-border-default bg-surface"
        aria-busy={list.loading}
      >
        {!list.page && list.loading ? (
          <ReadState loading rows={8} />
        ) : !list.items.length && !list.error ? (
          <p className="px-5 py-14 text-center text-sm text-fg-muted">
            {t(query || tool ? "No results" : "No pending decisions")}
          </p>
        ) : (
          list.items.map((proposal) => (
            <div key={proposal.id}>
              <WorkRow
                title={title(proposal)}
                context={
                  statedFields(proposal).length
                    ? statedFields(proposal)
                        .map(([key, value]) => `${t(proposalFields[key])}: ${String(value)}`)
                        .join(" · ")
                    : origin(proposal)
                }
                meta={formatDateTime(proposal.created_at)}
                icon={<CheckSquare size={18} />}
                selected={selected?.id === proposal.id}
                previewId={`decision-preview-${proposal.id}`}
                open={() => setSelected(selected?.id === proposal.id ? null : proposal)}
              />
              <WorkPreview
                id={`decision-preview-${proposal.id}`}
                open={selected?.id === proposal.id}
              >
                <h3 className="text-lg font-semibold text-fg-strong">{title(proposal)}</h3>
                <p className="mt-2 text-sm text-fg-muted">
                  {origin(proposal)} · {formatDateTime(proposal.created_at)}
                </p>
                {statedFields(proposal).length > 0 && (
                  <dl className="mt-4 divide-y divide-border-default">
                    {statedFields(proposal).map(([key, value]) => (
                      <div key={key} className="flex gap-4 py-2 text-sm">
                        <dt className="w-28 text-fg-muted">{t(proposalFields[key])}</dt>
                        <dd>{String(value)}</dd>
                      </div>
                    ))}
                  </dl>
                )}
                <button className="br-btn br-btn-primary mt-4" onClick={() => review(proposal)}>
                  {t("Review proposed changes")}
                </button>
              </WorkPreview>
            </div>
          ))
        )}
        <WorkFooter list={list} />
      </section>
    </div>
  );
}

import { useTrialResult } from "./FreePlayground";
import { FinanceSettings } from "../finance/FinanceSettings";
import { financeContext } from "./actionDiscovery";
import { useContextActions } from "./ActionLauncher";
import { PageActionBar } from "./PageActionBar";
import { RegisterWorkbench, RegisterHeader, RegisterToolbar } from "./RegisterWorkbench";

import { useState } from "react";
import { FinancialComponents } from "../finance/FinancialComponents";
import { OpeningItems } from "../finance/OpeningItems";
import { SettlementFlow } from "../finance/SettlementFlow";
import { SettlementReduction } from "../finance/SettlementReduction";
import { useRegisterQuery } from "./TableContext";
import { RegisterTable } from "./RegisterTable";
import { Wallet, Search } from "lucide-react";
import { Fragment } from "react";
import {
  api,
  type OpenItemRow,
  type PartyBalanceRow,
  type BalanceTotals,
  type PaymentRow,
  type JournalRow,
  type FinancialTotals,
  type JournalTotal,
  type Page,
  type ProjectionMetadata,
} from "../api";
import { formatDateTime, formatMoney, t } from "../localization";
import { ProjectionFreshness } from "./ProjectionFreshness";
import { ReadState } from "./ReadState";
import { RegisterPager } from "./WarehousePage";
import { InlineInspector, PreviewButton, TablePreview } from "./InlinePreview";
import { useRead } from "./useCompanyContext";
import type { Selection } from "./routing";
import { DocumentContributionExplanations } from "./DocumentContributionExplanations";

type FinanceData =
  | {
      view: "open-items";
      metadata?: ProjectionMetadata;
      items: OpenItemRow[];
      totals: FinancialTotals[];
      page: Page;
    }
  | { view: "payments"; items: PaymentRow[]; totals: FinancialTotals[]; page: Page }
  | { view: "journal"; items: JournalRow[]; totals: JournalTotal[]; page: Page }
  | { view: "balances"; items: PartyBalanceRow[]; totals: BalanceTotals[]; page: Page };
const statuses = [
  ["outstanding", "Outstanding"],
  ["open", "Open"],
  ["partial", "Partially settled"],
  ["paid", "Settled"],
] as const;
export function FinancePage(
  props: Parameters<typeof FinanceRegister>[0] & { canManage?: boolean },
) {
  const { selection, navigate, canManage = false } = props;
  return (
    <RegisterWorkbench>
      <RegisterHeader title="Finance">
        <div className="register-tabs">
          {(
            [
              ["open-items", "Open items"],
              ["payments", "Payments"],
              ["journal", "Journal"],
              ["balances", "Balances"],
              ["settings", "Settings"],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              className="br-btn aria-pressed:border-accent aria-pressed:bg-accent-soft"
              aria-pressed={selection.financeView === value}
              onClick={() => navigate({ financeView: value, entry: "", q: "", page: 1 })}
            >
              {t(label)}
            </button>
          ))}
        </div>
      </RegisterHeader>

      {selection.financeView === "settings" ? (
        <FinanceSettings
          key={selection.tenant}
          tenantId={selection.tenant}
          canManage={canManage}
          area={selection.financeSettings}
          selectArea={(financeSettings) => navigate({ financeSettings })}
        />
      ) : (
        <FinanceRegister key={selection.tenant} {...props} />
      )}
    </RegisterWorkbench>
  );
}

function FinanceRegister({
  selection,
  canAcceptReduction = false,
  navigate,
  create,
  recordPayment,
  reverse,
  credit,
  refund,
}: {
  selection: Selection;
  canAcceptReduction?: boolean;
  create?: () => void;
  recordPayment?: () => void;
  reverse?: (id?: string) => void;
  credit?: (id?: string) => void;
  refund?: (id?: string) => void;
  navigate: (changes: Partial<Selection>) => void;
}) {
  const {
    tenant,
    financeView: view,
    flow,
    financeStatus: status,
    direction,
    account,
    balanceSide,
    creditOnly,
    financeOverdue,
    partyId,
    q,
    page,
    entry,
  } = selection;
  const [detailDocument, setDetailDocument] = useState("");
  const [opening, setOpening] = useState(false);
  const [settlement, setSettlement] = useState<{
    document: string;
    mode: "payment" | "allocate_credit";
  } | null>(null);
  const [reductionInvoice, setReductionInvoice] = useState("");
  const creditBalance =
    view === "open-items" && ["customer-balance", "supplier-balance"].includes(flow);
  const table = useRegisterQuery();
  const read = useRead<FinanceData>(async () => {
    if (view === "open-items")
      return {
        view,
        ...(await api.openItems(tenant, q, flow, status, page, table, partyId, financeOverdue)),
      };
    if (view === "balances")
      return {
        view,
        ...(await api.partyBalances(tenant, balanceSide, q, creditOnly, page, table)),
      };
    if (view === "payments")
      return { view, ...(await api.payments(tenant, q, direction, page, table)) };
    return { view: "journal", ...(await api.journal(tenant, q, account, "", "", page, table)) };
  }, [
    tenant,
    view,
    flow,
    status,
    direction,
    account,
    balanceSide,
    creditOnly,
    selection.financeOverdue,
    partyId,
    q,
    page,
    table.size,
    table.sort,
    table.sort_direction,
  ]);
  const data = read.data?.view === view ? read.data : null;
  const awaitingCalculation =
    data?.view === "open-items" && data.metadata && !data.metadata.completed_at;
  useTrialResult(
    "invoices",
    tenant,
    !!data &&
      view === "open-items" &&
      flow === "receivable" &&
      status === "outstanding" &&
      !read.loading &&
      !read.error &&
      !awaitingCalculation,
  );
  const explain = (id: string) => (
    <PreviewButton
      open={entry === id}
      controls={`finance-preview-${id}`}
      label={id}
      toggle={() => navigate({ entry: entry === id ? "" : id })}
    />
  );
  const money = (value: string, currency: string) => formatMoney(value, currency);
  const financeActions = useContextActions(financeContext(selection));
  return (
    <>
      <section className="register-surface">
        <RegisterToolbar
          count={awaitingCalculation ? undefined : data?.page.total}
          search={
            <label className="relative min-w-0 basis-full sm:basis-0 sm:flex-1">
              <span className="sr-only">{t("Search finance")}</span>
              <Search size={16} className="absolute left-3 top-3 text-fg-muted" />
              <input
                className="br-control w-full"
                style={{ paddingInlineStart: "2.25rem" }}
                value={q}
                placeholder={t(
                  view === "open-items"
                    ? "Search invoice or party"
                    : view === "balances"
                      ? "Search party"
                      : "Search by reference ID",
                )}
                onChange={(e) => navigate({ q: e.target.value, page: 1 })}
              />
            </label>
          }
          filters={
            <>
              {view === "balances" ? (
                <>
                  <select
                    style={{ width: "auto", maxWidth: "100%" }}
                    className="br-control"
                    aria-label={t("Side")}
                    value={balanceSide}
                    onChange={(e) =>
                      navigate({
                        balanceSide: e.target.value as Selection["balanceSide"],
                        page: 1,
                      })
                    }
                  >
                    <option value="customer">{t("Customers")}</option>
                    <option value="supplier">{t("Suppliers")}</option>
                  </select>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={creditOnly}
                      onChange={(e) => navigate({ creditOnly: e.target.checked, page: 1 })}
                    />
                    {t("Credit only")}
                  </label>
                </>
              ) : view === "open-items" ? (
                <>
                  {partyId && (
                    <button
                      className="br-btn"
                      onClick={() => navigate({ partyId: "", page: 1 })}
                      title={t("Only this party")}
                    >
                      {t("All parties")}
                    </button>
                  )}
                  <select
                    style={{ width: "auto", maxWidth: "100%" }}
                    className="br-control"
                    aria-label={t("Flow")}
                    value={flow}
                    onChange={(e) =>
                      navigate({
                        flow: e.target.value as Selection["flow"],
                        page: 1,
                        entry: "",
                        financeOverdue: false,
                      })
                    }
                  >
                    <option value="receivable">{t("Receivables")}</option>
                    <option value="payable">{t("Payables")}</option>
                    <option value="customer-credit">{t("Customer credits")}</option>
                    <option value="customer-balance">{t("Available customer credit")}</option>
                    <option value="supplier-balance">{t("Available supplier credit")}</option>
                  </select>
                  {["receivable", "payable"].includes(flow) && (
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={!!selection.financeOverdue}
                        onChange={(event) =>
                          navigate({ financeOverdue: event.target.checked, page: 1 })
                        }
                      />
                      {t("Overdue invoices")}
                    </label>
                  )}
                  <select
                    style={{ width: "auto", maxWidth: "100%" }}
                    className="br-control"
                    aria-label={t("Status")}
                    value={status}
                    onChange={(e) => navigate({ financeStatus: e.target.value, page: 1 })}
                  >
                    <option value="">{t("All states")}</option>
                    {statuses.map(([value, label]) => (
                      <option key={value} value={value}>
                        {t(label)}
                      </option>
                    ))}
                  </select>
                </>
              ) : view === "payments" ? (
                <select
                  style={{ width: "auto", maxWidth: "100%" }}
                  className="br-control sm:w-auto"
                  aria-label={t("Direction")}
                  value={direction}
                  onChange={(e) => navigate({ direction: e.target.value, page: 1 })}
                >
                  <option value="">{t("All directions")}</option>
                  <option value="incoming">{t("Incoming")}</option>
                  <option value="outgoing">{t("Outgoing")}</option>
                </select>
              ) : (
                <label className="text-sm">
                  <span className="sr-only">{t("Exact account")}</span>
                  <input
                    className="br-control"
                    aria-label={t("Exact account")}
                    value={account}
                    placeholder={t("Exact account")}
                    onChange={(e) => navigate({ account: e.target.value, page: 1 })}
                  />
                </label>
              )}
            </>
          }
        />
        <PageActionBar
          actions={[
            ...financeActions,
            canAcceptReduction && {
              key: "opening-positions",
              label: "Import opening positions",
              onClick: () => setOpening(true),
            },
          ]}
        />

        {!data ? (
          <ReadState loading={read.loading} error={read.error} retry={read.refresh} rows={8} />
        ) : (
          <>
            {data.view === "open-items" && (
              <ProjectionFreshness
                metadata={data.metadata}
                refresh={read.refresh}
                loading={read.loading}
                error={read.error}
              />
            )}
            {data.view !== "payments" && data.totals.length > 0 && (
              <div data-finance-controls className="mb-6 grid gap-3 md:grid-cols-2">
                {data.totals.map((total) => {
                  const journal = total as JournalTotal,
                    open = total as FinancialTotals,
                    balances = total as BalanceTotals;
                  const values =
                    data.view === "journal"
                      ? [
                          ["Debit", journal.debit],
                          ["Credit", journal.credit],
                          ["Balance", journal.balance],
                        ]
                      : data.view === "balances"
                        ? [
                            ["Open", balances.open],
                            ["Of which overdue", balances.overdue],
                            ["Available credit", balances.credit],
                            ["Balance", balances.balance],
                          ]
                        : [
                            [creditBalance ? "Original credit" : "Gross", open.gross!],
                            [creditBalance ? "Used credit" : "Settled", open.settled!],
                            [creditBalance ? "Available credit" : "Open", open.open!],
                          ];
                  return (
                    <section
                      key={total.currency}
                      className="rounded-xl border border-border-default bg-surface-muted p-5"
                    >
                      <h2 className="mb-4 text-sm font-medium">
                        {total.currency} · {t("All filtered records")}
                      </h2>
                      <dl
                        className={`grid gap-3 ${values.length === 4 ? "sm:grid-cols-4" : "sm:grid-cols-3"}`}
                      >
                        {values.map(([label, value]) => (
                          <div key={label}>
                            <dt className="text-xs text-fg-muted">{t(label)}</dt>
                            <dd className="mt-1 break-words text-lg font-semibold text-fg-strong">
                              {money(value, total.currency)}
                            </dd>
                          </div>
                        ))}
                      </dl>
                    </section>
                  );
                })}
              </div>
            )}
            {!awaitingCalculation && (
              <div className="min-w-0">
                <RegisterTable
                  actionWidth={view === "open-items" ? 140 : view === "balances" ? 170 : 80}
                  busy={read.loading}
                  className="w-full min-w-[780px] text-sm"
                  footer={
                    awaitingCalculation ? undefined : (
                      <RegisterPager page={data.page} change={(page) => navigate({ page })} />
                    )
                  }
                >
                  <thead>
                    <tr className="border-b border-border-default text-left text-fg-muted">
                      {(view === "open-items"
                        ? [
                            creditBalance
                              ? "Credit origin / party"
                              : flow === "customer-credit"
                                ? "Credit / party"
                                : "Invoice / party",
                            "Date",
                            creditBalance ? "Original credit" : "Gross",
                            creditBalance ? "Used credit" : "Settled",
                            creditBalance ? "Available credit" : "Open",
                            "Status",
                            "Details",
                          ]
                        : view === "balances"
                          ? [
                              "Party / currency",
                              "Open",
                              "Of which overdue",
                              "Available credit",
                              "Balance",
                              "Open documents",
                              "Credit documents",
                              "Oldest due",
                              "Details",
                            ]
                          : view === "payments"
                            ? [
                                "Payment / party",
                                "Direction",
                                "Amount",
                                "Allocated",
                                "Unallocated",
                                "Status",
                                "Details",
                              ]
                            : [
                                "Account / posting",
                                "Date",
                                "Debit",
                                "Credit",
                                "Currency",
                                "Details",
                              ]
                      ).map((label) => (
                        <th key={label} className="pb-3 pr-4">
                          {t(label)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.view === "open-items"
                      ? data.items.map((row) => (
                          <Fragment key={row.document_id}>
                            <tr className="border-b border-border-default">
                              <td className="py-5 pr-4">
                                <strong className="block text-fg-strong">
                                  {row.number || row.document_id}
                                </strong>
                                <span className="mt-1 block text-xs text-fg-muted">
                                  {row.party}
                                </span>
                                {row.document_type.startsWith("opening_") && !creditBalance && (
                                  <span className="mt-1 block text-xs text-fg-muted">
                                    {t(
                                      row.coverage_kind === "summary"
                                        ? "Summary opening position"
                                        : "Opening position",
                                    )}{" "}
                                    · {t("Due date")}: {row.original_due_date || t("Unknown")}
                                  </span>
                                )}
                                {creditBalance && (
                                  <span className="mt-1 block text-xs text-fg-muted">
                                    {t(
                                      row.document_type.startsWith("opening_")
                                        ? row.coverage_kind === "summary"
                                          ? "Summary opening position"
                                          : "Opening position"
                                        : row.document_type.endsWith("_payment")
                                          ? "Payment"
                                          : "Credit note",
                                    )}{" "}
                                    · {row.account_code}
                                  </span>
                                )}
                              </td>
                              <td className="py-5 pr-4 whitespace-nowrap">
                                {row.document_date || "—"}
                              </td>
                              {[row.gross, row.settled, row.open].map((value, i) => (
                                <td key={i} className="py-5 pr-4 whitespace-nowrap">
                                  {money(value, row.currency)}
                                </td>
                              ))}
                              <td className="py-5 pr-4">
                                {t(
                                  statuses.find(([value]) => value === row.status)?.[1] ||
                                    row.status,
                                )}
                              </td>
                              <td>{explain(row.document_id)}</td>
                            </tr>
                            <TablePreview
                              id={`finance-preview-${row.document_id}`}
                              open={entry === row.document_id}
                              columns={7}
                            >
                              <InlineInspector
                                tenant={tenant}
                                target={{ kind: "document", id: row.document_id }}
                                supplement={(detail) =>
                                  row.document_type === "sales_invoice" ? (
                                    <DocumentContributionExplanations
                                      tenant={tenant}
                                      detail={detail}
                                      source="document_lines"
                                    />
                                  ) : null
                                }
                              >
                                {[
                                  "sales_invoice",
                                  "supplier_invoice",
                                  "credit_note",
                                  "supplier_credit_note",
                                ].includes(row.document_type) && (
                                  <button
                                    className="br-btn"
                                    onClick={() => setDetailDocument(row.document_id)}
                                  >
                                    {t("Financial detail")}
                                  </button>
                                )}
                                {canAcceptReduction &&
                                  ["open", "partial"].includes(row.status) &&
                                  ([
                                    "sales_invoice",
                                    "supplier_invoice",
                                    "opening_customer_debt",
                                    "opening_supplier_debt",
                                  ].includes(row.document_type) ? (
                                    <button
                                      className="br-btn"
                                      onClick={() =>
                                        setSettlement({
                                          document: row.document_id,
                                          mode: "payment",
                                        })
                                      }
                                    >
                                      {t("Record payment and allocation")}
                                    </button>
                                  ) : (
                                    creditBalance && (
                                      <button
                                        className="br-btn"
                                        onClick={() =>
                                          setSettlement({
                                            document: row.document_id,
                                            mode: "allocate_credit",
                                          })
                                        }
                                      >
                                        {t("Use available credit")}
                                      </button>
                                    )
                                  ))}
                                {refund &&
                                  row.document_type === "credit_note" &&
                                  ["open", "partial"].includes(row.status) && (
                                    <button
                                      className="br-btn"
                                      onClick={() => refund(row.document_id)}
                                    >
                                      {t("Record refund")}
                                    </button>
                                  )}
                                {canAcceptReduction &&
                                  [
                                    "sales_invoice",
                                    "supplier_invoice",
                                    "opening_customer_debt",
                                    "opening_supplier_debt",
                                  ].includes(row.document_type) &&
                                  ["open", "partial"].includes(row.status) && (
                                    <button
                                      className="br-btn"
                                      onClick={() => setReductionInvoice(row.document_id)}
                                    >
                                      {t("Accept settlement reduction")}
                                    </button>
                                  )}
                                {credit && row.document_type === "sales_invoice" && (
                                  <button
                                    className="br-btn"
                                    onClick={() => credit(row.document_id)}
                                  >
                                    {t("New credit note")}
                                  </button>
                                )}
                              </InlineInspector>
                            </TablePreview>
                          </Fragment>
                        ))
                      : data.view === "balances"
                        ? data.items.map((row) => (
                            <tr
                              key={`${row.party_id}:${row.currency}`}
                              className="border-b border-border-default"
                              data-party-balance={row.party_id}
                            >
                              <td className="py-5 pr-4">
                                <strong className="block text-fg-strong">{row.party}</strong>
                                <span className="mt-1 block text-xs text-fg-muted">
                                  {row.currency}
                                </span>
                              </td>
                              {[row.open, row.overdue, row.credit, row.balance].map((value, i) => (
                                <td key={i} className="py-5 pr-4 whitespace-nowrap">
                                  {money(value, row.currency)}
                                </td>
                              ))}
                              <td className="py-5 pr-4">{row.open_count}</td>
                              <td className="py-5 pr-4">{row.credit_count}</td>
                              <td className="py-5 pr-4 whitespace-nowrap">
                                {row.oldest_due_date || "—"}
                              </td>
                              <td className="whitespace-nowrap">
                                <button
                                  className="br-btn mr-2"
                                  onClick={() =>
                                    navigate({
                                      financeView: "open-items",
                                      flow: balanceSide === "customer" ? "receivable" : "payable",
                                      financeStatus: "outstanding",
                                      partyId: row.party_id,
                                      q: "",
                                      page: 1,
                                      entry: "",
                                    })
                                  }
                                >
                                  {t("Open items")}
                                </button>
                                {row.credit_count > 0 && (
                                  <button
                                    className="br-btn"
                                    onClick={() =>
                                      navigate({
                                        financeView: "open-items",
                                        flow:
                                          balanceSide === "customer"
                                            ? "customer-balance"
                                            : "supplier-balance",
                                        financeStatus: "outstanding",
                                        partyId: row.party_id,
                                        q: "",
                                        page: 1,
                                        entry: "",
                                      })
                                    }
                                  >
                                    {t("Available credit")}
                                  </button>
                                )}
                              </td>
                            </tr>
                          ))
                        : data.view === "payments"
                          ? data.items.map((row) => (
                              <Fragment key={row.id}>
                                <tr className="border-b border-border-default">
                                  <td className="py-5 pr-4">
                                    <strong className="block text-fg-strong">
                                      {row.reference || row.id}
                                    </strong>
                                    <span className="mt-1 block text-xs text-fg-muted">
                                      {row.party} · {formatDateTime(row.effective_at)}
                                    </span>
                                  </td>
                                  <td className="py-5 pr-4">
                                    {t(row.direction === "incoming" ? "Incoming" : "Outgoing")}
                                  </td>
                                  {[row.amount, row.allocated, row.unallocated].map((value, i) => (
                                    <td key={i} className="py-5 pr-4 whitespace-nowrap">
                                      {money(value, row.currency)}
                                    </td>
                                  ))}
                                  <td>
                                    {!row.reversal_role || row.reversal_role === "normal"
                                      ? t("Recorded")
                                      : t(
                                          row.reversal_role === "reversed_original"
                                            ? "Reversed original"
                                            : "Reversing entry",
                                        )}
                                  </td>
                                  <td>{explain(row.id)}</td>
                                </tr>
                                <TablePreview
                                  id={`finance-preview-${row.id}`}
                                  open={entry === row.id}
                                  columns={7}
                                >
                                  <InlineInspector
                                    tenant={tenant}
                                    target={{ kind: "payment", id: row.id }}
                                  >
                                    {reverse &&
                                      (!row.reversal_role || row.reversal_role === "normal") && (
                                        <button
                                          className="br-btn"
                                          onClick={() => reverse(row.posting_group_id)}
                                        >
                                          {t("Reverse posting")}
                                        </button>
                                      )}
                                  </InlineInspector>
                                </TablePreview>
                              </Fragment>
                            ))
                          : data.items.map((row) => (
                              <Fragment key={row.id}>
                                <tr className="border-b border-border-default">
                                  <td className="max-w-64 py-5 pr-4">
                                    <button
                                      className="text-accent underline"
                                      onClick={() =>
                                        navigate({
                                          account: row.account_id || row.account,
                                          page: 1,
                                          entry: "",
                                        })
                                      }
                                    >
                                      {row.account_code || row.account}
                                    </button>
                                    <span className="block text-sm text-fg-muted">
                                      {row.account_name}
                                    </span>
                                    <span className="mt-1 block break-all text-xs text-fg-muted">
                                      {row.posting_group_id}
                                    </span>
                                  </td>
                                  <td className="py-5 pr-4">{formatDateTime(row.effective_at)}</td>
                                  <td className="py-5 pr-4 whitespace-nowrap">
                                    {row.debit_credit === "debit"
                                      ? money(row.amount, row.currency)
                                      : "—"}
                                  </td>
                                  <td className="py-5 pr-4 whitespace-nowrap">
                                    {row.debit_credit === "credit"
                                      ? money(row.amount, row.currency)
                                      : "—"}
                                  </td>
                                  <td className="py-5 pr-4">{row.currency}</td>
                                  <td>{explain(row.inspect_id)}</td>
                                </tr>
                                <TablePreview
                                  id={`finance-preview-${row.inspect_id}`}
                                  open={entry === row.inspect_id}
                                  columns={6}
                                >
                                  <InlineInspector
                                    tenant={tenant}
                                    target={{ kind: "ledger_entry", id: row.inspect_id }}
                                  >
                                    {reverse && (
                                      <button
                                        className="br-btn"
                                        onClick={() => reverse(row.posting_group_id)}
                                      >
                                        {t("Reverse posting")}
                                      </button>
                                    )}
                                  </InlineInspector>
                                </TablePreview>
                              </Fragment>
                            ))}
                  </tbody>
                </RegisterTable>
              </div>
            )}
          </>
        )}
      </section>
      {detailDocument && (
        <FinancialComponents
          key={`${tenant}:${detailDocument}`}
          tenant={tenant}
          documentId={detailDocument}
          canManage={canAcceptReduction}
          close={() => setDetailDocument("")}
          explain={(id) => {
            setDetailDocument("");
            navigate({ entry: id });
          }}
        />
      )}
      {opening && (
        <OpeningItems
          key={tenant}
          tenant={tenant}
          close={() => {
            setOpening(false);
            read.refresh();
          }}
          explain={(id) => {
            setOpening(false);
            navigate({ financeView: "open-items", entry: id });
          }}
        />
      )}
      {settlement && (
        <SettlementFlow
          key={`${tenant}:${settlement.document}`}
          tenant={tenant}
          documentId={settlement.document}
          initialMode={settlement.mode}
          close={() => setSettlement(null)}
          explain={(id) => {
            setSettlement(null);
            navigate({ entry: id });
          }}
        />
      )}
      {reductionInvoice && (
        <SettlementReduction
          key={`${tenant}:${reductionInvoice}`}
          tenant={tenant}
          invoice={reductionInvoice}
          close={() => setReductionInvoice("")}
        />
      )}
    </>
  );
}

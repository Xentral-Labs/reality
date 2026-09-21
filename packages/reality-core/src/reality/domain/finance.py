"""Fixed operational roles, independent of human account codes."""

ACCOUNT_ROLES = {
    "accounts_receivable": "Customer receivables",
    "accounts_payable": "Supplier payables",
    "cash": "Cash and bank",
    "sales_revenue": "Gross sales counterpart",
    "inventory": "Gross purchase counterpart",
}
BASE_ACCOUNT_ROLES = dict(ACCOUNT_ROLES)
ACCOUNT_ROLES.update(
    {
        "opening_counterpart": "Neutral opening subledger counterpart",
        "customer_reduction": "Accepted customer settlement reduction",
        "supplier_reduction": "Accepted supplier settlement reduction",
        "bad_debt_expense": "Customer bad-debt expense",
        "dunning_fee_revenue": "Dunning fee revenue",
    }
)
CONTROL_ROLES = frozenset({"accounts_receivable", "accounts_payable"})


OPENING_DIRECTIONS = {
    "customer_debt": ("accounts_receivable", "debit"),
    "customer_credit": ("accounts_receivable", "credit"),
    "supplier_debt": ("accounts_payable", "credit"),
    "supplier_credit": ("accounts_payable", "debit"),
}
OPENING_DEBTS = {
    "opening_customer_debt": "customer",
    "opening_supplier_debt": "supplier",
}
OPENING_CREDITS = {
    "opening_customer_credit": "customer",
    "opening_supplier_credit": "supplier",
}

REFERENCE_KINDS = ("cost_center", "case_code", "coding_group")


# Read descriptions of supported services, not an executable posting rule engine.
# Fields: transaction, label, debit role, credit role, stated basis, control policy.
TRANSACTION_MATRIX = (
    (
        "sales_invoice",
        "Sales invoice",
        "accounts_receivable",
        "sales_revenue",
        "Stated invoice gross",
        "configured_default",
    ),
    (
        "credit_note",
        "Customer credit note",
        "sales_revenue",
        "accounts_receivable",
        "Stated credit total",
        "configured_default",
    ),
    (
        "customer_payment",
        "Customer payment",
        "cash",
        "accounts_receivable",
        "Stated payment amount",
        "original_when_linked",
    ),
    (
        "customer_refund",
        "Customer refund",
        "accounts_receivable",
        "cash",
        "Stated refund amount",
        "original_when_linked",
    ),
    (
        "supplier_invoice",
        "Supplier invoice",
        "inventory",
        "accounts_payable",
        "Stated invoice gross",
        "configured_default",
    ),
    (
        "supplier_credit_note",
        "Supplier credit note",
        "accounts_payable",
        "inventory",
        "Stated credit total",
        "configured_default",
    ),
    (
        "supplier_payment",
        "Supplier payment",
        "accounts_payable",
        "cash",
        "Stated payment amount",
        "original_when_linked",
    ),
    (
        "supplier_refund",
        "Supplier refund",
        "cash",
        "accounts_payable",
        "Stated refund amount",
        "original_when_linked",
    ),
    (
        "customer_settlement_adjustment",
        "Customer settlement reduction",
        "customer_reduction",
        "accounts_receivable",
        "Explicitly accepted reduction",
        "original_required",
    ),
    (
        "supplier_settlement_adjustment",
        "Supplier settlement reduction",
        "accounts_payable",
        "supplier_reduction",
        "Explicitly accepted reduction",
        "original_required",
    ),
    (
        "dunning_fee_charge",
        "Dunning fee charge",
        "accounts_receivable",
        "dunning_fee_revenue",
        "Stated dunning fee",
        "configured_default",
    ),
    (
        "opening_customer_debt",
        "Opening customer debt",
        "accounts_receivable",
        "opening_counterpart",
        "Stated opening residual",
        "configured_default",
    ),
    (
        "opening_customer_credit",
        "Opening customer credit",
        "opening_counterpart",
        "accounts_receivable",
        "Stated opening residual",
        "configured_default",
    ),
    (
        "opening_supplier_debt",
        "Opening supplier debt",
        "opening_counterpart",
        "accounts_payable",
        "Stated opening residual",
        "configured_default",
    ),
    (
        "opening_supplier_credit",
        "Opening supplier credit",
        "accounts_payable",
        "opening_counterpart",
        "Stated opening residual",
        "configured_default",
    ),
)

"""Independent company-world oracle and released observations."""

from copy import deepcopy
from decimal import Decimal

ROLES = (
    "cash",
    "accounts_receivable",
    "accounts_payable",
    "sales_revenue",
    "inventory",
    "payment_fee_expense",
)
POSTINGS = {
    "sales_invoice": ("accounts_receivable", "sales_revenue"),
    "customer_payment": ("cash", "accounts_receivable"),
    "supplier_invoice": ("inventory", "accounts_payable"),
    "supplier_payment": ("accounts_payable", "cash"),
    "sales_credit": ("sales_revenue", "accounts_receivable"),
    "customer_refund": ("accounts_receivable", "cash"),
    "provider_charge": ("cash", "accounts_receivable"),
    "provider_refund": ("accounts_receivable", "cash"),
    "provider_fee": ("payment_fee_expense", "cash"),
    "payout_deposit": ("cash", "cash"),
}


def number(value) -> str:
    return format(Decimal(value).normalize(), "f")


class CompleteWorld:
    def __init__(self, scenario):
        self.scenario = deepcopy(scenario)
        self.requests = {}
        self.purchases = {}
        self.locations = {
            name: {sku: 0 for sku in scenario["items"]}
            for name in scenario["locations"]
        }
        self.locations["W1"].update(scenario["opening"])
        self.events = []
        self.messages = []
        self.documents = {}
        self.finance_actions = []
        self.accounts = {role: Decimal(0) for role in ROLES}
        self.exercised = set()

    def mark(self, kind, day, **data):
        self.exercised.add(kind)
        self.events.append({"kind": kind, "day": day, **data})

    def release(self, day):
        released = []
        for source in self.scenario["requests"]:
            if source["day"] == day:
                request = {
                    **deepcopy(source),
                    "cancelled": False,
                    "cancel_requested": False,
                    "dispatched": 0,
                    "shipments": [],
                    "invoice": None,
                    "return_announced": None,
                    "returned": 0,
                    "credit": None,
                }
                self.requests[source["id"]] = request
                released.append(request)
                self.mark("customer_order", day, id=source["id"])
        for request in self.requests.values():
            if request.get("cancel_day") == day:
                request["cancel_requested"] = True
                self.mark("customer_cancellation", day, id=request["id"])
        return released

    def view(self, day):
        requests = []
        for request in self.requests.values():
            # Conditional future customer behavior remains private world data.
            visible = {
                k: deepcopy(request[k])
                for k in (
                    "id",
                    "day",
                    "deadline",
                    "customer",
                    "sku",
                    "quantity",
                    "amount",
                    "cancelled",
                    "cancel_requested",
                    "dispatched",
                    "invoice",
                    "shipments",
                    "return_announced",
                    "returned",
                    "credit",
                )
            }
            if (
                request["cancel_requested"]
                or request["dispatched"] == request["quantity"]
            ):
                visible["billing_statement"] = {
                    "quantity": request["invoice_quantity"],
                    "amount": request["invoice_amount"],
                }
            if request["return_announced"]:
                visible["return_claim"] = {
                    "quantity": request["return"]["quantity"],
                    "amount": request["return"]["amount"],
                }
            visible["dispatch_limit"] = request.get(
                "dispatch_limit", request["quantity"]
            )
            requests.append(visible)
        return {
            "day": day,
            "requests": requests,
            "stock": deepcopy(self.locations),
            "purchases": [
                {
                    "id": p["id"],
                    "sku": p["sku"],
                    "quantity": p["quantity"],
                    "fulfilled": p["fulfilled"],
                    "invoice": p["invoice"],
                    "quoted_arrival_days": [
                        p["issued_day"] + d["after"]
                        for d in self.scenario["quote"]["deliveries"]
                    ],
                }
                for p in self.purchases.values()
            ],
            "quote": {
                k: deepcopy(v)
                for k, v in self.scenario["quote"].items()
                if k not in {"delay_sku", "delay_days"}
            },
            "address": deepcopy(self.scenario["address"]),
            "messages": deepcopy(self.messages),
        }

    def purchase(self, label, sku, day):
        quote = self.scenario["quote"]
        deliveries = [
            {
                "day": day
                + d["after"]
                + (quote["delay_days"] if sku == quote["delay_sku"] else 0),
                "quantity": d["quantity"],
                "received": False,
            }
            for d in quote["deliveries"]
        ]
        self.purchases[label] = {
            "id": label,
            "issued_day": day,
            "sku": sku,
            "quantity": quote["pack_quantity"],
            "fulfilled": 0,
            "deliveries": deliveries,
            "invoice": None,
        }
        self.mark("purchase_order", day, id=label)
        if sku == quote["delay_sku"]:
            self.mark("supplier_delay", day, id=label)

    def book(
        self, label, kind, amount, entry_ids, day, *, document_id=None, party_id=None
    ):
        amount = Decimal(amount)
        debit, credit = POSTINGS[kind]
        self.accounts[debit] += amount
        self.accounts[credit] -= amount
        self.finance_actions.append(
            {
                "label": label,
                "kind": kind,
                "amount": number(amount),
                "debit": debit,
                "credit": credit,
                "entry_ids": entry_ids,
                "document_id": document_id,
                "party_id": party_id,
            }
        )
        self.mark(kind, day, id=label, ledger_entry_ids=entry_ids)

    def expected(self):
        skus = self.scenario["items"]
        lines = {}
        for request in self.requests.values():
            lines[f"{request['id']}:{request['sku']}"] = {
                "quantity": str(request["quantity"]),
                "fulfilled": str(request["dispatched"]),
                "open": str(
                    0
                    if request["cancelled"]
                    else request["quantity"] - request["dispatched"]
                ),
                "reserved": "0",
                "line_amount": request["amount"],
                "document_amount": request["amount"],
            }
        for purchase in self.purchases.values():
            lines[f"{purchase['id']}:{purchase['sku']}"] = {
                "quantity": str(purchase["quantity"]),
                "fulfilled": str(purchase["fulfilled"]),
                "open": str(purchase["quantity"] - purchase["fulfilled"]),
                "reserved": "0",
                "line_amount": self.scenario["quote"]["pack_amount"],
                "document_amount": self.scenario["quote"]["pack_amount"],
            }
        return {
            "physical": {
                s: str(sum(loc[s] for loc in self.locations.values())) for s in skus
            },
            "locations": {
                loc: {s: str(q) for s, q in values.items()}
                for loc, values in self.locations.items()
            },
            "reserved": {s: "0" for s in skus},
            "lines": lines,
            "customer_open": {
                s: str(
                    sum(
                        r["quantity"] - r["dispatched"]
                        for r in self.requests.values()
                        if r["sku"] == s and not r["cancelled"]
                    )
                )
                for s in skus
            },
            "supplier_open": {
                s: str(
                    sum(
                        p["quantity"] - p["fulfilled"]
                        for p in self.purchases.values()
                        if p["sku"] == s
                    )
                )
                for s in skus
            },
            "return_open": {
                s: str(
                    sum(
                        r.get("return_quantity", 0) - r["returned"]
                        for r in self.requests.values()
                        if r["sku"] == s
                    )
                )
                for s in skus
            },
            "counts": {
                "sales_orders": len(self.requests),
                "purchase_orders": len(self.purchases),
                "ledger_entries": sum(
                    len(a["entry_ids"]) for a in self.finance_actions
                ),
            },
        }

    def expected_finance(self):
        result = {
            "accounts": {role: number(value) for role, value in self.accounts.items()},
            "open_balances": {
                label: number(d["open"]) for label, d in self.documents.items()
            },
            "errors": [],
        }
        if hasattr(self, "cash_accounts"):
            result["cash_accounts"] = {
                key: number(value) for key, value in self.cash_accounts.items()
            }
        if hasattr(self, "held_payments"):
            result["unallocated_payments"] = {
                label: number(value["open"])
                for label, value in self.held_payments.items()
            }
        return result

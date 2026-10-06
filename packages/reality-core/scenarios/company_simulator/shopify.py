"""Explicitly synthetic Shopify-shaped sources and provider payout statements."""

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import yaml
from sqlalchemy import select

from scenarios.company_simulator.complete import CompanyRun
from scenarios.company_simulator.complete_world import number
from scenarios.harness.observer import differences, observe

SHOPIFY_PLANNED = sorted(
    {
        "customer_order",
        "shopify_order",
        "shopify_refund",
        "customer_dispatch",
        "package_delivery",
        "sales_invoice",
        "return_announcement",
        "return_receipt",
        "sales_credit",
        "provider_charge",
        "provider_refund",
        "provider_fee",
        "payout_deposit",
        "payout_replay",
        "provider_unmatched",
    }
)


def shopify_profile():
    return yaml.safe_load(
        (Path(__file__).parent / "profiles/shopify_company/scenario.yaml").read_text()
    )


class ShopifyRun(CompanyRun):
    planned = SHOPIFY_PLANNED

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unmatched = {"charges": Decimal(0), "refunds": Decimal(0)}
        self.unallocated = {"charges": Decimal(0), "refunds": Decimal(0)}
        self.payouts = []
        self.replayed = False
        self.totals = {
            "charges": Decimal(0),
            "refunds": Decimal(0),
            "fees": Decimal(0),
            "bank_deposits": Decimal(0),
        }
        self.refund_sources = []
        self.raw_sources = []

    def initialize(self):
        from reality.services.finance.accounts import list_accounts

        super().initialize()
        tid = self.bridge.tenant_id
        provider = self.call(
            "party_create",
            {
                "records": [
                    {
                        "name": "Synthetic Shopify Payments provider",
                        "roles": ["supplier"],
                    }
                ]
            },
        )
        self.provider = provider["records"][0]["id"]
        state = list_accounts(self.session, tid)
        if "payment_fee_expense" not in state["defaults"]:
            created = self.call(
                "finance.account.create",
                {
                    "code": "SIM-FEE",
                    "name": "Synthetic provider fees",
                    "role": "payment_fee_expense",
                    "expected_revision": state["revision"],
                },
            )
            self.call(
                "finance.account.set_default",
                {
                    "role": "payment_fee_expense",
                    "account_id": created["id"],
                    "expected_revision": list_accounts(self.session, tid)["revision"],
                },
            )
        clearing = self.call(
            "finance.account.create",
            {
                "code": "SIM-PSP",
                "name": "Synthetic provider clearing",
                "role": "cash",
                "expected_revision": list_accounts(self.session, tid)["revision"],
            },
        )
        self.clearing = clearing["id"]
        self.bank = list_accounts(self.session, tid)["defaults"]["cash"]
        self.world.held_payments = {}
        self.world.cash_accounts = {self.bank: Decimal(0), self.clearing: Decimal(0)}

    def intake(self, source_type, payload, context=None):
        from reality.services.intake import (
            apply_prepared_intake,
            prepare_intake,
            review_intake,
        )
        from reality.services.memberships import Principal

        tid = self.bridge.tenant_id
        source = super().call(
            "source_record_ingest",
            {
                "source_system": "shopify",
                "source_type": source_type,
                "external_id": str(payload["id"]),
                "payload": payload,
                "context": context or {},
            },
        )
        before = observe(self.session, tid)
        proposal = prepare_intake(
            self.session, tid, source["import_job_id"], _commit=False
        )
        review = review_intake(self.session, tid, proposal.id)
        prepared = observe(self.session, tid)
        keys = ("counts", "physical", "reserved", "lines", "record_ids")
        if differences({k: before[k] for k in keys}, {k: prepared[k] for k in keys}):
            raise RuntimeError("Shopify preparation changed accepted reality")
        accepted = apply_prepared_intake(
            self.session,
            tid,
            proposal.id,
            review["digest"],
            confirmed=True,
            principal=Principal(self.owner),
            _commit=False,
        )
        receipt = json.loads(accepted.output)
        self.recorder.append(
            "events.jsonl",
            {
                "phase": "committed",
                "tool": "reviewed_shopify_intake",
                "scenario_day": self.day,
                "proposal_id": proposal.id,
                "source_record_id": source["source_record_id"],
                "receipt": receipt,
            },
        )
        self.raw_sources.append(
            {"source_record_id": source["source_record_id"], "payload": payload}
        )
        return receipt

    def order(self, label, sku, quantity, amount, customer=None):
        if customer is None:
            return super().order(label, sku, quantity, amount, customer)
        from scenarios.company_simulator.bridge import record_ids

        request = next(r for r in self.scenario["requests"] if r["id"] == label)
        payload = {
            "id": request["shop_id"],
            "name": label,
            "order_number": request["shop_id"],
            "currency": "EUR",
            "created_at": datetime.now(UTC).isoformat(),
            "total_price": amount,
            "customer": {
                "id": request["shop_id"] + 100,
                "email": "synthetic@example.invalid",
            },
            "shipping_address": dict(self.scenario["address"]),
            "line_items": [
                {
                    "id": request["shop_id"] + 1000,
                    "sku": sku,
                    "name": self.scenario["items"][sku]["name"],
                    "quantity": quantity,
                    "price": self.scenario["items"][sku]["sales_price"],
                    "total_price": amount,
                }
            ],
            "_fixture_note": "Synthetic authored Shopify-shaped order, not an original customer export",
        }
        receipt = self.intake(
            "order",
            payload,
            {
                "company_party_id": self.refs["parties"]["COMPANY"],
                "customer_party_id": self.refs["parties"][customer],
                "location_id": self.refs["locations"]["W1"],
            },
        )
        self.orders[label] = {
            "document_id": record_ids(receipt, "document")[0],
            "source_record_id": receipt["source_record_id"],
            "commitment_id": record_ids(receipt, "commitment")[0],
            "line_id": record_ids(receipt, "document_line")[0],
        }
        self.world.mark("shopify_order", self.day, id=label)
        return receipt

    def native_refund(self, request):
        from scenarios.company_simulator.bridge import record_ids

        if request.get("shop_refund_receipt"):
            return request["shop_refund_receipt"]
        amount = request["return"]["amount"]
        payload = {
            "id": request["shop_id"] + 5000,
            "order_id": request["shop_id"],
            "created_at": datetime.now(UTC).isoformat(),
            "refund_line_items": [
                {
                    "line_item_id": request["shop_id"] + 1000,
                    "quantity": request["return"]["quantity"],
                    "subtotal": amount,
                    "restock_type": "return",
                }
            ],
            "transactions": [
                {
                    "id": request["shop_id"] + 6000,
                    "kind": "refund",
                    "status": "success",
                    "amount": amount,
                    "currency": "EUR",
                }
            ],
            "_fixture_note": "Synthetic shop refund evidence; not a warehouse receipt or bank payout",
        }
        receipt = self.intake("refund", payload)
        request["shop_refund_receipt"] = receipt
        self.refund_sources.append(receipt["source_record_id"])
        self.world.mark("shopify_refund", self.day, id=request["id"])
        announcements = record_ids(receipt, "return_announcement")
        if announcements:
            request["return_announced"] = announcements[0]
            request["return_quantity"] = request["return"]["quantity"]
        return receipt

    def call(self, tool, args, operator_action=False):
        if tool == "return_announce":
            from scenarios.company_simulator.bridge import record_ids

            request = next(
                r
                for r in self.world.requests.values()
                if r["commitment_id"] == args["commitment_id"]
            )
            return record_ids(self.native_refund(request), "return_announcement")[0]
        return super().call(tool, args, operator_action)

    def financial(self, label, kind, amount, args, *, target=None, party=None):
        if kind in {"customer_payment", "customer_refund"}:
            # Provider evidence is exogenous; no separate bank payment is invented here.
            return {}
        return super().financial(label, kind, amount, args, target=target, party=party)

    def process_world(self):
        super().process_world()
        if self.day == self.scenario["shop_refund_day"]:
            for request in self.world.requests.values():
                if request.get("return"):
                    self.native_refund(request)
        for statement in self.scenario["payouts"]:
            if statement["day"] == self.day:
                self.settle(statement)

    def settle(self, statement):
        from reality.db.core import LedgerEntry

        pending = {}
        for line in statement["lines"]:
            request = self.world.requests.get(line.get("request"))
            target = (
                (("INV-" if line["kind"] == "charge" else "CR-") + line["request"])
                if request
                else None
            )
            pending[line["id"]] = {
                "kind": line["kind"],
                "amount": line["amount"],
                "target": target,
                "party": self.refs["parties"][request["customer"]] if request else None,
                "shop_id": request["shop_id"] if request else line["shop_id"],
            }
        lines = [
            {
                "line_id": key,
                "kind": p["kind"],
                "amount": p["amount"],
                "references": [{"type": "shop_id", "value": str(p["shop_id"])}],
            }
            for key, p in pending.items()
        ]
        lines.append(
            {
                "line_id": "fee",
                "kind": "fee",
                "amount": statement["fee"],
                "references": [],
            }
        )
        args = {
            "provider_party_id": self.provider,
            "payout_reference": statement["id"],
            "paid_on": datetime.now(UTC).date().isoformat(),
            "currency": "EUR",
            "amount": statement["amount"],
            "clearing_account_id": self.clearing,
            "bank_account_id": self.bank,
            "lines": lines,
        }
        receipt = self.call("finance.payout.settle", args)
        for line in receipt["lines"]:
            if line["kind"] != "fee":
                source = pending[line["line_id"]]
                total_key = "charges" if line["kind"] == "charge" else "refunds"
                self.totals[total_key] += Decimal(source["amount"])
                target = self.world.documents.get(source["target"])
                expected_booked = source["party"] is not None
                if (line["state"] == "booked") != expected_booked:
                    raise RuntimeError(
                        "Provider receipt differs from independent invoice/credit availability"
                    )
                if not expected_booked:
                    self.unmatched[total_key] += Decimal(source["amount"])
                    self.world.mark("provider_unmatched", self.day, id=line["line_id"])
                    continue
            entries = list(
                self.session.scalars(
                    select(LedgerEntry).where(
                        LedgerEntry.tenant_id == self.bridge.tenant_id,
                        LedgerEntry.document_id == line["document_id"],
                    )
                )
            )
            if line["kind"] == "fee":
                kind, amount, party = "provider_fee", statement["fee"], self.provider
                self.totals["fees"] += Decimal(amount)
                self.world.cash_accounts[self.clearing] -= Decimal(amount)
            else:
                source = pending[line["line_id"]]
                kind, amount, party = (
                    "provider_" + line["kind"],
                    source["amount"],
                    source["party"],
                )
                target_document = self.world.documents.get(source["target"])
                allocated = (
                    Decimal(amount) if target_document is not None else Decimal(0)
                )
                if target_document is not None:
                    target_document["open"] -= allocated
                else:
                    self.unallocated[
                        "charges" if line["kind"] == "charge" else "refunds"
                    ] += Decimal(amount)
                    self.world.mark(
                        "provider_unallocated", self.day, id=line["line_id"]
                    )
                self.world.held_payments[statement["id"] + ":" + line["line_id"]] = {
                    "id": line["document_id"],
                    "open": Decimal(amount) - allocated,
                    "kind": "held_provider_payment",
                }

                self.world.cash_accounts[self.clearing] += (
                    Decimal(amount) if line["kind"] == "charge" else -Decimal(amount)
                )
            self.world.book(
                statement["id"] + ":" + line["line_id"],
                kind,
                amount,
                [e.id for e in entries],
                self.day,
                document_id=line["document_id"],
                party_id=party,
            )
            action = self.world.finance_actions[-1]
            action[
                "debit_account_id" if kind == "provider_charge" else "credit_account_id"
            ] = self.clearing
            if line["kind"] != "fee" and source["target"] in self.world.documents:
                action["allocation_to"] = source["target"]
        entries = list(
            self.session.scalars(
                select(LedgerEntry).where(
                    LedgerEntry.tenant_id == self.bridge.tenant_id,
                    LedgerEntry.document_id == receipt["id"],
                )
            )
        )
        self.world.book(
            statement["id"],
            "payout_deposit",
            statement["amount"],
            [e.id for e in entries],
            self.day,
            document_id=receipt["id"],
            party_id=self.provider,
        )
        self.world.finance_actions[-1].update(
            debit_account_id=self.bank, credit_account_id=self.clearing
        )
        self.world.cash_accounts[self.bank] += Decimal(statement["amount"])
        self.world.cash_accounts[self.clearing] -= Decimal(statement["amount"])
        self.totals["bank_deposits"] += Decimal(statement["amount"])
        self.payouts.append(receipt)
        if not self.replayed:
            before = observe(self.session, self.bridge.tenant_id)
            repeated = self.call("finance.payout.settle", args)
            after = observe(self.session, self.bridge.tenant_id)
            if {k: v for k, v in before.items() if k != "event_cutoff"} != {
                k: v for k, v in after.items() if k != "event_cutoff"
            } or repeated["id"] != receipt["id"]:
                raise RuntimeError("Payout replay changed accepted reality")
            self.replayed = True
            self.world.mark("payout_replay", self.day, id=statement["id"])

    def run(self):
        result = super().run()
        result["coverage"] = {
            "planned": SHOPIFY_PLANNED,
            "exercised": sorted(set(SHOPIFY_PLANNED) & self.world.exercised),
            "not_exercised": sorted(set(SHOPIFY_PLANNED) - self.world.exercised),
        }
        result["shopify"] = {
            "synthetic": True,
            **{k: number(v) for k, v in self.totals.items()},
            "payouts": self.payouts,
            "clearing_balance": number(self.world.cash_accounts[self.clearing]),
            "replay_no_effect": self.replayed,
            "refund_source_ids": self.refund_sources,
            "unmatched_charges": number(self.unmatched["charges"]),
            "unmatched_refunds": number(self.unmatched["refunds"]),
            "unallocated_charges": number(self.unallocated["charges"]),
            "unallocated_refunds": number(self.unallocated["refunds"]),
            "raw_sources": self.raw_sources,
        }
        self.recorder.write("report.json", result)
        with (self.recorder.directory / "report.md").open("a") as report:
            report.write(
                "\nSynthetic Shopify-shaped sources; synthetic provider statement, not an original Shopify export.\n"
            )
            report.write(
                f"\nCharges: {result['shopify']['charges']}; refunds: {result['shopify']['refunds']}; fees: {result['shopify']['fees']}; bank deposits: {result['shopify']['bank_deposits']}.\n"
            )
        return result


def run_shopify(session, owner_id, *, days, operator, output_root, confirmed=False):
    if (
        confirmed is not True
        or type(days) is not int
        or not 1 <= days <= 30
        or operator not in {"prompt", "idle"}
    ):
        raise ValueError(
            "Explicit confirmation, supported operator and 1–30 day horizon required"
        )
    return ShopifyRun(
        session, owner_id, shopify_profile(), days, operator, output_root, None
    ).run()

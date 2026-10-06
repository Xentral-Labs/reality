"""Extended reactive company rehearsal using production financial/logistics tools."""

from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import yaml

from scenarios.company_simulator import complete_observer
from scenarios.company_simulator.complete_world import CompleteWorld
from scenarios.harness.observer import differences, observe
from scenarios.harness.reporting import Recorder, encode, timestamp

PLANNED = sorted(
    {
        "customer_order",
        "customer_message",
        "customer_status_query",
        "customer_return",
        "supplier_confirmation",
        "supplier_delay_notice",
        "supplier_receipt",
        "agent_reply",
        "purchase_order",
        "partial_supplier_receipt",
        "supplier_delay",
        "partial_customer_dispatch",
        "customer_dispatch",
        "package_delivery",
        "carrier_exception",
        "delivery_failure",
        "customer_cancellation",
        "cancel_commitment",
        "return_announcement",
        "return_receipt",
        "stock_adjustment",
        "warehouse_transfer",
        "sales_invoice",
        "customer_payment",
        "supplier_invoice",
        "supplier_payment",
        "sales_credit",
        "customer_refund",
    }
)


def complete_profile():
    return yaml.safe_load(
        (Path(__file__).parent / "profiles/general_company/complete.yaml").read_text()
    )


class InitialCheckpointFailed(Exception):
    """Stop before releasing demand when the initial oracle fails."""


class CompanyRun:
    planned = PLANNED

    def __init__(self, session, owner, scenario, days, operator, output_root, review):
        from reality.services.company_setup import create_company
        from scenarios.company_simulator.bridge import ToolBridge

        self.scenario = deepcopy(scenario)
        self.session, self.owner, self.days, self.operator = (
            session,
            owner,
            days,
            operator,
        )
        self.run_id = uuid4().hex
        self.recorder = Recorder(Path(output_root) / self.run_id)
        self.world = CompleteWorld(scenario)
        self.bridge = ToolBridge(
            session,
            owner,
            scenario,
            self.run_id,
            self.recorder,
            datetime.now(UTC),
            supervised=callable(operator),
            review=review,
        )
        setup = create_company(
            session,
            owner,
            f"complete-company:{self.run_id}",
            f"Company Month {self.run_id}",
            "business",
            "empty",
            confirmed=True,
        )
        self.bridge.tenant_id = setup["tenant_id"]
        self.refs = self.bridge.refs
        self.orders = {}
        self.correspondence = None
        if scenario.get("correspondence"):
            from scenarios.company_simulator.correspondence import Correspondence

            self.correspondence = Correspondence(self)
        self.day = 0
        self.spectator_error = None
        self.recorder.write(
            "manifest.json",
            {
                "run_id": self.run_id,
                "company_id": setup["tenant_id"],
                "setup_receipt": setup,
                "owner_id": owner,
                "profile_id": scenario["id"],
                "profile_hash": sha256(encode(scenario).encode()).hexdigest(),
                "days": days,
                "operator": "supervised_custom" if callable(operator) else operator,
                "clock": "ordinal scenario days; application clock remains real",
                "source_hashes": {
                    p.name: sha256(p.read_bytes()).hexdigest()
                    for p in Path(__file__).parent.glob("*.py")
                },
            },
        )

    def call(self, tool, args, operator_action=False):
        self.bridge.day = self.day
        return self.bridge.call(tool, args, operator_action=operator_action)

    def order(self, label, sku, quantity, amount, customer=None):
        receipt = self.call(
            "order_create",
            {
                "direction": "sales" if customer else "purchase",
                "number": label,
                "company_party_id": self.refs["parties"]["COMPANY"],
                "counterparty_id": self.refs["parties"][customer or "SUPPLIER"],
                "location_id": self.refs["locations"]["W1"],
                "currency": "EUR",
                "gross_amount": amount,
                "lines": [
                    {
                        "item_id": self.refs["items"][sku],
                        "quantity": str(quantity),
                        "unit_price": self.scenario["items"][sku][
                            "sales_price" if customer else "purchase_price"
                        ],
                        "gross_amount": amount,
                    }
                ],
            },
            operator_action=customer is None,
        )
        self.orders[label] = {
            "document_id": receipt["document_id"],
            "source_record_id": receipt["source_record_id"],
            "commitment_id": receipt["commitment_ids"][0],
            "line_id": receipt["document_line_ids"][0],
        }
        return receipt

    def initialize(self):
        from reality.services.finance.accounts import list_accounts

        self.bridge.masters({"id": "setup", "scenario_time": "day:0"})
        state = list_accounts(self.session, self.bridge.tenant_id)
        self.call(
            "finance.account.initialize", {"expected_revision": state["revision"]}
        )
        for sku, quantity in self.scenario["opening"].items():
            self.call(
                "movement_create",
                {
                    "movement_type": "opening_stock",
                    "item_id": self.refs["items"][sku],
                    "quantity": str(quantity),
                    "to_location_id": self.refs["locations"]["W1"],
                },
            )

    def financial(self, label, kind, amount, args, *, target=None, party=None):
        from scenarios.company_simulator.bridge import record_ids

        tool = {
            "sales_invoice": "sales_invoice_record",
            "supplier_invoice": "supplier_invoice_record",
            "customer_payment": "customer_payment_post",
            "supplier_payment": "supplier_payment_post",
            "sales_credit": "sales_credit_record",
            "customer_refund": "customer_refund_post",
        }[kind]
        if kind in {"customer_payment", "supplier_payment", "customer_refund"}:
            source = self.call(
                "source_record_ingest",
                {
                    "source_system": "manual",
                    "source_type": "simulated_bank_transaction",
                    "external_id": self.run_id + ":" + label,
                    "payload": dict(args),
                },
            )
            args = {**args, "source_record_id": source["source_record_id"]}
        receipt = self.call(
            tool,
            args,
            operator_action=kind
            in {
                "sales_invoice",
                "supplier_invoice",
                "supplier_payment",
                "sales_credit",
            },
        )
        documents = record_ids(receipt, "document")
        self.world.book(
            label,
            kind,
            amount,
            record_ids(receipt, "ledger_entry"),
            self.day,
            document_id=documents[0] if documents else None,
            party_id=party,
        )
        if target:
            self.world.documents[target]["open"] -= Decimal(amount)
            self.world.finance_actions[-1]["allocation_to"] = target
        if kind in {"sales_invoice", "supplier_invoice", "sales_credit"}:
            self.world.documents[label] = {
                "id": documents[0],
                "open": Decimal(amount),
                "kind": kind,
                "line_ids": record_ids(receipt, "document_line"),
                "day": self.day,
            }
        return receipt

    def invoice_request(self, request):
        label = "INV-" + request["id"]
        amount = request["invoice_amount"]
        self.financial(
            label,
            "sales_invoice",
            amount,
            {
                "number": label,
                "gross_amount": amount,
                "lines": [
                    {
                        "order_line_id": self.orders[request["id"]]["line_id"],
                        "quantity": str(request["invoice_quantity"]),
                        "gross_amount": amount,
                    }
                ],
            },
            party=self.refs["parties"][request["customer"]],
        )
        request["invoice"] = label
        request["invoice_day"] = self.day
        request["payment_events"] = [
            {**p, "day": self.day + p["after"], "done": False}
            for p in request["payments"]
        ]

    def process_world(self):
        for request in self.world.release(self.day):
            if self.correspondence:
                row = self.correspondence.order(request)
                request["message_source_id"] = row["source_record_id"]
            else:
                message = {
                    "message_id": self.run_id + ":" + request["id"],
                    "from": "customer@example.invalid",
                    "to": "company@example.invalid",
                    "subject": "Order " + request["id"],
                    "body": {
                        "item": request["sku"],
                        "quantity": request["quantity"],
                        "stated_amount": request["amount"],
                        "deadline_day": request["deadline"],
                        "destination": self.scenario["address"],
                    },
                    "synthetic": True,
                }
                source = self.call(
                    "source_record_ingest",
                    {
                        "source_system": "manual",
                        "source_type": "simulated_customer_email",
                        "external_id": message["message_id"],
                        "payload": message,
                        "context": {
                            "customer_party_id": self.refs["parties"][request["customer"]]
                        },
                    },
                )
                request["message_source_id"] = source["source_record_id"]
                self.world.mark(
                    "customer_message",
                    self.day,
                    id=request["id"],
                    source_record_id=source["source_record_id"],
                )
                self.world.messages.append(
                    {"source_record_id": source["source_record_id"], "payload": message}
                )
                self.recorder.append(
                    "messages.jsonl",
                    {
                        "day": self.day,
                        "source_record_id": source["source_record_id"],
                        "payload": message,
                    },
                )
            self.order(
                request["id"],
                request["sku"],
                request["quantity"],
                request["amount"],
                request["customer"],
            )
            request["commitment_id"] = self.orders[request["id"]]["commitment_id"]
        for purchase in self.world.purchases.values():
            for delivery in purchase["deliveries"]:
                if delivery["day"] == self.day and not delivery["received"]:
                    self.call(
                        "shipment_receive",
                        {
                            "purpose": "supplier_delivery",
                            "counterparty_id": self.refs["parties"]["SUPPLIER"],
                            "movements": [
                                {
                                    "commitment_id": self.orders[purchase["id"]][
                                        "commitment_id"
                                    ],
                                    "item_id": self.refs["items"][purchase["sku"]],
                                    "quantity": str(delivery["quantity"]),
                                    "to_location_id": self.refs["locations"]["W1"],
                                }
                            ],
                        },
                    )
                    delivery["received"] = True
                    purchase["fulfilled"] += delivery["quantity"]
                    self.world.locations["W1"][purchase["sku"]] += delivery["quantity"]
                    self.world.mark(
                        "partial_supplier_receipt", self.day, id=purchase["id"]
                    )
        for request in self.world.requests.values():
            for shipment in request["shipments"]:
                if (
                    shipment["arrival"] != self.day
                    or shipment["delivered"]
                    or shipment["failed"]
                ):
                    continue
                if request.get("failed_first_attempt") and not request.get(
                    "failure_recorded"
                ):
                    self.call(
                        "shipment_delivery_failure",
                        {
                            "shipment_id": shipment["id"],
                            "kind": "undeliverable",
                            "reason": "Synthetic carrier confirmed undeliverable and physical return",
                        },
                    )
                    shipment["failed"] = True
                    request["failure_recorded"] = True
                    request["dispatched"] -= shipment["quantity"]
                    self.world.locations["W1"][request["sku"]] += shipment["quantity"]
                    self.world.mark("delivery_failure", self.day, id=request["id"])
                    continue
                if request.get("carrier_exception") and not shipment.get(
                    "exception_recorded"
                ):
                    for package in shipment["packages"]:
                        self.call(
                            "shipment_event_record",
                            {
                                "shipment_id": shipment["id"],
                                "shipment_package_id": package,
                                "event_type": "delivery_exception",
                                "reporter_type": "carrier",
                                "external_event_id": self.run_id
                                + shipment["id"]
                                + "exception",
                            },
                        )
                    shipment["exception_recorded"] = True
                    shipment["arrival"] += 1
                    self.world.mark("carrier_exception", self.day, id=request["id"])
                    continue
                for package in shipment["packages"]:
                    self.call(
                        "shipment_event_record",
                        {
                            "shipment_id": shipment["id"],
                            "shipment_package_id": package,
                            "event_type": "delivered",
                            "reporter_type": "carrier",
                            "external_event_id": self.run_id + package + "delivered",
                        },
                    )
                shipment["delivered"] = True
                self.world.mark("package_delivery", self.day, id=request["id"])
            for payment in request.get("payment_events", []):
                if payment["day"] == self.day and not payment["done"]:
                    label = f"PAY-{request['id']}-{payment['after']}"
                    self.financial(
                        label,
                        "customer_payment",
                        payment["amount"],
                        {
                            "invoice_id": self.world.documents[request["invoice"]][
                                "id"
                            ],
                            "amount": payment["amount"],
                            "payment_number": label,
                        },
                        target=request["invoice"],
                        party=self.refs["parties"][request["customer"]],
                    )
                    payment["done"] = True
            if (
                request.get("invoice")
                and request.get("return")
                and self.day == request["invoice_day"] + request["return"]["after"]
            ):
                quantity = request["return"]["quantity"]
                announcement = self.call(
                    "return_announce",
                    {
                        "commitment_id": request["commitment_id"],
                        "quantity": str(quantity),
                        "reference": "RET-" + request["id"],
                        "reason": "Customer reported damaged item",
                    },
                )
                request.update(
                    return_announced=announcement,
                    return_quantity=quantity,
                    return_arrival=self.day + 1,
                )
                self.world.mark("return_announcement", self.day, id=request["id"])
            if request.get("return_arrival") == self.day:
                receipt = self.call(
                    "movement_create",
                    {
                        "movement_type": "return",
                        "commitment_id": request["commitment_id"],
                        "return_announcement_id": request["return_announced"],
                        "item_id": self.refs["items"][request["sku"]],
                        "quantity": str(request["return_quantity"]),
                        "to_location_id": self.refs["locations"]["W1"],
                    },
                )
                request["returned"] = request["return_quantity"]
                from scenarios.company_simulator.bridge import record_ids

                request["return_movement_ids"] = record_ids(receipt, "movement")
                self.world.locations["W1"][request["sku"]] += request["returned"]
                self.world.mark("return_receipt", self.day, id=request["id"])
            for refund in request.get("refund_events", []):
                if refund["day"] == self.day and not refund["done"]:
                    label = f"REF-{request['id']}-{refund['after']}"
                    self.financial(
                        label,
                        "customer_refund",
                        refund["amount"],
                        {
                            "credit_note_id": self.world.documents[request["credit"]][
                                "id"
                            ],
                            "amount": refund["amount"],
                            "refund_number": label,
                        },
                        target=request["credit"],
                        party=self.refs["parties"][request["customer"]],
                    )
                    refund["done"] = True
        for event in self.scenario["stock_events"]:
            if event["day"] != self.day:
                continue
            sku, quantity = event["sku"], event["quantity"]
            # A count/transfer is conditional on actually available physical stock.
            if self.world.locations[event["from"]][sku] < quantity:
                self.world.mark("stock_event_blocked", self.day, source_event=event)
                continue
            args = {
                "movement_type": event["kind"],
                "item_id": self.refs["items"][sku],
                "quantity": str(quantity),
                "from_location_id": self.refs["locations"][event["from"]],
                "reason": event["reason"],
            }
            if event.get("to"):
                args["to_location_id"] = self.refs["locations"][event["to"]]
            self.call("movement_create", args)
            self.world.locations[event["from"]][sku] -= quantity
            if event.get("to"):
                self.world.locations[event["to"]][sku] += quantity
            self.world.mark(
                "warehouse_transfer"
                if event["kind"] == "transfer"
                else "stock_adjustment",
                self.day,
            )

    def dispatch(self, request, quantity, address):
        from reality.services.shipments import shipment_explain
        from scenarios.company_simulator.bridge import record_ids

        cid = request["commitment_id"]
        self.call("reserve", {"commitment_id": cid, "quantity": str(quantity)}, True)
        plan = self.call(
            "outbound_delivery_plan",
            {
                "customer_id": self.refs["parties"][request["customer"]],
                "recipient_party_id": self.refs["parties"][request["customer"]],
                "address": address,
                "lines": [{"commitment_id": cid, "quantity": str(quantity)}],
            },
            True,
        )
        receipt = self.call(
            "shipment_dispatch",
            {
                "purpose": "customer_delivery",
                "counterparty_id": self.refs["parties"][request["customer"]],
                "outbound_delivery_id": record_ids(plan, "outbound_delivery")[0],
                "movements": [
                    {
                        "commitment_id": cid,
                        "item_id": self.refs["items"][request["sku"]],
                        "from_location_id": self.refs["locations"]["W1"],
                        "quantity": str(quantity),
                    }
                ],
            },
            True,
        )
        detail = shipment_explain(
            self.session, self.bridge.tenant_id, receipt["shipment_id"]
        )
        request["shipments"].append(
            {
                "id": receipt["shipment_id"],
                "quantity": quantity,
                "arrival": self.day + self.scenario["transit_days"],
                "delivered": False,
                "failed": False,
                "packages": [p["id"] for p in detail["packages"]],
                "address": deepcopy(address),
                "recipient_party_id": self.refs["parties"][request["customer"]],
            }
        )
        request["dispatched"] += quantity
        self.world.locations["W1"][request["sku"]] -= quantity
        self.world.mark(
            "partial_customer_dispatch"
            if request["dispatched"] < request["quantity"]
            else "customer_dispatch",
            self.day,
            id=request["id"],
        )

    def cancel_request(self, request):
        self.call(
            "commitment_cancel",
            {
                "commitment_id": request["commitment_id"],
                "reason": "Customer cancelled remaining open quantity",
            },
            True,
        )
        request["cancelled"] = True
        self.world.mark("cancel_commitment", self.day, id=request["id"])

    def credit_request(self, request):
        label = "CR-" + request["id"]
        invoice = self.world.documents[request["invoice"]]
        amount = request["return"]["amount"]
        self.financial(
            label,
            "sales_credit",
            amount,
            {
                "invoice_id": invoice["id"],
                "number": label,
                "gross_amount": amount,
                "reason": "Accepted customer return",
                "allocation_amount": "0",
                "lines": [
                    {
                        "invoice_line_id": invoice["line_ids"][0],
                        "quantity": str(request["returned"]),
                        "gross_amount": amount,
                    }
                ],
            },
            party=self.refs["parties"][request["customer"]],
        )
        request["credit"] = label
        request["refund_events"] = [
            {**r, "day": self.day + r["after"], "done": False}
            for r in request["return"]["refunds"]
        ]

    def invoice_purchase(self, purchase):
        label = "PINV-" + purchase["id"]
        amount = self.scenario["quote"]["pack_amount"]
        self.financial(
            label,
            "supplier_invoice",
            amount,
            {
                "number": label,
                "gross_amount": amount,
                "lines": [
                    {
                        "order_line_id": self.orders[purchase["id"]]["line_id"],
                        "quantity": str(purchase["quantity"]),
                        "gross_amount": amount,
                    }
                ],
            },
            party=self.refs["parties"]["SUPPLIER"],
        )
        purchase["invoice"] = label
        purchase["payment_day"] = self.day + self.scenario["quote"]["payment_after"]

    def pay_purchase(self, purchase):
        amount = self.scenario["quote"]["pack_amount"]
        self.financial(
            "PPAY-" + purchase["id"],
            "supplier_payment",
            amount,
            {
                "invoice_id": self.world.documents[purchase["invoice"]]["id"],
                "amount": amount,
                "payment_number": "PPAY-" + purchase["id"],
            },
            target=purchase["invoice"],
            party=self.refs["parties"]["SUPPLIER"],
        )

    def operate(self):
        if callable(self.operator):
            view = deepcopy(self.world.view(self.day))
            view["reality"] = observe(self.session, self.bridge.tenant_id)
            view["finance"] = complete_observer.finance_observation(
                self.session, self.bridge.tenant_id, self.world
            )
            commands = self.operator(view)
            for command in commands:
                if command["kind"] == "reply":
                    if not self.correspondence:
                        raise ValueError("reply drafts require the complete profile")
                    self.correspondence.draft(command)
                elif command["kind"] == "purchase":
                    self.purchase(command["sku"])
                elif command["kind"] == "ship":
                    request = self.world.requests[command["request_id"]]
                    self.dispatch(
                        request,
                        int(command["quantity"]),
                        command.get("address", self.scenario["address"]),
                    )
                elif command["kind"] == "cancel":
                    self.cancel_request(self.world.requests[command["request_id"]])
                elif command["kind"] == "invoice":
                    self.invoice_request(self.world.requests[command["request_id"]])
                elif command["kind"] == "credit":
                    self.credit_request(self.world.requests[command["request_id"]])
                elif command["kind"] == "supplier_invoice":
                    self.invoice_purchase(self.world.purchases[command["purchase_id"]])
                elif command["kind"] == "supplier_payment":
                    self.pay_purchase(self.world.purchases[command["purchase_id"]])
                else:
                    raise ValueError("unsupported custom operator command")
            return
        if self.operator == "idle":
            return
        for request in self.world.requests.values():
            if self.operator == "delayed" and self.day < request["day"] + 4:
                continue
            if request["cancel_requested"] and not request["cancelled"]:
                self.cancel_request(request)
            remaining = (
                0
                if request["cancelled"]
                else request["quantity"] - request["dispatched"]
            )
            if remaining:
                available = self.world.view(self.day)["stock"]["W1"][request["sku"]]
                quantity = min(
                    remaining, available, request.get("dispatch_limit", remaining)
                )
                if quantity:
                    address = deepcopy(self.scenario["address"])
                    if self.operator == "wrong_address":
                        address["street"] = "Wrong Road 99"
                    self.dispatch(request, quantity, address)
                elif not any(
                    p["sku"] == request["sku"] and p["fulfilled"] < p["quantity"]
                    for p in self.world.purchases.values()
                ):
                    self.purchase(request["sku"])
            delivered = sum(
                s["quantity"]
                for s in request["shipments"]
                if s["delivered"] and not s["failed"]
            )
            if (
                not request["invoice"]
                and request["invoice_quantity"]
                and delivered >= request["invoice_quantity"]
            ):
                self.invoice_request(request)
            if request["returned"] and not request["credit"]:
                self.credit_request(request)
        for purchase in self.world.purchases.values():
            if (
                purchase["fulfilled"] == purchase["quantity"]
                and not purchase["invoice"]
            ):
                self.invoice_purchase(purchase)
            if purchase.get("payment_day") == self.day:
                self.pay_purchase(purchase)

    def purchase(self, sku):
        label = f"P{len(self.world.purchases) + 1:03}"
        quote = self.scenario["quote"]
        self.order(label, sku, quote["pack_quantity"], quote["pack_amount"])
        self.world.purchase(label, sku, self.day)

    def checkpoint(self):
        actual = observe(self.session, self.bridge.tenant_id)
        expected = self.world.expected()
        for label, row in expected["lines"].items():
            refs = self.orders[label.rsplit(":", 1)[0]]
            row.update(
                commitment_id=refs["commitment_id"],
                document_id=refs["document_id"],
                source_record_id=refs["source_record_id"],
                document_line_id=refs["line_id"],
            )
        mismatch = differences(expected, actual)
        for key in ("invariants", "evidence_errors"):
            mismatch.extend(differences([], actual[key], key))
        finance = complete_observer.finance_observation(
            self.session, self.bridge.tenant_id, self.world
        )
        mismatch.extend(differences(self.world.expected_finance(), finance, "finance"))
        logistics = complete_observer.logistics_observation(
            self.session, self.bridge.tenant_id, self.world
        )
        expected_shipments = {
            s["id"]: {
                "recipient_party_id": s["recipient_party_id"],
                "address": s["address"],
                "delivered": s["delivered"],
                "failed": s["failed"],
            }
            for r in self.world.requests.values()
            for s in r["shipments"]
        }
        mismatch.extend(
            differences(
                {"shipments": expected_shipments, "errors": []}, logistics, "logistics"
            )
        )
        self.recorder.append(
            "checkpoints.jsonl",
            {
                "day": self.day,
                "expected": expected,
                "actual": actual,
                "expected_finance": self.world.expected_finance(),
                "actual_finance": finance,
                "actual_logistics": logistics,
                "differences": mismatch,
            },
        )
        self.publish_spectator(
            "unfinished",
            "failed_at_checkpoint" if mismatch else "passed_at_checkpoint",
            logistics,
        )
        return actual, finance, logistics, mismatch

    def publish_spectator(self, run_state, core_status, logistics, result=None):
        """Export released observations only; viewer failure has no business effect."""
        payload = {
            "schema_version": 1,
            "run_id": self.run_id,
            "day": self.day,
            "observed_at": timestamp(),
            "run_state": run_state,
            "core_status": core_status,
            "business_references": self.refs,
            "order_references": self.orders,
            "parties": [
                {
                    "id": self.refs["parties"][label],
                    "label": label,
                    "name": name,
                    "role": role,
                }
                for group, role in (("customers", "customer"), ("supplier", "supplier"))
                for label, name in self.scenario[group].items()
                if label in self.refs["parties"]
            ],
            "released": self.world.view(self.day),
            "world_events": self.world.events,
            "goals": self.goals(logistics),
            "coverage": {
                "planned": self.planned,
                "exercised": sorted(self.world.exercised & set(self.planned)),
                "not_exercised": sorted(set(self.planned) - self.world.exercised),
            },
        }
        if result:
            payload["pending_proposal"] = result.get("pending_proposal")
            payload["failure"] = result.get("failure")
        target = self.recorder.directory / "spectator.json"
        temporary = target.with_suffix(".tmp")
        try:
            temporary.write_text(encode(payload) + "\n", encoding="utf-8")
            temporary.replace(target)
            self.spectator_error = None
        except OSError as error:
            self.spectator_error = type(error).__name__

    def goals(self, logistics):
        goals = []
        for r in self.world.requests.values():
            good = 0
            wrong = False
            arrivals = []
            for s in r["shipments"]:
                proof = logistics.get("shipments", {}).get(s["id"], {})
                destination = (
                    proof.get("address") == self.scenario["address"]
                    and proof.get("recipient_party_id")
                    == self.refs["parties"][r["customer"]]
                )
                wrong |= bool(proof) and not destination
                if (
                    proof.get("delivered")
                    and not proof.get("failed")
                    and destination
                    and s["arrival"] <= r["deadline"]
                ):
                    good += s["quantity"]
                    arrivals.append(s["arrival"])
            target = r["dispatched"] if r["cancelled"] else r["quantity"]
            status = (
                "cancelled"
                if r["cancelled"] and not target
                else "met"
                if good >= target
                else "missed"
                if r["deadline"] <= self.day
                else "pending"
            )
            goals.append(
                {
                    "id": r["id"],
                    "quantity": r["quantity"],
                    "required_after_cancellation": target,
                    "delivered_on_time_correct_destination": good,
                    "deadline": r["deadline"],
                    "arrival": max(arrivals) if arrivals else None,
                    "wrong_destination": wrong,
                    "status": status,
                }
            )
        return goals

    def run(self):
        from scenarios.company_simulator.bridge import ReviewRequired

        result = {
            "run_id": self.run_id,
            "company_id": self.bridge.tenant_id,
            "artifact_dir": str(self.recorder.directory),
            "core_status": "passed",
        }
        logistics = {}
        try:
            self.initialize()
            actual, finance, logistics, mismatch = self.checkpoint()
            result.update(
                final=actual, final_finance=finance, final_logistics=logistics
            )
            if mismatch:
                result.update(
                    core_status="failed", failure={"day": 0, "differences": mismatch}
                )
                raise InitialCheckpointFailed()
            for day in range(1, self.days + 1):
                self.day = day
                self.process_world()
                if self.correspondence:
                    self.correspondence.incoming()
                self.operate()
                if self.correspondence:
                    self.correspondence.baseline_replies()
                actual, finance, logistics, mismatch = self.checkpoint()
                result.update(
                    final=actual, final_finance=finance, final_logistics=logistics
                )
                if mismatch:
                    result.update(
                        core_status="failed",
                        failure={"day": self.day, "differences": mismatch},
                    )
                    break
        except InitialCheckpointFailed:
            pass
        except ReviewRequired as error:
            result.update(core_status="awaiting_review", pending_proposal=error.pending)
        except Exception as error:  # noqa: BLE001 - unknown effect is never retried
            self.session.rollback()
            result.update(
                core_status="unknown",
                failure={
                    "day": self.day,
                    "error_type": type(error).__name__,
                    "error_code": getattr(error, "code", None),
                    "outcome": "reconcile retained receipts before retry",
                },
            )
        result.update(
            goals=self.goals(logistics),
            world_events=self.world.events,
            coverage={
                "planned": self.planned,
                "exercised": sorted(self.world.exercised & set(self.planned)),
                "not_exercised": sorted(set(self.planned) - self.world.exercised),
            },
            business_references=self.refs,
            order_references=self.orders,
        )
        if self.correspondence:
            result["communication"] = self.correspondence.summary()
        self.publish_spectator("finished", result["core_status"], logistics, result)
        if self.spectator_error:
            result["spectator_error"] = self.spectator_error
        self.recorder.write("report.json", result)
        self.recorder.write("world.json", self.world.events)
        (self.recorder.directory / "report.md").write_text(
            f"# {self.scenario['id']}\n\nCore: {result['core_status']}\n\n"
            + "\n".join(
                f"- {g['id']}: {g['status']}; quantity on time at correct destination {g['delivered_on_time_correct_destination']}/{g['required_after_cancellation']}"
                for g in result["goals"]
            )
            + "\n\nNot exercised: "
            + ", ".join(result["coverage"]["not_exercised"])
            + "\n"
        )
        return result


def run_complete(
    session,
    owner_id,
    scenario,
    *,
    days,
    operator,
    output_root,
    confirmed=False,
    review=None,
):
    if confirmed is not True:
        raise ValueError("explicit confirmation required")
    if (
        type(days) is not int
        or not 1 <= days <= 30
        or (
            not callable(operator)
            and operator not in {"prompt", "delayed", "idle", "wrong_address"}
        )
    ):
        raise ValueError("invalid horizon or operator")
    if scenario != complete_profile():
        raise ValueError("only the reviewed complete profile is supported")
    return CompanyRun(
        session, owner_id, scenario, days, operator, output_root, review
    ).run()

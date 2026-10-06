"""Exact local manual-source fixture effects through production proposal tools."""

import json
from datetime import datetime
from hashlib import sha256
from typing import Any

from sqlalchemy.orm import Session

from reality.services.company_setup import create_company
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)
from scenarios.harness.observer import differences, observe
from scenarios.harness.reporting import Recorder, encode, timestamp


class Simulator:
    def __init__(
        self,
        session: Session,
        owner_id: str,
        scenario: dict,
        run_id: str,
        recorder: Recorder,
        start: datetime,
    ) -> None:
        self.session = session
        self.owner_id = owner_id
        self.scenario = scenario
        self.run_id = run_id
        self.recorder = recorder
        self.start = start
        self.tenant_id = None
        self.refs = {"items": {}, "parties": {}, "locations": {}, "orders": {}}
        self.order_proposals = {}
        self.return_announcements: dict[str, str] = {}

    def create(self) -> dict:
        created = create_company(
            self.session,
            self.owner_id,
            f"reference-week:{self.run_id}",
            f"Reality Rehearsal {self.run_id}",
            "sandbox",
            "empty",
            confirmed=True,
        )
        self.tenant_id = created["tenant_id"]
        return created

    def invoke(self, event: dict, tool: str, arguments: dict) -> tuple[str, Any]:
        before = observe(self.session, self.tenant_id)
        proposal = create_change_proposal(
            self.session,
            self.tenant_id,
            tool,
            arguments,
            actor_type="human",
        )
        prepared = observe(self.session, self.tenant_id)
        no_effect_fields = ("counts", "physical", "reserved", "lines", "record_ids")
        effect_delta = differences(
            {key: before[key] for key in no_effect_fields},
            {key: prepared[key] for key in no_effect_fields},
        )
        self.recorder.append(
            "events.jsonl",
            {
                "event_id": event["id"],
                "phase": "prepared",
                "tool": tool,
                "scenario_time": event["scenario_time"],
                "proposal_id": proposal.id,
                "arguments": arguments,
                "input_hash": sha256(encode(arguments).encode()).hexdigest(),
                "accepted_effect_delta": effect_delta,
            },
        )
        if effect_delta:
            raise RuntimeError("Proposal preparation changed accepted business reality")
        review = json.loads(proposal.input).get("_delivery_review", {})
        executed = approve_and_execute_proposal(
            self.session,
            self.tenant_id,
            proposal.id,
            confirming_principal=Principal(self.owner_id),
            review_token=review.get("token"),
            confirmed=True,
        )
        if executed.status != "executed":
            raise RuntimeError("Proposal did not execute")
        receipt = json.loads(executed.output)
        self.recorder.append(
            "events.jsonl",
            {
                "event_id": event["id"],
                "phase": "committed",
                "tool": tool,
                "scenario_time": event["scenario_time"],
                "proposal_id": executed.id,
                "committed_at": timestamp(),
                "receipt": receipt,
            },
        )
        return executed.id, receipt

    def masters(self, event: dict) -> None:
        parties = [{"name": "Reality Rehearsal", "roles": ["company"]}]
        labels = ["COMPANY"]
        for group, role in (("customers", "customer"), ("supplier", "supplier")):
            for label, name in self.scenario[group].items():
                labels.append(label)
                parties.append({"name": name, "roles": [role]})
        _, receipt = self.invoke(event, "party_create", {"records": parties})
        self.refs["parties"] = dict(
            zip(labels, (r["id"] for r in receipt["records"]), strict=True)
        )
        items = [
            {"sku": sku, "name": data["name"], "unit": data["unit"]}
            for sku, data in self.scenario["items"].items()
        ]
        _, receipt = self.invoke(event, "item_create", {"records": items})
        self.refs["items"] = dict(
            zip(
                self.scenario["items"],
                (r["id"] for r in receipt["records"]),
                strict=True,
            )
        )
        _, receipt = self.invoke(
            event,
            "location_create",
            {
                "records": [{"name": name} for name in self.scenario["locations"]],
            },
        )
        self.refs["locations"] = dict(
            zip(
                self.scenario["locations"],
                (r["id"] for r in receipt["records"]),
                strict=True,
            )
        )

    def order(self, event: dict, label: str) -> None:
        order = self.scenario["orders"][label]
        purchase = "supplier" in order
        price_key = "purchase_price" if purchase else "sales_price"
        due = order["promised_at"]
        arguments = {
            "direction": "purchase" if purchase else "sales",
            "number": label,
            "company_party_id": self.refs["parties"]["COMPANY"],
            "counterparty_id": self.refs["parties"][
                order.get("supplier", order.get("customer"))
            ],
            "location_id": self.refs["locations"]["W1"],
            "currency": "EUR",
            "gross_amount": order["total"],
            "ordered_at": event["scenario_time"],
            "requested_delivery_at": due,
            "lines": [
                {
                    "item_id": self.refs["items"][sku],
                    "quantity": str(quantity),
                    "unit_price": self.scenario["items"][sku][price_key],
                    "gross_amount": order["amounts"][sku],
                    "promised_at": due,
                }
                for sku, quantity in order["lines"].items()
            ],
        }
        proposal_id, receipt = self.invoke(event, "order_create", arguments)
        self.order_proposals[label] = proposal_id
        self.refs["orders"][label] = {
            "document_id": receipt["document_id"],
            "source_record_id": receipt["source_record_id"],
            "commitments": dict(
                zip(order["lines"], receipt["commitment_ids"], strict=True)
            ),
        }

    def replay(self, event: dict, label: str) -> None:
        proposal_id = self.order_proposals[label]
        receipt = approve_and_execute_proposal(
            self.session,
            self.tenant_id,
            proposal_id,
            confirming_principal=Principal(self.owner_id),
            confirmed=True,
        )
        self.recorder.append(
            "events.jsonl",
            {
                "event_id": event["id"],
                "phase": "replayed",
                "proposal_id": proposal_id,
                "scenario_time": event["scenario_time"],
                "receipt": json.loads(receipt.output),
                "coverage": "retained proposal receipt replay; raw external intake not exercised",
            },
        )

    def execute(self, event: dict) -> None:
        for step in event["steps"]:
            action = step["action"]
            label = step.get("order")
            if action == "masters":
                self.masters(event)
                continue
            if action == "order":
                self.order(event, label)
                continue
            if action == "replay":
                self.replay(event, label)
                continue
            if action == "cancel":
                for commitment_id in self.refs["orders"][label]["commitments"].values():
                    self.invoke(
                        event,
                        "commitment_cancel",
                        {"commitment_id": commitment_id, "reason": step["reason"]},
                    )
                continue
            for sku, quantity in step["quantities"].items():
                arguments = {"quantity": str(quantity)}
                if label:
                    arguments["commitment_id"] = self.refs["orders"][label][
                        "commitments"
                    ][sku]
                if action == "reserve":
                    self.invoke(event, "reserve", arguments)
                elif action == "announce_return":
                    _, announcement_id = self.invoke(
                        event,
                        "return_announce",
                        {
                            **arguments,
                            "reference": "S5-return-A2",
                            "reason": step["reason"],
                        },
                    )
                    self.return_announcements[f"{label}:{sku}"] = announcement_id
                else:
                    movement_type = {
                        "opening": "opening_stock",
                        "ship": "shipment",
                        "receive": "receipt",
                    }.get(action, action)
                    arguments.update(
                        movement_type=movement_type, item_id=self.refs["items"][sku]
                    )
                    if action == "return":
                        arguments["return_announcement_id"] = self.return_announcements[
                            f"{label}:{sku}"
                        ]
                    if action in {"ship", "adjustment", "transfer"}:
                        arguments["from_location_id"] = self.refs["locations"]["W1"]
                    if action in {"opening", "receive", "return", "transfer"}:
                        arguments["to_location_id"] = self.refs["locations"][
                            "W2" if action == "transfer" else "W1"
                        ]
                    if step.get("reason"):
                        arguments["reason"] = step["reason"]
                    # Actual booking time remains real. Scenario time lives in the run log.
                    self.invoke(event, "movement_create", arguments)


def validate_fixture(scenario: dict) -> None:
    """Reject unsupported events before creating a company."""
    supported = {
        "masters",
        "order",
        "opening",
        "reserve",
        "ship",
        "cancel",
        "replay",
        "receive",
        "announce_return",
        "return",
        "adjustment",
        "transfer",
    }
    for event in scenario["events"]:
        for step in event["steps"]:
            if step.get("action") not in supported:
                raise ValueError("unsupported reference-week action")
            if "order" in step and step["order"] not in scenario["orders"]:
                raise ValueError("unknown order reference")
            for sku, quantity in step.get("quantities", {}).items():
                if (
                    sku not in scenario["items"]
                    or type(quantity) is not int
                    or quantity <= 0
                ):
                    raise ValueError("invalid fixture quantity")

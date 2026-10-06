"""Production proposal bridge with an exact-action supervision boundary."""

import json
from hashlib import sha256

from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)
from scenarios.harness.observer import differences, observe
from scenarios.harness.reporting import encode
from scenarios.reference_week.simulator import Simulator


class ReviewRequired(Exception):
    def __init__(self, pending: dict):
        self.pending = pending


class ToolBridge(Simulator):
    def __init__(self, *args, supervised=False, review=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.supervised = supervised
        self.review = review
        self.day = 0
        self.sequence = 0
        self.receipts = []

    def call(self, tool: str, arguments: dict, *, operator_action=False):
        self.sequence += 1
        event = {
            "id": f"D{self.day}-E{self.sequence}",
            "scenario_time": f"day:{self.day}",
        }
        before = observe(self.session, self.tenant_id)
        proposal = create_change_proposal(
            self.session,
            self.tenant_id,
            tool,
            arguments,
            actor_type="agent" if operator_action and self.supervised else "human",
        )
        prepared = observe(self.session, self.tenant_id)
        keys = ("counts", "physical", "reserved", "lines", "record_ids")
        delta = differences(
            {k: before[k] for k in keys}, {k: prepared[k] for k in keys}
        )
        pending = {
            "proposal_id": proposal.id,
            "tool": tool,
            "arguments": arguments,
            "scenario_day": self.day,
            "input_hash": sha256(encode(arguments).encode()).hexdigest(),
        }
        self.recorder.append(
            "events.jsonl",
            {**event, **pending, "phase": "prepared", "accepted_effect_delta": delta},
        )
        if delta:
            raise RuntimeError("Proposal preparation changed accepted reality")
        principal = Principal(self.owner_id)
        if operator_action and self.supervised:
            principal = self.review(pending) if self.review else None
            if (
                not isinstance(principal, Principal)
                or principal.user_id != self.owner_id
            ):
                raise ReviewRequired(pending)
        review = json.loads(proposal.input).get("_delivery_review", {})
        executed = approve_and_execute_proposal(
            self.session,
            self.tenant_id,
            proposal.id,
            confirming_principal=principal,
            review_token=review.get("token"),
            confirmed=True,
        )
        if executed.status != "executed":
            raise RuntimeError("Proposal did not execute")
        receipt = json.loads(executed.output)
        evidence = {
            "event_id": event["id"],
            "proposal_id": proposal.id,
            "receipt": receipt,
        }
        self.receipts.append(evidence)
        self.recorder.append(
            "events.jsonl", {**event, **evidence, "phase": "committed", "tool": tool}
        )
        return receipt

    def masters(self, event):
        from sqlalchemy import select

        from reality.db.core import PartyRole

        company_id = self.session.scalar(
            select(PartyRole.party_id).where(
                PartyRole.tenant_id == self.tenant_id, PartyRole.role == "company"
            )
        )
        if company_id is None:
            raise RuntimeError("Ordinary test company has no canonical company party")
        labels, parties = [], []
        for group, role in (("customers", "customer"), ("supplier", "supplier")):
            for label, name in self.scenario[group].items():
                labels.append(label)
                parties.append({"name": name, "roles": [role]})
        receipt = self.call("party_create", {"records": parties})
        self.refs["parties"] = {
            "COMPANY": company_id,
            **dict(zip(labels, record_ids(receipt, "party"), strict=True)),
        }
        receipt = self.call(
            "item_create",
            {
                "records": [
                    {"sku": sku, "name": item["name"], "unit": item["unit"]}
                    for sku, item in self.scenario["items"].items()
                ]
            },
        )
        self.refs["items"] = dict(
            zip(self.scenario["items"], record_ids(receipt, "item"), strict=True)
        )
        receipt = self.call(
            "location_create",
            {"records": [{"name": name} for name in self.scenario["locations"]]},
        )
        self.refs["locations"] = dict(
            zip(
                self.scenario["locations"], record_ids(receipt, "location"), strict=True
            )
        )

    def invoke(self, event, tool, arguments):
        receipt = self.call(tool, arguments)
        return self.receipts[-1]["proposal_id"], receipt


def record_ids(receipt: dict, family: str) -> list[str]:
    return [
        r["id"]
        for r in receipt.get("records", [])
        if r.get("family", r.get("type")) == family
    ]

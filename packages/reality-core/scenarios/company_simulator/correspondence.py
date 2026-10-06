"""Source-backed local correspondence; never production mail authorization/transport."""

from copy import deepcopy


class Correspondence:
    def __init__(self, run):
        self.run = run
        self.recorded = {}
        self.config = run.scenario["correspondence"]

    def emit(
        self, key, kind, label, body, *, outgoing=False, reply_to=None, draft=False
    ):
        if key in self.recorded:
            return self.recorded[key]
        run = self.run
        request = run.world.requests.get(label)
        party_label = request["customer"] if request else "SUPPLIER"
        party = run.refs["parties"][party_label]
        role = "customer" if request else "supplier"
        address = self.config["addresses"][party_label]
        message_id = f"{run.run_id}:mail:{key}"
        refs = [{"kind": "party", "id": party}]
        if label in run.orders:
            refs.append({"kind": "document", "id": run.orders[label]["document_id"]})
        payload = {
            "message_id": message_id,
            "thread_id": f"{run.run_id}:thread:{label}",
            "in_reply_to": reply_to,
            "kind": kind,
            "from": self.config["company_address"] if outgoing else address,
            "to": address if outgoing else self.config["company_address"],
            "subject": body.pop(
                "subject", self.config["subjects"].get(kind, kind) + " " + label
            ),
            "body": body["draft_text"] if draft else body,
            "synthetic": True,
            "transport": "local_simulation",
            "business_references": refs,
        }
        source = run.call(
            "source_record_ingest",
            {
                "source_system": "manual",
                "source_type": "simulated_correspondence",
                "external_id": message_id,
                "payload": payload,
                "context": {f"{role}_party_id": party},
            },
        )
        row = {
            "day": run.day,
            "party_id": party,
            "direction": "outgoing" if outgoing else "incoming",
            "status": "proposed" if draft else "simulated" if outgoing else "received",
            "source_record_id": source["source_record_id"],
            "payload": payload,
        }
        self.recorded[key] = row
        run.world.messages.append(deepcopy(row))
        run.recorder.append("messages.jsonl", row)
        run.world.mark(
            "agent_reply" if outgoing else kind,
            run.day,
            id=label,
            party_id=party,
            source_record_id=source["source_record_id"],
        )
        return row

    def order(self, request):
        return self.emit(
            "order:" + request["id"],
            "customer_message",
            request["id"],
            {
                "text": self.config["texts"]["customer_order"],
                "item": request["sku"],
                "quantity": request["quantity"],
                "stated_amount": request["amount"],
                "deadline_day": request["deadline"],
                "destination": deepcopy(self.run.scenario["address"]),
            },
        )

    def incoming(self):
        run = self.run
        for request in run.world.requests.values():
            label = request["id"]
            for condition, kind in (
                (request["cancel_requested"], "customer_cancellation"),
                (bool(request["return_announced"]), "customer_return"),
                (
                    run.day
                    == request["deadline"]
                    - self.config["status_query_before_deadline"],
                    "customer_status_query",
                ),
            ):
                if condition:
                    self.emit(
                        kind + ":" + label,
                        kind,
                        label,
                        {"text": self.config["texts"][kind]},
                    )
        for purchase in run.world.purchases.values():
            label = purchase["id"]
            if run.day == purchase["issued_day"] + self.config["supplier_notice_after"]:
                self.emit(
                    "confirmation:" + label,
                    "supplier_confirmation",
                    label,
                    {
                        "text": self.config["texts"]["supplier_confirmation"],
                        "quantity": purchase["quantity"],
                        "quoted_arrival_days": [
                            purchase["issued_day"] + d["after"]
                            for d in run.scenario["quote"]["deliveries"]
                        ],
                    },
                )
                if purchase["sku"] == run.scenario["quote"]["delay_sku"]:
                    self.emit(
                        "delay:" + label,
                        "supplier_delay_notice",
                        label,
                        {
                            "text": self.config["texts"]["supplier_delay_notice"],
                            "revised_arrival_days": [
                                d["day"] for d in purchase["deliveries"]
                            ],
                        },
                    )
            for index, delivery in enumerate(purchase["deliveries"]):
                if delivery["received"]:
                    self.emit(
                        f"receipt:{label}:{index}",
                        "supplier_receipt",
                        label,
                        {
                            "text": self.config["texts"]["supplier_receipt"],
                            "quantity": delivery["quantity"],
                        },
                    )

    def baseline_replies(self):
        run = self.run
        if callable(run.operator) or run.operator == "idle":
            return
        for key, incoming in list(self.recorded.items()):
            if incoming["direction"] != "incoming":
                continue
            label = incoming["payload"]["thread_id"].rsplit(":", 1)[1]
            request = run.world.requests.get(label)
            if request and run.operator == "delayed" and run.day < request["day"] + 4:
                continue
            facts = (
                {
                    k: deepcopy(request[k])
                    for k in (
                        "dispatched",
                        "cancelled",
                        "invoice",
                        "returned",
                        "credit",
                    )
                }
                if request
                else {
                    k: deepcopy(run.world.purchases[label][k])
                    for k in ("fulfilled", "invoice")
                }
            )
            self.emit(
                "reply:" + key,
                "agent_reply",
                label,
                {
                    "text": self.config["texts"]["agent_reply"],
                    "observed": facts,
                },
                outgoing=True,
                reply_to=incoming["payload"]["message_id"],
            )

        # Emit factual updates only for already accepted operator business effects.
        for index, event in enumerate(list(run.world.events)):
            if event["day"] != run.day or event["kind"] not in {
                "partial_customer_dispatch",
                "customer_dispatch",
                "cancel_commitment",
                "sales_invoice",
                "sales_credit",
                "supplier_payment",
            }:
                continue
            label = event["id"]
            for prefix in ("INV-", "CR-", "PPAY-"):
                label = label.removeprefix(prefix)
            original = next(
                (
                    m
                    for m in self.recorded.values()
                    if m["direction"] == "incoming"
                    and m["payload"]["thread_id"].endswith(":" + label)
                ),
                None,
            )
            if original:
                self.emit(
                    f"update:{index}",
                    "agent_reply",
                    label,
                    {
                        "text": self.config["texts"]["agent_update"],
                        "accepted_event": deepcopy(event),
                    },
                    outgoing=True,
                    reply_to=original["payload"]["message_id"],
                )

    def draft(self, command):
        target = next(
            (
                m
                for m in self.recorded.values()
                if m["payload"]["message_id"] == command["message_id"]
                and m["direction"] == "incoming"
            ),
            None,
        )
        if target is None:
            raise ValueError("reply must reference a released incoming message")
        if not all(
            isinstance(command.get(k), str) and command[k].strip()
            for k in ("subject", "body")
        ):
            raise ValueError("reply requires exact nonempty subject and body")
        label = target["payload"]["thread_id"].rsplit(":", 1)[1]
        row = self.emit(
            f"draft:{len(self.recorded)}",
            "agent_reply",
            label,
            {"subject": command["subject"], "draft_text": command["body"]},
            outgoing=True,
            reply_to=command["message_id"],
            draft=True,
        )
        return row

    def summary(self):
        rows = list(self.recorded.values())
        return {
            "transport": "local_simulation",
            "messages": len(rows),
            "incoming": sum(r["direction"] == "incoming" for r in rows),
            "simulated_replies": sum(r["status"] == "simulated" for r in rows),
            "reply_drafts": sum(r["status"] == "proposed" for r in rows),
        }

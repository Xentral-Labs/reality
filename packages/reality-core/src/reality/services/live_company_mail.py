"""Concrete, bounded local conversations; requests never execute company actions."""

import hashlib
from datetime import timedelta

from sqlalchemy import cast, exists, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import aliased

from reality.db.core import (
    Commitment,
    Document,
    DocumentLine,
    Movement,
    MovementCorrection,
    ShipmentEvent,
    ShipmentEventSupersession,
    SourceRecord,
)
from reality.services import core


def case_variant(key):
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % 12


def customer_conversations(session, tenant, run_id, config, at):
    from reality.services import live_company as live

    system = live._namespace(run_id)
    original = aliased(SourceRecord)
    sent = aliased(SourceRecord)
    terms = core.commitment_terms(session, tenant)
    total = 0
    for stage, minutes in [
        ("request", 1),
        ("acknowledgement", 2),
        ("delivery", 5),
        ("followup", 15),
    ]:
        originals = list(
            session.scalars(
                select(original)
                .where(
                    original.tenant_id == tenant,
                    original.source_system == system,
                    original.source_type == "incoming",
                    original.payload.like('%"kind":"order"%'),
                    original.received_at <= at - timedelta(minutes=minutes),
                    ~exists().where(
                        sent.tenant_id == tenant,
                        sent.source_system == system,
                        sent.source_type == "incoming",
                        sent.external_id == "conversation:" + original.id + ":" + stage,
                    ),
                )
                .order_by(original.received_at, original.id)
                .limit(20)
            )
        )
        for source in originals:
            message = live._json(source)
            doc = session.scalar(
                select(Document).where(
                    Document.tenant_id == tenant, Document.id == message["document_id"]
                )
            )
            if not doc:
                continue
            commitments = list(
                session.scalars(
                    select(Commitment).where(
                        Commitment.tenant_id == tenant, Commitment.document_id == doc.id
                    )
                )
            )
            outstanding = sum(
                terms[c.id].open for c in commitments if c.status != "cancelled"
            )
            dispatched = sum(terms[c.id].fulfilled for c in commitments)
            quantity = message["quantity"]
            item = next(
                i["name"] for i in config["items"] if i["id"] == message["item_id"]
            )
            label = f"Order {doc.number} · {quantity} {item}"
            kind, requested = "customer_email", None
            if stage == "acknowledgement":
                subject = f"Have you received my order {doc.number}?"
                body = f"Hi, I ordered {quantity} {item}. Could you confirm that my order arrived and whether you can meet the requested delivery time?"
                family = "order_acknowledgement_query"
            elif stage == "delivery":
                kind = "status_query"
                if dispatched and outstanding:
                    subject = f"Only part of order {doc.number} has shipped — what about the rest?"
                    body = f"Hi, I can see {dispatched} of my {quantity} {item} have shipped. Will the remaining {outstanding} arrive separately, and when? Please send the tracking details."
                    family = "partial_dispatch_query"
                elif dispatched:
                    subject = f"Where is the parcel for order {doc.number}?"
                    body = f"Hi, my {quantity} {item} show as dispatched. Can you send the tracking link and confirm when they will reach our receiving desk?"
                    family = "tracking_query"
                elif outstanding:
                    subject = f"Where is my order {doc.number}?"
                    body = f"Hi, I am still waiting for my {quantity} {item}. They are needed at our receiving desk within the agreed two-hour window. What is holding up shipment, and can you give me a concrete delivery time?"
                    family = "unshipped_order_query"
                else:
                    subject = f"Please confirm the cancellation of {doc.number}"
                    body = "Hi, is the cancellation recorded? Please confirm that no further goods will be sent and tell me whether any payment needs to be refunded."
                    family = "cancellation_confirmation_query"
            elif stage == "followup":
                if outstanding:
                    subject = f"We still need the remaining {outstanding} items from {doc.number}"
                    body = f"Hi, our team is planning around order {doc.number}: {quantity} {item} ordered, {dispatched} shipped and {outstanding} still open. Can you give us a confirmed dispatch plan for the rest? If you cannot meet our requested time, please suggest an available alternative before changing the order."
                    family = "remaining_items_escalation"
                elif dispatched:
                    subject = f"Paperwork and delivery update for {doc.number}"
                    body = f"Hi, can you send the invoice and tracking details for the {dispatched} {item} dispatched against order {doc.number}? Our receiving and accounts teams need them. Please distinguish the carrier's actual delivery confirmation from an estimated arrival time."
                    family = "post_dispatch_documents_query"
                else:
                    subject = f"Cancellation and refund status for {doc.number}"
                    body = f"Hi, order {doc.number} for {quantity} {item} no longer has an open delivery. Please confirm whether it was cancelled, whether you received a payment and, if so, whether a refund is due. Please send the relevant confirmation."
                    family = "cancellation_refund_query"
            else:
                variant = case_variant(source.external_id)
                if variant == 0 and quantity >= 2 and outstanding >= 1:
                    kind, requested = "cancellation", "1"
                    subject = f"Cancel 1 item from order {doc.number}, please"
                    body = f"Hi, please cancel 1 of the {quantity} {item} and keep the other {quantity - 1} unchanged, including any already dispatched items. Currently {outstanding} are still open and {dispatched} have shipped. Please confirm whether that one item can still be stopped before dispatch; do not cancel the whole order."
                    family = "partial_cancellation_request"
                elif variant == 1:
                    subject = f"Please check the delivery address for {doc.number}"
                    destination = message["destination"]
                    body = f"Hi, please confirm the delivery is addressed to {destination['name']}, {destination['street']}, {destination['postal_code']} {destination['city']}. The goods must go to our receiving desk. Can you confirm that before they leave?"
                    family = "destination_confirmation_query"
                elif variant == 2:
                    subject = f"Invoice copy for order {doc.number}"
                    body = f"Hi, our accounts team needs an invoice for the {quantity} {item} with order reference {doc.number}. Has it been issued yet? Please send a copy, or tell me when it will be available."
                    family = "invoice_copy_query"
                elif variant == 3 and outstanding:
                    kind, requested = "cancellation", str(outstanding)
                    subject = f"Please stop the remaining order {doc.number}"
                    body = f"Hi, we no longer need the unshipped part of our order for {quantity} {item}. Please cancel all {outstanding} still-open items, keeping any {dispatched} already dispatched separate. Can you confirm what can still be stopped and whether a refund is needed?"
                    family = "full_cancellation_request"
                elif variant == 4:
                    subject = f"Can we add 2 {item} to {doc.number}?"
                    body = f"Hi, we ordered {quantity} {item} but now need {quantity + 2}. Can you quote the extra 2 and confirm availability and delivery timing? If the original order has already shipped, please quote a separate additional order instead. Please wait for our confirmation before booking the increase."
                    family = "quantity_increase_request"
                elif variant == 5 and outstanding >= 1 and quantity >= 2:
                    requested = str(min(outstanding, max(1, quantity // 2)))
                    kind = "cancellation"
                    subject = f"Please reduce the quantity on {doc.number}"
                    body = f"Hi, the project has become smaller. We ordered {quantity} {item}; please remove {requested} from the still-open {outstanding}, keeping the other items. Please confirm the revised quantity and amount, and tell us if any part has already left your warehouse."
                    family = "quantity_reduction_request"
                elif variant == 6:
                    alternative = next(
                        (
                            i["name"]
                            for i in config["items"]
                            if i["id"] != message["item_id"]
                        ),
                        "a comparable available product",
                    )
                    subject = f"Alternative product for {doc.number}?"
                    body = f"Hi, for our {quantity} {item} on order {doc.number}, could you quote {alternative} as an alternative? Please tell us the price difference and availability. Do not substitute anything without our approval; if the original goods have shipped, explain the return or separate-order options."
                    family = "substitute_item_query"
                elif variant == 7:
                    destination = message["destination"]
                    subject = f"Delivery instructions changed for {doc.number}"
                    body = f"Hi, our order for {quantity} {item} should go to {destination['name']}, {destination['street']}, {destination['postal_code']} {destination['city']}, but please use the side entrance marked Goods receiving, not reception. Can you still update the delivery instructions? If a parcel has left, please tell us how to contact the carrier."
                    family = "destination_change_request"
                elif variant == 8:
                    subject = f"Can you expedite order {doc.number}?"
                    body = f"Hi, the {quantity} {item} are needed urgently for an event. Can you dispatch today and offer an express service? Please quote any extra shipping charge and a realistic arrival estimate before we agree. If already dispatched, please send the tracking details instead."
                    family = "urgent_dispatch_request"
                elif variant == 9:
                    subject = f"Can you send available items first on {doc.number}?"
                    body = f"Hi, we ordered {quantity} {item}. If some are available before the rest, can you send those first? Please confirm the quantities per parcel, any additional shipping cost and the timing for the remainder before changing the delivery plan. If already shipped, please explain how it was split."
                    family = "split_delivery_request"
                elif variant == 10:
                    subject = f"Has our payment for {doc.number} arrived?"
                    body = f"Hi, our accounts team is checking payment for order {doc.number}, {quantity} {item}. Can you check whether you have received and allocated any payment? Please send the invoice reference and amount still due; if nothing has arrived, send the payment instructions."
                    family = "payment_confirmation_query"
                elif variant == 11:
                    subject = f"Quote for a larger repeat order after {doc.number}"
                    body = f"Hi, we ordered {quantity} {item} and are considering another {quantity * 5}. Could you quote the unit price, any volume discount, availability and delivery time? This is an enquiry, not a confirmed order. Please keep order {doc.number} unchanged."
                    family = "volume_quote_query"
                else:
                    subject = f"A concrete update on {doc.number}, please"
                    body = f"Hi, could you give me a concrete update on my {quantity} {item}: what has shipped, what is still outstanding, and the expected arrival time? If a delivery is split, please list each parcel."
                    family = "delivery_followup"
            latest_reply = session.scalar(
                select(SourceRecord)
                .where(
                    SourceRecord.tenant_id == tenant,
                    SourceRecord.source_system == system,
                    SourceRecord.source_type == "outgoing",
                    SourceRecord.payload.like('%"document_id":"' + doc.id + '"%'),
                )
                .order_by(SourceRecord.received_at.desc(), SourceRecord.id.desc())
                .limit(1)
            )
            event = {
                "kind": kind,
                "party_id": message["party_id"],
                "document_id": doc.id,
                "subject": subject,
                "body": body + "\n\n" + label,
                "case_family": family,
                "original_message_source_id": source.id,
            }
            if requested:
                event["requested_quantity"] = requested
            if latest_reply:
                event["reply_source_record_id"] = latest_reply.id
            live.inject(
                session,
                tenant,
                config["owner_id"],
                run_id,
                event,
                request_id=f"conversation:{source.id}:{stage}",
                confirmed=True,
                origin="automatic",
                at=at,
            )
            total += 1
    # A return request needs actual arrival evidence, not a dispatch promise.
    originals = list(
        session.scalars(
            select(original)
            .where(
                original.tenant_id == tenant,
                original.source_system == system,
                original.source_type == "incoming",
                original.payload.like('%"kind":"order"%'),
                original.received_at <= at - timedelta(minutes=10),
                ~exists().where(
                    sent.tenant_id == tenant,
                    sent.source_system == system,
                    sent.source_type.in_(["incoming", "conversation_skip"]),
                    sent.external_id == "conversation:" + original.id + ":return",
                ),
                exists().where(
                    DocumentLine.tenant_id == tenant,
                    DocumentLine.document_id
                    == cast(original.payload, JSONB)["document_id"].astext,
                    Commitment.tenant_id == tenant,
                    Commitment.document_line_id == DocumentLine.id,
                    Movement.tenant_id == tenant,
                    Movement.commitment_id == Commitment.id,
                    Movement.type == "shipment",
                    Movement.quantity >= 1,
                    ShipmentEvent.tenant_id == tenant,
                    ShipmentEvent.shipment_package_id == Movement.shipment_package_id,
                    ShipmentEvent.event_type == "delivered",
                    ~exists().where(
                        MovementCorrection.tenant_id == tenant,
                        MovementCorrection.original_movement_id == Movement.id,
                    ),
                    ~exists().where(
                        ShipmentEventSupersession.tenant_id == tenant,
                        ShipmentEventSupersession.superseded_event_id
                        == ShipmentEvent.id,
                    ),
                ),
            )
            .order_by(original.received_at, original.id)
            .limit(20)
        )
    )
    for source in originals:
        if case_variant(source.external_id) % 4 != 3:
            live._store(
                session,
                tenant,
                system,
                "conversation_skip",
                f"conversation:{source.id}:return",
                {"reason": "Return case not selected"},
            )
            continue
        message = live._json(source)
        key = f"conversation:{source.id}:return"
        live.inject(
            session,
            tenant,
            config["owner_id"],
            run_id,
            {
                "kind": "return_request",
                "party_id": message["party_id"],
                "document_id": message["document_id"],
                "subject": "One item arrived damaged — how do I return it?",
                "body": f"Hi, the delivery has arrived, but one of the {message['quantity']} items is damaged. I would like to return that one item and keep the others. Please explain the return procedure and whether a replacement or refund is possible.",
                "requested_quantity": "1",
                "case_family": "damaged_item_return_request",
                "original_message_source_id": source.id,
            },
            request_id=key,
            confirmed=True,
            origin="automatic",
            at=at,
        )
        total += 1
    return total

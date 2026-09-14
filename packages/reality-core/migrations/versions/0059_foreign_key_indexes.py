"""Index the first column of every foreign key (spec 181, ingest cost and company removal).

Reads that resolve a referenced row through its referrers, and deletes that check for
referrers, scanned whole tables where the referencing column carried no index: matching
one payment walked every ledger entry of the company for its document (197 ms per payment
at 10,000 orders), and removing a company took half an hour in foreign-key checks
(`business_event.causation_id`, every `source_record_id`). The models derive the same
indexes with `reality.db.core.index_foreign_keys`; this migration creates them for
existing databases. `if_not_exists` tolerates indexes an operator created by hand under
the same name.
"""

from alembic import op

revision = "0059_foreign_key_indexes"
down_revision = "0058_storyline"
branch_labels = None
depends_on = None

INDEXES: tuple[tuple[str, str, str], ...] = (
    (
        "ix_access_application_reviewed_by_user_id",
        "access_application",
        "reviewed_by_user_id",
    ),
    (
        "ix_company_invitation_accepted_by_user_id",
        "company_invitation",
        "accepted_by_user_id",
    ),
    ("ix_reality_gap_created_by_user_id", "reality_gap", "created_by_user_id"),
    ("ix_scheduled_job_actor_id", "scheduled_job", "actor_id"),
    ("ix_ai_settings_api_key_secret_id", "ai_settings", "api_key_secret_id"),
    ("ix_chat_message_session_id", "chat_message", "session_id"),
    (
        "ix_interpretation_rule_created_by_user_id",
        "interpretation_rule",
        "created_by_user_id",
    ),
    ("ix_reality_gap_entry_actor_user_id", "reality_gap_entry", "actor_user_id"),
    ("ix_scheduled_job_run_actor_id", "scheduled_job_run", "actor_id"),
    (
        "ix_source_classification_mapping_revision_action_id",
        "source_classification_mapping_revision",
        "action_id",
    ),
    ("ix_source_record_source_artifact_id", "source_record", "source_artifact_id"),
    (
        "ix_source_record_supersedes_source_record_id",
        "source_record",
        "supersedes_source_record_id",
    ),
    ("ix_business_event_causation_id", "business_event", "causation_id"),
    ("ix_business_event_action_id", "business_event", "action_id"),
    ("ix_business_event_source_record_id", "business_event", "source_record_id"),
    ("ix_fact_source_record_id", "fact", "source_record_id"),
    (
        "ix_finance_target_mapping_revision_action_id",
        "finance_target_mapping_revision",
        "action_id",
    ),
    ("ix_handling_unit_source_record_id", "handling_unit", "source_record_id"),
    ("ix_location_source_record_id", "location", "source_record_id"),
    ("ix_location_parent_location_id", "location", "parent_location_id"),
    ("ix_party_group_source_record_id", "party_group", "source_record_id"),
    ("ix_payment_term_source_record_id", "payment_term", "source_record_id"),
    ("ix_price_list_source_record_id", "price_list", "source_record_id"),
    (
        "ix_source_stream_current_source_record_id",
        "source_stream",
        "current_source_record_id",
    ),
    ("ix_item_default_location_id", "item", "default_location_id"),
    ("ix_item_source_record_id", "item", "source_record_id"),
    ("ix_party_source_record_id", "party", "source_record_id"),
    ("ix_party_payment_term_id", "party", "payment_term_id"),
    (
        "ix_rule_interpretation_outcome_fact_id",
        "rule_interpretation_outcome",
        "fact_id",
    ),
    ("ix_document_source_record_id", "document", "source_record_id"),
    ("ix_document_payment_term_id", "document", "payment_term_id"),
    ("ix_document_party_id", "document", "party_id"),
    ("ix_document_ship_to_party_id", "document", "ship_to_party_id"),
    ("ix_lot_source_record_id", "lot", "source_record_id"),
    ("ix_party_role_default_location_id", "party_role", "default_location_id"),
    ("ix_price_list_entry_source_record_id", "price_list_entry", "source_record_id"),
    ("ix_shipment_counterparty_id", "shipment", "counterparty_id"),
    ("ix_shipment_source_record_id", "shipment", "source_record_id"),
    ("ix_document_line_item_id", "document_line", "item_id"),
    (
        "ix_document_line_billed_document_line_id",
        "document_line",
        "billed_document_line_id",
    ),
    ("ix_document_line_document_id", "document_line", "document_id"),
    ("ix_document_line_price_list_entry_id", "document_line", "price_list_entry_id"),
    ("ix_ledger_entry_party_id", "ledger_entry", "party_id"),
    ("ix_ledger_entry_document_id", "ledger_entry", "document_id"),
    ("ix_ledger_entry_source_record_id", "ledger_entry", "source_record_id"),
    ("ix_serial_unit_lot_id", "serial_unit", "lot_id"),
    ("ix_serial_unit_source_record_id", "serial_unit", "source_record_id"),
    ("ix_shipment_package_shipment_id", "shipment_package", "shipment_id"),
    ("ix_shipment_package_source_record_id", "shipment_package", "source_record_id"),
    ("ix_commitment_location_id", "commitment", "location_id"),
    ("ix_commitment_from_party_id", "commitment", "from_party_id"),
    ("ix_commitment_document_line_id", "commitment", "document_line_id"),
    ("ix_commitment_item_id", "commitment", "item_id"),
    ("ix_commitment_document_id", "commitment", "document_id"),
    ("ix_commitment_to_party_id", "commitment", "to_party_id"),
    ("ix_shipment_event_shipment_package_id", "shipment_event", "shipment_package_id"),
    ("ix_shipment_event_shipment_id", "shipment_event", "shipment_id"),
    ("ix_shipment_event_source_record_id", "shipment_event", "source_record_id"),
    (
        "ix_commitment_revision_source_record_id",
        "commitment_revision",
        "source_record_id",
    ),
    (
        "ix_component_assignment_revision_actor_id",
        "component_assignment_revision",
        "actor_id",
    ),
    ("ix_reservation_item_id", "reservation", "item_id"),
    ("ix_reservation_location_id", "reservation", "location_id"),
    ("ix_reservation_serial_unit_id", "reservation", "serial_unit_id"),
    ("ix_reservation_handling_unit_id", "reservation", "handling_unit_id"),
    ("ix_reservation_lot_id", "reservation", "lot_id"),
    ("ix_reservation_commitment_id", "reservation", "commitment_id"),
    (
        "ix_return_announcement_source_record_id",
        "return_announcement",
        "source_record_id",
    ),
    (
        "ix_shipment_event_supersession_source_record_id",
        "shipment_event_supersession",
        "source_record_id",
    ),
    (
        "ix_shipment_event_supersession_superseded_event_id",
        "shipment_event_supersession",
        "superseded_event_id",
    ),
    (
        "ix_shipment_event_supersession_replacement_event_id",
        "shipment_event_supersession",
        "replacement_event_id",
    ),
    ("ix_movement_to_location_id", "movement", "to_location_id"),
    ("ix_movement_source_record_id", "movement", "source_record_id"),
    ("ix_movement_item_id", "movement", "item_id"),
    ("ix_movement_resolves_movement_id", "movement", "resolves_movement_id"),
    ("ix_movement_serial_unit_id", "movement", "serial_unit_id"),
    ("ix_movement_handling_unit_id", "movement", "handling_unit_id"),
    ("ix_movement_commitment_id", "movement", "commitment_id"),
    ("ix_movement_return_announcement_id", "movement", "return_announcement_id"),
    ("ix_movement_lot_id", "movement", "lot_id"),
    ("ix_movement_from_location_id", "movement", "from_location_id"),
)


def upgrade():
    for name, table, column in INDEXES:
        op.create_index(name, table, [column], if_not_exists=True)


def downgrade():
    for name, table, _ in reversed(INDEXES):
        op.drop_index(name, table_name=table, if_exists=True)

# Data model
No persisted entities change. New reporting nodes read document subtypes, document_line
children, reservation, holds, lot, serial_unit, handling_unit, shipment_package,
shipment_event and its supersession, payment_term, price lists and assignments,
party roles/groups/membership and subledger_account. Node category and aliases are
presentation metadata. Every relationship names an existing identity FK and cardinality.
Document amount measures read gross_amount; quantity measures require their recorded
unit (or the existing reservation item's base unit); counts count distinct identity.

Financial detail and evidence scope: include received financial components, opening scopes/items, generic evidence documents/lines, source-version metadata and historical additional facts. Raw payload inspection and mapping/assignment histories stay in the Inspector. These are existing records, not newly computed authorities.

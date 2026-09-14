# Research
- Decision: use existing item_create with reviewed import metadata, not report a source_ingest queue receipt as imported items. Plan research agent confirmed batch creation and existing confirmation hooks. Alternative: new public tool/queue orchestration; unnecessary for <=500 rows.
- Decision: atomic source/item/event transaction uses canonical create_item(_commit=False). Existing create_items does not pass the uploaded source reference; import service bridges only this proof-backed case.
- Decision: serialize all item creation and existing updates with shared tenant lock. SKU conflict is import policy, not database identity.
- Decision: raw bounded CSV upload adapter with tenant-bound artifacts; download materialization remains alive through stream. Current API has no artifact endpoints to reuse.
- Decision: exact event/source receipt reconstruction supports lost-response reconciliation. Normal master-data edits do not erase original import proof.
- Decision: retain legacy item profile behavior fields but fix atomicity/replay/retry; no financial profile repair in this feature.

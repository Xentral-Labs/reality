# Research
Decision: reuse core.inventory_rows, not warehouse pagination or a second stock sum.
Rationale: the canonical bulk service already combines movements, active reservations
and commitment terms for the entire tenant. Physical transfer legs cancel; corrections
compensate. Available can be negative and does not subtract holds or expired lots.
Alternative: location_inventory_rows is a different grain and loops over item/location
pairs; it is outside this approved first stock-analysis slice. Existing Warehouse
inventory_page supplies an independent parity check for the same article quantities.
Read-only research by warehouse_analysis_research confirmed these boundaries.

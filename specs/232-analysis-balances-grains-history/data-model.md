# Read-time data model
Balance grain: tenant/side/party/currency. Inventory detail grain: tenant/item/location/
lot/serial/handling unit. Opaque deterministic read-time position_id is distinct from
backing party/item id. No new table or column. snapshot_date is an explicit analysis
input; effective_before is next-day UTC midnight and always exclusive. Current metadata
labels do not pretend to reconstruct historical master-data names or units.

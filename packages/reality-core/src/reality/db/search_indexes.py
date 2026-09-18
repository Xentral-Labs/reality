"""Migration-owned, nonunique search access paths; no runtime installation."""

INDEX_FIELDS = {
    "party": ("id", "name", "accounting_code"),
    "item": ("id", "name", "sku"),
    "location": ("id", "name"),
    "document": ("id", "number", "customer_reference"),
    "source_record": ("id", "external_id"),
    "shipment_package": ("tracking_number",),
    "analytics_report": ("id", "name"),
}
LABEL_FIELDS = {
    "party": "name",
    "item": "name",
    "location": "name",
    "analytics_report": "name",
}


def install_search_indexes(connection):
    # pg_trgm accelerates the complete regular-expression superset, not approximate sampling.
    connection.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    for table, fields in INDEX_FIELDS.items():
        for field in fields:
            owner = "owner_user_id, " if table == "analytics_report" else ""
            connection.exec_driver_sql(
                f"CREATE INDEX ix_search_v1_{table}_{field} ON {table} (tenant_id, {owner}reality_search_normalize_v1({field}) text_pattern_ops)"
            )
    for table, field in LABEL_FIELDS.items():
        owner = "owner_user_id, " if table == "analytics_report" else ""
        connection.exec_driver_sql(
            f"CREATE INDEX ix_search_v1_{table}_label_order ON {table} (tenant_id, {owner}(reality_search_normalize_v1(coalesce(nullif({field}, ''), id)) COLLATE \"C\"), id)"
        )
        connection.exec_driver_sql(
            f"CREATE INDEX ix_search_v1_{table}_words ON {table} USING gin (reality_search_normalize_v1({field}) gin_trgm_ops)"
        )


def drop_search_indexes(connection):
    for table, fields in INDEX_FIELDS.items():
        for field in fields:
            connection.exec_driver_sql(f"DROP INDEX ix_search_v1_{table}_{field}")
    for table in LABEL_FIELDS:
        connection.exec_driver_sql(f"DROP INDEX ix_search_v1_{table}_label_order")
        connection.exec_driver_sql(f"DROP INDEX ix_search_v1_{table}_words")
    # Extensions may be shared by unrelated indexes; rollback leaves pg_trgm installed.

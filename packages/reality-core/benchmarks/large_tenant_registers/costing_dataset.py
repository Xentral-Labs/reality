"""Deterministic PostgreSQL-only experimental input, separate from product tables."""

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import Connection

VERSION = "costing-spike-v3"


@dataclass(frozen=True)
class Profile:
    name: str
    orders: int
    items: int

    @classmethod
    def named(cls, name: str) -> "Profile":
        if name == "full":
            return cls(name, 100_000, 10_000)
        if name == "reduced":
            return cls(name, 120, 12)
        raise ValueError("Unknown profile.")


def build(connection: Connection, profile: Profile) -> None:
    """Called only after runner disposable-target validation, or rolled-back test scope."""
    if connection.scalar(text("SELECT to_regnamespace('costing_spike')")) is not None:
        raise ValueError("Experiment namespace already exists; use validated reuse.")
    connection.execute(text("CREATE SCHEMA costing_spike"))
    statements = [
        "CREATE TABLE manifest (version text, profile text, seed int, business_date date)",
        "CREATE TABLE tenant (id text PRIMARY KEY)",
        "CREATE TABLE item (tenant text REFERENCES tenant(id), id int, PRIMARY KEY(tenant,id))",
        """CREATE TABLE trade_order (tenant text, id int, item int, economic_date date,
            PRIMARY KEY(tenant,id), FOREIGN KEY(tenant,item) REFERENCES item(tenant,id))""",
        """CREATE TABLE movement (tenant text, id int, order_id int, item int, sequence int,
            original_issue int, kind text, quantity numeric(18,4), source_ref text NOT NULL,
            PRIMARY KEY(tenant,id), FOREIGN KEY(tenant,order_id) REFERENCES trade_order(tenant,id),
            FOREIGN KEY(tenant,original_issue) REFERENCES movement(tenant,id))""",
        """CREATE TABLE component (tenant text REFERENCES tenant(id), id int, amount numeric(18,4),
            known boolean, category text, source_ref text NOT NULL, PRIMARY KEY(tenant,id))""",
        """CREATE TABLE attribution (tenant text, id int, component_id int, receipt_id int,
            order_id int, PRIMARY KEY(tenant,id),
            FOREIGN KEY(tenant,component_id) REFERENCES component(tenant,id),
            FOREIGN KEY(tenant,receipt_id) REFERENCES movement(tenant,id),
            FOREIGN KEY(tenant,order_id) REFERENCES trade_order(tenant,id),
            CHECK ((receipt_id IS NULL) <> (order_id IS NULL)))""",
        """CREATE TABLE matching (tenant text, id int, issue_id int, order_id int,
            quantity numeric(18,4), revenue numeric(18,4), invoice_ref text NOT NULL, PRIMARY KEY(tenant,id),
            FOREIGN KEY(tenant,issue_id) REFERENCES movement(tenant,id),
            FOREIGN KEY(tenant,order_id) REFERENCES trade_order(tenant,id))""",
        """CREATE TABLE observation (tenant text REFERENCES tenant(id), issue_id int, order_id int,
            item int, economic_date date, cost numeric(18,4), revenue numeric(18,4),
            selling numeric(18,4), PRIMARY KEY(tenant,issue_id))""",
        """CREATE TABLE inventory_observation (tenant text, item int, quantity numeric(18,4),
            cost numeric(18,4), unknown_quantity numeric(18,4), PRIMARY KEY(tenant,item))""",
        """CREATE TABLE checkpoint (tenant text PRIMARY KEY REFERENCES tenant(id),
            generation int NOT NULL, input_revision int NOT NULL, updated_at timestamptz NOT NULL)""",
    ]
    connection.execute(text("SET LOCAL search_path TO costing_spike,public"))
    # Bulk generation first, then validate all declared foreign keys with set-based
    # ALTER TABLE scans. Constraints are present before any measurement or test read.
    import re

    constraints = []
    for statement in statements:
        table = re.search(r"CREATE TABLE (\w+)", statement).group(1)
        for foreign in re.findall(
            r",?\s*FOREIGN KEY\([^)]+\) REFERENCES \w+\([^)]+\)", statement
        ):
            constraints.append((table, foreign.lstrip(", \n")))
        statement = re.sub(
            r",?\s*FOREIGN KEY\([^)]+\) REFERENCES \w+\([^)]+\)", "", statement
        )
        connection.execute(text(statement))
    connection.execute(
        text("""CREATE TABLE adjustment (tenant text,id int,component_id int,
        amount numeric(18,4),source_ref text NOT NULL,PRIMARY KEY(tenant,id),
        FOREIGN KEY(tenant,component_id) REFERENCES component(tenant,id))""")
    )
    connection.execute(
        text("INSERT INTO manifest VALUES (:version,:profile,234,'2026-09-18')"),
        {"version": VERSION, "profile": profile.name},
    )
    orders = profile.orders
    hot = min(100, profile.items // 2)
    cold = profile.items - hot
    params = {
        "n": orders,
        "items": profile.items,
        "hot": hot,
        "cold": cold,
        "historical": orders * 9 // 10,
    }
    for tenant in ("a", "b"):
        params["tenant"] = tenant
        connection.execute(text("INSERT INTO tenant VALUES (:tenant)"), params)
        connection.execute(
            text("INSERT INTO item SELECT :tenant,i FROM generate_series(1,:items) i"),
            params,
        )
        connection.execute(
            text("""INSERT INTO trade_order
            SELECT :tenant,i, CASE WHEN i<=:n/2 THEN 1+(i-1)%:hot ELSE :hot+1+(i-1)%:cold END,
            CASE WHEN i>:historical THEN DATE '2026-09-18'
            ELSE (DATE '2024-09-01' + make_interval(months=>((i-1)*24/:historical)::int)
                 + (((i-1)%(:historical/24))*28/(:historical/24))*INTERVAL '1 day')::date END
            FROM generate_series(1,:n) i"""),
            params,
        )
        # IDs are synthetic opaque identities, not human business numbers. Per-order
        # source sequence disambiguates same-day business events for this fixture.
        connection.execute(
            text("""INSERT INTO movement
            SELECT o.tenant,(o.id-1)*10+j,o.id,o.item,(o.id-1)*10+j,NULL,
              CASE WHEN j<=3 THEN 'receipt' WHEN j<=9 THEN 'issue' ELSE 'transfer' END,
              CASE WHEN j<=3 THEN 4 ELSE 1 END,
              'source:movement:'||o.tenant||':'||((o.id-1)*10+j)
            FROM trade_order o CROSS JOIN generate_series(1,10) j WHERE o.tenant=:tenant"""),
            params,
        )
        connection.execute(
            text("""INSERT INTO component
            SELECT :tenant,i,
              CASE WHEN i<=:n*3 THEN 40+(i%7) + CASE WHEN :tenant='b' THEN 10 ELSE 0 END
                   WHEN i<=:n*6 THEN CASE WHEN i%3=1 THEN -1.5 WHEN i%3=0 THEN 2 ELSE 4 END ELSE 1 END,
              i%100<>0,
              CASE WHEN i<=:n*3 THEN 'purchase' WHEN i<=:n*6 THEN CASE WHEN i%3=1 THEN 'supplier_credit' WHEN i%3=0 THEN 'nonrecoverable_tax' ELSE 'inbound_freight' END ELSE 'selling' END,
              'source:component:'||:tenant||':'||i FROM generate_series(1,:n*10) i"""),
            params,
        )
        connection.execute(
            text("""INSERT INTO attribution
            SELECT :tenant,i,i,
              CASE WHEN i<=:n*6 THEN (((i-1)%(:n*3))/3)*10+((i-1)%3)+1 END,
              CASE WHEN i>:n*6 THEN (i-:n*6-1)/4+1 END
            FROM generate_series(1,:n*10) i"""),
            params,
        )
        connection.execute(
            text("""INSERT INTO matching
            SELECT :tenant,i,((i-1)/6)*10+4+(i-1)%6,(i-1)/6+1,1,20,
              'source:invoice:'||:tenant||':'||i FROM generate_series(1,:n*6) i"""),
            params,
        )
    # Author adversarial source scenarios before the fixture becomes readable.
    # Returns are a receipt-family subset, preserving all fixed family totals.
    connection.execute(
        text("""WITH previous AS (
      SELECT tenant,id,lag(id) OVER (PARTITION BY tenant,item ORDER BY id) prior
      FROM trade_order
    ) UPDATE movement m SET kind='return',quantity=1,original_issue=(p.prior-1)*10+4
      FROM previous p WHERE m.tenant=p.tenant AND m.order_id=p.id
      AND m.id=(p.id-1)*10+3 AND p.id%10=0 AND p.prior IS NOT NULL""")
    )
    connection.execute(
        text("""UPDATE attribution a SET receipt_id=m.id-2
      FROM movement m WHERE m.tenant=a.tenant AND m.id=a.receipt_id AND m.kind='return'""")
    )
    connection.execute(
        text("""UPDATE matching SET
      issue_id=(order_id-1)*10+CASE WHEN (id-1)%6<2 THEN 4 ELSE 4+(id-1)%6 END,
      quantity=CASE WHEN (id-1)%6<3 THEN 0.5 ELSE 1 END,
      revenue=CASE WHEN (id-1)%6<3 THEN 10 ELSE 20 END
      WHERE order_id%10=0""")
    )
    for table, foreign in constraints:
        connection.execute(text(f"ALTER TABLE {table} ADD {foreign}"))
    indexes = [
        "CREATE INDEX ON attribution(tenant,component_id)",
        "CREATE INDEX ON movement(tenant,item,sequence)",
        "CREATE INDEX ON movement(tenant,order_id)",
        "CREATE INDEX ON attribution(tenant,receipt_id) WHERE receipt_id IS NOT NULL",
        "CREATE INDEX ON attribution(tenant,order_id) WHERE order_id IS NOT NULL",
        "CREATE INDEX ON matching(tenant,issue_id)",
        "CREATE INDEX ON observation(tenant,order_id)",
        "CREATE INDEX ON observation(tenant,economic_date,item)",
        "CREATE INDEX ON observation(tenant,item)",
    ]
    for statement in indexes:
        connection.execute(text(statement))
    connection.execute(text("ANALYZE"))


def validate(connection: Connection, profile: Profile) -> dict:
    manifest = connection.execute(
        text("SELECT version,profile,seed FROM costing_spike.manifest")
    ).one()
    if tuple(manifest) != (VERSION, profile.name, 234):
        raise ValueError("Dataset manifest mismatch.")
    expected = {
        "item": profile.items,
        "trade_order": profile.orders,
        "movement": profile.orders * 10,
        "component": profile.orders * 10,
        "attribution": profile.orders * 10,
        "matching": profile.orders * 6,
    }
    result = {}
    for tenant in ("a", "b"):
        counts = {}
        for table, amount in expected.items():
            # Table identifiers are fixed internal constants, never user-supplied SQL.
            count = connection.scalar(
                text(
                    f"SELECT count(*) FROM costing_spike.{table} WHERE tenant=:tenant"
                ),
                {"tenant": tenant},
            )
            if count != amount:
                raise ValueError(f"Incomplete dataset: {tenant}/{table}.")
            counts[table] = count
        result[tenant] = counts
    return result

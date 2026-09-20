"""Integrated fixture J reads through the same application surfaces as product clients."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from reality.mcp.catalog import MCP_TOOL_REGISTRY
from reality.tools.application import run_read_tool
from reality.web.read_models import exception_count, exception_page


def serialized(value: Any) -> tuple[bytes, str]:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode()
    return payload, hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class ProductWorkloadScope:
    """Exact retained product references selected by the fixture builder."""

    order_line_id: str
    inventory_item_id: str
    company_generation_id: str
    monthly_question: dict[str, Any]


class ProductWorkloads:
    """Read-only adapters used by the timed fixture J driver.

    The caller owns transaction isolation and timing.  Keeping these adapters small makes
    it obvious that no benchmark relation, ORM write, enqueue or alternate rule is used.
    """

    def __init__(self, session: Session, tenant_id: str, scope: ProductWorkloadScope):
        self.session = session
        self.tenant_id = tenant_id
        self.scope = scope

    def order(self) -> tuple[bytes, str]:
        return serialized(
            run_read_tool(
                self.session,
                self.tenant_id,
                "cost.query.get",
                {"kind": "contribution", "scope_id": self.scope.order_line_id},
            )
        )

    def inventory(self) -> tuple[bytes, str]:
        detail = run_read_tool(
            self.session,
            self.tenant_id,
            "cost.query.get",
            {"kind": "inventory", "scope_id": self.scope.inventory_item_id},
        )
        page = run_read_tool(
            self.session,
            self.tenant_id,
            "graph.ask",
            {
                "question": {
                    "from": "inventory_valuation",
                    "company_cost_context": {
                        "generation_id": self.scope.company_generation_id
                    },
                    "measures": ["inventory_acquisition_value"],
                    "group_by": [
                        {"field": "root.currency"},
                        {"field": "root.base_unit"},
                        {"field": "root.item_id"},
                    ],
                    "limit": 100,
                }
            },
        )
        totals = run_read_tool(
            self.session,
            self.tenant_id,
            "graph.ask",
            {
                "question": {
                    "from": "inventory_valuation",
                    "company_cost_context": {
                        "generation_id": self.scope.company_generation_id
                    },
                    "measures": ["inventory_acquisition_value"],
                    "group_by": [
                        {"field": "root.currency"},
                        {"field": "root.base_unit"},
                    ],
                }
            },
        )
        return serialized({"detail": detail, "page": page, "totals": totals})

    def monthly(self) -> tuple[bytes, str]:
        return serialized(
            run_read_tool(
                self.session,
                self.tenant_id,
                "graph.ask",
                {"question": self.scope.monthly_question},
            )
        )

    def exceptions(self) -> tuple[bytes, str]:
        rows, pager = exception_page(self.session, self.tenant_id, page=1, size=100)
        return serialized(
            {
                "rows": rows,
                "page": pager.page,
                "size": pager.size,
                "pages": pager.pages,
                "count": exception_count(self.session, self.tenant_id),
            }
        )

    def mcp(self) -> tuple[bytes, str]:
        value = MCP_TOOL_REGISTRY["cost_query_get"].handler(
            self.session,
            self.tenant_id,
            {"kind": "contribution", "scope_id": self.scope.order_line_id},
        )
        return serialized(value)


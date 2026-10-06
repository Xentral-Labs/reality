"""Authored outside-world state; never expose future demand to an operator."""

from copy import deepcopy


class World:
    def __init__(self, scenario: dict) -> None:
        self.scenario = deepcopy(scenario)
        self.requests: dict[str, dict] = {}
        self.purchases: dict[str, dict] = {}
        self.stock = dict(scenario["opening"])
        self.events: list[dict] = []

    def release(self, day: int) -> list[dict]:
        released = []
        for request in self.requests.values():
            if request["arrival"] == day:
                request["delivered"] = True
                self.events.append(
                    {"kind": "customer_arrival", "day": day, "id": request["id"]}
                )
        for request in self.scenario["requests"]:
            if request["day"] == day:
                row = {**request, "shipped": False, "arrival": None, "delivered": False}
                self.requests[row["id"]] = row
                released.append(row)
                self.events.append(
                    {"kind": "customer_request", "day": day, "id": row["id"]}
                )
        return released

    def view(self, day: int) -> dict:
        return deepcopy(
            {
                "day": day,
                "requests": list(self.requests.values()),
                "stock": self.stock,
                "purchases": list(self.purchases.values()),
                "quote": self.scenario["quote"],
            }
        )

    def purchased(self, label: str, sku: str, day: int) -> None:
        quote = self.scenario["quote"]
        self.purchases[label] = {
            "id": label,
            "sku": sku,
            "quantity": quote["pack_quantity"],
            "arrival": day + quote["lead_days"],
            "received": False,
        }
        self.events.append({"kind": "accepted_purchase", "id": label, "day": day})

    def received(self, purchase: dict, day: int) -> None:
        self.stock[purchase["sku"]] += purchase["quantity"]
        purchase["received"] = True
        self.events.append(
            {"kind": "supplier_arrival", "id": purchase["id"], "day": day}
        )

    def dispatched(self, request: dict, day: int) -> None:
        self.stock[request["sku"]] -= request["quantity"]
        request["shipped"] = True
        request["arrival"] = day + self.scenario["transit_days"]
        self.events.append(
            {"kind": "accepted_dispatch", "id": request["id"], "day": day}
        )

    def goals(self, horizon: int) -> list[dict]:
        return [
            {
                "id": r["id"],
                "deadline": r["deadline"],
                "arrival": r["arrival"],
                "status": "met"
                if r["delivered"]
                and r["arrival"] is not None
                and r["arrival"] <= min(horizon, r["deadline"])
                else "missed"
                if r["deadline"] <= horizon
                else "pending",
            }
            for r in self.requests.values()
        ]

    def expected(self) -> dict:
        skus = self.stock
        lines = {}
        for request in self.requests.values():
            quantity = request["quantity"]
            lines[f"{request['id']}:{request['sku']}"] = {
                "quantity": str(quantity),
                "fulfilled": str(quantity if request["shipped"] else 0),
                "open": str(0 if request["shipped"] else quantity),
                "reserved": "0",
                "line_amount": request["amount"],
                "document_amount": request["amount"],
            }
        for purchase in self.purchases.values():
            quantity = purchase["quantity"]
            lines[f"{purchase['id']}:{purchase['sku']}"] = {
                "quantity": str(quantity),
                "fulfilled": str(quantity if purchase["received"] else 0),
                "open": str(0 if purchase["received"] else quantity),
                "reserved": "0",
                "line_amount": self.scenario["quote"]["pack_amount"],
                "document_amount": self.scenario["quote"]["pack_amount"],
            }
        return {
            "counts": {
                "sales_orders": len(self.requests),
                "purchase_orders": len(self.purchases),
                "ledger_entries": 0,
            },
            "lines": lines,
            "physical": {s: str(self.stock[s]) for s in skus},
            "reserved": {s: "0" for s in skus},
            "customer_open": {
                s: str(
                    sum(
                        r["quantity"]
                        for r in self.requests.values()
                        if r["sku"] == s and not r["shipped"]
                    )
                )
                for s in skus
            },
            "supplier_open": {
                s: str(
                    sum(
                        p["quantity"]
                        for p in self.purchases.values()
                        if p["sku"] == s and not p["received"]
                    )
                )
                for s in skus
            },
        }

"""Finite test policies consume only released, copied observations."""


def decide(view: dict, request: dict, operator: str) -> str | None:
    if request["shipped"] or operator == "idle":
        return None
    if operator == "delayed" and view["day"] < request["day"] + 4:
        return None
    if view["stock"][request["sku"]] >= request["quantity"]:
        return "ship"
    if not any(
        p["sku"] == request["sku"] and not p["received"] for p in view["purchases"]
    ):
        return "purchase"
    return None

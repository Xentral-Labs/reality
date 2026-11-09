"""Spec 388: validate received GraphQL meaning without rewriting its Source."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class GraphQLOrderNeedsReview(ValueError):
    """An original selected entity is not a supported first-order observation."""


class _Money(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    amount: str = Field(pattern=r"^(0|[1-9][0-9]*)(\.[0-9]+)?$", max_length=60)
    currencyCode: str = Field(pattern=r"^[A-Z]{3}$")


class _MoneySet(BaseModel):
    shopMoney: _Money


class _Line(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    id: str = Field(pattern=r"^gid://shopify/LineItem/[0-9]{1,32}$")
    name: str = Field(min_length=1, max_length=500)
    sku: str | None = Field(default=None, max_length=200)
    quantity: int = Field(gt=0)
    currentQuantity: int = Field(gt=0)
    requiresShipping: bool
    originalUnitPriceSet: _MoneySet


class _Page(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    hasNextPage: bool


class _Lines(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    nodes: list[_Line] = Field(min_length=1, max_length=500)
    pageInfo: _Page


class _Order(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)
    id: str = Field(pattern=r"^gid://shopify/Order/[0-9]{1,32}$")
    name: str = Field(min_length=1, max_length=500)
    createdAt: str
    updatedAt: str
    cancelledAt: str | None
    displayFulfillmentStatus: str
    currencyCode: str = Field(pattern=r"^[A-Z]{3}$")
    totalPriceSet: _MoneySet
    lineItems: _Lines


def project_order(raw: dict[str, Any], external_id: str) -> dict[str, Any]:
    """Project only received values; raw remains the authoritative original entity."""
    try:
        value = _Order.model_validate(raw)
        if (
            value.id != f"gid://shopify/Order/{external_id}"
            or value.cancelledAt is not None
            or value.displayFulfillmentStatus != "UNFULFILLED"
            or value.lineItems.pageInfo.hasNextPage
            or value.totalPriceSet.shopMoney.currencyCode != value.currencyCode
            or len({line.id for line in value.lineItems.nodes})
            != len(value.lineItems.nodes)
            or any(
                line.currentQuantity != line.quantity
                or line.originalUnitPriceSet.shopMoney.currencyCode
                != value.currencyCode
                for line in value.lineItems.nodes
            )
            or datetime.fromisoformat(value.createdAt).utcoffset() is None
            or datetime.fromisoformat(value.updatedAt).utcoffset() is None
        ):
            raise ValueError("unsupported_first_order")
        # Validate decimal range without calculating a replacement stated amount.
        if not Decimal(value.totalPriceSet.shopMoney.amount).is_finite():
            raise ValueError("invalid_amount")
    except (ValidationError, ValueError, TypeError, OverflowError) as error:
        raise GraphQLOrderNeedsReview() from error
    return {
        "id": external_id,
        "name": value.name,
        "created_at": value.createdAt,
        "updated_at": value.updatedAt,
        "currency": value.currencyCode,
        "total_price": value.totalPriceSet.shopMoney.amount,
        "line_items": [
            {
                "id": line.id,
                "name": line.name,
                "sku": line.sku or "",
                "quantity": line.quantity,
                "price": line.originalUnitPriceSet.shopMoney.amount,
                "requires_shipping": line.requiresShipping,
            }
            for line in value.lineItems.nodes
        ],
    }

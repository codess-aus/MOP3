"""
Discount calculation engine for the Meridian storefront.

Business rules are defined by the commercial team and documented
in Confluence (COMM-2024-Q4-PRICING). This module implements
the approved discount stacking and cap logic.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime


TIER_RATES = {
    "bronze": Decimal("0.05"),
    "silver": Decimal("0.10"),
    "gold": Decimal("0.15"),
    "platinum": Decimal("0.20"),
}

PROMO_CODES = {
    "SAVE10": {"type": "percentage", "value": Decimal("0.10")},
    "FLAT20": {"type": "flat", "value": Decimal("20.00")},
    "WELCOME5": {"type": "percentage", "value": Decimal("0.05")},
}

MAX_DISCOUNT_RATE = Decimal("0.40")
MINIMUM_PRICE = Decimal("1.00")


def calculate_discount(
    subtotal_cents,
    customer_tier,
    promo_code=None,
    is_first_purchase=False,
    order_date=None,
):
    """
    Calculate the final price after applying all eligible discounts.

    Discounts stack in this order:
        1. Tier-based percentage discount
        2. Promotional code (percentage or flat)
        3. First-purchase bonus (+5%)
        4. Weekend surcharge (-2%)
    Total percentage discounts are capped at 40%.
    Final price never drops below $1.00.

    Args:
        subtotal_cents: Pre-discount total in cents (integer).
        customer_tier: One of "bronze", "silver", "gold", "platinum".
        promo_code: Optional promo code string.
        is_first_purchase: True if this is the customer's first order.
        order_date: Date of the order. Defaults to today.

    Returns:
        Dict with final_price_cents, total_discount_cents, and breakdown.

    Raises:
        ValueError: If subtotal is negative or tier is unrecognised.
    """
    if subtotal_cents < 0:
        raise ValueError("Subtotal cannot be negative")

    if customer_tier not in TIER_RATES:
        raise ValueError(
            f"Unrecognised tier: {customer_tier}. "
            f"Valid tiers: {', '.join(TIER_RATES.keys())}"
        )

    subtotal = Decimal(subtotal_cents) / Decimal("100")
    breakdown = []
    total_percentage = Decimal("0")
    flat_discount = Decimal("0")

    tier_rate = TIER_RATES[customer_tier]
    total_percentage += tier_rate
    breakdown.append({
        "type": "tier",
        "description": f"{customer_tier} member discount",
        "rate": float(tier_rate),
    })

    if promo_code:
        normalised = promo_code.upper().strip()
        if normalised in PROMO_CODES:
            promo = PROMO_CODES[normalised]
            if promo["type"] == "percentage":
                total_percentage += promo["value"]
                breakdown.append({
                    "type": "promo",
                    "description": f"{normalised} promotion",
                    "rate": float(promo["value"]),
                })
            elif promo["type"] == "flat":
                flat_discount += promo["value"]
                breakdown.append({
                    "type": "promo",
                    "description": f"{normalised} promotion",
                    "amount": float(promo["value"]),
                })

    if is_first_purchase:
        total_percentage += Decimal("0.05")
        breakdown.append({
            "type": "first_purchase",
            "description": "First order bonus",
            "rate": 0.05,
        })

    if order_date is None:
        order_date = datetime.now()
    if order_date.weekday() >= 5:
        total_percentage -= Decimal("0.02")
        breakdown.append({
            "type": "surcharge",
            "description": "Weekend processing surcharge",
            "rate": -0.02,
        })

    if total_percentage > MAX_DISCOUNT_RATE:
        total_percentage = MAX_DISCOUNT_RATE
        breakdown.append({"type": "cap", "description": "Discount cap applied at 40%"})

    percentage_savings = (subtotal * total_percentage).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    final_price = subtotal - percentage_savings - flat_discount

    if final_price < MINIMUM_PRICE:
        final_price = MINIMUM_PRICE

    final_price_cents = int((final_price * 100).to_integral_value())
    total_discount_cents = subtotal_cents - final_price_cents

    return {
        "final_price_cents": final_price_cents,
        "total_discount_cents": total_discount_cents,
        "subtotal_cents": subtotal_cents,
        "breakdown": breakdown,
    }

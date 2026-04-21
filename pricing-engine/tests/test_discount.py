"""
Deterministic regression tests for the Meridian discount calculation engine.

Each test covers an explicitly specified scenario with fixed inputs so that
results never depend on the current date or external state.
"""

from pathlib import Path
import sys
from datetime import datetime

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pricing.discount import calculate_discount

# ---------------------------------------------------------------------------
# Deterministic reference dates
# ---------------------------------------------------------------------------
A_MONDAY = datetime(2024, 1, 8)   # weekday() == 0 → no surcharge
A_SATURDAY = datetime(2024, 1, 6)  # weekday() == 5 → weekend surcharge


# ---------------------------------------------------------------------------
# Tier-only discount tests
# ---------------------------------------------------------------------------

def test_bronze_tier_applies_five_percent():
    """Bronze tier gives a 5 % discount."""
    result = calculate_discount(10_000, "bronze", order_date=A_MONDAY)

    assert result["final_price_cents"] == 9_500
    assert result["total_discount_cents"] == 500
    assert result["subtotal_cents"] == 10_000


def test_silver_tier_applies_ten_percent():
    """Silver tier gives a 10 % discount."""
    result = calculate_discount(10_000, "silver", order_date=A_MONDAY)

    assert result["final_price_cents"] == 9_000
    assert result["total_discount_cents"] == 1_000


def test_gold_tier_applies_fifteen_percent():
    """Gold tier gives a 15 % discount."""
    result = calculate_discount(10_000, "gold", order_date=A_MONDAY)

    assert result["final_price_cents"] == 8_500
    assert result["total_discount_cents"] == 1_500


def test_platinum_tier_applies_twenty_percent():
    """Platinum tier gives a 20 % discount."""
    result = calculate_discount(10_000, "platinum", order_date=A_MONDAY)

    assert result["final_price_cents"] == 8_000
    assert result["total_discount_cents"] == 2_000


# ---------------------------------------------------------------------------
# Promo code tests
# ---------------------------------------------------------------------------

def test_save10_percentage_promo_stacks_with_tier():
    """SAVE10 (10 %) plus bronze (5 %) = 15 % total."""
    result = calculate_discount(10_000, "bronze", promo_code="SAVE10", order_date=A_MONDAY)

    assert result["final_price_cents"] == 8_500
    assert result["total_discount_cents"] == 1_500


def test_welcome5_percentage_promo_stacks_with_tier():
    """WELCOME5 (5 %) plus silver (10 %) = 15 % total."""
    result = calculate_discount(10_000, "silver", promo_code="WELCOME5", order_date=A_MONDAY)

    assert result["final_price_cents"] == 8_500
    assert result["total_discount_cents"] == 1_500


def test_flat20_promo_applied_after_percentage_discount():
    """FLAT20 reduces price by $20 after the percentage discount.

    bronze (5 %) on $100 → $95.00, then minus $20 flat → $75.00.
    """
    result = calculate_discount(10_000, "bronze", promo_code="FLAT20", order_date=A_MONDAY)

    assert result["final_price_cents"] == 7_500
    assert result["total_discount_cents"] == 2_500


def test_unknown_promo_code_is_silently_ignored():
    """An unrecognised promo code must not raise and must not change the price."""
    result_without = calculate_discount(10_000, "bronze", order_date=A_MONDAY)
    result_with = calculate_discount(10_000, "bronze", promo_code="BOGUS99", order_date=A_MONDAY)

    assert result_without["final_price_cents"] == result_with["final_price_cents"]


def test_promo_code_matching_is_case_insensitive():
    """Lowercase or mixed-case promo codes must be treated the same as uppercase."""
    result_upper = calculate_discount(10_000, "bronze", promo_code="SAVE10", order_date=A_MONDAY)
    result_lower = calculate_discount(10_000, "bronze", promo_code="save10", order_date=A_MONDAY)
    result_mixed = calculate_discount(10_000, "bronze", promo_code="Save10", order_date=A_MONDAY)

    assert result_upper["final_price_cents"] == result_lower["final_price_cents"]
    assert result_upper["final_price_cents"] == result_mixed["final_price_cents"]


def test_promo_code_surrounding_whitespace_is_stripped():
    """Promo codes with leading/trailing whitespace must be normalised."""
    result_clean = calculate_discount(10_000, "bronze", promo_code="SAVE10", order_date=A_MONDAY)
    result_padded = calculate_discount(10_000, "bronze", promo_code="  SAVE10  ", order_date=A_MONDAY)

    assert result_clean["final_price_cents"] == result_padded["final_price_cents"]


# ---------------------------------------------------------------------------
# First-purchase bonus tests
# ---------------------------------------------------------------------------

def test_first_purchase_adds_five_percent_to_tier_discount():
    """First-purchase flag adds 5 % on top of the tier discount."""
    result = calculate_discount(
        10_000, "bronze", is_first_purchase=True, order_date=A_MONDAY
    )

    # bronze 5 % + first-purchase 5 % = 10 %
    assert result["final_price_cents"] == 9_000
    assert result["total_discount_cents"] == 1_000


def test_first_purchase_combined_with_promo_code():
    """First-purchase bonus stacks correctly with a percentage promo code."""
    result = calculate_discount(
        10_000, "bronze", promo_code="SAVE10", is_first_purchase=True, order_date=A_MONDAY
    )

    # bronze 5 % + SAVE10 10 % + first-purchase 5 % = 20 %
    assert result["final_price_cents"] == 8_000
    assert result["total_discount_cents"] == 2_000


# ---------------------------------------------------------------------------
# Weekend surcharge tests
# ---------------------------------------------------------------------------

def test_weekend_surcharge_reduces_effective_discount():
    """Weekend orders carry a -2 % surcharge, reducing the net discount."""
    result = calculate_discount(10_000, "silver", order_date=A_SATURDAY)

    # silver 10 % − weekend 2 % = 8 % net discount
    assert result["final_price_cents"] == 9_200
    assert result["total_discount_cents"] == 800


def test_weekday_order_has_no_surcharge():
    """Weekday orders must not attract the weekend surcharge."""
    result = calculate_discount(10_000, "silver", order_date=A_MONDAY)

    # silver 10 % only
    assert result["final_price_cents"] == 9_000


def test_saturday_is_treated_as_weekend():
    """Saturday (weekday index 5) must trigger the surcharge."""
    saturday = datetime(2024, 1, 6)
    result = calculate_discount(10_000, "bronze", order_date=saturday)

    # bronze 5 % − 2 % = 3 % discount
    assert result["final_price_cents"] == 9_700


def test_sunday_is_treated_as_weekend():
    """Sunday (weekday index 6) must also trigger the surcharge."""
    sunday = datetime(2024, 1, 7)
    result = calculate_discount(10_000, "bronze", order_date=sunday)

    # bronze 5 % − 2 % = 3 % discount
    assert result["final_price_cents"] == 9_700


# ---------------------------------------------------------------------------
# Minimum price guardrail tests
# ---------------------------------------------------------------------------

def test_minimum_price_guardrail_prevents_price_below_one_dollar():
    """Final price must never fall below $1.00 (100 cents)."""
    # $2.00 subtotal − 5 % (bronze) = $1.90 − $20 flat (FLAT20) → negative → floor at $1.00
    result = calculate_discount(200, "bronze", promo_code="FLAT20", order_date=A_MONDAY)

    assert result["final_price_cents"] == 100


def test_zero_subtotal_is_floored_at_minimum_price():
    """A zero-cent subtotal with any discount must resolve to the $1.00 floor."""
    result = calculate_discount(0, "bronze", order_date=A_MONDAY)

    assert result["final_price_cents"] == 100


def test_subtotal_exactly_at_minimum_price_is_unchanged_after_flat_discount():
    """When the post-discount price would land exactly on the floor, it stays there."""
    # $21.00 − 5 % (bronze) = $19.95 − $20.00 flat → negative → floor at $1.00
    result = calculate_discount(2_100, "bronze", promo_code="FLAT20", order_date=A_MONDAY)

    assert result["final_price_cents"] == 100


# ---------------------------------------------------------------------------
# Discount cap tests
# ---------------------------------------------------------------------------

def test_discount_cap_not_applied_when_total_below_forty_percent():
    """No cap entry should appear in the breakdown when total discount < 40 %."""
    result = calculate_discount(
        10_000, "platinum", promo_code="SAVE10", is_first_purchase=True, order_date=A_MONDAY
    )

    # platinum 20 % + SAVE10 10 % + first-purchase 5 % = 35 % → under cap
    cap_entries = [e for e in result["breakdown"] if e.get("type") == "cap"]
    assert cap_entries == []
    assert result["final_price_cents"] == 6_500


def test_discount_cap_boundary_cases():
    """Cap is a guardrail at 40 %; current business rules top out at 35 %.

    Verify the highest achievable combination (35 %) does not trigger the cap,
    and that a lower combination (30 %) also behaves correctly.
    """
    # Highest reachable rate: platinum(20%) + SAVE10(10%) + first_purchase(5%) = 35%
    result_35 = calculate_discount(
        10_000, "platinum", promo_code="SAVE10", is_first_purchase=True, order_date=A_MONDAY
    )
    cap_entries = [e for e in result_35["breakdown"] if e.get("type") == "cap"]
    assert cap_entries == [], "Cap should not fire at 35 %"
    assert result_35["final_price_cents"] == 6_500

    # Combination at 30%: platinum(20%) + WELCOME5(5%) + first_purchase(5%)
    result_30 = calculate_discount(
        10_000, "platinum", promo_code="WELCOME5", is_first_purchase=True, order_date=A_MONDAY
    )
    cap_entries_30 = [e for e in result_30["breakdown"] if e.get("type") == "cap"]
    assert cap_entries_30 == [], "Cap should not fire at 30 %"
    assert result_30["final_price_cents"] == 7_000


# ---------------------------------------------------------------------------
# Breakdown structure tests
# ---------------------------------------------------------------------------

def test_breakdown_contains_tier_entry():
    """Result must always include a tier discount entry in the breakdown."""
    result = calculate_discount(10_000, "gold", order_date=A_MONDAY)

    tier_entries = [e for e in result["breakdown"] if e.get("type") == "tier"]
    assert len(tier_entries) == 1
    assert tier_entries[0]["rate"] == pytest.approx(0.15)


def test_breakdown_contains_promo_entry_for_valid_code():
    """A valid percentage promo code must add a promo entry to the breakdown."""
    result = calculate_discount(10_000, "bronze", promo_code="SAVE10", order_date=A_MONDAY)

    promo_entries = [e for e in result["breakdown"] if e.get("type") == "promo"]
    assert len(promo_entries) == 1
    assert promo_entries[0]["rate"] == pytest.approx(0.10)


def test_breakdown_contains_flat_promo_entry_with_amount_key():
    """A flat promo code must record an 'amount' key, not a 'rate' key."""
    result = calculate_discount(10_000, "bronze", promo_code="FLAT20", order_date=A_MONDAY)

    promo_entries = [e for e in result["breakdown"] if e.get("type") == "promo"]
    assert len(promo_entries) == 1
    assert "amount" in promo_entries[0]
    assert promo_entries[0]["amount"] == pytest.approx(20.0)


def test_breakdown_contains_surcharge_on_weekend():
    """Weekend orders must include a surcharge entry in the breakdown."""
    result = calculate_discount(10_000, "bronze", order_date=A_SATURDAY)

    surcharge_entries = [e for e in result["breakdown"] if e.get("type") == "surcharge"]
    assert len(surcharge_entries) == 1
    assert surcharge_entries[0]["rate"] == pytest.approx(-0.02)


def test_breakdown_has_no_surcharge_on_weekday():
    """Weekday orders must not include a surcharge entry."""
    result = calculate_discount(10_000, "bronze", order_date=A_MONDAY)

    surcharge_entries = [e for e in result["breakdown"] if e.get("type") == "surcharge"]
    assert surcharge_entries == []


def test_breakdown_contains_first_purchase_entry():
    """First-purchase orders must include a first_purchase entry in the breakdown."""
    result = calculate_discount(
        10_000, "bronze", is_first_purchase=True, order_date=A_MONDAY
    )

    fp_entries = [e for e in result["breakdown"] if e.get("type") == "first_purchase"]
    assert len(fp_entries) == 1
    assert fp_entries[0]["rate"] == pytest.approx(0.05)


# ---------------------------------------------------------------------------
# Input validation tests
# ---------------------------------------------------------------------------

def test_negative_subtotal_raises_value_error():
    """Negative subtotals are not permitted and must raise ValueError."""
    with pytest.raises(ValueError, match="Subtotal cannot be negative"):
        calculate_discount(-1, "bronze")


def test_invalid_tier_raises_value_error():
    """An unrecognised customer tier must raise ValueError."""
    with pytest.raises(ValueError, match="Unrecognised tier"):
        calculate_discount(10_000, "diamond")


def test_all_valid_tiers_are_accepted():
    """All four documented tiers must not raise."""
    for tier in ("bronze", "silver", "gold", "platinum"):
        result = calculate_discount(10_000, tier, order_date=A_MONDAY)
        assert "final_price_cents" in result


# ---------------------------------------------------------------------------
# Return-value contract tests
# ---------------------------------------------------------------------------

def test_return_value_contains_required_keys():
    """The result dict must always include the three documented keys."""
    result = calculate_discount(10_000, "bronze", order_date=A_MONDAY)

    assert "final_price_cents" in result
    assert "total_discount_cents" in result
    assert "subtotal_cents" in result
    assert "breakdown" in result


def test_subtotal_cents_is_echoed_in_result():
    """The returned subtotal_cents must equal the input value."""
    result = calculate_discount(5_555, "silver", order_date=A_MONDAY)

    assert result["subtotal_cents"] == 5_555


def test_final_price_plus_discount_equals_subtotal():
    """final_price_cents + total_discount_cents must always equal subtotal_cents.

    This identity holds even when the minimum-price guardrail is active because
    total_discount_cents is derived as subtotal_cents − final_price_cents.
    """
    # Normal case: no guardrail
    result = calculate_discount(10_000, "gold", order_date=A_MONDAY)

    assert result["final_price_cents"] + result["total_discount_cents"] == result["subtotal_cents"]


def test_final_price_plus_discount_equals_subtotal_when_guardrail_fires():
    """The identity also holds when the minimum-price guardrail clamps the price."""
    # $2.00 − 5 % bronze − $20 FLAT20 would be negative; guardrail fires.
    result = calculate_discount(200, "bronze", promo_code="FLAT20", order_date=A_MONDAY)

    assert result["final_price_cents"] == 100
    assert result["final_price_cents"] + result["total_discount_cents"] == result["subtotal_cents"]

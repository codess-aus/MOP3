"""Tests for the search query builder pagination helper."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from search.query_builder import fetch_paginated_results


# ---------------------------------------------------------------------------
# Mutable-default regression tests
# ---------------------------------------------------------------------------

def test_fetch_paginated_results_does_not_leak_default_filters_between_calls():
    """Each call should receive a fresh default list of filters."""
    first = fetch_paginated_results(page=1, page_size=10)
    second = fetch_paginated_results(page=2, page_size=10)

    assert first["query"]["filters"] == [{"active": True}]
    assert second["query"]["filters"] == [{"active": True}]


def test_fetch_paginated_results_does_not_mutate_caller_filters():
    """Caller-provided filters should remain unchanged after invocation."""
    caller_filters = [{"order_status": "pending"}]

    result = fetch_paginated_results(page=1, page_size=5, filters=caller_filters)

    assert caller_filters == [{"order_status": "pending"}]
    assert result["query"]["filters"] == [{"order_status": "pending"}, {"active": True}]


def test_fetch_paginated_results_repeated_default_calls_each_have_single_active_filter():
    """Calling without filters many times must never accumulate active entries."""
    for _ in range(5):
        result = fetch_paginated_results(page=1, page_size=10)
        assert result["query"]["filters"] == [{"active": True}]


def test_fetch_paginated_results_caller_list_not_mutated_across_multiple_calls():
    """The same caller list passed twice must not grow between calls."""
    caller_filters = [{"category": "electronics"}]

    fetch_paginated_results(page=1, page_size=10, filters=caller_filters)
    fetch_paginated_results(page=2, page_size=10, filters=caller_filters)

    assert caller_filters == [{"category": "electronics"}]


# ---------------------------------------------------------------------------
# Pagination offset tests
# ---------------------------------------------------------------------------

def test_first_page_produces_zero_offset():
    """Page 1 should always map to offset 0."""
    result = fetch_paginated_results(page=1, page_size=10)

    assert result["query"]["offset"] == 0


def test_second_page_produces_correct_offset():
    """Page 2 with page_size 10 should map to offset 10."""
    result = fetch_paginated_results(page=2, page_size=10)

    assert result["query"]["offset"] == 10


def test_arbitrary_page_produces_correct_offset():
    """Page 5 with page_size 3 should map to offset 12."""
    result = fetch_paginated_results(page=5, page_size=3)

    assert result["query"]["offset"] == 12


def test_page_size_is_used_as_query_limit():
    """The page_size argument must be forwarded as the query limit."""
    result = fetch_paginated_results(page=1, page_size=25)

    assert result["query"]["limit"] == 25


# ---------------------------------------------------------------------------
# Filter composition tests
# ---------------------------------------------------------------------------

def test_active_filter_is_appended_after_caller_filters():
    """The active-only constraint must come after any caller-supplied filters."""
    result = fetch_paginated_results(page=1, page_size=10, filters=[{"brand": "acme"}])

    assert result["query"]["filters"] == [{"brand": "acme"}, {"active": True}]


def test_multiple_caller_filters_are_all_preserved():
    """All caller-provided filters must be present in the final query."""
    filters = [{"brand": "acme"}, {"price_max": 500}]
    result = fetch_paginated_results(page=1, page_size=10, filters=filters)

    assert {"brand": "acme"} in result["query"]["filters"]
    assert {"price_max": 500} in result["query"]["filters"]
    assert {"active": True} in result["query"]["filters"]


def test_empty_explicit_filter_list_behaves_like_no_filters():
    """Passing an explicit empty list should behave identically to omitting filters."""
    result_omitted = fetch_paginated_results(page=1, page_size=10)
    result_explicit = fetch_paginated_results(page=1, page_size=10, filters=[])

    assert result_omitted["query"]["filters"] == result_explicit["query"]["filters"]

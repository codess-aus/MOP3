"""Tests for the search query builder pagination helper."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from search.query_builder import fetch_paginated_results


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

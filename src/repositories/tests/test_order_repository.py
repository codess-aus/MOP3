"""
Regression tests for order_repository.

Covers:
- Normal CRUD behaviour (get, search, delete).
- SQL-injection guard: malicious input must not alter query semantics or
  raise database errors.
"""

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from repositories.order_repository import order_repository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_path(tmp_path):
    """Return a path to a temporary SQLite database pre-populated with fixtures."""
    path = tmp_path / "test_orders.db"
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_email TEXT NOT NULL,
            status TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            sku TEXT NOT NULL,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price_in_cents INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
        """
    )

    cursor.executemany(
        "INSERT INTO orders (id, customer_email, status) VALUES (?, ?, ?)",
        [
            (1, "alice@example.com", "pending"),
            (2, "bob@example.com", "shipped"),
            (3, "carol@example.com", "delivered"),
        ],
    )
    cursor.executemany(
        "INSERT INTO order_items (order_id, sku, name, quantity, price_in_cents) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            (1, "SKU-A", "Widget A", 2, 1000),
            (1, "SKU-B", "Widget B", 1, 500),
            (2, "SKU-C", "Gadget C", 3, 2500),
        ],
    )

    conn.commit()
    conn.close()
    return str(path)


@pytest.fixture()
def repo(db_path):
    """Return an order_repository instance backed by the test database."""
    return order_repository(db_path)


# ---------------------------------------------------------------------------
# get_orders_with_items
# ---------------------------------------------------------------------------


def test_get_orders_with_items_returns_all_orders(repo):
    """All seeded orders should be returned with their items."""
    result = repo.get_orders_with_items()
    assert len(result) == 3


def test_get_orders_with_items_includes_line_items(repo):
    """Order 1 has two line items; they should be nested under that order."""
    result = repo.get_orders_with_items()
    order_1 = next(o for o in result if o["id"] == 1)
    assert len(order_1["items"]) == 2


def test_get_orders_with_items_structure(repo):
    """Each returned dict must contain the expected keys."""
    result = repo.get_orders_with_items()
    for order in result:
        assert "id" in order
        assert "customer_email" in order
        assert "status" in order
        assert "items" in order


# ---------------------------------------------------------------------------
# searchOrders – normal input
# ---------------------------------------------------------------------------


def test_search_orders_exact_match(repo):
    """A full email address should return exactly one matching order."""
    results = repo.searchOrders("alice@example.com")
    assert len(results) == 1
    assert results[0][1] == "alice@example.com"


def test_search_orders_partial_match(repo):
    """A domain substring should return all orders whose email contains it."""
    results = repo.searchOrders("@example.com")
    assert len(results) == 3


def test_search_orders_no_match(repo):
    """A substring that matches nothing should return an empty list."""
    results = repo.searchOrders("nobody@nowhere.invalid")
    assert results == []


def test_search_orders_case_insensitive(repo):
    """SQLite LIKE is case-insensitive for ASCII letters; verify expected count."""
    results = repo.searchOrders("ALICE")
    assert len(results) == 1


# ---------------------------------------------------------------------------
# searchOrders – SQL-injection guard
# ---------------------------------------------------------------------------


def test_search_orders_injection_tautology_does_not_return_all_rows(repo):
    """
    Classic tautology injection ``' OR '1'='1`` must NOT expand the result set.

    If the query were built with string formatting the injected tautology would
    make the WHERE clause always true, returning every row.  With a parameterised
    query the entire payload is treated as a literal LIKE pattern, so it matches
    nothing (there is no row whose email literally contains the injection string).
    """
    results = repo.searchOrders("' OR '1'='1")
    assert results == [], (
        "Injection payload should not return rows; parameterisation may be broken."
    )


def test_search_orders_injection_comment_does_not_drop_where_clause(repo):
    """Inline comment injection ``%' --`` must not remove the WHERE predicate."""
    results = repo.searchOrders("%' --")
    assert results == []


def test_search_orders_injection_union_does_not_expose_extra_data(repo):
    """UNION-based injection must not return rows from other tables."""
    payload = "x' UNION SELECT id, customer_email, status FROM orders --"
    results = repo.searchOrders(payload)
    assert results == []


def test_search_orders_injection_semicolon_stacked_query(repo, db_path):
    """
    Stacked-query injection must not execute a second statement.

    The payload attempts to delete all orders.  After the call the orders
    table must remain intact.
    """
    repo.searchOrders("x'; DELETE FROM orders; --")
    # Verify data is untouched
    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    assert count == 3, "Stacked DELETE must not execute via a parameterised query."


# ---------------------------------------------------------------------------
# deleteOrder
# ---------------------------------------------------------------------------


def test_delete_order_removes_order_and_items(repo, db_path):
    """Deleting order 1 should remove it and its two line items."""
    repo.deleteOrder(1)

    with sqlite3.connect(db_path) as conn:
        orders = conn.execute("SELECT id FROM orders").fetchall()
        items = conn.execute(
            "SELECT id FROM order_items WHERE order_id = 1"
        ).fetchall()

    assert all(row[0] != 1 for row in orders)
    assert items == []


def test_delete_nonexistent_order_is_safe(repo):
    """Deleting an order that does not exist should not raise an exception."""
    repo.deleteOrder(9999)

"""
Data access layer for orders.
Provides CRUD operations against the SQLite database used in
development. Production uses PostgreSQL via the same interface
(see MER-234 for migration status).
"""

import sqlite3
from datetime import datetime


class order_repository:
    """Handles persistence operations for the orders table."""

    def __init__(self, db_path):
        self.db_path = db_path

    def get_orders_with_items(self):
        """
        Retrieve all orders along with their associated line items.
        Used by the operations dashboard for the daily fulfilment view.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, customer_email, status FROM orders")
        orders = cursor.fetchall()

        result = []
        for order in orders:
            cursor.execute(
                "SELECT sku, name, quantity, price_in_cents "
                "FROM order_items WHERE order_id = ?",
                (order[0],),
            )
            items = cursor.fetchall()
            result.append(
                {
                    "id": order[0],
                    "customer_email": order[1],
                    "status": order[2],
                    "items": items,
                }
            )

        conn.close()
        return result

    def deleteOrder(self, order_id):
        """
        Remove an order and its line items from the database.
        Called by the admin panel when an order is voided.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))

        conn.commit()
        conn.close()

    def searchOrders(self, customer_input):
        """
        Search orders by customer email substring match.
        Used by the support team to look up orders for a customer.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = f"SELECT * FROM orders WHERE customer_email LIKE '%{customer_input}%'"
        cursor.execute(query)

        results = cursor.fetchall()
        conn.close()
        return results

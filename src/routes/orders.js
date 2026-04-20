const express = require("express");
const router = express.Router();
const db = require("../data/orderStore");

/**
 * GET /api/orders
 * Returns all orders, optionally filtered by status.
 * @query {string} status - Filter by order status
 */
router.get("/", (req, res) => {
  let orders = db.getAll();

  if (req.query.status) {
    orders = orders.filter((o) => o.status === req.query.status);
  }

  res.json({ data: orders, count: orders.length });
});

/**
 * GET /api/orders/:id
 * Returns a single order by its ID.
 * @param {string} id - The order ID
 */
router.get("/:id", (req, res) => {
  const order = db.findById(parseInt(req.params.id));

  if (!order) {
    return res.status(404).json({
      type: "https://meridian.internal/errors/not-found",
      title: "Order Not Found",
      status: 404,
      detail: `No order exists with ID ${req.params.id}.`,
    });
  }

  res.json({ data: order });
});

/**
 * POST /api/orders
 * Creates a new order. Currently accepts any payload without
 * validation or authentication.
 */
router.post("/", (req, res) => {
  const { customerEmail, items } = req.body;

  if (!customerEmail || !items || !Array.isArray(items) || items.length === 0) {
    return res.status(400).json({
      type: "https://meridian.internal/errors/validation",
      title: "Validation Error",
      status: 400,
      detail: "customerEmail and a non-empty items array are required.",
    });
  }

  const order = db.create({ customerEmail, items });
  res.status(201).json({ data: order });
});

/**
 * PATCH /api/orders/:id/status
 * Updates the status of an existing order.
 * @param {string} id - The order ID
 * @body {string} status - The new status value
 */
router.patch("/:id/status", (req, res) => {
  const { status } = req.body;
  const validStatuses = ["pending", "processing", "shipped", "delivered", "cancelled"];

  if (!status || !validStatuses.includes(status)) {
    return res.status(400).json({
      type: "https://meridian.internal/errors/validation",
      title: "Invalid Status",
      status: 400,
      detail: `Status must be one of: ${validStatuses.join(", ")}.`,
    });
  }

  const order = db.updateStatus(parseInt(req.params.id), status);

  if (!order) {
    return res.status(404).json({
      type: "https://meridian.internal/errors/not-found",
      title: "Order Not Found",
      status: 404,
      detail: `No order exists with ID ${req.params.id}.`,
    });
  }

  res.json({ data: order });
});

/**
 * DELETE /api/orders/:id
 * Permanently removes an order. This action cannot be undone.
 * @param {string} id - The order ID
 */
router.delete("/:id", (req, res) => {
  const deleted = db.remove(parseInt(req.params.id));

  if (!deleted) {
    return res.status(404).json({
      type: "https://meridian.internal/errors/not-found",
      title: "Order Not Found",
      status: 404,
      detail: `No order exists with ID ${req.params.id}.`,
    });
  }

  res.status(204).send();
});

module.exports = router;

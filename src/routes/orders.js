const express = require("express");
const router = express.Router();
const db = require("../data/orderStore");

/** Simple email format check (local@domain.tld). */
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Returns a RFC 7807 Problem Details JSON response.
 * Sets the recommended Content-Type header.
 * @param {import('express').Response} res
 * @param {number} statusCode
 * @param {string} type
 * @param {string} title
 * @param {string} detail
 */
function problemResponse(res, statusCode, type, title, detail) {
  return res
    .status(statusCode)
    .set("Content-Type", "application/problem+json")
    .json({ type, title, status: statusCode, detail });
}

/**
 * Validates that an :id route parameter is a positive integer string.
 * Responds with 400 if invalid, otherwise continues.
 */
function validateId(req, res, next) {
  const id = req.params.id;
  if (!/^\d+$/.test(id) || parseInt(id, 10) < 1) {
    return problemResponse(
      res,
      400,
      "https://meridian.internal/errors/validation",
      "Invalid Order ID",
      "Order ID must be a positive integer."
    );
  }
  next();
}

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
router.get("/:id", validateId, (req, res) => {
  const order = db.findById(parseInt(req.params.id, 10));

  if (!order) {
    return problemResponse(
      res,
      404,
      "https://meridian.internal/errors/not-found",
      "Order Not Found",
      `No order exists with ID ${req.params.id}.`
    );
  }

  res.json({ data: order });
});

/**
 * POST /api/orders
 * Creates a new order.
 * @body {string} customerEmail - Valid email address of the customer
 * @body {Array}  items - Non-empty array; each item must include sku, name, quantity (>0), priceInCents (>=0)
 */
router.post("/", (req, res) => {
  const { customerEmail, items } = req.body || {};

  if (!customerEmail || typeof customerEmail !== "string" || !EMAIL_RE.test(customerEmail)) {
    return problemResponse(
      res,
      400,
      "https://meridian.internal/errors/validation",
      "Validation Error",
      "customerEmail must be a valid email address."
    );
  }

  if (!items || !Array.isArray(items) || items.length === 0) {
    return problemResponse(
      res,
      400,
      "https://meridian.internal/errors/validation",
      "Validation Error",
      "items must be a non-empty array."
    );
  }

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (!item || typeof item !== "object") {
      return problemResponse(
        res,
        400,
        "https://meridian.internal/errors/validation",
        "Validation Error",
        `items[${i}] must be an object.`
      );
    }
    if (typeof item.sku !== "string" || item.sku.trim() === "") {
      return problemResponse(
        res,
        400,
        "https://meridian.internal/errors/validation",
        "Validation Error",
        `items[${i}].sku must be a non-empty string.`
      );
    }
    if (typeof item.name !== "string" || item.name.trim() === "") {
      return problemResponse(
        res,
        400,
        "https://meridian.internal/errors/validation",
        "Validation Error",
        `items[${i}].name must be a non-empty string.`
      );
    }
    if (!Number.isInteger(item.quantity) || item.quantity < 1) {
      return problemResponse(
        res,
        400,
        "https://meridian.internal/errors/validation",
        "Validation Error",
        `items[${i}].quantity must be a positive integer.`
      );
    }
    if (!Number.isInteger(item.priceInCents) || item.priceInCents < 0) {
      return problemResponse(
        res,
        400,
        "https://meridian.internal/errors/validation",
        "Validation Error",
        `items[${i}].priceInCents must be a non-negative integer (cents).`
      );
    }
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
router.patch("/:id/status", validateId, (req, res) => {
  const { status } = req.body || {};
  const validStatuses = ["pending", "processing", "shipped", "delivered", "cancelled"];

  if (!status || !validStatuses.includes(status)) {
    return problemResponse(
      res,
      400,
      "https://meridian.internal/errors/validation",
      "Invalid Status",
      `Status must be one of: ${validStatuses.join(", ")}.`
    );
  }

  const order = db.updateStatus(parseInt(req.params.id, 10), status);

  if (!order) {
    return problemResponse(
      res,
      404,
      "https://meridian.internal/errors/not-found",
      "Order Not Found",
      `No order exists with ID ${req.params.id}.`
    );
  }

  res.json({ data: order });
});

/**
 * DELETE /api/orders/:id
 * Permanently removes an order. This action cannot be undone.
 * @param {string} id - The order ID
 */
router.delete("/:id", validateId, (req, res) => {
  const deleted = db.remove(parseInt(req.params.id, 10));

  if (!deleted) {
    return problemResponse(
      res,
      404,
      "https://meridian.internal/errors/not-found",
      "Order Not Found",
      `No order exists with ID ${req.params.id}.`
    );
  }

  res.status(204).send();
});

module.exports = router;

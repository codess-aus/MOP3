/**
 * In-memory order store.
 * This module will be replaced with a PostgreSQL-backed repository
 * once the database migration is complete (see GitHub issue: MER-234).
 */

let nextId = 4;

let orders = [
  {
    id: 1,
    customerEmail: "chen.wei@meridian.co",
    items: [{ sku: "KB-2400", name: "Mechanical Keyboard", quantity: 2, priceInCents: 8999 }],
    status: "shipped",
    createdAt: "2026-03-12T09:14:00Z",
    updatedAt: "2026-03-14T11:30:00Z",
  },
  {
    id: 2,
    customerEmail: "priya.sharma@meridian.co",
    items: [{ sku: "MN-3200", name: "Ultra-wide Monitor", quantity: 1, priceInCents: 54999 }],
    status: "processing",
    createdAt: "2026-04-01T14:22:00Z",
    updatedAt: "2026-04-01T14:22:00Z",
  },
  {
    id: 3,
    customerEmail: "james.oconnor@meridian.co",
    items: [
      { sku: "MS-1100", name: "Ergonomic Mouse", quantity: 5, priceInCents: 3499 },
      { sku: "MP-0500", name: "Mouse Pad XL", quantity: 5, priceInCents: 1299 },
    ],
    status: "delivered",
    createdAt: "2026-02-18T08:45:00Z",
    updatedAt: "2026-03-02T16:10:00Z",
  },
];

module.exports = {
  getAll() {
    return [...orders];
  },

  findById(id) {
    return orders.find((o) => o.id === id) || null;
  },

  create({ customerEmail, items }) {
    const now = new Date().toISOString();
    const order = {
      id: nextId++,
      customerEmail,
      items,
      status: "pending",
      createdAt: now,
      updatedAt: now,
    };
    orders.push(order);
    return order;
  },

  updateStatus(id, status) {
    const order = orders.find((o) => o.id === id);
    if (!order) return null;
    order.status = status;
    order.updatedAt = new Date().toISOString();
    return order;
  },

  remove(id) {
    const index = orders.findIndex((o) => o.id === id);
    if (index === -1) return false;
    orders.splice(index, 1);
    return true;
  },
};

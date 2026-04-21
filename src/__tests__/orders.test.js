"use strict";

const request = require("supertest");
const app = require("../index");

/**
 * Reset the in-memory order store before each test so state does not leak
 * between test cases.  We reach into the module cache and replace the orders
 * array directly to keep the implementation simple.
 */
const orderStore = require("../data/orderStore");

/** Seed data mirroring orderStore.js initial state. */
const SEED = [
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

/**
 * Helper – asserts the body conforms to RFC 7807 Problem Details structure.
 * @param {object} body - Parsed response body
 * @param {number} expectedStatus
 */
function assertProblemDetails(body, expectedStatus) {
  expect(typeof body.type).toBe("string");
  expect(body.type).toMatch(/^https:\/\/meridian\.internal\/errors\//);
  expect(typeof body.title).toBe("string");
  expect(body.status).toBe(expectedStatus);
  expect(typeof body.detail).toBe("string");
}

/** Valid item shape for POST requests. */
const VALID_ITEM = { sku: "KB-2400", name: "Mechanical Keyboard", quantity: 1, priceInCents: 8999 };

beforeEach(() => {
  // Restore in-memory store to a clean copy of the seed data.
  const fresh = SEED.map((order) => ({ ...order, items: order.items.map((item) => ({ ...item })) }));
  // Overwrite the internal orders array and reset the ID counter via the
  // exported module – we patch through the known public API where possible,
  // and reset internal state via a test-only backdoor on the module itself.
  // Since orderStore exports a plain object we can mutate its internal state
  // by replacing orders via a helper exposed on the module.
  if (typeof orderStore._reset === "function") {
    orderStore._reset(fresh);
  }
});

// ─── GET /api/orders ──────────────────────────────────────────────────────────

describe("GET /api/orders", () => {
  it("returns 200 with data array and count", async () => {
    const res = await request(app).get("/api/orders");
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.data)).toBe(true);
    expect(typeof res.body.count).toBe("number");
    expect(res.body.count).toBe(res.body.data.length);
  });

  it("filters by status query parameter", async () => {
    const res = await request(app).get("/api/orders?status=shipped");
    expect(res.status).toBe(200);
    res.body.data.forEach((order) => expect(order.status).toBe("shipped"));
  });

  it("returns empty array for unknown status filter", async () => {
    const res = await request(app).get("/api/orders?status=nonexistent");
    expect(res.status).toBe(200);
    expect(res.body.data).toEqual([]);
    expect(res.body.count).toBe(0);
  });
});

// ─── GET /api/orders/:id ──────────────────────────────────────────────────────

describe("GET /api/orders/:id", () => {
  it("returns 200 with the order when found", async () => {
    const res = await request(app).get("/api/orders/1");
    expect(res.status).toBe(200);
    expect(res.body.data).toBeDefined();
    expect(res.body.data.id).toBe(1);
  });

  it("returns 404 RFC 7807 problem details for unknown ID", async () => {
    const res = await request(app).get("/api/orders/9999");
    expect(res.status).toBe(404);
    expect(res.headers["content-type"]).toMatch(/application\/problem\+json/);
    assertProblemDetails(res.body, 404);
  });

  it("returns 400 RFC 7807 problem details for non-integer ID", async () => {
    const res = await request(app).get("/api/orders/abc");
    expect(res.status).toBe(400);
    expect(res.headers["content-type"]).toMatch(/application\/problem\+json/);
    assertProblemDetails(res.body, 400);
  });

  it("returns 400 for negative ID", async () => {
    const res = await request(app).get("/api/orders/-5");
    expect(res.status).toBe(400);
    assertProblemDetails(res.body, 400);
  });

  it("returns 400 for floating point ID", async () => {
    const res = await request(app).get("/api/orders/1.5");
    expect(res.status).toBe(400);
    assertProblemDetails(res.body, 400);
  });
});

// ─── POST /api/orders ─────────────────────────────────────────────────────────

describe("POST /api/orders", () => {
  const VALID_BODY = {
    customerEmail: "test@example.com",
    items: [VALID_ITEM],
  };

  it("creates an order and returns 201 with the order object", async () => {
    const res = await request(app)
      .post("/api/orders")
      .send(VALID_BODY);
    expect(res.status).toBe(201);
    expect(res.body.data).toBeDefined();
    expect(res.body.data.customerEmail).toBe("test@example.com");
    expect(res.body.data.status).toBe("pending");
  });

  it("returns 400 RFC 7807 when customerEmail is missing", async () => {
    const res = await request(app)
      .post("/api/orders")
      .send({ items: [VALID_ITEM] });
    expect(res.status).toBe(400);
    expect(res.headers["content-type"]).toMatch(/application\/problem\+json/);
    assertProblemDetails(res.body, 400);
  });

  it("returns 400 RFC 7807 when customerEmail is not a valid email", async () => {
    const res = await request(app)
      .post("/api/orders")
      .send({ customerEmail: "not-an-email", items: [VALID_ITEM] });
    expect(res.status).toBe(400);
    expect(res.headers["content-type"]).toMatch(/application\/problem\+json/);
    assertProblemDetails(res.body, 400);
  });

  it("returns 400 RFC 7807 when items is missing", async () => {
    const res = await request(app)
      .post("/api/orders")
      .send({ customerEmail: "test@example.com" });
    expect(res.status).toBe(400);
    assertProblemDetails(res.body, 400);
  });

  it("returns 400 RFC 7807 when items is empty array", async () => {
    const res = await request(app)
      .post("/api/orders")
      .send({ customerEmail: "test@example.com", items: [] });
    expect(res.status).toBe(400);
    assertProblemDetails(res.body, 400);
  });

  it("returns 400 RFC 7807 when an item is missing sku", async () => {
    const item = { ...VALID_ITEM };
    delete item.sku;
    const res = await request(app)
      .post("/api/orders")
      .send({ customerEmail: "test@example.com", items: [item] });
    expect(res.status).toBe(400);
    assertProblemDetails(res.body, 400);
  });

  it("returns 400 RFC 7807 when an item has non-positive quantity", async () => {
    const res = await request(app)
      .post("/api/orders")
      .send({ customerEmail: "test@example.com", items: [{ ...VALID_ITEM, quantity: 0 }] });
    expect(res.status).toBe(400);
    assertProblemDetails(res.body, 400);
  });

  it("returns 400 RFC 7807 when priceInCents is negative", async () => {
    const res = await request(app)
      .post("/api/orders")
      .send({ customerEmail: "test@example.com", items: [{ ...VALID_ITEM, priceInCents: -1 }] });
    expect(res.status).toBe(400);
    assertProblemDetails(res.body, 400);
  });

  it("returns 400 RFC 7807 when priceInCents is a float", async () => {
    const res = await request(app)
      .post("/api/orders")
      .send({ customerEmail: "test@example.com", items: [{ ...VALID_ITEM, priceInCents: 9.99 }] });
    expect(res.status).toBe(400);
    assertProblemDetails(res.body, 400);
  });
});

// ─── PATCH /api/orders/:id/status ─────────────────────────────────────────────

describe("PATCH /api/orders/:id/status", () => {
  it("updates status and returns 200 with the updated order", async () => {
    const res = await request(app)
      .patch("/api/orders/2/status")
      .send({ status: "shipped" });
    expect(res.status).toBe(200);
    expect(res.body.data.status).toBe("shipped");
  });

  it("returns 400 RFC 7807 for invalid status value", async () => {
    const res = await request(app)
      .patch("/api/orders/1/status")
      .send({ status: "flying" });
    expect(res.status).toBe(400);
    expect(res.headers["content-type"]).toMatch(/application\/problem\+json/);
    assertProblemDetails(res.body, 400);
  });

  it("returns 400 RFC 7807 when status is missing", async () => {
    const res = await request(app)
      .patch("/api/orders/1/status")
      .send({});
    expect(res.status).toBe(400);
    assertProblemDetails(res.body, 400);
  });

  it("returns 404 RFC 7807 when order not found", async () => {
    const res = await request(app)
      .patch("/api/orders/9999/status")
      .send({ status: "pending" });
    expect(res.status).toBe(404);
    expect(res.headers["content-type"]).toMatch(/application\/problem\+json/);
    assertProblemDetails(res.body, 404);
  });

  it("returns 400 RFC 7807 for non-integer ID", async () => {
    const res = await request(app)
      .patch("/api/orders/abc/status")
      .send({ status: "pending" });
    expect(res.status).toBe(400);
    assertProblemDetails(res.body, 400);
  });
});

// ─── DELETE /api/orders/:id ───────────────────────────────────────────────────

describe("DELETE /api/orders/:id", () => {
  it("deletes an order and returns 204 with no body", async () => {
    const res = await request(app).delete("/api/orders/1");
    expect(res.status).toBe(204);
    expect(res.text).toBe("");
  });

  it("returns 404 RFC 7807 when order not found", async () => {
    const res = await request(app).delete("/api/orders/9999");
    expect(res.status).toBe(404);
    expect(res.headers["content-type"]).toMatch(/application\/problem\+json/);
    assertProblemDetails(res.body, 404);
  });

  it("returns 400 RFC 7807 for non-integer ID", async () => {
    const res = await request(app).delete("/api/orders/abc");
    expect(res.status).toBe(400);
    assertProblemDetails(res.body, 400);
  });
});

// ─── RFC 7807 shape guarantee ─────────────────────────────────────────────────

describe("RFC 7807 Problem Details shape", () => {
  const errorCases = [
    { label: "GET /:id non-integer", req: () => request(app).get("/api/orders/x") },
    { label: "GET /:id not-found",   req: () => request(app).get("/api/orders/9999") },
    { label: "POST missing email",   req: () => request(app).post("/api/orders").send({ items: [VALID_ITEM] }) },
    { label: "PATCH invalid status", req: () => request(app).patch("/api/orders/1/status").send({ status: "bad" }) },
    { label: "DELETE non-integer",   req: () => request(app).delete("/api/orders/x") },
  ];

  errorCases.forEach(({ label, req }) => {
    it(`${label} – response has type, title, status, detail`, async () => {
      const res = await req();
      expect(res.status).toBeGreaterThanOrEqual(400);
      expect(res.headers["content-type"]).toMatch(/application\/problem\+json/);
      const body = res.body;
      expect(typeof body.type).toBe("string");
      expect(typeof body.title).toBe("string");
      expect(typeof body.status).toBe("number");
      expect(typeof body.detail).toBe("string");
      expect(body.status).toBe(res.status);
    });
  });
});

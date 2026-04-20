# Meridian Operations Platform

Backend services and support modules for Meridian internal order operations.

This repository currently contains:

- A Node.js Express API for order management.
- A Python search helper module used for query-building demos and test exercises.
- A Python pricing utility for discount calculations.

## Repository Layout

- src/: Express API (orders endpoints, in-memory data store, service classes)
- search-service/: Python search module and pytest suite
- pricing-engine/: Python pricing and discount logic
- project-structure.txt: Snapshot of the current repository structure

## Tech Stack

- Node.js >= 22
- Express 5
- Jest + ESLint (configured in package.json)
- Python 3.11+ recommended (used by search-service and pricing-engine)
- pytest (for search-service tests)

## Quick Start

### 1) Install JavaScript dependencies

Run from repository root:

npm install

### 2) Start the API

Run from repository root:

npm start

By default, the API runs on port 3000.

Health check:

GET /health

### 3) Run API in watch mode (development)

npm run dev

## API Endpoints

Base path: /api/orders

### List orders

- Method: GET
- Path: /api/orders
- Optional query: status

Returns:

- data: array of orders
- count: number of returned orders

### Get order by ID

- Method: GET
- Path: /api/orders/:id

404 responses use RFC 7807 style Problem Details fields:

- type
- title
- status
- detail

### Create order

- Method: POST
- Path: /api/orders
- Required body fields: customerEmail, items (non-empty array)

### Update order status

- Method: PATCH
- Path: /api/orders/:id/status
- Required body field: status
- Allowed statuses: pending, processing, shipped, delivered, cancelled

### Delete order

- Method: DELETE
- Path: /api/orders/:id

Returns 204 on success.

## Data Model (Current)

The API currently uses an in-memory order store in src/data/orderStore.js.

Each order contains:

- id
- customerEmail
- items (sku, name, quantity, priceInCents)
- status
- createdAt
- updatedAt

Note: Monetary values are represented as integer cents.

## Python Modules

### search-service

Path: search-service/search/query_builder.py

Contains query construction helpers and pagination behavior used in tests and demos.

Run tests:

cd search-service
python -m venv .venv
source .venv/bin/activate
pip install -U pip pytest
pytest -q

### pricing-engine

Path: pricing-engine/pricing/discount.py

Implements pricing rules including:

- Tier discounts
- Promo code discounts
- First purchase bonus
- Weekend surcharge
- Maximum discount cap
- Minimum final price guardrail

## Scripts

From repository root:

- npm start: Start API server
- npm run dev: Start API with file watching
- npm test: Run Jest with coverage
- npm run lint: Lint JavaScript under src/

## Environment Variables

Currently used:

- PORT (optional): HTTP port for API, defaults to 3000

## Current Limitations and Follow-ups

- Authentication is not implemented yet.
- JavaScript service classes currently use console logging and are not wired into the Express routes.
- src/repositories/order_repository.py includes mixed naming conventions and a string-interpolated SQL query in searchOrders that should be parameterized.
- Search and pricing Python modules are local utilities and are not yet exposed as standalone services.

## Development Notes

- Use RFC 7807-compatible error responses for API failures.
- Keep money values in integer cents.
- Prefer parameterized SQL queries.
- Add deterministic tests for new behavior.

## License

See LICENSE.
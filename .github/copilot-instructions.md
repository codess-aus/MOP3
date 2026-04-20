# Copilot Instructions for Meridian Operations Platform

## Repository Context
This repository contains the backend API for Meridian's internal order
management system. It is used by the operations team to manage customer
orders, process payments, send notifications, and generate reports.

## Architecture
- Runtime: Node.js with Express
- Database: SQLite for development, PostgreSQL for staging and production
- Authentication: Currently unimplemented (tracked as a priority item)
- Deployment: Docker containers on Azure Container Apps behind Azure Application Gateway

## Code Standards
- Use ES module syntax where possible
- All functions must include JSDoc comments
- Error responses must follow RFC 7807 Problem Details format
- Use structured JSON logging (no console.log in production code)
- All monetary values must be handled with integer cents, not floats

## Security Requirements
- All secrets must come from environment variables, never hardcoded
- SQL queries must use parameterised statements
- User input must be validated and sanitised before use
- Authentication tokens must be short-lived with a refresh mechanism
- Passwords must be hashed with a computationally expensive algorithm

## Testing
- Unit tests required for all business logic
- Integration tests required for all API endpoints
- Minimum 80% code coverage for new code
- Tests must be deterministic and not depend on external services

## Review Guidelines
- Prioritise security and correctness over brevity
- Flag any N+1 query patterns
- Flag any missing error handling on async operations
- Enforce consistent naming conventions (camelCase for JS, snake_case for DB)

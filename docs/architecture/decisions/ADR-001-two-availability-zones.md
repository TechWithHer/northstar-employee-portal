# ADR-001: Use Two Availability Zones

**Status:** Accepted by the Engineering Lead (AM)
**Date:** 2026-10-07

## Context

Northstar V1 uses a single application instance and a single database instance, creating potential single points of failure.

For V2, the infrastructure needs improved availability without
introducing unnecessary cost and operational complexity.

## Options Considered

### Option 1 — Single Availability Zone
- Lowest cost and complexity.
- Does not provide resilience against an Availability Zone failure.

### Option 2 — Two Availability Zones
- Provides fault isolation across Availability Zones.
- Allows the application architecture to continue operating if one AZ becomes unavailable.
- Introduces additional infrastructure and potential cross-AZ costs.
- Appropriate for Northstar's current availability requirements.

### Option 3 — Three Availability Zones
- Provides additional resilience and capacity distribution.
- Introduces additional cost and infrastructure complexity.
- Not currently justified by Northstar's scale and availability requirements.

## Decision

Northstar V2 will use **two Availability Zones within a single AWS Region**.

This provides an appropriate balance between availability, cost, and operational complexity.

## Consequences

- Networking must be designed across two AZs.
- Application resources can be distributed across both AZs.
- Database architecture can take advantage of Multi-AZ capabilities.
- Infrastructure cost and complexity will increase compared with V1.
- A regional failure is not addressed by this decision; multi-region disaster recovery is outside the current V2 scope.
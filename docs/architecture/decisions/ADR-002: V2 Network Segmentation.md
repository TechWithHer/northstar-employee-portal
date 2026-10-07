# ADR-002: V2 Network Segmentation

**Status:** Accepted  
**Date:** 2026-10-07

## Context

Northstar V1 places the application server in a public subnet and the database
server in a private subnet.

The V1 audit identified several limitations:

- The application server is directly internet-facing.
- SSH is exposed to the internet for deployment.
- The database EC2 instance receives an unnecessary public IPv4 address.
- Application and database tiers have different outbound connectivity requirements.
- The architecture contains single points of failure.

Northstar V2 requires clearer network boundaries while supporting the
two-Availability-Zone strategy defined in ADR-001.

## Decision

Northstar V2 will use one VPC with six subnets distributed across two
Availability Zones.

| Tier | AZ-1 | AZ-2 |
|---|---|---|
| Public | `10.0.1.0/24` | `10.0.2.0/24` |
| Private App | `10.0.11.0/24` | `10.0.12.0/24` |
| Private DB | `10.0.21.0/24` | `10.0.22.0/24` |

**VPC CIDR:** `10.0.0.0/16`

### Public Tier

The two public subnets will provide the network layer for internet-facing
resources such as the Application Load Balancer.

Both public subnets will share a public route table containing:

`0.0.0.0/0 → Internet Gateway`

### Private Application Tier

Application instances will run in the two private App subnets.

- Application instances will not receive public IPv4 addresses.
- Internet users will not communicate directly with application instances.
- Application traffic will enter through the public load-balancing layer.
- The outbound connectivity strategy for the application tier will be
  evaluated separately.

### Private Database Tier

Database resources will use the two private DB subnets.

- Database resources will not receive public IPv4 addresses.
- The database tier will not have a direct route to the Internet Gateway.
- Database access will be restricted to the application tier using appropriate
  Security Group rules.
- Database routing will remain separate from application-tier routing.

## Routing Strategy

Different tiers have different routing requirements.

Therefore:

- Public subnets will share a public route table.
- Private App subnets will use application-specific private routing.
- Private DB subnets will use database-specific private routing.

Separate Availability Zones do not automatically require separate route tables.
Route tables are separated when routing requirements differ.

## NAT Decision

A NAT Gateway will **not** be created automatically.

Private application instances may require controlled outbound connectivity for
operating-system updates, package repositories, AWS services, or external APIs.

The actual outbound requirements will be identified before deciding between
options such as NAT Gateway, VPC endpoints, or another suitable approach.

This avoids introducing infrastructure and recurring cost without a defined
requirement.

## Consequences

### Benefits

- Application instances are no longer directly exposed to the internet.
- Database resources remain isolated from direct internet access.
- Application and database tiers can have different routing policies.
- Resources can be distributed across two Availability Zones.
- The network structure provides clearer security and operational boundaries.

### Trade-offs

- Six subnets increase networking complexity compared with V1.
- Additional routing and security policies must be maintained.
- Private application outbound connectivity requires an additional design
  decision.
- Multi-AZ architecture may introduce additional infrastructure and
  cross-AZ traffic costs.
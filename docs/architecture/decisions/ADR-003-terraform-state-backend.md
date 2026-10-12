# ADR-003: Terraform Remote State Backend

**Status:** Accepted  
**Date:** 2026-10-08  
**Project:** Northstar Employee Records Portal — V2

## Context

Northstar V2 uses Terraform to provision and manage AWS infrastructure.

Terraform requires a state file to track the infrastructure it manages. Keeping state only on a developer's local machine introduces risks involving loss of state, inconsistent environments, and collaboration.

## Decision

Use an Amazon S3 backend for Northstar V2 Terraform state.

The S3 bucket will be created manually before initializing the main Terraform configuration, avoiding a bootstrap dependency.

The backend will use:

- S3 bucket versioning
- Encryption at rest
- Block Public Access
- Restricted IAM permissions
- Native S3 state locking, subject to Terraform version compatibility

The S3 bucket name and state object key will be finalized during backend implementation.

## Alternatives Considered

**1. Local state**

Simple and suitable for experiments, but less appropriate for shared infrastructure management.

**2. Manually bootstrapped S3 backend — Selected**

Straightforward setup with centralized state storage and fewer bootstrap components.

**3. Separate Terraform bootstrap configuration**

More automated and reproducible, but introduces an additional configuration to maintain.

## Consequences

**Benefits**

- Centralized state storage
- Recovery of previous state versions
- Improved support for collaboration
- Reduced reliance on a single developer's local machine

**Trade-offs**

- Initial manual setup
- IAM permissions and backend configuration must be maintained
- S3 storage and request charges may apply
- State must be protected because it can contain sensitive information

## Implementation Notes

- Do not commit Terraform state files or sensitive variable files to Git.
- Verify bucket security settings before backend initialization.
- Configure the S3 backend separately from the infrastructure resources.
- Validate state locking and backend initialization before provisioning infrastructure.

# Developer Guide

This document is for contributors and maintainers of the German load forecasting MLOps stack.

## Scope

The platform targets two outcomes:
- short-term German electricity load forecasting
- anomaly detection for abnormal consumption behavior

## Core Components

### Model Service
Responsibilities:
- load trained model artifacts
- expose inference endpoints
- execute request-time prediction logic

Typical tools: FastAPI, Flask, TorchServe, TensorFlow Serving, Triton.

### API Gateway
Responsibilities:
- route external requests to internal services
- enforce authentication and authorization
- apply rate limits and basic traffic protection
- provide centralized observability hooks

Typical tools: NGINX, Kong, Traefik, AWS API Gateway.

### Reverse Proxy
A reverse proxy forwards traffic to internal services and often handles TLS, buffering, and caching. It is not the same as a full API gateway.

### Load Balancer
Responsibilities:
- distribute traffic across service replicas
- remove unhealthy backends from rotation
- improve availability under load

Typical tools: NGINX, HAProxy, managed cloud balancers.

## Request Flow (Conceptual)

1. Client sends request.
2. Gateway validates credentials and policy.
3. Request is routed to the target service.
4. Service processes and responds.
5. Gateway/proxy returns response to client.

## Engineering Guidelines

- CI/CD: run tests and checks before deployment.
- Security: avoid hardcoded secrets; use env vars or a secret manager.
- Observability: expose health endpoints, metrics, and structured logs.
- Reliability: design for retries, timeouts, and graceful degradation.
- Documentation: keep setup/run/test instructions current.

## Common Pitfalls

- Over-engineering too early.
- Blurring responsibilities between gateway, proxy, and app service.
- Missing monitoring for data, models, and service health.
- Ignoring stateful concerns (sessions, cache invalidation, idempotency).

## SQL Layering Convention

Use data layers based on outputs, not script purpose.

```text
sql/
├── staging/
│   └── stg_german_load.sql
├── features/
│   └── fct_german_load.sql
├── marts/
│   └── german_load_api.sql
├── quality/
│   └── data_quality_checks.sql
└── playground.sql
```

Layer intent:
- staging: cleaned, standardized base tables
- features: model-ready feature sets
- marts: serving-oriented views/tables
- quality: data validation checks

## Reproducibility

- Track code in Git.
- Track large data/model artifacts with DVC.
- Pin runtime dependencies in environment files.
- Keep experiments and model versions traceable.

## Suggested Dev Checklist

1. Configure local environment and `.env`.
2. Start stack with Docker Compose.
3. Validate service health endpoints.
4. Run tests before opening a PR.
5. Update docs when behavior changes.

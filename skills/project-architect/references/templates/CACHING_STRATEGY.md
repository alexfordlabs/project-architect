---
template_name: CACHING_STRATEGY
generate_when: "decisions.scale >= \"growth\" OR decisions.caching.enabled == true"
required_decisions: []
optional_decisions:
  - caching.edge
  - caching.app_cache
  - caching.db_cache
  - caching.invalidation_strategy
depends_on: []
revision_triggers:
  - caching.edge
  - caching.app_cache
  - caching.db_cache
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Caching Strategy: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [Cache Layers](#cache-layers)
- [CDN Caching](#cdn-caching)
- [Application Cache](#application-cache)
- [🗄️ Database Query Cache](#database-query-cache)
- [Invalidation Strategy](#invalidation-strategy)
- [Cache-Warming](#cache-warming)
- [📊 Monitoring](#monitoring)
- [↻ Revision Log](#revision-log)

## Cache Layers
Overview of every cache layer in the stack (edge → app → DB → client) with the role each plays, the TTL class, and the owner of invalidation.

## CDN Caching
CDN provider (Cloudflare, Fastly, CloudFront, Vercel Edge), what's cached at the edge (static assets, HTML, API responses, images), cache keys, surrogate keys, and ESI/edge-functions usage.

## Application Cache
In-process (LRU/SWR), shared Redis/Valkey/Memcached, or platform cache (Vercel Cache, Cloudflare Cache API). Document hot keys, eviction policy, and serialization format.

## 🗄️ Database Query Cache
DB-level caching choices (Postgres prepared statements, MySQL query cache off, materialized views, pg_repack), connection-level pooled caches, ORM query cache configuration.

## Invalidation Strategy
TTL-only, event-driven (write → publish invalidation), tag-based (Cloudflare cache tags, Vercel cache tags), version/cache-buster, or hybrid. Document who owns the invalidation event and how races are handled.

## Cache-Warming
Pre-warm strategies (cron, build-time, on-deploy, request-driven), warm-cache deployment policy, cold-start mitigation.

## 📊 Monitoring
Hit-rate dashboards per layer, miss-cost dashboards, alerting thresholds, sampling for stampede/thundering-herd detection.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*

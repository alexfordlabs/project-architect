---
template_name: FILE_STORAGE
generate_when: "decisions.file_handling.enabled == true"
required_decisions:
  - file_storage.provider
optional_decisions:
  - file_storage.cdn
  - file_storage.processing
  - file_storage.access_control
depends_on: []
revision_triggers:
  - file_storage.provider
  - file_storage.cdn
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# File Storage: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🗄️ Storage Provider](#storage-provider)
- [🎨 Bucket / Container Layout](#bucket-container-layout)
- [Upload Flow](#upload-flow)
- [Access Control](#access-control)
- [Processing Pipeline](#processing-pipeline)
- [CDN & Caching](#cdn-caching)
- [Lifecycle Policies](#lifecycle-policies)
- [💰 Costs](#costs)
- [↻ Revision Log](#revision-log)

## 🗄️ Storage Provider
Chosen provider (S3, R2, GCS, Azure Blob, Supabase Storage, UploadThing) with rationale and region(s). Note egress pricing, S3-API compatibility, and lock-in considerations.

## 🎨 Bucket / Container Layout
Naming convention, environment separation (dev/staging/prod), prefix scheme (`tenant/<id>/...`), public vs private buckets, retention buckets.

## Upload Flow
Direct-to-bucket via presigned URLs vs proxied through the API, multipart strategy for large objects, client-side validation, virus/malware scanning.

## Access Control
Signed URL TTLs, per-object ACLs, bucket policies, IAM role separation for app vs admin, public-read justification, anti-hotlink rules.

## Processing Pipeline
If applicable: image resizing (imgproxy, Cloudflare Images, Vercel/Next Image), video transcoding (Mux, AWS MediaConvert), OCR/extraction, async vs on-the-fly with caching.

## CDN & Caching
CDN in front of storage (Cloudflare, CloudFront, Fastly), cache headers, signed-URL-friendly caching strategy, cache invalidation triggers.

## Lifecycle Policies
Archive tiers (S3 IA / Glacier, R2 Infrequent), automatic deletion rules, soft-delete vs hard-delete, legal hold considerations.

## 💰 Costs
Storage GB/mo, request pricing, egress, processing. Link to `COST_MODEL.md` for the full breakdown.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*

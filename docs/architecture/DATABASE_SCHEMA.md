# Database Schema — Logical Draft

Final persistence design belongs to Member 1 and must follow actual database choice and access patterns. This is not a production DynamoDB schema.

## Logical entities

### Field
`field_id`, optional `owner_id`, optional `name`, `geometry` or geometry reference, `crop_type`, `created_at`, `updated_at`.

### AnalysisJob
`job_id`, `field_id`, `status`, requested date range, requested language, `created_at`, `updated_at`, optional `error_code`, optional `result_reference`.

### AnalysisResult
`job_id`, `field_id`, observations, weather evidence, report, source metadata, processing version, `created_at`.

## Guidance
Store large raster files and map assets in object storage with references in the database. Store queryable job state and metadata in the chosen database. Define access control, retention, backups and deletion rules. Never store secrets in application records.

Member 1 must decide actual keys, indexes, access patterns, TTL, backups and permissions before implementation.

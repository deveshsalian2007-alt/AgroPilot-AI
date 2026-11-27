# API Contract — Draft for Team Agreement

This is a proposal. Members 1–4 must agree routes, fields, units, statuses and error handling before depending on it.

## Principles
JSON over HTTPS; consistent field naming; timestamps and units; no secrets in frontend; use job IDs for long-running imagery work.

## Create analysis
`POST /api/analyze`

Illustrative request (replace empty coordinates with a valid GeoJSON polygon):
```json
{
  "field": {"type": "Polygon", "coordinates": []},
  "crop": "paddy",
  "date_range": {"start": "2026-10-01", "end": "2026-11-01"},
  "language": "en"
}
```
Illustrative response:
```json
{"job_id":"example-job-id","status":"QUEUED"}
```

## Job status
`GET /api/analyze/{job_id}`

```json
{
  "job_id":"example-job-id",
  "status":"PROCESSING",
  "stage":"GEOSPATIAL_ANALYSIS",
  "updated_at":"2026-11-27T00:00:00Z"
}
```
Suggested statuses: `QUEUED`, `PROCESSING`, `COMPLETED`, `PARTIAL`, `FAILED`. Define progress only if it can be measured reliably.

## Result
`GET /api/results/{job_id}`

```json
{
  "job_id":"example-job-id",
  "status":"COMPLETED",
  "observations":[],
  "weather":{"status":"UNAVAILABLE","provider":null,"metrics":{}},
  "report":{
    "language":"en",
    "summary":"",
    "findings":[],
    "confidence":"LOW",
    "limitations":[]
  },
  "sources":[]
}
```

## Proposed geospatial-to-agent evidence shape
```json
{
  "job_id":"example-job-id",
  "imagery_quality":{"status":"USABLE","valid_pixel_percent":null,"limitations":[]},
  "ndvi":{
    "observations":[
      {"date":"2026-10-10","mean":null,"median":null,"source_id":"example-source"}
    ],
    "change":{"absolute":null,"percent":null,"method":null}
  },
  "flood_analysis":{"status":"NOT_ANALYSED","indicator":null,"method":null,"limitations":[]},
  "weather":{"status":"UNAVAILABLE","provider":null,"rainfall_mm":null},
  "provenance":{"generated_at":"2026-11-27T00:00:00Z","processing_version":null,"sources":[]}
}
```
All values are illustrative placeholders. `null` means unavailable/not calculated, not zero. Member 2 and 3 must agree units, dates, aggregation, quality flags and null semantics.

## Error shape
```json
{"error":{"code":"INVALID_FIELD_GEOMETRY","message":"The field boundary is invalid.","details":[]}}
```

## Team decisions required
Exact routes/versioning; polygon limits; coordinate/date conventions; job states; evidence schema; agent invocation method; authentication; result and map-layer storage.

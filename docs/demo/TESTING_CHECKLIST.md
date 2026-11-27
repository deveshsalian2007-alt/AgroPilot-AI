# Testing Checklist

## API/input
- [ ] Valid polygon accepted; invalid geometry rejected.
- [ ] Invalid crop/date/language handled.
- [ ] Job ID and status work.
- [ ] Unknown job returns safe error.

## Geospatial
- [ ] Source and observation dates recorded.
- [ ] Cloud/no-data masking tested.
- [ ] NDVI tested against known example.
- [ ] Aggregation method and units documented.
- [ ] Missing imagery yields inconclusive status.
- [ ] Inundation result includes method and limitations.

## AI
- [ ] Report uses only supplied evidence.
- [ ] Missing values remain unavailable, not zero.
- [ ] Dates, confidence and limitations included.
- [ ] No disease diagnosis or pesticide prescription.
- [ ] LLM failure triggers fallback.
- [ ] English/Tamil meaning reviewed.

## Integration/cloud
- [ ] Frontend creates job and retrieves result.
- [ ] Backend handles timeouts and module failures.
- [ ] No secrets in repository or client bundle.
- [ ] Logs do not expose secrets.
- [ ] AWS budgets/monitoring enabled.
- [ ] Demo is repeatable.

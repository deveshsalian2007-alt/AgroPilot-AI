# Known Issues and Risks

These are items to verify, not necessarily confirmed software bugs.

| Item | Type | Status | Next action |
|---|---|---|---|
| Actual code maturity in each module not inspected | Verification | OPEN | Inspect source and tests |
| API contract needs agreement | Integration | OPEN | Team review |
| Satellite data may be cloudy/stale/unavailable | Data risk | OPEN | Verify scenes for demo area/dates |
| Sentinel-1 inundation interpretation needs validation | Technical risk | OPEN | Agree method and caveats |
| Bedrock access/model/quota/cost not verified | Dependency | OPEN | Test access and fallback |
| Heavy raster processing may not suit one synchronous request/Lambda | Architecture | OPEN | Select suitable worker design |
| AWS permissions and costs need controls | Cloud risk | OPEN | Least privilege, budget and monitoring |

# Technology Stack — Proposed

Confirm actual choices with module owners before installing packages.

| Layer | Candidate | Owner/confirmation |
|---|---|---|
| Frontend | React, Tailwind, Leaflet | Member 4 |
| Backend | API framework/runtime TBD | Member 1 |
| Geospatial | Python and satellite processing libraries | Member 2 |
| AI agents | Python, Bedrock adapter if available, deterministic fallback | Member 3 |
| Weather | Open-Meteo candidate | Members 1 and 3 |
| Cloud | S3, DynamoDB, API Gateway, Lambda candidates | Member 1 |
| Docs | Markdown and Mermaid | All |

Inspect existing dependency files before adding packages. Coordinate root `requirements.txt` changes. Keep secrets out of source and frontend bundles.

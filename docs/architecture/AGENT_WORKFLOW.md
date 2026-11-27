# AI Agent Workflow

## Proposed stages
1. Input validator: check required fields, types, dates, units and missing values.
2. Evidence normaliser: map agreed module output into the internal schema without changing meaning.
3. Weather tool: consume approved weather data or retrieve it through the agreed provider.
4. Orchestrator: decide which reporting steps are possible from available evidence.
5. Reporter: generate concise plain-language report in a supported language.
6. Output validator: check required sections, numeric consistency and safe wording.
7. Fallback: deterministic templates if LLM is unavailable or fails validation.

## Rules
- Geospatial calculations are deterministic, not LLM-generated.
- Reporter may only use numbers present in validated evidence.
- Missing values stay missing.
- State observation dates, confidence and limitations.
- Separate measured indicators from possible explanations.
- Never diagnose disease or prescribe treatments.
- If evidence is insufficient, say so.

## Model integration
Bedrock is a candidate, not an assumed working dependency. Verify access, model availability, region, permissions, quotas and cost. Keep provider calls behind an interface and implement a deterministic fallback.

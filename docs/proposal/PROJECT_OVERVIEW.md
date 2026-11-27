# AgroPilot AI — Project Overview

## Description
A satellite-based crop-risk advisor for small Indian farms. A farmer selects/draws a field, chooses a crop and requests an analysis. The platform uses suitable satellite observations and weather context to create a plain-language, evidence-based report.

## Problem
Small farmers may lack timely, field-specific information about vegetation changes or possible waterlogging, and technical dashboards can be difficult to interpret.

## Proposed MVP flow
1. Farmer draws/selects a field polygon.
2. Selects crop, analysis period and report language.
3. Backend validates input and creates an analysis job.
4. Geospatial module finds suitable satellite observations and calculates indicators.
5. Weather context is retrieved where available.
6. AI reporter explains only validated evidence.
7. Frontend displays report, metrics, observation dates, quality and limitations.

## Candidate MVP features
- Field boundary input and validation.
- Sentinel-2 vegetation indicator such as NDVI, where usable observations exist.
- Comparison across available dates.
- Transparent unusual-change flags.
- Sentinel-1 potential inundation indicator only if validated.
- Recent weather/rainfall context.
- English and a selected regional language (Tamil is a candidate).
- Clear confidence and data limitations.

## Out of scope initially
Confirmed disease diagnosis, pesticide prescriptions, guaranteed yield prediction, marketplace/social network, native mobile app, and custom deep-learning detection unless separately justified.

## Product language
Say "vegetation indicator changed" or "possible waterlogging signal", not "crop is diseased". State when data is insufficient.

## Provisional stack
React frontend; backend framework to be confirmed by Member 1; Python geospatial processing; Python AI module; Open-Meteo candidate for weather; AWS services such as S3, DynamoDB, API Gateway and Lambda as candidates. Verify actual repo choices, access, limits and cost before implementation.

## Decisions still needed
Initial district/crop/date range, satellite access method, weather provider, backend framework, job/worker design, AWS deployment approach, Bedrock access and supported language.

"""Deterministic farmer-friendly report generator (English and Tamil).

Guarantees:
- Uses only numbers present in validated GeospatialEvidence.
- Never converts None/missing values to 0.
- Explicitly separates measured observations from possible interpretations.
- Never diagnoses crop diseases or prescribes pesticides/fertilisers.
- Reports inconclusive results honestly when imagery is cloudy, stale, or missing.
"""

from __future__ import annotations

from typing import Optional

from schemas.evidence import (
    ConfidenceLevel,
    FarmerReport,
    FloodStatus,
    GeospatialEvidence,
    ImageryStatus,
    Language,
    NdviObservation,
    ReportFinding,
    WeatherStatus,
)

DISCLAIMERS_EN = [
    "This advisory is based on satellite and weather indicators only and is not a confirmed disease diagnosis.",
    "Do not apply pesticides, fertilisers, or chemical treatments based solely on this report; consult a local agricultural officer or inspect the field directly.",
]

DISCLAIMERS_TA = [
    "இந்த அறிக்கை செயற்கைக்கோள் மற்றும் வானிலை குறிகாட்டிகளின் அடிப்படையில் மட்டுமே உருவாக்கப்பட்டது; இது உறுதிப்படுத்தப்பட்ட நோய் கண்டறிதல் அல்ல.",
    "இந்த அறிக்கையின் அடிப்படையில் மட்டும் பூச்சிக்கொல்லி, உரம் அல்லது ரசாயன மருந்துகளைப் பயன்படுத்த வேண்டாம்; வயலை நேரில் ஆய்வு செய்து உள்ளூர் வேளாண் அலுவலரை அணுகவும்.",
]


def _fmt_num(value: Optional[float]) -> str:
    if value is None:
        return "unavailable"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


def _fmt_num_ta(value: Optional[float]) -> str:
    if value is None:
        return "கிடைக்கவில்லை"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


def compute_confidence(evidence: GeospatialEvidence) -> ConfidenceLevel:
    """Deterministically assess report confidence from imagery quality and observations."""
    img_status = evidence.imagery_quality.status
    valid_ndvi = [
        obs for obs in evidence.ndvi.observations if obs.mean is not None or obs.median is not None
    ]

    if img_status == ImageryStatus.UNAVAILABLE or len(valid_ndvi) == 0:
        return ConfidenceLevel.INSUFFICIENT

    if img_status in {ImageryStatus.CLOUDY, ImageryStatus.STALE}:
        return ConfidenceLevel.LOW

    valid_pct = evidence.imagery_quality.valid_pixel_percent
    if valid_pct is not None and valid_pct < 50.0:
        return ConfidenceLevel.LOW

    if len(valid_ndvi) >= 2 and (valid_pct is None or valid_pct >= 70.0):
        if evidence.weather.status == WeatherStatus.AVAILABLE:
            return ConfidenceLevel.HIGH
        return ConfidenceLevel.MEDIUM

    return ConfidenceLevel.MEDIUM


def _collect_limitations(evidence: GeospatialEvidence, lang: Language) -> list[str]:
    limitations: list[str] = []
    limitations.extend(evidence.imagery_quality.limitations)
    limitations.extend(evidence.flood_analysis.limitations)
    limitations.extend(evidence.weather.limitations)

    if evidence.imagery_quality.status in {
        ImageryStatus.CLOUDY,
        ImageryStatus.STALE,
        ImageryStatus.UNAVAILABLE,
    }:
        msg = (
            f"Satellite imagery status is {evidence.imagery_quality.status.value}; results may be incomplete."
            if lang == Language.EN
            else f"செயற்கைக்கோள் படத்தின் நிலை {evidence.imagery_quality.status.value} ஆகும்; முடிவுகள் முழுமையற்றதாக இருக்கலாம்."
        )
        limitations.append(msg)

    if evidence.weather.status == WeatherStatus.UNAVAILABLE:
        msg = (
            "Weather data was unavailable for this analysis."
            if lang == Language.EN
            else "இந்த ஆய்விற்கு வானிலை தரவு கிடைக்கவில்லை."
        )
        limitations.append(msg)

    if not evidence.ndvi.observations:
        msg = (
            "No NDVI observations were available in the selected period."
            if lang == Language.EN
            else "தேர்ந்தெடுக்கப்பட்ட காலத்தில் NDVI அளவீடுகள் எதுவும் கிடைக்கவில்லை."
        )
        limitations.append(msg)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for item in limitations:
        if item and item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def _latest_valid_ndvi(observations: list[NdviObservation]) -> Optional[NdviObservation]:
    for obs in reversed(observations):
        if obs.mean is not None or obs.median is not None:
            return obs
    return None


def _build_en_report(evidence: GeospatialEvidence, confidence: ConfidenceLevel) -> FarmerReport:
    findings: list[ReportFinding] = []
    latest = _latest_valid_ndvi(evidence.ndvi.observations)
    crop_label = evidence.crop if evidence.crop else "selected crop"

    # Imagery quality finding
    valid_pct_text = (
        f"valid pixel coverage {_fmt_num(evidence.imagery_quality.valid_pixel_percent)}%"
        if evidence.imagery_quality.valid_pixel_percent is not None
        else "valid pixel coverage unavailable"
    )
    findings.append(
        ReportFinding(
            indicator="imagery_quality",
            observation=f"Satellite imagery status is {evidence.imagery_quality.status.value} ({valid_pct_text}).",
            interpretation=(
                "Observations are usable for general vegetation monitoring."
                if evidence.imagery_quality.status == ImageryStatus.USABLE
                else "Cloud cover, stale timing, or missing imagery limits what can be concluded from satellite data."
            ),
        )
    )

    # NDVI finding
    if latest is not None:
        parts = []
        if latest.mean is not None:
            parts.append(f"mean NDVI {_fmt_num(latest.mean)}")
        if latest.median is not None:
            parts.append(f"median NDVI {_fmt_num(latest.median)}")
        obs_text = f"Latest NDVI on {latest.date}: " + ", ".join(parts) + "."
        if evidence.ndvi.change is not None and (
            evidence.ndvi.change.absolute is not None or evidence.ndvi.change.percent is not None
        ):
            change_parts = []
            if evidence.ndvi.change.absolute is not None:
                change_parts.append(f"absolute change {_fmt_num(evidence.ndvi.change.absolute)}")
            if evidence.ndvi.change.percent is not None:
                change_parts.append(f"percent change {_fmt_num(evidence.ndvi.change.percent)}%")
            obs_text += " Period change: " + ", ".join(change_parts) + "."

        if evidence.ndvi.change is not None and evidence.ndvi.change.absolute is not None:
            if evidence.ndvi.change.absolute < -0.05:
                interp_text = (
                    f"Greenness declined over the period for the {crop_label}; this may reflect crop stress, "
                    "harvesting, cloud artefacts, or moisture changes. Field inspection is recommended."
                )
            elif evidence.ndvi.change.absolute > 0.05:
                interp_text = (
                    f"Greenness increased over the period for the {crop_label}, consistent with active vegetation growth."
                )
            else:
                interp_text = (
                    f"Greenness remained relatively stable for the {crop_label} over the observed dates."
                )
        else:
            interp_text = (
                "Single-date or incomplete NDVI data shows current vegetation greenness, but trend direction cannot be confirmed."
            )

        findings.append(
            ReportFinding(
                indicator="ndvi",
                observation=obs_text,
                interpretation=interp_text,
                observation_date=latest.date,
            )
        )
    else:
        findings.append(
            ReportFinding(
                indicator="ndvi",
                observation="No valid NDVI values were measured.",
                interpretation="Vegetation condition cannot be assessed from satellite imagery at this time.",
            )
        )

    # Flood analysis finding
    if evidence.flood_analysis.status != FloodStatus.NOT_ANALYSED:
        ind_text = (
            f" (indicator {_fmt_num(evidence.flood_analysis.indicator)})"
            if evidence.flood_analysis.indicator is not None
            else ""
        )
        findings.append(
            ReportFinding(
                indicator="flood_analysis",
                observation=f"Surface water / flood screening status: {evidence.flood_analysis.status.value}{ind_text}.",
                interpretation=(
                    "Possible standing water or wet surface conditions were screened; verify drainage conditions on the ground."
                    if evidence.flood_analysis.status in {FloodStatus.MODERATE, FloodStatus.HIGH}
                    else "Flood screening did not show strong standing-water signals, though local wet patches remain possible."
                ),
            )
        )

    # Weather finding
    wx = evidence.weather
    hist_parts: list[str] = []
    if wx.rainfall_mm is not None:
        hist_parts.append(f"rainfall {_fmt_num(wx.rainfall_mm)} mm")
    if wx.temperature_c_mean is not None:
        hist_parts.append(f"mean temperature {_fmt_num(wx.temperature_c_mean)} C")
    if wx.humidity_percent_mean is not None:
        hist_parts.append(f"mean humidity {_fmt_num(wx.humidity_percent_mean)}%")

    fc_parts: list[str] = []
    if wx.forecast_rainfall_mm is not None:
        fc_parts.append(f"forecast rainfall {_fmt_num(wx.forecast_rainfall_mm)} mm")
    if wx.forecast_temperature_c_mean is not None:
        fc_parts.append(f"forecast mean temperature {_fmt_num(wx.forecast_temperature_c_mean)} C")
    if wx.forecast_humidity_percent_mean is not None:
        fc_parts.append(f"forecast mean humidity {_fmt_num(wx.forecast_humidity_percent_mean)}%")

    if wx.status != WeatherStatus.UNAVAILABLE and (hist_parts or fc_parts):
        provider_note = f" (source: {wx.provider})" if wx.provider else ""
        sections: list[str] = []
        if hist_parts:
            period_note = (
                f" ({wx.period_start} to {wx.period_end})"
                if wx.period_start and wx.period_end
                else ""
            )
            sections.append(f"Historical observed weather{period_note}: " + ", ".join(hist_parts))
        else:
            sections.append("Historical observed weather: unavailable")

        if fc_parts:
            days_note = f" (next {_fmt_num(float(wx.forecast_days))} days)" if wx.forecast_days is not None else ""
            sections.append(f"Weather forecast{days_note}: " + ", ".join(fc_parts))
        elif wx.status == WeatherStatus.PARTIAL:
            sections.append("Weather forecast: unavailable")

        interp_parts = [
            "Historical weather observations and upcoming forecasts are reported separately."
        ]
        if wx.status == WeatherStatus.PARTIAL:
            interp_parts.append("Some weather data is missing, so weather context is incomplete.")
        interp_parts.append(
            "Weather indicators alone do not confirm crop damage; consider rainfall, temperature, "
            "and humidity alongside field drainage, irrigation, and direct crop inspection."
        )

        findings.append(
            ReportFinding(
                indicator="weather",
                observation="; ".join(sections) + f"{provider_note}.",
                interpretation=" ".join(interp_parts),
                observation_date=wx.retrieved_at,
            )
        )
    else:
        findings.append(
            ReportFinding(
                indicator="weather",
                observation="Weather rainfall, temperature, and humidity data are unavailable.",
                interpretation="Recent and upcoming weather effects cannot be confirmed from weather records.",
            )
        )

    if confidence == ConfidenceLevel.INSUFFICIENT:
        summary = (
            f"Inconclusive satellite advisory for {crop_label}: usable satellite NDVI observations were not available."
        )
    elif confidence == ConfidenceLevel.LOW:
        summary = (
            f"Low-confidence satellite advisory for {crop_label} due to imagery quality or data limitations. "
            "Check the field directly before making management decisions."
        )
    else:
        summary = (
            f"Satellite vegetation and context summary for {crop_label} (confidence: {confidence.value}). "
            "Review measured indicators and field conditions carefully."
        )

    return FarmerReport(
        language=Language.EN.value,
        summary=summary,
        findings=findings,
        confidence=confidence.value,
        limitations=_collect_limitations(evidence, Language.EN),
        generation_mode="deterministic",
        disclaimers=list(DISCLAIMERS_EN),
    )


def _build_ta_report(evidence: GeospatialEvidence, confidence: ConfidenceLevel) -> FarmerReport:
    findings: list[ReportFinding] = []
    latest = _latest_valid_ndvi(evidence.ndvi.observations)
    crop_label = evidence.crop if evidence.crop else "தேர்ந்தெடுக்கப்பட்ட பயிர்"

    valid_pct_text = (
        f"செல்லுபடியாகும் பிக்சல் அளவு {_fmt_num_ta(evidence.imagery_quality.valid_pixel_percent)}%"
        if evidence.imagery_quality.valid_pixel_percent is not None
        else "செல்லுபடியாகும் பிக்சல் அளவு கிடைக்கவில்லை"
    )
    findings.append(
        ReportFinding(
            indicator="imagery_quality",
            observation=f"செயற்கைக்கோள் பட நிலை: {evidence.imagery_quality.status.value} ({valid_pct_text}).",
            interpretation=(
                "பொதுவான பயிர் பசுமை கண்காணிப்பிற்கு படம் பயன்படக்கூடியதாக உள்ளது."
                if evidence.imagery_quality.status == ImageryStatus.USABLE
                else "மேக மூட்டம், பழைய படம் அல்லது தரவு இல்லாமை காரணமாக முடிவுகள் வரம்பிற்குட்பட்டவை."
            ),
        )
    )

    if latest is not None:
        parts = []
        if latest.mean is not None:
            parts.append(f"சராசரி NDVI {_fmt_num_ta(latest.mean)}")
        if latest.median is not None:
            parts.append(f"நடுநிலை NDVI {_fmt_num_ta(latest.median)}")
        obs_text = f"{latest.date} அன்று NDVI அளவீடு: " + ", ".join(parts) + "."
        if evidence.ndvi.change is not None and (
            evidence.ndvi.change.absolute is not None or evidence.ndvi.change.percent is not None
        ):
            change_parts = []
            if evidence.ndvi.change.absolute is not None:
                change_parts.append(f"மாற்றம் {_fmt_num_ta(evidence.ndvi.change.absolute)}")
            if evidence.ndvi.change.percent is not None:
                change_parts.append(f"சதவீத மாற்றம் {_fmt_num_ta(evidence.ndvi.change.percent)}%")
            obs_text += " கால மாற்றம்: " + ", ".join(change_parts) + "."

        if evidence.ndvi.change is not None and evidence.ndvi.change.absolute is not None:
            if evidence.ndvi.change.absolute < -0.05:
                interp_text = (
                    f"{crop_label} பசுமை அளவு குறைந்துள்ளது; இது பயிர் அழுத்தம், அறுவடை அல்லது ஈரப்பத மாற்றத்தால் இருக்கலாம். வயலை நேரில் பார்க்கவும்."
                )
            elif evidence.ndvi.change.absolute > 0.05:
                interp_text = f"{crop_label} பசுமை அளவு அதிகரித்துள்ளது; இது பயிர் வளர்ச்சியைக் காட்டலாம்."
            else:
                interp_text = f"{crop_label} பசுமை அளவு கடந்த நாட்களில் நிலையாக உள்ளது."
        else:
            interp_text = "ஒரு நாள் அல்லது முழுமையற்ற NDVI தரவு மட்டுமே உள்ளதால் மாற்றத்தின் போக்கை உறுதிப்படுத்த முடியாது."

        findings.append(
            ReportFinding(
                indicator="ndvi",
                observation=obs_text,
                interpretation=interp_text,
                observation_date=latest.date,
            )
        )
    else:
        findings.append(
            ReportFinding(
                indicator="ndvi",
                observation="செல்லுபடியாகும் NDVI அளவீடுகள் கிடைக்கவில்லை.",
                interpretation="செயற்கைக்கோள் தரவிலிருந்து பயிர் நிலையை தற்போது மதிப்பிட முடியவில்லை.",
            )
        )

    if evidence.flood_analysis.status != FloodStatus.NOT_ANALYSED:
        ind_text = (
            f" (குறிகாட்டி {_fmt_num_ta(evidence.flood_analysis.indicator)})"
            if evidence.flood_analysis.indicator is not None
            else ""
        )
        findings.append(
            ReportFinding(
                indicator="flood_analysis",
                observation=f"நீர் தேக்க / வெள்ள ஆய்வு நிலை: {evidence.flood_analysis.status.value}{ind_text}.",
                interpretation=(
                    "வயலில் நீர் தேங்கும் சாத்தியம் உள்ளதால் வடிகால் நிலையை நேரில் சரிபார்க்கவும்."
                    if evidence.flood_analysis.status in {FloodStatus.MODERATE, FloodStatus.HIGH}
                    else "பெரிய அளவிலான நீர் தேக்க அறிகுறி தெரியவில்லை; எனினும் உள்ளூர் ஈரப்பதத்தைச் சரிபார்க்கவும்."
                ),
            )
        )

    wx = evidence.weather
    ta_hist_parts: list[str] = []
    if wx.rainfall_mm is not None:
        ta_hist_parts.append(f"மழை {_fmt_num_ta(wx.rainfall_mm)} mm")
    if wx.temperature_c_mean is not None:
        ta_hist_parts.append(f"சராசரி வெப்பநிலை {_fmt_num_ta(wx.temperature_c_mean)} C")
    if wx.humidity_percent_mean is not None:
        ta_hist_parts.append(f"சராசரி ஈரப்பதம் {_fmt_num_ta(wx.humidity_percent_mean)}%")

    ta_fc_parts: list[str] = []
    if wx.forecast_rainfall_mm is not None:
        ta_fc_parts.append(f"மழை முன்னறிவிப்பு {_fmt_num_ta(wx.forecast_rainfall_mm)} mm")
    if wx.forecast_temperature_c_mean is not None:
        ta_fc_parts.append(f"வெப்பநிலை முன்னறிவிப்பு {_fmt_num_ta(wx.forecast_temperature_c_mean)} C")
    if wx.forecast_humidity_percent_mean is not None:
        ta_fc_parts.append(f"ஈரப்பதம் முன்னறிவிப்பு {_fmt_num_ta(wx.forecast_humidity_percent_mean)}%")

    if wx.status != WeatherStatus.UNAVAILABLE and (ta_hist_parts or ta_fc_parts):
        ta_sections: list[str] = []
        if ta_hist_parts:
            ta_sections.append("கடந்த கால வானிலை: " + ", ".join(ta_hist_parts))
        else:
            ta_sections.append("கடந்த கால வானிலை: கிடைக்கவில்லை")

        if ta_fc_parts:
            ta_sections.append("வானிலை முன்னறிவிப்பு: " + ", ".join(ta_fc_parts))
        elif wx.status == WeatherStatus.PARTIAL:
            ta_sections.append("வானிலை முன்னறிவிப்பு: கிடைக்கவில்லை")

        ta_interp = (
            "கடந்த கால வானிலையும் வரவிருக்கும் முன்னறிவிப்பும் தனித்தனியாகக் காட்டப்பட்டுள்ளன. "
            "வானிலை தரவு மட்டும் பயிர் சேதத்தை உறுதிப்படுத்தாது; மழை, வெப்பநிலை மற்றும் ஈரப்பதத்தை "
            "வயலின் வடிகால், நீர்ப்பாசனம் மற்றும் நேரடி வயல் ஆய்வுடன் சேர்த்துப் பார்க்கவும்."
        )
        if wx.status == WeatherStatus.PARTIAL:
            ta_interp += " சில வானிலை தரவுகள் முழுமையாகக் கிடைக்கவில்லை."

        findings.append(
            ReportFinding(
                indicator="weather",
                observation="; ".join(ta_sections) + ".",
                interpretation=ta_interp,
                observation_date=wx.retrieved_at,
            )
        )
    else:
        findings.append(
            ReportFinding(
                indicator="weather",
                observation="வானிலை மழை, வெப்பநிலை மற்றும் ஈரப்பதத் தரவு கிடைக்கவில்லை.",
                interpretation="சமீபத்திய மற்றும் வரவிருக்கும் வானிலை தாக்கத்தை வானிலை தரவிலிருந்து உறுதிப்படுத்த முடியவில்லை.",
            )
        )

    if confidence == ConfidenceLevel.INSUFFICIENT:
        summary = f"{crop_label} பற்றிய செயற்கைக்கோள் அறிக்கை: போதுமான NDVI தரவு இல்லாததால் முடிவு எடுக்க முடியவில்லை."
    elif confidence == ConfidenceLevel.LOW:
        summary = (
            f"{crop_label} பற்றிய குறைந்த நம்பகத்தன்மை அறிக்கை: படத்தின் தரம் அல்லது தரவு வரம்புகள் உள்ளன. வயலை நேரில் ஆய்வு செய்யவும்."
        )
    else:
        summary = (
            f"{crop_label} பற்றிய செயற்கைக்கோள் மற்றும் வானிலை சுருக்கம் (நம்பகத்தன்மை: {confidence.value})."
        )

    return FarmerReport(
        language=Language.TA.value,
        summary=summary,
        findings=findings,
        confidence=confidence.value,
        limitations=_collect_limitations(evidence, Language.TA),
        generation_mode="deterministic",
        disclaimers=list(DISCLAIMERS_TA),
    )


def generate_deterministic_report(evidence: GeospatialEvidence) -> FarmerReport:
    """Generate an evidence-grounded report in English or Tamil without an LLM."""
    confidence = compute_confidence(evidence)
    if evidence.language == Language.TA:
        return _build_ta_report(evidence, confidence)
    return _build_en_report(evidence, confidence)

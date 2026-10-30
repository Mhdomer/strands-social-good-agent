"""Environmental and heat-stress assessment tools for Nafas (نَفَس).

Calculates Wet-Bulb Globe Temperature (WBGT), OSHA work-rest schedules,
hydration requirements, and particulate air quality indices (PM2.5/PM10).
"""

import math
from typing import Any
from strands import tool
from nafas.config import WBGTThresholds


def calculate_wet_bulb_temperature(temperature_c: float, relative_humidity: float) -> float:
    """Calculate approximate Wet-Bulb Temperature using Stull's formula.

    Valid for relative humidity between 5% and 99% and temperatures between -20C and 50C.
    """
    t = temperature_c
    rh = max(0.1, min(100.0, relative_humidity))
    
    tw = (
        t * math.atan(0.151977 * math.sqrt(rh + 8.313659))
        + math.atan(t + rh)
        - math.atan(rh - 1.676331)
        + 0.00391838 * (rh ** 1.5) * math.atan(0.023101 * rh)
        - 4.686035
    )
    return round(tw, 2)


def calculate_wbgt(
    temperature_c: float,
    relative_humidity: float,
    direct_sunlight: bool = True,
) -> float:
    """Calculate Wet-Bulb Globe Temperature (WBGT) in Celsius.

    In direct sunlight: approximated as 0.7 * Tw + 0.2 * Tg + 0.1 * Ta,
    where globe temperature Tg is estimated from solar radiation and air temperature.
    In shade/indoors: approximated as 0.7 * Tw + 0.3 * Ta.
    """
    tw = calculate_wet_bulb_temperature(temperature_c, relative_humidity)
    ta = temperature_c

    if direct_sunlight:
        # Solar radiation adjustment in high-sun arid climates (adds ~10C to 14C to globe temp)
        tg = ta + 12.0
        wbgt = 0.7 * tw + 0.2 * tg + 0.1 * ta
    else:
        wbgt = 0.7 * tw + 0.3 * ta

    return round(wbgt, 2)


def evaluate_heat_stress(wbgt_c: float) -> dict[str, Any]:
    """Evaluate heat stress risk tier and determine OSHA work-rest and hydration requirements."""
    if wbgt_c < WBGTThresholds.LOW_RISK_MAX:
        return {
            "tier": "LOW",
            "risk_label": "Low Risk",
            "work_rest_cycle": "Continuous work permitted (standard 60 min work / 0 min rest)",
            "hydration_liters_per_hour": 0.25,
            "caution": "Stay hydrated and monitor vulnerable co-workers.",
            "work_ban_active": False,
        }
    elif wbgt_c <= WBGTThresholds.MODERATE_RISK_MAX:
        return {
            "tier": "MODERATE",
            "risk_label": "Moderate Heat Stress",
            "work_rest_cycle": "45 minutes work / 15 minutes rest per hour in shade",
            "hydration_liters_per_hour": 0.5,
            "caution": "Drink water every 15 to 20 minutes even if not thirsty.",
            "work_ban_active": False,
        }
    elif wbgt_c <= WBGTThresholds.HIGH_RISK_MAX:
        return {
            "tier": "HIGH",
            "risk_label": "High Heat Stress Hazard",
            "work_rest_cycle": "30 minutes work / 30 minutes rest per hour in air-conditioned or shaded area",
            "hydration_liters_per_hour": 0.75,
            "caution": "High risk of heat exhaustion and heat cramps. Mandatory buddy-system monitoring.",
            "work_ban_active": False,
        }
    elif wbgt_c <= WBGTThresholds.VERY_HIGH_RISK_MAX:
        return {
            "tier": "VERY_HIGH",
            "risk_label": "Very High Heat Stress Danger",
            "work_rest_cycle": "15 minutes work / 45 minutes rest per hour in shaded cooling area",
            "hydration_liters_per_hour": 1.0,
            "caution": "Severe risk of heat stroke. Heavy outdoor manual labor should be curtailed.",
            "work_ban_active": False,
        }
    else:
        return {
            "tier": "EXTREME",
            "risk_label": "Extreme Lethal Heat Danger",
            "work_rest_cycle": "STOP all outdoor manual labor immediately. Move to climate-controlled shelters.",
            "hydration_liters_per_hour": 1.0,
            "caution": "Life-threatening conditions. Risk of rapid heatstroke, delirium, and circulatory collapse.",
            "work_ban_active": True,
        }


def evaluate_air_quality(pm25: float, pm10: float) -> dict[str, Any]:
    """Evaluate particulate matter levels and generate respiratory guidance."""
    # WHO 24-hour guidelines: PM2.5 > 15 ug/m3, PM10 > 45 ug/m3
    # EPA breakpoints: PM2.5 > 35 ug/m3 Unhealthy for sensitive groups, > 55 Unhealthy, > 150 Hazardous
    dust_storm = pm10 >= 250.0 or pm25 >= 150.0

    if pm25 > 150.0 or pm10 > 300.0:
        category = "HAZARDOUS"
        health_advisory = "Hazardous dust storm or acute particulate pollution. Asthmatics and COPD patients must remain indoors with sealed windows and doors."
        mask_recommendation = "N95 or FFP2 respirator mandatory if going outdoors."
    elif pm25 > 55.0 or pm10 > 150.0:
        category = "UNHEALTHY"
        health_advisory = "High particulate pollution. Children, elderly, and individuals with respiratory disease must avoid outdoor exertion."
        mask_recommendation = "Well-fitted N95 mask strongly advised for outdoor workers."
    elif pm25 > 35.0 or pm10 > 100.0:
        category = "UNHEALTHY_FOR_SENSITIVE"
        health_advisory = "Elevated dust and particulates. Asthmatic patients should keep rescue inhalers within reach."
        mask_recommendation = "Mask recommended during extended outdoor exposure."
    elif pm25 > 15.0 or pm10 > 50.0:
        category = "MODERATE"
        health_advisory = "Acceptable air quality for general population. Sensitive individuals may experience mild throat or eye irritation."
        mask_recommendation = "Standard hygiene precautions."
    else:
        category = "GOOD"
        health_advisory = "Air quality is satisfactory and poses little or no respiratory risk."
        mask_recommendation = "None required."

    return {
        "category": category,
        "pm25": pm25,
        "pm10": pm10,
        "is_dust_storm": dust_storm,
        "health_advisory": health_advisory,
        "mask_recommendation": mask_recommendation,
    }


# Representative climate and particulate presets for key Middle Eastern cities
CITY_CLIMATE_PRESETS: dict[str, dict[str, float]] = {
    "riyadh": {"temp_c": 46.5, "humidity": 14.0, "pm25": 145.0, "pm10": 320.0},
    "cairo": {"temp_c": 39.0, "humidity": 45.0, "pm25": 85.0, "pm10": 190.0},
    "jeddah": {"temp_c": 41.0, "humidity": 65.0, "pm25": 48.0, "pm10": 110.0},
    "dammam": {"temp_c": 45.0, "humidity": 55.0, "pm25": 62.0, "pm10": 135.0},
    "alexandria": {"temp_c": 33.0, "humidity": 70.0, "pm25": 38.0, "pm10": 80.0},
    "mecca": {"temp_c": 47.0, "humidity": 20.0, "pm25": 90.0, "pm10": 180.0},
    "medina": {"temp_c": 46.0, "humidity": 16.0, "pm25": 75.0, "pm10": 160.0},
    "aswan": {"temp_c": 48.0, "humidity": 12.0, "pm25": 50.0, "pm10": 120.0},
}


@tool
def get_environmental_hazard_index(
    city: str,
    temperature_c: float | None = None,
    relative_humidity: float | None = None,
    pm25: float | None = None,
    pm10: float | None = None,
    direct_sunlight: bool = True,
) -> dict[str, Any]:
    """Retrieve environmental hazard metrics, WBGT heat index, work-rest cycles, and particulate risk.

    Calculates heat stress according to OSHA/ISO 7243 standards and evaluates
    particulate pollution for outdoor workers and asthmatic patients.

    Args:
        city: The target city name (e.g. Riyadh, Cairo, Jeddah, Dammam, Alexandria).
        temperature_c: Optional ambient dry-bulb air temperature in Celsius. If omitted, uses realistic city presets.
        relative_humidity: Optional relative humidity percentage (0-100).
        pm25: Optional PM2.5 particulate concentration in ug/m3.
        pm10: Optional PM10 particulate concentration in ug/m3.
        direct_sunlight: Whether the worker is under direct desert sunlight (True) or in shade (False).

    Returns:
        A dictionary containing ambient temperature, relative humidity, calculated WBGT,
        heat stress category, OSHA work-rest cycle, hydration guidelines, PM2.5/PM10 category,
        and specific respiratory warnings.
    """
    key = city.strip().lower()
    preset = CITY_CLIMATE_PRESETS.get(key, {"temp_c": 38.0, "humidity": 35.0, "pm25": 45.0, "pm10": 95.0})

    t = temperature_c if temperature_c is not None else preset["temp_c"]
    rh = relative_humidity if relative_humidity is not None else preset["humidity"]
    p25 = pm25 if pm25 is not None else preset["pm25"]
    p10 = pm10 if pm10 is not None else preset["pm10"]

    wbgt = calculate_wbgt(t, rh, direct_sunlight=direct_sunlight)
    heat_stress = evaluate_heat_stress(wbgt)
    air_quality = evaluate_air_quality(p25, p10)

    # Check Saudi Midday Work Ban conditions (prohibited outdoor work 12 PM to 3 PM during summer, or extreme WBGT)
    is_saudi_city = key in ["riyadh", "jeddah", "dammam", "mecca", "medina"]
    saudi_midday_ban_alert = (
        is_saudi_city and (t >= 45.0 or wbgt >= WBGTThresholds.VERY_HIGH_RISK_MAX)
    )

    return {
        "city": city,
        "ambient_temperature_c": t,
        "relative_humidity_percent": rh,
        "calculated_wbgt_c": wbgt,
        "direct_sunlight": direct_sunlight,
        "heat_stress": heat_stress,
        "air_quality": air_quality,
        "saudi_midday_work_ban_alert": saudi_midday_ban_alert,
        "summary": (
            f"City: {city.title()} | Temp: {t}C | WBGT: {wbgt}C ({heat_stress['tier']}) | "
            f"AQI: {air_quality['category']} (PM2.5: {p25}, PM10: {p10}) | "
            f"Work Cycle: {heat_stress['work_rest_cycle']} | "
            f"Hydration: {heat_stress['hydration_liters_per_hour']} L/hr"
        ),
    }

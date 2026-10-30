"""Unit tests for Nafas environmental, medication, and shelter tools."""

import pytest
from nafas.tools.environmental import (
    calculate_wet_bulb_temperature,
    calculate_wbgt,
    evaluate_heat_stress,
    evaluate_air_quality,
    get_environmental_hazard_index,
)
from nafas.tools.medication import (
    verify_respiratory_medication_safety,
    DANGEROUS_ASTHMA_CONTRAINDICATIONS,
)
from nafas.tools.shelter import find_cooling_or_nebulizer_shelter


class TestEnvironmentalTools:
    """Test suite for heat stress and air quality tools."""

    def test_stull_wet_bulb_temperature_calculation(self):
        """Verify Stull formula produces realistic wet-bulb values."""
        tw = calculate_wet_bulb_temperature(temperature_c=40.0, relative_humidity=30.0)
        assert 20.0 < tw < 30.0

    def test_wbgt_sun_vs_shade(self):
        """Verify direct sunlight yields higher WBGT than shaded conditions."""
        wbgt_sun = calculate_wbgt(temperature_c=45.0, relative_humidity=20.0, direct_sunlight=True)
        wbgt_shade = calculate_wbgt(temperature_c=45.0, relative_humidity=20.0, direct_sunlight=False)
        assert wbgt_sun > wbgt_shade

    def test_heat_stress_tiers(self):
        """Verify OSHA work-rest tiers correspond to temperature thresholds."""
        low = evaluate_heat_stress(24.0)
        assert low["tier"] == "LOW"
        assert "Continuous work" in low["work_rest_cycle"]

        moderate = evaluate_heat_stress(27.0)
        assert moderate["tier"] == "MODERATE"
        assert moderate["hydration_liters_per_hour"] == 0.5

        high = evaluate_heat_stress(30.0)
        assert high["tier"] == "HIGH"
        assert high["hydration_liters_per_hour"] == 0.75

        very_high = evaluate_heat_stress(32.0)
        assert very_high["tier"] == "VERY_HIGH"

        extreme = evaluate_heat_stress(33.5)
        assert extreme["tier"] == "EXTREME"
        assert extreme["work_ban_active"] is True
        assert "STOP" in extreme["work_rest_cycle"]

    def test_air_quality_dust_storm(self):
        """Verify severe particulate levels trigger dust storm warnings."""
        aq = evaluate_air_quality(pm25=160.0, pm10=350.0)
        assert aq["category"] == "HAZARDOUS"
        assert aq["is_dust_storm"] is True
        assert "N95" in aq["mask_recommendation"]

    def test_get_environmental_hazard_index_tool_call(self):
        """Test tool execution with city preset."""
        result = get_environmental_hazard_index(city="Riyadh")
        assert result["city"] == "Riyadh"
        assert result["ambient_temperature_c"] >= 45.0
        assert result["calculated_wbgt_c"] > 30.0
        assert "saudi_midday_work_ban_alert" in result


class TestMedicationTools:
    """Test suite for respiratory medication safety and contraindications."""

    def test_rescue_inhaler_recognition(self):
        """Verify Ventolin is classified as rescue inhaler without oral rinse requirement."""
        res = verify_respiratory_medication_safety(drug_name="Ventolin")
        assert res["is_safe_for_patient"] is True
        assert res["is_rescue_inhaler"] is True
        assert res["is_daily_maintenance"] is False
        assert res["drug_class"] == "SABA"
        assert res["oral_rinse_required"] is False

    def test_maintenance_steroid_rinse_enforcement(self):
        """Verify Pulmicort requires mandatory post-inhalation oral rinsing."""
        res = verify_respiratory_medication_safety(drug_name="Pulmicort")
        assert res["is_safe_for_patient"] is True
        assert res["is_rescue_inhaler"] is False
        assert res["is_daily_maintenance"] is True
        assert res["drug_class"] == "ICS"
        assert res["oral_rinse_required"] is True
        assert "rinse mouth" in res["technique_guideline"].lower()

    def test_acute_attack_steroid_misuse_warning(self):
        """Verify acute warning when patient attempts to use steroid for active suffocation."""
        res = verify_respiratory_medication_safety(drug_name="Pulmicort", is_acute_attack=True)
        assert res["attack_misuse_warning"] is not None
        assert "NOT a rescue inhaler" in res["attack_misuse_warning"]

    @pytest.mark.parametrize("contra_drug", [
        "aspirin", "ibuprofen", "advil", "brufen", "cataflam", "voltaren", "propranolol"
    ])
    def test_lethal_contraindication_interception(self, contra_drug):
        """Verify 100% detection of critical contraindicated drugs in asthma."""
        res = verify_respiratory_medication_safety(drug_name=contra_drug, patient_has_asthma=True)
        assert res["is_safe_for_patient"] is False
        assert res["contraindication_level"] == "LETHAL_CONTRAINDICATION"
        assert res["severity"] == "CRITICAL"
        assert "safe_alternative" in res
        if "propranolol" not in contra_drug:
            assert "Paracetamol" in res["safe_alternative"]

    def test_unknown_drug_fail_closed(self):
        """Verify unverified drugs return fail-closed advisory to consult pharmacist."""
        res = verify_respiratory_medication_safety(drug_name="ExperimentalCompoundX")
        assert res["is_safe_for_patient"] is None
        assert res["contraindication_level"] == "UNKNOWN_UNVERIFIED"


class TestShelterTools:
    """Test suite for cooling shelter and nebulizer clinic locator."""

    def test_riyadh_shelters_nebulizer(self):
        """Verify Riyadh shelters filter returns clinics with emergency nebulizers."""
        res = find_cooling_or_nebulizer_shelter(city="Riyadh", need_nebulizer=True)
        assert res["found"] is not False
        assert len(res["recommended_shelters"]) > 0
        for s in res["recommended_shelters"]:
            assert s["has_nebulizer"] is True

    def test_cairo_shelters_district_filter(self):
        """Verify Cairo shelter search filters by district."""
        res = find_cooling_or_nebulizer_shelter(city="Cairo", district="Shubra")
        assert len(res["recommended_shelters"]) > 0
        assert any("shubra" in s["district"].lower() for s in res["recommended_shelters"])

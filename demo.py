#!/usr/bin/env python3
"""Interactive demonstration CLI for Nafas (نَفَس).

Demonstrates the 7 workshop modules across realistic field scenarios:
1. Riyadh Outdoor Laborer Heat Stress & Saudi Midday Ban
2. Cairo Asthmatic Child & Lethal Ibuprofen/Aspirin Interception
3. Acute Red-Flag Crisis Cyanosis Trigger (Saudi 997 / Egypt 123)
4. Persistent Patient Baseline Memory Across Ephemeral Sessions
"""

import json
import sys
import time
from nafas.config import APP_NAME, APP_ARABIC_NAME, APP_TAGLINE
from nafas.tools.environmental import get_environmental_hazard_index
from nafas.tools.medication import verify_respiratory_medication_safety
from nafas.tools.shelter import find_cooling_or_nebulizer_shelter
from nafas.steering.clinical_guardrails import check_red_flag_emergency
from nafas.session.patient_memory import PatientSessionStore, PatientRespiratoryProfile
from nafas.agents.supervisor import NafasOrchestrator


def print_banner():
    print("=" * 70)
    print(f" {APP_NAME} ({APP_ARABIC_NAME}): {APP_TAGLINE}")
    print(" Built with AWS Strands Agents SDK for AWS Builder Center Challenge")
    print(" Author: Mohamed Makhlouf (Omar)")
    print("=" * 70)


def demo_scenario_1_heatwave_worker():
    print("\n" + "#" * 70)
    print(" SCENARIO 1: Outdoor Construction Worker in Riyadh (46.5C Extreme Heat)")
    print("#" * 70)
    print("Context: Worker under direct desert sun asks about safe working hours and hydration.\n")

    t0 = time.time()
    env = get_environmental_hazard_index(city="Riyadh", direct_sunlight=True)
    shelters = find_cooling_or_nebulizer_shelter(city="Riyadh", district="Al-Batha")
    latency = round((time.time() - t0) * 1000, 2)

    print(f"[Module 1: Environmental Tool Execution ({latency} ms)]")
    print(f"• City: {env['city']} (Temp: {env['ambient_temperature_c']}C, Humidity: {env['relative_humidity_percent']}%)")
    print(f"• Calculated WBGT: {env['calculated_wbgt_c']}C -> Risk Tier: {env['heat_stress']['tier']}")
    print(f"• Mandatory Work-Rest Schedule: {env['heat_stress']['work_rest_cycle']}")
    print(f"• Hourly Hydration Requirement: {env['heat_stress']['hydration_liters_per_hour']} Liters/hour")
    print(f"• Saudi Midday Work Ban Alert: {'ACTIVE (Outdoor work prohibited)' if env['saudi_midday_work_ban_alert'] else 'Inactive'}")

    print("\n[Module 1: Municipal Cooling Shelter Routing]")
    for s in shelters["recommended_shelters"][:2]:
        print(f"• {s['name']} ({s['district']}): {s['address']} (Hours: {s['operating_hours']})")


def demo_scenario_2_medication_safety():
    print("\n" + "#" * 70)
    print(" SCENARIO 2: Asthmatic Child in Cairo (Ibuprofen / Aspirin Safety Check)")
    print("#" * 70)
    print("Context: Mother in Cairo asks if she can give her asthmatic 8-year-old Brufen (Ibuprofen) for a fever.\n")

    t0 = time.time()
    res = verify_respiratory_medication_safety(drug_name="Brufen", patient_has_asthma=True)
    latency = round((time.time() - t0) * 1000, 2)

    print(f"[Module 1 & 3: Clinical Safety Interception ({latency} ms)]")
    print(f"• Drug Queried: {res['drug_name']}")
    print(f"• Safe for Asthmatic Patient: {res['is_safe_for_patient']}")
    print(f"• Contraindication Level: {res['contraindication_level']} ({res['severity']})")
    print(f"• Alert: {res['alert_title']}")
    print(f"• Clinical Rationale: {res['clinical_rationale']}")
    print(f"• Prescribed Safe Alternative: {res['safe_alternative']}")


def demo_scenario_3_red_flag_emergency():
    print("\n" + "#" * 70)
    print(" SCENARIO 3: Acute Red-Flag Emergency (Cyanosis & Severe Breathlessness)")
    print("#" * 70)
    print("Context: User frantic message: 'الولد شفايفه زرقاء ومش قادر يتنفس وخلاص هيغمى عليه' (Child has blue lips and fainting).\n")

    t0 = time.time()
    triage = check_red_flag_emergency("الولد شفايفه زرقاء ومش قادر يتنفس وخلاص هيغمى عليه")
    latency = round((time.time() - t0) * 1000, 2)

    print(f"[Module 3: Sub-Second Fail-Closed Emergency Interrupt ({latency} ms)]")
    print(f"• Red-Flag Crisis Detected: {triage['is_emergency']}")
    print(f"• Matched Clinical Invariants: {triage['matched_red_flags']}")
    print("\nHigh-Visibility Dispatch Output:")
    print("-" * 50)
    print(triage["emergency_dispatch_message"])
    print("-" * 50)


def demo_scenario_4_session_persistence():
    print("\n" + "#" * 70)
    print(" SCENARIO 4: Persistent Patient Memory Across Stateless Consultations")
    print("#" * 70)
    print("Context: Patient baseline profile preserved in session store across Lambda restarts.\n")

    store = PatientSessionStore(base_dir=".demo_sessions")
    profile = PatientRespiratoryProfile(
        patient_id="patient_zaid_09",
        name="Zaid",
        age=8,
        primary_condition="Moderate Persistent Allergic Asthma",
        known_allergies=["Aspirin", "Ibuprofen / NSAIDs"],
        prescribed_inhalers=["Ventolin (Reliever)", "Pulmicort 200mcg (Twice daily)"],
        notes=["History of Khamaseen exacerbation in Cairo"],
    )
    store.save_profile(profile)

    context_prompt = store.format_profile_for_prompt("patient_zaid_09")
    print("[Module 4: Injected Patient Baseline Memory Prompt]")
    print(context_prompt)


def main():
    print_banner()
    demo_scenario_1_heatwave_worker()
    demo_scenario_2_medication_safety()
    demo_scenario_3_red_flag_emergency()
    demo_scenario_4_session_persistence()
    print("\n" + "=" * 70)
    print(" All 4 demonstration scenarios executed successfully.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

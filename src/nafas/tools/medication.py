"""Respiratory medication safety and inhaler verification tools for Nafas (نَفَس).

Verifies inhaler classifications, flags dangerous drug contraindications (NSAIDs/aspirin in asthma),
and provides spacer inhalation guidance.
"""

from typing import Any
from strands import tool


# Clinical database of respiratory medications and contraindications
RESPIRATORY_DRUG_DATABASE: dict[str, dict[str, Any]] = {
    "ventolin": {
        "generic": "Salbutamol (Albuterol)",
        "class": "SABA",
        "category_label": "Fast-Acting Rescue Bronchodilator",
        "is_rescue": True,
        "is_maintenance": False,
        "critical_instructions": [
            "Use immediately during sudden wheezing, chest tightness, or asthma attacks.",
            "Standard emergency dose: 2 puffs with 1 minute between puffs.",
            "If no relief after 4 puffs, seek emergency medical care immediately (call 997 in Saudi Arabia, 123 in Egypt).",
            "Always shake canister for 5 seconds prior to inhalation.",
            "Use a spacer chamber whenever possible to maximize lung delivery.",
        ],
        "contraindicated_drugs": ["propranolol", "timolol", "atenolol", "carvedilol"],
    },
    "albuterol": {
        "generic": "Albuterol sulfate",
        "class": "SABA",
        "category_label": "Fast-Acting Rescue Bronchodilator",
        "is_rescue": True,
        "is_maintenance": False,
        "critical_instructions": [
            "Emergency rescue inhaler for acute shortness of breath.",
            "Shake well, inhale deeply, and hold breath for 10 seconds.",
            "Needing rescue inhaler more than twice a week indicates uncontrolled asthma.",
        ],
        "contraindicated_drugs": ["propranolol", "timolol", "carvedilol"],
    },
    "salbutamol": {
        "generic": "Salbutamol",
        "class": "SABA",
        "category_label": "Fast-Acting Rescue Bronchodilator",
        "is_rescue": True,
        "is_maintenance": False,
        "critical_instructions": [
            "Use for sudden shortness of breath, coughing fits, or wheezing.",
            "Take 1 to 2 puffs, wait 1 minute between puffs.",
            "Do not exceed maximum doctor-prescribed puffs.",
        ],
        "contraindicated_drugs": ["propranolol", "timolol"],
    },
    "pulmicort": {
        "generic": "Budesonide",
        "class": "ICS",
        "category_label": "Inhaled Corticosteroid (Maintenance / Preventative)",
        "is_rescue": False,
        "is_maintenance": True,
        "critical_instructions": [
            "MUST NOT be used as a rescue inhaler during acute sudden suffocation; it takes days to weeks to build anti-inflammatory effect.",
            "MANDATORY: Rinse mouth thoroughly with water and spit it out after every dose to prevent fungal oral thrush (candidiasis) and voice hoarseness.",
            "Take every day consistently as prescribed, even when feeling well.",
        ],
        "contraindicated_drugs": [],
    },
    "budesonide": {
        "generic": "Budesonide",
        "class": "ICS",
        "category_label": "Inhaled Corticosteroid (Maintenance / Preventative)",
        "is_rescue": False,
        "is_maintenance": True,
        "critical_instructions": [
            "Daily controller medication reducing chronic airway inflammation.",
            "Not for sudden acute asthma attacks.",
            "Always rinse and spit with water after every inhalation.",
        ],
        "contraindicated_drugs": [],
    },
    "flixotide": {
        "generic": "Fluticasone propionate",
        "class": "ICS",
        "category_label": "Inhaled Corticosteroid (Maintenance / Preventative)",
        "is_rescue": False,
        "is_maintenance": True,
        "critical_instructions": [
            "Daily maintenance steroid to prevent asthma flare-ups.",
            "Do not use for sudden emergency attacks.",
            "Always rinse mouth with water and spit after use.",
        ],
        "contraindicated_drugs": [],
    },
    "fluticasone": {
        "generic": "Fluticasone propionate",
        "class": "ICS",
        "category_label": "Inhaled Corticosteroid (Maintenance / Preventative)",
        "is_rescue": False,
        "is_maintenance": True,
        "critical_instructions": [
            "Daily maintenance inhaler.",
            "Rinse mouth and spit after use to protect oral mucosa.",
        ],
        "contraindicated_drugs": [],
    },
    "symbicort": {
        "generic": "Budesonide + Formoterol",
        "class": "ICS_LABA",
        "category_label": "Combination Controller & Fast-Onset LABA",
        "is_rescue": True,  # Under SMART / MART protocols
        "is_maintenance": True,
        "critical_instructions": [
            "Combines an anti-inflammatory steroid with a rapid long-acting bronchodilator.",
            "Used as scheduled daily therapy, and can also be used as emergency reliever under SMART protocol guidance.",
            "Always rinse mouth and spit after each dose.",
        ],
        "contraindicated_drugs": ["propranolol", "timolol"],
    },
    "seretide": {
        "generic": "Fluticasone + Salmeterol",
        "class": "ICS_LABA",
        "category_label": "Combination Maintenance Controller",
        "is_rescue": False,
        "is_maintenance": True,
        "critical_instructions": [
            "Scheduled morning and evening preventative controller.",
            "Not for immediate relief of sudden acute asthma attack; keep Ventolin accessible.",
            "Rinse mouth and spit out water after every inhalation.",
        ],
        "contraindicated_drugs": ["propranolol"],
    },
    "atrovent": {
        "generic": "Ipratropium bromide",
        "class": "SAMA",
        "category_label": "Short-Acting Anticholinergic Bronchodilator",
        "is_rescue": True,
        "is_maintenance": False,
        "critical_instructions": [
            "Relaxes airway muscles; often nebulized during acute COPD or severe asthma exacerbation in clinic.",
            "Avoid spraying near eyes (risk of acute angle-closure glaucoma).",
        ],
        "contraindicated_drugs": [],
    },
}

# Dangerous contraindicated non-respiratory drugs for asthmatic patients
DANGEROUS_ASTHMA_CONTRAINDICATIONS: dict[str, dict[str, str]] = {
    "aspirin": {
        "severity": "CRITICAL",
        "reason": (
            "Aspirin triggers severe, potentially fatal bronchospasms in asthmatics with "
            "AERD (Aspirin-Exacerbated Respiratory Disease). Can induce sudden status asthmaticus."
        ),
        "safe_alternative": "Paracetamol (Acetaminophen) for fever or mild-to-moderate pain.",
    },
    "acetylsalicylic acid": {
        "severity": "CRITICAL",
        "reason": "Chemical name for aspirin. High risk of precipitating lethal bronchospasm in asthma.",
        "safe_alternative": "Paracetamol (Acetaminophen).",
    },
    "ibuprofen": {
        "severity": "CRITICAL",
        "reason": (
            "Non-steroidal anti-inflammatory drug (NSAID). Inhibits COX-1 and shunts arachidonic "
            "acid into the leukotriene pathway, causing acute bronchial constriction in asthmatics."
        ),
        "safe_alternative": "Paracetamol (Acetaminophen).",
    },
    "advil": {
        "severity": "CRITICAL",
        "reason": "Brand name for Ibuprofen (NSAID). High risk of triggering acute asthma attack.",
        "safe_alternative": "Paracetamol (Panadol / Tylenol).",
    },
    "brufen": {
        "severity": "CRITICAL",
        "reason": "Brand name for Ibuprofen (NSAID). High risk of acute bronchospasm.",
        "safe_alternative": "Paracetamol (Panadol / Adol).",
    },
    "cataflam": {
        "severity": "CRITICAL",
        "reason": "Diclofenac potassium (NSAID). High risk of precipitating severe asthma exacerbation.",
        "safe_alternative": "Paracetamol (Panadol).",
    },
    "voltaren": {
        "severity": "CRITICAL",
        "reason": "Diclofenac sodium (NSAID). May provoke sudden acute bronchospasm in asthmatics.",
        "safe_alternative": "Paracetamol.",
    },
    "naproxen": {
        "severity": "CRITICAL",
        "reason": "NSAID with prolonged half-life. Can trigger severe asthma attacks.",
        "safe_alternative": "Paracetamol.",
    },
    "propranolol": {
        "severity": "CRITICAL",
        "reason": (
            "Non-selective beta-blocker (Inderal). Blocks beta-2 adrenergic receptors in lungs, "
            "completely neutralizing rescue inhalers (Ventolin) and causing severe refractory bronchospasm."
        ),
        "safe_alternative": "Cardioselective beta-blocker or calcium channel blocker under cardiologist direction.",
    },
    "inderal": {
        "severity": "CRITICAL",
        "reason": "Brand name for Propranolol. Strongly contraindicated in asthma and COPD.",
        "safe_alternative": "Consult prescribing cardiologist for asthma-safe antihypertensive.",
    },
}


@tool
def verify_respiratory_medication_safety(
    drug_name: str,
    patient_has_asthma: bool = True,
    patient_has_copd: bool = False,
    is_acute_attack: bool = False,
) -> dict[str, Any]:
    """Verify safety, classification, contraindications, and usage technique for respiratory and pain drugs.

    Flags lethal drug contraindications (such as Aspirin or Ibuprofen in asthmatics),
    clarifies difference between emergency rescue inhalers (Ventolin) and daily preventative
    steroids (Pulmicort), and mandates post-steroid oral rinsing to prevent fungal infections.

    Args:
        drug_name: The name of the medication to check (e.g. Ventolin, Pulmicort, Aspirin, Brufen, Propranolol).
        patient_has_asthma: Whether the patient has a diagnosed history of asthma.
        patient_has_copd: Whether the patient has Chronic Obstructive Pulmonary Disease.
        is_acute_attack: Whether the patient is currently experiencing an acute breathing emergency.

    Returns:
        A dictionary detailing safety status, contraindication alerts, inhaler class,
        crucial administration instructions, and emergency escalation advice if required.
    """
    cleaned_name = drug_name.strip().lower()

    # 1. Check for dangerous contraindications first (Aspirin, NSAIDs, Beta-blockers in asthma)
    for contra_key, contra_info in DANGEROUS_ASTHMA_CONTRAINDICATIONS.items():
        if contra_key in cleaned_name or cleaned_name in contra_key:
            if patient_has_asthma or patient_has_copd:
                return {
                    "drug_name": drug_name,
                    "is_safe_for_patient": False,
                    "contraindication_level": "LETHAL_CONTRAINDICATION",
                    "severity": contra_info["severity"],
                    "alert_title": f"DO NOT ADMINISTER {drug_name.upper()} TO ASTHMATIC PATIENTS",
                    "clinical_rationale": contra_info["reason"],
                    "safe_alternative": contra_info["safe_alternative"],
                    "action_required": (
                        f"STOP immediately. Do not take {drug_name}. If fever or pain relief is needed, "
                        f"use {contra_info['safe_alternative']} unless allergic."
                    ),
                }

    # 2. Check respiratory drug database
    matched_entry = None
    for db_key, entry in RESPIRATORY_DRUG_DATABASE.items():
        if db_key in cleaned_name or cleaned_name in db_key:
            matched_entry = entry
            break

    if matched_entry:
        is_rescue = matched_entry["is_rescue"]
        is_maintenance = matched_entry["is_maintenance"]

        # Critical warning if patient is having an acute attack but holding a maintenance steroid
        attack_misuse_warning = None
        if is_acute_attack and is_maintenance and not is_rescue:
            attack_misuse_warning = (
                f"DANGER: {drug_name} is a maintenance steroid, NOT a rescue inhaler. "
                "It will NOT open closed airways during an acute attack. "
                "Use your blue rescue inhaler (Ventolin / Salbutamol) immediately, "
                "or call emergency medical dispatch (Saudi 997, Egypt 123)."
            )

        oral_rinse_required = matched_entry["class"] in ["ICS", "ICS_LABA"]

        return {
            "drug_name": drug_name,
            "is_safe_for_patient": True,
            "contraindication_level": "NONE",
            "generic_name": matched_entry["generic"],
            "drug_class": matched_entry["class"],
            "category_label": matched_entry["category_label"],
            "is_rescue_inhaler": is_rescue,
            "is_daily_maintenance": is_maintenance,
            "attack_misuse_warning": attack_misuse_warning,
            "oral_rinse_required": oral_rinse_required,
            "instructions": matched_entry["critical_instructions"],
            "technique_guideline": (
                "1. Shake canister 5 seconds. "
                "2. Sit upright, breathe out away from inhaler. "
                "3. Use spacer chamber if available. "
                "4. Press canister once while breathing in slowly and deeply. "
                "5. Hold breath for 10 seconds. "
                "6. Wait 1 minute before second puff."
                + (" 7. Rinse mouth with water and spit it out." if oral_rinse_required else "")
            ),
        }

    # 3. Drug not found in database: return safe fail-closed advisory
    return {
        "drug_name": drug_name,
        "is_safe_for_patient": None,
        "contraindication_level": "UNKNOWN_UNVERIFIED",
        "alert_title": f"Unverified Medication: {drug_name}",
        "action_required": (
            f"The medication '{drug_name}' is not in the verified respiratory safety catalog. "
            "To prevent severe adverse reactions, consult a registered pharmacist or physician "
            "before taking this drug with asthma or COPD."
        ),
    }

"""Cultural dialect steering and accessibility prompts for Nafas (نَفَس).

Supports Saudi vernacular, Egyptian colloquial, and plain English for migrant outdoor workers.
"""

DIALECT_STEERING_INSTRUCTIONS: dict[str, str] = {
    "saudi": (
        "Respond in warm, respectful, and accessible Saudi vernacular (Najdi/Hejazi phrasing). "
        "Use reassuring local expressions like 'سلامتك وما تشوف شر يا غالي' and 'انتبه على نفسك من لهيب الشمس'. "
        "Reference official Saudi health hotlines: 937 (Ministry of Health consultation) and 997 (Red Crescent Ambulance). "
        "Keep the advice grounded, direct, and easy to follow on mobile voice or messaging."
    ),
    "egyptian": (
        "Respond in reassuring, compassionate, and clear Egyptian colloquial Arabic. "
        "Use warm cultural expressions like 'ألف سلامة عليك' and 'ربنا يحفظك ويطمنا عليك'. "
        "Reference official Egyptian emergency lines: 123 (Ambulance) and 137 (Ministry of Health emergency). "
        "Explain medical instructions in plain street-level vocabulary without patronizing clinical jargon."
    ),
    "english_worker": (
        "Respond in simple, clear, 6th-grade level English designed for migrant outdoor laborers. "
        "Use short sentences, direct verbs, and clean bullet points. "
        "Avoid medical jargon (use 'water' instead of 'hydration', 'shade' instead of 'micro-climate shelter', 'blue inhaler' for 'fast-acting beta-2 agonist'). "
        "Highlight emergency numbers clearly."
    ),
}


def get_dialect_steering(dialect: str = "english_worker") -> str:
    """Retrieve system steering prompt corresponding to user's dialect and accessibility needs."""
    key = dialect.strip().lower()
    if "saudi" in key or "gulf" in key or "سعودي" in key:
        return DIALECT_STEERING_INSTRUCTIONS["saudi"]
    elif "egypt" in key or "masri" in key or "مصر" in key:
        return DIALECT_STEERING_INSTRUCTIONS["egyptian"]
    else:
        return DIALECT_STEERING_INSTRUCTIONS["english_worker"]

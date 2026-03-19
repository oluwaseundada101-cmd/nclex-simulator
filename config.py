"""
config.py — Layer definitions, badge maps, stop rules.
No Streamlit imports — pure data.
"""

LAYER_INFO = {
    "A":        {"label": "Layer A",         "long": "Layer A — Recall Anchors",           "cls": "badge-layer-a"},
    "A-Applied":{"label": "Layer A-Applied", "long": "Layer A-Applied — Facts in Disguise","cls": "badge-layer-aa"},
    "B":        {"label": "Layer B",         "long": "Layer B — Mechanism/Physiology",     "cls": "badge-layer-b"},
    "C":        {"label": "Layer C",         "long": "Layer C — Clinical Judgment",        "cls": "badge-layer-c"},
    "D":        {"label": "Layer D",         "long": "Layer D — Confusable Pairs",         "cls": "badge-layer-d"},
    "NGN":      {"label": "NGN",             "long": "NGN — Next Generation Formats",      "cls": "badge-layer-ngn"},
}

# Framework stop-rule thresholds (%) before advancing to next layer
LAYER_STOP_RULES = {
    "A":         95,
    "A-Applied": 90,
    "B":         68,
    "C":         90,
    "D":         85,
    "NGN":       68,
}

TYPE_BADGE = {
    "MC":    ("badge-mc",    "Multiple Choice"),
    "SATA":  ("badge-sata",  "Select All That Apply"),
    "BOWTIE":("badge-bowtie","Bowtie"),
    "MATRIX":("badge-matrix","Matrix Grid"),
    "TREND": ("badge-trend", "Trend"),
    "CLOZE": ("badge-cloze", "Drop-Down / Cloze"),
}

# Miss-type inference: maps (question_type, pattern) → inferred miss type
# Used in grading.py to auto-diagnose what went wrong
MISS_TYPE_LABELS = {
    "Fact gap":             "You don't yet know this fact — add it to Layer A drills.",
    "Translation failure":  "You know the fact but missed it in disguised form — redo Layer A-Applied.",
    "Distractor trap":      "You chose a plausible-sounding wrong answer — read the rationale carefully.",
    "Wrong priority schema":"You picked a correct action but the wrong PRIORITY — review priority rules.",
    "Stem misread":         "Re-read the question stem — the answer changes based on what is actually being asked.",
    "Answer-change error":  "Your first instinct was likely correct — avoid second-guessing.",
}

PASSING_PCT = 68  # NCLEX standard passing threshold

# Layer ordering for display/progression
LAYER_ORDER = ["A", "A-Applied", "B", "C", "D", "NGN"]

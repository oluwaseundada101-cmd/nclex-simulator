# NGN Simulator — Question Bank Schema Reference
Generated from MASTER_FRAMEWORK_VERSION_FINAL_COMPLETE

---

## Top-Level Bank Object

```json
{
  "id": "unique_bank_id",
  "title": "Unit X — Topic Name",
  "description": "Short description of content covered",
  "question_count": 25,
  "questions": [ ... ]
}
```

---

## Per-Question Fields (ALL types)

| Field | Type | Required | Values / Notes |
|---|---|---|---|
| `id` | string | ✅ | Unique, e.g. `mc_001` |
| `type` | string | ✅ | `MC` \| `SATA` \| `BOWTIE` \| `MATRIX` \| `TREND` \| `CLOZE` |
| `ngn` | boolean | ✅ | `true` for BOWTIE/MATRIX/TREND/CLOZE; `false` for MC/SATA |
| `layer` | string | ✅ | `A` \| `A-Applied` \| `B` \| `C` \| `D` \| `NGN` |
| `layer_subtype` | string | ✅ | See table below |
| `nclex_category` | string | ✅ | See NCLEX categories below |
| `nclex_subcategory` | string | ✅ | See NCLEX subcategories below |
| `concept_bucket` | string | ✅ | Disease/drug/topic name, e.g. `BPH`, `Meningitis` |
| `tier1_fact` | string \| null | ⬜ | Required for Layer A and A-Applied — exact fact being tested |
| `interference_pair` | string \| null | ⬜ | Required for Layer D — e.g. `Crohn's vs UC` |
| `miss_type_flags` | array | ⬜ | 1-2 expected miss types (see list below) |
| `case_study` | string | ⬜ | Clinical scenario paragraph (for NGN types, highly recommended) |
| `text` | string | ✅ | Question stem |
| `rationale` | string | ✅ | Explanation of correct answer and why distractors are wrong |

---

## Layer Values

| Layer | % of Bank | Purpose |
|---|---|---|
| `A` | 20% | Verbatim fact recall — no clinical scenario, direct and short |
| `A-Applied` | 12% | Same Tier 1 fact but disguised (food scenario, actual lab values, threshold) |
| `B` | 15% | Mechanism/physiology — WHY the rule exists |
| `C` | 45-50% | Clinical judgment — the NCLEX core (priority, complication, teaching, delegation) |
| `D` | 8-10% | Interference items — two confusable concepts in ONE stem |
| `NGN` | varies | Next-Gen format items (Bowtie/Matrix/Trend/Cloze) |

---

## Layer Subtype Values (for `layer_subtype`)

**Layer C subtypes:**
- `priority/first action`
- `complication/escalation`
- `teaching-content`
- `teaching-evaluation`
- `cue recognition`
- `expected vs concerning finding`
- `lab cluster interpretation`
- `multi-patient triage`
- `delegation/UAP`
- `therapeutic communication`
- `drug polypharmacy/comorbidity`

**Layer A/A-Applied subtypes:**
- `recall`
- `translation`

**Layer B:**
- `mechanism`

**Layer D:**
- `interference`

**NGN type subtypes:**
- `bowtie`
- `matrix grid`
- `trend`
- `drop-down/cloze`

---

## NCLEX Client Need Categories

| Category | Subcategories |
|---|---|
| Safe and Effective Care Environment | Management of Care; Safety and Infection Control |
| Health Promotion and Maintenance | (none required for subcategory) |
| Psychosocial Integrity | (none required for subcategory) |
| Physiological Integrity | Basic Care and Comfort; Pharmacological and Parenteral Therapies; Reduction of Risk Potential; Physiological Adaptation |

---

## Miss Type Flags (for `miss_type_flags`)

| Flag | Meaning |
|---|---|
| `Fact gap` | Student doesn't know the underlying fact |
| `Translation failure` | Knows the fact but can't apply it in disguised form |
| `Distractor trap` | Chooses a plausible-sounding wrong answer |
| `Wrong priority schema` | Picks a correct action but wrong PRIORITY |
| `Stem misread` | Misreads what the question is actually asking |
| `Answer-change error` | Would have had it right but second-guessed |

---

## Type-Specific Fields

### MC (Multiple Choice)
```json
{
  "options": { "A": "...", "B": "...", "C": "...", "D": "..." },
  "correct_answers": ["B"]
}
```

### SATA (Select All That Apply)
```json
{
  "options": { "A": "...", "B": "...", "C": "...", "D": "...", "E": "...", "F": "..." },
  "correct_answers": ["A", "C", "E"]
}
```

### BOWTIE (Framework-aligned)
```json
{
  "bowtie": {
    "condition_options": ["...", "...", "...", "...", "..."],   // 4-5 options, select 1
    "actions_to_take":   ["...", "...", "...", "...", "..."],   // 5 options, select 2
    "parameters_to_monitor": ["...", "...", "...", "...", "..."] // 5 options, select 2
  },
  "correct_answers": {
    "condition": "Exact text of correct condition option",
    "actions": ["Exact action 1", "Exact action 2"],
    "parameters": ["Exact param 1", "Exact param 2"]
  }
}
```

### MATRIX (Matrix Grid)
```json
{
  "matrix": {
    "columns": ["Column A", "Column B", "Column C"],
    "rows": [
      { "id": "r1", "label": "Row description" },
      { "id": "r2", "label": "Row description" }
    ]
  },
  "correct_answers": {
    "r1": "Column A",
    "r2": "Column C"
  }
}
```

### TREND
```json
{
  "trend": {
    "timepoints": ["0800", "1200", "1600"],
    "data": [
      { "label": "Temperature (°F)", "values": ["101.2", "102.4", "103.6"] }
    ],
    "items": [
      { "id": "temp", "label": "Temperature" }
    ]
  },
  "correct_answers": {
    "temp": "Worsening"
  }
}
```
Allowed trend values: `"Improving"` | `"Worsening"` | `"No change"`

### CLOZE (Drop-Down / Drag-and-Drop)
```json
{
  "cloze": {
    "sentence_parts": [
      "Text before blank ",
      { "blank_id": "b1", "label": "Blank label", "options": ["Option 1", "Option 2", "Option 3", "Option 4"] },
      " text after blank."
    ]
  },
  "correct_answers": {
    "b1": "Option 2"
  }
}
```

---

## Per-Bucket Distribution Targets (from Framework)

| Bucket type | Total items | Breakdown |
|---|---|---|
| Major disease | 7 | 2×A + 1×A-Applied + 1×B + 3×C |
| Drug | 6 | 1×A + 1×A-Applied + 1×B + 3×C |
| Calculation | 6 | 2×A + 1×A-Applied + 2×B + 1×C |
| Layer D | 1 per interference pair | One per named pair from your Phase 2 map |
| NGN | ~3 per major bucket | Bowtie, Matrix, Trend, Cloze |

---

## Example Prompt for AI Question Generation

> "Generate a Layer C clinical judgment question for the concept bucket 'Meningitis'. 
> Layer subtype: complication/escalation. NCLEX category: Physiological Integrity / Reduction of Risk Potential.
> Format: SATA. Include 6 options with 3-4 correct. Include miss_type_flags: ['Wrong priority schema', 'Distractor trap'].
> Follow the JSON schema in QUESTION_SCHEMA.md exactly."

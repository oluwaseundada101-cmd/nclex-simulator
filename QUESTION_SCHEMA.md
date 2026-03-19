# NGN NCLEX Simulator — Question Schema v4

Complete documentation for the `questions.json` format.
Use this when adding new questions or building the AI generation pipeline.

---

## Top-Level Structure

```json
{
  "id": "bank-id-slug",
  "title": "Bank Display Name",
  "description": "Short description of content/coverage",
  "version": "4.0",
  "questions": [ ...question objects... ]
}
```

You may also wrap multiple banks in an array at the top level:
```json
[
  { "id": "bank1", "title": "...", "questions": [...] },
  { "id": "bank2", "title": "...", "questions": [...] }
]
```

---

## Universal Question Fields (All Types)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | ✅ | Unique slug, e.g. `"u4-a-001"` |
| `type` | string | ✅ | `"MC"`, `"SATA"`, `"BOWTIE"`, `"MATRIX"`, `"TREND"`, `"CLOZE"` |
| `layer` | string | ✅ | `"A"`, `"A-Applied"`, `"B"`, `"C"`, `"D"`, `"NGN"` |
| `layer_subtype` | string | ✅ | Free-text description, e.g. `"Recall — Formula"`, `"Clinical Judgment — Priority"` |
| `ngn` | boolean | ✅ | `true` if this is an NGN format item (Bowtie/Matrix/Trend/Cloze always `true`) |
| `nclex_category` | string | ✅ | NCLEX Client Needs category |
| `nclex_subcategory` | string | ✅ | NCLEX subcategory |
| `concept_bucket` | string | ✅ | Topic label, e.g. `"CBI Output Calculation"` |
| `interference_pair` | string | ⬜ | Name of confusable pair, e.g. `"Prazosin vs Finasteride"` — for Layer D items |
| `case_study` | string | ⬜ | Clinical scenario displayed above the stem. Use for NGN and context-heavy questions |
| `text` | string | ✅ | The question stem |
| `correct_answers` | varies | ✅ | See per-type docs below |
| `rationale` | string | ✅ | Overall explanation shown after submission |
| `source_reference` | string | ✅ | Source document(s) and page/section, e.g. `"Unit4-Hybrid-Supplemental.md.pdf (Prazosin section)"` |
| `miss_type_flags` | array | ⬜ | Override auto-inferred miss type. Array of strings from: `["Fact gap", "Translation failure", "Distractor trap", "Wrong priority schema", "Stem misread", "Answer-change error"]` |

---

## Question Types

### MC — Multiple Choice
Single best answer from 4–5 options.

```json
{
  "type": "MC",
  "options": { "A": "...", "B": "...", "C": "...", "D": "..." },
  "correct_answers": ["B"],
  "option_rationales": {
    "A": "Why A is wrong",
    "B": "Why B is correct",
    "C": "Why C is wrong",
    "D": "Why D is wrong"
  }
}
```

### SATA — Select All That Apply
Multiple correct answers; partial credit (earn 1 pt per correct selection, lose 1 pt per wrong selection).

```json
{
  "type": "SATA",
  "options": { "A": "...", "B": "...", "C": "...", "D": "...", "E": "..." },
  "correct_answers": ["A", "C", "E"],
  "option_rationales": {
    "A": "CORRECT — rationale",
    "B": "INCORRECT — rationale",
    "C": "CORRECT — rationale",
    "D": "INCORRECT — rationale",
    "E": "CORRECT — rationale"
  }
}
```

### BOWTIE
Center = condition (select 1), Left = actions to take (select N), Right = parameters to monitor (select N).

**Framework rule:** 1 condition, 2 actions, 2 parameters — do NOT change without explicit instructions.

```json
{
  "type": "BOWTIE",
  "bowtie": {
    "condition_options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "condition_count": 1,
    "actions_to_take": ["Action 1", "Action 2", "Action 3", "Action 4", "Action 5"],
    "action_count": 2,
    "parameters_to_monitor": ["Param 1", "Param 2", "Param 3", "Param 4"],
    "param_count": 2
  },
  "correct_answers": {
    "condition": "Option 2",
    "actions": ["Action 1", "Action 3"],
    "parameters": ["Param 2", "Param 4"]
  },
  "bowtie_rationales": {
    "condition": "Why this is the correct condition",
    "actions": "Why these 2 actions are correct",
    "parameters": "Why these 2 parameters are correct"
  }
}
```

**Backward compatibility:** The app also reads old-format keys `causes/actions/outcomes` automatically.

### MATRIX
One choice per row from a fixed set of columns.

```json
{
  "type": "MATRIX",
  "matrix": {
    "columns": ["Expected", "Unexpected"],
    "rows": [
      {"id": "r1", "label": "Finding 1"},
      {"id": "r2", "label": "Finding 2"}
    ]
  },
  "correct_answers": {
    "r1": "Expected",
    "r2": "Unexpected"
  },
  "cell_rationales": {
    "r1": "Why finding 1 is Expected",
    "r2": "Why finding 2 is Unexpected"
  }
}
```

**Fix note:** The app uses `st.radio(..., horizontal=True)` per row — NOT per-cell checkboxes.
This ensures true single-selection per row, matching real NCLEX behavior.

### TREND
Time-series data table followed by per-parameter classification.

```json
{
  "type": "TREND",
  "trend": {
    "timepoints": ["0800", "1200", "1600"],
    "data": [
      {"label": "WBC (cells/mm³)", "values": [12000, 16000, 21000]},
      {"label": "Temperature °F",  "values": [99.1,  100.5, 102.4]}
    ],
    "items": [
      {"id": "wbc",  "label": "WBC trend"},
      {"id": "temp", "label": "Temperature trend"}
    ]
  },
  "correct_answers": {
    "wbc":  "Worsening",
    "temp": "Worsening"
  }
}
```

Options are always: `"Improving"`, `"Worsening"`, `"No change"`.

### CLOZE — Drop-Down / Extended Drop-Down
Sentence with embedded dropdown blanks.

```json
{
  "type": "CLOZE",
  "cloze": {
    "sentence_parts": [
      "Text before first blank ",
      {"blank_id": "b1", "label": "Blank label", "options": ["Option A", "Option B", "Option C"]},
      " text between blanks ",
      {"blank_id": "b2", "label": "Second blank", "options": ["Choice 1", "Choice 2", "Choice 3"]}
    ]
  },
  "correct_answers": {
    "b1": "Option A",
    "b2": "Choice 2"
  }
}
```

---

## Miss-Type Inference (v4 Addition)

The app auto-infers miss type from `grading.py` based on layer, question type, and error pattern.
You can override with `miss_type_flags` in the question JSON.

| Miss Type | Meaning | Auto-triggered by |
|-----------|---------|-------------------|
| `Fact gap` | Student doesn't know this fact | Layer A miss, matrix/trend miss |
| `Translation failure` | Knows fact but missed it disguised | Layer A-Applied miss |
| `Distractor trap` | Chose a plausible wrong answer | Layer D miss, SATA extra selection |
| `Wrong priority schema` | Right action, wrong priority | Layer C priority subtype miss, Bowtie actions miss |
| `Stem misread` | Answer would be different if stem re-read | Set manually via `miss_type_flags` |
| `Answer-change error` | First instinct was right | Set manually via `miss_type_flags` |

---

## v4 New Fields Reference

| Field | Question Types | Purpose |
|-------|---------------|---------|
| `option_rationales` | MC, SATA | Per-option explanation shown in review |
| `cell_rationales` | MATRIX | Per-row explanation shown in review |
| `bowtie_rationales` | BOWTIE | Per-section (condition/actions/parameters) explanation |
| `miss_type_diagnosis` | All (auto) | Dynamically inferred by `grading.py` — not stored in JSON |
| `source_reference` | All | Full citation to course document + page |
| `interference_pair` | D layer | Pair name for priority tracking in SQLite |
| `bowtie.condition_count` | BOWTIE | How many conditions to select (default 1) |
| `bowtie.action_count` | BOWTIE | How many actions to select (default 2) |
| `bowtie.param_count` | BOWTIE | How many parameters to select (default 2) |

---

## Scoring

| Type | Points | Method |
|------|--------|--------|
| MC | 0 or 1 | All-or-nothing |
| SATA | 0–N | Partial credit: +1 correct, −1 wrong; min 0 |
| BOWTIE | 0–3 | 1 point each: condition, actions, parameters |
| MATRIX | 0–N rows | 1 point per correct row |
| TREND | 0–N items | 1 point per correct item |
| CLOZE | 0–N blanks | 1 point per correct blank |

---

## NCLEX Categories (Quick Reference)

- Safe and Effective Care Environment
  - Management of Care
  - Safety and Infection Control
- Health Promotion and Maintenance
- Psychosocial Integrity
- Physiological Integrity
  - Basic Care and Comfort
  - Pharmacological and Parenteral Therapies
  - Reduction of Risk Potential
  - Physiological Adaptation

---

## Layer Reference

| Layer | Threshold | Focus |
|-------|-----------|-------|
| A | 95% | Pure recall — isolated facts, normal values, drug names |
| A-Applied | 90% | Same facts as A, hidden inside a clinical scenario |
| B | 68% | Mechanisms, pharmacology, pathophysiology |
| C | 90% | Clinical judgment — priority, SATA, Bowtie, Matrix |
| D | 85% | Confusable pairs — interference pair questions |
| NGN | 68% | Full NGN formats (Bowtie, Trend, Matrix, Cloze) |

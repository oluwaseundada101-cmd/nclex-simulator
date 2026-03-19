#!/usr/bin/env python3
"""
generate_bank.py — Document-to-questions.json pipeline.

Reads one or more source documents (PDF, HTML, .md, .txt) and uses
an LLM (OpenAI GPT-4o or compatible) to emit a schema-valid questions.json.

Usage
-----
  python generate_bank.py --sources doc1.pdf doc2.html --out my_bank.json
  python generate_bank.py --sources lecture.pdf --out q.json --count 10 --layers A C D
  python generate_bank.py --sources notes.txt --out q.json --model gpt-4o-mini

Environment
-----------
  OPENAI_API_KEY   Required. Set in your shell or in a .env file.
  OPENAI_BASE_URL  Optional. Override for Azure / local LLM endpoints.

Outputs
-------
  A single questions.json file valid against QUESTION_SCHEMA.md.
  The app loads it immediately after you click "Reload Question Banks".
"""

import argparse
import json
import os
import re
import sys
import textwrap
from pathlib import Path

# ── Optional deps — install only what you need ───────────────────────────────
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


# ── Text extraction ────────────────────────────────────────────────────────────

def extract_text(path: Path) -> str:
    """Return plain text from a PDF, HTML, .md, or .txt file."""
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        if not PDF_AVAILABLE:
            print(f"  [!] pdfplumber not installed. Run: pip install pdfplumber")
            print(f"      Falling back to raw byte read (may include garbage).")
            return path.read_bytes().decode("utf-8", errors="replace")
        pages = []
        with pdfplumber.open(str(path)) as pdf:
            for pg in pdf.pages:
                t = pg.extract_text()
                if t:
                    pages.append(t)
        return "\n\n".join(pages)

    if suffix in (".html", ".htm"):
        raw = path.read_text(encoding="utf-8", errors="replace")
        # Strip tags
        raw = re.sub(r"<script[^>]*>.*?</script>", "", raw, flags=re.DOTALL)
        raw = re.sub(r"<style[^>]*>.*?</style>", "", raw, flags=re.DOTALL)
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = re.sub(r"  +", " ", raw)
        return raw.strip()

    # .md / .txt / anything else
    return path.read_text(encoding="utf-8", errors="replace")


def truncate(text: str, max_chars: int = 12_000) -> str:
    """Trim source text to stay within token budget."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[...content truncated for token budget...]"


# ── Prompt builder ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = textwrap.dedent("""
You are an expert NCLEX NGN question writer. Your job is to read source material
provided by the user and produce a valid questions.json file for the NGN NCLEX Simulator.

RULES:
1. Output ONLY valid JSON — no markdown fences, no explanations, no prose.
2. The root object must match this structure exactly:
   {
     "id": "<slug>",
     "title": "<bank title>",
     "description": "<one line>",
     "version": "4.0",
     "questions": [ ...question objects... ]
   }
3. Every question must include ALL required fields from the schema below.
4. Distribute questions across layers: A, A-Applied, B, C, D, NGN.
5. Use all six types when count ≥ 6: MC, SATA, BOWTIE, MATRIX, TREND, CLOZE.
6. Bowtie ALWAYS: 1 condition (condition_count:1), 2 actions (action_count:2),
   2 parameters (param_count:2). Do not deviate.
7. Every question must have:
   - option_rationales (MC/SATA) OR cell_rationales (MATRIX) OR bowtie_rationales (BOWTIE)
   - source_reference citing the document name and topic
   - rationale explaining the correct answer
   - correct_answers matching the format for each type
8. Layer D questions must set interference_pair to the confusable concept pair name.
9. For TREND, correct_answers values must be one of: "Improving", "Worsening", "No change".
10. For CLOZE, sentence_parts is an array of strings and blank objects.

QUESTION FIELD SCHEMA (minimal required set per type):

MC/SATA:
  type, layer, layer_subtype, ngn, nclex_category, nclex_subcategory,
  concept_bucket, text, options {A:,B:,C:,D:}, correct_answers [list],
  option_rationales {A:,B:,C:,D:}, rationale, source_reference

BOWTIE:
  type:"BOWTIE", layer, layer_subtype, ngn:true,
  nclex_category, nclex_subcategory, concept_bucket,
  case_study (required), text,
  bowtie:{condition_options:[],condition_count:1,
          actions_to_take:[],action_count:2,
          parameters_to_monitor:[],param_count:2},
  correct_answers:{condition:"",actions:[],parameters:[]},
  bowtie_rationales:{condition:"",actions:"",parameters:""},
  rationale, source_reference

MATRIX:
  type:"MATRIX", layer, layer_subtype, ngn:true,
  nclex_category, nclex_subcategory, concept_bucket,
  case_study (optional), text,
  matrix:{columns:[],rows:[{id:"r1",label:"..."},...]},
  correct_answers:{r1:"ColName",...},
  cell_rationales:{r1:"...",r2:"..."},
  rationale, source_reference

TREND:
  type:"TREND", layer, layer_subtype, ngn:true,
  nclex_category, nclex_subcategory, concept_bucket,
  case_study (required), text,
  trend:{timepoints:[],data:[{label:"",values:[]},...],items:[{id:"",label:""}...]},
  correct_answers:{item_id:"Improving|Worsening|No change",...},
  rationale, source_reference

CLOZE:
  type:"CLOZE", layer, layer_subtype, ngn:true,
  nclex_category, nclex_subcategory, concept_bucket, text,
  cloze:{sentence_parts:[...strings and {blank_id,label,options:[]}...]},
  correct_answers:{b1:"...",b2:"..."},
  rationale, source_reference
""").strip()


def build_user_prompt(source_text: str, count: int, layers: list[str]) -> str:
    layer_str = ", ".join(layers)
    return textwrap.dedent(f"""
    SOURCE MATERIAL:
    ----------------
    {source_text}
    ----------------

    Generate exactly {count} NCLEX NGN questions from the source material above.
    Target these layers (distribute evenly): {layer_str}
    Use a variety of question types (MC, SATA, BOWTIE, MATRIX, TREND, CLOZE).
    All content must be grounded in the source — do not invent facts.
    Output ONLY the JSON object. No markdown. No explanation.
    """).strip()


# ── LLM call ──────────────────────────────────────────────────────────────────

def call_llm(source_text: str, count: int, layers: list[str],
             model: str = "gpt-4o") -> str:
    if not OPENAI_AVAILABLE:
        print("ERROR: openai package not installed. Run: pip install openai")
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        print("  Set it with:  export OPENAI_API_KEY=sk-...")
        sys.exit(1)

    base_url = os.environ.get("OPENAI_BASE_URL")  # optional Azure / local override
    client = OpenAI(api_key=api_key, **({"base_url": base_url} if base_url else {}))

    print(f"  Calling {model} (this may take 15–60 seconds)…")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": build_user_prompt(source_text, count, layers)},
        ],
        temperature=0.4,
        response_format={"type": "json_object"},
        max_tokens=4096,
    )
    return resp.choices[0].message.content


# ── Validation ────────────────────────────────────────────────────────────────

VALID_TYPES   = {"MC", "SATA", "BOWTIE", "MATRIX", "TREND", "CLOZE"}
VALID_LAYERS  = {"A", "A-Applied", "B", "C", "D", "NGN"}
TREND_OPTIONS = {"Improving", "Worsening", "No change"}


def validate_and_repair(bank: dict) -> tuple[dict, list[str]]:
    """
    Light validation + auto-repair pass.
    Returns (repaired_bank, list_of_warnings).
    """
    warnings = []
    questions = bank.get("questions", [])
    repaired  = []

    for i, q in enumerate(questions):
        qid = q.get("id", f"q{i+1}")

        # Type check
        qt = q.get("type", "")
        if qt not in VALID_TYPES:
            warnings.append(f"Q{i+1} ({qid}): unknown type '{qt}' — skipping")
            continue

        # Layer check
        lyr = q.get("layer", "")
        if lyr not in VALID_LAYERS:
            warnings.append(f"Q{i+1} ({qid}): unknown layer '{lyr}' — defaulting to 'C'")
            q["layer"] = "C"

        # NGN flag
        if qt in ("BOWTIE", "MATRIX", "TREND", "CLOZE"):
            q["ngn"] = True

        # Ensure id exists
        if not q.get("id"):
            q["id"] = f"gen-{i+1:03d}"

        # Bowtie: enforce 1/2/2 defaults
        if qt == "BOWTIE":
            bt = q.get("bowtie", {})
            bt.setdefault("condition_count", 1)
            bt.setdefault("action_count",    2)
            bt.setdefault("param_count",     2)
            q["bowtie"] = bt

        # Trend: validate correct_answers values
        if qt == "TREND":
            ca = q.get("correct_answers", {})
            for k, v in ca.items():
                if v not in TREND_OPTIONS:
                    warnings.append(
                        f"Q{i+1} ({qid}): TREND answer '{v}' for '{k}' "
                        f"not in {TREND_OPTIONS} — defaulting to 'No change'")
                    ca[k] = "No change"

        # Ensure required fields have at least empty values
        for field in ("rationale", "source_reference", "nclex_category",
                      "nclex_subcategory", "concept_bucket", "text"):
            if not q.get(field):
                q.setdefault(field, "")

        repaired.append(q)

    bank["questions"] = repaired
    return bank, warnings


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate a schema-valid questions.json from source documents.")
    parser.add_argument(
        "--sources", nargs="+", required=True,
        help="Paths to source files (PDF, HTML, .md, .txt)")
    parser.add_argument(
        "--out", default="generated_bank.json",
        help="Output path for the questions.json file (default: generated_bank.json)")
    parser.add_argument(
        "--count", type=int, default=8,
        help="Number of questions to generate (default: 8)")
    parser.add_argument(
        "--layers", nargs="+",
        default=["A", "A-Applied", "B", "C", "D", "NGN"],
        choices=["A", "A-Applied", "B", "C", "D", "NGN"],
        help="Which layers to include (default: all 6)")
    parser.add_argument(
        "--model", default="gpt-4o",
        help="OpenAI model to use (default: gpt-4o). gpt-4o-mini works too.")
    parser.add_argument(
        "--bank-id", default="generated",
        help="Bank ID slug in the output JSON (default: generated)")
    parser.add_argument(
        "--bank-title", default="Generated Question Bank",
        help="Bank title shown in the simulator home screen")
    parser.add_argument(
        "--max-chars", type=int, default=12_000,
        help="Max source characters sent to the LLM (default: 12,000)")
    args = parser.parse_args()

    # ── Extract text from all source files ──
    all_text = []
    for src in args.sources:
        p = Path(src)
        if not p.exists():
            print(f"ERROR: source file not found: {src}")
            sys.exit(1)
        print(f"  Reading {p.name}…")
        text = extract_text(p)
        all_text.append(f"=== {p.name} ===\n{text}")

    combined = "\n\n".join(all_text)
    combined = truncate(combined, args.max_chars)
    print(f"  Source text: {len(combined):,} chars → sending to LLM")

    # ── Call LLM ──
    raw_json = call_llm(combined, args.count, args.layers, model=args.model)

    # ── Parse ──
    try:
        bank = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"ERROR: LLM returned invalid JSON: {e}")
        print("  Raw response saved to: llm_raw_output.txt")
        Path("llm_raw_output.txt").write_text(raw_json)
        sys.exit(1)

    # ── If LLM returned just a questions array ──
    if isinstance(bank, list):
        bank = {
            "id":          args.bank_id,
            "title":       args.bank_title,
            "description": f"Generated from: {', '.join(Path(s).name for s in args.sources)}",
            "version":     "4.0",
            "questions":   bank,
        }

    # Ensure top-level fields
    bank.setdefault("id",          args.bank_id)
    bank.setdefault("title",       args.bank_title)
    bank.setdefault("description", f"Generated from: {', '.join(Path(s).name for s in args.sources)}")
    bank.setdefault("version",     "4.0")

    # ── Validate + repair ──
    bank, warnings = validate_and_repair(bank)

    if warnings:
        print(f"\n  Validation warnings ({len(warnings)}):")
        for w in warnings:
            print(f"    ⚠ {w}")

    # ── Write output ──
    out = Path(args.out)
    out.write_text(json.dumps(bank, indent=2, ensure_ascii=False))
    n = len(bank["questions"])
    print(f"\n  Done. {n} questions written to: {out.resolve()}")
    print(f"  Drop this file into your ngn_app_v4/ folder and click")
    print(f"  '🔄 Reload Question Banks' in the simulator sidebar.")


if __name__ == "__main__":
    main()

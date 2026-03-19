"""
grading.py — Question grading logic + dynamic miss-type inference.
"""
from config import LAYER_STOP_RULES, MISS_TYPE_LABELS


def grade_question(q, ans):
    """
    Returns: (earned_points, max_points, detail_dict)
    detail_dict varies by question type; always has 'inferred_miss_type' if wrong.
    """
    qt = q["type"]

    if qt in ("MC", "SATA"):
        correct = set(q["correct_answers"])
        user    = set(ans) if ans else set()

        if qt == "MC":
            pts = 1 if user == correct else 0
            d   = {"correct": correct, "user": user}
            if pts == 0:
                d["inferred_miss_type"] = _infer_mc_miss(q, user, correct)
            return pts, 1, d

        # SATA partial credit
        earned = max(0, sum(1 for x in user if x in correct)
                        - sum(1 for x in user if x not in correct))
        d = {"correct": correct, "user": user}
        if earned < len(correct):
            d["inferred_miss_type"] = _infer_sata_miss(q, user, correct)
        return earned, len(correct), d

    elif qt == "BOWTIE":
        ans = ans or {}
        ca  = q["correct_answers"]
        correct_cond   = ca.get("condition") or ca.get("cause", "")
        correct_actions= ca.get("actions")   or ca.get("action", [])
        correct_params = ca.get("parameters") or ca.get("outcome", "")
        user_cond   = ans.get("condition") or ans.get("cause", "")
        user_actions= ans.get("actions")   or ans.get("action", [])
        user_params = ans.get("parameters") or ans.get("outcome", "")
        if isinstance(correct_params, str): correct_params = [correct_params]
        if isinstance(user_params, str):    user_params    = [user_params]

        c_ok = user_cond == correct_cond
        a_ok = set(user_actions) == set(correct_actions)
        p_ok = set(user_params)  == set(correct_params)
        pts  = int(c_ok) + int(a_ok) + int(p_ok)
        d    = {
            "condition_ok":   c_ok,  "actions_ok":    a_ok, "parameters_ok": p_ok,
            "correct": {"condition": correct_cond, "actions": correct_actions,
                        "parameters": correct_params},
            "user":    {"condition": user_cond,    "actions": user_actions,
                        "parameters": user_params},
        }
        if pts < 3:
            d["inferred_miss_type"] = _infer_bowtie_miss(q, c_ok, a_ok, p_ok)
        return pts, 3, d

    elif qt in ("MATRIX", "TREND", "CLOZE"):
        ans = ans or {}
        cm  = q["correct_answers"]
        misses = {k: (ans.get(k), v) for k, v in cm.items() if ans.get(k) != v}
        earned = len(cm) - len(misses)
        d = {"correct": cm, "user": ans, "misses": misses}
        if misses:
            d["inferred_miss_type"] = _infer_table_miss(q, misses)
        return max(0, earned), len(cm), d

    return 0, 1, {}


# ── Miss-type inference helpers ──────────────────────────────────────────────

def _infer_mc_miss(q, user, correct):
    """Infer why a student got an MC wrong."""
    layer = q.get("layer", "")
    flags = q.get("miss_type_flags", [])
    if flags:
        return flags[0]
    if layer == "A":
        return "Fact gap"
    if layer == "A-Applied":
        return "Translation failure"
    if layer == "D":
        return "Distractor trap"
    if layer == "C":
        sub = q.get("layer_subtype", "")
        if "priority" in sub:
            return "Wrong priority schema"
    return "Distractor trap"


def _infer_sata_miss(q, user, correct):
    """Infer why a student got a SATA wrong."""
    extra = user - correct   # chose things they shouldn't have
    missed = correct - user  # didn't choose things they should have
    flags = q.get("miss_type_flags", [])
    if flags:
        return flags[0]
    if extra and not missed:
        return "Distractor trap"
    if missed and not extra:
        return "Fact gap"
    return "Distractor trap"


def _infer_bowtie_miss(q, c_ok, a_ok, p_ok):
    if not c_ok:
        return "Distractor trap"  # misidentified the condition
    if not a_ok:
        return "Wrong priority schema"
    if not p_ok:
        return "Fact gap"
    return "Distractor trap"


def _infer_table_miss(q, misses):
    flags = q.get("miss_type_flags", [])
    if flags:
        return flags[0]
    return "Fact gap"


# ── Result aggregation ────────────────────────────────────────────────────────

def aggregate_results(questions, answers_dict):
    """
    Grade all questions, return:
      total_earned, total_max, details (list of (q, earned, max, detail))
      layer_stats: {layer: [earned, max]}
      type_stats:  {type:  [earned, max]}
      missed_pairs: list of interference_pair strings that were missed
    """
    total_earned = 0
    total_max    = 0
    details      = []
    layer_stats  = {}
    type_stats   = {}
    missed_pairs = []

    for i, q in enumerate(questions):
        qid = f"{i}_{q.get('id', i)}"
        ans = answers_dict.get(qid)
        e, p, d = grade_question(q, ans)
        total_earned += e
        total_max    += p
        details.append((q, e, p, d))

        # Layer stats
        lyr = q.get("layer", "?")
        if lyr not in layer_stats:
            layer_stats[lyr] = [0, 0]
        layer_stats[lyr][0] += e
        layer_stats[lyr][1] += p

        # Type stats
        qt = q["type"]
        if qt not in type_stats:
            type_stats[qt] = [0, 0]
        type_stats[qt][0] += e
        type_stats[qt][1] += p

        # Interference pairs — track missed Layer D items
        if e < p and q.get("interference_pair"):
            missed_pairs.append(q["interference_pair"])

    return total_earned, total_max, details, layer_stats, type_stats, missed_pairs


def check_layer_readiness(layer, score_pct):
    """Return (is_ready, needed_pct)"""
    needed = LAYER_STOP_RULES.get(layer, 68)
    return score_pct >= needed, needed


def get_miss_explanation(miss_type):
    return MISS_TYPE_LABELS.get(miss_type, "Review this question's rationale carefully.")

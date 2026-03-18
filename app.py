"""
NGN NCLEX Simulator — Framework Edition
Supports: MC, SATA, Bowtie, Matrix Grid, Trend, Drag-and-Drop (Cloze)
Bowtie format: Condition (center) | Actions to Take (left) | Parameters to Monitor (right)
Layer badges, Study Mode filter, framework metadata display.
One question at a time. No going back. True NCLEX experience.
"""
import json
import time
import random
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="NGN NCLEX Simulator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #F0F2F6; }
[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #D4D1CA; }

/* Cards */
.case-card {
    background: #FFFDE7; border-left: 5px solid #F9A825;
    border-radius: 8px; padding: 1.2rem 1.4rem; margin-bottom: 1.2rem;
    font-size: 0.95rem; line-height: 1.7; color: #28251D;
}
.q-card {
    background: #FFFFFF; border: 1px solid #D4D1CA; border-radius: 10px;
    padding: 1.6rem 1.8rem; margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.q-text { font-size: 1.05rem; font-weight: 500; color: #1A1917; line-height: 1.65; }

/* Badges — question type */
.badge {
    display:inline-block; font-size:0.72rem; font-weight:700;
    padding:3px 10px; border-radius:100px; margin-bottom:0.6rem; margin-right:4px;
}
.badge-mc     { background:#EEF2FF; color:#3730A3; border:1px solid #C7D2FE; }
.badge-sata   { background:#E8F4F5; color:#01696F; border:1px solid #B3DADE; }
.badge-bowtie { background:#FEF3C7; color:#92400E; border:1px solid #FCD34D; }
.badge-matrix { background:#FCE7F3; color:#9D174D; border:1px solid #F9A8D4; }
.badge-trend  { background:#ECFDF5; color:#065F46; border:1px solid #6EE7B7; }
.badge-cloze  { background:#F5F3FF; color:#5B21B6; border:1px solid #C4B5FD; }
.badge-ngn    { background:#FFF1F2; color:#9F1239; border:1px solid #FDA4AF; }

/* Badges — framework layer */
.badge-layer-a       { background:#FEF9C3; color:#713F12; border:1px solid #FDE68A; }
.badge-layer-aa      { background:#FFF7ED; color:#9A3412; border:1px solid #FDBA74; }
.badge-layer-b       { background:#EFF6FF; color:#1E40AF; border:1px solid #BFDBFE; }
.badge-layer-c       { background:#F0FDF4; color:#14532D; border:1px solid #BBF7D0; }
.badge-layer-d       { background:#FDF4FF; color:#581C87; border:1px solid #E9D5FF; }
.badge-layer-ngn     { background:#FFF1F2; color:#9F1239; border:1px solid #FDA4AF; }

/* Timer */
.timer { background:#01696F; color:white; border-radius:8px; padding:0.5rem 1rem;
         font-size:1.15rem; font-weight:700; text-align:center; margin-bottom:1rem; }
.timer-warn { background:#B45309 !important; }
.timer-crit { background:#9D174D !important; }

/* Progress */
.prog-wrap { background:#E5E7EB; border-radius:100px; height:8px; margin:0.4rem 0 0.8rem; }
.prog-fill  { background:#01696F; height:8px; border-radius:100px; }

/* Bowtie */
.bowtie-col  { background:#F8FAFC; border:1px solid #CBD5E1; border-radius:8px; padding:0.8rem; }
.bowtie-center-col { background:#FFFBEB; border:2px solid #FCD34D; border-radius:8px; padding:0.8rem; text-align:center; }
.bowtie-label { font-weight:700; font-size:0.85rem; color:#475569; margin-bottom:0.6rem; text-transform:uppercase; letter-spacing:0.04em; }

/* Matrix */
.matrix-table { width:100%; border-collapse:collapse; margin-top:0.8rem; }
.matrix-table th { background:#F1F5F9; padding:10px 14px; text-align:center;
                   font-size:0.85rem; font-weight:600; color:#334155;
                   border:1px solid #CBD5E1; }
.matrix-table td { padding:10px 14px; border:1px solid #E2E8F0; font-size:0.92rem; color:#1E293B; }
.matrix-table tr:hover td { background:#F8FAFC; }

/* Trend */
.trend-table { width:100%; border-collapse:collapse; margin:0.8rem 0; }
.trend-table th { background:#ECFDF5; padding:9px 14px; text-align:center;
                  font-size:0.82rem; font-weight:700; color:#065F46; border:1px solid #A7F3D0; }
.trend-table td { padding:9px 14px; border:1px solid #D1FAE5; font-size:0.9rem; color:#1E293B; text-align:center; }
.trend-table .highlight { background:#FEF9C3; font-weight:600; }

/* Drag-and-drop (cloze) */
.cloze-sentence { font-size:1.05rem; line-height:2.2; color:#1E293B; }
.blank-box { display:inline-block; min-width:160px; background:#EEF2FF;
             border:2px dashed #6366F1; border-radius:6px; padding:2px 10px;
             margin:0 4px; font-weight:600; color:#3730A3; }

/* Results */
.score-card { background:#FFF; border:1px solid #D4D1CA; border-radius:12px;
              padding:2rem; text-align:center; margin-bottom:1.5rem; }
.score-pass { border-top:5px solid #059669; }
.score-fail { border-top:5px solid #DC2626; }
.score-num  { font-size:3.5rem; font-weight:800; line-height:1; }
.score-pass .score-num { color:#059669; }
.score-fail .score-num { color:#DC2626; }

.rat-correct   { background:#F0FDF4; border-left:4px solid #059669; border-radius:6px; padding:0.8rem 1rem; margin-top:0.6rem; font-size:0.9rem; }
.rat-incorrect { background:#FFF1F2; border-left:4px solid #DC2626; border-radius:6px; padding:0.8rem 1rem; margin-top:0.6rem; font-size:0.9rem; }

/* Framework metadata panel */
.meta-panel { background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px;
              padding:0.7rem 1rem; margin-top:0.8rem; font-size:0.82rem; color:#475569; }
.meta-label { font-weight:700; color:#334155; }

/* Buttons */
.stButton>button { background:#01696F; color:#FFF; border:none; border-radius:8px;
                   padding:0.55rem 1.6rem; font-weight:600; font-size:0.95rem; }
.stButton>button:hover { background:#0C4E54; color:#FFF; }
#MainMenu, footer, header { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ─── LAYER CONFIG ─────────────────────────────────────────────────────────────
LAYER_INFO = {
    "A":       {"label": "Layer A — Recall",          "cls": "badge-layer-a",   "desc": "Verbatim Tier 1 fact retrieval"},
    "A-Applied":{"label": "Layer A-Applied — Translation","cls":"badge-layer-aa","desc": "Tier 1 facts in exam disguise"},
    "B":       {"label": "Layer B — Mechanism",       "cls": "badge-layer-b",   "desc": "Why the rule exists (physiology)"},
    "C":       {"label": "Layer C — Clinical Judgment","cls": "badge-layer-c",   "desc": "Core NCLEX clinical reasoning"},
    "D":       {"label": "Layer D — Interference",    "cls": "badge-layer-d",   "desc": "Cross-bucket confusion pairs"},
    "NGN":     {"label": "NGN Format",                "cls": "badge-layer-ngn", "desc": "Next Generation NCLEX item type"},
}

LAYER_STOP_RULES = {
    "A": 95, "A-Applied": 90, "C": 90, "D": 85,
}

# ─── DATA ────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    for p in [
        Path(__file__).parent / "questions.json",
        Path(__file__).parent.parent / "questions.json",
    ]:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return []

data = load_data()
BANKS = {b["id"]: b for b in data}

# ─── SESSION STATE ────────────────────────────────────────────────────────────
def init():
    defaults = {
        "screen": "home",
        "bank_id": None,
        "questions": [],
        "idx": 0,
        "answers": {},
        "locked": {},
        "start_time": None,
        "timer_min": 90,
        "elapsed": 0,
        "shuffle": True,
        "study_layer": "All Layers",
        "show_meta": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def fmt_time(s):
    m, s = divmod(int(max(0, s)), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def remaining():
    if not st.session_state.start_time:
        return st.session_state.timer_min * 60
    return max(0, st.session_state.timer_min * 60 - (time.time() - st.session_state.start_time))

def start_test(bank_id, q_count, shuffle, timer_min, layer_filter):
    bank = BANKS[bank_id]
    qs = list(bank["questions"])
    if layer_filter != "All Layers":
        qs = [q for q in qs if q.get("layer") == layer_filter]
        if not qs:
            st.warning(f"No questions found for layer '{layer_filter}'. Loading all layers.")
            qs = list(bank["questions"])
    if shuffle:
        random.shuffle(qs)
    qs = qs[:q_count]
    st.session_state.update({
        "screen": "test", "bank_id": bank_id, "questions": qs,
        "idx": 0, "answers": {}, "locked": {},
        "start_time": time.time(), "timer_min": timer_min,
        "shuffle": shuffle, "study_layer": layer_filter,
    })

def go_home():
    st.session_state.update({
        "screen": "home", "answers": {}, "locked": {}, "start_time": None,
    })

def render_layer_badge(q):
    layer = q.get("layer", "")
    subtype = q.get("layer_subtype", "")
    info = LAYER_INFO.get(layer, {})
    if info:
        cls = info["cls"]
        label = info["label"]
        html = f'<span class="badge {cls}">{label}</span>'
        if subtype:
            html += f'<span class="badge" style="background:#F1F5F9;color:#475569;border:1px solid #CBD5E1;">{subtype}</span>'
        return html
    return ""

def render_meta_panel(q):
    if not st.session_state.get("show_meta", True):
        return ""
    parts = []
    if q.get("nclex_category"):
        parts.append(f'<span class="meta-label">NCLEX Category:</span> {q["nclex_category"]}')
    if q.get("nclex_subcategory"):
        parts.append(f'<span class="meta-label">Subcategory:</span> {q["nclex_subcategory"]}')
    if q.get("concept_bucket"):
        parts.append(f'<span class="meta-label">Concept:</span> {q["concept_bucket"]}')
    if q.get("interference_pair"):
        parts.append(f'<span class="meta-label">Interference Pair:</span> {q["interference_pair"]}')
    if parts:
        return '<div class="meta-panel">' + " &nbsp;·&nbsp; ".join(parts) + '</div>'
    return ""

# ─── GRADING ─────────────────────────────────────────────────────────────────
def grade_question(q, ans):
    qt = q["type"]

    if qt in ("MC", "SATA"):
        correct = set(q["correct_answers"])
        user    = set(ans) if ans else set()
        if qt == "MC":
            earned = 1 if user == correct else 0
            return earned, 1, {"correct": correct, "user": user}
        else:  # SATA partial credit
            pts = sum(1 for x in user if x in correct) - sum(1 for x in user if x not in correct)
            possible = len(correct)
            earned = max(0, pts)
            return earned, possible, {"correct": correct, "user": user}

    elif qt == "BOWTIE":
        # New framework format: condition + actions (2) + parameters (2)
        if not ans:
            ans = {}
        ca = q["correct_answers"]
        condition_ok  = ans.get("condition", "") == ca.get("condition", "")
        actions_ok    = set(ans.get("actions", [])) == set(ca.get("actions", []))
        parameters_ok = set(ans.get("parameters", [])) == set(ca.get("parameters", []))
        earned   = int(condition_ok) + int(actions_ok) + int(parameters_ok)
        possible = 3
        return earned, possible, {
            "condition_ok": condition_ok,
            "actions_ok": actions_ok,
            "parameters_ok": parameters_ok,
            "correct": ca, "user": ans
        }

    elif qt == "MATRIX":
        if not ans:
            ans = {}
        correct_map = q["correct_answers"]
        earned   = sum(1 for r, c in correct_map.items() if ans.get(r) == c)
        possible = len(correct_map)
        return earned, possible, {"correct": correct_map, "user": ans}

    elif qt == "TREND":
        if not ans:
            ans = {}
        correct_map = q["correct_answers"]
        earned   = sum(1 for k, v in correct_map.items() if ans.get(k) == v)
        possible = len(correct_map)
        return earned, possible, {"correct": correct_map, "user": ans}

    elif qt == "CLOZE":
        if not ans:
            ans = {}
        correct_map = q["correct_answers"]
        earned   = sum(1 for k, v in correct_map.items() if ans.get(k) == v)
        possible = len(correct_map)
        return earned, possible, {"correct": correct_map, "user": ans}

    return 0, 1, {}

# ─── QUESTION TYPE RENDERERS ─────────────────────────────────────────────────

def render_mc(q, qid, locked):
    opts = q["options"]
    keys = sorted(opts.keys())
    cur  = st.session_state.answers.get(qid, [])
    cur_val = cur[0] if cur else None

    if locked:
        for k in keys:
            sel = k == cur_val
            icon = "◉" if sel else "○"
            color = "#01696F" if sel else "#6B7280"
            st.markdown(f'<div style="padding:5px 0;color:{color};">{icon} <b>{k}.</b> {opts[k]}</div>',
                        unsafe_allow_html=True)
    else:
        idx_default = keys.index(cur_val) if cur_val in keys else None
        choice = st.radio("", keys, index=idx_default,
                          format_func=lambda k: f"{k}.  {opts[k]}",
                          key=f"mc_{qid}", label_visibility="collapsed")
        st.session_state.answers[qid] = [choice] if choice else []

def render_sata(q, qid, locked):
    opts = q["options"]
    keys = sorted(opts.keys())
    cur  = st.session_state.answers.get(qid, [])

    st.markdown('<div style="color:#01696F;font-size:0.88rem;font-weight:600;margin-bottom:0.4rem;">Select ALL that apply</div>',
                unsafe_allow_html=True)
    if locked:
        for k in keys:
            sel = k in cur
            icon = "☑" if sel else "☐"
            color = "#01696F" if sel else "#6B7280"
            st.markdown(f'<div style="padding:4px 0;color:{color};">{icon} <b>{k}.</b> {opts[k]}</div>',
                        unsafe_allow_html=True)
    else:
        selected = st.multiselect("", keys, default=cur,
                                  format_func=lambda k: f"{k}.  {opts[k]}",
                                  key=f"sata_{qid}", label_visibility="collapsed")
        st.session_state.answers[qid] = selected

def render_bowtie(q, qid, locked):
    """
    Framework-aligned Bowtie:
    Left column  = Actions to Take (select 2 of 5)
    Center       = Condition (select 1 of 4-5)
    Right column = Parameters to Monitor (select 2 of 5)
    """
    bt = q["bowtie"]
    condition_opts  = bt.get("condition_options", [])
    actions_opts    = bt.get("actions_to_take", [])
    parameters_opts = bt.get("parameters_to_monitor", [])
    cur = st.session_state.answers.get(qid, {})

    st.markdown("""
    <div style="background:#FFFBEB;border:1px solid #FCD34D;border-radius:8px;padding:0.8rem 1rem;margin-bottom:1rem;font-size:0.88rem;color:#78350F;">
    <strong>Bowtie Item:</strong> Select the most likely <em>condition</em> (center), the <em>2 priority actions to take</em> (left), and the <em>2 parameters to monitor</em> (right).
    </div>
    """, unsafe_allow_html=True)

    col_left, col_mid, col_right = st.columns([5, 4, 5])

    # ── Left: Actions to Take ──
    with col_left:
        st.markdown('<div class="bowtie-label">Actions to Take (Select 2)</div>', unsafe_allow_html=True)
        if locked:
            chosen_actions = cur.get("actions", [])
            for a in actions_opts:
                sel = a in chosen_actions
                icon = "☑" if sel else "☐"
                color = "#01696F" if sel else "#6B7280"
                st.markdown(f'<div style="padding:4px 0;color:{color};font-size:0.92rem;">{icon} {a}</div>',
                            unsafe_allow_html=True)
        else:
            chosen_actions = st.multiselect("", actions_opts,
                                            default=cur.get("actions", []),
                                            key=f"bt_actions_{qid}",
                                            label_visibility="collapsed",
                                            max_selections=2)
            cur["actions"] = chosen_actions
            st.session_state.answers[qid] = cur

    # ── Center: Condition ──
    with col_mid:
        st.markdown('<div class="bowtie-label" style="text-align:center;">Condition (Select 1)</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;font-size:1.8rem;color:#94A3B8;margin-bottom:0.4rem;">⟵ ⟶</div>', unsafe_allow_html=True)
        if locked:
            chosen_cond = cur.get("condition", "")
            for c in condition_opts:
                icon = "◉" if c == chosen_cond else "○"
                color = "#92400E" if c == chosen_cond else "#6B7280"
                st.markdown(f'<div style="padding:4px 0;color:{color};font-size:0.9rem;">{icon} {c}</div>',
                            unsafe_allow_html=True)
        else:
            chosen_cond = st.radio("", condition_opts,
                                   index=condition_opts.index(cur["condition"]) if cur.get("condition") in condition_opts else None,
                                   key=f"bt_cond_{qid}", label_visibility="collapsed")
            cur["condition"] = chosen_cond
            st.session_state.answers[qid] = cur

    # ── Right: Parameters to Monitor ──
    with col_right:
        st.markdown('<div class="bowtie-label">Parameters to Monitor (Select 2)</div>', unsafe_allow_html=True)
        if locked:
            chosen_params = cur.get("parameters", [])
            for p in parameters_opts:
                sel = p in chosen_params
                icon = "☑" if sel else "☐"
                color = "#065F46" if sel else "#6B7280"
                st.markdown(f'<div style="padding:4px 0;color:{color};font-size:0.92rem;">{icon} {p}</div>',
                            unsafe_allow_html=True)
        else:
            chosen_params = st.multiselect("", parameters_opts,
                                           default=cur.get("parameters", []),
                                           key=f"bt_params_{qid}",
                                           label_visibility="collapsed",
                                           max_selections=2)
            cur["parameters"] = chosen_params
            st.session_state.answers[qid] = cur

def render_matrix(q, qid, locked):
    rows    = q["matrix"]["rows"]
    columns = q["matrix"]["columns"]
    cur     = st.session_state.answers.get(qid, {})

    st.markdown("""
    <div style="background:#FDF4FF;border:1px solid #E879F9;border-radius:8px;padding:0.8rem 1rem;margin-bottom:1rem;font-size:0.88rem;color:#701A75;">
    <strong>Matrix Grid:</strong> For each row, select the most appropriate response column.
    </div>
    """, unsafe_allow_html=True)

    header_html = "<table class='matrix-table'><tr><th style='text-align:left;width:40%;'>Assessment Finding</th>"
    for col in columns:
        header_html += f"<th>{col}</th>"
    header_html += "</tr>"
    st.markdown(header_html, unsafe_allow_html=True)

    for row in rows:
        row_id = row["id"]
        row_label = row["label"]
        cols_st = st.columns([4] + [1] * len(columns))
        cols_st[0].markdown(f"**{row_label}**")
        if locked:
            chosen = cur.get(row_id, "")
            for i, col in enumerate(columns):
                icon = "◉" if chosen == col else "○"
                cols_st[i+1].markdown(f'<div style="text-align:center;font-size:1.3rem;color:{"#01696F" if chosen==col else "#D1D5DB"};">{icon}</div>',
                                      unsafe_allow_html=True)
        else:
            for i, col in enumerate(columns):
                checked = cur.get(row_id) == col
                if cols_st[i+1].checkbox("", value=checked, key=f"mat_{qid}_{row_id}_{col}",
                                          label_visibility="collapsed"):
                    cur[row_id] = col
                    st.session_state.answers[qid] = cur

def render_trend(q, qid, locked):
    trend_data = q["trend"]["data"]
    timepoints = q["trend"]["timepoints"]
    items      = q["trend"]["items"]
    cur        = st.session_state.answers.get(qid, {})
    options    = ["Improving", "Worsening", "No change"]

    st.markdown("""
    <div style="background:#ECFDF5;border:1px solid #6EE7B7;border-radius:8px;padding:0.8rem 1rem;margin-bottom:1rem;font-size:0.88rem;color:#065F46;">
    <strong>Trend Item:</strong> Review the client data over time and select whether each parameter is improving, worsening, or showing no change.
    </div>
    """, unsafe_allow_html=True)

    header = "<table class='trend-table'><tr><th style='text-align:left;'>Parameter</th>"
    for tp in timepoints:
        header += f"<th>{tp}</th>"
    header += "</tr>"
    rows_html = ""
    for row in trend_data:
        rows_html += f"<tr><td><strong>{row['label']}</strong></td>"
        for i, val in enumerate(row["values"]):
            cls = "highlight" if i == len(row["values"]) - 1 else ""
            rows_html += f"<td class='{cls}'>{val}</td>"
        rows_html += "</tr>"
    st.markdown(header + rows_html + "</table>", unsafe_allow_html=True)

    st.markdown("**For each item below, select the trend:**")
    for item in items:
        item_id = item["id"]
        label   = item["label"]
        col1, col2 = st.columns([3, 2])
        col1.markdown(f"**{label}**")
        if locked:
            col2.markdown(f'<span style="font-weight:600;color:#01696F;">{cur.get(item_id, "—")}</span>',
                          unsafe_allow_html=True)
        else:
            idx_def = options.index(cur[item_id]) if cur.get(item_id) in options else None
            choice = col2.selectbox("", options, index=idx_def,
                                    key=f"trend_{qid}_{item_id}", label_visibility="collapsed")
            cur[item_id] = choice
            st.session_state.answers[qid] = cur

def render_cloze(q, qid, locked):
    sentence_parts = q["cloze"]["sentence_parts"]
    cur = st.session_state.answers.get(qid, {})

    st.markdown("""
    <div style="background:#F5F3FF;border:1px solid #C4B5FD;border-radius:8px;padding:0.8rem 1rem;margin-bottom:1rem;font-size:0.88rem;color:#4C1D95;">
    <strong>Drop-Down / Cloze:</strong> Complete the sentence by selecting the best answer for each blank.
    </div>
    """, unsafe_allow_html=True)

    for part in sentence_parts:
        if isinstance(part, str):
            st.markdown(f'<span style="font-size:1.05rem;">{part}</span>', unsafe_allow_html=True)
        elif isinstance(part, dict):
            blank_id = part["blank_id"]
            opts     = part["options"]
            label    = part.get("label", f"Blank {blank_id}")
            if locked:
                val = cur.get(blank_id, "___")
                st.markdown(f'<span class="blank-box">{val}</span>', unsafe_allow_html=True)
            else:
                idx_def = opts.index(cur[blank_id]) if cur.get(blank_id) in opts else None
                col1, col2 = st.columns([1, 3])
                col1.markdown(f"**{label}:**")
                choice = col2.selectbox("", opts, index=idx_def,
                                        key=f"cloze_{qid}_{blank_id}", label_visibility="collapsed")
                cur[blank_id] = choice
                st.session_state.answers[qid] = cur

# ─── ANSWER COMPLETENESS CHECK ───────────────────────────────────────────────
def is_answered(q, qid):
    ans = st.session_state.answers.get(qid)
    qt  = q["type"]
    if qt in ("MC", "SATA"):
        return bool(ans)
    elif qt == "BOWTIE":
        if not ans:
            return False
        return (bool(ans.get("condition"))
                and len(ans.get("actions", [])) == 2
                and len(ans.get("parameters", [])) == 2)
    elif qt in ("MATRIX", "TREND", "CLOZE"):
        if not ans:
            return False
        if qt == "MATRIX":
            return len(ans) >= len(q["matrix"]["rows"])
        elif qt == "TREND":
            return len(ans) >= len(q["trend"]["items"])
        elif qt == "CLOZE":
            blanks = [p for p in q["cloze"]["sentence_parts"] if isinstance(p, dict)]
            return len(ans) >= len(blanks)
    return False

# ─── HOME ─────────────────────────────────────────────────────────────────────
def render_home():
    st.markdown("## 🏥 NGN NCLEX Simulator")
    st.markdown("*Next Generation NCLEX — Framework Edition · All 6 Question Types*")

    type_cols = st.columns(6)
    badges = [
        ("MC", "badge-mc", "Multiple Choice"),
        ("SATA", "badge-sata", "Select All"),
        ("BOWTIE", "badge-bowtie", "Bowtie"),
        ("MATRIX", "badge-matrix", "Matrix Grid"),
        ("TREND", "badge-trend", "Trend"),
        ("CLOZE", "badge-cloze", "Drag & Drop"),
    ]
    for col, (code, cls, label) in zip(type_cols, badges):
        col.markdown(f'<div class="badge {cls}" style="width:100%;text-align:center;">{label}</div>',
                     unsafe_allow_html=True)

    st.markdown("---")

    if not BANKS:
        st.error("No question banks loaded. Make sure questions.json is in the same folder as app.py.")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Question Banks")
        for bid, bank in BANKS.items():
            type_counts = {}
            layer_counts = {}
            for q in bank["questions"]:
                type_counts[q["type"]] = type_counts.get(q["type"], 0) + 1
                layer = q.get("layer", "?")
                layer_counts[layer] = layer_counts.get(layer, 0) + 1
            type_summary  = " · ".join(f"{v} {k}" for k, v in type_counts.items())
            layer_summary = " · ".join(f"L{k}: {v}" for k, v in sorted(layer_counts.items()))

            st.markdown(f"""
            <div class="q-card" style="padding:1rem 1.4rem;">
                <strong style="font-size:1rem;">{bank['title']}</strong>
                <div style="color:#6B7280;font-size:0.83rem;margin-top:3px;">
                    {bank['question_count']} questions &nbsp;·&nbsp; {type_summary}
                </div>
                <div style="color:#9CA3AF;font-size:0.80rem;">Layers: {layer_summary}</div>
                <div style="color:#6B7280;font-size:0.83rem;">{bank.get('description','')}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Start: {bank['title']}", key=f"start_{bid}"):
                start_test(
                    bid,
                    st.session_state.get(f"qc_{bid}", min(75, bank['question_count'])),
                    st.session_state.get(f"sh_{bid}", True),
                    st.session_state.get(f"tm_{bid}", 90),
                    st.session_state.get(f"layer_{bid}", "All Layers"),
                )
                st.rerun()

    with col2:
        st.markdown("### Configure")
        if BANKS:
            sel_bid = st.selectbox("Bank", list(BANKS.keys()),
                                   format_func=lambda x: BANKS[x]["title"])
            bank = BANKS[sel_bid]

            # Layer filter
            available_layers = sorted(set(q.get("layer","?") for q in bank["questions"]))
            layer_options = ["All Layers"] + available_layers
            st.selectbox("Study Mode (Filter by Layer)", layer_options, key=f"layer_{sel_bid}",
                         help="Filter questions by framework layer for targeted practice")

            max_q = bank["question_count"]
            layer_sel = st.session_state.get(f"layer_{sel_bid}", "All Layers")
            if layer_sel != "All Layers":
                max_q = max(1, sum(1 for q in bank["questions"] if q.get("layer") == layer_sel))
            st.slider("Questions", 1, max_q, min(75, max_q), key=f"qc_{sel_bid}")
            st.slider("Time (min)", 30, 180, 90, step=15, key=f"tm_{sel_bid}")
            st.checkbox("Shuffle", value=True, key=f"sh_{sel_bid}")
            st.checkbox("Show Metadata (category/concept)", value=True, key="show_meta")

        st.markdown("---")

        # Layer legend
        st.markdown("**Framework Layers:**")
        for key, info in LAYER_INFO.items():
            if key in ("A", "A-Applied", "B", "C", "D"):
                st.markdown(f'<span class="badge {info["cls"]}">{key}</span> {info["desc"]}',
                            unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("""
**Stop Rules (mastery thresholds):**
- Layer A ≥ 95%
- Layer A-Applied ≥ 90%
- Layer C ≥ 90%
- Layer D ≥ 85%
- Pass score: 68% (NCLEX standard)
        """)

# ─── TEST SCREEN ──────────────────────────────────────────────────────────────
def render_test():
    qs = st.session_state.questions
    if not qs:
        go_home(); st.rerun(); return

    bid   = st.session_state.bank_id
    bank  = BANKS[bid]
    idx   = st.session_state.idx
    total = len(qs)
    rem   = remaining()
    total_sec = st.session_state.timer_min * 60
    pct_time  = rem / total_sec

    if rem <= 0:
        st.session_state.elapsed = total_sec
        st.session_state.screen  = "results"
        st.rerun(); return

    q   = qs[idx]
    qid = f"{idx}_{q.get('id', idx)}"
    locked = st.session_state.locked.get(qid, False)

    tcls = "timer" + (" timer-crit" if pct_time < 0.10 else " timer-warn" if pct_time < 0.25 else "")

    # ─ Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"## {bank['title']}")
        layer_mode = st.session_state.get("study_layer", "All Layers")
        if layer_mode != "All Layers":
            layer_info = LAYER_INFO.get(layer_mode, {})
            st.markdown(f'<span class="badge {layer_info.get("cls","")}">{layer_info.get("label","")}</span>',
                        unsafe_allow_html=True)
        st.markdown(f'<div class="{tcls}">⏱ {fmt_time(rem)}</div>', unsafe_allow_html=True)
        done = len(st.session_state.locked)
        pct_done = done / total * 100
        st.markdown(f"**Q {idx+1} / {total}**")
        st.markdown(f"""
        <div class="prog-wrap"><div class="prog-fill" style="width:{pct_done:.1f}%"></div></div>
        <div style="color:#6B7280;font-size:0.8rem;">{done} answered · {total-done} remaining</div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("*No going back — just like the real NCLEX.*")
        st.markdown("---")
        if st.button("Abandon Test"):
            go_home(); st.rerun()

    # ─ Case study banner ──────────────────────────────────────────────────────
    if q.get("case_study"):
        st.markdown(f'<div class="case-card"><strong>📋 Clinical Scenario</strong><br><br>{q["case_study"]}</div>',
                    unsafe_allow_html=True)

    # ─ Question header ────────────────────────────────────────────────────────
    qt = q["type"]
    badge_map = {"MC":"badge-mc Multiple Choice","SATA":"badge-sata Select All That Apply",
                 "BOWTIE":"badge-bowtie Bowtie","MATRIX":"badge-matrix Matrix Grid",
                 "TREND":"badge-trend Trend","CLOZE":"badge-cloze Drop-Down / Cloze"}
    badge_str = badge_map.get(qt, "badge-ngn NGN")
    badge_cls, badge_label = badge_str.split(" ", 1)

    if q.get("ngn"):
        st.markdown('<span class="badge badge-ngn">NGN</span>', unsafe_allow_html=True)

    layer_badge_html = render_layer_badge(q)
    meta_html = render_meta_panel(q) if st.session_state.get("show_meta", True) else ""

    st.markdown(f"""
    <div class="q-card">
        <div style="color:#6B7280;font-size:0.82rem;margin-bottom:0.3rem;">Question {idx+1} of {total}</div>
        <span class="badge {badge_cls}">{badge_label}</span>
        {layer_badge_html}
        <div class="q-text">{q["text"]}</div>
        {meta_html}
    </div>
    """, unsafe_allow_html=True)

    # ─ Render by type ─────────────────────────────────────────────────────────
    if qt == "MC":
        render_mc(q, qid, locked)
    elif qt == "SATA":
        render_sata(q, qid, locked)
    elif qt == "BOWTIE":
        render_bowtie(q, qid, locked)
    elif qt == "MATRIX":
        render_matrix(q, qid, locked)
    elif qt == "TREND":
        render_trend(q, qid, locked)
    elif qt == "CLOZE":
        render_cloze(q, qid, locked)

    # ─ Navigation ─────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    answered = is_answered(q, qid)
    is_last  = (idx == total - 1)

    col_btn, col_warn = st.columns([2, 3])
    with col_btn:
        btn_label = "Submit Test ✓" if is_last else "Next Question →"
        if st.button(btn_label, disabled=(not answered and not locked)):
            if not locked:
                st.session_state.locked[qid] = True
            if is_last:
                st.session_state.elapsed = total_sec - rem
                st.session_state.screen  = "results"
            else:
                st.session_state.idx += 1
            st.rerun()

    with col_warn:
        if not answered and not locked:
            st.markdown("""
            <div style="color:#B45309;font-size:0.88rem;padding-top:0.6rem;">
            ⚠️ Answer all parts before continuing
            </div>""", unsafe_allow_html=True)

# ─── RESULTS ─────────────────────────────────────────────────────────────────
def render_results():
    qs      = st.session_state.questions
    bid     = st.session_state.bank_id
    bank    = BANKS[bid]
    elapsed = st.session_state.get("elapsed", 0)

    total_earned   = 0
    total_possible = 0
    details = []

    for i, q in enumerate(qs):
        qid = f"{i}_{q.get('id', i)}"
        ans = st.session_state.answers.get(qid)
        earned, possible, detail = grade_question(q, ans)
        total_earned   += earned
        total_possible += possible
        details.append((q, earned, possible, detail))

    pct    = (total_earned / total_possible * 100) if total_possible else 0
    passed = pct >= 68

    # ─ Layer breakdown ────────────────────────────────────────────────────────
    layer_stats = {}
    for q, earned, possible, _ in details:
        lyr = q.get("layer", "?")
        if lyr not in layer_stats:
            layer_stats[lyr] = [0, 0]
        layer_stats[lyr][0] += earned
        layer_stats[lyr][1] += possible

    with st.sidebar:
        st.markdown("## Results")
        st.metric("Score",   f"{pct:.1f}%")
        st.metric("Points",  f"{total_earned} / {total_possible}")
        st.metric("Time",    fmt_time(elapsed))
        st.markdown("---")
        st.markdown("**By Layer:**")
        for lyr, (e, p) in sorted(layer_stats.items()):
            lyr_pct = f"{e/p*100:.0f}%" if p else "—"
            threshold = LAYER_STOP_RULES.get(lyr, 68)
            met = (e/p*100 >= threshold) if p else False
            icon = "✅" if met else "⚠️"
            st.markdown(f"{icon} **{lyr}**: {e}/{p} ({lyr_pct}) — need {threshold}%")
        st.markdown("---")
        if st.button("Try Again"):
            start_test(bid, len(qs), st.session_state.shuffle,
                       st.session_state.timer_min,
                       st.session_state.get("study_layer", "All Layers"))
            st.rerun()
        if st.button("Home"):
            go_home(); st.rerun()

    pass_label = "PASSED ✓" if passed else "NEEDS MORE PRACTICE"
    pass_color = "#059669" if passed else "#DC2626"
    card_cls   = "score-card score-pass" if passed else "score-card score-fail"

    st.markdown("## Your Results")
    st.markdown(f"""
    <div class="{card_cls}">
        <div class="score-num">{pct:.1f}%</div>
        <div style="font-size:1.1rem;font-weight:700;color:{pass_color};margin-top:0.4rem;">{pass_label}</div>
        <div style="color:#6B7280;font-size:0.88rem;margin-top:0.3rem;">
            {total_earned} / {total_possible} points &nbsp;·&nbsp; {fmt_time(elapsed)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ─ Breakdown by type ──────────────────────────────────────────────────────
    type_stats = {}
    for q, earned, possible, _ in details:
        t = q["type"]
        if t not in type_stats:
            type_stats[t] = [0, 0]
        type_stats[t][0] += earned
        type_stats[t][1] += possible

    type_cols = st.columns(len(type_stats))
    for col, (t, (e, p)) in zip(type_cols, type_stats.items()):
        col.metric(t, f"{e}/{p}", f"{e/p*100:.0f}%" if p else "—")

    # ─ Layer mastery check ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Layer Mastery Check")
    layer_cols = st.columns(max(1, len(layer_stats)))
    for col, (lyr, (e, p)) in zip(layer_cols, sorted(layer_stats.items())):
        threshold = LAYER_STOP_RULES.get(lyr, 68)
        lyr_pct = e/p*100 if p else 0
        met = lyr_pct >= threshold
        info = LAYER_INFO.get(lyr, {"label": lyr, "cls": "badge-ngn"})
        color = "#059669" if met else "#DC2626"
        col.markdown(
            f'<div style="background:#FFF;border:1px solid #E5E7EB;border-radius:8px;padding:0.8rem;text-align:center;">'
            f'<div class="badge {info["cls"]}">{lyr}</div>'
            f'<div style="font-size:1.6rem;font-weight:800;color:{color};">{lyr_pct:.0f}%</div>'
            f'<div style="font-size:0.78rem;color:#6B7280;">Need {threshold}% · {"✅ Met" if met else "⚠️ Below"}</div>'
            f'</div>', unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("### Answer Review & Rationales")
    filt = st.radio("Show:", ["All", "Incorrect / Partial", "Full Credit Only"], horizontal=True)

    for i, (q, earned, possible, detail) in enumerate(details):
        is_full = (earned == possible)
        is_zero = (earned == 0)
        if filt == "Incorrect / Partial" and is_full: continue
        if filt == "Full Credit Only" and not is_full: continue

        icon = "✅" if is_full else ("❌" if is_zero else "⚠️")
        score_str = f"{earned}/{possible} pts"
        qt = q["type"]
        layer = q.get("layer","")
        concept = q.get("concept_bucket","")
        layer_info = LAYER_INFO.get(layer, {})
        layer_cls = layer_info.get("cls","badge-ngn")

        with st.expander(f"{icon} Q{i+1} [{qt}] — {score_str} — {q['text'][:70]}..."):
            # Layer + metadata
            subtype = q.get("layer_subtype","")
            col_l, col_r = st.columns([3,2])
            with col_l:
                st.markdown(
                    f'<span class="badge {layer_cls}">{layer}</span>'
                    + (f'<span class="badge" style="background:#F1F5F9;color:#475569;border:1px solid #CBD5E1;">{subtype}</span>' if subtype else "")
                    + (f'<span class="badge" style="background:#F8FAFC;color:#64748B;border:1px solid #E2E8F0;">{concept}</span>' if concept else ""),
                    unsafe_allow_html=True
                )
            with col_r:
                nclex_cat = q.get("nclex_category","")
                nclex_sub = q.get("nclex_subcategory","")
                if nclex_cat:
                    st.markdown(f'<div style="font-size:0.8rem;color:#64748B;text-align:right;">{nclex_cat}<br>{nclex_sub}</div>',
                                unsafe_allow_html=True)

            # Miss type flags (for remediation guidance)
            miss_flags = q.get("miss_type_flags", [])
            if miss_flags and not is_full:
                flags_html = " ".join(f'<span style="background:#FEF3C7;color:#92400E;border:1px solid #FCD34D;border-radius:4px;padding:2px 7px;font-size:0.75rem;font-weight:600;">{f}</span>' for f in miss_flags)
                st.markdown(f'<div style="margin:0.4rem 0;"><span style="font-size:0.78rem;color:#9CA3AF;">Watch for: </span>{flags_html}</div>', unsafe_allow_html=True)

            # Interference pair warning
            if q.get("interference_pair") and not is_full:
                st.markdown(f'<div style="background:#FDF4FF;border-left:3px solid #A855F7;padding:6px 10px;border-radius:4px;font-size:0.82rem;color:#581C87;margin-bottom:0.5rem;">⚡ Interference pair: <strong>{q["interference_pair"]}</strong> — review both concepts together</div>',
                            unsafe_allow_html=True)

            # Show correct answers by type
            if qt in ("MC", "SATA"):
                opts = q.get("options", {})
                correct = detail.get("correct", set())
                user    = detail.get("user", set())
                for k, v in sorted(opts.items()):
                    c = k in correct
                    u = k in user
                    if c and u:   style,prefix = "background:#F0FDF4;border:1.5px solid #059669;","✅ "
                    elif c:       style,prefix = "background:#ECFDF5;border:1.5px solid #059669;","☑ "
                    elif u:       style,prefix = "background:#FFF1F2;border:1.5px solid #DC2626;","❌ "
                    else:         style,prefix = "background:#F9FAFB;border:1px solid #E5E7EB;",""
                    st.markdown(f'<div style="{style}border-radius:6px;padding:6px 12px;margin:3px 0;">'
                                f'<b>{prefix}{k}.</b> {v}</div>', unsafe_allow_html=True)

            elif qt == "BOWTIE":
                corr = detail.get("correct", {})
                usr  = detail.get("user", {})
                c_icon = "✅" if detail.get("condition_ok")  else "❌"
                a_icon = "✅" if detail.get("actions_ok")    else "❌"
                p_icon = "✅" if detail.get("parameters_ok") else "❌"
                st.markdown(f"**Condition:** {c_icon} Correct: `{corr.get('condition')}` | Your answer: `{usr.get('condition')}`")
                st.markdown(f"**Actions to Take:** {a_icon} Correct: `{corr.get('actions')}` | Your answer: `{usr.get('actions', [])}`")
                st.markdown(f"**Parameters to Monitor:** {p_icon} Correct: `{corr.get('parameters')}` | Your answer: `{usr.get('parameters', [])}`")

            elif qt in ("MATRIX", "TREND"):
                correct_map = detail.get("correct", {})
                user_map    = detail.get("user", {})
                for k, cv in correct_map.items():
                    uv = user_map.get(k, "—")
                    ok = uv == cv
                    icon2 = "✅" if ok else "❌"
                    st.markdown(f"{icon2} **{k}:** Correct: `{cv}` | Your answer: `{uv}`")

            elif qt == "CLOZE":
                correct_map = detail.get("correct", {})
                user_map    = detail.get("user", {})
                for k, cv in correct_map.items():
                    uv = user_map.get(k, "—")
                    ok = uv == cv
                    icon2 = "✅" if ok else "❌"
                    st.markdown(f"{icon2} **Blank '{k}':** Correct: `{cv}` | Your answer: `{uv}`")

            # Rationale
            rat = q.get("rationale", "")
            if rat:
                cls = "rat-correct" if is_full else "rat-incorrect"
                st.markdown(f'<div class="{cls}"><strong>📝 Rationale:</strong> {rat}</div>',
                            unsafe_allow_html=True)

# ─── ROUTER ──────────────────────────────────────────────────────────────────
screen = st.session_state.screen
if screen == "home":
    render_home()
elif screen == "test":
    render_test()
elif screen == "results":
    render_results()

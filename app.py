"""
NGN NCLEX Simulator — Framework Edition v3
- Unified clinical scenario + question in one card (no disconnect)
- True NCLEX bowtie visual (boxes + arrows, not columns)
- Matrix: proper radio-button rows with header alignment
- Trend: compact table + inline selects on same screen
- Cloze: inline sentence with embedded dropdowns
- Metadata collapsed into a subtle footer row
- Optimized for 14-inch laptop (no excessive scrolling)
"""
import json, time, random
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="NGN NCLEX Simulator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── GLOBAL CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*, html, body, [class*="css"] { font-family: 'Inter', sans-serif; box-sizing: border-box; }
.stApp { background: #ECEEF2; }
[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #D4D1CA; }

/* ── MAIN QUESTION CARD ── */
.qcard {
  background: #FFFFFF;
  border: 1px solid #D1D5DB;
  border-radius: 12px;
  padding: 0;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  margin-bottom: 16px;
}

/* Scenario stripe at top of card */
.scenario-stripe {
  background: #FFFBEB;
  border-bottom: 2px solid #FCD34D;
  padding: 14px 20px;
  font-size: 0.9rem;
  line-height: 1.65;
  color: #1C1917;
}
.scenario-label {
  font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; color: #B45309; margin-bottom: 6px;
}

/* Question stem area */
.qstem {
  padding: 16px 20px 10px 20px;
}
.qnum {
  font-size: 0.75rem; color: #9CA3AF; margin-bottom: 6px;
}
.stem-text {
  font-size: 1rem; font-weight: 600; color: #111827; line-height: 1.6;
  margin-bottom: 8px;
}
.badge-row { margin-bottom: 6px; }

/* Metadata footer stripe */
.meta-stripe {
  background: #F9FAFB;
  border-top: 1px solid #E5E7EB;
  padding: 7px 20px;
  font-size: 0.75rem;
  color: #6B7280;
}
.meta-stripe b { color: #374151; }

/* ── ANSWER AREA ── */
.answer-area {
  padding: 14px 20px 18px 20px;
  border-top: 1px solid #F3F4F6;
}

/* Type instruction banner */
.type-banner {
  border-radius: 6px;
  padding: 8px 14px;
  font-size: 0.82rem;
  font-weight: 600;
  margin-bottom: 12px;
}
.banner-bowtie  { background:#FFFBEB; color:#92400E; border:1px solid #FCD34D; }
.banner-matrix  { background:#FDF4FF; color:#6B21A8; border:1px solid #E9D5FF; }
.banner-trend   { background:#ECFDF5; color:#065F46; border:1px solid #A7F3D0; }
.banner-cloze   { background:#EFF6FF; color:#1E40AF; border:1px solid #BFDBFE; }

/* ── BADGES ── */
.badge {
  display:inline-block; font-size:0.68rem; font-weight:700;
  padding:2px 9px; border-radius:100px; margin-right:4px; margin-bottom:2px;
}
.badge-mc     { background:#EEF2FF; color:#3730A3; border:1px solid #C7D2FE; }
.badge-sata   { background:#E8F4F5; color:#01696F; border:1px solid #B3DADE; }
.badge-bowtie { background:#FEF3C7; color:#92400E; border:1px solid #FCD34D; }
.badge-matrix { background:#FCE7F3; color:#9D174D; border:1px solid #F9A8D4; }
.badge-trend  { background:#ECFDF5; color:#065F46; border:1px solid #6EE7B7; }
.badge-cloze  { background:#EFF6FF; color:#1D4ED8; border:1px solid #BFDBFE; }
.badge-ngn    { background:#FFF1F2; color:#9F1239; border:1px solid #FDA4AF; }
.badge-layer-a   { background:#FEF9C3; color:#713F12; border:1px solid #FDE68A; }
.badge-layer-aa  { background:#FFF7ED; color:#9A3412; border:1px solid #FDBA74; }
.badge-layer-b   { background:#EFF6FF; color:#1E40AF; border:1px solid #BFDBFE; }
.badge-layer-c   { background:#F0FDF4; color:#14532D; border:1px solid #BBF7D0; }
.badge-layer-d   { background:#FDF4FF; color:#581C87; border:1px solid #E9D5FF; }
.badge-layer-ngn { background:#FFF1F2; color:#9F1239; border:1px solid #FDA4AF; }

/* ── BOWTIE DIAGRAM ── */
.bowtie-wrap {
  display: grid;
  grid-template-columns: 1fr 36px 180px 36px 1fr;
  gap: 0;
  align-items: center;
  margin: 12px 0;
}
.bt-panel {
  background: #F8FAFC;
  border: 1px solid #CBD5E1;
  border-radius: 8px;
  padding: 10px 12px;
  min-height: 160px;
}
.bt-center {
  background: #FFFBEB;
  border: 2px solid #F59E0B;
  border-radius: 8px;
  padding: 10px 12px;
  text-align: center;
  min-height: 160px;
}
.bt-arrow {
  text-align: center;
  font-size: 1.4rem;
  color: #94A3B8;
  line-height: 1;
  padding: 0 2px;
}
.bt-header {
  font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.05em; color: #64748B; margin-bottom: 8px;
  padding-bottom: 4px; border-bottom: 1px solid #E2E8F0;
}
.bt-center-header {
  font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.05em; color: #B45309; margin-bottom: 8px;
  padding-bottom: 4px; border-bottom: 1px solid #FDE68A;
}
.bt-opt {
  padding: 4px 0; font-size: 0.88rem; color: #374151; line-height: 1.4;
}
.bt-opt-selected { color: #01696F; font-weight: 600; }

/* ── MATRIX TABLE ── */
.mat-wrap { overflow-x: auto; }
.mat-table {
  width: 100%; border-collapse: collapse; font-size: 0.88rem;
}
.mat-table th {
  background: #F1F5F9; padding: 9px 14px; text-align: center;
  font-weight: 700; font-size: 0.8rem; color: #374151;
  border: 1px solid #CBD5E1; white-space: nowrap;
}
.mat-table th.row-header { text-align: left; min-width: 260px; }
.mat-table td {
  padding: 9px 14px; border: 1px solid #E2E8F0;
  vertical-align: middle; color: #1E293B;
}
.mat-table td.cell-center { text-align: center; }
.mat-table tr:hover td { background: #F8FAFC; }

/* ── TREND TABLE ── */
.trend-tbl {
  width: 100%; border-collapse: collapse; font-size: 0.88rem;
  margin-bottom: 14px;
}
.trend-tbl th {
  background: #ECFDF5; padding: 8px 12px; text-align: center;
  font-size: 0.78rem; font-weight: 700; color: #065F46;
  border: 1px solid #A7F3D0; white-space: nowrap;
}
.trend-tbl th.row-header { text-align: left; }
.trend-tbl td {
  padding: 8px 12px; border: 1px solid #D1FAE5;
  text-align: center; color: #1E293B;
}
.trend-tbl td.last-val { background: #FEF9C3; font-weight: 600; }
.trend-tbl td.row-label { text-align: left; font-weight: 500; }

/* ── CLOZE ── */
.cloze-text {
  font-size: 0.95rem; line-height: 2.4; color: #1E293B;
}
.blank-placeholder {
  display: inline-block; min-width: 180px; background: #EFF6FF;
  border: 2px dashed #3B82F6; border-radius: 6px; padding: 0 10px;
  font-weight: 600; color: #1D4ED8; font-size: 0.88rem;
  vertical-align: middle;
}

/* ── TIMER ── */
.timer { background:#01696F; color:white; border-radius:8px; padding:8px 14px;
         font-size:1.05rem; font-weight:700; text-align:center; margin-bottom:12px; }
.timer-warn { background:#B45309 !important; }
.timer-crit { background:#9D174D !important; }

/* ── PROGRESS ── */
.prog-wrap { background:#E5E7EB; border-radius:100px; height:6px; margin:4px 0 8px; }
.prog-fill  { background:#01696F; height:6px; border-radius:100px; }

/* ── RESULTS ── */
.score-card {
  background:#FFF; border:1px solid #D4D1CA; border-radius:12px;
  padding:1.6rem 2rem; text-align:center; margin-bottom:1rem;
}
.score-pass { border-top:5px solid #059669; }
.score-fail { border-top:5px solid #DC2626; }
.score-num  { font-size:3rem; font-weight:800; line-height:1; }
.score-pass .score-num { color:#059669; }
.score-fail .score-num { color:#DC2626; }
.rat-ok   { background:#F0FDF4; border-left:4px solid #059669; border-radius:6px; padding:10px 14px; font-size:0.87rem; margin-top:8px; }
.rat-miss { background:#FFF1F2; border-left:4px solid #DC2626; border-radius:6px; padding:10px 14px; font-size:0.87rem; margin-top:8px; }

/* ── MISC ── */
.stButton>button {
  background:#01696F; color:#FFF; border:none; border-radius:8px;
  padding:8px 20px; font-weight:600; font-size:0.92rem;
}
.stButton>button:hover { background:#0C4E54; color:#FFF; }
div[data-testid="stCheckbox"] label { font-size: 0.88rem !important; }
#MainMenu, footer, header { visibility:hidden; }

/* Reduce Streamlit default vertical padding */
.block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)

# ─── LAYER CONFIG ─────────────────────────────────────────────────────────────
LAYER_INFO = {
    "A":        {"label": "Layer A — Recall",           "cls": "badge-layer-a"},
    "A-Applied":{"label": "Layer A-Applied — Translation","cls":"badge-layer-aa"},
    "B":        {"label": "Layer B — Mechanism",        "cls": "badge-layer-b"},
    "C":        {"label": "Layer C — Clinical Judgment","cls": "badge-layer-c"},
    "D":        {"label": "Layer D — Interference",     "cls": "badge-layer-d"},
    "NGN":      {"label": "NGN Format",                 "cls": "badge-layer-ngn"},
}
LAYER_STOP_RULES = {"A": 95, "A-Applied": 90, "C": 90, "D": 85}

# ─── DATA ─────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    for p in [Path(__file__).parent/"questions.json",
              Path(__file__).parent.parent/"questions.json"]:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    return []

data  = load_data()
BANKS = {b["id"]: b for b in data}

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
def init():
    defaults = {
        "screen":"home","bank_id":None,"questions":[],
        "idx":0,"answers":{},"locked":{},"start_time":None,
        "timer_min":90,"elapsed":0,"shuffle":True,"study_layer":"All Layers",
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init()

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def fmt_time(s):
    m,s = divmod(int(max(0,s)),60); h,m = divmod(m,60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def remaining():
    if not st.session_state.start_time:
        return st.session_state.timer_min*60
    return max(0, st.session_state.timer_min*60-(time.time()-st.session_state.start_time))

def start_test(bank_id, q_count, shuffle, timer_min, layer_filter):
    bank = BANKS[bank_id]
    qs   = list(bank["questions"])
    if layer_filter != "All Layers":
        qs = [q for q in qs if q.get("layer")==layer_filter] or qs
    if shuffle: random.shuffle(qs)
    qs = qs[:q_count]
    st.session_state.update({
        "screen":"test","bank_id":bank_id,"questions":qs,
        "idx":0,"answers":{},"locked":{},"start_time":time.time(),
        "timer_min":timer_min,"shuffle":shuffle,"study_layer":layer_filter,
    })

def go_home():
    st.session_state.update({"screen":"home","answers":{},"locked":{},"start_time":None})

# ─── BADGE HELPERS ────────────────────────────────────────────────────────────
TYPE_BADGE = {
    "MC":    ("badge-mc",    "Multiple Choice"),
    "SATA":  ("badge-sata",  "Select All That Apply"),
    "BOWTIE":("badge-bowtie","Bowtie"),
    "MATRIX":("badge-matrix","Matrix Grid"),
    "TREND": ("badge-trend", "Trend"),
    "CLOZE": ("badge-cloze", "Drop-Down / Cloze"),
}
def type_badge_html(qt):
    cls, label = TYPE_BADGE.get(qt, ("badge-ngn","NGN"))
    return f'<span class="badge {cls}">{label}</span>'

def layer_badge_html(q):
    lyr   = q.get("layer","")
    sub   = q.get("layer_subtype","")
    info  = LAYER_INFO.get(lyr,{})
    html  = f'<span class="badge {info.get("cls","")}">{info.get("label",lyr)}</span>' if info else ""
    if sub:
        html += f'<span class="badge" style="background:#F1F5F9;color:#64748B;border:1px solid #CBD5E1;">{sub}</span>'
    return html

def meta_html(q):
    parts = []
    if q.get("nclex_category"):    parts.append(f'<b>Category:</b> {q["nclex_category"]}')
    if q.get("nclex_subcategory"): parts.append(f'<b>Subcategory:</b> {q["nclex_subcategory"]}')
    if q.get("concept_bucket"):    parts.append(f'<b>Concept:</b> {q["concept_bucket"]}')
    if q.get("interference_pair"): parts.append(f'<b>Interference Pair:</b> {q["interference_pair"]}')
    return " &nbsp;·&nbsp; ".join(parts)

# ─── QUESTION HEADER (unified card top) ──────────────────────────────────────
def render_qcard_top(q, idx, total):
    qt = q["type"]
    # --- scenario stripe ---
    scenario = q.get("case_study","")
    scenario_html = ""
    if scenario:
        scenario_html = f"""
        <div class="scenario-stripe">
          <div class="scenario-label">📋 Clinical Scenario</div>
          {scenario}
        </div>"""

    # --- stem ---
    stem_html = f"""
    <div class="qstem">
      <div class="qnum">Question {idx+1} of {total}</div>
      <div class="badge-row">
        {type_badge_html(qt)}
        {"<span class='badge badge-ngn'>NGN</span>" if q.get("ngn") else ""}
        {layer_badge_html(q)}
      </div>
      <div class="stem-text">{q["text"]}</div>
    </div>"""

    # --- meta footer ---
    m = meta_html(q)
    meta_footer = f'<div class="meta-stripe">{m}</div>' if m else ""

    st.markdown(
        f'<div class="qcard">{scenario_html}{stem_html}{meta_footer}</div>',
        unsafe_allow_html=True
    )

# ─── GRADING ─────────────────────────────────────────────────────────────────
def grade_question(q, ans):
    qt = q["type"]
    if qt in ("MC","SATA"):
        correct = set(q["correct_answers"])
        user    = set(ans) if ans else set()
        if qt=="MC":
            return (1 if user==correct else 0), 1, {"correct":correct,"user":user}
        pts = sum(1 for x in user if x in correct)-sum(1 for x in user if x not in correct)
        return max(0,pts), len(correct), {"correct":correct,"user":user}

    elif qt=="BOWTIE":
        ans = ans or {}
        ca  = q["correct_answers"]
        # Support both new keys and old keys in correct_answers
        correct_cond   = ca.get("condition") or ca.get("cause", "")
        correct_actions= ca.get("actions")   or ca.get("action", [])
        correct_params = ca.get("parameters") or ca.get("outcome", "")
        # Support both new keys and old keys in user answers
        user_cond   = ans.get("condition") or ans.get("cause", "")
        user_actions= ans.get("actions")   or ans.get("action", [])
        user_params = ans.get("parameters") or ans.get("outcome", "")
        # Normalize: outcome was a single string in old format, parameters is a list
        if isinstance(correct_params, str): correct_params = [correct_params]
        if isinstance(user_params, str):    user_params    = [user_params]
        c_ok = user_cond == correct_cond
        a_ok = set(user_actions) == set(correct_actions)
        p_ok = set(user_params)  == set(correct_params)
        return int(c_ok)+int(a_ok)+int(p_ok), 3, {
            "condition_ok":c_ok,"actions_ok":a_ok,"parameters_ok":p_ok,
            "correct":{"condition":correct_cond,"actions":correct_actions,"parameters":correct_params},
            "user":{"condition":user_cond,"actions":user_actions,"parameters":user_params}}

    elif qt in ("MATRIX","TREND","CLOZE"):
        ans = ans or {}
        cm  = q["correct_answers"]
        earned = sum(1 for k,v in cm.items() if ans.get(k)==v)
        return earned, len(cm), {"correct":cm,"user":ans}

    return 0,1,{}

# ─── ANSWER COMPLETENESS ─────────────────────────────────────────────────────
def is_answered(q, qid):
    ans = st.session_state.answers.get(qid)
    qt  = q["type"]
    if qt in ("MC","SATA"):  return bool(ans)
    if qt=="BOWTIE":
        return (ans and bool(ans.get("condition"))
                and len(ans.get("actions",[]))==2
                and len(ans.get("parameters",[]))==2)
    if qt=="MATRIX":  return ans and len(ans)>=len(q["matrix"]["rows"])
    if qt=="TREND":   return ans and len(ans)>=len(q["trend"]["items"])
    if qt=="CLOZE":
        blanks=[p for p in q["cloze"]["sentence_parts"] if isinstance(p,dict)]
        return ans and len(ans)>=len(blanks)
    return False

# ─── RENDERERS ───────────────────────────────────────────────────────────────

def render_mc(q, qid, locked):
    opts = q["options"]; keys = sorted(opts.keys())
    cur  = st.session_state.answers.get(qid,[])
    cur_val = cur[0] if cur else None
    if locked:
        for k in keys:
            sel = k==cur_val
            icon="◉" if sel else "○"
            color="#01696F" if sel else "#6B7280"
            st.markdown(f'<div style="padding:5px 0;color:{color};">{icon} <b>{k}.</b> {opts[k]}</div>',
                        unsafe_allow_html=True)
    else:
        idx_d = keys.index(cur_val) if cur_val in keys else None
        choice = st.radio("", keys, index=idx_d,
                          format_func=lambda k:f"{k}.  {opts[k]}",
                          key=f"mc_{qid}", label_visibility="collapsed")
        st.session_state.answers[qid] = [choice] if choice else []

def render_sata(q, qid, locked):
    opts = q["options"]; keys = sorted(opts.keys())
    cur  = st.session_state.answers.get(qid,[])
    st.markdown('<div style="color:#01696F;font-size:0.82rem;font-weight:600;margin-bottom:6px;">Select ALL that apply</div>',
                unsafe_allow_html=True)
    if locked:
        for k in keys:
            icon="☑" if k in cur else "☐"
            color="#01696F" if k in cur else "#6B7280"
            st.markdown(f'<div style="padding:4px 0;color:{color};">{icon} <b>{k}.</b> {opts[k]}</div>',
                        unsafe_allow_html=True)
    else:
        sel = st.multiselect("",keys,default=cur,
                             format_func=lambda k:f"{k}.  {opts[k]}",
                             key=f"sata_{qid}",label_visibility="collapsed")
        st.session_state.answers[qid] = sel

def render_bowtie(q, qid, locked):
    """
    True NCLEX bowtie visual:
      [Actions to Take panel] → ◇ Condition ◇ → [Parameters to Monitor panel]
    Each side uses a multiselect (select 2); center uses radio (select 1).
    Backward-compatible: also reads old cause/action/outcome keys.
    """
    bt   = q["bowtie"]
    # Support both new keys (condition_options/actions_to_take/parameters_to_monitor)
    # and old keys (causes/actions/outcomes) for backward compatibility
    c_opts = bt.get("condition_options") or bt.get("causes", [])
    a_opts = bt.get("actions_to_take")   or bt.get("actions", [])
    p_opts = bt.get("parameters_to_monitor") or bt.get("outcomes", [])
    cur    = st.session_state.answers.get(qid,{})

    st.markdown('<div class="type-banner banner-bowtie">Bowtie — Select the <strong>condition</strong> (center), <strong>2 actions to take</strong> (left), and <strong>2 parameters to monitor</strong> (right).</div>',
                unsafe_allow_html=True)

    # ── Three columns with arrow connectors ──
    col_a, col_arr1, col_c, col_arr2, col_p = st.columns([5, 1, 4, 1, 5])

    # Left: Actions to Take
    with col_a:
        st.markdown('<div style="background:#F8FAFC;border:1px solid #CBD5E1;border-radius:8px;padding:12px;">'
                    '<div class="bt-header">Actions to Take</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.78rem;color:#9CA3AF;margin-bottom:6px;">Select 2</div>',
                    unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if locked:
            chosen_a = cur.get("actions",[])
            for opt in a_opts:
                sel = opt in chosen_a
                icon = "☑" if sel else "☐"
                color = "#01696F" if sel else "#6B7280"
                st.markdown(f'<div style="padding:3px 0;font-size:0.87rem;color:{color};">{icon} {opt}</div>',
                            unsafe_allow_html=True)
        else:
            chosen_a = st.multiselect("", a_opts, default=cur.get("actions",[]),
                                      key=f"bt_a_{qid}", label_visibility="collapsed",
                                      max_selections=2)
            cur["actions"] = chosen_a
            st.session_state.answers[qid] = cur

    # Arrow 1
    with col_arr1:
        st.markdown('<div style="text-align:center;padding-top:60px;font-size:1.6rem;color:#94A3B8;">→</div>',
                    unsafe_allow_html=True)

    # Center: Condition
    with col_c:
        st.markdown('<div style="background:#FFFBEB;border:2px solid #F59E0B;border-radius:8px;padding:12px;">'
                    '<div class="bt-center-header" style="text-align:center;">Condition Most Likely Experiencing</div>',
                    unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.78rem;color:#B45309;margin-bottom:6px;text-align:center;">Select 1</div>',
                    unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if locked:
            chosen_c = cur.get("condition","")
            for opt in c_opts:
                icon = "◉" if opt==chosen_c else "○"
                color = "#92400E" if opt==chosen_c else "#6B7280"
                st.markdown(f'<div style="padding:3px 0;font-size:0.87rem;color:{color};">{icon} {opt}</div>',
                            unsafe_allow_html=True)
        else:
            idx_d = c_opts.index(cur["condition"]) if cur.get("condition") in c_opts else None
            chosen_c = st.radio("", c_opts, index=idx_d,
                                key=f"bt_c_{qid}", label_visibility="collapsed")
            cur["condition"] = chosen_c
            st.session_state.answers[qid] = cur

    # Arrow 2
    with col_arr2:
        st.markdown('<div style="text-align:center;padding-top:60px;font-size:1.6rem;color:#94A3B8;">→</div>',
                    unsafe_allow_html=True)

    # Right: Parameters to Monitor
    with col_p:
        st.markdown('<div style="background:#F8FAFC;border:1px solid #CBD5E1;border-radius:8px;padding:12px;">'
                    '<div class="bt-header">Parameters to Monitor</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.78rem;color:#9CA3AF;margin-bottom:6px;">Select 2</div>',
                    unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if locked:
            chosen_p = cur.get("parameters",[])
            for opt in p_opts:
                sel = opt in chosen_p
                icon = "☑" if sel else "☐"
                color = "#065F46" if sel else "#6B7280"
                st.markdown(f'<div style="padding:3px 0;font-size:0.87rem;color:{color};">{icon} {opt}</div>',
                            unsafe_allow_html=True)
        else:
            chosen_p = st.multiselect("", p_opts, default=cur.get("parameters",[]),
                                      key=f"bt_p_{qid}", label_visibility="collapsed",
                                      max_selections=2)
            cur["parameters"] = chosen_p
            st.session_state.answers[qid] = cur

def render_matrix(q, qid, locked):
    """
    Matrix: proper aligned table using st.columns so headers stay above checkboxes.
    One radio-group per row (only one can be selected per row).
    """
    rows    = q["matrix"]["rows"]
    columns = q["matrix"]["columns"]
    cur     = st.session_state.answers.get(qid,{})

    st.markdown('<div class="type-banner banner-matrix">Matrix Grid — For each finding, select the correct column.</div>',
                unsafe_allow_html=True)

    # Header row
    ncols = len(columns)
    col_widths = [4] + [2]*ncols
    hcols = st.columns(col_widths)
    hcols[0].markdown('<div style="font-weight:700;font-size:0.82rem;color:#374151;padding:6px 0;">Assessment Finding</div>',
                      unsafe_allow_html=True)
    for i,col_name in enumerate(columns):
        hcols[i+1].markdown(
            f'<div style="text-align:center;font-weight:700;font-size:0.82rem;color:#374151;'
            f'background:#F1F5F9;border:1px solid #CBD5E1;border-radius:6px;padding:6px 4px;">{col_name}</div>',
            unsafe_allow_html=True)

    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

    # Data rows
    for row in rows:
        row_id    = row["id"]
        row_label = row["label"]
        dcols     = st.columns(col_widths)

        dcols[0].markdown(
            f'<div style="font-size:0.88rem;padding:6px 0;color:#1E293B;">{row_label}</div>',
            unsafe_allow_html=True)

        if locked:
            chosen = cur.get(row_id,"")
            for i,col_name in enumerate(columns):
                selected = chosen==col_name
                icon = "◉" if selected else "○"
                color = "#01696F" if selected else "#D1D5DB"
                dcols[i+1].markdown(
                    f'<div style="text-align:center;font-size:1.25rem;color:{color};padding:4px 0;">{icon}</div>',
                    unsafe_allow_html=True)
        else:
            for i,col_name in enumerate(columns):
                checked = cur.get(row_id)==col_name
                if dcols[i+1].checkbox("", value=checked,
                                       key=f"mat_{qid}_{row_id}_{col_name}",
                                       label_visibility="collapsed"):
                    cur[row_id] = col_name
                    st.session_state.answers[qid] = cur

        st.markdown('<div style="height:1px;background:#F3F4F6;margin:2px 0;"></div>',
                    unsafe_allow_html=True)

def render_trend(q, qid, locked):
    """
    Trend: compact data table then inline select per item on same view.
    """
    tdata = q["trend"]["data"]
    tpts  = q["trend"]["timepoints"]
    items = q["trend"]["items"]
    cur   = st.session_state.answers.get(qid,{})
    opts  = ["Improving","Worsening","No change"]

    st.markdown('<div class="type-banner banner-trend">Trend — Review the data, then classify each parameter below.</div>',
                unsafe_allow_html=True)

    # Data table (compact)
    th = "".join(f"<th>{tp}</th>" for tp in tpts)
    rows_html = ""
    for row in tdata:
        cells = ""
        for i,val in enumerate(row["values"]):
            cls = ' class="last-val"' if i==len(row["values"])-1 else ""
            cells += f"<td{cls}>{val}</td>"
        rows_html += f"<tr><td class='row-label'>{row['label']}</td>{cells}</tr>"
    st.markdown(
        f'<div style="overflow-x:auto;"><table class="trend-tbl">'
        f'<thead><tr><th class="row-header">Parameter</th>{th}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div>',
        unsafe_allow_html=True)

    # Classification rows — each item on one line: label | selectbox
    st.markdown('<div style="font-size:0.82rem;font-weight:700;color:#065F46;margin-bottom:6px;">For each item below, select the trend:</div>',
                unsafe_allow_html=True)

    for item in items:
        iid   = item["id"]
        label = item["label"]
        c1,c2 = st.columns([3,2])
        c1.markdown(
            f'<div style="font-size:0.9rem;font-weight:600;color:#1E293B;padding-top:6px;">{label}</div>',
            unsafe_allow_html=True)
        if locked:
            val = cur.get(iid,"—")
            color = "#059669" if val=="Improving" else ("#DC2626" if val=="Worsening" else "#6B7280")
            c2.markdown(f'<div style="font-size:0.9rem;font-weight:700;color:{color};padding-top:6px;">{val}</div>',
                        unsafe_allow_html=True)
        else:
            idx_d = opts.index(cur[iid]) if cur.get(iid) in opts else None
            choice = c2.selectbox("", opts, index=idx_d,
                                  key=f"tr_{qid}_{iid}", label_visibility="collapsed")
            cur[iid] = choice
            st.session_state.answers[qid] = cur

def render_cloze(q, qid, locked):
    """
    Cloze: sentence flows inline; each blank shows a compact selectbox on its own line
    labeled clearly, then continues sentence text.
    """
    parts = q["cloze"]["sentence_parts"]
    cur   = st.session_state.answers.get(qid,{})

    st.markdown('<div class="type-banner banner-cloze">Drop-Down — Select the best answer for each blank to complete the statement.</div>',
                unsafe_allow_html=True)

    # Build the sentence as segments; blanks get their own labeled row
    text_buffer = ""
    for part in parts:
        if isinstance(part, str):
            text_buffer += part
        elif isinstance(part, dict):
            bid   = part["blank_id"]
            bopts = part["options"]
            blabel = part.get("label", bid)

            # flush text so far
            if text_buffer.strip():
                st.markdown(f'<div class="cloze-text">{text_buffer}</div>', unsafe_allow_html=True)
                text_buffer = ""

            if locked:
                val = cur.get(bid,"___")
                st.markdown(f'<div style="margin:4px 0 8px 0;">'
                            f'<span style="font-size:0.78rem;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:0.05em;">{blabel}: </span>'
                            f'<span class="blank-placeholder">{val}</span>'
                            f'</div>', unsafe_allow_html=True)
            else:
                idx_d = bopts.index(cur[bid]) if cur.get(bid) in bopts else None
                c1,c2 = st.columns([1,3])
                c1.markdown(f'<div style="font-size:0.82rem;font-weight:700;color:#374151;padding-top:8px;">{blabel}:</div>',
                            unsafe_allow_html=True)
                choice = c2.selectbox("", bopts, index=idx_d,
                                      key=f"cz_{qid}_{bid}", label_visibility="collapsed")
                cur[bid] = choice
                st.session_state.answers[qid] = cur

    # flush any remaining text
    if text_buffer.strip():
        st.markdown(f'<div class="cloze-text">{text_buffer}</div>', unsafe_allow_html=True)

# ─── HOME ─────────────────────────────────────────────────────────────────────
def render_home():
    st.markdown("## 🏥 NGN NCLEX Simulator")
    st.markdown("*Next Generation NCLEX · Framework Edition · All 6 Item Types*")

    badge_cols = st.columns(6)
    for col,(cls,lbl) in zip(badge_cols,[
        ("badge-mc","Multiple Choice"),("badge-sata","Select All"),
        ("badge-bowtie","Bowtie"),("badge-matrix","Matrix Grid"),
        ("badge-trend","Trend"),("badge-cloze","Drop-Down")]):
        col.markdown(f'<div class="badge {cls}" style="width:100%;text-align:center;">{lbl}</div>',
                     unsafe_allow_html=True)
    st.markdown("---")

    if not BANKS:
        st.error("No question banks found. Make sure questions.json is in the same folder as app.py.")
        return

    c1,c2 = st.columns([2,1])

    with c1:
        st.markdown("### Question Banks")
        for bid,bank in BANKS.items():
            tc = {}; lc = {}
            for q in bank["questions"]:
                tc[q["type"]] = tc.get(q["type"],0)+1
                lc[q.get("layer","?")] = lc.get(q.get("layer","?"),0)+1
            ts = " · ".join(f"{v} {k}" for k,v in tc.items())
            ls = " · ".join(f"L{k}:{v}" for k,v in sorted(lc.items()))
            st.markdown(f"""<div class="qcard" style="padding:1rem 1.4rem;">
              <strong style="font-size:1rem;">{bank['title']}</strong>
              <div style="color:#6B7280;font-size:0.8rem;margin-top:2px;">{bank['question_count']} questions · {ts}</div>
              <div style="color:#9CA3AF;font-size:0.77rem;">Layers: {ls}</div>
              <div style="color:#6B7280;font-size:0.8rem;">{bank.get('description','')}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Start: {bank['title']}", key=f"start_{bid}"):
                start_test(bid,
                    st.session_state.get(f"qc_{bid}", min(75,bank['question_count'])),
                    st.session_state.get(f"sh_{bid}", True),
                    st.session_state.get(f"tm_{bid}", 90),
                    st.session_state.get(f"lay_{bid}", "All Layers"))
                st.rerun()

    with c2:
        st.markdown("### Configure")
        if BANKS:
            sel = st.selectbox("Bank", list(BANKS.keys()),
                               format_func=lambda x:BANKS[x]["title"])
            bank = BANKS[sel]
            avail = sorted(set(q.get("layer","?") for q in bank["questions"]))
            st.selectbox("Study Mode", ["All Layers"]+avail, key=f"lay_{sel}",
                         help="Filter by framework layer for targeted practice")
            lay_sel = st.session_state.get(f"lay_{sel}","All Layers")
            max_q = bank["question_count"] if lay_sel=="All Layers" else max(1,sum(1 for q in bank["questions"] if q.get("layer")==lay_sel))
            st.slider("Questions", 1, max_q, min(75,max_q), key=f"qc_{sel}")
            st.slider("Time (min)", 30, 180, 90, step=15, key=f"tm_{sel}")
            st.checkbox("Shuffle questions", value=True, key=f"sh_{sel}")
        st.markdown("---")
        st.markdown("""**Stop-rule thresholds:**
- Layer A ≥ 95%
- Layer A-Applied ≥ 90%
- Layer C ≥ 90%
- Layer D ≥ 85%
- NCLEX pass ≥ 68%""")

# ─── TEST ─────────────────────────────────────────────────────────────────────
def render_test():
    qs = st.session_state.questions
    if not qs: go_home(); st.rerun(); return

    bid   = st.session_state.bank_id
    bank  = BANKS[bid]
    idx   = st.session_state.idx
    total = len(qs)
    rem   = remaining()
    tsec  = st.session_state.timer_min*60
    pct_t = rem/tsec if tsec else 1

    if rem<=0:
        st.session_state.elapsed=tsec; st.session_state.screen="results"; st.rerun(); return

    q    = qs[idx]
    qid  = f"{idx}_{q.get('id',idx)}"
    lock = st.session_state.locked.get(qid,False)

    tcls = "timer"+(" timer-crit" if pct_t<.10 else " timer-warn" if pct_t<.25 else "")

    # Sidebar
    with st.sidebar:
        st.markdown(f"## {bank['title']}")
        st.markdown(f'<div class="{tcls}">⏱ {fmt_time(rem)}</div>', unsafe_allow_html=True)
        done = len(st.session_state.locked)
        st.markdown(f"**Q {idx+1} / {total}**")
        st.markdown(f'<div class="prog-wrap"><div class="prog-fill" style="width:{done/total*100:.1f}%"></div></div>'
                    f'<div style="color:#9CA3AF;font-size:0.77rem;">{done} answered · {total-done} remaining</div>',
                    unsafe_allow_html=True)
        st.markdown("---")
        sl = st.session_state.get("study_layer","All Layers")
        if sl!="All Layers":
            info = LAYER_INFO.get(sl,{}); st.markdown(f'<span class="badge {info.get("cls","")}">{info.get("label",sl)}</span>', unsafe_allow_html=True)
        st.markdown("*No going back — just like the real NCLEX.*")
        st.markdown("---")
        if st.button("Abandon Test"): go_home(); st.rerun()

    # Unified question card (scenario + stem + meta all in one)
    render_qcard_top(q, idx, total)

    # Answer area
    qt = q["type"]
    if qt=="MC":      render_mc(q, qid, lock)
    elif qt=="SATA":  render_sata(q, qid, lock)
    elif qt=="BOWTIE":render_bowtie(q, qid, lock)
    elif qt=="MATRIX":render_matrix(q, qid, lock)
    elif qt=="TREND": render_trend(q, qid, lock)
    elif qt=="CLOZE": render_cloze(q, qid, lock)

    # Navigation
    st.markdown("<br>", unsafe_allow_html=True)
    answered = is_answered(q,qid)
    is_last  = (idx==total-1)
    btn_lbl  = "Submit Test ✓" if is_last else "Next Question →"
    c_btn, c_warn = st.columns([2,3])
    with c_btn:
        if st.button(btn_lbl, disabled=(not answered and not lock)):
            if not lock: st.session_state.locked[qid]=True
            if is_last:
                st.session_state.elapsed=tsec-rem; st.session_state.screen="results"
            else:
                st.session_state.idx+=1
            st.rerun()
    with c_warn:
        if not answered and not lock:
            st.markdown('<div style="color:#B45309;font-size:0.85rem;padding-top:8px;">⚠️ Answer all parts before continuing</div>',
                        unsafe_allow_html=True)

# ─── RESULTS ─────────────────────────────────────────────────────────────────
def render_results():
    qs      = st.session_state.questions
    bid     = st.session_state.bank_id
    bank    = BANKS[bid]
    elapsed = st.session_state.get("elapsed",0)

    te=0; tp=0; details=[]
    for i,q in enumerate(qs):
        qid  = f"{i}_{q.get('id',i)}"
        ans  = st.session_state.answers.get(qid)
        e,p,d= grade_question(q,ans)
        te+=e; tp+=p; details.append((q,e,p,d))

    pct    = te/tp*100 if tp else 0
    passed = pct>=68

    # Layer breakdown
    lstats={}
    for q,e,p,_ in details:
        l=q.get("layer","?")
        if l not in lstats: lstats[l]=[0,0]
        lstats[l][0]+=e; lstats[l][1]+=p

    with st.sidebar:
        st.markdown("## Results")
        st.metric("Score",f"{pct:.1f}%")
        st.metric("Points",f"{te}/{tp}")
        st.metric("Time",fmt_time(elapsed))
        st.markdown("---")
        st.markdown("**Layer mastery:**")
        for lyr,(e,p) in sorted(lstats.items()):
            thr = LAYER_STOP_RULES.get(lyr,68)
            lp  = e/p*100 if p else 0
            icon= "✅" if lp>=thr else "⚠️"
            st.markdown(f"{icon} **{lyr}**: {lp:.0f}% (need {thr}%)")
        st.markdown("---")
        if st.button("Try Again"):
            start_test(bid,len(qs),st.session_state.shuffle,
                       st.session_state.timer_min,st.session_state.get("study_layer","All Layers"))
            st.rerun()
        if st.button("Home"): go_home(); st.rerun()

    p_lbl  = "PASSED ✓" if passed else "NEEDS MORE PRACTICE"
    p_color= "#059669" if passed else "#DC2626"
    p_cls  = "score-card score-pass" if passed else "score-card score-fail"
    st.markdown("## Your Results")
    st.markdown(f'<div class="{p_cls}"><div class="score-num">{pct:.1f}%</div>'
                f'<div style="font-size:1rem;font-weight:700;color:{p_color};margin-top:4px;">{p_lbl}</div>'
                f'<div style="color:#9CA3AF;font-size:0.85rem;margin-top:2px;">{te}/{tp} pts · {fmt_time(elapsed)}</div></div>',
                unsafe_allow_html=True)

    # Type breakdown
    tstats={}
    for q,e,p,_ in details:
        t=q["type"]
        if t not in tstats: tstats[t]=[0,0]
        tstats[t][0]+=e; tstats[t][1]+=p
    tcols=st.columns(len(tstats))
    for col,(t,(e,p)) in zip(tcols,tstats.items()):
        col.metric(t,f"{e}/{p}",f"{e/p*100:.0f}%" if p else "—")

    # Layer mastery grid
    st.markdown("---")
    st.markdown("### Layer Mastery")
    lcols=st.columns(max(1,len(lstats)))
    for col,(lyr,(e,p)) in zip(lcols,sorted(lstats.items())):
        thr=LAYER_STOP_RULES.get(lyr,68); lp=e/p*100 if p else 0; met=lp>=thr
        info=LAYER_INFO.get(lyr,{"label":lyr,"cls":"badge-layer-ngn"})
        col.markdown(
            f'<div style="background:#FFF;border:1px solid #E5E7EB;border-radius:8px;padding:12px;text-align:center;">'
            f'<div class="badge {info["cls"]}">{lyr}</div>'
            f'<div style="font-size:1.5rem;font-weight:800;color:{"#059669" if met else "#DC2626"};">{lp:.0f}%</div>'
            f'<div style="font-size:0.75rem;color:#9CA3AF;">Need {thr}% · {"✅ Met" if met else "⚠️ Below"}</div>'
            f'</div>', unsafe_allow_html=True)

    # Answer review
    st.markdown("---")
    st.markdown("### Answer Review & Rationales")
    filt = st.radio("Show:", ["All","Incorrect / Partial","Full Credit Only"], horizontal=True)

    for i,(q,e,p,d) in enumerate(details):
        full=(e==p); zero=(e==0)
        if filt=="Incorrect / Partial" and full: continue
        if filt=="Full Credit Only" and not full: continue

        icon="✅" if full else ("❌" if zero else "⚠️")
        qt = q["type"]
        lyr= q.get("layer","")
        info=LAYER_INFO.get(lyr,{})

        with st.expander(f"{icon} Q{i+1} [{qt}] — {e}/{p} pts — {q['text'][:72]}..."):
            # Layer + concept header
            sub=q.get("layer_subtype",""); concept=q.get("concept_bucket","")
            st.markdown(
                f'<span class="badge {info.get("cls","")}">{lyr}</span>'
                +(f'<span class="badge" style="background:#F1F5F9;color:#64748B;border:1px solid #CBD5E1;">{sub}</span>' if sub else "")
                +(f'<span class="badge" style="background:#F8FAFC;color:#64748B;border:1px solid #E2E8F0;">{concept}</span>' if concept else ""),
                unsafe_allow_html=True)

            # NCLEX metadata
            nc=q.get("nclex_category",""); ns=q.get("nclex_subcategory","")
            if nc: st.markdown(f'<div style="font-size:0.77rem;color:#9CA3AF;">{nc} › {ns}</div>',unsafe_allow_html=True)

            # Miss type flags
            mf=q.get("miss_type_flags",[])
            if mf and not full:
                flags=" ".join(f'<span style="background:#FEF3C7;color:#92400E;border:1px solid #FCD34D;border-radius:4px;padding:2px 7px;font-size:0.72rem;font-weight:700;">{f}</span>' for f in mf)
                st.markdown(f'<div style="margin:4px 0;">Watch for: {flags}</div>',unsafe_allow_html=True)

            # Interference pair
            ip=q.get("interference_pair","")
            if ip and not full:
                st.markdown(f'<div style="background:#FDF4FF;border-left:3px solid #A855F7;padding:6px 10px;border-radius:4px;font-size:0.82rem;color:#581C87;margin:6px 0;">⚡ Interference pair: <strong>{ip}</strong> — study both together</div>',unsafe_allow_html=True)

            # Answer breakdown
            if qt in ("MC","SATA"):
                opts=q.get("options",{}); correct=d.get("correct",set()); user=d.get("user",set())
                for k,v in sorted(opts.items()):
                    c=k in correct; u=k in user
                    if c and u:   style,pref="background:#F0FDF4;border:1.5px solid #059669;","✅ "
                    elif c:       style,pref="background:#ECFDF5;border:1.5px solid #059669;","☑ "
                    elif u:       style,pref="background:#FFF1F2;border:1.5px solid #DC2626;","❌ "
                    else:         style,pref="background:#F9FAFB;border:1px solid #E5E7EB;",""
                    st.markdown(f'<div style="{style}border-radius:6px;padding:5px 12px;margin:3px 0;font-size:0.87rem;"><b>{pref}{k}.</b> {v}</div>',unsafe_allow_html=True)

            elif qt=="BOWTIE":
                c=d.get("correct",{}); u=d.get("user",{})
                st.markdown(f'**Condition** {"✅" if d.get("condition_ok") else "❌"} — Correct: `{c.get("condition")}` | Yours: `{u.get("condition")}`')
                st.markdown(f'**Actions to Take** {"✅" if d.get("actions_ok") else "❌"} — Correct: `{c.get("actions")}` | Yours: `{u.get("actions",[])}`')
                st.markdown(f'**Parameters to Monitor** {"✅" if d.get("parameters_ok") else "❌"} — Correct: `{c.get("parameters")}` | Yours: `{u.get("parameters",[])}`')

            elif qt in ("MATRIX","TREND","CLOZE"):
                cm=d.get("correct",{}); um=d.get("user",{})
                for k,cv in cm.items():
                    uv=um.get(k,"—"); ok=uv==cv
                    st.markdown(f'{"✅" if ok else "❌"} **{k}** — Correct: `{cv}` | Yours: `{uv}`')

            # Rationale
            rat=q.get("rationale","")
            if rat:
                cls2="rat-ok" if full else "rat-miss"
                st.markdown(f'<div class="{cls2}"><strong>📝 Rationale:</strong> {rat}</div>',
                            unsafe_allow_html=True)

# ─── ROUTER ──────────────────────────────────────────────────────────────────
s = st.session_state.screen
if s=="home":    render_home()
elif s=="test":  render_test()
elif s=="results": render_results()

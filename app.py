"""
NCLEX Test Simulator — Streamlit App
One question at a time, no going back (true NCLEX mode)
"""
import json
import time
import random
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="NCLEX Test Simulator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #F7F6F2; }
[data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #D4D1CA; }

.q-card {
    background: #FFFFFF;
    border: 1px solid #D4D1CA;
    border-radius: 10px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.q-text { font-size: 1.08rem; font-weight: 500; color: #28251D; line-height: 1.65; }
.q-number { font-size: 0.85rem; color: #7A7974; margin-bottom: 0.4rem; }

.sata-badge {
    display: inline-block; background: #E8F4F5; color: #01696F;
    font-size: 0.75rem; font-weight: 600; padding: 2px 10px;
    border-radius: 100px; margin-bottom: 0.5rem; border: 1px solid #B3DADE;
}
.mc-badge {
    display: inline-block; background: #F0EDFF; color: #5C3FA5;
    font-size: 0.75rem; font-weight: 600; padding: 2px 10px;
    border-radius: 100px; margin-bottom: 0.5rem; border: 1px solid #C8BFEF;
}
.timer-box {
    background: #01696F; color: white; border-radius: 8px;
    padding: 0.5rem 1rem; font-size: 1.2rem; font-weight: 700;
    text-align: center; letter-spacing: 0.05em; margin-bottom: 1rem;
}
.timer-warning { background: #964219 !important; }
.timer-danger  { background: #A12C7B !important; }

.progress-bar-wrap {
    background: #E8E6E0; border-radius: 100px; height: 8px; margin: 0.5rem 0 1rem;
}
.progress-bar-fill {
    background: #01696F; height: 8px; border-radius: 100px; transition: width 0.3s;
}

.score-card {
    background: #FFFFFF; border: 1px solid #D4D1CA; border-radius: 12px;
    padding: 2rem; text-align: center; margin-bottom: 1.5rem;
}
.score-pass { border-top: 5px solid #437A22; }
.score-fail { border-top: 5px solid #A12C7B; }
.score-number { font-size: 3.5rem; font-weight: 700; line-height: 1; }
.score-pass .score-number { color: #437A22; }
.score-fail .score-number { color: #A12C7B; }

.rationale-correct {
    background: #F0F7EC; border-left: 4px solid #437A22; border-radius: 6px;
    padding: 0.8rem 1rem; margin-top: 0.5rem; font-size: 0.9rem; color: #2A4A1A;
}
.rationale-incorrect {
    background: #FDF0F7; border-left: 4px solid #A12C7B; border-radius: 6px;
    padding: 0.8rem 1rem; margin-top: 0.5rem; font-size: 0.9rem; color: #4A1A35;
}

.stButton > button {
    background-color: #01696F; color: white; border: none;
    border-radius: 8px; padding: 0.6rem 1.8rem;
    font-weight: 600; font-size: 1rem;
}
.stButton > button:hover { background-color: #0C4E54; color: white; }

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── DATA ────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    for p in [Path(__file__).parent / "nclex_questions.json",
              Path(__file__).parent.parent / "nclex_questions.json"]:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return []

data = load_data()
TEST_META = {t["test_number"]: t for t in data}

# ─── SESSION STATE ───────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "screen": "home",
        "test_num": None,
        "questions": [],
        "current_idx": 0,        # which question we're on
        "answers": {},            # {q_number: [selections]}
        "submitted": False,
        "start_time": None,
        "timer_minutes": 90,
        "shuffle": False,
        "locked": {},             # {q_number: True} once answered and moved on
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def format_time(seconds):
    m, s = divmod(int(max(0, seconds)), 60)
    h, m2 = divmod(m, 60)
    if h:
        return f"{h}:{m2:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def remaining_seconds():
    if st.session_state.start_time is None:
        return st.session_state.timer_minutes * 60
    elapsed = time.time() - st.session_state.start_time
    return max(0, st.session_state.timer_minutes * 60 - elapsed)

def grade(q, user_ans):
    correct = set(q["correct_answers"])
    user = set(user_ans) if user_ans else set()
    return user == correct, correct, user

def start_test(test_num, q_count, shuffle, timer_min):
    questions = list(TEST_META[test_num]["questions"])
    if shuffle:
        random.shuffle(questions)
    questions = questions[:q_count]
    st.session_state.update({
        "screen": "test",
        "test_num": test_num,
        "questions": questions,
        "current_idx": 0,
        "answers": {},
        "locked": {},
        "submitted": False,
        "start_time": time.time(),
        "timer_minutes": timer_min,
        "shuffle": shuffle,
    })

def go_home():
    st.session_state.update({
        "screen": "home", "submitted": False,
        "answers": {}, "start_time": None, "locked": {},
    })

# ─── HOME ────────────────────────────────────────────────────────────────────
def render_home():
    st.markdown("## 🏥 NCLEX Test Simulator")
    st.markdown("**Crowder College | HCIIIA Unit 4 | 2026 NCLEX-RN Test Plan**")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Select a Test")
        for t_num, meta in TEST_META.items():
            sata_c = sum(1 for q in meta["questions"] if q["type"] == "SATA")
            mc_c   = sum(1 for q in meta["questions"] if q["type"] == "MC")
            st.markdown(f"""
            <div class="q-card" style="padding:1rem 1.4rem;">
                <strong style="font-size:1rem;color:#28251D;">Test {t_num} — {meta['difficulty']} Level</strong>
                <div style="color:#7A7974;font-size:0.85rem;margin-top:3px;">
                    {meta['question_count']} questions &nbsp;·&nbsp; {mc_c} MC &nbsp;·&nbsp;
                    {sata_c} SATA &nbsp;·&nbsp; {meta['stars']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Start Test {t_num}", key=f"start_{t_num}"):
                start_test(
                    t_num,
                    st.session_state.get(f"qcount_{t_num}", min(75, meta['question_count'])),
                    st.session_state.get(f"shuffle_{t_num}", False),
                    st.session_state.get(f"timer_{t_num}", 90),
                )
                st.rerun()

    with col2:
        st.markdown("### Settings")
        sel = st.selectbox("Configure Test", list(TEST_META.keys()),
                           format_func=lambda x: f"Test {x}")
        meta = TEST_META[sel]
        st.slider("Questions", 10, meta['question_count'],
                  min(75, meta['question_count']), key=f"qcount_{sel}")
        st.slider("Time limit (min)", 30, 180, 90, step=15, key=f"timer_{sel}")
        st.checkbox("Shuffle order", value=False, key=f"shuffle_{sel}")
        st.markdown("---")
        st.markdown("""
**NCLEX Mode:**
- One question at a time
- Cannot go back once you move forward
- Submit when you reach the last question
        """)

# ─── TEST (ONE QUESTION AT A TIME) ───────────────────────────────────────────
def render_test():
    questions = st.session_state.questions
    if not questions:
        go_home(); st.rerun(); return

    t_num     = st.session_state.test_num
    meta      = TEST_META[t_num]
    idx       = st.session_state.current_idx
    total     = len(questions)
    remaining = remaining_seconds()
    total_sec = st.session_state.timer_minutes * 60

    # Auto-submit on time up
    if remaining <= 0 and not st.session_state.submitted:
        st.session_state.submitted = True
        st.session_state.screen = "results"
        st.rerun(); return

    q = questions[idx]
    q_num = q["number"]
    is_locked = st.session_state.locked.get(q_num, False)

    # Timer color
    pct = remaining / total_sec
    tcls = "timer-box" + (" timer-danger" if pct < 0.10 else " timer-warning" if pct < 0.25 else "")

    # ─ Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"## Test {t_num}")
        st.markdown(f"*{meta['difficulty']} Level*")
        st.markdown("---")
        st.markdown(f'<div class="{tcls}">⏱ {format_time(remaining)}</div>', unsafe_allow_html=True)

        answered = len(st.session_state.locked)
        pct_done = answered / total
        st.markdown(f"**Question {idx+1} of {total}**")
        st.markdown(f"""
        <div class="progress-bar-wrap">
            <div class="progress-bar-fill" style="width:{pct_done*100:.1f}%"></div>
        </div>
        <div style="color:#7A7974;font-size:0.82rem;">{answered} answered · {total - answered} remaining</div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("*Once you move to the next question, you cannot return — just like the real NCLEX.*")

        st.markdown("---")
        if st.button("Abandon & Go Home", type="secondary" if hasattr(st.button, 'type') else "primary"):
            go_home(); st.rerun()

    # ─ Main question ──────────────────────────────────────────────────────────
    st.markdown(f"## Test {t_num} — {meta['difficulty']} Level")

    badge = ('<span class="sata-badge">SELECT ALL THAT APPLY</span>'
             if q["type"] == "SATA" else '<span class="mc-badge">MULTIPLE CHOICE</span>')

    st.markdown(f"""
    <div class="q-card">
        <div class="q-number">Question {idx+1} of {total}</div>
        {badge}
        <div class="q-text">{q["text"]}</div>
    </div>
    """, unsafe_allow_html=True)

    options = q.get("options", {})
    key_list = sorted(options.keys())
    current_ans = st.session_state.answers.get(q_num, [])

    

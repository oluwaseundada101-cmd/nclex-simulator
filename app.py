"""
NCLEX Test Simulator — Streamlit App
Crowder College | HCIIIA Unit 4 | 2026 NCLEX-RN Test Plan
"""
import json
import time
import random
import streamlit as st
from pathlib import Path

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NCLEX Test Simulator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Main bg */
.stApp { background-color: #F7F6F2; }

/* Sidebar */
[data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #D4D1CA; }
[data-testid="stSidebar"] .stMarkdown h2 { color: #01696F; }

/* Question card */
.q-card {
    background: #FFFFFF;
    border: 1px solid #D4D1CA;
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

/* Question text */
.q-text { font-size: 1.05rem; font-weight: 500; color: #28251D; line-height: 1.6; }

/* SATA badge */
.sata-badge {
    display: inline-block;
    background: #E8F4F5;
    color: #01696F;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 100px;
    margin-bottom: 0.5rem;
    border: 1px solid #B3DADE;
}

/* MC badge */
.mc-badge {
    display: inline-block;
    background: #F0EDFF;
    color: #5C3FA5;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 100px;
    margin-bottom: 0.5rem;
    border: 1px solid #C8BFEF;
}

/* Timer */
.timer-box {
    background: #01696F;
    color: white;
    border-radius: 8px;
    padding: 0.4rem 0.9rem;
    font-size: 1.1rem;
    font-weight: 700;
    text-align: center;
    letter-spacing: 0.05em;
}
.timer-warning { background: #964219 !important; }
.timer-danger  { background: #A12C7B !important; }

/* Score card */
.score-card {
    background: #FFFFFF;
    border: 1px solid #D4D1CA;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    margin-bottom: 1.5rem;
}
.score-pass { border-top: 5px solid #437A22; }
.score-fail { border-top: 5px solid #A12C7B; }
.score-number { font-size: 3.5rem; font-weight: 700; line-height: 1; }
.score-pass .score-number { color: #437A22; }
.score-fail .score-number { color: #A12C7B; }

/* Rationale box */
.rationale-correct {
    background: #F0F7EC;
    border-left: 4px solid #437A22;
    border-radius: 6px;
    padding: 0.8rem 1rem;
    margin-top: 0.5rem;
    font-size: 0.9rem;
    color: #2A4A1A;
}
.rationale-incorrect {
    background: #FDF0F7;
    border-left: 4px solid #A12C7B;
    border-radius: 6px;
    padding: 0.8rem 1rem;
    margin-top: 0.5rem;
    font-size: 0.9rem;
    color: #4A1A35;
}
.correct-answer-label { font-weight: 600; color: #437A22; }
.incorrect-answer-label { font-weight: 600; color: #A12C7B; }

/* Progress bar */
.stProgress > div > div { background-color: #01696F; }

/* Buttons */
.stButton > button {
    background-color: #01696F;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.55rem 1.5rem;
    font-weight: 600;
    font-size: 0.95rem;
    transition: background 0.15s;
}
.stButton > button:hover { background-color: #0C4E54; color: white; }
.stButton > button[kind="secondary"] { background-color: #F7F6F2; color: #28251D; border: 1px solid #D4D1CA; }
.stButton > button[kind="secondary"]:hover { background-color: #ECECEA; }

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── DATA ────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    data_path = Path(__file__).parent.parent / "nclex_questions.json"
    if not data_path.exists():
        data_path = Path(__file__).parent / "nclex_questions.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

data = load_data()
TEST_META = {t["test_number"]: t for t in data}

# ─── SESSION STATE INIT ──────────────────────────────────────────────────────
def init_state():
    defaults = {
        "screen": "home",       # home | test | results
        "test_num": None,
        "questions": [],
        "answers": {},          # {q_number: list_of_selections}
        "submitted": False,
        "start_time": None,
        "elapsed": 0,
        "timer_minutes": 90,
        "shuffle": False,
        "q_count": 75,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def remaining_seconds():
    if st.session_state.start_time is None:
        return st.session_state.timer_minutes * 60
    elapsed = time.time() - st.session_state.start_time
    return max(0, st.session_state.timer_minutes * 60 - elapsed)

def grade_question(q, user_ans):
    """Returns (is_correct, correct_set, user_set)"""
    correct = set(q["correct_answers"])
    user = set(user_ans) if user_ans else set()
    if q["type"] == "SATA":
        return user == correct, correct, user
    else:
        return user == correct, correct, user

def start_test(test_num, q_count, shuffle, timer_min):
    questions = list(TEST_META[test_num]["questions"])
    if shuffle:
        random.shuffle(questions)
    questions = questions[:q_count]
    
    st.session_state.screen = "test"
    st.session_state.test_num = test_num
    st.session_state.questions = questions
    st.session_state.answers = {}
    st.session_state.submitted = False
    st.session_state.start_time = time.time()
    st.session_state.timer_minutes = timer_min
    st.session_state.shuffle = shuffle

def go_home():
    st.session_state.screen = "home"
    st.session_state.submitted = False
    st.session_state.answers = {}
    st.session_state.start_time = None

# ─── HOME SCREEN ─────────────────────────────────────────────────────────────
def render_home():
    st.markdown("## 🏥 NCLEX Test Simulator")
    st.markdown("**Crowder College | HCIIIA Unit 4 | 2026 NCLEX-RN Test Plan**")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Select a Test")
        
        for t_num, meta in TEST_META.items():
            q_list = meta["questions"]
            sata_c = sum(1 for q in q_list if q["type"] == "SATA")
            mc_c   = sum(1 for q in q_list if q["type"] == "MC")
            
            with st.container():
                st.markdown(f"""
                <div class="q-card" style="padding:1rem 1.4rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <strong style="font-size:1rem; color:#28251D;">Test {t_num} — {meta['difficulty']} Level</strong>
                            <div style="color:#7A7974; font-size:0.85rem; margin-top:2px;">
                                {meta['question_count']} questions &nbsp;·&nbsp;
                                {mc_c} MC &nbsp;·&nbsp; {sata_c} SATA &nbsp;·&nbsp; {meta['stars']}
                            </div>
                        </div>
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
        
        selected_test = st.selectbox("Configure Test", list(TEST_META.keys()),
                                      format_func=lambda x: f"Test {x}")
        meta = TEST_META[selected_test]
        max_q = meta['question_count']
        
        q_count = st.slider("Questions to attempt", 10, max_q, min(75, max_q),
                             key=f"qcount_{selected_test}")
        timer_min = st.slider("Time limit (minutes)", 30, 180, 90, step=15,
                               key=f"timer_{selected_test}")
        shuffle = st.checkbox("Shuffle question order", value=False,
                               key=f"shuffle_{selected_test}")
        
        st.markdown("---")
        st.markdown("**How to use:**")
        st.markdown("""
- Select a test above and click **Start**  
- Answer all questions — SATA allows multiple selections  
- Submit when done to see your score and rationales  
- Tests get harder from Test 1 → Test 6
        """)

# ─── TEST SCREEN ─────────────────────────────────────────────────────────────
def render_test():
    questions = st.session_state.questions
    if not questions:
        go_home()
        st.rerun()
        return
    
    t_num = st.session_state.test_num
    meta  = TEST_META[t_num]
    
    # ─ Timer ──────────────────────────────────────────────────────────────────
    remaining = remaining_seconds()
    total_secs = st.session_state.timer_minutes * 60
    pct_left = remaining / total_secs
    
    timer_class = "timer-box"
    if pct_left < 0.10:
        timer_class = "timer-box timer-danger"
    elif pct_left < 0.25:
        timer_class = "timer-box timer-warning"
    
    # Auto-submit when time runs out
    if remaining <= 0 and not st.session_state.submitted:
        st.session_state.submitted = True
        st.session_state.elapsed = total_secs
        st.session_state.screen = "results"
        st.rerun()
        return
    
    # ─ Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"## Test {t_num}")
        st.markdown(f"*{meta['difficulty']} Level*")
        st.markdown("---")
        
        st.markdown(f"""
        <div class="{timer_class}">⏱ {format_time(remaining)}</div>
        """, unsafe_allow_html=True)
        
        answered = sum(1 for q in questions if q["number"] in st.session_state.answers
                       and st.session_state.answers[q["number"]])
        
        st.markdown(f"**Progress:** {answered} / {len(questions)}")
        st.progress(answered / len(questions))
        
        st.markdown("---")
        
        if st.button("Submit Test", type="primary"):
            st.session_state.submitted = True
            st.session_state.elapsed = total_secs - remaining
            st.session_state.screen = "results"
            st.rerun()
        
        if st.button("Abandon & Go Home", type="secondary"):
            go_home()
            st.rerun()
        
        st.markdown("---")
        st.markdown("**Question Navigator**")
        # Show small grid of Q numbers
        cols = st.columns(5)
        for i, q in enumerate(questions):
            ans = st.session_state.answers.get(q["number"], [])
            label = str(q["number"])
            bg = "#01696F" if ans else "#D4D1CA"
            color = "white" if ans else "#28251D"
            cols[i % 5].markdown(
                f'<div style="background:{bg};color:{color};border-radius:4px;'
                f'text-align:center;font-size:0.72rem;padding:2px;margin:1px;">{label}</div>',
                unsafe_allow_html=True
            )
    
    # ─ Main content ───────────────────────────────────────────────────────────
    st.markdown(f"## Test {t_num} — {meta['difficulty']} Level")
    
    # Refresh timer every ~5 seconds via auto-rerun hint
    st.markdown(
        f'<div style="font-size:0.85rem;color:#7A7974;margin-bottom:1rem;">'
        f'⏱ Time remaining: <strong>{format_time(remaining)}</strong> &nbsp;·&nbsp; '
        f'{answered}/{len(questions)} answered</div>',
        unsafe_allow_html=True
    )
    
    for idx, q in enumerate(questions):
        q_num = q["number"]
        q_type = q["type"]
        
        badge = (
            '<span class="sata-badge">SELECT ALL THAT APPLY</span>'
            if q_type == "SATA"
            else '<span class="mc-badge">MULTIPLE CHOICE</span>'
        )
        
        st.markdown(f"""
        <div class="q-card">
            {badge}
            <div class="q-text"><strong>Q{idx+1}.</strong> {q["text"]}</div>
        </div>
        """, unsafe_allow_html=True)
        
        options = q.get("options", {})
        option_labels = [f"{k}. {v}" for k, v in sorted(options.items())]
        
        if q_type == "SATA":
            existing = st.session_state.answers.get(q_num, [])
            selected = st.multiselect(
                "Select all that apply:",
                options=list(sorted(options.keys())),
                default=existing,
                format_func=lambda k, opts=options: f"{k}. {opts[k]}",
                key=f"sata_{t_num}_{q_num}",
                label_visibility="collapsed"
            )
            # Display custom options
            st.caption("☝️ Select all correct answers")
            st.session_state.answers[q_num] = selected
        else:
            existing = st.session_state.answers.get(q_num, [None])
            existing_val = existing[0] if existing else None
            
            # Map answer letter back to full label
            default_idx = None
            key_list = sorted(options.keys())
            if existing_val and existing_val in key_list:
                default_idx = key_list.index(existing_val)
            
            choice = st.radio(
                "Select one answer:",
                options=key_list,
                index=default_idx,
                format_func=lambda k, opts=options: f"{k}. {opts[k]}",
                key=f"mc_{t_num}_{q_num}",
                label_visibility="collapsed",
                horizontal=False
            )
            st.session_state.answers[q_num] = [choice] if choice else []
        
        st.markdown("<hr style='margin:0.8rem 0; border-color:#E8E6E0;'>", unsafe_allow_html=True)

# ─── RESULTS SCREEN ──────────────────────────────────────────────────────────
def render_results():
    questions  = st.session_state.questions
    t_num      = st.session_state.test_num
    meta       = TEST_META[t_num]
    elapsed    = st.session_state.get("elapsed", 0)
    
    # Grade
    results = []
    for q in questions:
        user_ans = st.session_state.answers.get(q["number"], [])
        is_correct, correct_set, user_set = grade_question(q, user_ans)
        results.append({
            "q": q,
            "is_correct": is_correct,
            "correct_set": correct_set,
            "user_set": user_set,
        })
    
    total    = len(results)
    correct  = sum(1 for r in results if r["is_correct"])
    pct      = (correct / total * 100) if total else 0
    passed   = pct >= 68  # NCLEX passing threshold (~68%)
    
    sata_r   = [r for r in results if r["q"]["type"] == "SATA"]
    mc_r     = [r for r in results if r["q"]["type"] == "MC"]
    sata_cor = sum(1 for r in sata_r if r["is_correct"])
    mc_cor   = sum(1 for r in mc_r   if r["is_correct"])
    
    # ─ Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## Results")
        st.markdown(f"**Test {t_num} — {meta['difficulty']}**")
        st.markdown("---")
        st.metric("Score", f"{pct:.1f}%")
        st.metric("Correct", f"{correct} / {total}")
        st.metric("Time Used", format_time(elapsed))
        st.markdown("---")
        
        if st.button("Try Again", type="primary"):
            start_test(t_num, len(questions),
                       st.session_state.shuffle,
                       st.session_state.timer_minutes)
            st.rerun()
        
        if st.button("Go Home", type="secondary"):
            go_home()
            st.rerun()
    
    # ─ Score card ─────────────────────────────────────────────────────────────
    st.markdown("## Your Results")
    
    pass_label = "PASSED ✓" if passed else "NEEDS MORE PRACTICE"
    pass_color = "#437A22" if passed else "#A12C7B"
    card_class = "score-card score-pass" if passed else "score-card score-fail"
    
    st.markdown(f"""
    <div class="{card_class}">
        <div class="score-number">{pct:.1f}%</div>
        <div style="font-size:1.1rem;font-weight:600;color:{pass_color};margin-top:0.3rem;">{pass_label}</div>
        <div style="color:#7A7974;font-size:0.9rem;margin-top:0.3rem;">
            {correct} correct out of {total} &nbsp;·&nbsp; Time: {format_time(elapsed)}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("MC Correct",   f"{mc_cor}/{len(mc_r)}"   if mc_r   else "N/A")
    c2.metric("SATA Correct", f"{sata_cor}/{len(sata_r)}" if sata_r else "N/A")
    c3.metric("Passing Threshold", "68%")
    c4.metric("Test Level", meta['difficulty'])
    
    st.markdown("---")
    
    # ─ Answer review ──────────────────────────────────────────────────────────
    st.markdown("### Answer Review & Rationales")
    
    filter_opt = st.radio("Show:", ["All Questions", "Incorrect Only", "Correct Only"],
                           horizontal=True)
    
    for idx, r in enumerate(results):
        q          = r["q"]
        is_correct = r["is_correct"]
        
        if filter_opt == "Incorrect Only" and is_correct:
            continue
        if filter_opt == "Correct Only" and not is_correct:
            continue
        
        icon = "✅" if is_correct else "❌"
        bg   = "#F7FFF5" if is_correct else "#FFF5FA"
        border = "#437A22" if is_correct else "#A12C7B"
        
        with st.expander(f"{icon} Q{idx+1}. {q['text'][:80]}...", expanded=not is_correct):
            options = q.get("options", {})
            
            for letter, text in sorted(options.items()):
                is_correct_opt = letter in r["correct_set"]
                was_selected   = letter in r["user_set"]
                
                if is_correct_opt and was_selected:
                    style = "background:#ECFAE8; border:1.5px solid #437A22; border-radius:6px; padding:6px 12px; margin:3px 0;"
                    prefix = "✅ "
                elif is_correct_opt and not was_selected:
                    style = "background:#E8F5F3; border:1.5px solid #01696F; border-radius:6px; padding:6px 12px; margin:3px 0;"
                    prefix = "☑ "  # correct but not selected
                elif not is_correct_opt and was_selected:
                    style = "background:#FAE8F3; border:1.5px solid #A12C7B; border-radius:6px; padding:6px 12px; margin:3px 0;"
                    prefix = "❌ "
                else:
                    style = "background:#FAFAF8; border:1px solid #E0DDD8; border-radius:6px; padding:6px 12px; margin:3px 0;"
                    prefix = ""
                
                st.markdown(
                    f'<div style="{style}"><strong>{prefix}{letter}.</strong> {text}</div>',
                    unsafe_allow_html=True
                )
            
            # Correct answer summary
            st.markdown("")
            correct_labels = ", ".join(sorted(r["correct_set"]))
            if r["user_set"]:
                user_labels = ", ".join(sorted(r["user_set"]))
            else:
                user_labels = "(no answer)"
            
            label_class = "correct-answer-label" if is_correct else "incorrect-answer-label"
            st.markdown(
                f'<div class="{label_class}">Correct: {correct_labels} &nbsp;|&nbsp; '
                f'Your answer: {user_labels}</div>',
                unsafe_allow_html=True
            )
            
            # Rationale
            rationale = q.get("rationale", "")
            if rationale and "Refer to your study" not in rationale:
                rat_class = "rationale-correct" if is_correct else "rationale-incorrect"
                st.markdown(
                    f'<div class="{rat_class}"><strong>📝 Rationale:</strong> {rationale}</div>',
                    unsafe_allow_html=True
                )

# ─── ROUTER ──────────────────────────────────────────────────────────────────
if st.session_state.screen == "home":
    render_home()
elif st.session_state.screen == "test":
    render_test()
elif st.session_state.screen == "results":
    render_results()

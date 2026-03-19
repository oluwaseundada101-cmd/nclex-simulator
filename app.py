"""
app.py — NGN NCLEX Simulator v4 main entry point.

Features:
  - streamlit-autorefresh every 30 s during test (live countdown timer)
  - JSON load wrapped in try/except → friendly error + reload button
  - len(questions) used everywhere — never trusts JSON question_count
  - Modular: home.py / renderers.py / grading.py / persistence.py / config.py
  - Stop-rule enforcement (Guided Mode)
  - SQLite progress tracking
  - Per-option rationales on review screen
  - Bowtie: schema-driven counts (intentional: 1 condition, 2 actions, 2 parameters)
"""
import json
import os
import time
import html as _html
import streamlit as st

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NGN NCLEX Simulator · Unit 4",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Optional autorefresh (safe import) ───────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

# ── Local imports ─────────────────────────────────────────────────────────────
from config import LAYER_INFO, LAYER_ORDER, LAYER_STOP_RULES, PASSING_PCT
from grading import aggregate_results, check_layer_readiness, get_miss_explanation
from persistence import (
    init_db, save_session, get_session_history,
    get_layer_mastery_summary, get_priority_pairs
)
from renderers import (
    render_qcard_top, render_mc, render_sata, render_bowtie,
    render_matrix, render_trend, render_cloze, is_answered, h
)
from home import render_home

# ── Init DB ───────────────────────────────────────────────────────────────────
init_db()

# ── Resolve paths ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _bank_paths():
    """Return all .json paths in BASE_DIR that look like question banks."""
    paths = []
    for fname in os.listdir(BASE_DIR):
        if fname.endswith(".json") and fname not in ("progress.db",):
            paths.append(os.path.join(BASE_DIR, fname))
    return sorted(paths)


# ── Load question banks (cached) ──────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_banks():
    banks    = []
    errors   = []
    for path in _bank_paths():
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"**{os.path.basename(path)}** — JSON parse error: `{e}`")
            continue
        except Exception as e:
            errors.append(f"**{os.path.basename(path)}** — could not read: `{e}`")
            continue

        # Normalise: accept either a bare list or {banks: [...]} or {questions: [...]}
        if isinstance(raw, list):
            # Top-level array = multiple banks
            for b in raw:
                if "questions" in b:
                    b["questions"] = b["questions"]  # count from len(), never from field
                    banks.append(b)
        elif isinstance(raw, dict):
            if "banks" in raw:
                for b in raw["banks"]:
                    banks.append(b)
            elif "questions" in raw:
                banks.append(raw)
            else:
                errors.append(f"**{os.path.basename(path)}** — unrecognised structure "
                               f"(no 'questions' or 'banks' key found)")

    return banks, errors


# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar(banks, errors):
    with st.sidebar:
        st.markdown("""
        <div style="font-weight:800;font-size:1.05rem;color:#01696F;
                    margin-bottom:2px;">🩺 NGN Simulator</div>
        <div style="font-size:0.78rem;color:#9CA3AF;margin-bottom:16px;">
            Unit 4 HCIIIA · v4
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        screen = st.session_state.get("screen", "home")
        if screen in ("test", "review"):
            if st.button("← Back to Home", key="btn_nav_home"):
                st.session_state.screen = "home"
                st.rerun()
        if screen == "home":
            if st.button("📊 Progress History", key="btn_nav_progress"):
                st.session_state.screen = "progress"
                st.rerun()
        if screen == "progress":
            if st.button("← Back to Home", key="btn_nav_home2"):
                st.session_state.screen = "home"
                st.rerun()

        st.markdown("---")

        # Reload button
        if st.button("🔄 Reload Question Banks", key="btn_reload"):
            st.cache_data.clear()
            st.rerun()

        # Error display
        if errors:
            st.markdown("**⚠️ Bank load errors:**")
            for e in errors:
                st.error(e)

        # Bank count
        if banks:
            total_q = sum(len(b.get("questions", [])) for b in banks)
            st.markdown(
                f'<div style="font-size:0.8rem;color:#6B7280;">'
                f'{len(banks)} bank{"s" if len(banks)!=1 else ""} · '
                f'{total_q} question{"s" if total_q!=1 else ""}</div>',
                unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            '<div style="font-size:0.72rem;color:#9CA3AF;">'
            'Source: Unit 4 HCIIIA lecture slides, hybrid supplement, mastery guide<br>'
            'Framework: Prof Master Framework v1.0<br>'
            'Formats: MC · SATA · Bowtie · Matrix · Trend · Cloze</div>',
            unsafe_allow_html=True)


# ── CSS ───────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    /* ── Base ── */
    .stApp { background: #F7F6F2; }
    .block-container { max-width: 900px; padding: 1.5rem 1.5rem; }

    /* ── Badges ── */
    .badge {
        display:inline-block;border-radius:12px;padding:2px 10px;
        font-size:0.72rem;font-weight:700;letter-spacing:0.04em;
        white-space:nowrap;margin-right:4px;
    }
    .badge-mc      { background:#DBEAFE;color:#1E40AF; }
    .badge-sata    { background:#D1FAE5;color:#065F46; }
    .badge-bowtie  { background:#FEF3C7;color:#92400E; }
    .badge-matrix  { background:#EDE9FE;color:#4C1D95; }
    .badge-trend   { background:#FCE7F3;color:#9D174D; }
    .badge-cloze   { background:#FFEDD5;color:#9A3412; }
    .badge-ngn     { background:#F59E0B22;color:#92400E;border:1px solid #F59E0B; }

    .badge-layer-a   { background:#D1FAE5;color:#065F46; }
    .badge-layer-aa  { background:#A7F3D0;color:#064E3B; }
    .badge-layer-b   { background:#DBEAFE;color:#1E40AF; }
    .badge-layer-c   { background:#EDE9FE;color:#4C1D95; }
    .badge-layer-d   { background:#FEE2E2;color:#991B1B; }
    .badge-layer-ngn { background:#FEF3C7;color:#92400E; }

    /* ── Question card ── */
    .qcard {
        background:#FFFFFF;border:1px solid #E5E7EB;
        border-radius:12px;padding:20px 22px;margin-bottom:16px;
        box-shadow:0 1px 4px rgba(0,0,0,0.06);
    }
    .scenario-stripe {
        background:#F0FAFA;border-left:4px solid #01696F;
        border-radius:0 8px 8px 0;padding:12px 16px;
        margin-bottom:14px;font-size:0.88rem;color:#1E293B;
        line-height:1.6;
    }
    .scenario-label {
        font-size:0.74rem;font-weight:700;color:#01696F;
        text-transform:uppercase;letter-spacing:0.06em;margin-bottom:5px;
    }
    .qstem { margin-bottom:8px; }
    .qnum  { font-size:0.75rem;color:#9CA3AF;font-weight:600;margin-bottom:5px; }
    .badge-row { margin-bottom:9px; }
    .stem-text { font-size:0.97rem;font-weight:600;color:#111827;line-height:1.55; }
    .meta-stripe {
        font-size:0.75rem;color:#9CA3AF;margin-top:6px;
        padding-top:6px;border-top:1px solid #F3F4F6;
    }

    /* ── Type banners ── */
    .type-banner {
        border-radius:6px;padding:8px 12px;
        font-size:0.82rem;font-weight:700;margin-bottom:12px;
    }
    .banner-bowtie  { background:#FEF9C3;color:#92400E; }
    .banner-matrix  { background:#EDE9FE;color:#4C1D95; }
    .banner-trend   { background:#FCE7F3;color:#9D174D; }
    .banner-cloze   { background:#FFEDD5;color:#9A3412; }

    /* ── Bowtie headers ── */
    .bt-header        { font-weight:700;font-size:0.82rem;color:#374151;margin-bottom:4px; }
    .bt-center-header { font-weight:700;font-size:0.82rem;color:#92400E;margin-bottom:4px; }

    /* ── Trend table ── */
    .trend-tbl {
        border-collapse:collapse;width:100%;font-size:0.84rem;
        margin-bottom:12px;
    }
    .trend-tbl th, .trend-tbl td {
        padding:7px 10px;border:1px solid #E5E7EB;text-align:center;
    }
    .trend-tbl .row-header { font-weight:700;text-align:left;background:#F9FAFB; }
    .trend-tbl .row-label  { text-align:left;color:#374151;font-weight:600; }
    .trend-tbl thead th    { background:#F1F5F9;font-weight:700;color:#374151; }
    .trend-tbl .last-val   { background:#FFF7ED;font-weight:700;color:#C2410C; }

    /* ── Cloze ── */
    .cloze-text      { font-size:0.93rem;color:#1E293B;line-height:1.65;margin-bottom:8px; }
    .blank-placeholder {
        display:inline-block;background:#F0FAFA;border:1px solid #01696F;
        border-radius:4px;padding:1px 8px;color:#01696F;font-weight:700;
    }

    /* ── Timer bar ── */
    .timer-ok      { color:#059669;font-weight:800;font-size:1.15rem; }
    .timer-warn    { color:#D97706;font-weight:800;font-size:1.15rem; }
    .timer-danger  { color:#DC2626;font-weight:800;font-size:1.15rem;
                     animation:pulse 1s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }

    /* ── Result card ── */
    .result-card {
        background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;
        padding:20px 24px;margin-bottom:14px;
    }
    .correct-banner   { background:#D1FAE5;border-left:4px solid #059669; }
    .incorrect-banner { background:#FEE2E2;border-left:4px solid #EF4444; }
    .partial-banner   { background:#FEF3C7;border-left:4px solid #F59E0B; }

    /* ── Misc ── */
    .stButton > button { border-radius:8px !important; }
    div[data-testid="stRadio"] label { font-size:0.88rem !important; }
    </style>
    """, unsafe_allow_html=True)


# ── Timer helpers ─────────────────────────────────────────────────────────────
def seconds_remaining():
    if not st.session_state.get("use_timer"):
        return None
    start   = st.session_state.get("start_time", time.time())
    minutes = st.session_state.get("timer_minutes", 30)
    elapsed = time.time() - start
    return max(0, minutes * 60 - elapsed)


def render_timer(container=None):
    """Render the countdown timer. Returns True when time is up (triggers auto-submit).

    Uses a st.empty() container when provided so the timer updates in-place
    rather than appending a new element every 5-second refresh cycle.
    """
    rem = seconds_remaining()
    if rem is None:
        return False  # timer disabled

    mins = int(rem) // 60
    secs = int(rem) % 60
    label = f"\u23f1 {mins:02d}:{secs:02d}"

    target = container if container is not None else st

    if rem <= 0:
        target.markdown(
            '<div class="timer-danger">\u23f0 Time\'s up! Auto-submitting\u2026</div>',
            unsafe_allow_html=True)
        return True  # signal auto-submit

    cls = "timer-ok" if rem > 120 else ("timer-warn" if rem > 30 else "timer-danger")
    target.markdown(f'<div class="{cls}">{label}</div>', unsafe_allow_html=True)
    return False


# ── Test screen ───────────────────────────────────────────────────────────────
def render_test_screen():
    # Autorefresh every 5 s — tight enough for a visible countdown,
    # light enough not to thrash hosted deployments.
    if AUTOREFRESH_AVAILABLE and st.session_state.get("use_timer"):
        st_autorefresh(interval=5_000, key="timer_refresh")

    questions = st.session_state.get("active_questions", [])
    cur_idx   = st.session_state.get("current_q", 0)

    if not questions:
        st.warning("No questions loaded.")
        if st.button("← Home"):
            st.session_state.screen = "home"
            st.rerun()
        return

    # Header row: timer + nav indicator
    h_left, h_mid, h_right = st.columns([3, 4, 3])
    with h_left:
        # st.empty() lets the timer update in-place on every 5-second rerun
        # instead of stacking a new element. Works correctly in both local
        # and hosted (Render / HuggingFace) deployments.
        timer_slot = st.empty()
        auto_submit = render_timer(container=timer_slot)
    with h_mid:
        # Progress dots
        dots = "".join(
            f'<span style="display:inline-block;width:10px;height:10px;'
            f'border-radius:50%;margin:0 2px;'
            f'background:{"#01696F" if i == cur_idx else ("#10B981" if i < cur_idx else "#CBD5E1")};"></span>'
            for i in range(len(questions)))
        st.markdown(
            f'<div style="text-align:center;padding-top:6px;">{dots}</div>',
            unsafe_allow_html=True)
    with h_right:
        n_answered = sum(
            1 for i, q in enumerate(questions)
            if is_answered(q, f"{i}_{q.get('id',i)}"))
        st.markdown(
            f'<div style="text-align:right;font-size:0.82rem;color:#6B7280;">'
            f'{n_answered} / {len(questions)} answered</div>',
            unsafe_allow_html=True)

    # Auto-submit on timer expiry
    if auto_submit:
        time.sleep(0.5)
        st.session_state.submitted = True
        st.session_state.screen    = "review"
        st.rerun()

    st.markdown("---")

    q   = questions[cur_idx]
    qid = f"{cur_idx}_{q.get('id', cur_idx)}"
    qt  = q["type"]

    if qid not in st.session_state.answers:
        st.session_state.answers[qid] = {} if qt in ("BOWTIE","MATRIX","TREND","CLOZE") else []

    # Render question card top
    render_qcard_top(q, cur_idx, len(questions))

    # Render answer widget
    locked = False  # test mode — never locked
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

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Navigation buttons
    nav_l, nav_mid, nav_r = st.columns([2, 4, 2])

    # No going back (framework requirement)
    with nav_l:
        pass  # intentionally empty

    with nav_r:
        answered = is_answered(q, qid)
        is_last  = (cur_idx == len(questions) - 1)

        if is_last:
            if st.button("✅ Submit Session",
                         type="primary", use_container_width=True,
                         key="btn_submit",
                         disabled=not answered):
                st.session_state.submitted = True
                st.session_state.screen    = "review"
                st.rerun()
        else:
            if st.button("Next Question →",
                         type="primary", use_container_width=True,
                         key="btn_next",
                         disabled=not answered):
                st.session_state.current_q += 1
                st.rerun()

    with nav_mid:
        if not answered:
            st.markdown(
                '<div style="text-align:center;font-size:0.8rem;color:#9CA3AF;">'
                'Answer this question to continue</div>',
                unsafe_allow_html=True)


# ── Review screen ─────────────────────────────────────────────────────────────
def render_review_screen():
    questions = st.session_state.get("active_questions", [])
    answers   = st.session_state.get("answers", {})
    bank      = st.session_state.get("active_bank", {})
    layer     = st.session_state.get("active_layer", "All Layers")

    if not questions:
        st.warning("No session data.")
        return

    # ── Grade ──
    answers_keyed = {}
    for i, q in enumerate(questions):
        qid = f"{i}_{q.get('id', i)}"
        answers_keyed[qid] = answers.get(qid)

    total_e, total_m, details, layer_stats, type_stats, missed_pairs = \
        aggregate_results(questions, answers_keyed)

    pct = (total_e / total_m * 100) if total_m else 0

    # ── Save session once ──
    if not st.session_state.get("session_saved"):
        elapsed = int(time.time() - st.session_state.get("start_time", time.time()))
        save_session(
            bank_id    = bank.get("id", "default"),
            bank_title = bank.get("title", ""),
            layer      = layer,
            score_pct  = pct,
            earned     = total_e,
            max_pts    = total_m,
            q_count    = len(questions),
            elapsed_sec= elapsed,
            miss_details = details,
        )
        st.session_state.session_saved = True

    # ── Score header ──
    pass_color = "#059669" if pct >= PASSING_PCT else "#EF4444"
    pass_label = "PASS" if pct >= PASSING_PCT else "BELOW PASSING"

    st.markdown(f"""
    <div style="background:{'#D1FAE5' if pct>=PASSING_PCT else '#FEE2E2'};
                border-radius:12px;padding:20px 24px;margin-bottom:18px;">
        <div style="font-size:0.8rem;font-weight:700;color:{pass_color};
                    text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">
            {pass_label}
        </div>
        <div style="font-size:2.4rem;font-weight:900;color:{pass_color};
                    line-height:1;margin-bottom:4px;">
            {pct:.1f}%
        </div>
        <div style="font-size:0.9rem;color:#374151;">
            {total_e} / {total_m} points · {len(questions)} questions ·
            Layer: {layer}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Layer readiness ──
    if layer_stats:
        st.markdown("**Layer breakdown:**")
        cols = st.columns(len(layer_stats))
        for i, (lyr, (e, m)) in enumerate(layer_stats.items()):
            lp = (e / m * 100) if m else 0
            ready, needed = check_layer_readiness(lyr, lp)
            info  = LAYER_INFO.get(lyr, {})
            color = "#059669" if ready else "#EF4444"
            cols[i].markdown(
                f'<div style="text-align:center;padding:8px;border:1px solid #E5E7EB;'
                f'border-radius:8px;">'
                f'<div style="font-size:0.7rem;color:#6B7280;">{info.get("label",lyr)}</div>'
                f'<div style="font-size:1.1rem;font-weight:800;color:{color};">{lp:.0f}%</div>'
                f'<div style="font-size:0.68rem;color:{color};">{"✓ Ready" if ready else f"Need {needed}%"}</div>'
                f'</div>',
                unsafe_allow_html=True)

    # ── Interference pair warnings ──
    if missed_pairs:
        pairs_str = ", ".join(set(missed_pairs))
        st.markdown(f"""
        <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;
                    padding:10px 14px;margin:12px 0;">
            🔴 <strong>High Priority — Missed interference pairs:</strong> {_html.escape(pairs_str)}<br>
            <span style="font-size:0.82rem;color:#6B7280;">
            Review these carefully — they appear on Layer D specifically because students confuse them.</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Question-by-Question Review")

    for i, (q, earned, max_pts, detail) in enumerate(details):
        qid    = f"{i}_{q.get('id', i)}"
        qt     = q["type"]
        ratio  = earned / max_pts if max_pts else 0
        banner = ("correct-banner" if ratio == 1
                  else "partial-banner" if ratio > 0
                  else "incorrect-banner")
        label  = ("✓ Correct" if ratio == 1
                  else f"Partial ({earned}/{max_pts} pts)" if ratio > 0
                  else "✗ Incorrect")
        score_color = "#059669" if ratio==1 else ("#D97706" if ratio>0 else "#DC2626")

        with st.expander(
            f"Q{i+1}. [{label}] {q['text'][:80]}{'…' if len(q['text'])>80 else ''}",
            expanded=(ratio < 1)):

            # Re-render locked question card
            render_qcard_top(q, i, len(questions))

            if qt == "MC":
                render_mc(q, qid, locked=True)
            elif qt == "SATA":
                render_sata(q, qid, locked=True)
            elif qt == "BOWTIE":
                render_bowtie(q, qid, locked=True)
            elif qt == "MATRIX":
                render_matrix(q, qid, locked=True)
            elif qt == "TREND":
                render_trend(q, qid, locked=True)
            elif qt == "CLOZE":
                render_cloze(q, qid, locked=True)

            # Score line
            st.markdown(
                f'<div style="font-size:0.88rem;font-weight:700;color:{score_color};'
                f'margin:8px 0;">{label} — {earned}/{max_pts} points</div>',
                unsafe_allow_html=True)

            # Per-option rationales (MC / SATA)
            if qt in ("MC", "SATA") and q.get("option_rationales"):
                st.markdown(
                    '<div style="font-size:0.8rem;font-weight:700;color:#374151;'
                    'margin-top:8px;margin-bottom:3px;">Per-Option Rationale:</div>',
                    unsafe_allow_html=True)
                or_map  = q["option_rationales"]
                correct = set(q.get("correct_answers", []))
                user    = set(detail.get("user", []))
                for key in sorted(or_map.keys()):
                    rat   = or_map[key]
                    is_c  = key in correct
                    is_u  = key in user
                    icon  = "✓" if is_c else "✗"
                    color = "#059669" if is_c else "#EF4444"
                    you   = " ← you chose" if is_u else ""
                    st.markdown(
                        f'<div style="font-size:0.82rem;padding:3px 0;">'
                        f'<span style="color:{color};font-weight:700;">{icon} {h(key)}.</span> '
                        f'{h(rat)}<em style="color:#9CA3AF;">{you}</em></div>',
                        unsafe_allow_html=True)

            # Cell rationales (MATRIX)
            # Build id→label map so we show the actual row text, not 'r1','r2' etc.
            if qt == "MATRIX" and q.get("cell_rationales"):
                row_label_map = {
                    row["id"]: row["label"]
                    for row in q.get("matrix", {}).get("rows", [])
                }
                st.markdown(
                    '<div style="font-size:0.8rem;font-weight:700;color:#374151;'
                    'margin-top:8px;margin-bottom:3px;">Row Rationale:</div>',
                    unsafe_allow_html=True)
                for rid, rat in q["cell_rationales"].items():
                    display_label = row_label_map.get(rid, rid)  # fallback to id if not found
                    st.markdown(
                        f'<div style="font-size:0.82rem;padding:4px 0;color:#374151;'
                        f'border-bottom:1px solid #F3F4F6;">'
                        f'<b>{h(display_label)}:</b> {h(rat)}</div>',
                        unsafe_allow_html=True)

            # Bowtie rationales
            if qt == "BOWTIE" and q.get("bowtie_rationales"):
                br = q["bowtie_rationales"]
                st.markdown(
                    '<div style="font-size:0.8rem;font-weight:700;color:#374151;'
                    'margin-top:8px;margin-bottom:3px;">Bowtie Rationale:</div>',
                    unsafe_allow_html=True)
                for part in ("condition", "actions", "parameters"):
                    if part in br:
                        st.markdown(
                            f'<div style="font-size:0.82rem;padding:2px 0;color:#374151;">'
                            f'<b style="text-transform:capitalize;">{part}:</b> {h(br[part])}</div>',
                            unsafe_allow_html=True)

            # Overall rationale
            rationale = q.get("rationale", "")
            if rationale:
                source = q.get("source_reference", "")
                src_html = (f' <span style="color:#9CA3AF;font-style:italic;">'
                            f'({h(source)})</span>' if source else "")
                st.markdown(
                    f'<div style="background:#F0FAFA;border-left:3px solid #01696F;'
                    f'border-radius:0 6px 6px 0;padding:10px 14px;margin-top:10px;">'
                    f'<div style="font-size:0.78rem;font-weight:700;color:#01696F;'
                    f'margin-bottom:4px;">📚 Rationale{src_html}</div>'
                    f'<div style="font-size:0.85rem;color:#1E293B;line-height:1.6;">'
                    f'{h(rationale)}</div>'
                    f'</div>',
                    unsafe_allow_html=True)

            # Miss-type diagnosis
            miss_type = detail.get("inferred_miss_type", "")
            if miss_type and earned < max_pts:
                explanation = get_miss_explanation(miss_type)
                st.markdown(
                    f'<div style="background:#FFFBEB;border:1px solid #FDE68A;'
                    f'border-radius:6px;padding:8px 12px;margin-top:8px;">'
                    f'<div style="font-size:0.78rem;font-weight:700;color:#92400E;">'
                    f'🔎 Inferred Miss Type: {h(miss_type)}</div>'
                    f'<div style="font-size:0.82rem;color:#78350F;margin-top:3px;">'
                    f'{h(explanation)}</div>'
                    f'</div>',
                    unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🏠 Back to Home", type="primary", key="btn_review_home"):
        st.session_state.screen = "home"
        st.rerun()


# ── Progress screen ────────────────────────────────────────────────────────────
def render_progress_screen(banks):
    st.markdown("## Progress History")

    all_sessions = get_session_history(limit=50)
    if not all_sessions:
        st.info("No sessions recorded yet. Complete your first practice session to see progress here.")
        return

    # Session table
    import pandas as pd
    rows = []
    for s in all_sessions:
        rows.append({
            "Date": s["ts"][:10],
            "Bank": s["bank_title"] or s["bank_id"],
            "Layer": s["layer"] or "All",
            "Score": f"{s['score_pct']:.1f}%",
            "Earned": f"{s['earned']}/{s['max_pts']}",
            "Questions": s["q_count"],
            "Time (min)": f"{s['elapsed_sec']//60}" if s['elapsed_sec'] else "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # Per-bank mastery
    if banks:
        st.markdown("### Layer Mastery by Bank")
        for bank in banks:
            bid     = bank.get("id","")
            title   = bank.get("title", bid)
            mastery = get_layer_mastery_summary(bid)
            if mastery:
                st.markdown(f"**{title}**")
                mcols = st.columns(len(LAYER_ORDER))
                for i, lyr in enumerate(LAYER_ORDER):
                    d = mastery.get(lyr, {})
                    if not d:
                        mcols[i].markdown(
                            f'<div style="text-align:center;">'
                            f'<div style="font-size:0.7rem;color:#9CA3AF;">'
                            f'{LAYER_INFO[lyr]["label"]}</div>'
                            f'<div style="color:#E5E7EB;">—</div></div>',
                            unsafe_allow_html=True)
                    else:
                        lp    = d["last_pct"]
                        ready = d["is_mastered"]
                        color = "#059669" if ready else "#EF4444"
                        mcols[i].markdown(
                            f'<div style="text-align:center;border:1px solid #E5E7EB;'
                            f'border-radius:8px;padding:6px 2px;">'
                            f'<div style="font-size:0.68rem;color:#6B7280;">'
                            f'{LAYER_INFO[lyr]["label"]}</div>'
                            f'<div style="font-size:1.1rem;font-weight:800;color:{color};">'
                            f'{lp:.0f}%</div>'
                            f'<div style="font-size:0.65rem;color:{color};">'
                            f'{"✓" if ready else "✗"} {d["session_count"]} sessions</div>'
                            f'</div>',
                            unsafe_allow_html=True)

                # Priority pairs
                pairs = get_priority_pairs(bid)
                if pairs:
                    st.markdown("**High-miss interference pairs:**")
                    for p in pairs[:5]:
                        st.markdown(
                            f'<div style="font-size:0.82rem;color:#EF4444;font-weight:600;">'
                            f'⚠ {h(p["pair_name"])} — missed {p["miss_count"]} time{"s" if p["miss_count"]!=1 else ""}</div>',
                            unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    inject_css()
    banks, errors = load_banks()
    render_sidebar(banks, errors)

    if "screen" not in st.session_state:
        st.session_state.screen = "home"

    screen = st.session_state.screen

    if screen == "home":
        render_home(banks)
    elif screen == "test":
        render_test_screen()
    elif screen == "review":
        render_review_screen()
    elif screen == "progress":
        render_progress_screen(banks)
    else:
        st.session_state.screen = "home"
        st.rerun()


if __name__ == "__main__":
    main()

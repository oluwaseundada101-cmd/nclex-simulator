"""
home.py — Home screen renderer.

Shows:
  - Welcome banner + brief explanation of what this app does
  - Framework Layer System explainer (all 6 layers, thresholds, stop rules)
  - 8-day Phase 6 study schedule
  - Question bank cards with layer pills and question counts
  - Session settings (layer filter, mode, question count, timer toggle)
  - Progress summary from SQLite (if any prior sessions)
  - Guided Mode toggle (stop-rule enforcement)
"""
import streamlit as st
from config import LAYER_INFO, LAYER_ORDER, LAYER_STOP_RULES, PASSING_PCT
from persistence import get_session_history, get_layer_mastery_summary, get_weak_concepts


# ── CSS injected once by app.py — these helpers assume it exists ─────────────


def _badge(cls, text):
    return f'<span class="badge {cls}">{text}</span>'


def _layer_badge(lyr):
    info = LAYER_INFO.get(lyr, {})
    return _badge(info.get("cls", ""), info.get("label", lyr))


# ── Welcome banner ─────────────────────────────────────────────────────────────

def render_welcome():
    st.markdown("""
    <div style="background:linear-gradient(135deg,#01696F 0%,#0C4E54 100%);
                border-radius:12px;padding:28px 32px;margin-bottom:24px;">
        <div style="color:#E0F5F5;font-size:0.8rem;font-weight:700;
                    letter-spacing:0.12em;text-transform:uppercase;margin-bottom:6px;">
            NGN NCLEX Simulator · Unit 4 HCIIIA
        </div>
        <div style="color:#FFFFFF;font-size:1.55rem;font-weight:800;line-height:1.25;
                    margin-bottom:10px;">
            Mastery-Based Clinical Reasoning Practice
        </div>
        <div style="color:#A7D8D8;font-size:0.93rem;line-height:1.6;max-width:680px;">
            This simulator uses your professor's <strong style="color:#fff;">layered mastery framework</strong>
            to build exam-ready clinical judgment — not just memorization.
            Questions are drawn directly from your Unit 4 lecture slides, hybrid supplement,
            and mastery guide, covering all 6 Next Generation NCLEX (NGN) item formats.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── What is this? New-user explainer ─────────────────────────────────────────

def render_new_user_explainer():
    with st.expander("👋 New here? Start reading this first", expanded=False):
        st.markdown("""
        ### How this simulator works

        **Step 1 — Pick a Layer**
        Your professor's framework breaks studying into 6 skill layers (see below).
        Start with **Layer A** (recall facts), then work up to **Layer C** (clinical judgment)
        and **NGN** (advanced question formats). Each layer has a *stop rule* — a minimum score
        you should hit before moving on.

        **Step 2 — Take a session**
        Choose how many questions, set a timer, and click **Start Practice**.
        You cannot go back to a previous question until the session is complete — just like
        the real NCLEX.

        **Step 3 — Review your results**
        After submitting, you'll see your score, a per-question rationale referencing your
        course materials, and an *inferred miss type* explaining what went wrong.

        **Step 4 — Track progress**
        Your scores are saved automatically. The Progress tab shows layer-by-layer mastery
        history and your highest-miss concepts.

        ---
        ### Question formats on this simulator (all active on real NCLEX NGN)

        | Format | What it tests |
        |--------|--------------|
        | **Multiple Choice (MC)** | Single best answer |
        | **Select All That Apply (SATA)** | Multiple correct answers |
        | **Bowtie** | Condition + actions + parameters — all three parts |
        | **Matrix Grid** | One choice per finding (e.g., Expected / Unexpected) |
        | **Trend** | Data over time → Improving / Worsening / No change |
        | **Drop-Down Cloze** | Fill in blanks from a dropdown within a sentence |

        ---
        ### What is the framework pipeline?

        Your professor provided a *question-generation pipeline* that defines exactly
        how each question type is built: what layer it targets, what clinical reasoning
        it requires, and what common errors it catches. This app implements that framework —
        every question is tagged with a layer, a concept bucket, and (where relevant)
        an interference pair showing which two drug/disease facts students most often confuse.
        """)


# ── Layer system explainer ────────────────────────────────────────────────────

LAYER_DETAILS = {
    "A": {
        "pct":   "~20% of questions",
        "desc":  "Pure recall — isolated facts, definitions, normal values, drug names.",
        "eg":    "\"What is the TRUE urine output formula for a patient with CBI?\"",
        "stop":  "95%",
        "color": "#059669",
    },
    "A-Applied": {
        "pct":   "~12% of questions",
        "desc":  "Same facts as Layer A, but hidden inside a clinical scenario. Tests whether you recognize a known fact when it is disguised.",
        "eg":    "\"A nurse notes the drainage bag reads 3,200 mL after 2,000 mL of irrigation. What does this indicate?\"",
        "stop":  "90%",
        "color": "#10B981",
    },
    "B": {
        "pct":   "~15% of questions",
        "desc":  "Mechanism and physiology — why a drug works, how a complication develops.",
        "eg":    "\"Why must Finasteride tablets never be crushed and handled by pregnant individuals?\"",
        "stop":  "68%",
        "color": "#3B82F6",
    },
    "C": {
        "pct":   "~45–50% of questions",
        "desc":  "Clinical judgment — priority actions, SATA, Bowtie, Matrix. The largest and hardest layer. This is what the real NCLEX tests most.",
        "eg":    "\"A patient 4 hours post-TURP has bright red urine and clots. What action is the PRIORITY?\"",
        "stop":  "90%",
        "color": "#8B5CF6",
    },
    "D": {
        "pct":   "~8–10% of questions",
        "desc":  "Confusable pairs — questions designed around concepts students routinely mix up (e.g., Prazosin vs Finasteride, Enteral vs TPN).",
        "eg":    "\"Which BPH medication requires first-dose administration at bedtime?\"",
        "stop":  "85%",
        "color": "#EF4444",
    },
    "NGN": {
        "pct":   "~8–10% of questions",
        "desc":  "Full NGN format items: Bowtie, Trend, Matrix, Drop-Down Cloze — all formats active on the 2024+ NCLEX NGN exam.",
        "eg":    "Bowtie: Identify the condition, 2 actions to take, 2 parameters to monitor.",
        "stop":  "68%",
        "color": "#F59E0B",
    },
}


def render_layer_explainer():
    st.markdown("""
    <div style="margin-bottom:8px;">
        <div style="font-size:1.1rem;font-weight:800;color:#111827;margin-bottom:4px;">
            The 6-Layer Mastery Framework
        </div>
        <div style="font-size:0.85rem;color:#6B7280;">
            Your professor's framework — each layer builds on the last.
            Hit the stop rule before advancing.
        </div>
    </div>
    """, unsafe_allow_html=True)

    for lyr in LAYER_ORDER:
        d = LAYER_DETAILS[lyr]
        info = LAYER_INFO[lyr]
        st.markdown(f"""
        <div style="border:1px solid #E5E7EB;border-left:4px solid {d['color']};
                    border-radius:8px;padding:12px 16px;margin-bottom:8px;
                    background:#FAFAFA;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <span style="font-weight:700;font-size:0.95rem;color:#111827;">
                        {info['long']}
                    </span>
                    <span style="font-size:0.78rem;color:#9CA3AF;margin-left:8px;">
                        {d['pct']}
                    </span>
                </div>
                <div style="font-size:0.78rem;font-weight:700;color:{d['color']};
                            background:{d['color']}15;border-radius:12px;
                            padding:2px 10px;white-space:nowrap;">
                    Stop rule: {d['stop']}
                </div>
            </div>
            <div style="font-size:0.85rem;color:#374151;margin-top:5px;">
                {d['desc']}
            </div>
            <div style="font-size:0.8rem;color:#6B7280;font-style:italic;margin-top:4px;">
                e.g. {d['eg']}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Study schedule ────────────────────────────────────────────────────────────

def render_study_schedule():
    st.markdown("""
    <div style="font-size:1.05rem;font-weight:800;color:#111827;
                margin-bottom:8px;margin-top:4px;">
        Phase 6 — 8-Day Exam Prep Schedule
    </div>
    """, unsafe_allow_html=True)

    schedule = [
        ("Day 1",   "Layer A",       "Recall Anchors",          "badge-layer-a"),
        ("Day 2",   "Layer A-Applied","Facts in Disguise",      "badge-layer-aa"),
        ("Day 3",   "Layer B",       "Mechanism / Physiology",  "badge-layer-b"),
        ("Day 4–5", "Layer C",       "Clinical Judgment",       "badge-layer-c"),
        ("Day 6",   "Layer D",       "Confusable Pairs",        "badge-layer-d"),
        ("Day 7–8", "NGN",           "All NGN Formats",         "badge-layer-ngn"),
        ("Exam Eve","Full Timed",    "All layers, timed",       "badge-ngn"),
    ]

    rows_html = ""
    for day, layer, desc, cls in schedule:
        rows_html += f"""
        <tr>
            <td style="font-weight:700;color:#374151;padding:7px 10px;white-space:nowrap;">
                {day}
            </td>
            <td style="padding:7px 10px;">
                <span class="badge {cls}">{layer}</span>
            </td>
            <td style="color:#6B7280;font-size:0.85rem;padding:7px 10px;">
                {desc}
            </td>
        </tr>
        """

    st.markdown(f"""
    <div style="overflow-x:auto;margin-bottom:12px;">
        <table style="width:100%;border-collapse:collapse;
                      border:1px solid #E5E7EB;border-radius:8px;">
            <thead>
                <tr style="background:#F9FAFB;">
                    <th style="text-align:left;padding:8px 10px;font-size:0.8rem;
                               color:#6B7280;border-bottom:1px solid #E5E7EB;">Day</th>
                    <th style="text-align:left;padding:8px 10px;font-size:0.8rem;
                               color:#6B7280;border-bottom:1px solid #E5E7EB;">Focus</th>
                    <th style="text-align:left;padding:8px 10px;font-size:0.8rem;
                               color:#6B7280;border-bottom:1px solid #E5E7EB;">Description</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)


# ── Progress summary ──────────────────────────────────────────────────────────

def render_progress_summary(bank_id):
    sessions = get_session_history(bank_id, limit=5)
    if not sessions:
        return

    st.markdown("""
    <div style="font-size:1.05rem;font-weight:800;color:#111827;
                margin-bottom:8px;margin-top:4px;">
        Your Recent Progress
    </div>
    """, unsafe_allow_html=True)

    mastery = get_layer_mastery_summary(bank_id)
    weak    = get_weak_concepts(bank_id, limit=3)

    cols = st.columns(len(LAYER_ORDER))
    for i, lyr in enumerate(LAYER_ORDER):
        d = mastery.get(lyr, {})
        if not d:
            cols[i].markdown(
                f'<div style="text-align:center;padding:8px 4px;">'
                f'<div style="font-size:0.7rem;color:#9CA3AF;">'
                f'{LAYER_INFO[lyr]["label"]}</div>'
                f'<div style="font-size:0.85rem;color:#CBD5E1;">—</div>'
                f'</div>', unsafe_allow_html=True)
        else:
            pct     = d["last_pct"]
            thr     = d["threshold"]
            color   = "#059669" if d["is_mastered"] else ("#F59E0B" if pct >= thr*0.8 else "#EF4444")
            status  = "✓ Mastered" if d["is_mastered"] else f"Need {thr}%"
            cols[i].markdown(
                f'<div style="text-align:center;padding:8px 4px;'
                f'border:1px solid #E5E7EB;border-radius:8px;margin:2px;">'
                f'<div style="font-size:0.7rem;color:#6B7280;">'
                f'{LAYER_INFO[lyr]["label"]}</div>'
                f'<div style="font-size:1.2rem;font-weight:800;color:{color};">'
                f'{pct:.0f}%</div>'
                f'<div style="font-size:0.68rem;color:{color};">{status}</div>'
                f'</div>', unsafe_allow_html=True)

    if weak:
        concepts = " &nbsp;·&nbsp; ".join(
            f'<span style="color:#EF4444;font-weight:600;">{w["concept_bucket"]}</span>'
            f' ({w["miss_count"]} miss{"es" if w["miss_count"]!=1 else ""})'
            for w in weak)
        st.markdown(
            f'<div style="font-size:0.82rem;color:#6B7280;margin-top:6px;">'
            f'⚠️ High-miss concepts: {concepts}</div>',
            unsafe_allow_html=True)


# ── Bank selection cards ──────────────────────────────────────────────────────

def render_bank_card(bank, idx, selected_bank_idx):
    qs   = bank.get("questions", [])
    n    = len(qs)
    title = bank.get("title", f"Question Bank {idx+1}")
    desc  = bank.get("description", "")
    bid   = bank.get("id", str(idx))

    # Layer distribution
    layer_counts = {}
    type_counts  = {}
    for q in qs:
        l = q.get("layer", "?")
        layer_counts[l] = layer_counts.get(l, 0) + 1
        t = q.get("type", "?")
        type_counts[t]  = type_counts.get(t, 0) + 1

    pills_html = "".join(
        f'<span class="badge {LAYER_INFO.get(l, {}).get("cls","")}">'
        f'{LAYER_INFO.get(l, {}).get("label", l)} {c}</span> '
        for l, c in sorted(layer_counts.items(),
                            key=lambda x: LAYER_ORDER.index(x[0])
                            if x[0] in LAYER_ORDER else 99))

    type_pills_html = "".join(
        f'<span class="badge" style="background:#F1F5F9;color:#475569;'
        f'border:1px solid #CBD5E1;font-size:0.72rem;">{t} {c}</span> '
        for t, c in sorted(type_counts.items()))

    selected = (idx == selected_bank_idx)
    border   = "border:2px solid #01696F;" if selected else "border:1px solid #E5E7EB;"
    bg       = "background:#F0FAFA;" if selected else "background:#FFFFFF;"

    st.markdown(f"""
    <div style="{border}{bg}border-radius:10px;padding:14px 16px;
                margin-bottom:10px;cursor:pointer;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div style="font-weight:700;font-size:0.97rem;color:#111827;">{title}</div>
            <div style="font-size:0.82rem;color:#6B7280;font-weight:600;">
                {n} question{"s" if n != 1 else ""}
            </div>
        </div>
        {"<div style='font-size:0.82rem;color:#6B7280;margin-top:3px;'>"+desc+"</div>" if desc else ""}
        <div style="margin-top:8px;">{pills_html}</div>
        <div style="margin-top:4px;">{type_pills_html}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Session settings ──────────────────────────────────────────────────────────

def render_session_settings(banks, bank_idx):
    """Returns (bank, layer_filter, q_count, use_timer, timer_minutes, guided_mode)"""
    bank = banks[bank_idx] if banks else None
    qs   = bank.get("questions", []) if bank else []

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(
            '<div style="font-weight:700;font-size:0.85rem;color:#374151;'
            'margin-bottom:4px;">Layer Filter</div>',
            unsafe_allow_html=True)

        all_layers_in_bank = sorted(
            set(q.get("layer","?") for q in qs),
            key=lambda x: LAYER_ORDER.index(x) if x in LAYER_ORDER else 99)
        layer_options = ["All Layers"] + all_layers_in_bank

        layer_filter = st.selectbox(
            "", layer_options,
            key="home_layer_filter",
            label_visibility="collapsed")

        # Layer unlock check
        if layer_filter != "All Layers" and bank:
            from persistence import layer_is_unlocked
            unlocked, reason = layer_is_unlocked(bank.get("id",""), layer_filter)
            if not unlocked:
                st.warning(f"⚠️ {reason}")

    with col2:
        st.markdown(
            '<div style="font-weight:700;font-size:0.85rem;color:#374151;'
            'margin-bottom:4px;">Study Mode</div>',
            unsafe_allow_html=True)
        mode = st.selectbox(
            "", ["HYBRID (Prof + NCLEX)", "PROF-FIRST", "NCLEX-FIRST"],
            key="home_mode",
            label_visibility="collapsed")

    col3, col4 = st.columns([1, 1])

    filtered_qs = (
        [q for q in qs if q.get("layer") == layer_filter]
        if layer_filter != "All Layers" else qs)

    n_available = len(filtered_qs)

    with col3:
        st.markdown(
            '<div style="font-weight:700;font-size:0.85rem;color:#374151;'
            'margin-bottom:4px;">Number of Questions</div>',
            unsafe_allow_html=True)
        q_count = st.slider(
            "", 1, max(1, n_available),
            min(10, n_available),
            key="home_q_count",
            label_visibility="collapsed")
        st.caption(f"{n_available} questions available in this filter")

    with col4:
        st.markdown(
            '<div style="font-weight:700;font-size:0.85rem;color:#374151;'
            'margin-bottom:4px;">Timer</div>',
            unsafe_allow_html=True)
        use_timer = st.toggle("Enable timer", value=True, key="home_use_timer")
        if use_timer:
            timer_minutes = st.number_input(
                "Minutes", min_value=5, max_value=180,
                value=q_count * 2, step=5,
                key="home_timer_min",
                label_visibility="visible")
        else:
            timer_minutes = 0

    st.markdown(
        '<div style="font-weight:700;font-size:0.85rem;color:#374151;'
        'margin-bottom:4px;margin-top:8px;">Guided Mode (Stop-Rule Enforcement)</div>',
        unsafe_allow_html=True)
    guided = st.toggle(
        "Warn me before advancing a layer I haven't mastered",
        value=st.session_state.get("guided_mode", False),
        key="home_guided_mode")

    return bank, layer_filter, q_count, use_timer, timer_minutes, guided


# ── Main home page render ─────────────────────────────────────────────────────

def render_home(banks):
    render_welcome()
    render_new_user_explainer()

    left, right = st.columns([6, 4])

    with left:
        render_layer_explainer()
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        render_study_schedule()

    with right:
        # Bank picker
        st.markdown("""
        <div style="font-size:1.05rem;font-weight:800;color:#111827;
                    margin-bottom:8px;">Question Banks</div>
        """, unsafe_allow_html=True)

        if not banks:
            st.warning("No question banks loaded. Place a `questions.json` file "
                       "in the app folder and click **Reload Question Banks** in the sidebar.")
        else:
            bank_titles = [b.get("title", f"Bank {i+1}") for i, b in enumerate(banks)]
            bank_idx    = st.radio(
                "Select bank",
                range(len(banks)),
                format_func=lambda i: bank_titles[i],
                key="home_bank_idx",
                label_visibility="collapsed")

            for i, bank in enumerate(banks):
                render_bank_card(bank, i, bank_idx)

            # Progress summary for selected bank
            if banks:
                bid = banks[bank_idx].get("id", str(bank_idx))
                render_progress_summary(bid)

        # Session settings
        st.markdown("""
        <div style="font-size:1.05rem;font-weight:800;color:#111827;
                    margin-bottom:8px;margin-top:12px;">Session Settings</div>
        """, unsafe_allow_html=True)

        if banks:
            bank_idx_val = st.session_state.get("home_bank_idx", 0)
            bank, layer_filter, q_count, use_timer, timer_minutes, guided = \
                render_session_settings(banks, bank_idx_val)

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            if st.button("▶  Start Practice Session",
                         type="primary", use_container_width=True,
                         key="btn_start"):

                # Guided mode: check unlock status
                if guided and layer_filter != "All Layers" and bank:
                    from persistence import layer_is_unlocked
                    unlocked, reason = layer_is_unlocked(bank.get("id",""), layer_filter)
                    if not unlocked:
                        if not st.session_state.get("guided_override_confirmed"):
                            st.warning(f"⚠️ **Guided Mode**: {reason}")
                            if st.button("I understand — continue anyway",
                                         key="btn_guided_override"):
                                st.session_state.guided_override_confirmed = True
                                st.rerun()
                            return
                    else:
                        st.session_state.guided_override_confirmed = False

                # Filter and shuffle questions
                import random
                qs_pool = bank.get("questions", [])
                if layer_filter != "All Layers":
                    qs_pool = [q for q in qs_pool if q.get("layer") == layer_filter]

                selected_qs = random.sample(qs_pool, min(q_count, len(qs_pool)))

                # Store in session state
                st.session_state.active_bank       = bank
                st.session_state.active_questions  = selected_qs
                st.session_state.active_layer      = layer_filter
                st.session_state.guided_mode       = guided
                st.session_state.use_timer         = use_timer
                st.session_state.timer_minutes     = timer_minutes
                st.session_state.answers           = {}
                st.session_state.current_q         = 0
                st.session_state.submitted          = False
                st.session_state.start_time        = __import__("time").time()
                st.session_state.session_saved     = False
                st.session_state.screen            = "test"
                st.rerun()

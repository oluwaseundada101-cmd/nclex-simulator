"""
renderers.py — All question-type rendering logic.
- html.escape() on ALL dynamic content before HTML injection
- Matrix uses st.radio per row (true single-choice, no checkbox artifacts)
- Bowtie: schema-driven counts (condition_count, action_count, param_count)
- All renderers return nothing; they write to st.session_state.answers[qid]
"""
import html
import streamlit as st
from config import TYPE_BADGE, LAYER_INFO


# ── Utility: safe HTML injection ─────────────────────────────────────────────

def h(s):
    """Escape a dynamic string for safe HTML injection."""
    return html.escape(str(s) if s is not None else "")


# ── Badge HTML ────────────────────────────────────────────────────────────────

def type_badge_html(qt):
    cls, label = TYPE_BADGE.get(qt, ("badge-ngn", "NGN"))
    return f'<span class="badge {h(cls)}">{h(label)}</span>'


def layer_badge_html(q):
    lyr  = q.get("layer", "")
    sub  = q.get("layer_subtype", "")
    info = LAYER_INFO.get(lyr, {})
    out  = (f'<span class="badge {h(info.get("cls",""))}">'
            f'{h(info.get("long", lyr))}</span>') if info else ""
    if sub:
        out += (f'<span class="badge" style="background:#F1F5F9;color:#64748B;'
                f'border:1px solid #CBD5E1;">{h(sub)}</span>')
    return out


def meta_html(q):
    parts = []
    if q.get("nclex_category"):    parts.append(f'<b>Category:</b> {h(q["nclex_category"])}')
    if q.get("nclex_subcategory"): parts.append(f'<b>Sub:</b> {h(q["nclex_subcategory"])}')
    if q.get("concept_bucket"):    parts.append(f'<b>Concept:</b> {h(q["concept_bucket"])}')
    if q.get("interference_pair"): parts.append(f'<b>Interference:</b> {h(q["interference_pair"])}')
    return " &nbsp;·&nbsp; ".join(parts)


# ── Question card top (scenario + stem + meta) ────────────────────────────────

def render_qcard_top(q, idx, total):
    qt = q["type"]
    scenario = q.get("case_study", "")

    scenario_html = ""
    if scenario:
        scenario_html = (
            f'<div class="scenario-stripe">'
            f'<div class="scenario-label">📋 Clinical Scenario</div>'
            f'{h(scenario)}'
            f'</div>'
        )

    ngn_badge = ('<span class="badge badge-ngn">NGN</span>'
                 if q.get("ngn") else "")

    stem_html = (
        f'<div class="qstem">'
        f'<div class="qnum">Question {idx+1} of {total}</div>'
        f'<div class="badge-row">'
        f'{type_badge_html(qt)}{ngn_badge}{layer_badge_html(q)}'
        f'</div>'
        f'<div class="stem-text">{h(q["text"])}</div>'
        f'</div>'
    )

    m = meta_html(q)
    meta_footer = f'<div class="meta-stripe">{m}</div>' if m else ""

    st.markdown(
        f'<div class="qcard">{scenario_html}{stem_html}{meta_footer}</div>',
        unsafe_allow_html=True
    )


# ── MC ────────────────────────────────────────────────────────────────────────

def render_mc(q, qid, locked):
    opts = q["options"]
    keys = sorted(opts.keys())
    cur  = st.session_state.answers.get(qid, [])
    cur_val = cur[0] if cur else None

    if locked:
        for k in keys:
            sel   = k == cur_val
            icon  = "◉" if sel else "○"
            color = "#01696F" if sel else "#6B7280"
            st.markdown(
                f'<div style="padding:5px 0;color:{color};">'
                f'{icon} <b>{h(k)}.</b> {h(opts[k])}</div>',
                unsafe_allow_html=True)
    else:
        idx_d  = keys.index(cur_val) if cur_val in keys else None
        choice = st.radio(
            "", keys, index=idx_d,
            format_func=lambda k: f"{k}.  {opts[k]}",
            key=f"mc_{qid}", label_visibility="collapsed")
        st.session_state.answers[qid] = [choice] if choice else []


# ── SATA ──────────────────────────────────────────────────────────────────────

def render_sata(q, qid, locked):
    opts = q["options"]
    keys = sorted(opts.keys())
    cur  = st.session_state.answers.get(qid, [])

    st.markdown(
        '<div style="color:#01696F;font-size:0.82rem;font-weight:600;'
        'margin-bottom:6px;">Select ALL that apply</div>',
        unsafe_allow_html=True)

    if locked:
        for k in keys:
            icon  = "☑" if k in cur else "☐"
            color = "#01696F" if k in cur else "#6B7280"
            st.markdown(
                f'<div style="padding:4px 0;color:{color};">'
                f'{icon} <b>{h(k)}.</b> {h(opts[k])}</div>',
                unsafe_allow_html=True)
    else:
        sel = st.multiselect(
            "", keys, default=cur,
            format_func=lambda k: f"{k}.  {opts[k]}",
            key=f"sata_{qid}", label_visibility="collapsed")
        st.session_state.answers[qid] = sel


# ── BOWTIE ────────────────────────────────────────────────────────────────────

def render_bowtie(q, qid, locked):
    """
    Schema-driven Bowtie:
    - condition_count: how many to select in center (default 1)
    - action_count: how many to select on left (default 2)
    - param_count:  how many to select on right (default 2)
    Backward-compatible with old causes/actions/outcomes keys.
    """
    bt = q["bowtie"]
    c_opts = bt.get("condition_options") or bt.get("causes", [])
    a_opts = bt.get("actions_to_take")   or bt.get("actions", [])
    p_opts = bt.get("parameters_to_monitor") or bt.get("outcomes", [])

    # Schema-driven counts (defaults to 1/2/2)
    c_count = bt.get("condition_count", 1)
    a_count = bt.get("action_count",    2)
    p_count = bt.get("param_count",     2)

    cur = st.session_state.answers.get(qid, {})

    st.markdown(
        f'<div class="type-banner banner-bowtie">Bowtie — Select the '
        f'<strong>condition</strong> (center), '
        f'<strong>{a_count} action{"s" if a_count>1 else ""} to take</strong> (left), and '
        f'<strong>{p_count} parameter{"s" if p_count>1 else ""} to monitor</strong> (right).</div>',
        unsafe_allow_html=True)

    col_a, col_arr1, col_c, col_arr2, col_p = st.columns([5, 1, 4, 1, 5])

    # ── LEFT: Actions ──
    with col_a:
        st.markdown(
            '<div style="background:#F8FAFC;border:1px solid #CBD5E1;'
            'border-radius:8px;padding:12px;">'
            '<div class="bt-header">Actions to Take</div>'
            f'<div style="font-size:0.78rem;color:#9CA3AF;margin-bottom:6px;">'
            f'Select {a_count}</div></div>',
            unsafe_allow_html=True)
        if locked:
            chosen_a = cur.get("actions", [])
            for opt in a_opts:
                sel   = opt in chosen_a
                icon  = "☑" if sel else "☐"
                color = "#01696F" if sel else "#6B7280"
                st.markdown(
                    f'<div style="padding:3px 0;font-size:0.87rem;color:{color};">'
                    f'{icon} {h(opt)}</div>',
                    unsafe_allow_html=True)
        else:
            chosen_a = st.multiselect(
                "", a_opts, default=cur.get("actions", []),
                key=f"bt_a_{qid}", label_visibility="collapsed",
                max_selections=a_count)
            cur["actions"] = chosen_a
            st.session_state.answers[qid] = cur

    # Arrow
    with col_arr1:
        st.markdown(
            '<div style="text-align:center;padding-top:60px;'
            'font-size:1.6rem;color:#94A3B8;">→</div>',
            unsafe_allow_html=True)

    # ── CENTER: Condition ──
    with col_c:
        st.markdown(
            '<div style="background:#FFFBEB;border:2px solid #F59E0B;'
            'border-radius:8px;padding:12px;">'
            '<div class="bt-center-header" style="text-align:center;">'
            'Condition Most Likely Experiencing</div>'
            f'<div style="font-size:0.78rem;color:#B45309;margin-bottom:6px;'
            f'text-align:center;">Select {c_count}</div></div>',
            unsafe_allow_html=True)
        if locked:
            chosen_c = cur.get("condition", "")
            for opt in c_opts:
                icon  = "◉" if opt == chosen_c else "○"
                color = "#92400E" if opt == chosen_c else "#6B7280"
                st.markdown(
                    f'<div style="padding:3px 0;font-size:0.87rem;color:{color};">'
                    f'{icon} {h(opt)}</div>',
                    unsafe_allow_html=True)
        else:
            idx_d    = c_opts.index(cur["condition"]) if cur.get("condition") in c_opts else None
            chosen_c = st.radio(
                "", c_opts, index=idx_d,
                key=f"bt_c_{qid}", label_visibility="collapsed")
            cur["condition"] = chosen_c
            st.session_state.answers[qid] = cur

    # Arrow
    with col_arr2:
        st.markdown(
            '<div style="text-align:center;padding-top:60px;'
            'font-size:1.6rem;color:#94A3B8;">→</div>',
            unsafe_allow_html=True)

    # ── RIGHT: Parameters ──
    with col_p:
        st.markdown(
            '<div style="background:#F8FAFC;border:1px solid #CBD5E1;'
            'border-radius:8px;padding:12px;">'
            '<div class="bt-header">Parameters to Monitor</div>'
            f'<div style="font-size:0.78rem;color:#9CA3AF;margin-bottom:6px;">'
            f'Select {p_count}</div></div>',
            unsafe_allow_html=True)
        if locked:
            chosen_p = cur.get("parameters", [])
            for opt in p_opts:
                sel   = opt in chosen_p
                icon  = "☑" if sel else "☐"
                color = "#065F46" if sel else "#6B7280"
                st.markdown(
                    f'<div style="padding:3px 0;font-size:0.87rem;color:{color};">'
                    f'{icon} {h(opt)}</div>',
                    unsafe_allow_html=True)
        else:
            chosen_p = st.multiselect(
                "", p_opts, default=cur.get("parameters", []),
                key=f"bt_p_{qid}", label_visibility="collapsed",
                max_selections=p_count)
            cur["parameters"] = chosen_p
            st.session_state.answers[qid] = cur


# ── MATRIX ────────────────────────────────────────────────────────────────────

def render_matrix(q, qid, locked):
    """
    FIX: True single-choice per row using st.radio (horizontal),
    NOT per-cell checkboxes. Eliminates the multi-select artifact.
    """
    rows    = q["matrix"]["rows"]
    columns = q["matrix"]["columns"]
    cur     = st.session_state.answers.get(qid, {})

    st.markdown(
        '<div class="type-banner banner-matrix">'
        'Matrix Grid — For each finding, select the correct column.</div>',
        unsafe_allow_html=True)

    # Header row
    ncols       = len(columns)
    col_widths  = [4] + [2] * ncols
    hcols       = st.columns(col_widths)
    hcols[0].markdown(
        '<div style="font-weight:700;font-size:0.82rem;color:#374151;'
        'padding:6px 0;">Assessment Finding</div>',
        unsafe_allow_html=True)
    for i, col_name in enumerate(columns):
        hcols[i + 1].markdown(
            f'<div style="text-align:center;font-weight:700;font-size:0.82rem;'
            f'color:#374151;background:#F1F5F9;border:1px solid #CBD5E1;'
            f'border-radius:6px;padding:6px 4px;">{h(col_name)}</div>',
            unsafe_allow_html=True)

    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

    for row in rows:
        row_id    = row["id"]
        row_label = row["label"]
        dcols     = st.columns(col_widths)

        dcols[0].markdown(
            f'<div style="font-size:0.88rem;padding:8px 0;color:#1E293B;">'
            f'{h(row_label)}</div>',
            unsafe_allow_html=True)

        if locked:
            chosen = cur.get(row_id, "")
            for i, col_name in enumerate(columns):
                selected = (chosen == col_name)
                icon     = "◉" if selected else "○"
                color    = "#01696F" if selected else "#D1D5DB"
                dcols[i + 1].markdown(
                    f'<div style="text-align:center;font-size:1.25rem;'
                    f'color:{color};padding:4px 0;">{icon}</div>',
                    unsafe_allow_html=True)
        else:
            # ── TRUE RADIO: one choice per row ──
            # Place label in first col; radio spanning all option cols
            # We use a single horizontal radio in the remaining columns area
            with dcols[1]:
                # options=columns; show as horizontal radio buttons inline
                cur_choice = cur.get(row_id)
                idx_d = columns.index(cur_choice) if cur_choice in columns else None
                choice = st.radio(
                    label=f"",
                    options=columns,
                    index=idx_d,
                    key=f"mat_{qid}_{row_id}",
                    horizontal=True,
                    label_visibility="collapsed"
                )
                if choice is not None:
                    cur[row_id] = choice
                    st.session_state.answers[qid] = cur

        st.markdown(
            '<div style="height:1px;background:#F3F4F6;margin:2px 0;"></div>',
            unsafe_allow_html=True)


# ── TREND ─────────────────────────────────────────────────────────────────────

def render_trend(q, qid, locked):
    tdata = q["trend"]["data"]
    tpts  = q["trend"]["timepoints"]
    items = q["trend"]["items"]
    cur   = st.session_state.answers.get(qid, {})
    opts  = ["Improving", "Worsening", "No change"]

    st.markdown(
        '<div class="type-banner banner-trend">'
        'Trend — Review the data, then classify each parameter below.</div>',
        unsafe_allow_html=True)

    # Data table
    th = "".join(f"<th>{h(tp)}</th>" for tp in tpts)
    rows_html = ""
    for row in tdata:
        cells = ""
        for i, val in enumerate(row["values"]):
            cls = ' class="last-val"' if i == len(row["values"]) - 1 else ""
            cells += f"<td{cls}>{h(str(val))}</td>"
        rows_html += f"<tr><td class='row-label'>{h(row['label'])}</td>{cells}</tr>"

    st.markdown(
        f'<div style="overflow-x:auto;"><table class="trend-tbl">'
        f'<thead><tr><th class="row-header">Parameter</th>{th}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div>',
        unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:0.82rem;font-weight:700;color:#065F46;'
        'margin-bottom:6px;">For each item below, select the trend:</div>',
        unsafe_allow_html=True)

    for item in items:
        iid   = item["id"]
        label = item["label"]
        c1, c2 = st.columns([3, 2])
        c1.markdown(
            f'<div style="font-size:0.9rem;font-weight:600;color:#1E293B;'
            f'padding-top:6px;">{h(label)}</div>',
            unsafe_allow_html=True)
        if locked:
            val   = cur.get(iid, "—")
            color = ("#059669" if val == "Improving"
                     else "#DC2626" if val == "Worsening"
                     else "#6B7280")
            c2.markdown(
                f'<div style="font-size:0.9rem;font-weight:700;'
                f'color:{color};padding-top:6px;">{h(val)}</div>',
                unsafe_allow_html=True)
        else:
            idx_d  = opts.index(cur[iid]) if cur.get(iid) in opts else None
            choice = c2.selectbox(
                "", opts, index=idx_d,
                key=f"tr_{qid}_{iid}", label_visibility="collapsed")
            cur[iid] = choice
            st.session_state.answers[qid] = cur


# ── CLOZE ─────────────────────────────────────────────────────────────────────

def render_cloze(q, qid, locked):
    parts = q["cloze"]["sentence_parts"]
    cur   = st.session_state.answers.get(qid, {})

    st.markdown(
        '<div class="type-banner banner-cloze">'
        'Drop-Down — Select the best answer for each blank.</div>',
        unsafe_allow_html=True)

    text_buffer = ""
    for part in parts:
        if isinstance(part, str):
            text_buffer += part
        elif isinstance(part, dict):
            bid    = part["blank_id"]
            bopts  = part["options"]
            blabel = part.get("label", bid)

            if text_buffer.strip():
                st.markdown(
                    f'<div class="cloze-text">{h(text_buffer)}</div>',
                    unsafe_allow_html=True)
                text_buffer = ""

            if locked:
                val = cur.get(bid, "___")
                st.markdown(
                    f'<div style="margin:4px 0 8px 0;">'
                    f'<span style="font-size:0.78rem;font-weight:700;color:#6B7280;'
                    f'text-transform:uppercase;letter-spacing:0.05em;">{h(blabel)}: </span>'
                    f'<span class="blank-placeholder">{h(val)}</span>'
                    f'</div>',
                    unsafe_allow_html=True)
            else:
                idx_d  = bopts.index(cur[bid]) if cur.get(bid) in bopts else None
                c1, c2 = st.columns([1, 3])
                c1.markdown(
                    f'<div style="font-size:0.82rem;font-weight:700;'
                    f'color:#374151;padding-top:8px;">{h(blabel)}:</div>',
                    unsafe_allow_html=True)
                choice = c2.selectbox(
                    "", bopts, index=idx_d,
                    key=f"cz_{qid}_{bid}", label_visibility="collapsed")
                cur[bid] = choice
                st.session_state.answers[qid] = cur

    if text_buffer.strip():
        st.markdown(
            f'<div class="cloze-text">{h(text_buffer)}</div>',
            unsafe_allow_html=True)


# ── Answer completeness check ─────────────────────────────────────────────────

def is_answered(q, qid):
    ans = st.session_state.answers.get(qid)
    qt  = q["type"]
    if qt in ("MC", "SATA"):
        return bool(ans)
    if qt == "BOWTIE":
        bt = q["bowtie"]
        a_count = bt.get("action_count", 2)
        p_count = bt.get("param_count",  2)
        return (ans
                and bool(ans.get("condition"))
                and len(ans.get("actions",   [])) == a_count
                and len(ans.get("parameters",[])) == p_count)
    if qt == "MATRIX":
        return ans and len(ans) >= len(q["matrix"]["rows"])
    if qt == "TREND":
        return ans and len(ans) >= len(q["trend"]["items"])
    if qt == "CLOZE":
        blanks = [p for p in q["cloze"]["sentence_parts"] if isinstance(p, dict)]
        return ans and len(ans) >= len(blanks)
    return False

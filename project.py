import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import random

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Reliability Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #0d1117;
        border-right: 1px solid #1e2d3d;
    }
    [data-testid="stSidebar"] * {
        color: #c9d1d9 !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.82rem;
        letter-spacing: 0.04em;
    }

    /* Main background */
    .stApp {
        background: #0d1117;
        color: #e6edf3;
    }

    /* Metric cards */
    .metric-card {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 12px;
    }
    .metric-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2rem;
        font-weight: 600;
        color: #58a6ff;
    }
    .metric-label {
        font-size: 0.78rem;
        color: #8b949e;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 4px;
    }
    .metric-delta-good { color: #3fb950; font-size: 0.82rem; }
    .metric-delta-bad  { color: #f85149; font-size: 0.82rem; }

    /* Equipment pill */
    .eq-pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .pill-A { background: #1a3a2a; color: #3fb950; border: 1px solid #3fb950; }
    .pill-B { background: #2d2a1a; color: #d29922; border: 1px solid #d29922; }
    .pill-C { background: #3a1a1a; color: #f85149; border: 1px solid #f85149; }

    /* Section header */
    .section-header {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 0.15em;
        color: #58a6ff;
        text-transform: uppercase;
        border-bottom: 1px solid #21262d;
        padding-bottom: 6px;
        margin-bottom: 16px;
    }

    /* Phase badge */
    .phase-badge {
        background: #1f3052;
        color: #58a6ff;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.1em;
        padding: 3px 10px;
        border-radius: 3px;
        border: 1px solid #2d4a7a;
        display: inline-block;
        margin-bottom: 8px;
    }

    /* Plotly chart background override */
    .js-plotly-plot .plotly {
        background: transparent !important;
    }

    /* Divider */
    hr { border-color: #21262d; }

    /* Compliance bar */
    .compliance-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
    }
    .compliance-bar-bg {
        flex: 1;
        height: 6px;
        background: #21262d;
        border-radius: 3px;
        overflow: hidden;
    }
    .compliance-bar-fill {
        height: 100%;
        border-radius: 3px;
    }

    /* Stagger animation */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .fade-up { animation: fadeUp 0.4s ease forwards; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SAMPLE DATA
# ─────────────────────────────────────────────
EQUIPMENT = {
    "Rotating": [
        {"id": "P-101", "name": "Feed Pump",           "class": "A", "discipline": "Mechanical", "pm_coverage": True},
        {"id": "P-102", "name": "Cooling Water Pump",  "class": "B", "discipline": "Mechanical", "pm_coverage": True},
        {"id": "C-201", "name": "Air Compressor",      "class": "A", "discipline": "Mechanical", "pm_coverage": True},
        {"id": "FN-301","name": "Cooling Tower Fan",   "class": "B", "discipline": "Mechanical", "pm_coverage": False},
    ],
    "Electrical": [
        {"id": "T-401", "name": "Main Transformer",    "class": "A", "discipline": "Electrical", "pm_coverage": True},
        {"id": "MCC-1", "name": "Motor Control Centre","class": "A", "discipline": "Electrical", "pm_coverage": True},
        {"id": "G-501", "name": "Standby Generator",   "class": "B", "discipline": "Electrical", "pm_coverage": False},
    ],
    "Instrumentation": [
        {"id": "FT-601", "name": "Flow Transmitter",   "class": "C", "discipline": "Instrument", "pm_coverage": True},
        {"id": "PT-602", "name": "Pressure Transmitter","class":"C", "discipline": "Instrument", "pm_coverage": False},
        {"id": "LT-603", "name": "Level Transmitter",  "class": "B", "discipline": "Instrument", "pm_coverage": True},
    ],
    "Static": [
        {"id": "HX-701", "name": "Heat Exchanger",     "class": "B", "discipline": "Mechanical", "pm_coverage": True},
        {"id": "V-801",  "name": "Pressure Vessel",    "class": "A", "discipline": "Mechanical", "pm_coverage": True},
        {"id": "F-901",  "name": "Fuel Filter",        "class": "C", "discipline": "Mechanical", "pm_coverage": False},
    ],
}

# Flat list
ALL_EQUIP = [eq for grp in EQUIPMENT.values() for eq in grp]
EQUIP_BY_ID = {eq["id"]: eq for eq in ALL_EQUIP}

# ── Breakdown / failure history ──────────────
random.seed(42)
np.random.seed(42)

def gen_history(eq_id, class_):
    months = pd.date_range("2023-01-01", periods=18, freq="MS")
    base = {"A": 1.2, "B": 2.4, "C": 4.0}[class_]
    failures   = np.random.poisson(base, 18)
    downtime   = failures * np.random.uniform(2, 8, 18)
    repair_hrs = downtime * np.random.uniform(0.6, 0.9, 18)
    return pd.DataFrame({"month": months, "failures": failures,
                         "downtime_hrs": downtime.round(1),
                         "repair_hrs": repair_hrs.round(1)})

HISTORY = {eq["id"]: gen_history(eq["id"], eq["class"]) for eq in ALL_EQUIP}

# ── Unplanned downtime per equipment ─────────
DOWNTIME_TOTALS = {
    eq["id"]: HISTORY[eq["id"]]["downtime_hrs"].sum() for eq in ALL_EQUIP
}

# ── PM Schedule data ──────────────────────────
GOVT_STANDARDS = {
    "Daily":    {"interval_days": 1,   "label": "Daily"},
    "Weekly":   {"interval_days": 7,   "label": "Weekly"},
    "Monthly":  {"interval_days": 30,  "label": "Monthly"},
    "Quarterly":{"interval_days": 90,  "label": "Quarterly"},
    "Annual":   {"interval_days": 365, "label": "Annual"},
}

PM_TASKS = {
    "P-101":  [("Lubrication check",  "Weekly",    7,   80),
               ("Vibration analysis", "Monthly",   28,  75),
               ("Seal inspection",    "Quarterly", 85,  90),
               ("Overhaul",           "Annual",    350, 365)],
    "P-102":  [("Lubrication check",  "Weekly",    7,   90),
               ("Impeller inspection","Monthly",   30,  30),
               ("Bearing replacement","Annual",    340, 365)],
    "C-201":  [("Filter change",      "Monthly",   30,  30),
               ("Belt tension",       "Weekly",    6,   7),
               ("Valve inspection",   "Quarterly", 88,  90),
               ("Full overhaul",      "Annual",    355, 365)],
    "FN-301": [("Blade inspection",   "Monthly",   45,  30),
               ("Motor check",        "Quarterly", 95,  90)],
    "T-401":  [("Oil sampling",       "Monthly",   30,  30),
               ("Thermography",       "Quarterly", 90,  90),
               ("Full inspection",    "Annual",    365, 365)],
    "MCC-1":  [("Thermal imaging",    "Quarterly", 92,  90),
               ("Connection torque",  "Annual",    360, 365)],
    "G-501":  [("Load test",          "Monthly",   28,  30),
               ("Oil change",         "Quarterly", 95,  90),
               ("Full service",       "Annual",    380, 365)],
    "FT-601": [("Calibration",        "Quarterly", 90,  90),
               ("Loop check",         "Annual",    365, 365)],
    "PT-602": [("Calibration",        "Quarterly", 105, 90),
               ("Zero check",         "Monthly",   35,  30)],
    "LT-603": [("Calibration",        "Quarterly", 90,  90),
               ("Transmitter service","Annual",    370, 365)],
    "HX-701": [("Tube cleaning",      "Monthly",   30,  30),
               ("Bundle inspection",  "Annual",    355, 365)],
    "V-801":  [("External inspection","Monthly",   30,  30),
               ("Thickness test",     "Annual",    365, 365),
               ("Safety valve test",  "Quarterly", 90,  90)],
    "F-901":  [("Element replacement","Monthly",   45,  30),
               ("Housing inspection", "Quarterly", 100, 90)],
}

# ─────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────
CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Sans", color="#8b949e", size=11),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor="#21262d", linecolor="#21262d", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="#21262d", linecolor="#21262d", tickfont=dict(size=10)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
)

def failure_timeline(df, eq_name):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.55, 0.45],
                        vertical_spacing=0.08)
    # Failures bar
    fig.add_trace(go.Bar(
        x=df["month"], y=df["failures"],
        name="Failures", marker_color="#f85149",
        marker_line_color="rgba(0,0,0,0)",
        opacity=0.85,
    ), row=1, col=1)
    # Downtime line
    fig.add_trace(go.Scatter(
        x=df["month"], y=df["downtime_hrs"],
        name="Downtime (hrs)", mode="lines+markers",
        line=dict(color="#58a6ff", width=2),
        marker=dict(size=5, color="#58a6ff"),
        fill="tozeroy", fillcolor="rgba(88,166,255,0.08)",
    ), row=2, col=1)
    # Repair hours
    fig.add_trace(go.Scatter(
        x=df["month"], y=df["repair_hrs"],
        name="Repair (hrs)", mode="lines",
        line=dict(color="#3fb950", width=1.5, dash="dot"),
    ), row=2, col=1)
    fig.update_layout(**CHART_LAYOUT, height=360,
                      title=dict(text=f"Failure & Downtime History — {eq_name}",
                                 font=dict(size=13, color="#e6edf3")))
    fig.update_yaxes(title_text="# Failures", row=1, col=1,
                     title_font=dict(size=10), gridcolor="#21262d")
    fig.update_yaxes(title_text="Hours",      row=2, col=1,
                     title_font=dict(size=10), gridcolor="#21262d")
    return fig

def failure_type_pie(eq_id):
    types  = ["Mechanical wear", "Electrical fault", "Operator error",
              "Lubrication failure", "Vibration / fatigue", "Corrosion"]
    counts = np.random.dirichlet(np.ones(6) * 2) * 100
    counts = counts.round(1)
    fig = go.Figure(go.Pie(
        labels=types, values=counts,
        hole=0.55,
        marker=dict(colors=["#58a6ff","#f85149","#d29922",
                             "#3fb950","#bc8cff","#39c5cf"]),
        textfont=dict(size=10),
    ))
    fig.update_layout(**CHART_LAYOUT, height=300,
                      title=dict(text="Failure Mode Distribution",
                                 font=dict(size=12, color="#e6edf3")),
                      showlegend=True,
                      legend=dict(orientation="v", x=1.02, y=0.5))
    return fig

def mtbf_mttr_bar(df, eq_name):
    months = df["month"].dt.strftime("%b %y")
    mtbf = np.where(df["failures"] > 0, 720 / df["failures"].clip(1), 720)
    mttr = df["repair_hrs"] / df["failures"].clip(1)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=mtbf, name="MTBF (hrs)",
                         marker_color="#3fb950", opacity=0.8))
    fig.add_trace(go.Bar(x=months, y=mttr, name="MTTR (hrs)",
                         marker_color="#f85149", opacity=0.8))
    fig.update_layout(**CHART_LAYOUT, height=280, barmode="group",
                      title=dict(text="MTBF vs MTTR",
                                 font=dict(size=12, color="#e6edf3")))
    return fig

def pareto_chart(selected_id=None):
    items = sorted(DOWNTIME_TOTALS.items(), key=lambda x: x[1], reverse=True)
    ids    = [i[0] for i in items]
    vals   = [i[1] for i in items]
    total  = sum(vals)
    cumulative = np.cumsum(vals) / total * 100
    names  = [f"{i} – {EQUIP_BY_ID[i]['name']}" for i in ids]

    bar_colors = []
    for i in ids:
        if i == selected_id:
            bar_colors.append("#f85149")
        else:
            bar_colors.append("#58a6ff")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=names, y=vals, name="Unplanned Downtime (hrs)",
        marker_color=bar_colors, opacity=0.85,
        marker_line_color="rgba(0,0,0,0)",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=names, y=cumulative, name="Cumulative %",
        mode="lines+markers",
        line=dict(color="#d29922", width=2),
        marker=dict(size=5),
    ), secondary_y=True)
    # 80% line
    fig.add_hline(y=80, line_dash="dash", line_color="#3fb950",
                  annotation_text="80%", annotation_position="right",
                  secondary_y=True)
    fig.update_layout(**CHART_LAYOUT, height=400,
                      title=dict(text="Pareto — Unplanned Downtime by Equipment",
                                 font=dict(size=13, color="#e6edf3")),
                      xaxis=dict(tickangle=-40, tickfont=dict(size=9)))
    fig.update_yaxes(title_text="Downtime (hrs)", secondary_y=False,
                     gridcolor="#21262d")
    fig.update_yaxes(title_text="Cumulative %", secondary_y=True,
                     range=[0, 105], gridcolor="rgba(0,0,0,0)")
    return fig

def pm_schedule_chart(eq_id):
    tasks = PM_TASKS.get(eq_id, [])
    if not tasks:
        return None
    task_names  = [t[0] for t in tasks]
    std_labels  = [t[1] for t in tasks]
    actual_days = [t[2] for t in tasks]
    std_days    = [t[3] for t in tasks]
    compliance  = [round(min(s, a) / max(s, a) * 100, 1)
                   for a, s in zip(actual_days, std_days)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=task_names, x=std_days, name="Govt / OEM Standard",
        orientation="h",
        marker=dict(color="#3fb950", opacity=0.6),
        text=[f"{d}d" for d in std_days], textposition="outside",
        textfont=dict(size=9, color="#3fb950"),
    ))
    fig.add_trace(go.Bar(
        y=task_names, x=actual_days, name="Actual Interval",
        orientation="h",
        marker=dict(color="#58a6ff", opacity=0.85),
        text=[f"{d}d" for d in actual_days], textposition="outside",
        textfont=dict(size=9, color="#58a6ff"),
    ))
    fig.update_layout(**CHART_LAYOUT, height=max(250, len(tasks)*65),
                      barmode="group",
                      title=dict(text="PM Interval — Actual vs Standard (days)",
                                 font=dict(size=13, color="#e6edf3")),
                      legend=dict(orientation="h", y=1.08))
    fig.update_xaxes(title_text="Days")
    return fig, compliance, task_names, std_labels

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:16px 0 8px;'>
      <div style='font-family:IBM Plex Mono,monospace;font-size:0.65rem;
                  letter-spacing:0.15em;color:#58a6ff;
                  text-transform:uppercase;margin-bottom:4px;'>Phase 4 · Deliverable</div>
      <div style='font-size:1.15rem;font-weight:700;color:#e6edf3;
                  letter-spacing:-0.02em;line-height:1.3;'>
        Reliability<br>Dashboard
      </div>
    </div>
    <hr style='border-color:#21262d;margin:8px 0 16px;'/>
    """, unsafe_allow_html=True)

    nav = st.radio(
        "Navigation",
        ["📋  Equipment Master", "📊  History & Breakdown",
         "🔧  PM Schedule", "📉  Downtime Pareto"],
        label_visibility="collapsed",
    )

    st.markdown("<hr style='border-color:#21262d;margin:12px 0;'/>",
                unsafe_allow_html=True)

    # Equipment selector (shown when relevant)
    if nav in ["📊  History & Breakdown", "🔧  PM Schedule"]:
        st.markdown(
            "<div style='font-family:IBM Plex Mono,monospace;font-size:0.65rem;"
            "letter-spacing:0.12em;color:#8b949e;text-transform:uppercase;"
            "margin-bottom:10px;'>Select Equipment</div>",
            unsafe_allow_html=True)
        for group, items in EQUIPMENT.items():
            with st.expander(f"⚙  {group}", expanded=False):
                for eq in items:
                    pill_cls  = f"pill-{eq['class']}"
                    pm_icon   = "✅" if eq["pm_coverage"] else "⚠️"
                    if st.button(
                        f"{pm_icon} {eq['id']} · {eq['name']}",
                        key=f"btn_{eq['id']}",
                        use_container_width=True,
                    ):
                        st.session_state["selected_eq"] = eq["id"]
        if "selected_eq" not in st.session_state:
            st.session_state["selected_eq"] = "P-101"
        sel = st.session_state["selected_eq"]
        st.markdown(
            f"<div style='margin-top:10px;font-family:IBM Plex Mono,monospace;"
            f"font-size:0.72rem;color:#58a6ff;'>Selected: <b>{sel}</b></div>",
            unsafe_allow_html=True)

    # Pareto highlight selector
    if nav == "📉  Downtime Pareto":
        st.markdown(
            "<div style='font-family:IBM Plex Mono,monospace;font-size:0.65rem;"
            "letter-spacing:0.12em;color:#8b949e;text-transform:uppercase;"
            "margin-bottom:10px;'>Highlight Equipment</div>",
            unsafe_allow_html=True)
        highlight = st.selectbox(
            "Equipment",
            options=["None"] + [f"{e['id']} – {e['name']}" for e in ALL_EQUIP],
            label_visibility="collapsed",
        )
        highlighted_id = highlight.split(" – ")[0] if highlight != "None" else None

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.65rem;color:#484f58;font-family:IBM Plex Mono,"
        "monospace;'>Plant Reliability v1.0<br>Data period: Jan 2023 – Jun 2024</div>",
        unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────

# ── 1. EQUIPMENT MASTER LIST ──────────────────
if nav == "📋  Equipment Master":
    st.markdown('<div class="phase-badge">PHASE 4 — DELIVERABLE</div>',
                unsafe_allow_html=True)
    st.markdown(
        "<h1 style='font-size:2rem;font-weight:700;color:#e6edf3;"
        "letter-spacing:-0.03em;margin-bottom:4px;'>Equipment Master List</h1>",
        unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#8b949e;font-size:0.92rem;margin-bottom:24px;'>"
        "Every plant asset with classification (A/B/C), PM coverage status, "
        "and discipline — giving an instant snapshot of the full asset population.</p>",
        unsafe_allow_html=True)

    # Summary metrics
    total = len(ALL_EQUIP)
    a_cnt = sum(1 for e in ALL_EQUIP if e["class"] == "A")
    b_cnt = sum(1 for e in ALL_EQUIP if e["class"] == "B")
    c_cnt = sum(1 for e in ALL_EQUIP if e["class"] == "C")
    pm_ok = sum(1 for e in ALL_EQUIP if e["pm_coverage"])

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, val, lbl, delta, good in [
        (c1, total, "Total Assets",      None, True),
        (c2, a_cnt, "Class A (Critical)", None, True),
        (c3, b_cnt, "Class B (Major)",   None, True),
        (c4, c_cnt, "Class C (Minor)",   None, True),
        (c5, f"{pm_ok}/{total}", "PM Covered", None, True),
    ]:
        col.markdown(f"""
        <div class="metric-card">
          <div class="metric-value">{val}</div>
          <div class="metric-label">{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Table
    rows = []
    for eq in ALL_EQUIP:
        total_dt = DOWNTIME_TOTALS[eq["id"]]
        total_f  = HISTORY[eq["id"]]["failures"].sum()
        rows.append({
            "ID": eq["id"],
            "Equipment Name": eq["name"],
            "Class": eq["class"],
            "Discipline": eq["discipline"],
            "PM Coverage": "✅ Yes" if eq["pm_coverage"] else "⚠️ No",
            "Total Failures (18M)": int(total_f),
            "Total Downtime (hrs)": round(total_dt, 1),
        })
    df_master = pd.DataFrame(rows)
    st.dataframe(df_master, use_container_width=True, height=440,
                 column_config={
                     "Class": st.column_config.TextColumn(width="small"),
                     "Total Failures (18M)": st.column_config.NumberColumn(format="%d"),
                     "Total Downtime (hrs)": st.column_config.NumberColumn(format="%.1f"),
                 })

# ── 2. HISTORY CARD & BREAKDOWN ───────────────
elif nav == "📊  History & Breakdown":
    eq_id   = st.session_state.get("selected_eq", "P-101")
    eq_info = EQUIP_BY_ID[eq_id]
    df      = HISTORY[eq_id]

    class_colors = {"A": "#3fb950", "B": "#d29922", "C": "#f85149"}
    cc = class_colors[eq_info["class"]]

    st.markdown(
        f"<div class='phase-badge'>HISTORY CARD · {eq_id}</div>",
        unsafe_allow_html=True)
    st.markdown(
        f"<h1 style='font-size:1.9rem;font-weight:700;color:#e6edf3;"
        f"letter-spacing:-0.03em;margin-bottom:2px;'>{eq_info['name']}</h1>"
        f"<div style='color:#8b949e;font-size:0.88rem;margin-bottom:20px;'>"
        f"{eq_info['discipline']} · "
        f"<span style='color:{cc};font-family:IBM Plex Mono,monospace;"
        f"font-weight:600;'>Class {eq_info['class']}</span> · "
        f"PM Coverage: {'✅ Active' if eq_info['pm_coverage'] else '⚠️ Not Covered'}"
        f"</div>",
        unsafe_allow_html=True)

    # KPI row
    total_f  = int(df["failures"].sum())
    total_dt = round(df["downtime_hrs"].sum(), 1)
    avg_mtbf = round(18 * 720 / max(total_f, 1), 1)
    avg_mttr = round(df["repair_hrs"].sum() / max(total_f, 1), 1)

    for col, val, lbl in zip(
        st.columns(4),
        [total_f, total_dt, f"{avg_mtbf}h", f"{avg_mttr}h"],
        ["Total Failures (18M)", "Total Downtime (hrs)", "Avg MTBF", "Avg MTTR"],
    ):
        col.markdown(f"""
        <div class="metric-card">
          <div class="metric-value">{val}</div>
          <div class="metric-label">{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.plotly_chart(failure_timeline(df, eq_info["name"]),
                    use_container_width=True)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.plotly_chart(failure_type_pie(eq_id), use_container_width=True)
    with col_b:
        st.plotly_chart(mtbf_mttr_bar(df, eq_info["name"]),
                        use_container_width=True)

    # Recent breakdown log
    st.markdown("<div class='section-header'>Recent Breakdown Log</div>",
                unsafe_allow_html=True)
    log_rows = []
    for _, row in df.tail(6).iterrows():
        if row["failures"] > 0:
            log_rows.append({
                "Month": row["month"].strftime("%b %Y"),
                "Failures": int(row["failures"]),
                "Downtime (hrs)": row["downtime_hrs"],
                "Repair (hrs)": row["repair_hrs"],
                "Status": "🔴 Corrective" if row["failures"] > 2 else "🟡 Minor",
            })
    if log_rows:
        st.dataframe(pd.DataFrame(log_rows), use_container_width=True, height=240)
    else:
        st.success("No breakdowns in the last 6 months.")

# ── 3. PM SCHEDULE ────────────────────────────
elif nav == "🔧  PM Schedule":
    eq_id   = st.session_state.get("selected_eq", "P-101")
    eq_info = EQUIP_BY_ID[eq_id]

    st.markdown(f"<div class='phase-badge'>PM SCHEDULE · {eq_id}</div>",
                unsafe_allow_html=True)
    st.markdown(
        f"<h1 style='font-size:1.9rem;font-weight:700;color:#e6edf3;"
        f"letter-spacing:-0.03em;margin-bottom:2px;'>PM Routes — {eq_info['name']}</h1>"
        f"<p style='color:#8b949e;font-size:0.88rem;margin-bottom:20px;'>"
        f"OEM-aligned maintenance intervals compared against Government / Industry standards. "
        f"Green = Standard · Blue = Actual plant interval.</p>",
        unsafe_allow_html=True)

    result = pm_schedule_chart(eq_id)
    if result is None:
        st.warning("No PM schedule data available for this equipment.")
    else:
        fig, compliance, task_names, std_labels = result
        st.plotly_chart(fig, use_container_width=True)

        # Compliance table
        st.markdown("<div class='section-header'>Compliance Analysis</div>",
                    unsafe_allow_html=True)
        tasks_data = PM_TASKS.get(eq_id, [])
        comp_rows = []
        for i, task in enumerate(tasks_data):
            actual, std = task[2], task[3]
            status = "✅ Compliant" if actual <= std * 1.1 else "⚠️ Overdue"
            delta  = actual - std
            comp_rows.append({
                "Task": task[0],
                "Std Frequency": task[1],
                "Standard (days)": std,
                "Actual (days)": actual,
                "Delta (days)": delta,
                "Compliance %": compliance[i],
                "Status": status,
            })
        df_comp = pd.DataFrame(comp_rows)
        st.dataframe(df_comp, use_container_width=True, height=260,
                     column_config={
                         "Compliance %": st.column_config.ProgressColumn(
                             format="%.1f%%", min_value=0, max_value=100),
                         "Delta (days)": st.column_config.NumberColumn(format="%+d"),
                     })

        # Overall compliance score
        avg_comp = round(sum(compliance) / len(compliance), 1)
        comp_color = "#3fb950" if avg_comp >= 85 else "#d29922" if avg_comp >= 70 else "#f85149"
        st.markdown(
            f"<div class='metric-card' style='margin-top:16px;'>"
            f"<div class='metric-value' style='color:{comp_color};'>{avg_comp}%</div>"
            f"<div class='metric-label'>Overall PM Compliance Score for {eq_id}</div>"
            f"</div>",
            unsafe_allow_html=True)

# ── 4. DOWNTIME PARETO ────────────────────────
elif nav == "📉  Downtime Pareto":
    h_id = highlighted_id if "highlighted_id" in dir() else None

    st.markdown("<div class='phase-badge'>KPI · DOWNTIME ANALYSIS</div>",
                unsafe_allow_html=True)
    st.markdown(
        "<h1 style='font-size:1.9rem;font-weight:700;color:#e6edf3;"
        "letter-spacing:-0.03em;margin-bottom:2px;'>Unplanned Downtime Pareto</h1>"
        "<p style='color:#8b949e;font-size:0.88rem;margin-bottom:20px;'>"
        "Identifies the vital few equipment items responsible for the majority of "
        "unplanned downtime — driving focused reliability improvement.</p>",
        unsafe_allow_html=True)

    total_dt = sum(DOWNTIME_TOTALS.values())
    sorted_dt = sorted(DOWNTIME_TOTALS.items(), key=lambda x: x[1], reverse=True)
    top3_ids  = [s[0] for s in sorted_dt[:3]]
    top3_pct  = sum(s[1] for s in sorted_dt[:3]) / total_dt * 100

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"""<div class="metric-card">
      <div class="metric-value">{round(total_dt,0):.0f}h</div>
      <div class="metric-label">Total Unplanned Downtime (18M)</div>
    </div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="metric-card">
      <div class="metric-value" style="color:#f85149;">{round(top3_pct,1)}%</div>
      <div class="metric-label">Top 3 Equipment Contribution</div>
    </div>""", unsafe_allow_html=True)
    c3.markdown(f"""<div class="metric-card">
      <div class="metric-value">{len(ALL_EQUIP)}</div>
      <div class="metric-label">Equipment Analysed</div>
    </div>""", unsafe_allow_html=True)

    st.plotly_chart(pareto_chart(h_id), use_container_width=True)

    # Breakdown table
    st.markdown("<div class='section-header'>Ranked Equipment — Downtime</div>",
                unsafe_allow_html=True)
    cumulative_pct = 0
    rank_rows = []
    for rank, (eid, dt) in enumerate(sorted_dt, 1):
        pct = dt / total_dt * 100
        cumulative_pct += pct
        eq  = EQUIP_BY_ID[eid]
        rank_rows.append({
            "Rank": rank,
            "Equipment ID": eid,
            "Name": eq["name"],
            "Class": eq["class"],
            "Downtime (hrs)": round(dt, 1),
            "% Contribution": round(pct, 1),
            "Cumulative %": round(cumulative_pct, 1),
            "Vital Few": "★ Yes" if cumulative_pct <= 80 else "—",
        })
    df_pareto = pd.DataFrame(rank_rows)
    st.dataframe(df_pareto, use_container_width=True, height=420,
                 column_config={
                     "% Contribution": st.column_config.ProgressColumn(
                         format="%.1f%%", min_value=0, max_value=100),
                     "Cumulative %": st.column_config.ProgressColumn(
                         format="%.1f%%", min_value=0, max_value=100),
                 })
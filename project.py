import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Plant Reliability Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
#  GLOBAL STYLES — WHITE THEME
# ─────────────────────────────────────────────
st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; }
        section[data-testid="stSidebar"] { background-color: #F5F5F5; }
        .stApp, .stMarkdown, p, label, h1, h2, h3 { color: #111111 !important; }
        .stSelectbox label, .stRadio label { color: #111111 !important; }
        div[data-testid="stMetricValue"] { color: #111111 !important; }
        div[data-testid="stMetricLabel"] { color: #555555 !important; }
        .block-container { padding-top: 2rem; }
        .phase-label {
            font-size: 11px;
            color: #888888;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .dashboard-title {
            font-size: 24px;
            font-weight: 700;
            color: #111111;
            margin-bottom: 1.5rem;
        }
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            background-color: #E8F4FD;
            color: #2980B9;
            margin-bottom: 10px;
        }
        .stDataFrame { border: 1px solid #E0E0E0 !important; }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  CHART LAYOUT — WHITE THEME
# ─────────────────────────────────────────────
CHART_LAYOUT = {
    "paper_bgcolor": "#FFFFFF",
    "plot_bgcolor":  "#FFFFFF",
    "font": dict(color="#111111", size=12),
    "xaxis": dict(gridcolor="#E0E0E0", linecolor="#CCCCCC", tickfont=dict(color="#333333")),
    "yaxis": dict(gridcolor="#E0E0E0", linecolor="#CCCCCC", tickfont=dict(color="#333333")),
    "margin": dict(l=40, r=20, t=60, b=40),
}

# ─────────────────────────────────────────────
#  EQUIPMENT DATA
# ─────────────────────────────────────────────
EQUIPMENT = {
    "Rotating": [
        {"id": "P-101",  "name": "Feed Pump",          "status": "ok",      "type": "Pump"},
        {"id": "P-102",  "name": "Cooling Water Pump",  "status": "ok",      "type": "Pump"},
        {"id": "C-201",  "name": "Air Compressor",      "status": "ok",      "type": "Compressor"},
        {"id": "FN-301", "name": "Cooling Tower Fan",   "status": "warning", "type": "Fan"},
    ],
    "Electrical": [
        {"id": "MCC-01", "name": "Motor Control Centre", "status": "ok",   "type": "Electrical"},
        {"id": "TR-01",  "name": "Transformer 11kV",      "status": "ok",   "type": "Electrical"},
        {"id": "DG-01",  "name": "Diesel Generator",      "status": "warning", "type": "Generator"},
    ],
    "Instrumentation": [
        {"id": "FT-101", "name": "Flow Transmitter",     "status": "ok",      "type": "Instrument"},
        {"id": "PT-201", "name": "Pressure Transmitter", "status": "ok",      "type": "Instrument"},
        {"id": "LT-301", "name": "Level Transmitter",    "status": "warning", "type": "Instrument"},
    ],
    "Static": [
        {"id": "HX-101", "name": "Heat Exchanger",  "status": "ok", "type": "Heat Exchanger"},
        {"id": "TK-201", "name": "Storage Tank",    "status": "ok", "type": "Tank"},
        {"id": "V-301",  "name": "Pressure Vessel", "status": "ok", "type": "Vessel"},
    ],
}

# ─────────────────────────────────────────────
#  PM SCHEDULE DATA (Standard vs Actual)
# ─────────────────────────────────────────────
PM_DATA = {
    "P-101": [
        {"task": "Lubrication",        "standard": 30,  "actual": 35},
        {"task": "Vibration Check",    "standard": 30,  "actual": 45},
        {"task": "Seal Inspection",    "standard": 90,  "actual": 90},
        {"task": "Coupling Check",     "standard": 180, "actual": 200},
        {"task": "Full Overhaul",      "standard": 365, "actual": 400},
    ],
    "P-102": [
        {"task": "Lubrication",        "standard": 30,  "actual": 30},
        {"task": "Vibration Check",    "standard": 30,  "actual": 30},
        {"task": "Seal Inspection",    "standard": 90,  "actual": 100},
        {"task": "Coupling Check",     "standard": 180, "actual": 180},
        {"task": "Full Overhaul",      "standard": 365, "actual": 365},
    ],
    "C-201": [
        {"task": "Air Filter Change",        "standard": 30,  "actual": 45},
        {"task": "Oil & Filter Change",      "standard": 90,  "actual": 120},
        {"task": "Belt Inspection",          "standard": 90,  "actual": 90},
        {"task": "Valve Inspection",         "standard": 180, "actual": 210},
        {"task": "Intercooler Cleaning",     "standard": 180, "actual": 240},
        {"task": "Safety Valve Test",        "standard": 365, "actual": 365},
        {"task": "Full Overhaul",            "standard": 730, "actual": 800},
    ],
    "FN-301": [
        {"task": "Blade Inspection",     "standard": 30,  "actual": 60},
        {"task": "Lubrication",          "standard": 30,  "actual": 45},
        {"task": "Belt Check",           "standard": 90,  "actual": 90},
        {"task": "Motor Inspection",     "standard": 180, "actual": 180},
        {"task": "Full Overhaul",        "standard": 365, "actual": 500},
    ],
    "MCC-01": [
        {"task": "Visual Inspection",     "standard": 30,  "actual": 30},
        {"task": "Thermal Imaging",       "standard": 90,  "actual": 90},
        {"task": "Breaker Test",          "standard": 180, "actual": 200},
        {"task": "Annual Maintenance",    "standard": 365, "actual": 365},
    ],
    "TR-01": [
        {"task": "Oil Level Check",       "standard": 30,  "actual": 30},
        {"task": "Temperature Check",     "standard": 30,  "actual": 35},
        {"task": "Oil Sampling",          "standard": 180, "actual": 200},
        {"task": "Annual Inspection",     "standard": 365, "actual": 365},
    ],
    "DG-01": [
        {"task": "Weekly Run Test",       "standard": 7,   "actual": 14},
        {"task": "Oil Change",            "standard": 90,  "actual": 100},
        {"task": "Battery Check",         "standard": 90,  "actual": 90},
        {"task": "Load Bank Test",        "standard": 365, "actual": 400},
    ],
    "FT-101": [
        {"task": "Calibration",           "standard": 180, "actual": 180},
        {"task": "Zero Check",            "standard": 90,  "actual": 90},
        {"task": "Loop Check",            "standard": 365, "actual": 365},
    ],
    "PT-201": [
        {"task": "Calibration",           "standard": 180, "actual": 200},
        {"task": "Zero Check",            "standard": 90,  "actual": 90},
        {"task": "Loop Check",            "standard": 365, "actual": 365},
    ],
    "LT-301": [
        {"task": "Calibration",           "standard": 180, "actual": 270},
        {"task": "Zero Check",            "standard": 90,  "actual": 120},
        {"task": "Loop Check",            "standard": 365, "actual": 400},
    ],
    "HX-101": [
        {"task": "Visual Inspection",     "standard": 90,  "actual": 90},
        {"task": "Tube Cleaning",         "standard": 180, "actual": 210},
        {"task": "Pressure Test",         "standard": 365, "actual": 365},
        {"task": "Full Inspection",       "standard": 730, "actual": 730},
    ],
    "TK-201": [
        {"task": "Visual Inspection",     "standard": 30,  "actual": 30},
        {"task": "Thickness Check",       "standard": 365, "actual": 365},
        {"task": "Internal Inspection",   "standard": 730, "actual": 800},
    ],
    "V-301": [
        {"task": "Visual Inspection",     "standard": 90,  "actual": 90},
        {"task": "Safety Valve Test",     "standard": 365, "actual": 365},
        {"task": "NDT Inspection",        "standard": 730, "actual": 730},
    ],
}

# ─────────────────────────────────────────────
#  BREAKDOWN HISTORY DATA
# ─────────────────────────────────────────────
def generate_breakdown_data(eq_id):
    random.seed(hash(eq_id) % 1000)
    records = []
    base_date = datetime(2024, 1, 1)
    for i in range(random.randint(4, 10)):
        date = base_date + timedelta(days=random.randint(0, 365))
        duration = random.randint(1, 48)
        records.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Failure Mode": random.choice([
                "Bearing Failure", "Seal Leak", "Overheating",
                "Vibration", "Electrical Fault", "Instrument Drift",
                "Corrosion", "Blockage", "Wear"
            ]),
            "Downtime (hrs)": duration,
            "Maintenance Type": random.choice(["Corrective", "Emergency"]),
            "Cost (USD)": random.randint(200, 5000),
            "Technician": random.choice(["Rajan", "Suresh", "Arjun", "Priya"]),
        })
    return pd.DataFrame(records).sort_values("Date", ascending=False)

# ─────────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────────
def status_icon(status):
    return "✅" if status == "ok" else "⚠️"

def get_all_equipment():
    result = []
    for category, items in EQUIPMENT.items():
        for item in items:
            result.append({**item, "category": category})
    return result

# ─────────────────────────────────────────────
#  CHART FUNCTIONS
# ─────────────────────────────────────────────
def pm_schedule_chart(eq_id):
    tasks_raw = PM_DATA.get(eq_id, [])
    if not tasks_raw:
        st.info("No PM data available for this equipment.")
        return

    tasks = [t["task"] for t in tasks_raw]
    standard = [t["standard"] for t in tasks_raw]
    actual = [t["actual"] for t in tasks_raw]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Standard (OEM/Govt)",
        x=tasks, y=standard,
        marker_color="#2ECC71",
        opacity=0.85
    ))
    fig.add_trace(go.Bar(
        name="Actual (Plant)",
        x=tasks, y=actual,
        marker_color="#3498DB",
        opacity=0.85
    ))

    layout = {
        **CHART_LAYOUT,
        "height": max(300, len(tasks) * 60),
        "barmode": "group",
        "title": dict(
            text="PM Interval — Actual vs Standard (days)",
            font=dict(size=14, color="#111111")
        ),
        "legend": dict(orientation="h", y=1.08, font=dict(color="#111111")),
        "xaxis": {**CHART_LAYOUT["xaxis"], "title": "Maintenance Task"},
        "yaxis": {**CHART_LAYOUT["yaxis"], "title": "Interval (Days)"},
    }
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)

def breakdown_chart(df, eq_id):
    if df.empty:
        st.info("No breakdown history found.")
        return

    monthly = df.copy()
    monthly["Month"] = pd.to_datetime(monthly["Date"]).dt.strftime("%b %Y")
    monthly_sum = monthly.groupby("Month")["Downtime (hrs)"].sum().reset_index()

    fig = go.Figure(go.Bar(
        x=monthly_sum["Month"],
        y=monthly_sum["Downtime (hrs)"],
        marker_color="#E74C3C",
        opacity=0.85
    ))
    layout = {
        **CHART_LAYOUT,
        "height": 300,
        "title": dict(text="Monthly Downtime (hrs)", font=dict(size=14, color="#111111")),
        "xaxis": {**CHART_LAYOUT["xaxis"], "title": "Month"},
        "yaxis": {**CHART_LAYOUT["yaxis"], "title": "Downtime (hrs)"},
    }
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)

def downtime_pareto_chart(eq_id):
    all_eq = get_all_equipment()
    pareto_data = []
    for eq in all_eq:
        df = generate_breakdown_data(eq["id"])
        total_dt = df["Downtime (hrs)"].sum() if not df.empty else 0
        pareto_data.append({"Equipment": f"{eq['id']} - {eq['name']}", "Downtime (hrs)": total_dt})

    pareto_df = pd.DataFrame(pareto_data).sort_values("Downtime (hrs)", ascending=False)
    pareto_df["Cumulative %"] = (pareto_df["Downtime (hrs)"].cumsum() / pareto_df["Downtime (hrs)"].sum() * 100).round(1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=pareto_df["Equipment"],
        y=pareto_df["Downtime (hrs)"],
        name="Downtime (hrs)",
        marker_color="#3498DB",
        opacity=0.85
    ))
    fig.add_trace(go.Scatter(
        x=pareto_df["Equipment"],
        y=pareto_df["Cumulative %"],
        name="Cumulative %",
        yaxis="y2",
        line=dict(color="#E74C3C", width=2),
        mode="lines+markers"
    ))

    layout = {
        **CHART_LAYOUT,
        "height": 420,
        "title": dict(text="Downtime Pareto — All Equipment", font=dict(size=14, color="#111111")),
        "xaxis": {**CHART_LAYOUT["xaxis"], "tickangle": -35},
        "yaxis": {**CHART_LAYOUT["yaxis"], "title": "Downtime (hrs)"},
        "yaxis2": dict(
            title="Cumulative %",
            overlaying="y",
            side="right",
            range=[0, 110],
            tickfont=dict(color="#E74C3C"),
            gridcolor="#F0F0F0"
        ),
        "legend": dict(orientation="h", y=1.08),
    }
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="phase-label">Phase 4 · Deliverable</div>', unsafe_allow_html=True)
    st.markdown("### Reliability\nDashboard")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["🗂 Equipment Master", "📊 History & Breakdown", "🔧 PM Schedule", "📉 Downtime Pareto"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("**SELECT EQUIPMENT**")

    category = st.selectbox("Category", list(EQUIPMENT.keys()), label_visibility="collapsed")
    eq_options = EQUIPMENT[category]
    eq_labels = [f"{status_icon(e['status'])} {e['id']} · {e['name']}" for e in eq_options]
    eq_choice = st.radio("Equipment", eq_labels, label_visibility="collapsed")
    selected_idx = eq_labels.index(eq_choice)
    selected_eq = eq_options[selected_idx]

    st.markdown("---")
    st.caption(f"Selected: **{selected_eq['id']}**")
    st.caption("Plant Reliability v1.0")

# ─────────────────────────────────────────────
#  MAIN CONTENT
# ─────────────────────────────────────────────
eq_id   = selected_eq["id"]
eq_name = selected_eq["name"]
eq_type = selected_eq["type"]
eq_status = selected_eq["status"]

# ── PAGE: EQUIPMENT MASTER ──────────────────
if "Equipment Master" in page:
    st.markdown('<div class="dashboard-title">Equipment Master</div>', unsafe_allow_html=True)

    all_eq = get_all_equipment()
    master_df = pd.DataFrame([{
        "ID":       e["id"],
        "Name":     e["name"],
        "Category": e["category"],
        "Type":     e["type"],
        "Status":   "✅ OK" if e["status"] == "ok" else "⚠️ Warning",
    } for e in all_eq])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Equipment", len(all_eq))
    col2.metric("Rotating",        len(EQUIPMENT["Rotating"]))
    col3.metric("Electrical",      len(EQUIPMENT["Electrical"]))
    col4.metric("⚠️ Warnings",     sum(1 for e in all_eq if e["status"] == "warning"))

    st.markdown("---")
    st.markdown(f"#### {eq_id} — {eq_name}")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Equipment ID",   eq_id)
    col_b.metric("Type",           eq_type)
    col_c.metric("Status",         "✅ OK" if eq_status == "ok" else "⚠️ Warning")

    st.markdown("---")
    st.markdown("#### All Equipment")
    st.dataframe(master_df, use_container_width=True, hide_index=True)

# ── PAGE: HISTORY & BREAKDOWN ───────────────
elif "History" in page:
    st.markdown(f'<div class="dashboard-title">History & Breakdown — {eq_name}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="badge">BREAKDOWN LOG · {eq_id}</div>', unsafe_allow_html=True)

    df = generate_breakdown_data(eq_id)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Breakdowns",    len(df))
    col2.metric("Total Downtime (hrs)", df["Downtime (hrs)"].sum())
    col3.metric("Avg Cost (USD)",       f"${int(df['Cost (USD)'].mean()):,}")

    breakdown_chart(df, eq_id)

    st.markdown("#### Breakdown Records")
    st.dataframe(df.reset_index(drop=True), use_container_width=True, hide_index=True)

# ── PAGE: PM SCHEDULE ───────────────────────
elif "PM Schedule" in page:
    st.markdown(f'<div class="badge">PM SCHEDULE · {eq_id}</div>', unsafe_allow_html=True)
    st.markdown(f"## PM Routes — {eq_name}")
    st.caption("OEM-aligned maintenance intervals compared against Government / Industry standards. "
               "Green = Standard · Blue = Actual plant interval.")

    pm_schedule_chart(eq_id)

    tasks_raw = PM_DATA.get(eq_id, [])
    if tasks_raw:
        pm_df = pd.DataFrame(tasks_raw)
        pm_df.columns = ["Maintenance Task", "Standard Interval (days)", "Actual Interval (days)"]
        pm_df["Variance (days)"] = pm_df["Actual Interval (days)"] - pm_df["Standard Interval (days)"]
        pm_df["Status"] = pm_df["Variance (days)"].apply(
            lambda x: "✅ On Schedule" if x <= 0 else ("⚠️ Slightly Overdue" if x <= 30 else "🔴 Overdue")
        )
        st.markdown("#### PM Interval Details")
        st.dataframe(pm_df, use_container_width=True, hide_index=True)

# ── PAGE: DOWNTIME PARETO ───────────────────
elif "Downtime Pareto" in page:
    st.markdown('<div class="dashboard-title">Downtime Pareto Analysis</div>', unsafe_allow_html=True)
    st.caption("Pareto chart showing cumulative downtime contribution across all equipment.")

    downtime_pareto_chart(eq_id)

    all_eq = get_all_equipment()
    pareto_rows = []
    for eq in all_eq:
        df_temp = generate_breakdown_data(eq["id"])
        pareto_rows.append({
            "Equipment ID":     eq["id"],
            "Equipment Name":   eq["name"],
            "Category":         eq["category"],
            "Breakdowns":       len(df_temp),
            "Total Downtime (hrs)": df_temp["Downtime (hrs)"].sum(),
            "Total Cost (USD)": f"${df_temp['Cost (USD)'].sum():,}",
        })
    pareto_df = pd.DataFrame(pareto_rows).sort_values("Total Downtime (hrs)", ascending=False)
    st.markdown("#### Downtime Summary — All Equipment")
    st.dataframe(pareto_df.reset_index(drop=True), use_container_width=True, hide_index=True)

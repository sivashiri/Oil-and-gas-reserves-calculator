
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PM Dashboard — Castrol Paharpur",
    page_icon="🔧",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid #ddd;
    }
    .metric-card.overdue  { border-left-color: #dc3545; background: #fff5f5; }
    .metric-card.due      { border-left-color: #fd7e14; background: #fff9f0; }
    .metric-card.ok       { border-left-color: #198754; background: #f0fff4; }
    .metric-card.total    { border-left-color: #0d6efd; background: #f0f4ff; }
    .metric-label { font-size: 12px; color: #666; margin-bottom: 4px; }
    .metric-value { font-size: 28px; font-weight: 600; color: #1a1a1a; }
    .status-overdue { color: #dc3545; font-weight: 600; }
    .status-due     { color: #fd7e14; font-weight: 600; }
    .status-ok      { color: #198754; font-weight: 600; }
    div[data-testid="stSidebarContent"] { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)

    # Normalise column names — strip spaces, title-case
    df.columns = df.columns.str.strip()

    # Parse date columns robustly
    for col in ["Last_PM_Date", "Next_Due_Date", "Breakdown_Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    # Derive status from Next_Due_Date
    today = date.today()
    if "Next_Due_Date" in df.columns:
        def _status(nd):
            if pd.isna(nd):
                return "Unknown"
            delta = (nd - today).days
            if delta < 0:
                return "Overdue"
            elif delta <= 7:
                return "Due Soon"
            else:
                return "OK"
        df["Status"] = df["Next_Due_Date"].apply(_status)
        df["Days_To_Due"] = df["Next_Due_Date"].apply(
            lambda nd: (nd - today).days if pd.notna(nd) else None
        )

    return df


# ── Sidebar — file + filters ──────────────────────────────────────────────────
with st.sidebar:
    st.title("🔧 PM Dashboard")
    st.caption("Castrol Paharpur Plant")
    st.divider()

    uploaded = st.file_uploader("Upload Excel datasheet", type=["xlsx", "xls"])
    default_path = r'C:\Users\sivas\Downloads\datasheet.xlsx'
    data_source = uploaded if uploaded else default_path

    try:
        df = load_data(data_source)
    except Exception as e:
        st.error(f"Could not load file: {e}")
        st.info("Please upload your Excel file above.")
        st.stop()

    st.divider()
    st.subheader("Filters")

    # Equipment filter
    eq_col = "Equipment" if "Equipment" in df.columns else df.columns[0]
    equipment_list = ["All"] + sorted(df[eq_col].dropna().unique().tolist())
    selected_equipment = st.selectbox("Equipment", equipment_list)

    # Status filter
    if "Status" in df.columns:
        status_opts = ["All"] + sorted(df["Status"].dropna().unique().tolist())
        selected_status = st.selectbox("Status", status_opts)
    else:
        selected_status = "All"

    # Frequency filter
    if "Frequency" in df.columns:
        freq_opts = ["All"] + sorted(df["Frequency"].dropna().unique().tolist())
        selected_freq = st.selectbox("Frequency", freq_opts)
    else:
        selected_freq = "All"

    st.divider()
    st.caption(f"Data loaded: {len(df)} records")
    st.caption(f"Today: {date.today():%d %b %Y}")


# ── Apply filters ─────────────────────────────────────────────────────────────
fdf = df.copy()

if selected_equipment != "All":
    fdf = fdf[fdf[eq_col] == selected_equipment]
if selected_status != "All" and "Status" in fdf.columns:
    fdf = fdf[fdf["Status"] == selected_status]
if selected_freq != "All" and "Frequency" in fdf.columns:
    fdf = fdf[fdf["Frequency"] == selected_freq]


# ── Header ────────────────────────────────────────────────────────────────────
title = selected_equipment if selected_equipment != "All" else "All Equipment"
st.title(f"Preventive Maintenance — {title}")
st.caption(f"Paharpur plant · as of {date.today():%d %B %Y}")


# ── KPI cards ─────────────────────────────────────────────────────────────────
total     = len(fdf)
overdue   = len(fdf[fdf["Status"] == "Overdue"])  if "Status" in fdf.columns else 0
due_soon  = len(fdf[fdf["Status"] == "Due Soon"])  if "Status" in fdf.columns else 0
ok_count  = len(fdf[fdf["Status"] == "OK"])         if "Status" in fdf.columns else 0
compliance = round((ok_count / total * 100), 1) if total > 0 else 0

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""
    <div class="metric-card total">
        <div class="metric-label">Total PM tasks</div>
        <div class="metric-value">{total}</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card overdue">
        <div class="metric-label">Overdue</div>
        <div class="metric-value">{overdue}</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card due">
        <div class="metric-label">Due this week</div>
        <div class="metric-value">{due_soon}</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-card ok">
        <div class="metric-label">OK / on schedule</div>
        <div class="metric-value">{ok_count}</div>
    </div>""", unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="metric-card ok">
        <div class="metric-label">Compliance rate</div>
        <div class="metric-value">{compliance}%</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Alert banner ──────────────────────────────────────────────────────────────
if overdue > 0:
    st.error(
        f"⚠️  **{overdue} task(s) are overdue.** "
        "Immediate action required — filter by 'Overdue' to view.",
        icon="🚨"
    )
if due_soon > 0:
    st.warning(
        f"🔔  **{due_soon} task(s) due within 7 days.** "
        "Plan maintenance this week.",
        icon="⏰"
    )


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 PM Schedule", "📊 Analytics", "⚡ Breakdown History", "📥 Export"
])


# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — PM Schedule
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("PM task register")

    if fdf.empty:
        st.info("No records match the current filters.")
    else:
        # Build display dataframe with coloured Status
        display_cols = [
            c for c in [eq_col, "Component", "PM_Activity", "Frequency",
                        "Last_PM_Date", "Next_Due_Date", "Days_To_Due", "Status"]
            if c in fdf.columns
        ]
        display_df = fdf[display_cols].copy()

        if "Days_To_Due" in display_df.columns:
            display_df["Days_To_Due"] = display_df["Days_To_Due"].apply(
                lambda x: f"{int(x)} days" if pd.notna(x) else "—"
            )

        # Apply row highlighting via Styler
        def _highlight(row):
            s = row.get("Status", "")
            if s == "Overdue":
                return ["background-color: #fff0f0"] * len(row)
            elif s == "Due Soon":
                return ["background-color: #fff8ee"] * len(row)
            return [""] * len(row)

        styled = display_df.style.apply(_highlight, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # Overdue table spotlight
        if "Status" in fdf.columns:
            overdue_df = fdf[fdf["Status"] == "Overdue"]
            if not overdue_df.empty:
                st.markdown("#### Overdue tasks — immediate action required")
                st.dataframe(
                    overdue_df[[c for c in display_cols if c in overdue_df.columns]],
                    use_container_width=True,
                    hide_index=True,
                )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — Analytics
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Maintenance analytics")

    if "Status" not in df.columns or df.empty:
        st.info("Need Next_Due_Date column to generate analytics.")
    else:
        col_left, col_right = st.columns(2)

        # ── Donut: status breakdown ──
        with col_left:
            status_counts = fdf["Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            color_map = {
                "Overdue": "#dc3545",
                "Due Soon": "#fd7e14",
                "OK": "#198754",
                "Unknown": "#adb5bd",
            }
            fig_donut = px.pie(
                status_counts, names="Status", values="Count",
                hole=0.55,
                color="Status",
                color_discrete_map=color_map,
                title="PM task status breakdown",
            )
            fig_donut.update_traces(textposition="outside", textinfo="percent+label")
            fig_donut.update_layout(showlegend=False, margin=dict(t=40, b=10, l=10, r=10))
            st.plotly_chart(fig_donut, use_container_width=True)

        # ── Bar: status by equipment ──
        with col_right:
            if eq_col in fdf.columns:
                grp = fdf.groupby([eq_col, "Status"]).size().reset_index(name="Count")
                fig_bar = px.bar(
                    grp, x=eq_col, y="Count", color="Status",
                    color_discrete_map=color_map,
                    title="PM status by equipment",
                    barmode="stack",
                )
                fig_bar.update_layout(
                    xaxis_tickangle=-30,
                    margin=dict(t=40, b=60, l=10, r=10),
                    legend_title_text="",
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        # ── Timeline: upcoming due dates ──
        upcoming = fdf[fdf["Status"].isin(["OK", "Due Soon"])].copy()
        if "Next_Due_Date" in upcoming.columns and not upcoming.empty:
            upcoming["Next_Due_Date"] = pd.to_datetime(upcoming["Next_Due_Date"])
            upcoming = upcoming.sort_values("Next_Due_Date").head(20)
            label_col = "PM_Activity" if "PM_Activity" in upcoming.columns else "Component"
            fig_timeline = px.scatter(
                upcoming,
                x="Next_Due_Date",
                y=label_col if label_col in upcoming.columns else upcoming.columns[0],
                color="Status",
                color_discrete_map=color_map,
                size_max=12,
                title="Upcoming PM tasks — next 20",
                labels={"Next_Due_Date": "Due date"},
            )
            fig_timeline.update_traces(marker=dict(size=10, symbol="diamond"))
            fig_timeline.update_layout(margin=dict(t=40, b=20, l=10, r=10))
            st.plotly_chart(fig_timeline, use_container_width=True)

        # ── Bar: tasks per frequency ──
        if "Frequency" in fdf.columns:
            freq_df = fdf["Frequency"].value_counts().reset_index()
            freq_df.columns = ["Frequency", "Count"]
            fig_freq = px.bar(
                freq_df, x="Frequency", y="Count",
                color="Frequency",
                title="PM tasks by frequency",
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_freq.update_layout(
                showlegend=False,
                margin=dict(t=40, b=20, l=10, r=10),
            )
            st.plotly_chart(fig_freq, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — Breakdown History
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Breakdown history")

    bd_cols = [c for c in [eq_col, "Component", "Breakdown_Date", "Issue"]
               if c in fdf.columns]

    if not bd_cols:
        st.info("No breakdown columns found in dataset.")
    else:
        bd_df = fdf[bd_cols].dropna(subset=["Breakdown_Date"] if "Breakdown_Date" in bd_cols else [bd_cols[0]])

        if bd_df.empty:
            st.success("No breakdown records for the selected filter — good sign!")
        else:
            st.dataframe(bd_df, use_container_width=True, hide_index=True)

            # Breakdown frequency chart per component
            if "Component" in bd_df.columns:
                freq_bd = bd_df["Component"].value_counts().reset_index()
                freq_bd.columns = ["Component", "Breakdowns"]
                fig_bd = px.bar(
                    freq_bd, x="Component", y="Breakdowns",
                    title="Breakdown frequency by component",
                    color="Breakdowns",
                    color_continuous_scale="Reds",
                )
                fig_bd.update_layout(
                    coloraxis_showscale=False,
                    xaxis_tickangle=-30,
                    margin=dict(t=40, b=60),
                )
                st.plotly_chart(fig_bd, use_container_width=True)

            # Breakdown trend over time
            if "Breakdown_Date" in bd_df.columns:
                bd_df["Breakdown_Date"] = pd.to_datetime(bd_df["Breakdown_Date"], errors="coerce")
                bd_monthly = (
                    bd_df.set_index("Breakdown_Date")
                    .resample("ME")
                    .size()
                    .reset_index(name="Count")
                )
                if len(bd_monthly) > 1:
                    fig_trend = px.line(
                        bd_monthly, x="Breakdown_Date", y="Count",
                        markers=True,
                        title="Monthly breakdown trend",
                        labels={"Breakdown_Date": "Month", "Count": "No. of breakdowns"},
                    )
                    fig_trend.update_traces(line_color="#dc3545", marker_color="#dc3545")
                    fig_trend.update_layout(margin=dict(t=40, b=20))
                    st.plotly_chart(fig_trend, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — Export
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Export data")
    st.caption("Download filtered data for reports or offline review.")

    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        # Export full filtered table as CSV
        csv_data = fdf.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download PM schedule (CSV)",
            data=csv_data,
            file_name=f"PM_schedule_{date.today():%Y%m%d}.csv",
            mime="text/csv",
        )

    with col_exp2:
        # Export overdue only
        if "Status" in fdf.columns:
            overdue_export = fdf[fdf["Status"] == "Overdue"].to_csv(index=False).encode("utf-8")
            st.download_button(
                label="🚨 Download overdue tasks only (CSV)",
                data=overdue_export,
                file_name=f"PM_overdue_{date.today():%Y%m%d}.csv",
                mime="text/csv",
            )

    # Summary statistics table
    st.markdown("#### Summary statistics")
    if "Status" in fdf.columns and eq_col in fdf.columns:
        summary = (
            fdf.groupby(eq_col)["Status"]
            .value_counts()
            .unstack(fill_value=0)
            .reset_index()
        )
        st.dataframe(summary, use_container_width=True, hide_index=True)
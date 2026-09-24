import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# --- 1. CONFIGURATION & CONSTANTS ---
st.set_page_config(
    page_title="Provisional Natality Analytics | CDC",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

US_STATE_TO_ABBREV = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
    "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA",
    "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}

ORDERED_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

COLOR_MAP = {
    "Female": "#1b9e77",  # Accessible Teal
    "Male": "#d95f02",    # Accessible Amber / Vermilion
    "Total": "#2c7bb6"    # Accessible Slate Blue
}


# --- 2. DATA INGESTION & VALIDATION ---
def resolve_data_path() -> Path:
    """Resolves data path across local environments and Streamlit Cloud."""
    base_dir = Path(__file__).resolve().parent
    candidates = [
        base_dir / "Provisional_Natality_2025_CDC1.csv",
        base_dir / "data" / "Provisional_Natality_2025_CDC1.csv",
        Path("Provisional_Natality_2025_CDC1.csv"),
        Path("data/Provisional_Natality_2025_CDC1.csv")
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("Could not find 'Provisional_Natality_2025_CDC1.csv'.")


def validate_dataframe(df: pd.DataFrame) -> None:
    """Runs data contract assertions."""
    required_cols = {"state_of_residence", "month", "month_code", "year_code", "sex_of_infant", "births"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if (df["births"] < 0).any():
        raise ValueError("Data error: negative birth values detected.")

    if df["births"].isnull().any():
        raise ValueError("Data error: null birth counts detected.")

    missing_states = set(df["state_of_residence"]) - set(US_STATE_TO_ABBREV.keys())
    if missing_states:
        raise ValueError(f"Unmapped geographies detected: {missing_states}")


@st.cache_data(show_spinner=True)
def load_natality_data() -> pd.DataFrame:
    """Loads, validates, and enhances raw CDC natality records."""
    file_path = resolve_data_path()
    df = pd.read_csv(file_path)
    validate_dataframe(df)

    # Attach postal codes and categorical ordering
    df["state_abbrev"] = df["state_of_residence"].map(US_STATE_TO_ABBREV)
    df["month"] = pd.Categorical(df["month"], categories=ORDERED_MONTHS, ordered=True)
    return df.sort_values(["state_of_residence", "month_code", "sex_of_infant"]).reset_index(drop=True)


# --- 3. VISUALIZATION FUNCTIONS ---
def create_monthly_trend_chart(df: pd.DataFrame) -> go.Figure:
    monthly_agg = df.groupby(["month", "month_code"], observed=True)["births"].sum().reset_index()
    monthly_agg = monthly_agg.sort_values("month_code")

    fig = px.line(
        monthly_agg,
        x="month",
        y="births",
        markers=True,
        title="Total Registered Births by Month (2025)",
        labels={"month": "Month", "births": "Total Births"}
    )
    fig.update_traces(
        line=dict(color=COLOR_MAP["Total"], width=3),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>Total Births: %{y:,.0f}<extra></extra>"
    )
    fig.update_layout(
        yaxis=dict(range=[0, monthly_agg["births"].max() * 1.15]),
        margin=dict(l=40, r=20, t=50, b=40),
        template="plotly_white"
    )
    return fig


def create_top_bottom_comparison(df: pd.DataFrame, n: int = 5) -> go.Figure:
    state_agg = df.groupby("state_of_residence", observed=True)["births"].sum().reset_index()
    if len(state_agg) < 2 * n:
        n = max(1, len(state_agg) // 2)

    top_df = state_agg.nlargest(n, "births").copy()
    top_df["Cohort"] = f"Top {n}"

    bottom_df = state_agg.nsmallest(n, "births").copy()
    bottom_df["Cohort"] = f"Bottom {n}"

    combined = pd.concat([top_df, bottom_df]).sort_values("births", ascending=True)

    fig = px.bar(
        combined,
        x="births",
        y="state_of_residence",
        color="Cohort",
        orientation="h",
        title=f"Top {n} vs. Bottom {n} Geographies by Birth Volume",
        labels={"births": "Total Births", "state_of_residence": "State"},
        color_discrete_map={f"Top {n}": "#2c7bb6", f"Bottom {n}": "#fdae61"}
    )
    fig.update_traces(hovertemplate="<b>%{y}</b> (%{data.name})<br>Births: %{x:,.0f}<extra></extra>")
    fig.update_layout(
        xaxis=dict(range=[0, combined["births"].max() * 1.1]),
        margin=dict(l=40, r=20, t=50, b=40),
        template="plotly_white"
    )
    return fig


def create_choropleth_map(df: pd.DataFrame) -> go.Figure:
    map_agg = df.groupby(["state_of_residence", "state_abbrev"], observed=True)["births"].sum().reset_index()
    fig = px.choropleth(
        map_agg,
        locations="state_abbrev",
        locationmode="USA-states",
        color="births",
        scope="usa",
        color_continuous_scale="Blues",
        title="Geographic Distribution of Selected Births",
        hover_name="state_of_residence",
        labels={"births": "Births"}
    )
    fig.update_traces(hovertemplate="<b>%{hovertext}</b> (%{location})<br>Total Births: %{z:,.0f}<extra></extra>")
    fig.update_layout(
        geo=dict(lakecolor="rgb(255, 255, 255)"),
        margin=dict(l=10, r=10, t=50, b=10),
        coloraxis_colorbar=dict(title="Births", tickformat=",.0f")
    )
    return fig


def create_state_ranking_chart(df: pd.DataFrame) -> go.Figure:
    state_agg = df.groupby("state_of_residence", observed=True)["births"].sum().reset_index()
    state_agg = state_agg.sort_values("births", ascending=True)

    fig = px.bar(
        state_agg,
        x="births",
        y="state_of_residence",
        orientation="h",
        title="Total Birth Volume by Geography",
        labels={"births": "Births", "state_of_residence": "State / Jurisdiction"},
        color_discrete_sequence=[COLOR_MAP["Total"]]
    )
    fig.update_traces(hovertemplate="<b>%{y}</b><br>Births: %{x:,.0f}<extra></extra>")
    fig.update_layout(
        xaxis=dict(range=[0, state_agg["births"].max() * 1.1]),
        height=max(400, len(state_agg) * 22),
        margin=dict(l=40, r=20, t=50, b=40),
        template="plotly_white"
    )
    return fig


def create_sex_comparison_chart(df: pd.DataFrame) -> go.Figure:
    sex_agg = df.groupby(["month", "sex_of_infant"], observed=True)["births"].sum().reset_index()

    fig = px.bar(
        sex_agg,
        x="month",
        y="births",
        color="sex_of_infant",
        barmode="group",
        title="Monthly Birth Counts by Infant Sex",
        labels={"month": "Month", "births": "Birth Count", "sex_of_infant": "Infant Sex"},
        color_discrete_map=COLOR_MAP
    )
    fig.update_traces(hovertemplate="<b>%{x} (%{data.name})</b><br>Births: %{y:,.0f}<extra></extra>")
    fig.update_layout(
        yaxis=dict(range=[0, sex_agg["births"].max() * 1.15]),
        legend=dict(title_text="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=50, b=40),
        template="plotly_white"
    )
    return fig


def create_heatmap(df: pd.DataFrame) -> go.Figure:
    pivot = df.pivot_table(
        index="state_of_residence",
        columns="month",
        values="births",
        aggfunc="sum",
        observed=True
    ).fillna(0)

    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale="Viridis",
        title="State-by-Month Natality Volume Heatmap",
        labels=dict(x="Month", y="State / Jurisdiction", color="Births")
    )
    fig.update_traces(hovertemplate="State: %{y}<br>Month: %{x}<br>Births: %{z:,.0f}<extra></extra>")
    fig.update_layout(
        height=max(500, len(pivot) * 18),
        margin=dict(l=40, r=20, t=50, b=40),
        coloraxis_colorbar=dict(title="Births", tickformat=",.0f")
    )
    return fig


# --- 4. MAIN APPLICATION ---
def main():
    # Ingest Data
    try:
        raw_df = load_natality_data()
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        st.stop()

    # Header & Pedagogy Notices
    st.title("Provisional U.S. Natality Dashboard (2025)")
    st.caption("CDC National Center for Health Statistics (NCHS) • Vital Statistics Cooperative Program")

    h_col1, h_col2 = st.columns([1, 1])
    with h_col1:
        st.warning(
            "**Provisional Data Notice:** Preliminary counts based on initial state reporting. "
            "Values remain subject to retrospective revisions as jurisdictions reconcile records.",
            icon="⚠️"
        )
    with h_col2:
        st.info(
            "**Metric Distinction:** Figures represent raw **birth counts**, not birth rates. "
            "Higher totals reflect jurisdiction population size rather than elevated fertility rates.",
            icon="ℹ️"
        )

    st.divider()

    # Sidebar Filter Controls
    st.sidebar.header("Filter Criteria")
    all_states = sorted(raw_df["state_of_residence"].unique().tolist())
    all_months = raw_df["month"].cat.categories.tolist()
    sex_options = ["All", "Female", "Male"]

    if "selected_states" not in st.session_state:
        st.session_state.selected_states = all_states
    if "selected_months" not in st.session_state:
        st.session_state.selected_months = all_months
    if "selected_sex" not in st.session_state:
        st.session_state.selected_sex = "All"

    btn_col1, btn_col2 = st.sidebar.columns(2)
    if btn_col1.button("Select All", use_container_width=True):
        st.session_state.selected_states = all_states
        st.session_state.selected_months = all_months
        st.session_state.selected_sex = "All"
        st.rerun()

    if btn_col2.button("Reset Filters", use_container_width=True):
        st.session_state.selected_states = all_states
        st.session_state.selected_months = all_months
        st.session_state.selected_sex = "All"
        st.rerun()

    selected_states = st.sidebar.multiselect("States / Geographies", options=all_states, key="selected_states")
    selected_months = st.sidebar.multiselect("Months", options=all_months, key="selected_months")
    selected_sex = st.sidebar.radio("Infant Sex", options=sex_options, key="selected_sex", horizontal=True)

    st.sidebar.divider()
    st.sidebar.markdown(
        f"""
        **Active Filter Scope:**
        - **Geographies:** {len(selected_states)} / {len(all_states)}
        - **Months:** {len(selected_months)} / {len(all_months)}
        - **Infant Sex:** `{selected_sex}`
        """
    )

    # Filter Dataset
    filtered_df = raw_df[
        (raw_df["state_of_residence"].isin(selected_states)) &
        (raw_df["month"].isin(selected_months))
    ]
    if selected_sex != "All":
        filtered_df = filtered_df[filtered_df["sex_of_infant"] == selected_sex]

    # Empty State Guardrail
    if filtered_df.empty:
        st.error("⚠️ No observations match your filter criteria. Please broaden your selection in the sidebar.")
        return

    # Render KPI Cards
    total_births = filtered_df["births"].sum()
    num_states = filtered_df["state_of_residence"].nunique()
    num_months = filtered_df["month"].nunique()
    avg_per_month = total_births / num_months if num_months > 0 else 0

    state_totals = filtered_df.groupby("state_of_residence")["births"].sum()
    top_state = state_totals.idxmax() if not state_totals.empty else "N/A"
    top_state_val = state_totals.max() if not state_totals.empty else 0

    month_totals = filtered_df.groupby("month", observed=True)["births"].sum()
    top_month = str(month_totals.idxmax()) if not month_totals.empty else "N/A"
    top_month_val = month_totals.max() if not month_totals.empty else 0

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Total Births", f"{total_births:,.0f}")
    kpi2.metric("Geographies", f"{num_states:d}")
    kpi3.metric("Avg Births / Month", f"{avg_per_month:,.0f}")
    kpi4.metric("Top Geography", top_state, f"{top_state_val:,.0f} births")
    kpi5.metric("Peak Month", top_month, f"{top_month_val:,.0f} births")

    st.markdown("---")

    # Analytical Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview",
        "🗺️ Geographic Analysis",
        "👥 Monthly & Sex Analysis",
        "📋 Data Table & Download",
        "📖 About the Data"
    ])

    with tab1:
        st.subheader("Aggregate Trends & Cohort Extremes")
        col1, col2 = st.columns([3, 2])
        with col1:
            st.plotly_chart(create_monthly_trend_chart(filtered_df), use_container_width=True)
        with col2:
            st.plotly_chart(create_top_bottom_comparison(filtered_df, n=5), use_container_width=True)

    with tab2:
        st.subheader("Geographic Distribution & State Ranking")
        st.plotly_chart(create_choropleth_map(filtered_df), use_container_width=True)
        st.plotly_chart(create_state_ranking_chart(filtered_df), use_container_width=True)

    with tab3:
        st.subheader("Demographic & Temporal Patterns")
        st.plotly_chart(create_sex_comparison_chart(filtered_df), use_container_width=True)
        st.plotly_chart(create_heatmap(filtered_df), use_container_width=True)

    with tab4:
        st.subheader("Filtered Natality Records")
        st.caption("Interactive, searchable view of the current filtered slice.")

        display_df = filtered_df[[
            "state_of_residence", "month", "sex_of_infant", "births"
        ]].rename(columns={
            "state_of_residence": "State / Jurisdiction",
            "month": "Month",
            "sex_of_infant": "Infant Sex",
            "births": "Birth Count"
        })

        st.dataframe(
            display_df.style.format({"Birth Count": "{:,.0f}"}),
            use_container_width=True,
            hide_index=True
        )

        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Current Filtered Data (CSV)",
            data=csv_data,
            file_name="provisional_natality_filtered_2025.csv",
            mime="text/csv"
        )

    with tab5:
        st.subheader("Methodology, Caveats, and CDC Source Context")
        st.markdown(
            """
            ### Background & Attribution
            The data analyzed here originate from the **Centers for Disease Control and Prevention (CDC)** 
            National Center for Health Statistics (NCHS) Vital Statistics Cooperative Program (VSCP).

            ### Crucial Analytics Considerations for Students:
            1. **Counts vs. Rates (Confounding by Population Size):**
               * The figures shown here represent absolute **birth counts**, *not* birth rates (e.g., General Fertility Rate or Crude Birth Rate).
               * States with large populations like California, Texas, and Florida naturally report the highest volume of births. High totals should not be confused with high reproductive propensity.
            2. **Provisional Status:**
               * Data from 2025 are preliminary and subject to ongoing revision as state registries complete birth record reconciliations.
            3. **Demographic Benchmarks:**
               * Biological sex ratios typically exhibit stable distributions of approximately ~105 male births per 100 female births across large population aggregates.
            """
        )


if __name__ == "__main__":
    main()

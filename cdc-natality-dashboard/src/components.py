import streamlit as st
import pandas as pd


def render_header():
    """Renders header banner with CDC attribution, provisional notice, and rate warnings."""
    st.title("Provisional U.S. Natality Dashboard (2025)")
    st.caption("CDC National Center for Health Statistics (NCHS) • Vital Statistics Cooperative Program")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.warning(
            "**Provisional Data Notice:** These records are preliminary counts based on initial "
            "state reporting and remain subject to retrospective revisions.",
            icon="⚠️"
        )
    with col2:
        st.info(
            "**Metric Distinction:** Values represent raw **birth counts**, not birth rates. "
            "High totals naturally mirror populated jurisdictions rather than elevated fertility rates.",
            icon="ℹ️"
        )


def render_kpis(filtered_df: pd.DataFrame, full_df: pd.DataFrame):
    """Calculates and renders KPI summary metrics."""
    if filtered_df.empty:
        st.warning("No records found matching current selection.")
        return

    total_births = filtered_df["births"].sum()
    num_states = filtered_df["state_of_residence"].nunique()
    num_months = filtered_df["month"].nunique()
    avg_per_month = total_births / num_months if num_months > 0 else 0

    # Max State calculation
    state_totals = filtered_df.groupby("state_of_residence")["births"].sum()
    top_state = state_totals.idxmax() if not state_totals.empty else "N/A"
    top_state_val = state_totals.max() if not state_totals.empty else 0

    # Max Month calculation
    month_totals = filtered_df.groupby("month", observed=True)["births"].sum()
    top_month = str(month_totals.idxmax()) if not month_totals.empty else "N/A"
    top_month_val = month_totals.max() if not month_totals.empty else 0

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Total Births", f"{total_births:,.0f}")
    kpi2.metric("Geographies", f"{num_states:d}")
    kpi3.metric("Avg Births / Month", f"{avg_per_month:,.0f}")
    kpi4.metric("Top Geography", top_state, f"{top_state_val:,.0f} births")
    kpi5.metric("Peak Month", top_month, f"{top_month_val:,.0f} births")


def render_sidebar_filters(df: pd.DataFrame):
    """Renders filter controls in sidebar with Reset and Select All capabilities."""
    st.sidebar.header("Filter Criteria")

    all_states = sorted(df["state_of_residence"].unique().tolist())
    all_months = df["month"].cat.categories.tolist()
    sex_options = ["All", "Female", "Male"]

    # Initialize session state keys
    if "selected_states" not in st.session_state:
        st.session_state.selected_states = all_states
    if "selected_months" not in st.session_state:
        st.session_state.selected_months = all_months
    if "selected_sex" not in st.session_state:
        st.session_state.selected_sex = "All"

    # Action buttons: Select All and Reset
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

    # Multiselect inputs
    selected_states = st.sidebar.multiselect(
        "States / Geographies",
        options=all_states,
        key="selected_states"
    )

    selected_months = st.sidebar.multiselect(
        "Months",
        options=all_months,
        key="selected_months"
    )

    selected_sex = st.sidebar.radio(
        "Infant Sex",
        options=sex_options,
        key="selected_sex",
        horizontal=True
    )

    # Active Filter Context Pill
    st.sidebar.divider()
    st.sidebar.markdown(
        f"""
        **Active Filter Scope:**
        - **Geographies:** {len(selected_states)} / {len(all_states)}
        - **Months:** {len(selected_months)} / {len(all_months)}
        - **Sex Selection:** `{selected_sex}`
        """
    )

    # Apply filters
    filtered_df = df[
        (df["state_of_residence"].isin(selected_states)) &
        (df["month"].isin(selected_months))
    ]

    if selected_sex != "All":
        filtered_df = filtered_df[filtered_df["sex_of_infant"] == selected_sex]

    return filtered_df

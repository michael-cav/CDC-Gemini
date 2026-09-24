import streamlit as st
import pandas as pd
from src.data_loader import load_natality_data
from src.components import render_header, render_kpis, render_sidebar_filters
import src.visuals as visuals

# Configure page metadata
st.set_page_config(
    page_title="Provisional Natality Analytics | CDC",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    # 1. Load Data
    try:
        raw_df = load_natality_data()
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        st.stop()

    # 2. Render Header
    render_header()
    st.divider()

    # 3. Render Sidebar Controls & Filter Data
    filtered_df = render_sidebar_filters(raw_df)

    # 4. Render KPI Cards
    render_kpis(filtered_df, raw_df)
    st.markdown("---")

    # 5. Empty Selection Guardrail
    if filtered_df.empty:
        st.error(
            "⚠️ No data matches your filter criteria. "
            "Please select at least one state, month, and sex category from the sidebar."
        )
        return

    # 6. Tab Navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview",
        "🗺️ Geographic Analysis",
        "👥 Monthly & Sex Analysis",
        "📋 Data Table & Download",
        "📖 About the Data"
    ])

    # Tab 1: Overview
    with tab1:
        st.subheader("Aggregate Trends & Cohort Extremes")
        col1, col2 = st.columns([3, 2])
        with col1:
            st.plotly_chart(visuals.create_monthly_trend_chart(filtered_df), use_container_width=True)
        with col2:
            st.plotly_chart(visuals.create_top_bottom_comparison(filtered_df, n=5), use_container_width=True)

    # Tab 2: Geographic Analysis
    with tab2:
        st.subheader("Geographic Distribution & State Ranking")
        st.plotly_chart(visuals.create_choropleth_map(filtered_df), use_container_width=True)
        st.plotly_chart(visuals.create_state_ranking_chart(filtered_df), use_container_width=True)

    # Tab 3: Monthly and Sex Analysis
    with tab3:
        st.subheader("Demographic & Temporal Patterns")
        st.plotly_chart(visuals.create_sex_comparison_chart(filtered_df), use_container_width=True)
        st.plotly_chart(visuals.create_heatmap(filtered_df), use_container_width=True)

    # Tab 4: Data Table and Download
    with tab4:
        st.subheader("Filtered Natality Records")
        st.caption("Interactive, searchable view of the current filtered slice.")

        # Formatting table for display
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

    # Tab 5: About the Data
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
               * States with large populations like California, Texas, and Florida naturally have the highest volume of births. High totals should not be confused with high reproductive propensity.
            2. **Provisional Status:**
               * Data from 2025 are provisional and subject to retrospective lag. Early reporting periods frequently experience updates as state health registries reconcile birth certificates.
            3. **Analytical Uses:**
               * Studying seasonality patterns across months.
               * Validating biological sex ratio stability (typically ~105 male births per 100 female births).
            """
        )


if __name__ == "__main__":
    main()

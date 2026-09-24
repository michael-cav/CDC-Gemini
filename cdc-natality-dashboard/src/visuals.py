import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

COLOR_MAP = {
    "Female": "#1b9e77",  # Accessible Teal / Green
    "Male": "#d95f02",    # Accessible Amber / Vermilion
    "Total": "#2c7bb6"    # Neutral Blue
}


def create_monthly_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Renders monthly aggregate trend with non-truncated zero baseline."""
    monthly_agg = df.groupby(["month", "month_code"], observed=True)["births"].sum().reset_index()
    monthly_agg = monthly_agg.sort_values("month_code")

    fig = px.line(
        monthly_agg,
        x="month",
        y="births",
        markers=True,
        title="Total Registered Births by Month (2025)",
        labels={"month": "Month", "births": "Total Births"},
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


def create_sex_comparison_chart(df: pd.DataFrame) -> go.Figure:
    """Renders grouped bar chart comparing Female and Male counts by month."""
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


def create_state_ranking_chart(df: pd.DataFrame) -> go.Figure:
    """Renders descending horizontal bar chart of all selected geographies."""
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


def create_choropleth_map(df: pd.DataFrame) -> go.Figure:
    """Renders interactive US choropleth map using 2-letter state codes."""
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
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b> (%{location})<br>Total Births: %{z:,.0f}<extra></extra>"
    )
    fig.update_layout(
        geo=dict(lakecolor="rgb(255, 255, 255)"),
        margin=dict(l=10, r=10, t=50, b=10),
        coloraxis_colorbar=dict(title="Births", tickformat=",.0f")
    )
    return fig


def create_heatmap(df: pd.DataFrame) -> go.Figure:
    """Renders state-by-month cross-tabulation heatmap."""
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
    fig.update_traces(
        hovertemplate="State: %{y}<br>Month: %{x}<br>Births: %{z:,.0f}<extra></extra>"
    )
    fig.update_layout(
        height=max(500, len(pivot) * 18),
        margin=dict(l=40, r=20, t=50, b=40),
        coloraxis_colorbar=dict(title="Births", tickformat=",.0f")
    )
    return fig


def create_top_bottom_comparison(df: pd.DataFrame, n: int = 5) -> go.Figure:
    """Renders side-by-side comparison of Top N and Bottom N geographies."""
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
        title=f"Comparison: Top {n} vs. Bottom {n} Geographies by Birth Volume",
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

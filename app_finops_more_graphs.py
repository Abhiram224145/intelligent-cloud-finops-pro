import streamlit as st
import pandas as pd
import plotly.express as px
from notification_system import create_notification
from aws_connector import get_aws_resources, detect_resource_waste
from analyzer import analyze_resources
from auth import show_login, get_all_users, update_user_role

st.set_page_config(
    page_title="Cloud FinOps Optimizer",
    page_icon="☁️",
    layout="wide"
)

# -------------------------------
# FinOps dashboard visual styling
# -------------------------------
st.markdown("""<style>
    :root {
        --finops-accent: #38bdf8;
        --finops-accent-strong: #0284c7;
        --finops-panel: rgba(30, 41, 59, 0.72);
        --finops-border: rgba(148, 163, 184, 0.22);
    }
    .stApp {
        background: radial-gradient(ellipse at top left, rgba(14, 116, 144, 0.12), transparent 38%),
                    linear-gradient(180deg, #0b1220 0%, #111827 100%);
    }
    [data-testid="stHeader"] {
        background: rgba(11, 18, 32, 0.78);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #172033 100%);
        border-right: 1px solid var(--finops-border);
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.2rem;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1440px;
    }
    h1, h2, h3 {
        letter-spacing: -0.025em;
    }
    h1 {
        font-weight: 750 !important;
        line-height: 1.15 !important;
    }
    h2, h3 {
        font-weight: 650 !important;
    }
    [data-testid="stMetric"] {
        background: var(--finops-panel);
        border: 1px solid var(--finops-border);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }
    [data-testid="stMetricLabel"] {
        color: #cbd5e1;
        font-weight: 600;
    }
    [data-testid="stMetricValue"] {
        color: #f8fafc;
        font-weight: 750;
    }
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        border: 1px solid var(--finops-border);
        border-radius: 12px;
        overflow: hidden;
    }
    div[data-testid="stPlotlyChart"] {
        background: rgba(15, 23, 42, 0.45);
        border: 1px solid var(--finops-border);
        border-radius: 14px;
        padding: 8px 8px 0 8px;
    }
    .stButton > button, .stDownloadButton > button {
        border-radius: 10px;
        border: 1px solid rgba(56, 189, 248, 0.5);
        font-weight: 650;
        transition: all 120ms ease-in-out;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: var(--finops-accent);
        color: #e0f2fe;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.12);
    }
    [data-testid="stFileUploader"] section {
        background: rgba(30, 41, 59, 0.42);
        border: 1px dashed rgba(56, 189, 248, 0.45);
        border-radius: 14px;
    }
    [data-testid="stAlert"] {
        border-radius: 12px;
    }
    hr {
        border-color: var(--finops-border);
    }
    @media (max-width: 768px) {
        .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        [data-testid="stMetric"] {
            padding: 12px;
        }
    }
</style>
""", unsafe_allow_html=True)
if not show_login():
    st.stop()

user_role = st.session_state.get("role", "Resource Owner")
st.sidebar.title("☁️ FinOps Navigation")

page = st.sidebar.radio(
    "Choose Dashboard",
    [
        "Overview",
        "Cloud Resource Monitoring",
        "Cost Analysis",
        "AI Predictions",
        "Optimization Recommendations",
        "Notifications & Approvals",
        "Reports",
    ],
)

if user_role == "Admin" and page == "Overview":
    st.header("Admin User Management")

    users = get_all_users()
    if users:
        st.dataframe(users, use_container_width=True)

        usernames = [user["Username"] for user in users]

        selected_user = st.selectbox(
            "Select a user",
            usernames,
            key="admin_selected_user",
        )

        new_role = st.selectbox(
            "Choose a new role",
            ["Resource Owner", "Manager", "Admin"],
            key="admin_new_role",
        )
        if st.button("Update User Role"):
            success, message = update_user_role(
                selected_user, new_role
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    else:
        st.info("No registered users found.")
st.sidebar.write(f"Access Level: {user_role}")

page_titles = {
    "Overview": "☁️ Intelligent Cloud FinOps Optimization Engine",
    "Cloud Resource Monitoring": "☁️ Cloud Resource Monitoring",
    "Cost Analysis": "💰 Cloud Cost Analysis",
    "AI Predictions": "🤖 AI Cost Predictions",
    "Optimization Recommendations": "🎯 Optimization Recommendations",
    "Notifications & Approvals": "🔔 Notifications & Approvals",
    "Reports": "📄 FinOps Reports",
}
st.title(page_titles.get(page, "☁️ Cloud FinOps Optimizer"))
st.caption("Cloud cost visibility • Waste detection • Practical optimization insights")

# Show the CSV upload only on Overview. Other pages use the default CSV.
uploaded_file = None
if page == "Overview":
    st.subheader("Cloud Resource Data")
    uploaded_file = st.file_uploader(
        "Upload your cloud resources CSV file",
        type=["csv"]
    )

try:
    if uploaded_file is not None:
        raw_data = pd.read_csv(uploaded_file)
    else:
        raw_data = pd.read_csv("cloud_resources.csv")

    results = analyze_resources(raw_data)

except Exception as error:
    st.error(f"Unable to analyze data: {error}")
    st.stop()


total_cost = results["monthly_cost"].sum()
total_savings = results["estimated_savings"].sum()
flagged = (results["recommendation"] != "Normal usage").sum()
anomalies = results["anomaly"].sum()


if page == 'Cloud Resource Monitoring':
    st.subheader("☁️ AWS Resource Monitoring")

    if st.button("Analyze Demo AWS Resources"):
        aws_data = get_aws_resources()

        st.success("Demo resources loaded successfully!")
        st.dataframe(aws_data, use_container_width=True)

        total_cost = aws_data["monthly_cost"].sum()
        st.metric("Total Demo Monthly Cost", f"₹{total_cost:,.2f}")

        waste_data = detect_resource_waste(aws_data)

        st.subheader("⚠️ Potential Resource Waste")

        if not waste_data.empty:
            st.dataframe(waste_data, use_container_width=True)

            potential_savings = waste_data["monthly_cost"].sum()
            st.metric(
                "Potential Monthly Savings",
                f"₹{potential_savings:,.2f}"
            )
        else:
            st.success("No potential waste detected.")
    st.write("Detect cloud resource waste and estimate potential savings.")
    # -------------------------------
    # Resource Health Monitor
    # -------------------------------

    st.subheader("Resource Health Monitor")

    health_data = results.copy()

    required_columns = [
        "resource_id", "cpu_usage", "memory_usage"
    ]

    if all(col in health_data.columns for col in required_columns):
        health_data["cpu_usage"] = pd.to_numeric(
            health_data["cpu_usage"], errors="coerce"
        )
        health_data["memory_usage"] = pd.to_numeric(
            health_data["memory_usage"], errors="coerce"
        )

        health_data = health_data.dropna(
            subset=["cpu_usage", "memory_usage"]
        )

        def get_health(row):
            if row["cpu_usage"] < 10 and row["memory_usage"] < 20:
                return "Underutilized"
            elif row["cpu_usage"] > 90 or row["memory_usage"] > 90:
                return "Needs Review"
            return "Healthy"

        health_data["health_status"] = health_data.apply(
            get_health, axis=1
        )

        st.dataframe(
            health_data[
                [
                    "resource_id",
                    "cpu_usage",
                    "memory_usage",
                    "health_status"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        health_chart = px.scatter(
            health_data,
            x="cpu_usage",
            y="memory_usage",
            color="health_status",
            size="monthly_cost" if "monthly_cost" in health_data.columns else None,
            hover_name="resource_id",
            title="Resource Health Map: CPU vs Memory",
            labels={
                "cpu_usage": "CPU Usage (%)",
                "memory_usage": "Memory Usage (%)",
                "health_status": "Health Status",
                "monthly_cost": "Monthly Cost (₹)"
            },
            template="plotly_dark"
        )
        health_chart.update_layout(legend_title_text="Resource Health")
        st.plotly_chart(health_chart, width="stretch")

        usage_long = health_data.melt(
            id_vars=["resource_id"], value_vars=["cpu_usage", "memory_usage"],
            var_name="Metric", value_name="Usage (%)"
        )
        usage_box = px.box(
            usage_long, x="Metric", y="Usage (%)", points="all",
            hover_data=["resource_id"], title="CPU vs Memory Usage Distribution",
            template="plotly_dark", color="Metric",
            color_discrete_sequence=["#38bdf8", "#818cf8"]
        )
        st.plotly_chart(usage_box, use_container_width=True)
    else:
        st.warning("Required CPU, memory, or resource ID columns are missing.")

    # Cloud Resource Search and Filter
    st.subheader("Cloud Resource Search and Filter")

    search_data = results.copy()

    search_text = st.text_input(
        "Search by resource ID",
        placeholder="Example: VM-01",
        key="resource_search"
    )

    resource_types = (
        search_data["resource_type"].dropna().unique().tolist()
        if "resource_type" in search_data.columns
        else []
    )

    selected_types = st.multiselect(
        "Filter by resource type",
        options=resource_types,
        default=resource_types,
        key="resource_type_filter"
    )

    filtered_data = search_data.copy()

    if search_text:
        filtered_data = filtered_data[
            filtered_data["resource_id"].astype(str).str.contains(
                search_text, case=False, na=False
            )
        ]

    if "resource_type" in filtered_data.columns:
        filtered_data = filtered_data[
            filtered_data["resource_type"].isin(selected_types)
        ]

    st.write(f"Matching resources: {len(filtered_data)}")

    st.dataframe(
        filtered_data,
        width="stretch",
        hide_index=True
    )

    # Cloud Resource Waste Detection Chart
    st.header("📊 Cloud Resource Waste Detection")

    if not results.empty:
        waste_data = results.copy()

        waste_data["resource_status"] = waste_data.apply(
            lambda row: (
                "Underutilized"
                if row["cpu_usage"] < 10 and row["memory_usage"] < 20
                else "High Usage"
                if row["cpu_usage"] > 90 or row["memory_usage"] > 90
                else "Normal"
            ),
            axis=1
        )

        status_counts = (
            waste_data["resource_status"]
            .value_counts()
            .reset_index()
        )
        status_counts.columns = ["Status", "Resource Count"]

        waste_chart = px.pie(
            status_counts,
            names="Status",
            values="Resource Count",
            hole=0.62,
            title="Resource Status Distribution",
            color="Status",
            template="plotly_dark"
        )
        waste_chart.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(waste_chart, width="stretch")

        st.subheader("Resources Requiring Attention")

        attention = waste_data[
            waste_data["resource_status"] != "Normal"
        ]

        st.dataframe(
            attention[
                ["resource_id", "cpu_usage", "memory_usage",
                 "resource_status"]
            ],
            use_container_width=True
        )


if page == 'Overview':
    total_cost = results["monthly_cost"].sum()
    total_savings = results["estimated_savings"].sum()

    flagged = (
        results["recommendation"] != "Normal usage"
    ).sum()

    anomalies = results["anomaly"].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Monthly Cloud Cost", f"₹{total_cost:,.0f}")
    col2.metric("Estimated Savings", f"₹{total_savings:,.0f}")
    col3.metric("Resources to Review", int(flagged))
    col4.metric("ML Anomalies", int(anomalies))

    st.subheader("Monthly Cost by Resource")

    cost_tree = results.copy()
    cost_tree["monthly_cost"] = pd.to_numeric(cost_tree["monthly_cost"], errors="coerce").fillna(0)
    fig = px.treemap(
        cost_tree,
        path=["recommendation", "resource_id"],
        values="monthly_cost",
        color="monthly_cost",
        color_continuous_scale="Blues",
        title="Cloud Cost Treemap — Larger Tiles Mean Higher Cost",
        hover_data={"monthly_cost": ":,.0f"},
        template="plotly_dark"
    )
    fig.update_layout(margin=dict(t=55, l=10, r=10, b=10))
    st.plotly_chart(fig, width="stretch")

    st.subheader("AI/ML Analysis Results")

    st.dataframe(
        results,
        use_container_width=True,
        hide_index=True
    )

    report = results.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Analysis Report",
        data=report,
        file_name="cloud_finops_report.csv",
        mime="text/csv"
    )
    # Cloud Resource Optimization Score
    st.header("🎯 Cloud Resource Optimization Score")

    if not results.empty:
        total_resources = len(results)

        underutilized = (
            (results["cpu_usage"] < 10) &
            (results["memory_usage"] < 20)
        ).sum()

        optimized_resources = total_resources - underutilized
        optimization_score = round(
            (optimized_resources / total_resources) * 100, 2
        )

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Resources", total_resources)
        col2.metric("Underutilized Resources", int(underutilized))
        col3.metric("Optimization Score", f"{optimization_score}%")

        if optimization_score >= 80:
            st.success("Good resource utilization!")
        elif optimization_score >= 50:
            st.warning("Some resources need optimization.")
        else:
            st.error("High resource waste detected.")

        st.progress(optimization_score / 100)

        st.caption(
            "Demo score based on CPU and memory utilization. "
            "It is not an official cloud-provider metric."
        )

    # Additional overview visuals: recommendation mix and cost distribution
    st.subheader("More Insights")
    chart_left, chart_right = st.columns(2)
    with chart_left:
        if "recommendation" in results.columns and "monthly_cost" in results.columns:
            rec_cost = results.copy()
            rec_cost["monthly_cost"] = pd.to_numeric(rec_cost["monthly_cost"], errors="coerce").fillna(0)
            sun = px.sunburst(
                rec_cost, path=["recommendation", "resource_id"], values="monthly_cost",
                title="Cost Breakdown by Recommendation", template="plotly_dark",
                color="monthly_cost", color_continuous_scale="Blues"
            )
            sun.update_layout(margin=dict(t=55, l=5, r=5, b=5))
            st.plotly_chart(sun, use_container_width=True)
    with chart_right:
        if "monthly_cost" in results.columns:
            cost_values = pd.to_numeric(results["monthly_cost"], errors="coerce").dropna()
            hist_data = pd.DataFrame({"Monthly Cost (₹)": cost_values})
            hist = px.histogram(
                hist_data, x="Monthly Cost (₹)", nbins=10,
                title="Distribution of Resource Costs", template="plotly_dark",
                color_discrete_sequence=["#38bdf8"]
            )
            hist.update_layout(yaxis_title="Number of Resources", bargap=0.12)
            st.plotly_chart(hist, use_container_width=True)


if page == 'AI Predictions':
    # -------------------------------
    # Cloud Cost Forecasting
    # -------------------------------

    st.subheader("Cloud Cost Forecasting")

    if "monthly_cost" in results.columns:
        total_cost = pd.to_numeric(
            results["monthly_cost"], errors="coerce"
        ).fillna(0).sum()

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Current Monthly Cost", f"₹{total_cost:,.0f}")

        with col2:
            growth_rate = st.slider(
                "Expected monthly cost growth (%)",
                min_value=0,
                max_value=30,
                value=5
            )

        forecast_cost = total_cost * (1 + growth_rate / 100)

        st.metric(
            "Estimated Next Month Cost",
            f"₹{forecast_cost:,.0f}",
            delta=f"₹{forecast_cost - total_cost:,.0f}"
        )

        forecast_data = pd.DataFrame({
            "Period": ["Current Month", "Next Month Forecast"],
            "Cost (₹)": [total_cost, forecast_cost]
        })

        forecast_data["Sequence"] = [1, 2]
        fig_forecast = px.line(
            forecast_data,
            x="Period",
            y="Cost (₹)",
            markers=True,
            title="Current Cost vs Next-Month Forecast",
            text="Cost (₹)",
            template="plotly_dark"
        )
        fig_forecast.update_traces(line=dict(width=4), texttemplate="₹%{y:,.0f}", textposition="top center")
        fig_forecast.update_layout(xaxis_title="Forecast Period", yaxis_title="Estimated Cost (₹)")
        st.plotly_chart(fig_forecast, width="stretch")

        # Scenario range chart for selected growth assumptions
        st.subheader("Forecast Scenarios")
        scenario_rates = [-5, 0, growth_rate, min(growth_rate + 5, 40), min(growth_rate + 10, 50)]
        scenario_rates = sorted(set(scenario_rates))
        scenario_data = pd.DataFrame({
            "Monthly Growth (%)": scenario_rates,
            "Estimated Next-Month Cost (₹)": [total_cost * (1 + rate / 100) for rate in scenario_rates]
        })
        scenario_fig = px.area(
            scenario_data, x="Monthly Growth (%)", y="Estimated Next-Month Cost (₹)",
            markers=True, title="Cost Sensitivity to Growth Rate", template="plotly_dark",
            color_discrete_sequence=["#38bdf8"]
        )
        scenario_fig.update_traces(line=dict(width=3))
        st.plotly_chart(scenario_fig, use_container_width=True)

        st.caption(
            "Forecast is a simple estimate based on your selected growth rate, "
            "not a prediction from historical billing data."
        )
    else:
        st.warning(
            "The monthly_cost column was not found in the analysis results."
        )


if page == 'Cost Analysis':
    # -------------------------------
    # What-If Savings Simulator
    # -------------------------------

    st.subheader("What-If Savings Simulator")

    if "monthly_cost" in results.columns:
        total_cost = pd.to_numeric(
            results["monthly_cost"], errors="coerce"
        ).fillna(0).sum()

        savings_percent = st.slider(
            "Potential cost reduction (%)",
            min_value=0,
            max_value=50,
            value=20,
            key="what_if_savings_percent"
        )

        potential_savings = total_cost * savings_percent / 100
        optimized_cost = total_cost - potential_savings

        col1, col2, col3 = st.columns(3)

        col1.metric("Current Cost", f"₹{total_cost:,.0f}")
        col2.metric("Potential Savings", f"₹{potential_savings:,.0f}")
        col3.metric("Cost After Optimization", f"₹{optimized_cost:,.0f}")

        st.caption(
            "Illustrative estimate only. Actual savings depend on "
            "resource usage and cloud pricing."
        )

    # Cloud Provider Cost Comparison
    st.subheader("Cloud Provider Cost Comparison")

    st.write(
        "Compare illustrative cloud costs using the same estimated workload."
    )

    provider_rates = {
        "AWS": 1.00,
        "Microsoft Azure": 0.95,
        "Google Cloud": 0.90
    }

    base_cost = float(total_cost)

    comparison_data = pd.DataFrame([
        {
            "Provider": provider,
            "Estimated Monthly Cost (₹)": base_cost * rate
        }
        for provider, rate in provider_rates.items()
    ])

    comparison_data["Estimated Annual Cost (₹)"] = (
        comparison_data["Estimated Monthly Cost (₹)"] * 12
    )

    st.dataframe(
        comparison_data.round(2),
        use_container_width=True,
        hide_index=True
    )

    fig_providers = px.pie(
        comparison_data,
        names="Provider",
        values="Estimated Monthly Cost (₹)",
        hole=0.55,
        title="Cloud Provider Cost Share (Illustrative Estimates)",
        template="plotly_dark"
    )
    fig_providers.update_traces(textposition="inside", textinfo="label+percent", hole=0.55)
    st.plotly_chart(fig_providers, width="stretch")

    # Waterfall-style view of current cost, savings, and optimized cost
    st.subheader("Cost Optimization Waterfall")
    waterfall = px.bar(
        pd.DataFrame({
            "Step": ["Current Cost", "Potential Savings", "Optimized Cost"],
            "Amount (₹)": [total_cost, -potential_savings, optimized_cost],
            "Type": ["Baseline", "Savings", "After Optimization"]
        }),
        x="Step", y="Amount (₹)", color="Type",
        title="Current Cost → Savings → Optimized Cost", template="plotly_dark",
        color_discrete_map={"Baseline": "#60a5fa", "Savings": "#34d399", "After Optimization": "#818cf8"}
    )
    waterfall.update_layout(showlegend=False)
    st.plotly_chart(waterfall, use_container_width=True)

    cheapest_provider = comparison_data.loc[
        comparison_data["Estimated Monthly Cost (₹)"].idxmin()
    ]

    st.success(
        f"Lowest illustrative estimate: {cheapest_provider['Provider']} "
        f"at ₹{cheapest_provider['Estimated Monthly Cost (₹)']:,.0f} per month."
    )

    st.caption(
        "Demo estimates only. These multipliers are illustrative, "
        "not actual AWS, Azure, or Google Cloud prices."
    )

    # Cloud Budget Alert System
    st.subheader("Cloud Budget Alert System")

    if "monthly_cost" in results.columns:
        total_cost = pd.to_numeric(
            results["monthly_cost"], errors="coerce"
        ).fillna(0).sum()

        monthly_budget = st.number_input(
            "Set your monthly cloud budget (₹)",
            min_value=1000,
            max_value=10000000,
            value=60000,
            step=1000,
            key="monthly_cloud_budget"
        )

        budget_used = (total_cost / monthly_budget) * 100

        col1, col2 = st.columns(2)
        col1.metric("Monthly Budget", f"₹{monthly_budget:,.0f}")
        col2.metric("Current Sample Cost", f"₹{total_cost:,.0f}")

        st.progress(min(budget_used / 100, 1.0))
        st.write(f"Budget used: **{budget_used:.1f}%**")

        if total_cost > monthly_budget:
            st.error("Budget exceeded! Review your cloud resources.")
        elif budget_used >= 80:
            st.warning("Budget alert: spending has reached at least 80%.")
        else:
            st.success("Spending is currently within your budget.")

        st.caption(
            "This alert uses the costs in your uploaded CSV. "
            "It is not connected to live cloud billing."
        )


if page == 'Optimization Recommendations':
    # Interactive Optimization Recommendations
    st.subheader("Interactive Optimization Recommendations")

    if "recommendation" in results.columns:
        recommendations = results.copy()

        def get_priority(row):
            rec = str(row.get("recommendation", "")).lower()
            if "idle" in rec:
                return "High"
            elif "downsiz" in rec:
                return "Medium"
            return "Low"

        recommendations["Priority"] = recommendations.apply(
            get_priority, axis=1
        )

        if "estimated_savings" in recommendations.columns:
            recommendations["estimated_savings"] = pd.to_numeric(
                recommendations["estimated_savings"], errors="coerce"
            ).fillna(0)

        priority_filter = st.multiselect(
            "Filter by priority",
            options=["High", "Medium", "Low"],
            default=["High", "Medium", "Low"],
            key="recommendation_priority_filter"
        )

        filtered_recommendations = recommendations[
            recommendations["Priority"].isin(priority_filter)
        ]

        display_columns = [
            col for col in [
                "resource_id",
                "resource_type",
                "recommendation",
                "Priority",
                "estimated_savings"
            ]
            if col in filtered_recommendations.columns
        ]

        st.dataframe(
            filtered_recommendations[display_columns],
            width="stretch",
            hide_index=True
        )

        st.subheader("Recommendation Priority Mix")
        priority_counts = filtered_recommendations["Priority"].value_counts().reindex(["High", "Medium", "Low"], fill_value=0).reset_index()
        priority_counts.columns = ["Priority", "Resource Count"]
        priority_polar = px.line_polar(
            priority_counts, r="Resource Count", theta="Priority", line_close=True,
            title="Resources by Priority", template="plotly_dark",
            color_discrete_sequence=["#38bdf8"]
        )
        priority_polar.update_traces(fill="toself")
        st.plotly_chart(priority_polar, use_container_width=True)

        if "estimated_savings" in filtered_recommendations.columns:
            total_recommended_savings = filtered_recommendations[
                "estimated_savings"
            ].sum()

            st.metric(
                "Estimated Savings for Filtered Resources",
                f"₹{total_recommended_savings:,.0f}"
            )

        st.caption(
            "Recommendations are based on sample utilization rules. "
            "Review resources before making changes."
        )
    else:
        st.warning("No recommendation column was found in the analysis results.")


if page == 'Reports':
    # PDF Report Download
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    )
    from reportlab.lib.styles import getSampleStyleSheet

    st.subheader("Download PDF Report")

    def create_pdf_report():
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(
            Paragraph("Cloud FinOps Optimization Report", styles["Title"])
        )
        elements.append(Spacer(1, 16))
        elements.append(
            Paragraph(
                "Summary of cloud resource costs and optimization analysis.",
                styles["Normal"]
            )
        )
        elements.append(Spacer(1, 16))

        pdf_data = [
            ["Resource ID", "Monthly Cost (Rs.)", "Recommendation"]
        ]

        for _, row in results.iterrows():
            pdf_data.append([
                str(row.get("resource_id", "")),
                f'{float(row.get("monthly_cost", 0)):,.0f}',
                str(row.get("recommendation", "Review"))
            ])

        table = Table(pdf_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243b53")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.whitesmoke]),
        ]))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    pdf_bytes = create_pdf_report()

    st.download_button(
        label="Download PDF Report",
        data=pdf_bytes,
        file_name="cloud_finops_report.pdf",
        mime="application/pdf"
    )


if page == 'Notifications & Approvals':
    from approval_system import (
        load_approvals,
        request_approval,
        update_approval
    )


    # Resource Waste Notifications
    st.header("🔔 Notifications")

    if "notifications" not in st.session_state:
        st.session_state["notifications"] = []

    if st.button("Generate Demo Notifications"):
        demo_data = get_aws_resources()
        waste_data = detect_resource_waste(demo_data)

        for _, resource in waste_data.iterrows():
            notification = create_notification(
                resource_id=resource["resource_id"],
                message=(
                    f"Resource {resource['resource_id']} may need attention."
                ),
            )
            st.session_state["notifications"].append(notification)

        st.success("Demo notifications generated.")

    notifications = st.session_state["notifications"]

    if notifications:
        st.subheader("Notification History")

        unread_count = sum(
            item["status"] == "Unread" for item in notifications
        )
        st.metric("Unread Notifications", unread_count)

        st.dataframe(notifications, use_container_width=True)

        if unread_count > 0 and st.button("Mark All as Read"):
            for item in notifications:
                item["status"] = "Read"
            st.session_state["notifications"] = notifications
            st.rerun()

        if st.button("Clear Notification History"):
            st.session_state["notifications"] = []
            st.rerun()
    else:
        st.info("No notifications yet. Generate demo notifications to begin.")

    if user_role in ("Admin", "Manager"):
        st.header("🔔 Manager Approval Center")

    if "notification_seen" not in st.session_state:
        st.session_state["notification_seen"] = False

    if st.button("Check Resource Notifications"):
        demo_data = get_aws_resources()
        waste_data = detect_resource_waste(demo_data)

        if not waste_data.empty:
            st.warning(
                f"⚠️ {len(waste_data)} resources need attention."
            )
            st.dataframe(waste_data, use_container_width=True)
        else:
            st.success("No resource waste detected.")

    if "approval_user" not in st.session_state:
        st.session_state["approval_user"] = ""

    st.session_state["approval_user"] = st.text_input(
        "Demo owner username",
        value=st.session_state["approval_user"],
        key="approval_owner_input"
    )

    if st.button("Create Demo Approval Request"):
        demo_id = "i-demo001"
        request = request_approval(
            resource_id=demo_id,
            resource_type="EC2",
            reason="Low CPU usage detected. Review before downsizing."
        )
        st.success(f"Created request: {request['request_id']}")

    approvals = load_approvals()
    st.subheader("Approval Requests")

    if approvals:
        st.dataframe(approvals, use_container_width=True)
        pending = [item for item in approvals if item["status"] == "Pending"]

        if pending and user_role in ("Admin", "Manager"):
            selected_id = st.selectbox(
                "Select pending request",
                [item["request_id"] for item in pending],
                key="pending_approval_id",
            )
            decision = st.radio(
                "Owner decision",
                ["Approved", "Rejected"],
                horizontal=True,
                key="approval_decision",
            )
            response = st.text_input("Owner comments", key="approval_comments")
            if st.button("Submit Owner Decision"):
                success = update_approval(selected_id, decision, response)
                if success:
                    st.success("Decision saved.")
                    st.rerun()
                else:
                    st.warning("This request is no longer pending.")
    else:
        st.info("No approval requests yet.")

    st.caption(
        "Demo only: this interface does not send real notifications "
        "or delete cloud resources."
    )

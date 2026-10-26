
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from modules.business_selector import select_business
from modules.sales_forecasting import forecast_sales


st.set_page_config(
    page_title="Sales Forecasting | BizAdvisor AI",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Sales Forecasting")
st.caption(
    "Forecast future daily revenue using historical sales data "
    "and compare a Random Forest model against a simple baseline."
)

st.info(
    "Forecasts are estimates, not guarantees. Their usefulness "
    "depends on the completeness and quality of your sales history."
)

# --------------------------------------------------
# 1. SHARED BUSINESS SELECTION
# --------------------------------------------------

business = select_business()

if business is None:
    st.info(
        "Choose a business from the sidebar to generate its sales forecast."
    )
    st.stop()

business_id = int(business["business_id"])
business_name = business["business_name"]
currency = business.get("currency") or "INR"

st.caption(f"Forecasting business: **{business_name}**")

# --------------------------------------------------
# 2. CONFIGURE THE FORECAST
# --------------------------------------------------

st.subheader("Forecast Settings")

forecast_days = st.selectbox(
    "Forecast horizon",
    options=[7, 14, 30],
    index=0,
    format_func=lambda days: f"{days} days",
    key="forecast_horizon",
)

if st.button(
    "Generate Sales Forecast",
    type="primary",
    key="generate_sales_forecast",
):
    try:
        with st.spinner("Preparing data and training the model..."):
            result = forecast_sales(
                business_id=business_id,
                forecast_days=forecast_days,
            )

            st.session_state["sales_forecast_result"] = result
            st.session_state["sales_forecast_business"] = business_id
            st.session_state["sales_forecast_days"] = forecast_days

    except (ValueError, KeyError) as error:
        st.error(f"Could not generate the forecast: {error}")
        st.stop()

    except Exception as error:
        st.error(
            "An unexpected error occurred while generating "
            f"the forecast: {error}"
        )
        st.stop()

# --------------------------------------------------
# 3. DISPLAY RESULTS FOR THE CURRENT BUSINESS
# --------------------------------------------------

result = st.session_state.get("sales_forecast_result")
result_business = st.session_state.get("sales_forecast_business")
result_days = st.session_state.get("sales_forecast_days")

# Never show a forecast generated for a different business or horizon.
if (
    result is not None
    and result_business == business_id
    and result_days == forecast_days
):

    st.divider()

    # ----------------------------------------------
    # 4. HANDLE INSUFFICIENT HISTORICAL DATA
    # ----------------------------------------------

    if result.get("status") == "insufficient_data":
        st.warning(result.get("message", "There is not enough data to forecast."))

        historical = result.get("historical", pd.DataFrame())

        if isinstance(historical, pd.DataFrame) and not historical.empty:
            st.subheader("Available Historical Data")

            if "revenue" in historical.columns:
                historical_revenue = pd.to_numeric(
                    historical["revenue"],
                    errors="coerce",
                ).fillna(0).sum()

                st.metric(
                    "Recorded Revenue",
                    f"{currency} {historical_revenue:,.2f}",
                )

            st.metric(
                "Recorded Calendar Days",
                len(historical),
            )

            if {"date", "revenue"}.issubset(historical.columns):
                chart = go.Figure()

                chart.add_trace(
                    go.Scatter(
                        x=historical["date"],
                        y=historical["revenue"],
                        mode="lines+markers",
                        name="Historical Revenue",
                    )
                )

                chart.update_layout(
                    title="Historical Daily Revenue",
                    xaxis_title="Date",
                    yaxis_title=f"Revenue ({currency})",
                    hovermode="x unified",
                )

                st.plotly_chart(chart, use_container_width=True)

        st.info(
            "Import more historical sales records and try again. "
            "The current model requires at least 30 calendar days "
            "of history, with additional usable observations after "
            "historical features are prepared."
        )

    # ----------------------------------------------
    # 5. DISPLAY A SUCCESSFUL FORECAST
    # ----------------------------------------------

    else:
        st.success(
            result.get("message", "Forecast generated successfully.")
        )

        historical = result.get("historical", pd.DataFrame()).copy()
        forecast = result.get("forecast", pd.DataFrame()).copy()

        required_forecast_columns = {
            "date",
            "baseline",
            "random_forest",
        }

        if (
            not isinstance(historical, pd.DataFrame)
            or historical.empty
            or "revenue" not in historical.columns
        ):
            st.warning("Historical revenue data is missing or incomplete.")
            st.stop()

        if (
            not isinstance(forecast, pd.DataFrame)
            or forecast.empty
            or not required_forecast_columns.issubset(forecast.columns)
        ):
            st.warning("Forecast results are missing expected columns.")
            st.stop()

        historical["revenue"] = pd.to_numeric(
            historical["revenue"],
            errors="coerce",
        ).fillna(0)

        forecast["random_forest"] = pd.to_numeric(
            forecast["random_forest"],
            errors="coerce",
        ).fillna(0)

        forecast["baseline"] = pd.to_numeric(
            forecast["baseline"],
            errors="coerce",
        ).fillna(0)

        # ------------------------------------------
        # 6. FORECAST SUMMARY
        # ------------------------------------------

        st.subheader("Forecast Summary")

        historical_revenue = float(historical["revenue"].sum())
        predicted_revenue = float(forecast["random_forest"].sum())
        baseline_revenue = float(forecast["baseline"].sum())

        metric_columns = st.columns(3)

        metric_columns[0].metric(
            "Historical Revenue",
            f"{currency} {historical_revenue:,.2f}",
        )

        metric_columns[1].metric(
            f"Forecast Revenue ({forecast_days} days)",
            f"{currency} {predicted_revenue:,.2f}",
        )

        metric_columns[2].metric(
            "Baseline Forecast",
            f"{currency} {baseline_revenue:,.2f}",
        )

        # ------------------------------------------
        # 7. HISTORICAL AND FORECAST CHART
        # ------------------------------------------

        st.subheader("Historical Sales vs. Forecast")

        chart = go.Figure()

        chart.add_trace(
            go.Scatter(
                x=historical["date"],
                y=historical["revenue"],
                mode="lines",
                name="Historical Revenue",
            )
        )

        chart.add_trace(
            go.Scatter(
                x=forecast["date"],
                y=forecast["random_forest"],
                mode="lines+markers",
                name="Random Forest Forecast",
                line=dict(dash="dash"),
            )
        )

        chart.add_trace(
            go.Scatter(
                x=forecast["date"],
                y=forecast["baseline"],
                mode="lines+markers",
                name="Baseline Forecast",
                line=dict(dash="dot"),
            )
        )

        chart.update_layout(
            title="Daily Revenue Forecast",
            xaxis_title="Date",
            yaxis_title=f"Revenue ({currency})",
            hovermode="x unified",
            legend_title="Series",
        )

        st.plotly_chart(chart, use_container_width=True)

        # ------------------------------------------
        # 8. MODEL EVALUATION
        # ------------------------------------------

        st.subheader("Model Evaluation")

        baseline_mae = result.get("baseline_mae")
        random_forest_mae = result.get("random_forest_mae")

        evaluation_columns = st.columns(2)

        evaluation_columns[0].metric(
            "Baseline MAE",
            (
                f"{currency} {baseline_mae:,.2f}"
                if baseline_mae is not None
                else "Unavailable"
            ),
        )

        evaluation_columns[1].metric(
            "Random Forest MAE",
            (
                f"{currency} {random_forest_mae:,.2f}"
                if random_forest_mae is not None
                else "Unavailable"
            ),
        )

        if (
            baseline_mae is not None
            and random_forest_mae is not None
        ):
            if random_forest_mae < baseline_mae:
                st.success(
                    "Random Forest had a lower MAE than the baseline "
                    "on the historical evaluation period."
                )
            elif random_forest_mae > baseline_mae:
                st.warning(
                    "The baseline had a lower MAE than Random Forest "
                    "on the historical evaluation period. The simpler "
                    "baseline may be preferable for now."
                )
            else:
                st.info(
                    "Both approaches had the same MAE on the "
                    "historical evaluation period."
                )

        st.caption(
            "MAE (Mean Absolute Error) measures the average absolute "
            "difference between predicted and actual daily revenue. "
            "Lower is better on the evaluated period, but historical "
            "performance does not guarantee future accuracy."
        )

        # ------------------------------------------
        # 9. FORECAST TABLE AND DOWNLOAD
        # ------------------------------------------

        st.subheader("Daily Forecast Details")

        display_forecast = forecast.copy()

        display_forecast["date"] = pd.to_datetime(
            display_forecast["date"],
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

        display_forecast = display_forecast.rename(
            columns={
                "date": "Date",
                "baseline": f"Baseline Revenue ({currency})",
                "random_forest": f"Random Forest Revenue ({currency})",
            }
        )

        st.dataframe(
            display_forecast,
            use_container_width=True,
            hide_index=True,
        )

        csv_data = display_forecast.to_csv(
            index=False,
        ).encode("utf-8")

        st.download_button(
            label="Download Forecast as CSV",
            data=csv_data,
            file_name=f"bizadvisor_sales_forecast_{business_id}.csv",
            mime="text/csv",
        )

        st.warning(
            "This initial model assumes missing dates between "
            "recorded transactions represent zero sales. If your "
            "records are incomplete, forecasts may be misleading. "
            "Returns, holidays, stock availability and business "
            "changes are not yet modeled separately."
        )

elif result is not None:
    st.info(
        "The saved forecast does not match the currently selected "
        "business or forecast horizon. Click **Generate Sales Forecast** "
        "to calculate the correct forecast."
    )

else:
    st.info(
        "Choose a forecast horizon, then click "
        "**Generate Sales Forecast** to begin."
    )


import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from modules.storage import get_sales_data


def prepare_daily_sales(business_id, start_date=None, end_date=None):
    """
    Convert transaction records into daily sales data.

    Missing dates between the first and last recorded transactions
    are filled with zero revenue and zero transactions.
    """

    if start_date is not None and end_date is not None:
        if pd.Timestamp(start_date) > pd.Timestamp(end_date):
            raise ValueError("Start date cannot be after end date.")

    sales = get_sales_data(business_id).copy()

    if sales.empty:
        return pd.DataFrame(
            columns=["date", "revenue", "transactions"]
        )

    sales["transaction_date"] = pd.to_datetime(
        sales["transaction_date"],
        errors="coerce",
    )

    sales["total_amount"] = pd.to_numeric(
        sales["total_amount"],
        errors="coerce",
    )

    sales = sales.dropna(
        subset=["transaction_date", "total_amount"]
    ).copy()

    if start_date is not None:
        sales = sales[
            sales["transaction_date"] >= pd.Timestamp(start_date)
        ]

    if end_date is not None:
        sales = sales[
            sales["transaction_date"]
            < pd.Timestamp(end_date) + pd.Timedelta(days=1)
        ]

    if sales.empty:
        return pd.DataFrame(
            columns=["date", "revenue", "transactions"]
        )

    # Group transactions by calendar day.
    sales["date"] = sales["transaction_date"].dt.normalize()

    daily = (
        sales.groupby("date")
        .agg(
            revenue=("total_amount", "sum"),
            transactions=("transaction_id", "count"),
        )
        .sort_index()
    )

    # Fill missing calendar days between recorded transactions.
    all_dates = pd.date_range(
        start=daily.index.min(),
        end=daily.index.max(),
        freq="D",
    )

    daily = daily.reindex(all_dates, fill_value=0)
    daily.index.name = "date"
    daily = daily.reset_index()

    daily["revenue"] = daily["revenue"].astype(float)
    daily["transactions"] = daily["transactions"].astype(int)

    return daily


def _empty_forecast():
    """Return an empty forecast DataFrame with consistent columns."""

    return pd.DataFrame(
        columns=["date", "baseline", "random_forest"]
    )


def forecast_sales(business_id, forecast_days=7):
    """
    Forecast daily revenue using a recent-average baseline
    and a Random Forest regression model.

    The model is evaluated on later observations using a
    chronological split instead of random shuffling.
    """

    if (
        not isinstance(forecast_days, int)
        or isinstance(forecast_days, bool)
    ):
        raise ValueError("Forecast days must be a whole number.")

    if not 1 <= forecast_days <= 30:
        raise ValueError("Forecast days must be between 1 and 30.")

    daily = prepare_daily_sales(business_id)

    # Require sufficient calendar history.
    if len(daily) < 30:
        return {
            "status": "insufficient_data",
            "message": (
                "At least 30 calendar days of sales history are "
                "required for this initial model. More history "
                "is preferable for reliable forecasting."
            ),
            "historical": daily,
            "forecast": _empty_forecast(),
            "baseline_mae": None,
            "random_forest_mae": None,
        }

    daily = daily.copy()
    daily = daily.sort_values("date").reset_index(drop=True)

    # This initial model forecasts non-negative sales revenue.
    # Refunds and returns need separate treatment.
    daily["revenue"] = daily["revenue"].clip(lower=0)

    def make_features(frame):
        """Build calendar and historical-revenue features."""

        dates = pd.to_datetime(frame["date"])
        features = pd.DataFrame(index=frame.index)

        # Calendar features.
        features["day_of_week"] = dates.dt.day_of_week
        features["day_of_month"] = dates.dt.day
        features["month"] = dates.dt.month
        features["day_of_year"] = dates.dt.day_of_year

        # Lag features use previous days only.
        for lag in (1, 2, 7, 14):
            features[f"lag_{lag}"] = (
                frame["revenue"].shift(lag)
            )

        # Previous seven-day mean; current-day revenue is excluded.
        features["rolling_mean_7"] = (
            frame["revenue"]
            .shift(1)
            .rolling(window=7)
            .mean()
        )

        return features

    features = make_features(daily)
    target = daily["revenue"]

    # Remove rows without enough historical data for their features.
    valid_rows = features.notna().all(axis=1)
    features = features.loc[valid_rows]
    target = target.loc[valid_rows]

    if len(features) < 14:
        return {
            "status": "insufficient_data",
            "message": (
                "Not enough usable observations remain after "
                "creating historical features. Add more sales history."
            ),
            "historical": daily,
            "forecast": _empty_forecast(),
            "baseline_mae": None,
            "random_forest_mae": None,
        }

    # Chronological holdout: train on earlier records and evaluate
    # on the latest records.
    split_index = int(len(features) * 0.8)
    split_index = max(1, min(split_index, len(features) - 1))

    X_train = features.iloc[:split_index]
    X_test = features.iloc[split_index:]

    y_train = target.iloc[:split_index]
    y_test = target.iloc[split_index:]

    # Baseline prediction: average of the last seven training days.
    baseline_value = float(y_train.tail(7).mean())

    baseline_predictions = np.full(
        len(y_test),
        baseline_value,
        dtype=float,
    )

    # Train the Random Forest model.
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    model_predictions = np.clip(
        model.predict(X_test),
        0,
        None,
    )

    # Evaluate both approaches using Mean Absolute Error (MAE).
    baseline_mae = float(
        mean_absolute_error(y_test, baseline_predictions)
    )

    random_forest_mae = float(
        mean_absolute_error(y_test, model_predictions)
    )

    # Generate future forecasts recursively.
    # Later predictions use earlier predicted revenue as lag values.
    history = daily[["date", "revenue"]].copy()
    future_rows = []

    for _ in range(forecast_days):
        next_date = (
            pd.Timestamp(history["date"].iloc[-1])
            + pd.Timedelta(days=1)
        )

        past_revenue = history["revenue"].astype(float)

        row = {
            "day_of_week": next_date.day_of_week,
            "day_of_month": next_date.day,
            "month": next_date.month,
            "day_of_year": next_date.day_of_year,
            "lag_1": float(past_revenue.iloc[-1]),
            "lag_2": float(past_revenue.iloc[-2]),
            "lag_7": float(past_revenue.iloc[-7]),
            "lag_14": float(past_revenue.iloc[-14]),
            "rolling_mean_7": float(past_revenue.tail(7).mean()),
        }

        next_features = pd.DataFrame(
            [row],
            columns=features.columns,
        )

        predicted_revenue = float(
            model.predict(next_features)[0]
        )
        predicted_revenue = max(0.0, predicted_revenue)

        # Calculate the baseline for this forecast day.
        future_baseline = float(past_revenue.tail(7).mean())

        future_rows.append(
            {
                "date": next_date,
                "baseline": future_baseline,
                "random_forest": predicted_revenue,
            }
        )

        # Add the prediction to history for the next forecast step.
        history = pd.concat(
            [
                history,
                pd.DataFrame(
                    [
                        {
                            "date": next_date,
                            "revenue": predicted_revenue,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    forecast = pd.DataFrame(future_rows)

    return {
        "status": "success",
        "message": (
            "Forecast generated. Review the evaluation errors "
            "before relying on the predictions."
        ),
        "historical": daily,
        "forecast": forecast,
        "baseline_mae": baseline_mae,
        "random_forest_mae": random_forest_mae,
    }

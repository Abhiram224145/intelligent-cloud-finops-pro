
import pandas as pd
from sklearn.ensemble import IsolationForest


def analyze_resources(data):
    data = data.copy()

    required_columns = [
        "resource_id",
        "resource_type",
        "cpu_usage",
        "memory_usage",
        "monthly_cost",
    ]

    for column in required_columns:
        if column not in data.columns:
            raise ValueError(f"Missing column: {column}")

    numeric_columns = [
        "cpu_usage",
        "memory_usage",
        "monthly_cost",
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column], errors="raise"
        )

    if data[numeric_columns].isna().any().any():
        raise ValueError("Numeric values cannot be empty.")

    if (
        (data["cpu_usage"] < 0).any()
        or (data["cpu_usage"] > 100).any()
        or (data["memory_usage"] < 0).any()
        or (data["memory_usage"] > 100).any()
        or (data["monthly_cost"] < 0).any()
    ):
        raise ValueError("Invalid resource usage or cost.")

    data["recommendation"] = "Normal usage"

    idle = (
        (data["cpu_usage"] < 10)
        & (data["memory_usage"] < 20)
    )

    oversized = (
        (data["cpu_usage"] < 30)
        & (data["memory_usage"] < 30)
        & ~idle
    )

    data.loc[idle, "recommendation"] = (
        "Review idle resource"
    )

    data.loc[oversized, "recommendation"] = (
        "Consider downsizing"
    )

    if len(data) >= 5:
        model = IsolationForest(
            contamination=0.15,
            random_state=42
        )

        features = data[numeric_columns]

        data["anomaly"] = (
            model.fit_predict(features) == -1
        )
    else:
        data["anomaly"] = False

    data["estimated_savings"] = 0.0

    data.loc[idle, "estimated_savings"] = (
        data.loc[idle, "monthly_cost"] * 0.50
    )

    data.loc[oversized, "estimated_savings"] = (
        data.loc[oversized, "monthly_cost"] * 0.20
    )

    data["estimated_savings"] = (
        data["estimated_savings"].round(2)
    )

    return data

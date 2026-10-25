import pandas as pd


def get_aws_resources():
    """Return mock AWS resources for local testing."""

    data = [
        {
            "resource_id": "i-demo001",
            "resource_type": "EC2",
            "cpu_usage": 5,
            "memory_usage": 15,
            "monthly_cost": 1200,
            "resource_status": "Underutilized",
        },
        {
            "resource_id": "i-demo002",
            "resource_type": "EC2",
            "cpu_usage": 65,
            "memory_usage": 70,
            "monthly_cost": 2500,
            "resource_status": "Normal",
        },
        {
            "resource_id": "vol-demo001",
            "resource_type": "EBS",
            "cpu_usage": 0,
            "memory_usage": 0,
            "monthly_cost": 300,
            "resource_status": "Unused",
        },
    ]

    return pd.DataFrame(data)
def detect_resource_waste(df):
    """Detect potentially wasted demo resources."""

    waste = df[
        (df["resource_status"] == "Unused")
        | (
            (df["resource_type"] == "EC2")
            & (df["cpu_usage"] < 10)
        )
    ].copy()

    waste["recommendation"] = waste["resource_status"].apply(
        lambda status: (
            "Review before deleting"
            if status == "Unused"
            else "Consider downsizing"
        )
    )

    return waste
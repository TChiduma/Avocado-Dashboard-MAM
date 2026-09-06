import pandas as pd

def load_data(csv_path: str = "avocado.csv") -> pd.DataFrame:
    """
    Load the avocado dataset and perform basic cleaning.
    Assumes columns: date, average_price, total_volume, type, region.
    """
    df = pd.read_csv(csv_path)

    # Parse date column to datetime (day-first format)
    df["date"] = pd.to_datetime(df["date"], dayfirst=True)

    return df
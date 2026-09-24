import streamlit as st
import pandas as pd
from pathlib import Path

# Mapping of all 50 states + District of Columbia to 2-letter postal abbreviations
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


def resolve_data_path() -> Path:
    """Finds the dataset path regardless of whether app is run locally or on Cloud."""
    base_dir = Path(__file__).resolve().parent.parent
    possible_paths = [
        base_dir / "data" / "Provisional_Natality_2025_CDC1.csv",
        base_dir / "Provisional_Natality_2025_CDC1.csv",
        Path("Provisional_Natality_2025_CDC1.csv"),
        Path("data/Provisional_Natality_2025_CDC1.csv")
    ]
    for p in possible_paths:
        if p.exists():
            return p
    raise FileNotFoundError("Provisional_Natality_2025_CDC1.csv could not be located.")


def validate_dataframe(df: pd.DataFrame) -> None:
    """Performs validation assertions against expected data contracts."""
    required_cols = {"state_of_residence", "month", "month_code", "year_code", "sex_of_infant", "births"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    if (df["births"] < 0).any():
        raise ValueError("Dataset contains negative birth counts.")

    if df["births"].isnull().any():
        raise ValueError("Dataset contains missing birth count values.")

    missing_states = set(df["state_of_residence"]) - set(US_STATE_TO_ABBREV.keys())
    if missing_states:
        raise ValueError(f"Unmapped geography entities encountered: {missing_states}")


@st.cache_data(show_spinner=True)
def load_natality_data() -> pd.DataFrame:
    """Loads, validates, and enhances the CDC Provisional Natality data."""
    file_path = resolve_data_path()
    df = pd.read_csv(file_path)

    # Perform structural checks
    validate_dataframe(df)

    # Attach postal codes for mapping
    df["state_abbrev"] = df["state_of_residence"].map(US_STATE_TO_ABBREV)

    # Ensure chronological month ordering
    df["month"] = pd.Categorical(df["month"], categories=ORDERED_MONTHS, ordered=True)
    df = df.sort_values(["state_of_residence", "month_code", "sex_of_infant"]).reset_index(drop=True)

    return df

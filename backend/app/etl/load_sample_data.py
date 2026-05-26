import pandas as pd


FILE_PATH = "data/sample_data.xlsx"


def standardize_columns(df):
    """
    Normalize raw Excel column names into canonical schema.
    """

    df = df.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    rename_map = {
        "caseid": "case",
        "case_id": "case",
        "ticket": "case",
        "incident": "case",

        "assigned_to": "assigned_to",
        "assignment_group": "assignment_group",
        "status": "status",

        "start": "start",
        "end": "end",
    }

    df = df.rename(columns=rename_map)

    # Safety check
    if "case" not in df.columns:
        raise ValueError(f"'case' column not found. Available columns: {df.columns}")

    return df
    
    
def load_excel():
    df = pd.read_excel(FILE_PATH)
    df = standardize_columns(df)
    
    print(df.head())
    print(df.columns.tolist())
    print(df.dtypes)

    # save interim normalized CSV
    df.to_csv("data/normalized_sample.csv", index=False)
    
    return df


if __name__ == "__main__":
    load_excel()
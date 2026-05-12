import pandas as pd

from reader import load_excel, load_csv
from preprocessing import normalize_excel, normalize_csv


def merge_sources(df_excel: pd.DataFrame, df_csv: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(df_excel, df_csv, on="id_cobranca", how="outer", indicator=True)
    df["fonte"] = df["_merge"].map({
        "both": "BOTH",
        "left_only": "EXCEL_ONLY",
        "right_only": "CSV_ONLY",
    })
    return df.drop(columns="_merge")


if __name__ == "__main__":
    df_excel = load_excel("data/cobrancas_internas.xlsx")
    df_csv = load_csv("data/cobrancas_convenio.csv")

    df_excel = normalize_excel(df_excel)
    df_csv = normalize_csv(df_csv)
    df = merge_sources(df_excel, df_csv)

    print(df.shape)
    print(df["fonte"].value_counts())


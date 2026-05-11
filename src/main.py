import pandas as pd
from unidecode import unidecode


def load_excel(path: str) -> pd.DataFrame:
    return pd.read_excel(path)


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", encoding="utf-8")


def normalize_name(name: str) -> str:
    return unidecode(name).upper()


def normalize_excel_names(df: pd.DataFrame) -> pd.DataFrame:
    df["paciente_norm"] = df["paciente"].apply(normalize_name)
    return df


if __name__ == "__main__":
    df_excel = load_excel("data/cobrancas_internas.xlsx")
    df_csv = load_csv("data/cobrancas_convenio.csv")

    df_excel = normalize_excel_names(df_excel)

    print(df_excel[["paciente", "paciente_norm"]])

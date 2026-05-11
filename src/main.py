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


def invert_name(name: str) -> str:
    parts = name.split(", ", 1)
    return f"{parts[1]} {parts[0]}" if len(parts) == 2 else name


def normalize_csv_names(df: pd.DataFrame) -> pd.DataFrame:
    df["nome_beneficiario_norm"] = df["nome_beneficiario"].apply(
        lambda n: normalize_name(invert_name(n))
    )
    return df


if __name__ == "__main__":
    df_excel = load_excel("data/cobrancas_internas.xlsx")
    df_csv = load_csv("data/cobrancas_convenio.csv")

    df_excel = normalize_excel_names(df_excel)
    df_csv = normalize_csv_names(df_csv)

    print(df_excel[["paciente", "paciente_norm"]])
    print(df_csv[["nome_beneficiario", "nome_beneficiario_norm"]].head())

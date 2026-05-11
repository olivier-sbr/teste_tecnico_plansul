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


def normalize_dates(df_excel: pd.DataFrame, df_csv: pd.DataFrame):
    df_excel["data_atendimento"] = pd.to_datetime(df_excel["data_atendimento"], format="%d/%m/%Y")
    df_csv["dt_realizacao"] = pd.to_datetime(df_csv["dt_realizacao"], format="%Y-%m-%d")
    df_csv["dt_lancamento"] = pd.to_datetime(df_csv["dt_lancamento"], format="%Y-%m-%d")
    return df_excel, df_csv


def normalize_monetary_values(df_csv: pd.DataFrame) -> pd.DataFrame:
    for col in ["vl_servico", "vl_glosa", "vl_liquido"]:
        df_csv[col] = df_csv[col].str.replace(",", ".").astype(float)
    return df_csv


if __name__ == "__main__":
    df_excel = load_excel("data/cobrancas_internas.xlsx")
    df_csv = load_csv("data/cobrancas_convenio.csv")

    df_excel = normalize_excel_names(df_excel)
    df_csv = normalize_csv_names(df_csv)
    df_excel, df_csv = normalize_dates(df_excel, df_csv)
    df_csv = normalize_monetary_values(df_csv)

    print(df_csv[["vl_servico", "vl_glosa", "vl_liquido"]].head())


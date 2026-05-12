import pandas as pd
from unidecode import unidecode


def normalize_name(name: str) -> str:
    return unidecode(name).upper()


def invert_name(name: str) -> str:
    parts = name.split(", ", 1)
    return f"{parts[1]} {parts[0]}" if len(parts) == 2 else name


def normalize_excel(df: pd.DataFrame) -> pd.DataFrame:
    df["paciente_norm"] = df["paciente"].apply(normalize_name)
    df["data_atendimento"] = pd.to_datetime(df["data_atendimento"], format="%d/%m/%Y")
    return df


def normalize_csv(df: pd.DataFrame) -> pd.DataFrame:
    df["nome_beneficiario_norm"] = df["nome_beneficiario"].apply(lambda n: normalize_name(invert_name(n)))
    df["dt_realizacao"] = pd.to_datetime(df["dt_realizacao"], format="%Y-%m-%d")
    df["dt_lancamento"] = pd.to_datetime(df["dt_lancamento"], format="%Y-%m-%d")
    for col in ["vl_servico", "vl_glosa", "vl_liquido"]:
        df[col] = df[col].str.replace(",", ".").astype(float)
    return df

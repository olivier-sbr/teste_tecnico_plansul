import logging

import pandas as pd

logger = logging.getLogger(__name__)


def merge_sources(df_excel: pd.DataFrame, df_csv: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(df_excel, df_csv, on="id_cobranca", how="outer", indicator=True)
    df["fonte"] = df["_merge"].map({
        "both": "BOTH",
        "left_only": "EXCEL_ONLY",
        "right_only": "CSV_ONLY",
    })
    return df.drop(columns="_merge")


def log_single_source_records(df: pd.DataFrame) -> None:
    for _, row in df[df["fonte"] != "BOTH"].iterrows():
        logger.warning(f"cobranca em fonte unica: {row['id_cobranca']} | fonte={row['fonte']}")


def log_value_divergences(df: pd.DataFrame) -> None:
    both = df[df["fonte"] == "BOTH"].copy()
    both["delta"] = abs(both["valor"] - both["vl_liquido"] - both["vl_glosa"])
    divergent = both[both["delta"] > 0.25]
    for _, row in divergent.iterrows():
        logger.warning(
            f"divergencia de valor: {row['id_cobranca']} | "
            f"excel={row['valor']} | csv_liquido={row['vl_liquido']} | "
            f"glosa={row['vl_glosa']} | delta={row['delta']:.2f}"
        )


def log_name_divergences(df: pd.DataFrame) -> None:
    both = df[df["fonte"] == "BOTH"]
    divergent = both[both["paciente_norm"] != both["nome_beneficiario_norm"]]
    for _, row in divergent.iterrows():
        logger.warning(
            f"divergencia de nome: {row['id_cobranca']} | "
            f"excel={row['paciente']} | csv={row['nome_beneficiario']}"
        )


def log_ans_divergences(df: pd.DataFrame) -> None:
    both = df[df["fonte"] == "BOTH"]
    divergent = both[both["registro_ans"] != both["ans"]]
    for _, row in divergent.iterrows():
        logger.warning(
            f"divergencia de ANS: {row['id_cobranca']} | "
            f"excel={row['registro_ans']} | csv={row['ans']}"
        )


def classify_divergences(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    both = df["fonte"] == "BOTH"
    delta = abs(df["valor"] - df["vl_liquido"] - df["vl_glosa"])
    value_diverges = both & (delta > 0.25)
    name_diverges = both & (df["paciente_norm"] != df["nome_beneficiario_norm"])
    ans_diverges = both & (df["registro_ans"] != df["ans"])
    single_source = ~both

    def get_divergences(row):
        issues = []
        if single_source[row.name]:
            issues.append(f"single_source:{row['fonte']}")
        if value_diverges[row.name]:
            issues.append("value_divergent")
        if name_diverges[row.name]:
            issues.append("name_divergent")
        if ans_diverges[row.name]:
            issues.append("ans_divergent")
        return "; ".join(issues)

    df["divergencias"] = df.apply(get_divergences, axis=1)
    return df

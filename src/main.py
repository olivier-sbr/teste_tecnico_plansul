import logging
import pandas as pd

from reader import load_excel, load_csv
from preprocessing import normalize_excel, normalize_csv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def merge_sources(df_excel: pd.DataFrame, df_csv: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(df_excel, df_csv, on="id_cobranca", how="outer", indicator=True)
    df["fonte"] = df["_merge"].map({
        "both": "BOTH",
        "left_only": "EXCEL_ONLY",
        "right_only": "CSV_ONLY",
    })
    return df.drop(columns="_merge")


if __name__ == "__main__":
    logger.info("carregando dados")
    df_excel = load_excel("data/cobrancas_internas.xlsx")
    df_csv = load_csv("data/cobrancas_convenio.csv")
    logger.info(f"excel: {len(df_excel)} linhas | csv: {len(df_csv)} linhas")

    logger.info("normalizando dados")
    df_excel = normalize_excel(df_excel)
    df_csv = normalize_csv(df_csv)

    logger.info("consolidando dataset")
    df = merge_sources(df_excel, df_csv)
    logger.info(f"dataset consolidado: {len(df)} linhas | BOTH={len(df[df.fonte=='BOTH'])} CSV_ONLY={len(df[df.fonte=='CSV_ONLY'])} EXCEL_ONLY={len(df[df.fonte=='EXCEL_ONLY'])}")


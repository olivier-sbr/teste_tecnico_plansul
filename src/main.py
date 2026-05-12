import logging

from reader import load_excel, load_csv
from preprocessing import normalize_excel, normalize_csv
from sourcemerger import (
    merge_sources,
    log_single_source_records,
    log_value_divergences,
    log_name_divergences,
    log_ans_divergences,
    classify_divergences,
)
from pdfmapper import rename_pdfs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


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
    logger.info(f"consolidado: {len(df)} linhas | BOTH={len(df[df.fonte=='BOTH'])} CSV_ONLY={len(df[df.fonte=='CSV_ONLY'])} EXCEL_ONLY={len(df[df.fonte=='EXCEL_ONLY'])}")

    logger.info("detectando registros em fonte unica")
    log_single_source_records(df)

    logger.info("detectando divergencias de valor")
    log_value_divergences(df)

    logger.info("detectando divergencias de nome e ANS")
    log_name_divergences(df)
    log_ans_divergences(df)

    logger.info("classificando divergencias por linha")
    df = classify_divergences(df)

    logger.info("renomeando laudos")
    renamed = rename_pdfs(df)
    df["pdf_renomeado"] = df["id_cobranca"].map(renamed)

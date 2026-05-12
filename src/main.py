import logging
import re
from typing import Optional

import ftfy
from rapidfuzz import fuzz
from unidecode import unidecode

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


MATCH_THRESHOLD = 80
MATCH_MIN_GAP = 10


def _score(filename_norm: str, patient: str) -> float:
    return 0.6 * fuzz.token_set_ratio(filename_norm, patient) + 0.4 * fuzz.partial_ratio(filename_norm, patient)


def match_pdf_to_patient(filename_norm: str, patient_names: list[str]) -> Optional[str]:
    scores = sorted([(p, _score(filename_norm, p)) for p in patient_names], key=lambda x: x[1], reverse=True)
    top1, top2 = scores[0], scores[1]
    if top1[1] < MATCH_THRESHOLD or (top1[1] - top2[1]) < MATCH_MIN_GAP:
        return None
    return top1[0]


def normalize_filename(filename: str) -> str:
    name = filename.removesuffix(".pdf")
    name = ftfy.fix_text(name)
    name = re.sub(r"[_\-\.]", " ", name)
    return unidecode(name).upper()


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


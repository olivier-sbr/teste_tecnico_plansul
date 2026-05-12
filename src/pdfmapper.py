import logging
import os
import re
import shutil
from typing import Optional

import ftfy
import pandas as pd
from rapidfuzz import fuzz
from unidecode import unidecode

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


def _extract_day_month(filename: str) -> Optional[tuple[int, int]]:
    m = re.search(r"[_\s](\d{2})[_\.](\d{2})(?:\b|$)", filename)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def rename_pdfs(df: pd.DataFrame) -> dict[str, str]:
    os.makedirs("output/laudos_processados", exist_ok=True)

    csv_rows = df[df["nome_beneficiario_norm"].notna()]
    patient_charges = {
        patient: group.sort_values("id_cobranca")
        for patient, group in csv_rows.groupby("nome_beneficiario_norm")
    }
    patient_names = list(patient_charges.keys())

    renamed: dict[str, str] = {}
    counts = {"renomeados": 0, "sem_cobranca_na_data": 0, "sem_data": 0, "nao_identificados": 0, "destino_existente": 0}

    for pdf in sorted(os.listdir("data/laudos")):
        if not pdf.endswith(".pdf"):
            continue

        norm = normalize_filename(pdf)
        patient = match_pdf_to_patient(norm, patient_names)

        if patient is None:
            logger.warning(f"laudo nao identificado: {pdf}")
            counts["nao_identificados"] += 1
            continue

        date = _extract_day_month(pdf)
        if date is None:
            logger.warning(f"laudo sem data no nome, cobranca indeterminada: {pdf} | paciente={patient}")
            counts["sem_data"] += 1
            continue

        day, month = date
        charges = patient_charges[patient]
        row = charges[(charges["dt_realizacao"].dt.day == day) & (charges["dt_realizacao"].dt.month == month)]

        if row.empty:
            logger.warning(f"laudo sem cobranca na data: {pdf} | paciente={patient} | data={day:02d}/{month:02d}")
            counts["sem_cobranca_na_data"] += 1
            continue

        row = row.iloc[0]
        cpf = str(row["cpf_beneficiario"]).replace(".", "").replace("-", "")
        nome = patient.replace(" ", "")
        id_cob = row["id_cobranca"]
        mmyyyy = row["dt_realizacao"].strftime("%m%Y")
        dest_name = f"{cpf}-{nome}-{id_cob}-{mmyyyy}.pdf"
        dest_path = os.path.join("output/laudos_processados", dest_name)

        if os.path.exists(dest_path):
            logger.warning(f"destino ja existe, pulando: {pdf} -> {dest_name}")
            counts["destino_existente"] += 1
            renamed[id_cob] = dest_name
            continue

        shutil.copy2(os.path.join("data/laudos", pdf), dest_path)
        logger.info(f"laudo renomeado: {pdf} -> {dest_name}")
        renamed[id_cob] = dest_name
        counts["renomeados"] += 1

    logger.info(
        f"laudos: {counts['renomeados']} renomeados | "
        f"{counts['sem_data']} sem data | "
        f"{counts['sem_cobranca_na_data']} sem cobranca na data | "
        f"{counts['nao_identificados']} nao identificados | "
        f"{counts['destino_existente']} destino existente"
    )
    return renamed

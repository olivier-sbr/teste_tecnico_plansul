import logging
import os
import re
import shutil
from collections import defaultdict
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


def _resolve_mappings(patient_charges: dict, patient_names: list[str]) -> list[dict]:
    results = []
    for pdf in sorted(os.listdir("data/laudos")):
        if not pdf.endswith(".pdf"):
            continue

        norm = normalize_filename(pdf)
        patient = match_pdf_to_patient(norm, patient_names)

        if patient is None:
            results.append({"pdf": pdf, "status": "nao_identificado"})
            continue

        date = _extract_day_month(pdf)
        if date is None:
            results.append({"pdf": pdf, "status": "sem_data", "patient": patient})
            continue

        day, month = date
        charges = patient_charges[patient]
        row = charges[(charges["dt_realizacao"].dt.day == day) & (charges["dt_realizacao"].dt.month == month)]

        if row.empty:
            results.append({"pdf": pdf, "status": "sem_cobranca_na_data", "patient": patient, "day": day, "month": month})
            continue

        if len(row) > 1:
            scored = sorted(
                [(r, _score(norm, unidecode(r["descricao_servico"]).upper())) for _, r in row.iterrows()],
                key=lambda x: x[1], reverse=True,
            )
            if scored[0][1] - scored[1][1] >= 10:
                results.append({"pdf": pdf, "status": "ok", "patient": patient, "row": scored[0][0]})
            else:
                candidatos = [(r["id_cobranca"], r["descricao_servico"]) for r, _ in scored]
                results.append({"pdf": pdf, "status": "ambiguo", "patient": patient, "candidatos": candidatos})
        else:
            results.append({"pdf": pdf, "status": "ok", "patient": patient, "row": row.iloc[0]})

    return results


def rename_pdfs(df: pd.DataFrame) -> tuple[dict, dict, list]:
    os.makedirs("output/laudos_processados", exist_ok=True)

    # CSV é a fonte de verdade: só considera registros com dados do CSV
    csv_rows = df[df["nome_beneficiario_norm"].notna()]
    patient_charges = {
        patient: group.sort_values("id_cobranca")
        for patient, group in csv_rows.groupby("nome_beneficiario_norm")
    }
    patient_names = list(patient_charges.keys())

    mappings = _resolve_mappings(patient_charges, patient_names)

    # Detecta conflitos: mais de um PDF resolvendo para a mesma cobrança
    cob_to_entries: dict[str, list] = defaultdict(list)
    for m in mappings:
        if m["status"] == "ok":
            cob_to_entries[m["row"]["id_cobranca"]].append(m)

    conflicting_cobs = {cob for cob, entries in cob_to_entries.items() if len(entries) > 1}

    renamed: dict[str, str] = {}
    conflicts: list[dict] = []
    counts = {
        "renomeados": 0, "sem_cobranca_na_data": 0, "sem_data": 0,
        "nao_identificados": 0, "destino_existente": 0, "ambiguos": 0, "conflitos": 0,
    }

    for m in mappings:
        pdf = m["pdf"]
        status = m["status"]

        if status == "nao_identificado":
            logger.warning(f"laudo nao identificado: {pdf}")
            counts["nao_identificados"] += 1

        elif status == "sem_data":
            logger.warning(f"laudo sem data no nome: {pdf} | paciente={m['patient']}")
            counts["sem_data"] += 1

        elif status == "sem_cobranca_na_data":
            logger.warning(f"laudo sem cobranca na data: {pdf} | paciente={m['patient']} | data={m['day']:02d}/{m['month']:02d}")
            counts["sem_cobranca_na_data"] += 1

        elif status == "ambiguo":
            logger.warning(f"laudo ambiguo, nao renomeado: {pdf} | paciente={m['patient']} | candidatos={m['candidatos']}")
            counts["ambiguos"] += 1

        elif status == "ok":
            row = m["row"]
            id_cob = row["id_cobranca"]

            # Conflito: outro PDF já resolveu para esta cobrança — não renomeia nenhum
            if id_cob in conflicting_cobs:
                continue

            cpf = str(row["cpf_beneficiario"]).replace(".", "").replace("-", "")
            nome = m["patient"].replace(" ", "")
            mmyyyy = row["dt_realizacao"].strftime("%m%Y")
            dest_name = f"{cpf}-{nome}-{id_cob}-{mmyyyy}.pdf"
            patient_dir = os.path.join("output/laudos_processados", m["patient"].replace(" ", "_"))
            os.makedirs(patient_dir, exist_ok=True)
            dest_path = os.path.join(patient_dir, dest_name)

            if os.path.exists(dest_path):
                logger.warning(f"destino ja existe, pulando: {pdf} -> {dest_name}")
                counts["destino_existente"] += 1
                renamed[id_cob] = dest_name
                continue

            shutil.copy2(os.path.join("data/laudos", pdf), dest_path)
            logger.info(f"laudo renomeado: {pdf} -> {dest_name}")
            renamed[id_cob] = dest_name
            counts["renomeados"] += 1

    for cob, entries in cob_to_entries.items():
        if cob not in conflicting_cobs:
            continue
        pdfs_list = [e["pdf"] for e in entries]
        patient = entries[0]["patient"]
        servico = entries[0]["row"]["descricao_servico"]
        logger.warning(f"conflito de laudos, nenhum renomeado: id_cobranca={cob} | paciente={patient} | laudos={pdfs_list}")
        conflicts.append({
            "id_cobranca": cob,
            "paciente": patient,
            "descricao_servico": servico,
            "pdfs": pdfs_list,
        })
        counts["conflitos"] += len(pdfs_list)

    logger.info(
        f"laudos: {counts['renomeados']} renomeados | "
        f"{counts['sem_data']} sem data | "
        f"{counts['sem_cobranca_na_data']} sem cobranca na data | "
        f"{counts['nao_identificados']} nao identificados | "
        f"{counts['ambiguos']} ambiguos | "
        f"{counts['conflitos']} em conflito | "
        f"{counts['destino_existente']} destino existente"
    )
    return renamed, counts, conflicts

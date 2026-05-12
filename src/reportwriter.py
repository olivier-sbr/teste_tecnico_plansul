import logging
import os

import pandas as pd
import xlsxwriter

DETAIL_COLUMNS = {
    "id_cobranca":       "ID Cobrança",
    "paciente":          "Paciente (Excel)",
    "nome_beneficiario": "Beneficiário (CSV)",
    "cpf_beneficiario":  "CPF",
    "registro_ans":      "ANS (Excel)",
    "ans":               "ANS (CSV)",
    "procedimento":      "Procedimento (Excel)",
    "descricao_servico": "Serviço (CSV)",
    "cod_tuss":          "Cód. TUSS",
    "data_atendimento":  "Data Atendimento",
    "dt_realizacao":     "Data Realização",
    "dt_lancamento":     "Data Lançamento",
    "valor":             "Valor (Excel)",
    "vl_servico":        "Vl. Serviço (CSV)",
    "vl_glosa":          "Vl. Glosa",
    "vl_liquido":        "Vl. Líquido",
    "nome_operadora":    "Convênio",
    "fonte":             "Fonte",
    "divergencias":      "Divergências",
    "pdf_renomeado":     "PDF Renomeado",
}

logger = logging.getLogger(__name__)


def generate_report(df: pd.DataFrame, pdf_counts: dict, output_dir: str = "output") -> str:
    missing = [col for col in DETAIL_COLUMNS if col not in df.columns]
    if missing:
        logger.error(f"relatorio abortado — colunas ausentes no dataset: {missing}")
        raise KeyError(f"colunas ausentes: {missing}")

    os.makedirs(output_dir, exist_ok=True)
    yyyymm = df["dt_realizacao"].dropna().dt.to_period("M").value_counts().index[0].strftime("%Y%m")
    filepath = os.path.join(output_dir, f"relatorio_faturamento_{yyyymm}.xlsx")

    workbook = xlsxwriter.Workbook(filepath)
    _write_resumo(workbook, df, pdf_counts)
    _write_detalhamento(workbook, df)
    _write_alertas(workbook, df)
    workbook.close()

    return filepath


def _write_resumo(workbook: xlsxwriter.Workbook, df: pd.DataFrame, pdf_counts: dict) -> None:
    ws = workbook.add_worksheet("Resumo")
    fonte_counts = df["fonte"].value_counts()

    laudos_rows = [
        ("Renomeados",            pdf_counts.get("renomeados", 0)),
        ("Destino já existente",  pdf_counts.get("destino_existente", 0)),
        ("Sem data no filename",  pdf_counts.get("sem_data", 0)),
        ("Sem cobrança na data",  pdf_counts.get("sem_cobranca_na_data", 0)),
        ("Não identificados",     pdf_counts.get("nao_identificados", 0)),
    ]

    row = _write_section(ws, 0, "COBRANÇAS POR FONTE", ("Fonte", "Quantidade"), [
        ("BOTH",       int(fonte_counts.get("BOTH", 0))),
        ("EXCEL_ONLY", int(fonte_counts.get("EXCEL_ONLY", 0))),
        ("CSV_ONLY",   int(fonte_counts.get("CSV_ONLY", 0))),
        ("Total",      len(df)),
    ])

    row = _write_section(ws, row, "VALORES (CSV)", ("Métrica", "Valor (R$)"), [
        ("Valor bruto total",   round(float(df["vl_servico"].sum()), 2)),
        ("Total de glosas",     round(float(df["vl_glosa"].sum()), 2)),
        ("Valor líquido total", round(float(df["vl_liquido"].sum()), 2)),
    ])

    _write_section(ws, row, "LAUDOS", ("Situação", "Quantidade"), [
        *laudos_rows,
        ("Total processado", sum(v for _, v in laudos_rows)),
    ])


def _write_detalhamento(workbook: xlsxwriter.Workbook, df: pd.DataFrame) -> None:
    ws = workbook.add_worksheet("Detalhamento")
    _write_sheet(ws, df)


def _write_alertas(workbook: xlsxwriter.Workbook, df: pd.DataFrame) -> None:
    ws = workbook.add_worksheet("Alertas")
    alertas = df[
        (df["fonte"] != "BOTH") |
        (df["divergencias"].notna() & (df["divergencias"] != ""))
    ].copy()
    _write_sheet(ws, alertas)


def _write_section(ws, start_row: int, title: str, headers: tuple, data: list) -> int:
    ws.write(start_row, 0, title)
    for col, header in enumerate(headers):
        ws.write(start_row + 1, col, header)
    for offset, values in enumerate(data, start=2):
        for col, val in enumerate(values):
            ws.write(start_row + offset, col, val)
    return start_row + len(data) + 3  # title + headers + data + blank line


def _write_sheet(ws, df: pd.DataFrame) -> None:
    for col_idx, header in enumerate(DETAIL_COLUMNS.values()):
        ws.write(0, col_idx, header)

    for row_idx, (_, row) in enumerate(df[list(DETAIL_COLUMNS.keys())].iterrows(), start=1):
        for col_idx, val in enumerate(row):
            ws.write(row_idx, col_idx, _cell_value(val))


def _cell_value(val):
    if pd.isna(val):
        return ""
    if isinstance(val, pd.Timestamp):
        return str(val.date())
    if isinstance(val, (int, float)):
        return val
    return str(val)

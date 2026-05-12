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
    fmts = _create_formats(workbook)
    _write_resumo(workbook, df, pdf_counts, fmts)
    _write_detalhamento(workbook, df, fmts)
    _write_alertas(workbook, df, fmts)
    _write_sem_laudo(workbook, df, fmts)
    workbook.close()

    return filepath


def _create_formats(workbook: xlsxwriter.Workbook) -> dict:
    return {
        "header":        workbook.add_format({"bold": True, "bg_color": "#1F4E79", "font_color": "white", "border": 1}),
        "section_title": workbook.add_format({"bold": True, "bg_color": "#2E75B6", "font_color": "white"}),
        "subheader":     workbook.add_format({"bold": True, "bg_color": "#BDD7EE"}),
        "alert_value":   workbook.add_format({"bg_color": "#FFCCCC"}),
        "alert_name":    workbook.add_format({"bg_color": "#FFE0CC"}),
        "alert_source":  workbook.add_format({"bg_color": "#FFFFCC"}),
        "sem_laudo":     workbook.add_format({"bg_color": "#F2F2F2"}),
    }


def _write_resumo(workbook: xlsxwriter.Workbook, df: pd.DataFrame, pdf_counts: dict, fmts: dict) -> None:
    ws = workbook.add_worksheet("Resumo")
    ws.set_column(0, 0, 28)
    ws.set_column(1, 1, 16)

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
    ], fmts)

    row = _write_section(ws, row, "VALORES (CSV)", ("Métrica", "Valor (R$)"), [
        ("Valor bruto total",   round(float(df["vl_servico"].sum()), 2)),
        ("Total de glosas",     round(float(df["vl_glosa"].sum()), 2)),
        ("Valor líquido total", round(float(df["vl_liquido"].sum()), 2)),
    ], fmts)

    row = _write_section(ws, row, "LAUDOS", ("Situação", "Quantidade"), [
        *laudos_rows,
        ("Total processado", sum(v for _, v in laudos_rows)),
    ], fmts)

    _write_legend(ws, row, fmts)


def _write_detalhamento(workbook: xlsxwriter.Workbook, df: pd.DataFrame, fmts: dict) -> None:
    ws = workbook.add_worksheet("Detalhamento")
    _write_sheet(ws, df, fmts)
    ws.freeze_panes(1, 0)
    ws.autofilter(0, 0, len(df), len(DETAIL_COLUMNS) - 1)


def _write_alertas(workbook: xlsxwriter.Workbook, df: pd.DataFrame, fmts: dict) -> None:
    ws = workbook.add_worksheet("Alertas")
    alertas = df[
        (df["fonte"] != "BOTH") |
        (df["divergencias"].notna() & (df["divergencias"] != ""))
    ].copy()
    _write_sheet(ws, alertas, fmts)
    ws.freeze_panes(1, 0)
    ws.autofilter(0, 0, len(alertas), len(DETAIL_COLUMNS) - 1)


def _write_legend(ws, start_row: int, fmts: dict) -> None:
    ws.write(start_row, 0, "LEGENDA DE CORES", fmts["section_title"])
    ws.write(start_row + 1, 0, "Cor", fmts["subheader"])
    ws.write(start_row + 1, 1, "Significado", fmts["subheader"])
    legend = [
        ("alert_value",  "Divergência de valor"),
        ("alert_name",   "Divergência de nome ou ANS"),
        ("alert_source", "Cobrança em fonte única"),
        ("sem_laudo",    "Cobrança sem laudo vinculado"),
    ]
    for offset, (fmt_key, label) in enumerate(legend, start=2):
        ws.write(start_row + offset, 0, "", fmts[fmt_key])
        ws.write(start_row + offset, 1, label)


def _write_sem_laudo(workbook: xlsxwriter.Workbook, df: pd.DataFrame, fmts: dict) -> None:
    ws = workbook.add_worksheet("Sem Laudo")
    sem_laudo = df[df["pdf_renomeado"].isna()].copy()
    _write_sheet(ws, sem_laudo, fmts)
    ws.freeze_panes(1, 0)
    ws.autofilter(0, 0, len(sem_laudo), len(DETAIL_COLUMNS) - 1)


def _write_section(ws, start_row: int, title: str, headers: tuple, data: list, fmts: dict) -> int:
    ws.write(start_row, 0, title, fmts["section_title"])
    for col, header in enumerate(headers):
        ws.write(start_row + 1, col, header, fmts["subheader"])
    for offset, values in enumerate(data, start=2):
        for col, val in enumerate(values):
            ws.write(start_row + offset, col, val)
    return start_row + len(data) + 3


def _write_sheet(ws, df: pd.DataFrame, fmts: dict) -> None:
    cols = list(DETAIL_COLUMNS.keys())
    headers = list(DETAIL_COLUMNS.values())

    _set_col_widths(ws, df, cols, headers)

    for col_idx, header in enumerate(headers):
        ws.write(0, col_idx, header, fmts["header"])

    for row_idx, (_, row_data) in enumerate(df[cols].iterrows(), start=1):
        row_fmt = _row_format(row_data, fmts)
        for col_idx, val in enumerate(row_data):
            ws.write(row_idx, col_idx, _cell_value(val), row_fmt)


def _set_col_widths(ws, df: pd.DataFrame, cols: list, headers: list) -> None:
    for col_idx, (col, header) in enumerate(zip(cols, headers)):
        max_data = max((len(str(_cell_value(v))) for v in df[col]), default=0)
        width = min(max(len(header), max_data) + 2, 50)
        ws.set_column(col_idx, col_idx, width)


def _row_format(row_data: pd.Series, fmts: dict):
    divs = str(row_data.get("divergencias") or "")
    fonte = str(row_data.get("fonte") or "")
    pdf = row_data.get("pdf_renomeado")
    if "value_divergent" in divs:
        return fmts["alert_value"]
    if "name_divergent" in divs or "ans_divergent" in divs:
        return fmts["alert_name"]
    if fonte != "BOTH":
        return fmts["alert_source"]
    if pd.isna(pdf) or pdf == "":
        return fmts["sem_laudo"]
    return None


def _cell_value(val):
    if pd.isna(val):
        return ""
    if isinstance(val, pd.Timestamp):
        return str(val.date())
    if isinstance(val, (int, float)):
        return val
    return str(val)

import logging
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd

logger = logging.getLogger(__name__)


def _brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _kpi_card(label: str, value: str, sub: str = "", accent: str = "#2E75B6") -> str:
    return f"""
    <td width="50%" style="padding:6px 8px;vertical-align:top">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:6px;border-top:3px solid {accent};
                    box-shadow:0 1px 4px rgba(0,0,0,.07)">
        <tr>
          <td style="padding:16px 18px 14px">
            <p style="margin:0 0 4px;font-size:11px;color:#888;letter-spacing:.8px;
                      text-transform:uppercase;font-family:Arial,sans-serif">{label}</p>
            <p style="margin:0;font-size:26px;font-weight:700;color:#1a1a1a;
                      font-family:Arial,sans-serif;letter-spacing:-.5px">{value}</p>
            {'<p style="margin:4px 0 0;font-size:12px;color:#aaa;font-family:Arial,sans-serif">' + sub + '</p>' if sub else ''}
          </td>
        </tr>
      </table>
    </td>"""


def _divider_row(label: str, color: str = "#2E75B6") -> str:
    return f"""
    <tr>
      <td colspan="2" style="padding:20px 0 8px">
        <p style="margin:0;font-size:11px;font-weight:700;color:{color};
                  letter-spacing:1.2px;text-transform:uppercase;
                  font-family:Arial,sans-serif;border-left:3px solid {color};
                  padding-left:8px">{label}</p>
      </td>
    </tr>"""


def _build_html(df: pd.DataFrame, pdf_counts: dict, yyyymm: str) -> str:
    fonte      = df["fonte"].value_counts()
    total      = len(df)
    both       = int(fonte.get("BOTH", 0))
    excel_only = int(fonte.get("EXCEL_ONLY", 0))
    csv_only   = int(fonte.get("CSV_ONLY", 0))

    vl_bruto   = float(df["vl_servico"].sum())
    vl_glosa   = float(df["vl_glosa"].sum())
    vl_liquido = float(df["vl_liquido"].sum())

    alertas   = int(df[
        (df["fonte"] != "BOTH") |
        (df["divergencias"].notna() & (df["divergencias"] != ""))
    ].shape[0])
    sem_laudo = int(df["pdf_renomeado"].isna().sum())

    renomeados        = pdf_counts.get("renomeados", 0)
    nao_identificados = pdf_counts.get("nao_identificados", 0)

    alerta_accent = "#c0392b" if alertas > 0 else "#27ae60"
    glosa_accent  = "#e67e22" if vl_glosa > 0 else "#27ae60"

    # period display: "202504" → "04 / 2025"
    period_display = f"{yyyymm[4:6]} / {yyyymm[:4]}" if len(yyyymm) == 6 else yyyymm

    cards_cobrancas = f"""
    <tr>
      {_kpi_card("Total de cobranças", f"{total:,}", f"período {period_display}", "#1F4E79")}
      {_kpi_card("Conciliadas (ambas)", f"{both:,}", f"{both/total*100:.0f}% do total" if total else "", "#27ae60")}
    </tr>
    <tr>
      {_kpi_card("Somente Excel", f"{excel_only:,}", "sem par no CSV", "#e67e22" if excel_only > 0 else "#27ae60")}
      {_kpi_card("Somente CSV", f"{csv_only:,}", "sem par no Excel", "#e67e22" if csv_only > 0 else "#27ae60")}
    </tr>"""

    cards_valores = f"""
    <tr>
      {_kpi_card("Valor líquido", _brl(vl_liquido), "após glosas", "#1F4E79")}
      {_kpi_card("Glosas", _brl(vl_glosa), f"{vl_glosa/vl_bruto*100:.1f}% do bruto" if vl_bruto else "", glosa_accent)}
    </tr>
    <tr>
      {_kpi_card("Valor bruto", _brl(vl_bruto), "total faturado (CSV)", "#2E75B6")}
      {_kpi_card("Alertas", f"{alertas:,}", f"{alertas/total*100:.0f}% dos registros" if total else "", alerta_accent)}
    </tr>"""

    cards_laudos = f"""
    <tr>
      {_kpi_card("Renomeados", f"{renomeados:,}", "laudos vinculados", "#27ae60")}
      {_kpi_card("Sem laudo", f"{sem_laudo:,}", "cobranças não vinculadas", "#e67e22" if sem_laudo > 0 else "#27ae60")}
    </tr>
    <tr>
      {_kpi_card("Não identificados", f"{nao_identificados:,}", "PDFs sem correspondência", "#c0392b" if nao_identificados > 0 else "#27ae60")}
      {_kpi_card("Processados", f"{renomeados + nao_identificados:,}", "total de PDFs lidos", "#2E75B6")}
    </tr>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#eef1f5;font-family:Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#eef1f5;padding:32px 0">
<tr><td align="center">
<table width="580" cellpadding="0" cellspacing="0">

  <!-- Header card -->
  <tr>
    <td style="background:#1F4E79;border-radius:8px 8px 0 0;padding:0">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:24px 28px 20px">
            <p style="margin:0;font-size:10px;color:#BDD7EE;letter-spacing:1.5px;
                      text-transform:uppercase">Plansul &nbsp;·&nbsp; Faturamento</p>
            <h1 style="margin:6px 0 0;font-size:26px;color:#fff;font-weight:700;letter-spacing:-.4px">
              Relatório {period_display}
            </h1>
          </td>
          <td style="padding:24px 28px 20px;text-align:right;vertical-align:middle">
            <span style="display:inline-block;background:#27ae60;color:#fff;font-size:11px;
                         font-weight:700;letter-spacing:.8px;text-transform:uppercase;
                         padding:5px 12px;border-radius:20px">✓ Concluído</span>
          </td>
        </tr>
        <tr>
          <td colspan="2" style="padding:0 28px 20px">
            <p style="margin:0;font-size:13px;color:#a8c4dc;line-height:1.6">
              Pipeline executado com sucesso.
              O arquivo <strong style="color:#BDD7EE">relatorio_faturamento_{yyyymm}.xlsx</strong>
              está em anexo.
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- KPI body -->
  <tr>
    <td style="background:#f7f9fc;border-radius:0 0 8px 8px;padding:20px 20px 24px;
               box-shadow:0 4px 16px rgba(0,0,0,.09)">

      <table width="100%" cellpadding="0" cellspacing="0">

        {_divider_row("Cobranças", "#1F4E79")}
        {cards_cobrancas}

        {_divider_row("Valores Financeiros", "#2E75B6")}
        {cards_valores}

        {_divider_row("Laudos PDF", "#2E75B6")}
        {cards_laudos}

      </table>

    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="padding:16px 0 0;text-align:center">
      <p style="margin:0;font-size:11px;color:#b0b8c4">
        Gerado automaticamente — não responda a este e-mail.
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def send_report(report_path: str, df: pd.DataFrame, pdf_counts: dict) -> None:
    user     = os.environ["EMAIL_USER"]
    password = os.environ["EMAIL_PASSWORD"]
    to       = os.environ["EMAIL_TO"]
    host     = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    port     = int(os.environ.get("EMAIL_PORT", "587"))

    yyyymm  = os.path.basename(report_path).replace("relatorio_faturamento_", "").replace(".xlsx", "")
    subject = f"Relatório de Faturamento — {yyyymm}"
    html    = _build_html(df, pdf_counts, yyyymm)

    outer = MIMEMultipart("mixed")
    outer["From"]    = user
    outer["To"]      = to
    outer["Subject"] = subject

    inner = MIMEMultipart("alternative")
    plain = f"Relatório de faturamento {yyyymm} em anexo."
    inner.attach(MIMEText(plain, "plain"))
    inner.attach(MIMEText(html, "html"))
    outer.attach(inner)

    with open(report_path, "rb") as f:
        attachment = MIMEApplication(f.read(), Name=os.path.basename(report_path))
    attachment["Content-Disposition"] = f'attachment; filename="{os.path.basename(report_path)}"'
    outer.attach(attachment)

    with smtplib.SMTP(host, port) as smtp:
        smtp.ehlo()
        try:
            smtp.starttls()
            smtp.ehlo()
        except smtplib.SMTPNotSupportedError:
            logger.warning("servidor nao suporta STARTTLS, conexao sem criptografia")
        smtp.login(user, password)
        smtp.sendmail(user, to, outer.as_string())

    logger.info(f"relatorio enviado para {to}")

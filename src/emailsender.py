import logging
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_report(report_path: str) -> None:
    user     = os.environ["EMAIL_USER"]
    password = os.environ["EMAIL_PASSWORD"]
    to       = os.environ["EMAIL_TO"]
    host     = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    port     = int(os.environ.get("EMAIL_PORT", "587"))

    yyyymm  = os.path.basename(report_path).replace("relatorio_faturamento_", "").replace(".xlsx", "")
    subject = f"Relatório de Faturamento — {yyyymm}"
    body    = f"Segue em anexo o relatório de faturamento referente ao período {yyyymm}."

    msg = MIMEMultipart()
    msg["From"]    = user
    msg["To"]      = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with open(report_path, "rb") as f:
        attachment = MIMEApplication(f.read(), Name=os.path.basename(report_path))
    attachment["Content-Disposition"] = f'attachment; filename="{os.path.basename(report_path)}"'
    msg.attach(attachment)

    with smtplib.SMTP(host, port) as smtp:
        smtp.ehlo()
        try:
            smtp.starttls()
            smtp.ehlo()
        except smtplib.SMTPNotSupportedError:
            logger.warning("servidor nao suporta STARTTLS, conexao sem criptografia")
        smtp.login(user, password)
        smtp.sendmail(user, to, msg.as_string())

    logger.info(f"relatorio enviado para {to}")

import logging

from dotenv import load_dotenv

from reader import load_excel, load_csv
from preprocessing import normalize_excel, normalize_csv
from sourcemerger import SourceMerger
from pdfmapper import rename_pdfs
from reportwriter import generate_report
from emailsender import send_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    load_dotenv()

    logger.info("carregando dados")
    df_excel = load_excel("data/cobrancas_internas.xlsx")
    df_csv = load_csv("data/cobrancas_convenio.csv")
    logger.info(f"excel: {len(df_excel)} linhas | csv: {len(df_csv)} linhas")

    logger.info("normalizando dados")
    df_excel = normalize_excel(df_excel)
    df_csv = normalize_csv(df_csv)

    logger.info("consolidando dataset")
    merger = SourceMerger(df_excel, df_csv)
    logger.info(
        f"consolidado: {len(merger.df)} linhas | "
        f"BOTH={len(merger.df[merger.df.fonte == 'BOTH'])} | "
        f"CSV_ONLY={len(merger.df[merger.df.fonte == 'CSV_ONLY'])} | "
        f"EXCEL_ONLY={len(merger.df[merger.df.fonte == 'EXCEL_ONLY'])}"
    )

    logger.info("detectando divergencias")
    merger.log_divergences()

    logger.info("classificando divergencias por linha")
    df = merger.classify()

    logger.info("renomeando laudos")
    renamed, pdf_counts, pdf_conflicts, pdf_unmatched = rename_pdfs(df)
    df["pdf_renomeado"] = df["id_cobranca"].map(renamed)

    logger.info("gerando relatorio")
    report_path = generate_report(df, pdf_counts, pdf_conflicts, pdf_unmatched)
    logger.info(f"relatorio gerado: {report_path}")

    logger.info("enviando relatorio por email")
    send_report(report_path, df, pdf_counts)


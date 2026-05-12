from reader import load_excel, load_csv
from preprocessing import normalize_excel, normalize_csv


if __name__ == "__main__":
    df_excel = load_excel("data/cobrancas_internas.xlsx")
    df_csv = load_csv("data/cobrancas_convenio.csv")

    df_excel = normalize_excel(df_excel)
    df_csv = normalize_csv(df_csv)

    print(df_csv.columns.tolist())
    print(df_csv[["id_cobranca"]].head())


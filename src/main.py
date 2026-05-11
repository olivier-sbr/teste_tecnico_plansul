import pandas as pd


def load_excel(path: str) -> pd.DataFrame:
    return pd.read_excel(path)


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", encoding="utf-8")


if __name__ == "__main__":
    df_excel = load_excel("data/cobrancas_internas.xlsx")
    df_csv = load_csv("data/cobrancas_convenio.csv")

    print(f"Excel: {len(df_excel)} linhas")
    print(f"CSV:   {len(df_csv)} linhas")

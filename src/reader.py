import pandas as pd


def load_excel(path: str) -> pd.DataFrame:
    return pd.read_excel(path)


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", encoding="utf-8")

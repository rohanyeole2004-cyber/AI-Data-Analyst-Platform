from pathlib import Path
import pandas as pd
ALLOWED={".csv",".xlsx",".xls"}
def load_dataframe(path_or_file):
    name=getattr(path_or_file,"name",str(path_or_file)); suffix=Path(name).suffix.lower()
    if suffix not in ALLOWED: raise ValueError("Only CSV/XLSX/XLS files are supported")
    return pd.read_csv(path_or_file) if suffix==".csv" else pd.read_excel(path_or_file)

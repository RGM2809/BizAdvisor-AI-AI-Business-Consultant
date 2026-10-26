
from io import BytesIO
from pathlib import Path

import pandas as pd

from modules.data_transformation import standardize_sales_columns


SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}


def load_sales_file(uploaded_file):
    """Read an uploaded CSV/XLSX file and standardize its columns."""
    filename = getattr(uploaded_file, "name", "upload.csv")
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Unsupported file type. Please upload a CSV or XLSX file."
        )

    file_bytes = uploaded_file.getvalue()

    if not file_bytes:
        raise ValueError("The uploaded file is empty.")

    try:
        if extension == ".csv":
            dataframe = pd.read_csv(BytesIO(file_bytes))
        else:
            dataframe = pd.read_excel(
                BytesIO(file_bytes),
                engine="openpyxl"
            )
    except Exception as exc:
        raise ValueError(
            f"Could not read the uploaded file: {exc}"
        ) from exc

    if dataframe.empty:
        raise ValueError("The uploaded file contains no data rows.")

    if len(dataframe.columns) == 0:
        raise ValueError("The uploaded file has no columns.")

    return standardize_sales_columns(dataframe)

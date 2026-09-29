import pandas as pd
from typing import Dict, Any

class HistoricalDataValidator:
    """
    Validation Data Quality Checks.
    Before data becomes eligible for backtesting, it must pass these checks.
    """
    
    def validate_dgca_format(self, df: pd.DataFrame) -> Dict[str, Any]:
        required_columns = {"month", "sector", "avg_fare", "source", "data_mode", "source_reference", "dataset_version"}
        
        report = {
            "eligible": False,
            "total_rows": len(df),
            "valid_rows": 0,
            "rejected_rows": 0,
            "duplicate_rows": 0,
            "missing_values": 0,
            "invalid_fares": 0,
            "invalid_sectors": 0,
            "date_coverage": [],
            "sector_coverage": [],
            "dataset_version": "N/A",
            "source_reference": "N/A",
            "reason": ""
        }
        
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            report["reason"] = f"Missing required columns: {missing}"
            report["rejected_rows"] = len(df)
            return report
            
        if df.empty:
            report["reason"] = "Dataset is empty"
            return report
            
        # Data Quality Checks
        missing_values_count = df.isnull().sum().sum()
        invalid_fares_count = (df["avg_fare"] <= 0).sum()
        invalid_sectors_count = df["sector"].isnull().sum()
        duplicate_rows_count = df.duplicated(subset=["month", "sector"]).sum()
        
        report["missing_values"] = int(missing_values_count)
        report["invalid_fares"] = int(invalid_fares_count)
        report["invalid_sectors"] = int(invalid_sectors_count)
        report["duplicate_rows"] = int(duplicate_rows_count)
        
        report["date_coverage"] = sorted(df["month"].dropna().unique().tolist())
        report["sector_coverage"] = sorted(df["sector"].dropna().unique().tolist())
        report["dataset_version"] = df["dataset_version"].dropna().unique()[0] if len(df["dataset_version"].dropna().unique()) > 0 else "N/A"
        report["source_reference"] = df["source_reference"].dropna().unique()[0] if len(df["source_reference"].dropna().unique()) > 0 else "N/A"
        
        failed = False
        if invalid_fares_count > 0:
            report["reason"] = "Dataset contains zero or negative fares"
            failed = True
        elif duplicate_rows_count > 0:
            report["reason"] = "Dataset contains duplicate month-sector observations"
            failed = True
        elif df["data_mode"].isnull().any() or not set(df["data_mode"].unique()).issubset({"official", "external"}):
            report["reason"] = "Invalid or missing data_mode for external/official validation"
            failed = True
        elif df["source_reference"].isnull().any() or report["source_reference"] == "N/A":
            report["reason"] = "missing_source_reference"
            failed = True
        elif df["dataset_version"].isnull().any() or report["dataset_version"] == "N/A":
            report["reason"] = "missing_dataset_version"
            failed = True
            
        if failed:
            report["rejected_rows"] = len(df)
            return report
            
        report["eligible"] = True
        report["valid_rows"] = len(df)
        report["reason"] = "passed"
        return report

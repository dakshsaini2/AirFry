from typing import Any, Dict
import pandas as pd
from backend.data.sources import HistoricalDataSource
from backend.data.validators import HistoricalDataValidator

class DGCADataSource(HistoricalDataSource):
    """
    Ingestion interface for official DGCA CSV data.
    """
    
    def __init__(self, file_path: str, dataset_version: str):
        self.file_path = file_path
        self.dataset_version = dataset_version
        
    def fetch(self, **kwargs) -> pd.DataFrame:
        # Expected format: month, sector, avg_fare, source, data_mode, source_reference
        return pd.read_csv(self.file_path)
        
    def validate(self, data: pd.DataFrame) -> bool:
        validator = HistoricalDataValidator()
        result = validator.validate_dgca_format(data)
        if not result["eligible"]:
            raise ValueError(f"DGCA Validation Failed: {result['reason']}")
        return True
        
    def normalize(self, data: pd.DataFrame) -> pd.DataFrame:
        # Ensures that the schema matches exactly what DB expects
        return data.copy()
        
    def get_provenance_metadata(self) -> Dict[str, str]:
        return {
            "source": "DGCA",
            "data_mode": "official",
            "dataset_version": self.dataset_version,
            "source_reference": self.file_path
        }

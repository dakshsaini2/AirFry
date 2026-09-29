from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, List

class HistoricalDataSource(ABC):
    """
    Base interface for independently sourced external/official data.
    """
    
    @abstractmethod
    def fetch(self, **kwargs) -> Any:
        """Fetch raw data from the source."""
        pass
        
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate the integrity and provenance of the fetched data."""
        pass
        
    @abstractmethod
    def normalize(self, data: Any) -> pd.DataFrame:
        """Convert the raw data into a normalized pandas DataFrame ready for DB injection."""
        pass
        
    @abstractmethod
    def get_provenance_metadata(self) -> Dict[str, str]:
        """Return provenance metadata (source, data_mode, dataset_version, etc.)."""
        pass

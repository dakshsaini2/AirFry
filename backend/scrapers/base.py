from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime

class BaseFareAdapter(ABC):
    def __init__(self, source_id: int, base_url: str):
        self.source_id = source_id
        self.base_url = base_url

    @abstractmethod
    def search(self, origin: str, dest: str, dep_date: datetime, lead_days: int) -> Any:
        """Search for flights and return raw result (HTML/JSON/etc)"""
        pass

    @abstractmethod
    def fetch(self, search_result: Any) -> Any:
        """Fetch details if search requires subsequent requests"""
        pass
        
    @abstractmethod
    def parse(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Parse raw data into a list of unnormalized dictionaries"""
        pass

    @abstractmethod
    def normalize(self, parsed_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize to the internal schema expected by the cleaning pipeline"""
        pass
        
    def execute(self, origin: str, dest: str, dep_date: datetime, lead_days: int) -> List[Dict[str, Any]]:
        raw = self.search(origin, dest, dep_date, lead_days)
        raw = self.fetch(raw)
        parsed = self.parse(raw)
        return self.normalize(parsed)

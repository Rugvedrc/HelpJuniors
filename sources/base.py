from abc import ABC, abstractmethod
from typing import List, Dict, Any
from models.job import Job

class SourceAdapter(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @abstractmethod
    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        """Discovers candidate raw job dictionaries."""
        pass

    @abstractmethod
    def normalize(self, raw_job: Dict[str, Any]) -> Job:
        """Converts raw job data into the Canonical Job Model."""
        pass

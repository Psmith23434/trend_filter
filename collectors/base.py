"""Base class for all source collectors."""
from abc import ABC, abstractmethod
from typing import List
from pipeline.models import RawSignal


class BaseCollector(ABC):
    source_name: str = "base"

    @abstractmethod
    def collect(self) -> List[RawSignal]:
        """Fetch raw signals from the source and return normalized RawSignal objects."""
        ...

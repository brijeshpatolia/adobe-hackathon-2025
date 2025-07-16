from abc import ABC, abstractmethod
from typing import List, Tuple
from src.common.data_structures import TextSpan, DocumentOutline, StyleProfile

class IExtractor(ABC):
    """Interface for extracting text spans from a PDF."""
    @abstractmethod
    def extract(self, pdf_path: str) -> List[TextSpan]:
        pass

class IAnalyzer(ABC):
    """Interface for analyzing document styles."""
    @abstractmethod
    def analyze(self, spans: List[TextSpan]) -> StyleProfile:
        pass

class IClassifier(ABC):
    """Interface for classifying spans into a document outline."""
    @abstractmethod
    def classify(self, spans: List[TextSpan], profile: StyleProfile) -> DocumentOutline:
        pass

class IFormatter(ABC):
    """Interface for formatting the outline into JSON."""
    @abstractmethod
    def format(self, outline: DocumentOutline) -> str:
        pass
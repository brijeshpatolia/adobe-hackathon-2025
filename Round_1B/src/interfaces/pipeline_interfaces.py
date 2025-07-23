from abc import ABC, abstractmethod
from typing import List
from src.common.data_structures import TextSpan, DocumentOutline, StyleProfile

class IExtractor(ABC):
    """Extracts text spans from a PDF file."""
    @abstractmethod
    def extract(self, pdf_path: str) -> List[TextSpan]:
        pass

class IAnalyzer(ABC):
    """Analyzes style information from text spans."""
    @abstractmethod
    def analyze(self, spans: List[TextSpan]) -> StyleProfile:
        pass

class IClassifier(ABC):
    """Classifies text spans into a structured document outline."""
    @abstractmethod
    def classify(self, spans: List[TextSpan], profile: StyleProfile) -> DocumentOutline:
        pass

class IFormatter(ABC):
    """Formats a document outline as a JSON string."""
    @abstractmethod
    def format(self, outline: DocumentOutline) -> str:
        pass
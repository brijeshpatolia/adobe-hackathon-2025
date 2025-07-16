from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict

class HeadingLevel(str, Enum):
    """Semantic levels for document headings."""
    H1 = "H1"
    H2 = "H2"
    H3 = "H3"

@dataclass
class TextSpan:
    """Represents a snippet of text with its properties."""
    text: str
    font_size: int
    font_name: str
    is_bold: bool
    page: int # The page number where the span is located
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class Heading:
    """Represents a single, classified heading."""
    text: str
    level: HeadingLevel
    page: int

@dataclass
class DocumentOutline:
    """Represents the final structured output for a document."""
    title: str
    headings: List[Heading] = field(default_factory=list)

@dataclass
class StyleProfile:
    """Stores the statistical analysis of document styles."""
    body_text_size: int = 0
    body_text_font: str = ""
    # We can add more profile metrics later, like common fonts, heading sizes, etc.
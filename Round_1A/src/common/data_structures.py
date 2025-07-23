from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

class HeadingLevel(str, Enum):
    """Document heading levels."""
    H1 = "H1"
    H2 = "H2"
    H3 = "H3"

@dataclass
class TextSpan:
    """Text segment with style and position attributes."""
    text: str
    font_size: int
    font_name: str
    is_bold: bool
    color: int
    background_color: Optional[int]
    page: int
    x0: float
    y0: float
    x1: float
    y1: float

@dataclass
class Heading:
    """Classified heading within a document."""
    text: str
    level: HeadingLevel
    page: int

@dataclass
class DocumentOutline:
    """Structured representation of a document's outline."""
    title: str
    headings: List[Heading] = field(default_factory=list)

@dataclass
class StyleProfile:
    """Statistical profile of standard body text styles."""
    body_text_size: int = 0
    body_font_name: str = ""
    body_is_bold: bool = False
    body_color: int = 0
   
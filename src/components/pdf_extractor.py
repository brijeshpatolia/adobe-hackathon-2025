import fitz  
import logging
from typing import List, Dict, Any

from src.interfaces.pipeline_interfaces import IExtractor
from src.common.data_structures import TextSpan


TEXT_BLOCK_TYPE = 0

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PDFExtractor(IExtractor):
    """
    Concrete implementation of the IExtractor interface using the PyMuPDF library.
    This class is responsible for extracting rich text data from a PDF document.
    """

    def _get_extraction_flags(self) -> int:
        """
        Returns the optimal flags for text extraction from PyMuPDF.
        This encapsulates the configuration for how PyMuPDF processes the document.
        The `TEXT_PRESERVE_LIGATURES` flag is disabled to correctly extract
        common character combinations like 'fi', 'fl', etc., as separate characters.
        """
        return fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_LIGATURES

    def _normalize_font_name(self, raw_font_name: str) -> str:
        """
        Cleans up font names provided by PyMuPDF.
        For example, a font like 'BCDEEE+Arial-BoldMT' becomes 'Arial-BoldMT'.
        """
        return raw_font_name.split('+')[-1]

    def _is_bold(self, normalized_font_name: str) -> bool:
        """
        Determines if a font is bold based on common naming conventions.
        """
        return any(indicator in normalized_font_name.lower() for indicator in ['bold', 'black', 'heavy'])

    def _create_span_from_fitz(self, fitz_span: Dict[str, Any], page_num: int) -> TextSpan:
        """
        Factory method to create a TextSpan object from a raw fitz span dictionary.
        This encapsulates the logic for converting raw data into our structured format.
        """
        text = fitz_span['text'].strip()
        font_name = self._normalize_font_name(fitz_span['font'])
        
        return TextSpan(
            text=text,
            font_size=round(fitz_span['size']),
            font_name=font_name,
            is_bold=self._is_bold(font_name),
            color=fitz_span['color'],
            page=page_num,
            x0=fitz_span['bbox'][0],
            y0=fitz_span['bbox'][1],
            x1=fitz_span['bbox'][2],
            y1=fitz_span['bbox'][3]
        )

    def extract(self, pdf_path: str) -> List[TextSpan]:
        """
        Opens a PDF and extracts detailed information about each text span.

        This method uses a context manager to ensure resources are handled safely
        and a list comprehension for efficient and readable data processing.

        Args:
            pdf_path: The file path to the PDF document.

        Returns:
            A list of TextSpan objects, each containing text and its properties.
            Returns an empty list if an error occurs.
        """
        spans = []
        try:
            # Using 'with' ensures the document is properly closed, even if errors occur.
            with fitz.open(pdf_path) as doc:
                flags = self._get_extraction_flags()
                
                # A nested list comprehension is a concise and Pythonic way to process the data.
                spans = [
                    self._create_span_from_fitz(fitz_span, page_num + 1)
                    for page_num, page in enumerate(doc)
                    for block in page.get_text("dict", flags=flags)["blocks"]
                    if block["type"] == TEXT_BLOCK_TYPE
                    for line in block["lines"]
                    for fitz_span in line["spans"]
                    if fitz_span["text"].strip()  # Ensure the span contains non-whitespace text
                ]
            logging.info(f"Successfully extracted {len(spans)} text spans from '{pdf_path}'.")
        except Exception as e:
            # Log the full exception traceback for easier debugging.
            logging.error(f"Failed to process PDF file: {pdf_path}. Error: {e}", exc_info=True)
            return []  # Return an empty list to prevent downstream errors.
            
        return spans
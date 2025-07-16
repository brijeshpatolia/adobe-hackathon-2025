import fitz 
from typing import List
from src.interfaces.pipeline_interfaces import IExtractor
from src.common.data_structures import TextSpan

class PDFExtractor(IExtractor):
    """
    Concrete implementation of the IExtractor interface using the PyMuPDF library.
    This class is responsible for extracting all text spans from a PDF document.
    """
    def extract(self, pdf_path: str) -> List[TextSpan]:
        """
        Opens a PDF and extracts detailed information about each text span.
        
        Args:
            pdf_path: The file path to the PDF document.

        Returns:
            A list of TextSpan objects, each containing text and its properties.
        """
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            print(f"Error opening or reading PDF file: {pdf_path}. Error: {e}")
            return []

        spans = []
        for page_num, page in enumerate(doc):
            # The "dict" option gives us a detailed breakdown of text blocks
            blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_LIGATURES)["blocks"]
            for block in blocks:
                # We are interested in text blocks (type 0), not image blocks (type 1)
                if block['type'] == 0:
                    for line in block['lines']:
                        for span in line['spans']:
                            text = span['text'].strip()
                            if text:  # Only add spans that contain text
                                spans.append(TextSpan(
                                    text=text,
                                    font_size=round(span['size']),
                                    font_name=span['font'],
                                    is_bold="bold" in span['font'].lower(),
                                    page=page_num + 1,
                                    x0=span['bbox'][0],
                                    y0=span['bbox'][1],
                                    x1=span['bbox'][2],
                                    y1=span['bbox'][3]
                                ))
        doc.close()
        return spans
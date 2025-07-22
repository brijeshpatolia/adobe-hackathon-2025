import fitz  # PyMuPDF
import logging
from typing import List, Dict, Any, Optional
import json
import os
import argparse
from collections import Counter

from src.common.data_structures import TextSpan
from src.interfaces.pipeline_interfaces import IExtractor

TEXT_BLOCK_TYPE = 0

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PDFExtractor(IExtractor):
    """
    Extracts text spans from a PDF, including background color detection using page rendering.
    """

    def _get_background_color(self, span_bbox: fitz.Rect, pix: fitz.Pixmap) -> Optional[int]:
        """
        Returns the most common non-white background color sampled from the bounding box area.
        """
        center_x = (span_bbox.x0 + span_bbox.x1) / 2
        center_y = (span_bbox.y0 + span_bbox.y1) / 2
        points_to_sample = [
            (span_bbox.x0 + 2, span_bbox.y0 + 2),
            (span_bbox.x1 - 2, span_bbox.y0 + 2),
            (span_bbox.x0 + 2, span_bbox.y1 - 2),
            (span_bbox.x1 - 2, span_bbox.y1 - 2),
            (center_x, center_y)
        ]
        colors = []
        for x, y in points_to_sample:
            if 0 <= x < pix.width and 0 <= y < pix.height:
                try:
                    pixel = pix.pixel(int(x), int(y))
                    if len(pixel) == 4:
                        r, g, b, _ = pixel
                    else:
                        r, g, b = pixel
                    if (r, g, b) != (255, 255, 255):
                        colors.append((r << 16) + (g << 8) + b)
                except (IndexError, ValueError):
                    continue
        if not colors:
            return None
        return Counter(colors).most_common(1)[0][0]

    def _create_span_from_fitz(self, fitz_span: Dict[str, Any], page_num: int, pix: fitz.Pixmap) -> TextSpan:
        """
        Converts a fitz span dictionary to a TextSpan, including background color.
        """
        text = fitz_span['text'].strip()
        font_name = self._normalize_font_name(fitz_span['font'])
        span_bbox = fitz.Rect(fitz_span['bbox'])
        return TextSpan(
            text=text,
            font_size=round(fitz_span['size']),
            font_name=font_name,
            is_bold=self._is_bold(font_name),
            color=fitz_span['color'],
            background_color=self._get_background_color(span_bbox, pix),
            page=page_num,
            x0=span_bbox.x0,
            y0=span_bbox.y0,
            x1=span_bbox.x1,
            y1=span_bbox.y1
        )

    def extract(self, pdf_path: str) -> List[TextSpan]:
        """
        Extracts text spans with background color information from a PDF file.
        """
        spans = []
        try:
            with fitz.open(pdf_path) as doc:
                flags = self._get_extraction_flags()
                for page_num, page in enumerate(doc):
                    pix = page.get_pixmap(dpi=300)
                    page_dict = page.get_text("dict", flags=flags)
                    for block in page_dict.get("blocks", []):
                        if block.get("type") == TEXT_BLOCK_TYPE:
                            for line in block.get("lines", []):
                                for fitz_span in line.get("spans", []):
                                    if fitz_span.get("text", "").strip():
                                        spans.append(self._create_span_from_fitz(fitz_span, page_num + 1, pix))
            logging.info(f"Extracted {len(spans)} text spans from '{pdf_path}'.")
        except Exception as e:
            logging.error(f"Failed to process PDF file: {pdf_path}. Error: {e}", exc_info=True)
            return []
        self._save_spans_to_json(spans, pdf_path)
        return spans

    def _get_extraction_flags(self) -> int:
        """
        Returns extraction flags for PyMuPDF text extraction.
        """
        return fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_LIGATURES

    def _normalize_font_name(self, raw_font_name: str) -> str:
        """
        Returns the normalized font name, removing foundry prefix if present.
        """
        return raw_font_name.split('+')[-1]

    def _is_bold(self, normalized_font_name: str) -> bool:
        """
        Determines if the font name indicates bold style.
        """
        return any(indicator in normalized_font_name.lower() for indicator in ['bold', 'black', 'heavy'])

    def _save_spans_to_json(self, spans: List[TextSpan], pdf_path: str, output_dir: str = "pdfoutput"):
        """
        Saves extracted TextSpan data to a JSON file in the specified output directory.
        """
        if not spans:
            return
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        base_name = os.path.basename(pdf_path)
        file_name_without_ext = os.path.splitext(base_name)[0]
        output_path = os.path.join(output_dir, f"{file_name_without_ext}_extracted.json")
        spans_as_dicts = [span.__dict__ for span in spans]
        logging.info(f"Saving extracted data to '{output_path}'")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(spans_as_dicts, f, ensure_ascii=False, indent=4)
            logging.info("Save complete.")
        except Exception as e:
            logging.error(f"Could not write to JSON file. Error: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract rich text and background color information from a PDF.")
    parser.add_argument("pdf_file", type=str, help="Path to the PDF file to process.")
    args = parser.parse_args()
    extractor = PDFExtractor()
    extractor.extract(args.pdf_file)
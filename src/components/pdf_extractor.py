import fitz  # PyMuPDF
import logging
from typing import List, Dict, Any
import json
import os
import argparse

# Assuming TextSpan is in this path. Adjust if necessary.
from src.common.data_structures import TextSpan
from src.interfaces.pipeline_interfaces import IExtractor


TEXT_BLOCK_TYPE = 0

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PDFExtractor(IExtractor):
    """
    Concrete implementation of the IExtractor interface using the PyMuPDF library.
    This class is responsible for extracting rich text data from a PDF document and
    saving the output to a JSON file.
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

    def _save_spans_to_json(self, spans: List[TextSpan], pdf_path: str, output_dir: str = "pdfoutput"):
        """
        Saves the extracted TextSpan data to a JSON file.
        
        Args:
            spans: The list of TextSpan objects to save.
            pdf_path: The path of the source PDF, used for naming the output file.
            output_dir: The directory to save the JSON file in. Defaults to 'pdfoutput'.
        """
        if not spans:
            logging.warning("No spans were extracted, skipping JSON save.")
            return

        # --- Create the output directory if it doesn't exist ---
        if not os.path.exists(output_dir):
            logging.info(f"Creating output directory: '{output_dir}'")
            os.makedirs(output_dir)

        # --- Determine the output filename ---
        base_name = os.path.basename(pdf_path)
        file_name_without_ext = os.path.splitext(base_name)[0]
        output_filename = f"{file_name_without_ext}_extracted.json"
        output_path = os.path.join(output_dir, output_filename)

        # --- Convert list of TextSpan objects to a list of dictionaries for JSON serialization ---
        spans_as_dicts = [span.__dict__ for span in spans]

        # --- Write the data to the JSON file ---
        logging.info(f"Saving extracted data to '{output_path}'")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(spans_as_dicts, f, ensure_ascii=False, indent=4)
            logging.info("Save complete.")
        except Exception as e:
            logging.error(f"Could not write to JSON file. Error: {e}")


    def extract(self, pdf_path: str) -> List[TextSpan]:
        """
        Opens a PDF, extracts detailed text spans, saves them to a file, and returns them.

        Args:
            pdf_path: The file path to the PDF document.

        Returns:
            A list of TextSpan objects, or an empty list if an error occurs.
        """
        spans = []
        try:
            with fitz.open(pdf_path) as doc:
                flags = self._get_extraction_flags()
                
                spans = [
                    self._create_span_from_fitz(fitz_span, page_num + 1)
                    for page_num, page in enumerate(doc)
                    for block in page.get_text("dict", flags=flags)["blocks"]
                    if block["type"] == TEXT_BLOCK_TYPE
                    for line in block["lines"]
                    for fitz_span in line["spans"]
                    if fitz_span["text"].strip()
                ]
            logging.info(f"Successfully extracted {len(spans)} text spans from '{pdf_path}'.")
        except Exception as e:
            logging.error(f"Failed to process PDF file: {pdf_path}. Error: {e}", exc_info=True)
            return []
            
        # --- ADDED: Automatically save the results after extraction ---
        self._save_spans_to_json(spans, pdf_path)
        
        return spans


# --- Added for easy command-line execution and testing ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Extracts rich text from a PDF and saves it to a JSON file."
    )
    parser.add_argument(
        "pdf_file", 
        type=str, 
        help="The full path to the PDF file you want to process."
    )
    args = parser.parse_args()

    # Instantiate the extractor and run the process
    extractor = PDFExtractor()
    extractor.extract(args.pdf_file)
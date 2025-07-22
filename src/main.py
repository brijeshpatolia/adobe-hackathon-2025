import json
import logging
import os
from typing import List

from src.interfaces.pipeline_interfaces import IExtractor, IAnalyzer, IClassifier, IFormatter
from src.common.data_structures import DocumentOutline, TextSpan
from src.components.pdf_extractor import PDFExtractor
from src.components.style_analyzer import StyleAnalyzer
from src.components.heading_classifier import HeadingClassifier
from src.components.visual_classifier import VisualClassifier
from src.components.json_formatter import JSONFormatter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_document_visually_driven(spans: List[TextSpan]) -> bool:
    """
    Determines if a document is visually driven based on its color palette.
    Returns True if less than 80% of background colors are monochrome.
    """
    GREYSCALE_TOLERANCE = 15
    background_colors = [s.background_color for s in spans if s.background_color is not None]
    if not background_colors:
        return False
    monochrome_count = 0
    for color in background_colors:
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        if max(r, g, b) - min(r, g, b) <= GREYSCALE_TOLERANCE:
            monochrome_count += 1
    monochrome_ratio = monochrome_count / len(background_colors)
    logging.info(f"Color analysis: {monochrome_ratio:.2%} of background colors are monochrome.")
    return monochrome_ratio < 0.8

class DocumentProcessor:
    """
    Orchestrates the document processing pipeline.
    Selects the appropriate classifier based on document style.
    """
    def __init__(self, extractor: IExtractor, analyzer: IAnalyzer, standard_classifier: IClassifier, visual_classifier: IClassifier, formatter: IFormatter):
        self.extractor = extractor
        self.analyzer = analyzer
        self.standard_classifier = standard_classifier
        self.visual_classifier = visual_classifier
        self.formatter = formatter

    def process_document(self, pdf_path: str) -> str:
        """
        Executes the full processing pipeline for a given PDF.
        Returns the resulting JSON string.
        """
        logging.info(f"Processing document: {pdf_path}")
        spans = self.extractor.extract(pdf_path)
        if not spans:
            logging.error(f"Extraction failed for {pdf_path}.")
            return "{}"
        style_profile = self.analyzer.analyze(spans)
        if is_document_visually_driven(spans):
            outline = self.visual_classifier.classify(spans, style_profile)
        else:
            logging.info("Using standard heading classifier (monochrome document).")
            outline = self.standard_classifier.classify(spans, style_profile)
        json_output = self.formatter.format(outline)
        logging.info(f"Processing complete: {pdf_path}")
        return json_output

if __name__ == "__main__":
    processor = DocumentProcessor(
        extractor=PDFExtractor(),
        analyzer=StyleAnalyzer(),
        standard_classifier=HeadingClassifier(),
        visual_classifier=VisualClassifier(),
        formatter=JSONFormatter()
    )
    pdf_file_path = r"data\STEMPathwaysFlyer.pdf"
    output_filename = os.path.basename(pdf_file_path).replace('.pdf', '.json')
    output_filepath = os.path.join("output", output_filename)
    os.makedirs("output", exist_ok=True)
    output_json_string = processor.process_document(pdf_file_path)
    with open(output_filepath, "w", encoding='utf-8') as f:
        f.write(output_json_string)
    print(f"\nJSON output saved to {output_filepath}")
    print(output_json_string)
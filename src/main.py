# src/main.py

import json
import logging
import os

# Import interfaces and data structures
from src.interfaces.pipeline_interfaces import IExtractor, IAnalyzer, IClassifier, IFormatter
from src.common.data_structures import DocumentOutline

# Import ALL concrete components
from src.components.pdf_extractor import PDFExtractor
from src.components.style_analyzer import StyleAnalyzer
from src.components.heading_classifier import HeadingClassifier
from src.components.json_formatter import JSONFormatter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DocumentProcessor:
    """Orchestrates the entire document processing pipeline."""
    def __init__(self, extractor: IExtractor, analyzer: IAnalyzer, classifier: IClassifier, formatter: IFormatter):
        self.extractor = extractor
        self.analyzer = analyzer
        self.classifier = classifier
        self.formatter = formatter

    def process_document(self, pdf_path: str) -> str:
        """
        Runs the full pipeline for a single PDF document.
        """
        logging.info(f"--- Starting processing for: {pdf_path} ---")
        
        # 1. Extract raw data from the PDF
        spans = self.extractor.extract(pdf_path)
        if not spans:
            logging.error(f"Extraction failed for {pdf_path}. Aborting.")
            return "{}"
        
        # 2. Analyze the styles of the extracted spans
        style_profile = self.analyzer.analyze(spans)
        
        # 3. Classify the spans into a structured outline
        outline = self.classifier.classify(spans, style_profile)
        
        # 4. Format the final outline into the required JSON string
        json_output = self.formatter.format(outline)
        
        logging.info(f"--- Pipeline finished successfully for: {pdf_path} ---")
        return json_output


if __name__ == "__main__":
    # This is where we inject our concrete implementations.
    processor = DocumentProcessor(
        extractor=PDFExtractor(),
        analyzer=StyleAnalyzer(),
        classifier=HeadingClassifier(),
        formatter=JSONFormatter()
    )
    
    # Use one of the sample PDFs from the repository
    # The 'r' prefix is important for Windows paths
    pdf_file_path = r"C:\Users\Brijesh\Downloads\E0H1CM114.pdf"
    
    # Define the output file path
    output_filename = os.path.basename(pdf_file_path).replace('.pdf', '.json')
    output_filepath = os.path.join("output", output_filename)
    
    # Ensure the output directory exists
    os.makedirs("output", exist_ok=True)

    # Process the document
    output_json_string = processor.process_document(pdf_file_path)
    
    # Save the final output to a file
    with open(output_filepath, "w") as f:
        f.write(output_json_string)
    
    print(f"\n--- Final JSON Output saved to {output_filepath} ---")
    print(output_json_string)
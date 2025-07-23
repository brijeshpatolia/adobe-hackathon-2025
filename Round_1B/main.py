import json
import logging
import os
import time
from typing import List, Dict, Any

# Import all our custom components
from src.components.pdf_extractor import PDFExtractor
from src.components.style_analyzer import StyleAnalyzer
from src.components.heading_classifier import HeadingClassifier
from src.components.visual_classifier import VisualClassifier
from src.components.json_formatter import JSONFormatter
from src.components.text_chunker import TextChunker
from src.components.embedding_generator import EmbeddingGenerator
from src.components.relevance_ranker import RelevanceRanker
from src.components.corpus_processor import CorpusProcessor

# Import the 1A DocumentProcessor from the renamed 1A main script.
from main_1a import DocumentProcessor


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Main execution function for the Round 1B task.
    """
    # --- CONFIGURATION ---
    # Set to True for local testing, False for Docker submission
    IS_LOCAL_TESTING = True

    if IS_LOCAL_TESTING:
        INPUT_DIR = "input"
        OUTPUT_DIR = "output"
        MODEL_PATH = "models/multi-qa-MiniLM-L6-cos-v1"
    else:
        INPUT_DIR = "/app/input"
        OUTPUT_DIR = "/app/output"
        MODEL_PATH = "/app/models/multi-qa-MiniLM-L6-cos-v1"
    # -----------------------------------------
    
    input_json_path = os.path.join(INPUT_DIR, "challenge1b_input.json")
    output_json_path = os.path.join(OUTPUT_DIR, "challenge1b_output.json")

    logging.info("--- Starting Round 1B: Persona-Driven Document Intelligence ---")

    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        persona = input_data["persona"]["role"]
        job_to_be_done = input_data["job_to_be_done"]["task"]
        pdf_filenames = [doc["filename"] for doc in input_data["documents"]]
        pdf_paths = [os.path.join(INPUT_DIR, "PDFs", fname) for fname in pdf_filenames]
        logging.info(f"Loaded persona '{persona}' and {len(pdf_paths)} documents.")
    except Exception as e:
        logging.error(f"Critical error loading input data from '{input_json_path}'. Error: {e}", exc_info=True)
        return

    logging.info("Initializing all system components...")
    
    pdf_extractor = PDFExtractor()
    style_analyzer = StyleAnalyzer()
    heading_classifier = HeadingClassifier()
    visual_classifier = VisualClassifier()
    json_formatter = JSONFormatter()
    
    document_processor_1a = DocumentProcessor(
        extractor=pdf_extractor,
        analyzer=style_analyzer,
        standard_classifier=heading_classifier,
        visual_classifier=visual_classifier,
        formatter=json_formatter
    )

    text_chunker = TextChunker()
    embedding_generator = EmbeddingGenerator(model_path=MODEL_PATH)
    relevance_ranker = RelevanceRanker()

    corpus_processor = CorpusProcessor(
        document_processor_1a=document_processor_1a,
        pdf_extractor=pdf_extractor,
        text_chunker=text_chunker,
        embedding_generator=embedding_generator,
        relevance_ranker=relevance_ranker
    )
    logging.info("All components initialized successfully.")

    start_time = time.time()
    processor_output = corpus_processor.process(pdf_paths, persona, job_to_be_done)
    final_ranked_sections = processor_output.get("final_results", [])
    end_time = time.time()
    
    processing_time = end_time - start_time
    logging.info(f"Corpus processing complete in {processing_time:.2f} seconds.")

    # REFINEMENT 1: Create the two lists for the final JSON output
    extracted_sections_list = []
    subsection_analysis_list = []

    # REFINEMENT 2: Add integer-based importance_rank and format lists
    for i, section in enumerate(final_ranked_sections):
        rank = i + 1
        
        extracted_sections_list.append({
            "document": section["document"],
            "page_number": section["page_number"],
            "section_title": section["section_title"],
            "importance_rank": rank 
        })
        
        subsection_analysis_list.append({
            "document": section["document"],
            "page_number": section["page_number"],
            "refined_text": section["refined_text"]
        })

    # REFINEMENT 3: Use the correct key "subsection_analysis"
    final_json_payload = {
        "metadata": {
            "input_documents": pdf_filenames,
            "persona": persona,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": time.time(),
            "processing_duration_seconds": round(processing_time, 2)
        },
        "extracted_sections": extracted_sections_list,
        "subsection_analysis": subsection_analysis_list
    }

    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(final_json_payload, f, indent=4)
        logging.info(f"Successfully wrote final output to {output_json_path}")
    except Exception as e:
        logging.error(f"Failed to write output JSON. Error: {e}")

    logging.info("--- Round 1B Processing Finished ---")


if __name__ == "__main__":
    main()

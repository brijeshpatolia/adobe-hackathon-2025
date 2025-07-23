import logging
from typing import List, Dict, Any
import json
import os

from src.components.pdf_extractor import PDFExtractor
from src.components.text_chunker import TextChunker
from src.components.embedding_generator import EmbeddingGenerator
from src.components.relevance_ranker import RelevanceRanker
from main_1a import DocumentProcessor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CorpusProcessor:
    """
    Orchestrates the end-to-end Round 1B pipeline with a section-aware ranking strategy.
    """
    def __init__(self, document_processor_1a: DocumentProcessor, pdf_extractor: PDFExtractor, text_chunker: TextChunker, embedding_generator: EmbeddingGenerator, relevance_ranker: RelevanceRanker):
        self.document_processor_1a = document_processor_1a
        self.pdf_extractor = pdf_extractor
        self.text_chunker = text_chunker
        self.embedding_generator = embedding_generator
        self.relevance_ranker = relevance_ranker

    def process(self, pdf_paths: List[str], persona: str, job_to_be_done: str) -> Dict[str, Any]:
        """
        Executes a persona-driven analysis across a collection of PDFs.
        """
        query = f"As a {persona}, my goal is to {job_to_be_done}. The following text is relevant if it addresses this goal."
        query_embedding = self.embedding_generator.generate(query)

        all_sections_with_chunks = []

        for pdf_path in pdf_paths:
            doc_name = os.path.basename(pdf_path)
            outline_json_str = self.document_processor_1a.process_document(pdf_path)
            outline_data = json.loads(outline_json_str)
            headings = outline_data.get("outline", [])
            full_text = self.pdf_extractor.extract_full_text(pdf_path)

            if not headings:
                continue

            for i, heading in enumerate(headings):
                start_pos = full_text.find(heading['text'])
                if start_pos == -1:
                    continue

                end_pos = None
                if i + 1 < len(headings):
                    next_heading_text = headings[i+1]['text']
                    end_pos = full_text.find(next_heading_text, start_pos + len(heading['text']))
                section_text = full_text[start_pos:end_pos] if end_pos is not None else full_text[start_pos:]
                chunks = self.text_chunker.chunk(section_text)
                all_sections_with_chunks.append({
                    "document": doc_name,
                    "page_number": heading['page'],
                    "section_title": heading['text'],
                    "chunks": chunks
                })

        flat_chunk_list = []
        for section_index, section in enumerate(all_sections_with_chunks):
            for chunk_text in section['chunks']:
                flat_chunk_list.append({
                    "text": chunk_text,
                    "parent_section_index": section_index
                })

        if not flat_chunk_list:
            logging.warning("No text chunks were created from the document corpus.")
            return {"final_results": []}

        chunk_texts = [chunk['text'] for chunk in flat_chunk_list]
        chunk_embeddings = self.embedding_generator.generate(chunk_texts)
        ranked_chunks = self.relevance_ranker.rank(query_embedding, chunk_embeddings, flat_chunk_list)

        section_scores = {}
        for chunk in ranked_chunks:
            parent_index = chunk['parent_section_index']
            if parent_index not in section_scores:
                section_scores[parent_index] = {
                    "score": chunk['relevance_score'],
                    "refined_text": chunk['text']
                }

        final_ranked_sections = []
        for index, data in section_scores.items():
            section_info = all_sections_with_chunks[index]
            final_ranked_sections.append({
                "document": section_info["document"],
                "page_number": section_info["page_number"],
                "section_title": section_info["section_title"],
                "importance_rank_score": data["score"],
                "refined_text": data["refined_text"]
            })
        final_ranked_sections.sort(key=lambda x: x['importance_rank_score'], reverse=True)

        return {"final_results": final_ranked_sections}

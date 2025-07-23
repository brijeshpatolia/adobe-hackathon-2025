from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TextChunker:
    """
    Splits text into manageable chunks for embedding and analysis.
    """
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            add_start_index=True,
        )

    def chunk(self, text: str) -> List[str]:
        """
        Split text into smaller chunks.
        """
        if not text:
            logging.warning("Attempted to chunk empty text.")
            return []
        logging.info(f"Chunking text of length {len(text)} characters...")
        chunks = self.splitter.split_text(text)
        logging.info(f"Successfully split text into {len(chunks)} chunks.")
        return chunks


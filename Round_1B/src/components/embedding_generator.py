import logging
from typing import List, Union

import torch
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EmbeddingGenerator:
    """
    Loads a local sentence-transformer model and generates text embeddings.
    """
    def __init__(self, model_path: str):
        """
        Initialize with a local model path.
        """
        try:
            logging.info(f"Loading sentence-transformer model from local path: {model_path}")
            self.model = SentenceTransformer(model_path)
            logging.info("Model loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load model from {model_path}.", exc_info=True)
            raise e

    def generate(self, texts: Union[str, List[str]], batch_size: int = 32) -> torch.Tensor:
        """
        Generate embeddings for a string or list of strings.
        """
        if not texts:
            logging.warning("Attempted to generate embeddings for empty text.")
            return torch.empty(0)

        logging.info(f"Generating embeddings for {len(texts) if isinstance(texts, list) else 1} text(s)...")
        embeddings = self.model.encode(
            texts,
            convert_to_tensor=True,
            batch_size=batch_size,
            show_progress_bar=False
        )
        logging.info(f"Successfully generated embeddings of shape: {embeddings.shape}")
        return embeddings


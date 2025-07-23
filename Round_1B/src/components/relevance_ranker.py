import logging
from typing import List, Dict, Any

import torch

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RelevanceRanker:
    def rank(self, query_embedding: torch.Tensor, chunk_embeddings: torch.Tensor, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if query_embedding is None or chunk_embeddings is None or not chunks:
            logging.warning("Ranking attempted with empty inputs. Returning empty list.")
            return []
        
        logging.info(f"Ranking {len(chunks)} chunks against the query...")

        query_embedding = query_embedding.to(chunk_embeddings.device)
        similarity_scores = torch.mm(query_embedding.unsqueeze(0), chunk_embeddings.T).squeeze(0)

        # Attach relevance scores to each chunk
        for i, chunk in enumerate(chunks):
            chunk['relevance_score'] = similarity_scores[i].item()

        # Sort chunks by relevance
        chunks.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logging.info("Ranking complete.")
        return chunks


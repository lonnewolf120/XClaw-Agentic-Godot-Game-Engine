import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ContextComposer:
    """
    Deterministically merges and budgets lexical, graph, and vector chunks before LLM ingestion.
    Enforces hard token/chunk limits to prevent context explosion.
    """
    def __init__(self, 
                 max_lexical: int = 8, 
                 max_graph: int = 4, 
                 max_vector: int = 4, 
                 max_total_chunks: int = 10):
        self.max_lexical = max_lexical
        self.max_graph = max_graph
        self.max_vector = max_vector
        self.max_total_chunks = max_total_chunks

    def compose(self, 
                lexical_results: List[Dict[str, Any]], 
                graph_results: List[Dict[str, Any]], 
                vector_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merges results respecting the budget.
        Priority: Lexical -> Graph -> Vector.
        Deduplicates by chunk_id/file_path/symbol_name.
        """
        composed = []
        seen_keys = set()
        
        def _add_result(item: Dict[str, Any], source: str):
            # Create a unique key for deduplication
            key = f"{item.get('file_path')}_{item.get('symbol_name', '')}_{item.get('text_excerpt', '')[:50]}"
            if key not in seen_keys and len(composed) < self.max_total_chunks:
                item['_source'] = source
                composed.append(item)
                seen_keys.add(key)
                return True
            return False

        # 1. Lexical (Highest Priority, exact matches)
        added_lex = 0
        for item in lexical_results:
            if added_lex >= self.max_lexical: break
            if _add_result(item, 'lexical'):
                added_lex += 1

        # 2. Graph Neighborhood
        added_graph = 0
        for item in graph_results:
            if added_graph >= self.max_graph: break
            if _add_result(item, 'graph'):
                added_graph += 1

        # 3. Vector (Semantic Fallback)
        added_vec = 0
        for item in vector_results:
            if added_vec >= self.max_vector: break
            if _add_result(item, 'vector'):
                added_vec += 1

        # Format output
        context_str = "--- RETRIEVED CONTEXT ---\n\n"
        for chunk in composed:
            context_str += f"[{chunk.get('_source', 'unknown').upper()}] {chunk.get('file_path')} :: {chunk.get('symbol_kind')} :: {chunk.get('symbol_name')}\n"
            context_str += f"{chunk.get('text_excerpt', '')}\n\n"
            
        return {
            "chunks_used": len(composed),
            "sources": {
                "lexical": added_lex,
                "graph": added_graph,
                "vector": added_vec
            },
            "formatted_context": context_str
        }

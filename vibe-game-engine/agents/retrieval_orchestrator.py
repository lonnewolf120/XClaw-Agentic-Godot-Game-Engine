import logging
from typing import Dict, Any, List
from store.project_graph import ProjectGraphStore
from tools.context_composer import ContextComposer

logger = logging.getLogger(__name__)

class RetrievalOrchestrator:
    """
    Tiered Context Retrieval Node.
    Executes the FTS -> Graph -> Vector escalation order.
    Returns budgeted composed context.
    """
    def __init__(self, store: ProjectGraphStore):
        self.store = store
        self.composer = ContextComposer(
            max_lexical=8,
            max_graph=4,
            max_vector=4,
            max_total_chunks=10
        )

    def retrieve_for_prompt(self, query: str, selected_file_paths: List[str] = None) -> Dict[str, Any]:
        """
        Escalation path:
        1. FTS search on the query text.
        2. If active files are selected, get their depth-1 graph neighborhood.
        3. (Placeholder) Vector search fallback if needed.
        """
        logger.info(f"Retrieving context for query: {query[:50]}...")
        
        # 1. Lexical FTS
        lexical_chunks = self.store.lexical_search(query, limit=10)
        
        # 2. Graph Neighborhood based on selection or FTS hits
        graph_chunks = []
        anchor_paths = selected_file_paths or []
        
        # If no explicit selection, use top FTS hits as graph anchors
        if not anchor_paths and lexical_chunks:
            anchor_paths = [lexical_chunks[0].get('file_path')]
            
        for path in anchor_paths:
            if path:
                # Get edge relationships
                edges = self.store.get_neighborhood(path, depth=1)
                # Expand edges to chunks
                for edge in edges:
                    target = edge.get('target_id')
                    if target and target.startswith("res://"):
                        # Resolve target file to its chunks
                        base_path = target.split('::')[0]
                        
                        # We do a fast FTS search against the file path to get its chunks
                        # A direct SQL lookup would be cleaner, but this reuses the existing API
                        file_chunks = self.store.lexical_search(base_path, limit=2)
                        for fc in file_chunks:
                            # Tag the relationship
                            fc['_edge_relation'] = edge.get('edge_type')
                            graph_chunks.append(fc)

        # 3. Vector Search (Semantic Fallback)
        # Note: Implementing actual vector search requires embedding the query via Vertex AIManager first.
        # For now, we stub it until we pipe the embedding model into this node.
        vector_chunks = [] 
        
        # Compose
        return self.composer.compose(
            lexical_results=lexical_chunks,
            graph_results=graph_chunks,
            vector_results=vector_chunks
        )

    def get_debugger_context(self, failure_class: str, file_paths: List[str]) -> Dict[str, Any]:
        """
        Targeted retrieval for Debugger. Ignores semantic/FTS query, pulls exactly the implicated files
        and their direct graph dependencies.
        """
        # We re-use composer but feed it strict graph-only results
        graph_chunks = []
        for path in file_paths:
            # 1. Grab the file's own chunks
            file_chunks = self.store.lexical_search(path, limit=5)
            graph_chunks.extend(file_chunks)
            
            # 2. Grab its neighborhood
            edges = self.store.get_neighborhood(path, depth=1)
            for edge in edges:
                 target = edge.get('target_id')
                 if target and target.startswith("res://"):
                    base_path = target.split('::')[0]
                    neighbor_chunks = self.store.lexical_search(base_path, limit=2)
                    for nc in neighbor_chunks:
                        nc['_edge_relation'] = edge.get('edge_type')
                        graph_chunks.append(nc)
                        
        composer = ContextComposer(max_lexical=0, max_graph=8, max_vector=0, max_total_chunks=8)
        return composer.compose([], graph_chunks, [])

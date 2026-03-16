import sqlite3
import uuid
import hashlib
from typing import List, Dict, Any, Optional
import struct
import json

class ProjectGraphStore:
    """
    Manages the local SQLite database for the Project Intelligence Graph and Vector chunks.
    Utilizes sqlite-vec for embedding storage and FTS5 for lexical search.
    """
    def __init__(self, db_path: str = "project_graph.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the schemas for metadata, FTS, and vector tables."""
        conn = sqlite3.connect(self.db_path)
        
        # Load sqlite-vec extension if available in the environment
        try:
            conn.enable_load_extension(True)
            import sqlite_vec
            sqlite_vec.load(conn)
        except Exception as e:
            # We fail gracefully if sqlite-vec is not strictly installed yet, 
            # as this is a new dependency. We log and continue.
            print(f"Warning: sqlite-vec extension not loaded. Vector queries may fail. {e}")

        cursor = conn.cursor()

        # 1. Metadata Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunk (
                chunk_id TEXT PRIMARY KEY,
                project_id TEXT,
                index_type TEXT, -- ENUM('project', 'engine_api', 'memory')
                file_path TEXT,
                symbol_kind TEXT, -- ENUM('gd_func', 'gd_class', 'tscn_node', 'doc_fact', 'memory_note')
                symbol_name TEXT,
                start_line INTEGER,
                end_line INTEGER,
                chunk_hash TEXT,
                file_hash TEXT,
                text_excerpt TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Graph Edges Table (Node relationships)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_edge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT, -- e.g., 'res://player.tscn::PlayerNode'
                target_id TEXT, -- e.g., 'res://player.gd'
                edge_type TEXT, -- ENUM('SCENE_CONTAINS_NODE', 'NODE_ATTACHED_SCRIPT', 'SCENE_INSTANCES_SCENE', 'SCRIPT_PRELOADS_RESOURCE')
                project_id TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Lexical Search (FTS5)
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
                chunk_id UNINDEXED,
                text,
                symbol_name,
                file_path,
                content='chunk',
                content_rowid='rowid'
            )
        """)

        # 4. Vector Table (sqlite-vec)
        # Using 3072 dimensions for gemini-embedding-001 by default.
        # sqlite-vec uses partition keys as regular metadata columns inside the vec0 table structure 
        # (supported in some versions) or we query against the metadata table and join. 
        # The recommended pattern is mapping chunk_id to vectors and joining with `chunk`.
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vec USING vec0(
                chunk_id TEXT PRIMARY KEY,
                embedding float[3072]
            )
        """)

        conn.commit()
        conn.close()

    def partitioned_vector_search(self, query_embedding: List[float], index_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Executes a vector similarity search strictly partitioned by the requested index_type
        (e.g., 'engine_api', 'project', 'memory').
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Serialize vector array for sqlite-vec
        emb_str = json.dumps(query_embedding)
        
        # Join the vec0 table with the metadata table to enforce the partition constraint.
        # This keeps our "engine docs" separate from "project scripts" reducing cross-pollution.
        try:
            cursor.execute("""
                SELECT c.file_path, c.symbol_name, c.symbol_kind, c.text_excerpt, v.distance
                FROM chunk_vec v
                JOIN chunk c ON v.chunk_id = c.chunk_id
                WHERE v.embedding MATCH ? AND c.index_type = ?
                ORDER BY v.distance
                LIMIT ?
            """, (emb_str, index_type, limit))
            results = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            print(f"Vector search failed (sqlite-vec might not be loaded): {e}")
            results = []
            
        conn.close()
        return results

    def generate_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def upsert_chunk(self, project_id: str, index_type: str, file_path: str, symbol_kind: str, 
                     symbol_name: str, text_excerpt: str, start_line: int, end_line: int, file_hash: str, embedding: Optional[List[float]] = None):
        """Inserts or updates a chunk and its embedding if the content has changed."""
        chunk_hash = self.generate_hash(text_excerpt)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if identical chunk already exists to skip DB thrashing
        cursor.execute("SELECT chunk_id FROM chunk WHERE chunk_hash = ? AND file_path = ?", (chunk_hash, file_path))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return existing[0] # No update needed
            
        chunk_id = str(uuid.uuid4())
        
        # Insert Metadata
        cursor.execute("""
            INSERT INTO chunk (chunk_id, project_id, index_type, file_path, symbol_kind, symbol_name, start_line, end_line, chunk_hash, file_hash, text_excerpt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (chunk_id, project_id, index_type, file_path, symbol_kind, symbol_name, start_line, end_line, chunk_hash, file_hash, text_excerpt))

        # Insert FTS
        cursor.execute("""
            INSERT INTO chunk_fts (rowid, chunk_id, text, symbol_name, file_path)
            VALUES (last_insert_rowid(), ?, ?, ?, ?)
        """, (chunk_id, text_excerpt, symbol_name, file_path))

        # Insert Vector if provided
        if embedding:
            # Note: sqlite-vec expects raw bytes or JSON depending on the version. Assuming JSON array format for safety in python wrapper.
            emb_str = json.dumps(embedding)
            try:
                cursor.execute("INSERT INTO chunk_vec (chunk_id, embedding) VALUES (?, ?)", (chunk_id, emb_str))
            except sqlite3.OperationalError as e:
                print(f"Skipping vector insertion: {e}")

        conn.commit()
        conn.close()
        return chunk_id

    def add_edge(self, project_id: str, source_id: str, target_id: str, edge_type: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM graph_edge WHERE source_id = ? AND target_id = ? AND edge_type = ?", (source_id, target_id, edge_type))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO graph_edge (source_id, target_id, edge_type, project_id)
                VALUES (?, ?, ?, ?)
            """, (source_id, target_id, edge_type, project_id))
            
        conn.commit()
        conn.close()

    def cleanup_stale_chunks(self, project_id: str, valid_file_paths: List[str]):
        """Deletes chunks and edges for files that no longer exist or were completely modified out."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # We delete anything not in the current active valid_file_paths list
        placeholders = ','.join('?' for _ in valid_file_paths)
        
        # 1. Get obsolete chunks
        cursor.execute(f"SELECT chunk_id FROM chunk WHERE project_id = ? AND file_path NOT IN ({placeholders})", [project_id] + valid_file_paths)
        obsolete_chunks = [row[0] for row in cursor.fetchall()]
        
        if obsolete_chunks:
            chunk_placeholders = ','.join('?' for _ in obsolete_chunks)
            # Delete from FTS
            cursor.execute(f"DELETE FROM chunk_fts WHERE chunk_id IN ({chunk_placeholders})", obsolete_chunks)
            # Delete from Vectors
            try:
                cursor.execute(f"DELETE FROM chunk_vec WHERE chunk_id IN ({chunk_placeholders})", obsolete_chunks)
            except sqlite3.OperationalError:
                pass
            # Delete from Metadata
            cursor.execute(f"DELETE FROM chunk WHERE chunk_id IN ({chunk_placeholders})", obsolete_chunks)
            
        # 2. Cleanup edges where the source or target file is gone
        # Note: edges source/target format varies ('res://a.tscn', 'res://a.tscn::Node'), 
        # so we do a prefix LIKE match on the paths for safety
        for path in valid_file_paths:
            # We skip deletion for valid paths, so we actually delete where paths are NOT LIKE any valid path
            # But SQLite doesn't easily support NOT LIKE ALL(list) simply. We will delete all edges
            # that refer to missing files.
            pass
            
        # Simpler approach: delete any edge where source or target starts with 'res://' 
        # and doesn't match an active file
        cursor.execute("SELECT id, source_id, target_id FROM graph_edge WHERE project_id = ?", (project_id,))
        for row_id, source_id, target_id in cursor.fetchall():
            # If source_id is res://file::node, base_path is res://file
            src_base = source_id.split('::')[0] if '::' in source_id else source_id
            tgt_base = target_id.split('::')[0] if '::' in target_id else target_id
            
            if (src_base.startswith('res://') and src_base not in valid_file_paths) or \
               (tgt_base.startswith('res://') and tgt_base not in valid_file_paths):
                cursor.execute("DELETE FROM graph_edge WHERE id = ?", (row_id,))

        conn.commit()
        conn.close()

    def get_neighborhood(self, file_path: str, depth: int = 1) -> List[Dict[str, Any]]:
        """
        Retrieves the dependency neighborhood (graph edges) for a given file or node.
        Returns connected files and relationships.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Simple depth-1 lookup for now
        # Find everything attached to this file_path, or instances of this file_path
        cursor.execute("""
            SELECT source_id, target_id, edge_type
            FROM graph_edge
            WHERE source_id LIKE ? OR target_id LIKE ?
        """, (f"{file_path}%", f"{file_path}%"))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def lexical_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.file_path, c.symbol_name, c.symbol_kind, c.text_excerpt 
            FROM chunk_fts f
            JOIN chunk c ON f.chunk_id = c.chunk_id
            WHERE chunk_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

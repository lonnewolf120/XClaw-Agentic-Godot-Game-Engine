import os
import shutil
from pathlib import Path

try:
    from google.cloud import storage
except ImportError:
    storage = None

class ArtifactStore:
    """
    Handles persisting the workspace and Godot artifacts to Google Cloud Storage 
    in GCP, or defaulting to local filesystem for testing.
    """
    def __init__(self, gcs_bucket_name: str = None):
        self.bucket_name = gcs_bucket_name or os.environ.get("GCS_BUCKET_NAME")
        
        if self.bucket_name and storage:
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
        else:
            self.client = None
            self.bucket = None
            
    def is_gcs_enabled(self) -> bool:
        return self.bucket is not None
        
    def upload_workspace(self, run_id: str, local_dir: str):
        """Zip the workspace and upload it, or just copy it."""
        if not self.is_gcs_enabled():
            return # Local relies on disk already

        archive_path = f"/tmp/{run_id}_workspace"
        shutil.make_archive(archive_path, 'zip', local_dir)
        
        blob = self.bucket.blob(f"runs/{run_id}/workspace.zip")
        blob.upload_from_filename(f"{archive_path}.zip")
        os.remove(f"{archive_path}.zip")
        
    def download_workspace(self, run_id: str, dest_dir: str):
        if not self.is_gcs_enabled():
            return
            
        archive_path = f"/tmp/{run_id}_workspace.zip"
        blob = self.bucket.blob(f"runs/{run_id}/workspace.zip")
        if blob.exists():
            blob.download_to_filename(archive_path)
            shutil.unpack_archive(archive_path, dest_dir, 'zip')
            os.remove(archive_path)

    def upload_artifact(self, run_id: str, artifact_name: str, local_path: str):
        if not self.is_gcs_enabled():
            # Already on disk, but maybe want to copy to a durable 'runs' folder?
            return
            
        blob = self.bucket.blob(f"runs/{run_id}/artifacts/{artifact_name}")
        blob.upload_from_filename(local_path)

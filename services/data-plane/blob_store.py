from dataclasses import dataclass
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import os


class BlobStore(ABC):
    """Abstract base class for storing large results referenced by URI"""
    
    @abstractmethod
    def store_blob(self, tenant_id: str, blob_id: str, content: bytes, content_type: str) -> str:
        """Store a blob and return its URI"""
        pass
    
    @abstractmethod
    def retrieve_blob(self, uri: str) -> Optional[bytes]:
        """Retrieve a blob by URI"""
        pass
    
    @abstractmethod
    def delete_blob(self, uri: str) -> bool:
        """Delete a blob by URI"""
        pass
    
    @abstractmethod
    def get_blob_metadata(self, uri: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a blob"""
        pass


class FileSystemBlobStore(BlobStore):
    """File system implementation of BlobStore for local development"""
    
    def __init__(self, base_path: str = "./blobs"):
        """Initialize file system blob store"""
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    def store_blob(self, tenant_id: str, blob_id: str, content: bytes, content_type: str) -> str:
        """Store a blob and return its URI"""
        # Create tenant directory
        tenant_path = os.path.join(self.base_path, tenant_id)
        os.makedirs(tenant_path, exist_ok=True)
        
        # Create blob file
        blob_path = os.path.join(tenant_path, f"{blob_id}.blob")
        with open(blob_path, 'wb') as f:
            f.write(content)
        
        # Store metadata
        metadata_path = os.path.join(tenant_path, f"{blob_id}.meta")
        metadata = {
            "content_type": content_type,
            "size_bytes": len(content),
            "created_at": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
        with open(metadata_path, 'w') as f:
            import json
            json.dump(metadata, f)
        
        return f"file://{blob_path}"
    
    def retrieve_blob(self, uri: str) -> Optional[bytes]:
        """Retrieve a blob by URI"""
        if not uri.startswith("file://"):
            return None
        
        file_path = uri[7:]  # Remove "file://" prefix
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            return None
    
    def delete_blob(self, uri: str) -> bool:
        """Delete a blob by URI"""
        if not uri.startswith("file://"):
            return False
        
        file_path = uri[7:]  # Remove "file://" prefix
        try:
            os.remove(file_path)
            
            # Also delete metadata file
            metadata_path = file_path.replace('.blob', '.meta')
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            
            return True
        except FileNotFoundError:
            return False
    
    def get_blob_metadata(self, uri: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a blob"""
        if not uri.startswith("file://"):
            return None
        
        file_path = uri[7:]  # Remove "file://" prefix
        metadata_path = file_path.replace('.blob', '.meta')
        
        try:
            with open(metadata_path, 'r') as f:
                import json
                return json.load(f)
        except FileNotFoundError:
            return None 
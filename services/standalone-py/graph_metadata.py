from dataclasses import dataclass
from typing import List, Dict
from .timestamp import Timestamp


@dataclass
class GraphMetadata:
    """Versioning, description, and graph-level configuration"""
    
    # Human-readable name for the graph
    name: str
    
    # Description of the graph's purpose
    description: str
    
    # Author of the graph
    author: str
    
    # Creation timestamp
    created_at: Timestamp
    
    # Last modified timestamp
    modified_at: Timestamp
    
    # Tags for categorization
    tags: List[str]
    
    # Graph-level configuration
    configuration: Dict[str, str]
    
    def __post_init__(self):
        """Validate metadata after initialization"""
        if not self.name:
            raise ValueError("name cannot be empty")
        if not self.author:
            raise ValueError("author cannot be empty") 
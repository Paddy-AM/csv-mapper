"""
Storage and retrieval of reusable mapping templates.
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import hashlib

class MappingStorage:
    """Handles saving and loading of mapping templates."""
    
    def __init__(self, storage_dir: str = "mappings"):
        """
        Initialize mapping storage.
        
        Args:
            storage_dir: Directory to store mapping files
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def _generate_mapping_id(self, name: str) -> str:
        """
        Generate a unique ID for a mapping.
        
        Args:
            name: Mapping name
            
        Returns:
            Unique mapping ID
        """
        timestamp = datetime.now().isoformat()
        hash_input = f"{name}_{timestamp}".encode()
        return hashlib.md5(hash_input).hexdigest()[:12]
    
    def save_mapping(self, name: str, description: str, mapping: Dict[str, str]) -> str:
        """
        Save a mapping template.
        
        Args:
            name: Name of the mapping
            description: Description of the mapping
            mapping: Dictionary mapping schema fields to CSV columns
            
        Returns:
            ID of the saved mapping
        """
        mapping_id = self._generate_mapping_id(name)
        
        mapping_data = {
            "id": mapping_id,
            "name": name,
            "description": description,
            "mapping": mapping,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        filepath = os.path.join(self.storage_dir, f"{mapping_id}.json")
        with open(filepath, 'w') as f:
            json.dump(mapping_data, f, indent=2)
        
        return mapping_id
    
    def get_mapping(self, mapping_id: str) -> Optional[Dict]:
        """
        Retrieve a mapping by ID.
        
        Args:
            mapping_id: ID of the mapping to retrieve
            
        Returns:
            Mapping data or None if not found
        """
        filepath = os.path.join(self.storage_dir, f"{mapping_id}.json")
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def list_mappings(self) -> List[Dict]:
        """
        List all saved mappings.
        
        Returns:
            List of mapping metadata (without full mapping details)
        """
        mappings = []
        
        if not os.path.exists(self.storage_dir):
            return mappings
        
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.storage_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        mappings.append({
                            "id": data["id"],
                            "name": data["name"],
                            "description": data["description"],
                            "created_at": data["created_at"]
                        })
                except Exception:
                    continue
        
        # Sort by creation date (newest first)
        mappings.sort(key=lambda x: x["created_at"], reverse=True)
        
        return mappings
    
    def delete_mapping(self, mapping_id: str) -> bool:
        """
        Delete a mapping by ID.
        
        Args:
            mapping_id: ID of the mapping to delete
            
        Returns:
            True if deleted, False if not found
        """
        filepath = os.path.join(self.storage_dir, f"{mapping_id}.json")
        
        if not os.path.exists(filepath):
            return False
        
        try:
            os.remove(filepath)
            return True
        except Exception:
            return False
    
    def update_mapping(self, mapping_id: str, name: str, description: str, mapping: Dict[str, str]) -> bool:
        """
        Update an existing mapping.
        
        Args:
            mapping_id: ID of the mapping to update
            name: New name
            description: New description
            mapping: New mapping configuration
            
        Returns:
            True if updated, False if not found
        """
        existing = self.get_mapping(mapping_id)
        if not existing:
            return False
        
        mapping_data = {
            "id": mapping_id,
            "name": name,
            "description": description,
            "mapping": mapping,
            "created_at": existing["created_at"],
            "updated_at": datetime.now().isoformat()
        }
        
        filepath = os.path.join(self.storage_dir, f"{mapping_id}.json")
        with open(filepath, 'w') as f:
            json.dump(mapping_data, f, indent=2)
        
        return True

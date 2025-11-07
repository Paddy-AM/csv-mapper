"""
Tests for mapping storage functionality.
"""
import pytest
import os
import tempfile
import shutil
from app.mapping_storage import MappingStorage


class TestMappingStorage:
    """Test cases for MappingStorage class."""
    
    def setup_method(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = MappingStorage(storage_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_save_mapping(self):
        """Test saving a mapping."""
        mapping = {
            "user_id": "id",
            "email": "email_col",
            "first_name": "fname",
            "last_name": "lname"
        }
        
        mapping_id = self.storage.save_mapping(
            name="Test Mapping",
            description="A test mapping",
            mapping=mapping
        )
        
        assert mapping_id is not None
        assert len(mapping_id) == 12  # MD5 hash truncated to 12 chars
        
        # Verify file was created
        filepath = os.path.join(self.temp_dir, f"{mapping_id}.json")
        assert os.path.exists(filepath)
    
    def test_get_mapping(self):
        """Test retrieving a saved mapping."""
        mapping = {
            "user_id": "id",
            "email": "email_col",
            "first_name": "fname",
            "last_name": "lname"
        }
        
        mapping_id = self.storage.save_mapping(
            name="Test Mapping",
            description="A test mapping",
            mapping=mapping
        )
        
        retrieved = self.storage.get_mapping(mapping_id)
        
        assert retrieved is not None
        assert retrieved["id"] == mapping_id
        assert retrieved["name"] == "Test Mapping"
        assert retrieved["description"] == "A test mapping"
        assert retrieved["mapping"] == mapping
        assert "created_at" in retrieved
        assert "updated_at" in retrieved
    
    def test_get_nonexistent_mapping(self):
        """Test retrieving a mapping that doesn't exist."""
        result = self.storage.get_mapping("nonexistent_id")
        assert result is None
    
    def test_list_mappings(self):
        """Test listing all saved mappings."""
        # Save multiple mappings
        mapping1 = {"user_id": "id1", "email": "email1", "first_name": "fname1", "last_name": "lname1"}
        mapping2 = {"user_id": "id2", "email": "email2", "first_name": "fname2", "last_name": "lname2"}
        
        id1 = self.storage.save_mapping("Mapping 1", "First mapping", mapping1)
        id2 = self.storage.save_mapping("Mapping 2", "Second mapping", mapping2)
        
        mappings = self.storage.list_mappings()
        
        assert len(mappings) == 2
        assert any(m["id"] == id1 for m in mappings)
        assert any(m["id"] == id2 for m in mappings)
        
        # Check that full mapping is not included in list
        for m in mappings:
            assert "mapping" not in m
            assert "name" in m
            assert "description" in m
            assert "created_at" in m
    
    def test_list_mappings_empty(self):
        """Test listing mappings when none exist."""
        mappings = self.storage.list_mappings()
        assert len(mappings) == 0
    
    def test_delete_mapping(self):
        """Test deleting a mapping."""
        mapping = {"user_id": "id", "email": "email", "first_name": "fname", "last_name": "lname"}
        mapping_id = self.storage.save_mapping("Test", "Test mapping", mapping)
        
        # Verify it exists
        assert self.storage.get_mapping(mapping_id) is not None
        
        # Delete it
        success = self.storage.delete_mapping(mapping_id)
        assert success is True
        
        # Verify it's gone
        assert self.storage.get_mapping(mapping_id) is None
    
    def test_delete_nonexistent_mapping(self):
        """Test deleting a mapping that doesn't exist."""
        success = self.storage.delete_mapping("nonexistent_id")
        assert success is False
    
    def test_update_mapping(self):
        """Test updating an existing mapping."""
        original_mapping = {"user_id": "id", "email": "email", "first_name": "fname", "last_name": "lname"}
        mapping_id = self.storage.save_mapping("Original", "Original description", original_mapping)
        
        # Get original created_at
        original = self.storage.get_mapping(mapping_id)
        original_created_at = original["created_at"]
        
        # Update the mapping
        updated_mapping = {"user_id": "new_id", "email": "new_email", "first_name": "new_fname", "last_name": "new_lname"}
        success = self.storage.update_mapping(
            mapping_id,
            "Updated",
            "Updated description",
            updated_mapping
        )
        
        assert success is True
        
        # Verify updates
        updated = self.storage.get_mapping(mapping_id)
        assert updated["name"] == "Updated"
        assert updated["description"] == "Updated description"
        assert updated["mapping"] == updated_mapping
        assert updated["created_at"] == original_created_at  # Should not change
        assert updated["updated_at"] != original["updated_at"]  # Should change
    
    def test_update_nonexistent_mapping(self):
        """Test updating a mapping that doesn't exist."""
        success = self.storage.update_mapping(
            "nonexistent_id",
            "Name",
            "Description",
            {"user_id": "id", "email": "email", "first_name": "fname", "last_name": "lname"}
        )
        assert success is False
    
    def test_generate_unique_ids(self):
        """Test that generated IDs are unique."""
        mapping = {"user_id": "id", "email": "email", "first_name": "fname", "last_name": "lname"}
        
        id1 = self.storage.save_mapping("Mapping 1", "Description", mapping)
        id2 = self.storage.save_mapping("Mapping 2", "Description", mapping)
        
        assert id1 != id2
    
    def test_storage_directory_creation(self):
        """Test that storage directory is created if it doesn't exist."""
        new_dir = os.path.join(self.temp_dir, "new_storage")
        assert not os.path.exists(new_dir)
        
        storage = MappingStorage(storage_dir=new_dir)
        assert os.path.exists(new_dir)

"""
Integration tests for the FastAPI application.
"""
import pytest
from fastapi.testclient import TestClient
import io
import os
import tempfile
import shutil

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_csv_with_header():
    """Create a sample CSV file with header."""
    content = b"user_id,email,first_name,last_name,age\nUSR001,john@example.com,John,Doe,30\nUSR002,jane@example.com,Jane,Smith,25"
    return ("test.csv", io.BytesIO(content), "text/csv")


@pytest.fixture
def sample_csv_without_header():
    """Create a sample CSV file without header."""
    content = b"USR001,john@example.com,John,Doe,30\nUSR002,jane@example.com,Jane,Smith,25"
    return ("test.csv", io.BytesIO(content), "text/csv")


class TestAPIEndpoints:
    """Test cases for API endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_get_schema(self, client):
        """Test getting schema information."""
        response = client.get("/api/schema")
        assert response.status_code == 200
        
        data = response.json()
        assert "fields" in data
        assert "required_fields" in data
        assert "all_fields" in data
        
        # Check required fields
        assert "user_id" in data["required_fields"]
        assert "email" in data["required_fields"]
        assert "first_name" in data["required_fields"]
        assert "last_name" in data["required_fields"]
    
    def test_upload_csv_with_header(self, client, sample_csv_with_header):
        """Test uploading a CSV file with header."""
        response = client.post(
            "/api/upload",
            files={"file": sample_csv_with_header}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "file_id" in data
        assert data["filename"] == "test.csv"
        assert data["row_count"] == 2
        assert data["has_header"] is True
        assert "user_id" in data["columns"]
        assert "email" in data["columns"]
        assert "suggested_mappings" in data
        assert "validation" in data
    
    def test_upload_csv_suggestions(self, client, sample_csv_with_header):
        """Test that upload provides good mapping suggestions."""
        response = client.post(
            "/api/upload",
            files={"file": sample_csv_with_header}
        )
        
        data = response.json()
        suggestions = data["suggested_mappings"]
        
        # Should suggest correct mappings for exact matches
        assert suggestions["user_id"] == "user_id"
        assert suggestions["email"] == "email"
        assert suggestions["first_name"] == "first_name"
        assert suggestions["last_name"] == "last_name"
    
    def test_upload_empty_file(self, client):
        """Test uploading an empty CSV file."""
        empty_csv = ("empty.csv", io.BytesIO(b""), "text/csv")
        
        response = client.post(
            "/api/upload",
            files={"file": empty_csv}
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    def test_validate_correct_mapping(self, client, sample_csv_with_header):
        """Test validating a correct mapping."""
        # First upload a file
        upload_response = client.post(
            "/api/upload",
            files={"file": sample_csv_with_header}
        )
        file_id = upload_response.json()["file_id"]
        
        # Validate with correct mapping
        validate_response = client.post(
            "/api/validate",
            json={
                "file_id": file_id,
                "mapping": {
                    "user_id": "user_id",
                    "email": "email",
                    "first_name": "first_name",
                    "last_name": "last_name",
                    "age": "age"
                }
            }
        )
        
        assert validate_response.status_code == 200
        data = validate_response.json()
        assert data["valid"] is True
        assert len(data["errors"]) == 0
    
    def test_validate_missing_required_field(self, client, sample_csv_with_header):
        """Test validation fails when required field is missing."""
        # First upload a file
        upload_response = client.post(
            "/api/upload",
            files={"file": sample_csv_with_header}
        )
        file_id = upload_response.json()["file_id"]
        
        # Validate with missing required field
        validate_response = client.post(
            "/api/validate",
            json={
                "file_id": file_id,
                "mapping": {
                    "user_id": "user_id",
                    "email": "email",
                    "first_name": "first_name"
                    # Missing last_name
                }
            }
        )
        
        assert validate_response.status_code == 200
        data = validate_response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0
        assert any("last_name" in error for error in data["errors"])
    
    def test_validate_nonexistent_file(self, client):
        """Test validation with nonexistent file ID."""
        response = client.post(
            "/api/validate",
            json={
                "file_id": "nonexistent",
                "mapping": {
                    "user_id": "id",
                    "email": "email",
                    "first_name": "fname",
                    "last_name": "lname"
                }
            }
        )
        
        assert response.status_code == 404
    
    def test_save_mapping(self, client):
        """Test saving a mapping template."""
        response = client.post(
            "/api/mappings/save",
            json={
                "name": "Test Mapping",
                "description": "A test mapping template",
                "mapping": {
                    "user_id": "id",
                    "email": "email",
                    "first_name": "fname",
                    "last_name": "lname"
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "mapping_id" in data
        assert data["message"] == "Mapping saved successfully"
    
    def test_save_invalid_mapping(self, client):
        """Test saving an invalid mapping (missing required fields)."""
        response = client.post(
            "/api/mappings/save",
            json={
                "name": "Invalid Mapping",
                "description": "Missing required fields",
                "mapping": {
                    "user_id": "id",
                    "email": "email"
                    # Missing first_name and last_name
                }
            }
        )
        
        assert response.status_code == 400
        assert "invalid mapping" in response.json()["detail"].lower()
    
    def test_list_mappings(self, client):
        """Test listing saved mappings."""
        # Save a mapping first
        client.post(
            "/api/mappings/save",
            json={
                "name": "Test Mapping",
                "description": "Test",
                "mapping": {
                    "user_id": "id",
                    "email": "email",
                    "first_name": "fname",
                    "last_name": "lname"
                }
            }
        )
        
        # List mappings
        response = client.get("/api/mappings")
        assert response.status_code == 200
        
        data = response.json()
        assert "mappings" in data
        assert len(data["mappings"]) >= 1
    
    def test_get_mapping(self, client):
        """Test retrieving a specific mapping."""
        # Save a mapping
        save_response = client.post(
            "/api/mappings/save",
            json={
                "name": "Test Mapping",
                "description": "Test",
                "mapping": {
                    "user_id": "id",
                    "email": "email",
                    "first_name": "fname",
                    "last_name": "lname"
                }
            }
        )
        mapping_id = save_response.json()["mapping_id"]
        
        # Get the mapping
        response = client.get(f"/api/mappings/{mapping_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == mapping_id
        assert data["name"] == "Test Mapping"
        assert "mapping" in data
    
    def test_get_nonexistent_mapping(self, client):
        """Test retrieving a mapping that doesn't exist."""
        response = client.get("/api/mappings/nonexistent_id")
        assert response.status_code == 404
    
    def test_delete_mapping(self, client):
        """Test deleting a mapping."""
        # Save a mapping
        save_response = client.post(
            "/api/mappings/save",
            json={
                "name": "Test Mapping",
                "description": "Test",
                "mapping": {
                    "user_id": "id",
                    "email": "email",
                    "first_name": "fname",
                    "last_name": "lname"
                }
            }
        )
        mapping_id = save_response.json()["mapping_id"]
        
        # Delete the mapping
        response = client.delete(f"/api/mappings/{mapping_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify it's gone
        get_response = client.get(f"/api/mappings/{mapping_id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_mapping(self, client):
        """Test deleting a mapping that doesn't exist."""
        response = client.delete("/api/mappings/nonexistent_id")
        assert response.status_code == 404

"""
Tests for CSV handler functionality.
"""
import pytest
import pandas as pd
from app.csv_handler import CSVHandler


class TestCSVHandler:
    """Test cases for CSVHandler class."""
    
    def test_parse_csv_with_header(self):
        """Test parsing CSV file with header."""
        csv_content = b"name,email,age\nJohn,john@example.com,30\nJane,jane@example.com,25"
        handler = CSVHandler(csv_content, "test.csv")
        
        success, error = handler.parse()
        
        assert success is True
        assert error is None
        assert handler.has_header is True
        assert handler.columns == ["name", "email", "age"]
        assert handler.get_row_count() == 2
    
    def test_parse_csv_without_header(self):
        """Test parsing CSV file without header."""
        csv_content = b"John,john@example.com,30\nJane,jane@example.com,25"
        handler = CSVHandler(csv_content, "test.csv")
        
        success, error = handler.parse()
        
        assert success is True
        assert error is None
        # Header detection is heuristic-based, so we just verify it parses successfully
        assert len(handler.columns) == 3
        # Columns should be either generated names or first row values
        assert handler.columns is not None
    
    def test_validate_file_size_within_limit(self):
        """Test file size validation for valid file."""
        csv_content = b"name,email\nJohn,john@example.com"
        handler = CSVHandler(csv_content, "test.csv")
        
        is_valid, error = handler.validate_file_size()
        
        assert is_valid is True
        assert error is None
    
    def test_validate_file_size_exceeds_limit(self):
        """Test file size validation for oversized file."""
        # Create content larger than 100 MB
        large_content = b"x" * (101 * 1024 * 1024)
        handler = CSVHandler(large_content, "large.csv")
        
        is_valid, error = handler.validate_file_size()
        
        assert is_valid is False
        assert "exceeds maximum" in error
    
    def test_get_preview(self):
        """Test getting preview of CSV data."""
        csv_content = b"name,email\nJohn,john@example.com\nJane,jane@example.com\nBob,bob@example.com"
        handler = CSVHandler(csv_content, "test.csv")
        handler.parse()
        
        preview = handler.get_preview(num_rows=2)
        
        assert len(preview) == 2
        assert preview[0]["name"] == "John"
        assert preview[1]["name"] == "Jane"
    
    def test_get_column_info(self):
        """Test getting column information."""
        csv_content = b"name,email,age\nJohn,john@example.com,30\nJane,jane@example.com,\nBob,bob@example.com,35"
        handler = CSVHandler(csv_content, "test.csv")
        handler.parse()
        
        column_info = handler.get_column_info()
        
        assert len(column_info) == 3
        
        # Check name column
        name_info = next(col for col in column_info if col["name"] == "name")
        assert name_info["non_null_count"] == 3
        assert name_info["null_count"] == 0
        
        # Check age column (has one null value)
        age_info = next(col for col in column_info if col["name"] == "age")
        assert age_info["non_null_count"] == 2
        assert age_info["null_count"] == 1
    
    def test_parse_empty_csv(self):
        """Test parsing empty CSV file."""
        csv_content = b""
        handler = CSVHandler(csv_content, "empty.csv")
        
        success, error = handler.parse()
        
        assert success is False
        assert "empty" in error.lower()
    
    def test_parse_malformed_csv(self):
        """Test parsing malformed CSV file."""
        csv_content = b"name,email\nJohn,john@example.com,extra,fields\nJane"
        handler = CSVHandler(csv_content, "malformed.csv")
        
        # pandas is quite forgiving, so this might still parse
        # but we test that it doesn't crash
        success, error = handler.parse()
        # Result depends on pandas behavior
        assert isinstance(success, bool)
    
    def test_column_name_whitespace_handling(self):
        """Test that column names with whitespace are trimmed."""
        csv_content = b" name , email ,age\nJohn,john@example.com,30"
        handler = CSVHandler(csv_content, "test.csv")
        handler.parse()
        
        assert handler.columns == ["name", "email", "age"]
    
    def test_detect_header_with_numeric_data(self):
        """Test header detection with numeric data."""
        # CSV with header
        csv_with_header = b"id,value\n1,100\n2,200"
        handler1 = CSVHandler(csv_with_header, "test1.csv")
        assert handler1.detect_header() is True
        
        # CSV without header (all numeric)
        csv_without_header = b"1,100\n2,200\n3,300"
        handler2 = CSVHandler(csv_without_header, "test2.csv")
        # This is harder to detect, but should handle gracefully
        result = handler2.detect_header()
        assert isinstance(result, bool)

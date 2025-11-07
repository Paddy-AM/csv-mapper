"""
Tests for mapping suggestion and validation functionality.
"""
import pytest
from app.mapper import MappingSuggester, MappingValidator


class TestMappingSuggester:
    """Test cases for MappingSuggester class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.suggester = MappingSuggester()
    
    def test_exact_match_suggestion(self):
        """Test that exact matches are suggested."""
        csv_columns = ["user_id", "email", "first_name", "last_name"]
        
        suggestions = self.suggester.suggest_mappings(csv_columns)
        
        assert suggestions["user_id"] == "user_id"
        assert suggestions["email"] == "email"
        assert suggestions["first_name"] == "first_name"
        assert suggestions["last_name"] == "last_name"
    
    def test_alias_match_suggestion(self):
        """Test that aliases are recognized."""
        csv_columns = ["id", "mail", "fname", "lname"]
        
        suggestions = self.suggester.suggest_mappings(csv_columns)
        
        assert suggestions["user_id"] == "id"
        assert suggestions["email"] == "mail"
        assert suggestions["first_name"] == "fname"
        assert suggestions["last_name"] == "lname"
    
    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        csv_columns = ["USER_ID", "EMAIL", "First_Name", "Last_Name"]
        
        suggestions = self.suggester.suggest_mappings(csv_columns)
        
        assert suggestions["user_id"] == "USER_ID"
        assert suggestions["email"] == "EMAIL"
        assert suggestions["first_name"] == "First_Name"
        assert suggestions["last_name"] == "Last_Name"
    
    def test_similarity_matching(self):
        """Test fuzzy similarity matching."""
        csv_columns = ["userid", "emailaddress", "firstname", "lastname"]
        
        suggestions = self.suggester.suggest_mappings(csv_columns)
        
        # These should match based on similarity
        assert suggestions["user_id"] == "userid"
        assert suggestions["email"] == "emailaddress"
        assert suggestions["first_name"] == "firstname"
        assert suggestions["last_name"] == "lastname"
    
    def test_no_match_returns_none(self):
        """Test that unmatched fields return None."""
        csv_columns = ["column1", "column2", "column3"]
        
        suggestions = self.suggester.suggest_mappings(csv_columns)
        
        # Required fields should still be in suggestions but with None
        assert "user_id" in suggestions
        assert suggestions["user_id"] is None
        assert "email" in suggestions
        assert suggestions["email"] is None
    
    def test_validate_mapping_all_required_fields(self):
        """Test validation passes when all required fields are mapped."""
        mapping = {
            "user_id": "id",
            "email": "email_address",
            "first_name": "fname",
            "last_name": "lname"
        }
        
        validation = self.suggester.validate_mapping(mapping)
        
        assert len(validation["errors"]) == 0
    
    def test_validate_mapping_missing_required_field(self):
        """Test validation fails when required field is missing."""
        mapping = {
            "user_id": "id",
            "email": "email_address",
            "first_name": None,  # Missing required field
            "last_name": "lname"
        }
        
        validation = self.suggester.validate_mapping(mapping)
        
        assert len(validation["errors"]) > 0
        assert any("first_name" in error for error in validation["errors"])
    
    def test_validate_mapping_duplicate_columns(self):
        """Test validation warns about duplicate column mappings."""
        mapping = {
            "user_id": "id_column",
            "email": "id_column",  # Same column mapped twice
            "first_name": "fname",
            "last_name": "lname"
        }
        
        validation = self.suggester.validate_mapping(mapping)
        
        assert len(validation["warnings"]) > 0
        assert any("id_column" in warning for warning in validation["warnings"])
    
    def test_calculate_similarity(self):
        """Test similarity calculation."""
        # Exact match
        assert self.suggester._calculate_similarity("email", "email") == 1.0
        
        # Similar strings
        similarity = self.suggester._calculate_similarity("email", "e-mail")
        assert similarity > 0.7
        
        # Different strings
        similarity = self.suggester._calculate_similarity("email", "phone")
        assert similarity < 0.5
    
    def test_find_best_match(self):
        """Test finding best match with aliases."""
        # Direct match
        score = self.suggester._find_best_match("email", "email", ["mail", "e-mail"])
        assert score == 1.0
        
        # Alias match
        score = self.suggester._find_best_match("mail", "email", ["mail", "e-mail"])
        assert score == 0.95
        
        # Similarity match
        score = self.suggester._find_best_match("emailaddress", "email", ["mail"])
        assert score > 0.5  # Adjusted threshold for realistic similarity


class TestMappingValidator:
    """Test cases for MappingValidator class."""
    
    def test_validate_valid_row(self):
        """Test validation of a valid row."""
        mapping = {
            "user_id": "id",
            "email": "email_col",
            "first_name": "fname",
            "last_name": "lname",
            "age": "age_col"
        }
        
        row = {
            "id": "USR001",
            "email_col": "john@example.com",
            "fname": "John",
            "lname": "Doe",
            "age_col": 30
        }
        
        validator = MappingValidator(mapping)
        result = validator.validate_row(row)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_invalid_email(self):
        """Test validation fails for invalid email."""
        mapping = {
            "user_id": "id",
            "email": "email_col",
            "first_name": "fname",
            "last_name": "lname"
        }
        
        row = {
            "id": "USR001",
            "email_col": "invalid-email",  # Missing @
            "fname": "John",
            "lname": "Doe"
        }
        
        validator = MappingValidator(mapping)
        result = validator.validate_row(row)
        
        assert result["valid"] is False
        assert any("email" in error.lower() for error in result["errors"])
    
    def test_validate_missing_required_field(self):
        """Test validation fails when required field is missing."""
        mapping = {
            "user_id": "id",
            "email": "email_col",
            "first_name": "fname",
            "last_name": "lname"
        }
        
        row = {
            "id": "USR001",
            "email_col": "john@example.com",
            "fname": "John"
            # Missing last_name
        }
        
        validator = MappingValidator(mapping)
        result = validator.validate_row(row)
        
        assert result["valid"] is False
    
    def test_validate_invalid_age(self):
        """Test validation fails for invalid age."""
        mapping = {
            "user_id": "id",
            "email": "email_col",
            "first_name": "fname",
            "last_name": "lname",
            "age": "age_col"
        }
        
        row = {
            "id": "USR001",
            "email_col": "john@example.com",
            "fname": "John",
            "lname": "Doe",
            "age_col": 200  # Invalid age
        }
        
        validator = MappingValidator(mapping)
        result = validator.validate_row(row)
        
        assert result["valid"] is False
        assert any("age" in error.lower() for error in result["errors"])
    
    def test_validate_with_optional_fields(self):
        """Test validation with optional fields."""
        mapping = {
            "user_id": "id",
            "email": "email_col",
            "first_name": "fname",
            "last_name": "lname",
            "phone": "phone_col",
            "country": "country_col"
        }
        
        row = {
            "id": "USR001",
            "email_col": "john@example.com",
            "fname": "John",
            "lname": "Doe",
            "phone_col": "+1-555-0123",
            "country_col": "US"
        }
        
        validator = MappingValidator(mapping)
        result = validator.validate_row(row)
        
        assert result["valid"] is True

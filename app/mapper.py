"""
Intelligent mapping suggestion engine for CSV columns to schema fields.
"""
from typing import Dict, List, Optional
from difflib import SequenceMatcher
from app import column_classifier
from app.schema import SCHEMA_FIELDS, get_required_fields
import pandas as pd
import re
from app.column_classifier import ColumnClassifier

class MappingSuggester:
    """Suggests mappings from CSV columns to schema fields."""
    
    SIMILARITY_THRESHOLD = 0.6  # Minimum similarity score for auto-mapping
    
    def __init__(self):
        """Initialize the mapping suggester."""
        self.schema_fields = SCHEMA_FIELDS
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        # Normalize strings: lowercase and remove special characters
        s1 = str1.lower().replace('_', '').replace('-', '').replace(' ', '')
        s2 = str2.lower().replace('_', '').replace('-', '').replace(' ', '')
        
        return SequenceMatcher(None, s1, s2).ratio()
    
    def _find_best_match(self, csv_column: str, schema_field: str, aliases: List[str]) -> float:
        # Check exact match first
        csv_lower = csv_column.lower()
        if csv_lower == schema_field.lower():
            return 1.0
        
        # Check aliases
        for alias in aliases:
            if csv_lower == alias.lower():
                return 0.95
        
        # Calculate similarity with field name
        max_similarity = self._calculate_similarity(csv_column, schema_field)
        
        # Calculate similarity with aliases
        for alias in aliases:
            similarity = self._calculate_similarity(csv_column, alias)
            max_similarity = max(max_similarity, similarity)
        
        return max_similarity

    def _content_based_score(self, schema_field: str, series: pd.Series) -> float:
        score = 0.0
        
        # Assign high score only if the content strongly matches the field type
        if schema_field == "email" and ColumnClassifier.is_email(series):
            score = max(score, 0.95) # Highest priority for email
        elif schema_field == "phone" and ColumnClassifier.is_phone_number(series):
            score = max(score, 0.90) # High priority for phone
        elif schema_field == "created_at" and ColumnClassifier.is_date(series):
            score = max(score, 0.85)  
        elif schema_field == "age" and ColumnClassifier.is_age(series):
            score = max(score, 0.85)  
        elif schema_field == "user_id" and ColumnClassifier.is_user_id(series):
            score = max(score, 0.85)  
        elif schema_field == "status" and ColumnClassifier.is_status_code(series):
            score = max(score, 0.85) 
        
        # If the field is 'user_id' (string/ID) but the content is a date, reduce the score.
        if schema_field == "user_id" and ColumnClassifier.is_date(series):
            score = 0.1 # Low score if it looks like a date

        # If the field is 'user_id' (string/ID) but the content is age value, reduce the score.
        if schema_field == "user_id" and ColumnClassifier.is_age(series):
            score = 0.1 # Low score if it looks like age
        
        if schema_field == "phone" and ColumnClassifier.is_date(series):
            score = 0.1 # Low score if it looks like a date
                
        return score

    def suggest_mappings(self, csv_columns: List[str], sample_data: Optional[pd.DataFrame] = None) -> Dict[str, Optional[str]]:
        suggestions = {}
        used_csv_columns = set()
        
        # Combine name-based and content-based scores
        def get_combined_score(schema_field, csv_col, metadata, sample_data):
            name_score = self._find_best_match(csv_col, schema_field, metadata["aliases"])
            content_score = 0.0
            
            if sample_data is not None and csv_col in sample_data.columns:
                content_score = self._content_based_score(schema_field, sample_data[csv_col])
            
            # If the column name is generic (Column_X), rely heavily on content score.
            if csv_col.lower().startswith("column_"):
                return content_score
            
            # For named columns, combine name and content scores
            if schema_field in ["email", "phone", "created_at"] and content_score > 0.0:
                # Use a weighted average or max to combine, prioritizing content for these types
                return max(name_score * 0.5, content_score)
            
            return name_score

        # First pass: Find high-confidence matches for required fields
        for schema_field, metadata in self.schema_fields.items():
            if not metadata["required"]:
                continue
            
            best_match = None
            best_score = 0.0
            
            for csv_col in csv_columns:
                if csv_col in used_csv_columns:
                    continue
                
                score = get_combined_score(schema_field, csv_col, metadata, sample_data)
                
                if score > best_score:
                    best_score = score
                    best_match = csv_col
            
            if best_score >= self.SIMILARITY_THRESHOLD:
                suggestions[schema_field] = best_match
                used_csv_columns.add(best_match)
            else:
                suggestions[schema_field] = None
        
        # Second pass: Find matches for optional fields
        for schema_field, metadata in self.schema_fields.items():
            if metadata["required"]:
                continue
            
            best_match = None
            best_score = 0.0
            
            for csv_col in csv_columns:
                if csv_col in used_csv_columns:
                    continue
                
                score = get_combined_score(schema_field, csv_col, metadata, sample_data)
                
                if score > best_score:
                    best_score = score
                    best_match = csv_col
            
            if best_score >= self.SIMILARITY_THRESHOLD:
                suggestions[schema_field] = best_match
                used_csv_columns.add(best_match)
            else:
                suggestions[schema_field] = None
        
        return suggestions
    
    def validate_mapping(self, mapping: Dict[str, Optional[str]]) -> Dict[str, List[str]]:
        errors = []
        warnings = []
        
        # Check that all required fields are mapped
        required_fields = get_required_fields()
        for field in required_fields:
            if field not in mapping or mapping[field] is None or mapping[field] == "":
                errors.append(f"Required field '{field}' is not mapped")
        
        # Check for duplicate mappings (same CSV column mapped to multiple schema fields)
        csv_columns_used = {}
        for schema_field, csv_column in mapping.items():
            if csv_column and csv_column != "":
                if csv_column in csv_columns_used:
                    warnings.append(
                        f"CSV column '{csv_column}' is mapped to multiple schema fields: "
                        f"'{csv_columns_used[csv_column]}' and '{schema_field}'"
                    )
                else:
                    csv_columns_used[csv_column] = schema_field
        
        return {
            "errors": errors,
            "warnings": warnings
        }


class MappingValidator:
    """Validates data against mapped schema."""
    
    def __init__(self, mapping: Dict[str, str]):
        self.mapping = mapping
    
    def validate_row(self, row: Dict) -> Dict:
        from app.schema import UserSchema
        from pydantic import ValidationError
        
        # Map CSV row to schema fields
        mapped_data = {}
        for schema_field, csv_column in self.mapping.items():
            if csv_column and csv_column in row:
                value = row[csv_column]
                # Handle empty strings and NaN values
                if pd.isna(value) or value == "":
                    mapped_data[schema_field] = None
                else:
                    mapped_data[schema_field] = value
            else:
                mapped_data[schema_field] = None
        
        # Validate against schema
        try:
            UserSchema(**mapped_data)
            return {
                "valid": True,
                "errors": []
            }
        except ValidationError as e:
            return {
                "valid": False,
                "errors": [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            }

import pandas as pd

"""
CSV file handling utilities for parsing and processing CSV files.
"""
import pandas as pd
import io
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class CSVHandler:
    """Handles CSV file parsing and column detection."""
    
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB in bytes
    SAMPLE_SIZE = 1000  # Number of rows to sample for preview
    
    def __init__(self, file_content: bytes, filename: str):
        """
        Initialize CSV handler with file content.
        
        Args:
            file_content: Raw bytes of the CSV file
            filename: Original filename
        """
        self.file_content = file_content
        self.filename = filename
        self.df: Optional[pd.DataFrame] = None
        self.has_header: bool = True
        self.columns: List[str] = []
        
        # Save file to uploads folder
        uploads_dir = Path(__file__).parent.parent / "uploads"
        uploads_dir.mkdir(exist_ok=True)
        file_path = uploads_dir / filename
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
    def validate_file_size(self) -> Tuple[bool, Optional[str]]:
        """
        Validate that file size is within limits.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        file_size = len(self.file_content)
        if file_size > self.MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            return False, f"File size ({size_mb:.2f} MB) exceeds maximum allowed size (100 MB)"
        return True, None
    
    def detect_header(self) -> bool:
        df = pd.read_csv(io.BytesIO(self.file_content), header=None, on_bad_lines='skip', nrows=2)
        if len(df) < 2:
            return True  # Default to header if only one row

        def type_vector(row):
            return [1 if is_numeric(val) else 0 for val in row]

        def is_numeric(val):
            try:
                float(val)
                return True
            except:
                return False

        vec0 = np.array(type_vector(df.iloc[0])).reshape(1, -1)
        vec1 = np.array(type_vector(df.iloc[1])).reshape(1, -1)

        similarity = cosine_similarity(vec0, vec1)[0][0]
        print(f"Row similarity score: {similarity:.2f}")

        # High similarity → likely no header
        return bool(similarity < 0.8)  # If rows differ, assume header

    def parse(self) -> Tuple[bool, Optional[str]]:
        """
        Parse the CSV file and detect columns.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate file size first
            is_valid, error = self.validate_file_size()
            if not is_valid:
                return False, error
            
            # Detect if file has header
            self.has_header = self.detect_header()
            
            # Parse CSV
            if self.has_header:
                self.df = pd.read_csv(io.BytesIO(self.file_content), on_bad_lines='skip')
                self.columns = list(self.df.columns)
            else:
                self.df = pd.read_csv(io.BytesIO(self.file_content), header=None, on_bad_lines='skip')
                # Generate column names: Column_0, Column_1, etc.
                self.columns = [f"Column_{i}" for i in range(len(self.df.columns))]
                self.df.columns = self.columns
            
            # Clean column names (strip whitespace)
            self.columns = [str(col).strip() for col in self.columns]
            self.df.columns = self.columns
            
            return True, None
            
        except pd.errors.EmptyDataError:
            return False, "CSV file is empty"
        except pd.errors.ParserError as e:
            return False, f"Failed to parse CSV: {str(e)}"
        except Exception as e:
            return False, f"Error processing CSV file: {str(e)}"
    
    def get_preview(self, num_rows: int = 5) -> List[Dict]:
        """
        Get a preview of the CSV data.
        
        Args:
            num_rows: Number of rows to include in preview
            
        Returns:
            List of dictionaries representing rows
        """
        if self.df is None:
            return []
        
        preview_df = self.df.head(num_rows)
        return preview_df.to_dict(orient='records')
    
    def get_data(self, skip_rows: int = 0, num_rows: int = 10) -> List[Dict]:
        """
        Gets the CSV data with optional row skipping and limiting.
        
        Args:
            skip_rows: Number of rows to skip from the beginning (default: 0)
            num_rows: Number of rows to return after skipping (default: 10)
        
        Returns:
            List of dictionaries representing rows
        """
        if self.df is None:
            return []
        
        # Skip rows and take the specified number of rows
        data_df = self.df.iloc[skip_rows:skip_rows + num_rows]
        return data_df.to_dict(orient='records')
    
    def get_column_info(self) -> List[Dict]:
        """
        Get information about each column.
        
        Returns:
            List of dictionaries with column metadata
        """
        if self.df is None:
            return []
        
        column_info = []
        for col in self.columns:
            info = {
                "name": col,
                "type": str(self.df[col].dtype),
                "non_null_count": int(self.df[col].count()),
                "null_count": int(self.df[col].isna().sum()),
                "sample_values": self.df[col].dropna().head(3).tolist()
            }
            column_info.append(info)
        
        return column_info
    
    def get_sample_data(self, num_rows: int = 100) -> pd.DataFrame:
        """
        Get a sample of the CSV data for content analysis.
        
        Args:
            num_rows: Number of rows to sample
            
        Returns:
            A pandas DataFrame containing the sample data.
        """
        if self.df is None:
            return pd.DataFrame()
        
        return self.df.head(num_rows)

    def get_row_count(self) -> int:
        """Get total number of rows in the CSV."""
        return len(self.df) if self.df is not None else 0

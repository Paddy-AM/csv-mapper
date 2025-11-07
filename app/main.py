"""
FastAPI application for CSV ingestion and mapping tool.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, List
import os

from app.csv_handler import CSVHandler
from app.mapper import MappingSuggester, MappingValidator
from app.mapping_storage import MappingStorage
from app.schema import SCHEMA_FIELDS, get_required_fields, get_all_fields
import numpy as np
import pandas as pd
import math

app = FastAPI(
    title="CSV Ingestion and Mapping Tool",
    description="Upload CSV files and map them to a predefined schema",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
mapping_storage = MappingStorage(storage_dir="mappings")
mapping_suggester = MappingSuggester()

# In-memory storage for uploaded files
uploaded_files: Dict[str, CSVHandler] = {}

class MappingRequest(BaseModel):
    """Request model for mapping configuration."""
    file_id: str
    mapping: Dict[str, Optional[str]]


class SaveMappingRequest(BaseModel):
    """Request model for saving a mapping template."""
    name: str
    description: str
    mapping: Dict[str, Optional[str]]


class ValidateRequest(BaseModel):
    """Request model for validating a mapping."""
    file_id: str
    mapping: Dict[str, Optional[str]]
    max_error_rows: Optional[int] = 5


def sanitize_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None  # or a placeholder like "N/A"
        return obj
    else:
        return obj


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI."""
    html_path = os.path.join("templates", "index.html")
    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            return f.read()
    return """
    <html>
        <head><title>CSV Mapping Tool</title></head>
        <body>
            <h1>CSV Ingestion and Mapping Tool</h1>
            <p>API is running. Access the API documentation at <a href="/docs">/docs</a></p>
        </body>
    </html>
    """

@app.get("/api/schema")
async def get_schema():
    """
    Get the predefined schema information.
    
    Returns:
        Schema fields with metadata
    """
    return {
        "fields": SCHEMA_FIELDS,
        "required_fields": get_required_fields(),
        "all_fields": get_all_fields()
    }


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a CSV file for processing.
    
    Args:
        file: CSV file to upload
        
    Returns:
        File metadata and suggested mappings
    """
    # Read file content
    content = await file.read()
    
    # Create CSV handler
    handler = CSVHandler(content, file.filename)
    
    # Validate and parse
    success, error = handler.parse()
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    # Generate file ID
    file_id = f"file_{len(uploaded_files)}"
    uploaded_files[file_id] = handler
    
    # Get column information
    columns = handler.columns
    column_info = handler.get_column_info()
    preview = handler.get_preview()
    
    # Suggest mappings
    sample_data = handler.get_sample_data(num_rows=100)
    suggested_mappings = mapping_suggester.suggest_mappings(columns, sample_data)
    
    # Validate suggested mappings
    validation = mapping_suggester.validate_mapping(suggested_mappings)
    
    # Return response: Sanitized JSON to handle NaN and inf values
    return sanitize_json({
        "file_id": file_id,
        "filename": file.filename,
        "row_count": handler.get_row_count(),
        "has_header": handler.has_header,
        "columns": columns,
        "column_info": column_info,
        "preview": preview,
        "suggested_mappings": suggested_mappings,
        "validation": validation
    })


@app.post("/api/validate")
async def validate_mapping(request: ValidateRequest):
    """
    Validate a mapping configuration.
    
    Args:
        request: Validation request with file_id, mapping, and optional max_error_rows
        
    Returns:
        Validation results
    """
    # Get file handler
    if request.file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    handler = uploaded_files[request.file_id]
    
    # Validate mapping structure
    validation = mapping_suggester.validate_mapping(request.mapping)
    row_errors = []
    if not validation["errors"]:
        # Validate data against schema
        validator = MappingValidator(request.mapping)
        total_rows = len(handler.df)
        batch_size = 10
        current_row = 0
        
        # Process rows in batches of 10
        while current_row < total_rows:
            batch_data = handler.get_data(skip_rows=current_row, num_rows=batch_size)
            
            if not batch_data:  # No more data
                break
            
            for idx, row in enumerate(batch_data):
                result = validator.validate_row(row)
                if not result["valid"]:
                    row_errors.append({
                        "row": current_row + idx + 1,
                        "errors": result["errors"]
                    })
                    if len(row_errors) >= request.max_error_rows:
                        break
            
            # Break outer loop if max errors reached
            if len(row_errors) >= request.max_error_rows:
                break
            
            current_row += batch_size
    
    return {
        "valid": len(validation["errors"]) == 0 and len(row_errors) == 0,
        "errors": validation["errors"],
        "warnings": validation["warnings"],
        "row_errors": row_errors[:request.max_error_rows]  # Return configurable number of row errors
    }


@app.post("/api/mappings/save")
async def save_mapping(request: SaveMappingRequest):
    """
    Save a mapping template for future use.
    
    Args:
        request: Save mapping request
        
    Returns:
        Saved mapping ID
    """
    validation = mapping_suggester.validate_mapping(request.mapping)
    
    # Check for structural errors (required fields not mapped)
    if validation["errors"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot save invalid mapping: {', '.join(validation['errors'])}"
        )
    
    # Filter out None values for storage, as the mapping storage expects Dict[str, str]
    # The structural validation already passed, so we only keep mapped fields.
    clean_mapping = {k: v for k, v in request.mapping.items() if v is not None and v != ""}
    
    mapping_id = mapping_storage.save_mapping(
        name=request.name,
        description=request.description,
        mapping=clean_mapping
    )
    
    return {
        "mapping_id": mapping_id,
        "message": "Mapping saved successfully"
    }


@app.get("/api/mappings")
async def list_mappings():
    """
    List all saved mapping templates.
    
    Returns:
        List of saved mappings
    """
    mappings = mapping_storage.list_mappings()
    return {"mappings": mappings}


@app.get("/api/mappings/{mapping_id}")
async def get_mapping(mapping_id: str):
    """
    Get a specific mapping template.
    
    Args:
        mapping_id: ID of the mapping to retrieve
        
    Returns:
        Mapping details
    """
    mapping = mapping_storage.get_mapping(mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    return mapping


@app.delete("/api/mappings/{mapping_id}")
async def delete_mapping(mapping_id: str):
    """
    Delete a saved mapping template.
    
    Args:
        mapping_id: ID of the mapping to delete
        
    Returns:
        Success message
    """
    success = mapping_storage.delete_mapping(mapping_id)
    if not success:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    return {"message": "Mapping deleted successfully"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

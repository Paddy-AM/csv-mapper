# AIBIDIA: CSV Ingestion and Mapping Tool

A robust web application for uploading CSV files and mapping their columns to a predefined schema. This tool provides intelligent mapping suggestions, comprehensive validation, and reusable mapping templates.

## Features

### Core Functionality

**File Upload**
- Supports CSV files up to 100 MB in size. 
- Automatically detects whether files have headers
- Generates column names for headerless files
- Provides file preview and column information

**Intelligent Column Mapping**
- Auto-suggests mappings based on column names and aliases
- Uses fuzzy matching for similar column names
- Allows manual adjustment of all mappings
- Supports both required and optional schema fields

**Comprehensive Validation**
- Validates that all required fields are mapped
- Checks data against schema rules (email format, age range, etc.)
- Provides clear, actionable error messages
- Warns about duplicate column mappings

**Reusable Mapping Templates**
- Save successful mappings for future use
- Load previously saved mappings
- Manage mapping templates (list, retrieve, delete)
- Includes metadata (name, description, timestamps)

### Technology Stack

- **Backend**: FastAPI (Python web framework)
- **Data Processing**: pandas (CSV handling and analysis)
- **Validation**: Pydantic (schema validation)
- **Frontend**: Vanilla JavaScript with modern CSS
- **Testing**: pytest with comprehensive test coverage

## Installation and Setup

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Installation Steps

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify installation**
   ```bash
   python -c "import fastapi, pandas, pydantic; print('All dependencies installed successfully')"
   ```

## Running the Application

### Start the Server

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The application will be available at:
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Using the Web Interface

1. **Upload CSV File**
   - Click "Choose File" and select your CSV file
   - Click "Upload File" to process it
   - View file preview and column information

2. **Map Columns**
   - Review auto-suggested mappings
   - Adjust mappings using dropdown menus
   - Required fields are marked with *

3. **Validate Mapping**
   - Click "Validate Mapping" to check your configuration
   - Review any errors or warnings
   - Fix issues and re-validate

4. **Save Mapping Template** (Optional)
   - Click "Save Mapping Template"
   - Enter a name and description
   - Use the template for similar files in the future

5. **Load Saved Mapping** (Optional)
   - Click "Load Saved Mapping"
   - Select a previously saved template
   - Mappings will be automatically applied

## Running Tests

### Execute All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Files

```bash
# Test CSV handler
pytest tests/test_csv_handler.py -v

# Test mapping logic
pytest tests/test_mapper.py -v

# Test storage functionality
pytest tests/test_mapping_storage.py -v

# Test API endpoints
pytest tests/test_api.py -v
```

### Run with Coverage Report

```bash
pytest tests/ --cov=app --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

### Expected Test Results

All tests should pass. The test suite includes:
- **CSV Handler Tests**: 10 tests covering file parsing, validation, and edge cases
- **Mapper Tests**: 15 tests for mapping suggestions and validation
- **Storage Tests**: 11 tests for saving, retrieving, and managing mappings
- **API Tests**: 15 tests for all API endpoints and integration scenarios

**Total**: 51 comprehensive test cases

## API Documentation

### Endpoints

#### `GET /api/schema`
Get the predefined schema information including all fields, required fields, and metadata.

**Response:**
```json
{
  "fields": {
    "user_id": {
      "required": true,
      "type": "string",
      "description": "Unique user identifier",
      "aliases": ["id", "userid", "user_identifier"]
    },
    ...
  },
  "required_fields": ["user_id", "email", "first_name", "last_name"],
  "all_fields": ["user_id", "email", "first_name", "last_name", "age", "phone", "country", "status", "created_at"]
}
```

#### `POST /api/upload`
Upload a CSV file for processing.

**Request:**
- Form data with file upload

**Response:**
```json
{
  "file_id": "file_0",
  "filename": "users.csv",
  "row_count": 100,
  "has_header": true,
  "columns": ["id", "email", "fname", "lname"],
  "column_info": [...],
  "preview": [...],
  "suggested_mappings": {
    "user_id": "id",
    "email": "email",
    "first_name": "fname",
    "last_name": "lname"
  },
  "validation": {
    "errors": [],
    "warnings": []
  }
}
```

#### `POST /api/validate`
Validate a mapping configuration and returns max error rows.

**Request:**
```json
{
  "file_id": "file_0",
  "mapping": {
    "user_id": "id",
    "email": "email",
    "first_name": "fname",
    "last_name": "lname"
  },
  "max_error_rows": 5 //optional
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "row_errors": []
}
```

#### `POST /api/mappings/save`
Save a mapping template.

**Request:**
```json
{
  "name": "Standard User Import",
  "description": "Mapping for standard user CSV format",
  "mapping": {
    "user_id": "id",
    "email": "email",
    "first_name": "fname",
    "last_name": "lname"
  }
}
```

**Response:**
```json
{
  "mapping_id": "a1b2c3d4e5f6",
  "message": "Mapping saved successfully"
}
```

#### `GET /api/mappings`
List all saved mapping templates.

**Response:**
```json
{
  "mappings": [
    {
      "id": "a1b2c3d4e5f6",
      "name": "Standard User Import",
      "description": "Mapping for standard user CSV format",
      "created_at": "2024-01-01T12:00:00"
    }
  ]
}
```

#### `GET /api/mappings/{mapping_id}`
Get a specific mapping template.

**Response:**
```json
{
  "id": "a1b2c3d4e5f6",
  "name": "Standard User Import",
  "description": "Mapping for standard user CSV format",
  "mapping": {
    "user_id": "id",
    "email": "email",
    "first_name": "fname",
    "last_name": "lname"
  },
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

#### `DELETE /api/mappings/{mapping_id}`
Delete a mapping template.

**Response:**
```json
{
  "message": "Mapping deleted successfully"
}
```

## Schema Definition

The predefined schema includes the following fields:

### Required Fields
- **user_id**: Unique user identifier (string)
- **email**: User email address (string, must contain @)
- **first_name**: User's first name (string)
- **last_name**: User's last name (string)

### Optional Fields
- **age**: User's age (integer, 0-150)
- **phone**: Phone number (string)
- **country**: Country code or name (string)
- **status**: Account status (string: "active", "inactive", or "pending")
- **created_at**: Account creation date (string)

## Project Structure

```
csv_mapping_tool/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── schema.py            # Schema definition
│   ├── csv_handler.py       # CSV parsing and processing
│   ├── mapper.py            # Mapping suggestion and validation
│   ├── column_classifier.py # Classifier for columns
│   └── mapping_storage.py   # Storage for reusable mappings
├── tests/
│   ├── __init__.py
│   ├── test_csv_handler.py  # CSV handler tests
│   ├── test_mapper.py       # Mapper tests
│   ├── test_mapping_storage.py  # Storage tests
│   └── test_api.py          # API integration tests
├── static/
│   ├── style.css            # Frontend styles
│   └── app.js               # Frontend JavaScript
├── templates/
│   └── index.html           # Main UI template
├── mappings/                # Saved mapping templates (created at runtime)
├── uploads/                 # Uploaded files (created at runtime)
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Design Decisions

### Architecture
- **FastAPI** was chosen for its modern async support, automatic API documentation, and excellent performance
- **Pydantic** provides robust schema validation with clear error messages
- **pandas** efficiently handles large CSV files and provides powerful data manipulation capabilities

### Mapping Intelligence
- The mapping suggester uses multiple strategies:
  1. Exact name matching (case-insensitive)
  2. Alias matching for common variations
  3. Fuzzy string similarity for close matches
- Similarity threshold of 0.6 balances accuracy and recall

### Storage
- Mapping templates are stored as JSON files for simplicity and human readability
- Each mapping has a unique ID generated from name and timestamp

### Validation
- Two-level validation:
  1. Structural validation (all required fields mapped)
  2. Data validation (values conform to schema rules)
- Sample validation on first 5 rows provides quick feedback without processing entire file

## Edge Cases Handled

1. **Files without headers**: Automatically generates column names (Column_0, Column_1, etc.)
2. **Large files**: Validates file size before processing (100 MB limit)
3. **Empty files**: Returns clear error message
4. **Malformed CSV**: Gracefully handles parsing errors
5. **Missing values**: Treats empty strings and NaN as None for optional fields
6. **Duplicate mappings**: Warns when same CSV column is mapped to multiple schema fields
7. **Invalid data**: Validates email format, age range, status values, etc.

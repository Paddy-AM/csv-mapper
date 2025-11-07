"""
Predefined schema definition for CSV mapping validation.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime
import re

class UserSchema(BaseModel):
    """
    Predefined schema that CSV data must be mapped to.
    This represents a typical user record with various field types and validation rules.
    """
    # Required fields
    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    
    # Optional fields
    age: Optional[int] = Field(None, description="User's age", ge=0, le=150)
    phone: Optional[str] = Field(None, description="Phone number")
    country: Optional[str] = Field(None, description="Country code or name")
    status: Optional[str] = Field(None, description="User account status (active/inactive/pending)")
    created_at: Optional[str] = Field(None, description="Account creation date")
    
    @validator('phone', pre=True)
    def validate_phone(cls, v):
        """Validate phone number format using regex."""
        if v is None:
            return v

        phone_str = str(v).strip()
        # Example: allows +44 1234567890, (123) 456-7890, 123-456-7890, etc.
        pattern = re.compile(r"^\+?\d{1,4}?[\s\-\.]?\(?\d{1,4}?\)?[\s\-\.]?\d{1,4}[\s\-\.]?\d{1,9}$")

        if not pattern.match(phone_str):
            raise ValueError("Invalid phone number format")

        return phone_str

    @validator('status', pre=True)
    def validate_status(cls, v):
        """Validate status against allowed values, case-insensitively."""
        if v is None:
            return v
        
        allowed_statuses = ["active", "inactive", "pending"]
        v_lower = str(v).lower()
        
        if v_lower not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        
        return v_lower

    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """Ensure user_id is not empty."""
        if not v or not v.strip():
            raise ValueError('user_id cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "USR001",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "age": 30,
                "phone": "+1-555-0123",
                "country": "US",
                "status": "active",
                "created_at": "2024-01-01"
            }
        }


# Schema metadata for UI and mapping suggestions
SCHEMA_FIELDS = {
    "user_id": {
        "required": True,
        "type": "string",
        "description": "Unique user identifier",
        "aliases": ["id", "userid", "user_identifier", "customer_id", "uid"]
    },
    "email": {
        "required": True,
        "type": "string",
        "description": "User email address",
        "aliases": ["email_address", "mail", "e-mail", "contact_email"]
    },
    "first_name": {
        "required": True,
        "type": "string",
        "description": "User's first name",
        "aliases": ["firstname", "fname", "given_name", "forename"]
    },
    "last_name": {
        "required": True,
        "type": "string",
        "description": "User's last name",
        "aliases": ["lastname", "lname", "surname", "family_name"]
    },
    "age": {
        "required": False,
        "type": "integer",
        "description": "User's age (0-150)",
        "aliases": ["years", "age_years", "user_age"]
    },
    "phone": {
        "required": False,
        "type": "string",
        "description": "Phone number",
        "aliases": ["phone_number", "telephone", "mobile", "contact_number", "tel"]
    },
    "country": {
        "required": False,
        "type": "string",
        "description": "Country code or name",
        "aliases": ["country_code", "nation", "location", "residence"]
    },
    "status": {
        "required": False,
        "type": "string",
        "description": "User account status (active/inactive/pending)",
        "aliases": ["account_status", "user_status", "state"]
    },
    "created_at": {
        "required": False,
        "type": "string",
        "description": "Account creation date",
        "aliases": ["creation_date", "created", "signup_date", "registration_date", "date_created"]
    }
}


def get_required_fields():
    """Return list of required field names."""
    return [field for field, meta in SCHEMA_FIELDS.items() if meta["required"]]


def get_all_fields():
    """Return list of all field names."""
    return list(SCHEMA_FIELDS.keys())

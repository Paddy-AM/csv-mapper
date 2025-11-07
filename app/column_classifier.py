import pandas as pd
import re

class ColumnClassifier:
    @staticmethod
    def is_email(series: pd.Series) -> bool:
        """Check if a series contains email addresses."""
        email_regex = re.compile("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63}$")
        non_null = series.dropna().astype(str)
        if non_null.empty:
            return False
        match_count = non_null.str.match(email_regex).sum()
        return match_count / len(non_null) > 0.8

    @staticmethod
    def is_phone_number(series: pd.Series) -> bool:
        """Check if a series contains phone numbers."""
        phone_regex = re.compile(r"^\+?(\d[\s\-]?)?(\(?\d{2,4}\)?[\s\-]?)?[\d\s\-]{6,15}\d$")
        non_null = series.dropna().astype(str)
        if non_null.empty:
            return False
        match_count = non_null.str.match(phone_regex).sum()
        return match_count / len(non_null) > 0.8

    @staticmethod
    def is_date(series: pd.Series) -> bool:
        """Check if a series contains date-like strings."""
        date_regex =  re.compile(r"^(?:(?:\d{4}[-/]\d{1,2}[-/]\d{1,2})|(?:\d{1,2}[-/]\d{1,2}[-/]\d{4}))$")
        non_null = series.dropna().astype(str)
        if non_null.empty:
            return False
        match_count = non_null.str.match(date_regex).sum()
        return match_count / len(non_null) > 0.8

    @staticmethod
    def is_age(series: pd.Series) -> bool:
        """Check if a series contains age values (0–150)."""
        non_null = series.dropna()
        if non_null.empty:
            return False
        try:
            numeric = pd.to_numeric(non_null, errors='coerce')
            valid = numeric[(numeric >= 0) & (numeric <= 150)]
            return len(valid) / len(non_null) > 0.8
        except Exception:
            return False

    @staticmethod
    def is_user_id(series: pd.Series) -> bool:
        """Check if a series contains unique user identifiers."""
        non_null = series.dropna().astype(str)
        if non_null.empty:
            return False
        unique_ratio = non_null.nunique() / len(non_null)
        # Heuristic: mostly unique, alphanumeric, no obvious semantic pattern
        alphanumeric_ratio = non_null.str.match(r"^[a-zA-Z0-9\-_]+$").sum() / len(non_null)
        return unique_ratio > 0.9 and alphanumeric_ratio > 0.8

    @staticmethod
    def is_status_code(series: pd.Series) -> bool:
        """Check if a series contains status values: active, inactive, pending (case-insensitive)."""
        non_null = series.dropna().astype(str).str.strip().str.lower()
        if non_null.empty:
            return False

        valid_statuses = {"active", "inactive", "pending"}
        match_ratio = non_null.isin(valid_statuses).sum() / len(non_null)

        # Heuristic: consider it a status column if ≥80% of values match expected statuses
        return match_ratio >= 0.8
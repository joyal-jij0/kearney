"""Schemas for file upload and response models."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    table_name: str = Field(..., description="Name of the created table")
    rows_inserted: int = Field(..., description="Number of rows inserted")
    columns: List[str] = Field(..., description="List of column names")
    total_rows: int = Field(..., description="Total number of rows in the file")
    total_columns: int = Field(..., description="Total number of columns in the file")


class TableDataResponse(BaseModel):
    """Response model for table data."""
    table_name: str
    data: List[Dict[str, Any]]
    count: int


class ColumnInfo(BaseModel):
    """Information about a table column."""
    name: str
    type: str
    nullable: bool
    default: Optional[Any] = None
    primary_key: bool


class TableInfo(BaseModel):
    """Information about a database table."""
    table_name: str
    columns: List[ColumnInfo]
    row_count: int


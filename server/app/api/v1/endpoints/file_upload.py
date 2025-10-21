"""API endpoints for file upload and data management."""
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Query
from app.schemas import (
    ApiResponse,
    ApiError,
    FileUploadResponse,
)

from app.services import file_service

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=ApiResponse[FileUploadResponse])
async def upload_file(
    file: UploadFile = File(...),
    table_name: Optional[str] = Query(None, description="Custom table name (optional)")
):
    """
    Upload a CSV or Excel file and store it in SQLite database.
    
    - **file**: CSV or Excel file (.csv, .xlsx, .xls)
    - **table_name**: Optional custom table name. If not provided, derived from filename
    
    Returns information about the uploaded data and created table.
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Process and store file
        result = await file_service.process_and_store_file(
            file_content=file_content,
            filename=file.filename,
            table_name=table_name
        )
        
        return ApiResponse[FileUploadResponse](
            status_code=200,
            data=FileUploadResponse(**result),
            message="File uploaded and stored successfully"
        ).to_response()
    
    except ValueError as e:
        error = ApiError(
            status_code=400,
            message=str(e)
        )
        return error.to_response()
    
    except Exception as e:
        error = ApiError(
            status_code=500,
            message=f"An error occurred while processing the file: {str(e)}"
        )
        return error.to_response()

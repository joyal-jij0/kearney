"""File processing utilities for CSV and Excel files."""
import pandas as pd
from io import BytesIO
from typing import Tuple
from pathlib import Path


class FileProcessor:
    """Processor for CSV and Excel files."""
    
    SUPPORTED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}
    
    @staticmethod
    def is_supported_file(filename: str) -> bool:
        """Check if file type is supported.
        
        Args:
            filename: Name of the file
            
        Returns:
            True if file is supported, False otherwise
        """
        ext = Path(filename).suffix.lower()
        return ext in FileProcessor.SUPPORTED_EXTENSIONS
    
    @staticmethod
    async def read_file_to_dataframe(file_content: bytes, filename: str) -> pd.DataFrame:
        """Read file content and convert to pandas DataFrame.
        
        Args:
            file_content: Binary content of the file
            filename: Name of the file
            
        Returns:
            pandas DataFrame containing file data
            
        Raises:
            ValueError: If file type is not supported or file cannot be read
        """
        ext = Path(filename).suffix.lower()
        
        if ext not in FileProcessor.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}. Supported types: {', '.join(FileProcessor.SUPPORTED_EXTENSIONS)}")
        
        try:
            file_buffer = BytesIO(file_content)
            
            if ext == '.csv':
                df = pd.read_csv(file_buffer)
            elif ext in {'.xlsx', '.xls'}:
                df = pd.read_excel(file_buffer, engine='openpyxl' if ext == '.xlsx' else 'xlrd')
            else:
                raise ValueError(f"Unsupported file extension: {ext}")
            
            return df
        
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")
    
    @staticmethod
    def sanitize_table_name(filename: str) -> str:
        """Create a valid SQL table name from filename.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized table name
        """
        # Remove extension and special characters
        name = Path(filename).stem
        # Replace spaces and special chars with underscores
        name = ''.join(c if c.isalnum() else '_' for c in name)
        # Ensure it starts with a letter
        if name and not name[0].isalpha():
            name = 'table_' + name
        # Lowercase and limit length
        name = name.lower()[:64]
        return name or 'uploaded_data'
    
    @staticmethod
    def infer_sql_type(dtype) -> str:
        """Infer SQL column type from pandas dtype.
        
        Args:
            dtype: pandas dtype
            
        Returns:
            SQL column type
        """
        dtype_str = str(dtype)
        
        if 'int' in dtype_str:
            return 'INTEGER'
        elif 'float' in dtype_str:
            return 'REAL'
        elif 'bool' in dtype_str:
            return 'INTEGER'  # SQLite stores booleans as integers
        elif 'datetime' in dtype_str:
            return 'TEXT'  # SQLite stores dates as text or integers
        else:
            return 'TEXT'

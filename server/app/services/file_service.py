"""Service for handling file uploads and data storage."""
from typing import Dict, Any, List
import pandas as pd
from app.db import db
from app.utils import FileProcessor


class FileService:
    """Service for processing and storing file data."""

    def __init__(self):
        """Initialize file service."""
        self.db = db
        self.file_processor = FileProcessor()

    async def process_and_store_file(
        self,
        file_content: bytes,
        filename: str,
        table_name: str = None
    ) -> Dict[str, Any]:
        """Process file and store data in SQLite.
        
        Args:
            file_content: Binary content of the file
            filename: Name of the file
            table_name: Optional custom table name
            
        Returns:
            Dictionary with processing results
            
        Raises:
            ValueError: If file processing fails
        """
        # Validate file type
        if not self.file_processor.is_supported_file(filename):
            raise ValueError(f"Unsupported file type. Supported: {', '.join(FileProcessor.SUPPORTED_EXTENSIONS)}")

        # Read file to DataFrame
        df = await self.file_processor.read_file_to_dataframe(file_content, filename)

        # Sanitize table name
        if table_name is None:
            table_name = self.file_processor.sanitize_table_name(filename)
        else:
            table_name = self.file_processor.sanitize_table_name(table_name)

        # Create table and insert data
        self._create_table_from_dataframe(df, table_name)
        rows_inserted = self._insert_dataframe_to_table(df, table_name)

        return {
            "table_name": table_name,
            "rows_inserted": rows_inserted,
            "columns": list(df.columns),
            "total_rows": len(df),
            "total_columns": len(df.columns)
        }

    def _create_table_from_dataframe(self, df: pd.DataFrame, table_name: str):
        """Create SQL table from DataFrame schema.
        
        Args:
            df: pandas DataFrame
            table_name: Name of the table to create
        """
        # Drop table if exists
        conn = self.db.get_connection()
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")

        # Build CREATE TABLE statement
        columns = []
        for col_name, dtype in df.dtypes.items():
            # Sanitize column name
            safe_col_name = ''.join(c if c.isalnum() else '_' for c in str(col_name))
            sql_type = self.file_processor.infer_sql_type(dtype)
            columns.append(f"{safe_col_name} {sql_type}")
        
        columns_str = ", ".join(columns)
        create_table_query = f"CREATE TABLE {table_name} ({columns_str})"
        
        conn.execute(create_table_query)
        conn.commit()
    
    def _insert_dataframe_to_table(self, df: pd.DataFrame, table_name: str) -> int:
        """Insert DataFrame data into SQL table.
        
        Args:
            df: pandas DataFrame with data
            table_name: Name of the table
            
        Returns:
            Number of rows inserted
        """
        # Sanitize column names to match table
        df_copy = df.copy()
        df_copy.columns = [''.join(c if c.isalnum() else '_' for c in str(col)) for col in df_copy.columns]

        # Use pandas to_sql for efficient insertion
        conn = self.db.get_connection()
        df_copy.to_sql(table_name, conn, if_exists='append', index=False)

        return len(df_copy)

    def get_table_data(self, table_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve data from a table.
        
        Args:
            table_name: Name of the table
            limit: Maximum number of rows to return
            
        Returns:
            List of rows as dictionaries
        """
        conn = self.db.get_connection()
        cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    def get_all_tables(self) -> List[str]:
        """Get all table names in the database.
        
        Returns:
            List of table names
        """
        return self.db.get_all_tables()

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table information
        """
        conn = self.db.get_connection()

        # Get column information
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = [
            {
                "name": row[1],
                "type": row[2],
                "nullable": not row[3],
                "default": row[4],
                "primary_key": bool(row[5])
            }
            for row in cursor.fetchall()
        ]

        # Get row count
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]

        return {
            "table_name": table_name,
            "columns": columns,
            "row_count": row_count
        }


# Singleton service instance
file_service = FileService()

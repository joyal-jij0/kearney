"""Tool implementations for AI service database operations."""
from typing import Dict, Any, List
import sqlite3
from functools import lru_cache
from app.db import db


class DatabaseTools:
    """Collection of database query tools for AI assistant."""

    def __init__(self):
        """Initialize database tools with database connection."""
        self.db = db

    def list_tables(self) -> List[str]:
        """Get list of all tables in the database."""
        return self.db.get_all_tables()

    def get_database_context(self, include_samples: bool = False, sample_limit: int = 3) -> Dict[str, Any]:
        """Get comprehensive database context in a single call.
        
        This function returns all tables with their schemas, row counts, and optionally sample data.
        This is much more efficient than making multiple separate calls.
        
        Args:
            include_samples: Whether to include sample rows from each table
            sample_limit: Number of sample rows per table
            
        Returns:
            Dictionary with complete database context
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get all tables
            tables = self.db.get_all_tables()

            database_context = {
                "success": True,
                "table_count": len(tables),
                "tables": []
            }

            for table_name in tables:
                # Get schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]

                table_info = {
                    "name": table_name,
                    "row_count": row_count,
                    "column_count": len(columns),
                    "columns": [
                        {
                            "name": col[1],
                            "type": col[2],
                            "not_null": bool(col[3]),
                            "default_value": col[4],
                            "primary_key": bool(col[5])
                        }
                        for col in columns
                    ]
                }

                # Optionally include sample data
                if include_samples and row_count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT ?", (sample_limit,))
                    rows = cursor.fetchall()
                    column_names = [description[0] for description in cursor.description]
                    table_info["sample_data"] = [dict(zip(column_names, row)) for row in rows]

                database_context["tables"].append(table_info)

        except sqlite3.Error as error:
            return {"error": str(error)}

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table schema information
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            schema = {
                "table_name": table_name,
                "columns": [
                    {
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "default_value": col[4],
                        "primary_key": bool(col[5])
                    }
                    for col in columns
                ]
            }
            return schema
        except sqlite3.Error as error:
            return {"error": str(error)}

    def execute_select_query(self, query: str) -> Dict[str, Any]:
        """Execute a SELECT query on the database.
        
        Args:
            query: SQL SELECT query
            
        Returns:
            Dictionary with query results
        """
        # Validate that it's a SELECT query
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT"):
            return {"error": "Only SELECT queries are allowed"}

        # Check for dangerous keywords
        dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE"]
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return {"error": f"Query contains forbidden keyword: {keyword}"}

        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            # Convert rows to list of dictionaries
            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]

            return {
                "success": True,
                "row_count": len(results),
                "columns": columns,
                "data": results
            }
        except sqlite3.Error as error:
            return {"error": str(error)}

    def get_table_sample(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """Get a sample of rows from a table.
        
        Args:
            table_name: Name of the table
            limit: Number of rows to return
            
        Returns:
            Dictionary with sample data
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
            rows = cursor.fetchall()

            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]

            return {
                "success": True,
                "table_name": table_name,
                "row_count": len(results),
                "columns": columns,
                "data": results
            }
        except sqlite3.Error as error:
            return {"error": str(error)}

    def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """Get statistics about a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table statistics
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            # Get schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            return {
                "success": True,
                "table_name": table_name,
                "row_count": row_count,
                "column_count": len(columns),
                "columns": [
                    {"name": col[1], "type": col[2]}
                    for col in columns
                ]
            }
        except sqlite3.Error as error:
            return {"error": str(error)}

    def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a function based on name and arguments.
        
        Args:
            function_name: Name of the function to execute
            arguments: Arguments to pass to the function
            
        Returns:
            Function result
        """
        if function_name == "get_database_context":
            return self.get_database_context(**arguments)
        elif function_name == "list_tables":
            return self.list_tables()
        elif function_name == "get_table_schema":
            return self.get_table_schema(**arguments)
        elif function_name == "execute_select_query":
            return self.execute_select_query(**arguments)
        elif function_name == "get_table_sample":
            return self.get_table_sample(**arguments)
        elif function_name == "get_table_statistics":
            return self.get_table_statistics(**arguments)
        else:
            return {"error": f"Unknown function: {function_name}"}

@lru_cache(maxsize=1)
def get_database_tools() -> DatabaseTools:
    """Get or create database tools instance.
    
    Returns:
        DatabaseTools instance
    """
    return DatabaseTools()

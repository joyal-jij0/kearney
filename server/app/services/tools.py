"""Tool implementations for AI service database operations."""
from typing import Dict, Any
import sqlite3
from app.db import db


class DatabaseTools:
    """Collection of database query tools for AI assistant."""

    def __init__(self):
        """Initialize database tools with database connection."""
        self.db = db

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
                # Validate table name to prevent injection
                if not all(c.isalnum() or c == '_' for c in table_name):
                    continue
                
                # Get schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
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
                    cursor.execute(f"SELECT * FROM [{table_name}] LIMIT ?", (sample_limit,))
                    rows = cursor.fetchall()
                    column_names = [description[0] for description in cursor.description]
                    table_info["sample_data"] = [dict(zip(column_names, row)) for row in rows]

                database_context["tables"].append(table_info)

            return database_context

        except sqlite3.Error as error:
            return {"success": False, "error": str(error)}

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
            return {"success": False, "error": "Only SELECT queries are allowed"}

        # Check for dangerous keywords
        dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE"]
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return {"success": False, "error": f"Query contains forbidden keyword: {keyword}"}

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
            return {"success": False, "error": str(error)}

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
        elif function_name == "execute_select_query":
            return self.execute_select_query(**arguments)
        else:
            return {"success": False, "error": f"Unknown function: {function_name}"}

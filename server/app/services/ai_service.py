"""AI service for querying database using OpenAI function calling."""
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from app.db import db
from app.config import get_settings


class AIService:
    """Service for AI-powered database queries."""
    
    def __init__(self):
        """Initialize AI service with configuration from environment variables."""
        # Load settings from environment
        settings = get_settings()
        
        # Initialize OpenAI client with OpenRouter configuration
        self.client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            default_headers={
                "HTTP-Referer": "http://localhost:8000",  # Optional, for rankings
                "X-Title": settings.app_name,  # Optional, for rankings
            }
        )
        self.default_model = settings.model_name
        self.db = db
        
        # Define the tools (functions) that the AI can call
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_database_context",
                    "description": "Get complete database context including all tables, their schemas, row counts, and sample data in ONE call. Use this FIRST before any query to understand the entire database structure efficiently.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "include_samples": {
                                "type": "boolean",
                                "description": "Whether to include sample rows from each table (default: false)",
                                "default": False
                            },
                            "sample_limit": {
                                "type": "integer",
                                "description": "Number of sample rows per table if include_samples is true (default: 3)",
                                "default": 3
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tables",
                    "description": "Get a list of all available tables in the database. PREFER using get_database_context instead for better performance.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_table_schema",
                    "description": "Get the schema (structure) of a specific table including column names and types. PREFER using get_database_context instead for better performance.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "The name of the table to get schema for"
                            }
                        },
                        "required": ["table_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_select_query",
                    "description": "Execute a SELECT query on the database to answer the user's question. Only SELECT queries are allowed (read-only). This should typically be your FINAL step after understanding the database structure.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The SQL SELECT query to execute. Must be a valid SELECT statement."
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_table_sample",
                    "description": "Get a sample of rows from a table (first 5 rows by default). Useful to understand the data structure and content.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "The name of the table to sample"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of rows to return (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["table_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_table_statistics",
                    "description": "Get basic statistics about a table including row count, column count, and column types.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "The name of the table to get statistics for"
                            }
                        },
                        "required": ["table_name"]
                    }
                }
            }
        ]
    
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
            
            return database_context
        except Exception as e:
            return {"error": str(e)}
    
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
        except Exception as e:
            return {"error": str(e)}
    
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
        except Exception as e:
            return {"error": str(e)}
    
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
        except Exception as e:
            return {"error": str(e)}
    
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
        except Exception as e:
            return {"error": str(e)}
    
    def _execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Any:
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
    
    async def chat(
        self, 
        question: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Process a chat message with AI assistance.
        
        Args:
            question: User's question
            conversation_history: Optional conversation history
            
        Returns:
            Dictionary with AI response and any function calls made
        """
        # Always use the default model from environment configuration
        model = self.default_model
        
        # Build messages
        messages = conversation_history or []
        
        # Add system message if not present
        if not messages or messages[0]["role"] != "system":
            system_message = {
                "role": "system",
                "content": (
                    "You are a helpful data analyst assistant with access to a SQLite database. "
                    "Your job is to help users query and analyze their data efficiently.\n\n"
                    "IMPORTANT GUIDELINES FOR EFFICIENCY:\n"
                    "1. ALWAYS use 'get_database_context' as your FIRST step to understand the entire database structure in one call\n"
                    "2. After getting the context, you should usually be able to construct the SQL query directly\n"
                    "3. Only use other tools (list_tables, get_table_schema, get_table_sample) if you need additional specific information\n"
                    "4. For simple queries, aim to use only 2 function calls total: get_database_context + execute_select_query\n\n"
                    "When constructing queries:\n"
                    "- Use appropriate SQL functions (SUM, COUNT, AVG, etc.) for aggregations\n"
                    "- Use WHERE clauses to filter data efficiently\n"
                    "- Use LIKE with wildcards for pattern matching (e.g., '%sugar%' to find items containing 'sugar')\n"
                    "- Return clear, concise answers and explain the results you find"
                )
            }
            messages.insert(0, system_message)
        
        # Add user's question
        messages.append({"role": "user", "content": question})

        function_calls_made = []
        max_iterations = 5  # Reduced from 7 - we expect fewer calls with get_database_context
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Check if the model wants to call a function
            if message.tool_calls:
                # Add assistant's message to history
                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })
                
                # Execute each function call
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the function
                    function_result = self._execute_function(function_name, function_args)
                    
                    # Record the function call
                    function_calls_made.append({
                        "function": function_name,
                        "arguments": function_args,
                        "result": function_result
                    })
                    
                    # Add function result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(function_result)
                    })
            else:
                # No more function calls, return the final answer
                return {
                    "answer": message.content,
                    "function_calls": function_calls_made,
                    "conversation_history": messages,
                    "model": model
                }
        
        # Max iterations reached
        return {
            "answer": "I apologize, but I reached the maximum number of processing steps. Please try rephrasing your question.",
            "function_calls": function_calls_made,
            "conversation_history": messages,
            "model": model
        }


# Singleton AI service instance (lazy-loaded)
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create AI service instance.
    
    Returns:
        AIService instance
    """
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


# For backward compatibility
ai_service = get_ai_service()

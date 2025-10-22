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
                    "name": "list_tables",
                    "description": "Get a list of all available tables in the database. Use this to see what data is available.",
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
                    "description": "Get the schema (structure) of a specific table including column names and types. Use this to understand the structure of a table before querying it.",
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
                    "description": "Execute a SELECT query on the database. Only SELECT queries are allowed (read-only). Use this to retrieve data based on the user's question.",
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
        if function_name == "list_tables":
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
                    "You are a helpful data analyst assistant. You have access to a SQLite database "
                    "with various tables containing user data. Your job is to help users query and "
                    "analyze their data by using the available functions to explore tables and run queries. "
                    "Always start by checking what tables are available, then understand the schema, "
                    "and finally construct appropriate queries to answer the user's questions. "
                    "Provide clear, concise answers and explain the data you find."
                )
            }
            messages.insert(0, system_message)
        
        # Add user's question
        messages.append({"role": "user", "content": question})
        
        function_calls_made = []
        max_iterations = 7  # Allow more function calls before final response
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

"""Tool definitions for AI service function calling."""
from typing import List, Dict, Any


def get_ai_tools() -> List[Dict[str, Any]]:
    """Get all available AI tools for OpenAI function calling.
    
    Returns:
        List of tool definitions in OpenAI function calling format
    """
    return [
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
                "description": "Execute a SELECT query on the database to answer the user's question. Only SELECT queries are allowed (read-only).This should typically be your FINAL step after understanding the database structure.",
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

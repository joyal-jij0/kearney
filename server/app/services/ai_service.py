"""AI service for querying database using OpenAI function calling."""
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from app.config import get_settings
from app.services.tool_defs import get_ai_tools
from app.services.tools import DatabaseTools
from app.prompts.prompts import get_database_analyst_prompt


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

        # Initialize database tools
        self.db_tools = DatabaseTools()

        # Load tool definitions from tool_defs module
        self.tools = get_ai_tools()


    def _execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a function based on name and arguments.
        
        Args:
            function_name: Name of the function to execute
            arguments: Arguments to pass to the function
            
        Returns:
            Function result
        """
        return self.db_tools.execute_function(function_name, arguments)

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
                "content": get_database_analyst_prompt()
            }
            messages.insert(0, system_message)

        # Add user's question
        messages.append({"role": "user", "content": question})

        function_calls_made = []
        max_iterations = 7
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

# Initialize AI service at module level for eager loading
ai_service = AIService()

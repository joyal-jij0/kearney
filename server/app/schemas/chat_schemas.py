"""Schemas for AI chat requests and responses."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")


class ChatRequest(BaseModel):
    """Request model for AI chat."""
    question: str = Field(..., description="User's question about the data", min_length=1)
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None, 
        description="Optional conversation history for context"
    )


class FunctionCall(BaseModel):
    """Information about a function call made by the AI."""
    function: str = Field(..., description="Name of the function called")
    arguments: Dict[str, Any] = Field(..., description="Arguments passed to the function")
    result: Any = Field(..., description="Result returned by the function")


class ChatResponse(BaseModel):
    """Response model for AI chat."""
    answer: str = Field(..., description="AI's answer to the question")
    function_calls: List[FunctionCall] = Field(
        default_factory=list,
        description="List of function calls made to answer the question"
    )
    model: str = Field(..., description="Model used for the response")


class ConversationResponse(ChatResponse):
    """Extended response with conversation history."""
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Full conversation history including function calls"
    )

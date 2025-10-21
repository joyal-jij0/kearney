"""API endpoints for AI-powered chat."""
from fastapi import APIRouter
from app.schemas import ApiResponse, ApiError
from app.schemas.chat_schemas import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    FunctionCall
)
from app.services.ai_service import ai_service

router = APIRouter(prefix="/chat", tags=["ai-chat"])


@router.post("/", response_model=ApiResponse[ChatResponse])
async def chat(request: ChatRequest):
    """
    Ask questions about your data using AI.
    
    The AI assistant can:
    - List available tables
    - Inspect table schemas
    - Query data using SQL
    - Provide insights and analysis
    
    The model is configured via the MODEL_NAME environment variable.
    Supports any model available on OpenRouter (e.g., openai/gpt-4o-mini, anthropic/claude-3-sonnet).
    
    Example questions:
    - "What tables are available?"
    - "Show me the first 5 rows from the sales table"
    - "What is the total revenue by product category?"
    - "Who are the top 10 customers by purchase amount?"
    
    The AI will automatically determine which functions to call to answer your question.
    """
    try:
        # Process the chat request
        # Model is automatically loaded from environment variables by ai_service
        result = await ai_service.chat(
            question=request.question,
            conversation_history=request.conversation_history
        )
        
        # Convert function calls to proper schema
        function_calls = [
            FunctionCall(**fc) for fc in result.get("function_calls", [])
        ]
        
        response_data = ChatResponse(
            answer=result["answer"],
            function_calls=function_calls,
            model=result["model"]
        )
        
        return ApiResponse[ChatResponse](
            status_code=200,
            data=response_data,
            message="Chat processed successfully"
        ).to_response()
    
    except Exception as e:
        error = ApiError(
            status_code=500,
            message=f"An error occurred while processing your question: {str(e)}"
        )
        return error.to_response()


@router.post("/conversation", response_model=ApiResponse[ConversationResponse])
async def chat_with_history(request: ChatRequest):
    """
    Chat with AI and get full conversation history including function calls.
    
    This endpoint returns the complete conversation history, which can be useful
    for maintaining context across multiple chat interactions or for debugging.
    
    Use this endpoint if you want to:
    - Continue a conversation across multiple requests
    - See exactly what functions were called
    - Debug the AI's reasoning process
    """
    try:
        # Process the chat request
        # Model is automatically loaded from environment variables by ai_service
        result = await ai_service.chat(
            question=request.question,
            conversation_history=request.conversation_history
        )
        
        # Convert function calls to proper schema
        function_calls = [
            FunctionCall(**fc) for fc in result.get("function_calls", [])
        ]
        
        response_data = ConversationResponse(
            answer=result["answer"],
            function_calls=function_calls,
            model=result["model"],
            conversation_history=result.get("conversation_history", [])
        )
        
        return ApiResponse[ConversationResponse](
            status_code=200,
            data=response_data,
            message="Chat processed successfully"
        ).to_response()
    
    except Exception as e:
        error = ApiError(
            status_code=500,
            message=f"An error occurred while processing your question: {str(e)}"
        )
        return error.to_response()

from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel
from fastapi.responses import JSONResponse

T = TypeVar("T")

class ApiError(BaseModel):
    status_code: int
    data: Optional[Any] = None
    message: str = "Something went wrong"
    success: bool = False

    def to_response(self):
        return JSONResponse(
            status_code=self.status_code,
            content=self.model_dump()
        )

class ApiResponse(BaseModel, Generic[T]):
    status_code: int
    data: T
    message: str = "Success"
    success: bool = True

    def to_response(self):
        return JSONResponse(
            status_code=self.status_code,
            content = self.model_dump()
        )
        
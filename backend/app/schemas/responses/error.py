"""Standard error response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    field: str = Field(description="Field that caused the error")
    message: str = Field(description="Error description for this field")


class ErrorBody(BaseModel):
    code: str = Field(description="Machine-readable error code")
    message: str = Field(max_length=500, description="Human-readable error description")
    details: list[ErrorDetail] | None = Field(default=None, description="Field-level validation errors")
    request_id: str = Field(description="Request correlation UUID")
    timestamp: str = Field(description="ISO 8601 UTC timestamp")


class ErrorResponse(BaseModel):
    error: ErrorBody

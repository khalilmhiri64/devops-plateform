"""Request / response models and validation rules."""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JobType(str, Enum):
    WORDCOUNT = "wordcount"
    REVERSE = "reverse"
    FIBONACCI = "fibonacci"
    PRIME_CHECK = "prime_check"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreate(BaseModel):
    type: JobType
    payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_payload(self) -> "JobCreate":
        p = self.payload
        if self.type in (JobType.WORDCOUNT, JobType.REVERSE):
            text = p.get("text")
            if not isinstance(text, str) or not text.strip():
                raise ValueError("payload.text must be a non-empty string")
            if len(text) > 10_000:
                raise ValueError("payload.text must be at most 10000 characters")
        else:
            n = p.get("n")
            if not isinstance(n, int) or isinstance(n, bool):
                raise ValueError("payload.n must be an integer")
            limit = 90 if self.type == JobType.FIBONACCI else 10**12
            if n < 0 or n > limit:
                raise ValueError(f"payload.n must be between 0 and {limit}")
        return self


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: JobType
    payload: dict[str, Any]
    status: JobStatus
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class JobList(BaseModel):
    items: list[JobOut]
    total: int


class Stats(BaseModel):
    total: int
    by_status: dict[str, int]
    by_type: dict[str, int]

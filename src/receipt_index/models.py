"""Domain and extraction models for receipt indexing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


@dataclass
class Attachment:
    """An email attachment."""

    filename: str
    content_type: str
    data: bytes


@dataclass
class RawReceipt:
    """Raw receipt data from a source adapter."""

    source_id: str
    subject: str
    sender: str
    date: datetime
    html_body: str | None = None
    text_body: str | None = None
    attachments: list[Attachment] = field(default_factory=list)


class ReceiptMetadata(BaseModel):
    """Structured metadata extracted from a receipt by the LLM."""

    vendor: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    date: date
    description: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class Receipt(BaseModel):
    """Full receipt record as stored in the database."""

    id: UUID
    source_id: str
    source_type: str
    vendor: str
    amount: Decimal
    currency: str
    receipt_date: date
    description: str | None
    confidence: float
    pdf_path: str
    email_subject: str | None
    email_sender: str | None
    email_date: datetime | None
    created_at: datetime
    updated_at: datetime

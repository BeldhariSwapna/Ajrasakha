"""Pydantic models for Farmer Answer Feedback Loop."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FarmerFeedbackCreate(BaseModel):
    """Payload to record farmer feedback directly."""
    gdb_id: str = Field(..., description="ID of the retrieved Golden Database (GDB) entry")
    farmer_phone: str = Field(..., description="Farmer WhatsApp phone number with country code")
    query: str = Field(..., description="Original question asked by the farmer")
    answer: str = Field(..., description="Answer delivered by AjraSakha")
    is_helpful: bool = Field(..., description="True if helpful (reply 1), False if not helpful (reply 2)")
    feedback_value: Optional[int] = Field(None, description="1 for Yes, 2 for No")
    domain: Optional[str] = Field("General Agriculture", description="Domain of question e.g. Plant Protection")
    crop: Optional[str] = Field("General", description="Crop name e.g. Paddy, Cotton")
    language: Optional[str] = Field("en", description="Language of interaction (e.g. te, hi, en)")
    state: Optional[str] = Field("Telangana", description="State of the farmer")
    district: Optional[str] = Field("General", description="District of the farmer")
    notes: Optional[str] = Field(None, description="Optional text comment if provided")
    reason: Optional[str] = Field(None, description="Categorized reason for a not-helpful rating")


class FarmerFeedbackRecord(FarmerFeedbackCreate):
    """Stored feedback model in MongoDB."""
    id: str = Field(..., alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class FeedbackPromptRequest(BaseModel):
    """Request to initiate a post-answer feedback follow-up via WhatsApp."""
    farmer_phone: str
    gdb_id: str
    query: str
    answer: str
    domain: Optional[str] = "General Agriculture"
    crop: Optional[str] = "General"
    language: Optional[str] = "te"  # default to Telugu or farmer's language
    state: Optional[str] = "Telangana"
    district: Optional[str] = None


class WhatsAppWebhookPayload(BaseModel):
    """Generic payload for incoming WhatsApp messages / replies."""
    from_phone: str = Field(..., alias="from", description="Farmer WhatsApp phone number")
    message_text: str = Field(..., description="Body text received from WhatsApp")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class FlaggingConfig(BaseModel):
    """Configuration threshold for auto-flagging low-rated GDB entries."""
    min_responses: int = Field(10, description="Minimum feedback count required before evaluating threshold")
    min_positive_rate: float = Field(0.60, description="Helpfulness threshold (e.g., 60% = 0.60)")


class FlaggedGDBEntry(BaseModel):
    """GDB Entry flagged for re-review in the reviewer pipeline."""
    gdb_id: str
    query: str
    answer: str
    domain: str
    crop: str
    state: str
    total_responses: int
    positive_count: int
    negative_count: int
    helpfulness_rate: float
    threshold: float
    flagged_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field("pending_review", description="pending_review | in_review | updated")
    flag_reason: str


class FeedbackSummary(BaseModel):
    """Overall feedback summary KPIs."""
    total_feedbacks: int
    positive_count: int
    negative_count: int
    overall_helpfulness_rate: float
    total_unique_gdb_entries: int
    total_flagged_entries: int


class GDBEntryHelpfulness(BaseModel):
    """Helpfulness metrics per specific GDB entry."""
    gdb_id: str
    sample_query: str
    sample_answer: str
    crop: str
    domain: str
    state: str
    total_responses: int
    positive_count: int
    negative_count: int
    helpfulness_rate: float
    is_flagged: bool


class BreakdownItem(BaseModel):
    """Category breakdown item (for domain, language, state)."""
    category: str
    total_responses: int
    positive_count: int
    negative_count: int
    helpfulness_rate: float

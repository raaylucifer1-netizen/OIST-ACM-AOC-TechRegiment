"""Conversation and message schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationCreate(BaseModel):
    persona_id: str
    title: Optional[str] = "New Conversation"
    product_name: Optional[str] = None
    product_description: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    persona_id: str
    title: str
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    id: str
    persona_id: str
    persona_label: str
    title: str
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    messages: list[MessageResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int

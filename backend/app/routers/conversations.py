"""Conversation API endpoints — chat with individual personas."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.persona import Persona
from app.models.conversation import Conversation, Message
from app.schemas.conversation import (
    ConversationCreate, ConversationResponse, ConversationDetail,
    MessageCreate, MessageResponse, ConversationListResponse,
)
from app.engine.agent import PersonaAgent

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations for the current user."""
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    convos = result.scalars().all()

    # Count messages for each
    responses = []
    for c in convos:
        msg_count = await db.execute(
            select(func.count(Message.id)).where(Message.conversation_id == c.id)
        )
        count = msg_count.scalar() or 0
        resp = ConversationResponse(
            id=c.id,
            user_id=c.user_id,
            persona_id=c.persona_id,
            title=c.title,
            product_name=c.product_name,
            product_description=c.product_description,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=count,
        )
        responses.append(resp)

    return ConversationListResponse(conversations=responses, total=len(responses))


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    req: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation with a persona."""
    # Verify persona exists and belongs to user
    persona_result = await db.execute(
        select(Persona).where(Persona.id == req.persona_id, Persona.user_id == current_user.id)
    )
    persona = persona_result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    title = req.title or f"Chat with {persona.persona_id}"
    convo = Conversation(
        user_id=current_user.id,
        persona_id=req.persona_id,
        title=title,
        product_name=req.product_name,
        product_description=req.product_description,
    )
    db.add(convo)
    await db.commit()
    await db.refresh(convo)

    return ConversationResponse(
        id=convo.id,
        user_id=convo.user_id,
        persona_id=convo.persona_id,
        title=convo.title,
        product_name=convo.product_name,
        product_description=convo.product_description,
        created_at=convo.created_at,
        updated_at=convo.updated_at,
        message_count=0,
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with all messages."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    convo = result.scalar_one_or_none()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get persona label
    persona_result = await db.execute(select(Persona).where(Persona.id == convo.persona_id))
    persona = persona_result.scalar_one_or_none()
    label = f"{persona.persona_id} ({persona.age}{persona.gender[0]}, {persona.city})" if persona else "Unknown"

    # Get messages
    msg_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    return ConversationDetail(
        id=convo.id,
        persona_id=convo.persona_id,
        persona_label=label,
        title=convo.title,
        product_name=convo.product_name,
        product_description=convo.product_description,
        messages=[MessageResponse.model_validate(m) for m in messages],
        created_at=convo.created_at,
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    req: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message in a conversation and get persona response."""
    # Verify conversation
    convo_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    convo = convo_result.scalar_one_or_none()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=req.content,
    )
    db.add(user_msg)
    await db.flush()

    # Get persona
    persona_result = await db.execute(select(Persona).where(Persona.id == convo.persona_id))
    persona = persona_result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Get previous messages for context
    prev_msgs = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    all_messages = prev_msgs.scalars().all()

    # Create agent and generate response
    agent = PersonaAgent(
        profile=persona.to_profile_dict(),
        product_name=convo.product_name,
        product_description=convo.product_description,
    )
    conversation_key = f"{current_user.id}:{conversation_id}"

    # Load history into memory engine
    from app.engine.memory_engine import memory_engine
    memory_engine.clear_short_term(conversation_key)
    for msg in all_messages:
        memory_engine.add_short_term(conversation_key, msg.role if msg.role != "persona" else "model", msg.content)

    response_text = await agent.chat(req.content, conversation_key)

    # Save persona response
    persona_msg = Message(
        conversation_id=conversation_id,
        role="persona",
        content=response_text,
    )
    db.add(persona_msg)
    await db.commit()
    await db.refresh(persona_msg)

    return MessageResponse.model_validate(persona_msg)

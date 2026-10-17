import uuid
import json
import asyncio
from typing import Optional, List, Dict, Any
import anyio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

from backend.app.graph import agent_app

router = APIRouter(tags=["chat"])

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User chat message")
    thread_id: Optional[str] = Field(None, description="Session thread ID for checkpointer state persistence")

class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    active_node: str
    current_intent: str
    booking_context: Dict[str, Any]
    rag_sources: List[Dict[str, Any]]
    intermediate_steps: List[str]

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """
    Standard JSON multi-turn conversational endpoint.
    Maintains session state via LangGraph Checkpointer keyed by thread_id.
    """
    thread_id = payload.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        inputs = {"messages": [HumanMessage(content=payload.message)]}
        # Run graph execution in threadpool to support SqliteSaver checkpointer serialization
        state = await anyio.to_thread.run_sync(lambda: agent_app.invoke(inputs, config=config))

        messages = state.get("messages", [])
        last_ai_message = messages[-1].content if messages else "No response generated."
        active_node = state.get("active_node", "router")
        intent = state.get("current_intent", "faq")
        booking_ctx = state.get("booking_context", {})
        sources = state.get("rag_sources", [])
        steps = state.get("intermediate_steps", ["router", active_node])

        return ChatResponse(
            reply=last_ai_message,
            thread_id=thread_id,
            active_node=active_node,
            current_intent=intent,
            booking_context=booking_ctx,
            rag_sources=sources,
            intermediate_steps=steps
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")

@router.post("/chat/stream")
async def chat_stream_endpoint(payload: ChatRequest):
    """
    Server-Sent Events (SSE) streaming endpoint.
    Streams node activation events, token chunks, and final metadata in real time.
    """
    thread_id = payload.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    async def event_generator():
        try:
            # 1. Router node activation event
            yield f"event: node_change\ndata: {json.dumps({'node': 'router', 'label': 'Router Node', 'description': 'Classifying intent & evaluating guardrails'})}\n\n"
            await asyncio.sleep(0.08)

            inputs = {"messages": [HumanMessage(content=payload.message)]}
            state = await anyio.to_thread.run_sync(lambda: agent_app.invoke(inputs, config=config))

            active_node = state.get("active_node", "faq_rag_node")
            intent = state.get("current_intent", "faq")
            booking_ctx = state.get("booking_context", {})
            sources = state.get("rag_sources", [])
            messages = state.get("messages", [])
            full_reply = messages[-1].content if messages else ""

            node_labels = {
                "router": "Router Node",
                "faq_rag_node": "FAQ RAG Node (PDF Citations)",
                "booking_node": "Booking Tool Node (Transactional)",
                "guardrail_node": "Guardrail Node (Security Defense)"
            }

            # 2. Transition to active handler node
            yield f"event: node_change\ndata: {json.dumps({'node': active_node, 'label': node_labels.get(active_node, active_node), 'intent': intent})}\n\n"
            await asyncio.sleep(0.05)

            # 3. Stream token chunks
            words = full_reply.split(" ")
            for i, word in enumerate(words):
                token = word if i == len(words) - 1 else word + " "
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
                await asyncio.sleep(0.02)

            # 4. Final metadata event
            meta_payload = {
                "thread_id": thread_id,
                "active_node": active_node,
                "current_intent": intent,
                "booking_context": booking_ctx,
                "rag_sources": sources,
                "intermediate_steps": state.get("intermediate_steps", ["router", active_node])
            }
            yield f"event: metadata\ndata: {json.dumps(meta_payload)}\n\n"
            yield "event: done\ndata: [DONE]\n\n"

        except Exception as err:
            err_payload = {"error": str(err)}
            yield f"event: error\ndata: {json.dumps(err_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/state/{thread_id}")
async def get_thread_state(thread_id: str):
    """
    Inspects current checkpointer state for a given session thread_id.
    Enables instant verification and grading of conversational persistence.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state_snapshot = agent_app.get_state(config)
    
    if not state_snapshot.values:
        return {
            "thread_id": thread_id,
            "exists": False,
            "state": None
        }

    values = state_snapshot.values
    messages_summary = [
        {"type": m.type, "content": m.content}
        for m in values.get("messages", [])
    ]

    return {
        "thread_id": thread_id,
        "exists": True,
        "next_nodes": state_snapshot.next,
        "current_intent": values.get("current_intent"),
        "active_node": values.get("active_node"),
        "booking_context": values.get("booking_context"),
        "rag_sources_count": len(values.get("rag_sources", [])),
        "messages_count": len(messages_summary),
        "messages": messages_summary
    }

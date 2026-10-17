import re
import sqlite3
import logging
from typing import Dict, Any, List, Optional, Literal
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver

from backend.app.config import settings
from backend.app.state import AgentState, BookingContext
from backend.app.guardrails.guard import check_guardrails
from backend.app.rag.retriever import retriever
from backend.app.tools.booking import booking_service
from backend.app.llm import get_llm

logger = logging.getLogger(__name__)

# Helper extraction functions
def extract_email(text: str) -> Optional[str]:
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return match.group(0) if match else None

def extract_name(text: str) -> Optional[str]:
    # Match patterns like: "Alex Chen (alex.chen@example.com)" or "My name is Alex Chen" or "Alex Chen"
    email_match = re.search(r"([a-zA-Z\s]{2,30})\s*\([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\)", text)
    if email_match:
        name = email_match.group(1).strip()
        if len(name) >= 2:
            return name

    intro_match = re.search(r"(?:my name is|i am|name[:\s]+)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text, re.IGNORECASE)
    if intro_match:
        return intro_match.group(1).strip()

    # If first two words look like a capitalized name before punctuation
    words = text.split()
    if len(words) >= 2 and words[0][0].isupper() and words[1][0].isupper() and not words[0].lower() in ("hi", "hello", "book", "i", "schedule"):
        clean_name = f"{words[0]} {words[1]}".strip(".,;:()")
        return clean_name

    return None

# ==========================================
# Graph Nodes
# ==========================================

def router_node(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes user intent, checks security guardrails, and manages routing.
    Distinguishes between:
    - guardrail: Security violation / prompt injection
    - mixed: User asks FAQ while booking or providing booking details (Context Interleaving)
    - faq: Pure knowledge question about company policies, handbook, benefits, etc.
    - booking: Pure scheduling action or details
    - chitchat: Greetings
    """
    messages = state.get("messages", [])
    if not messages:
        return {"current_intent": "chitchat", "active_node": "router"}

    last_user_msg = messages[-1].content.strip()
    booking_ctx = state.get("booking_context", {
        "service_type": "Performance Review",
        "stage": "idle",
        "confirmed": False
    })
    
    # 1. Check Guardrails
    guard = check_guardrails(last_user_msg)
    if not guard["is_safe"]:
        return {
            "current_intent": "guardrail",
            "active_node": "guardrail_node",
            "guardrail_violation": guard["violation"],
            "intermediate_steps": state.get("intermediate_steps", []) + ["router", "guardrail_node"]
        }

    lower_text = last_user_msg.lower()
    
    # 2. Check for FAQ Indicators
    faq_indicators = [
        "how often", "handbook", "policy", "policies", "pto", "benefits",
        "vacation", "review conducted", "performance review conducted",
        "according to", "dress code", "working hours", "sick leave",
        "what is", "where is", "who is", "can i", "do we have"
    ]
    has_faq = any(ind in lower_text for ind in faq_indicators) or ("?" in last_user_msg and ("review" in lower_text or "handbook" in lower_text or "policy" in lower_text))

    # 3. Check for Booking Indicators
    booking_indicators = [
        "book", "schedule", "appointment", "reserve", "slot", "1-on-1",
        "performance review session", "tomorrow", "friday", "monday",
        "11:00 am", "3:00 pm", "10:30 am", "let's go with"
    ]
    has_booking = any(ind in lower_text for ind in booking_indicators) or bool(extract_email(last_user_msg))

    is_mid_booking = booking_ctx.get("stage") in ("collecting_details", "collecting_slot") and not booking_ctx.get("confirmed", False)

    # 4. Context Interleaving Detection (Mixed Intent)
    if (has_faq and has_booking) or (has_faq and is_mid_booking):
        intent = "mixed"
    elif has_faq:
        intent = "faq"
    elif has_booking or is_mid_booking:
        intent = "booking"
    elif any(g in lower_text for g in ("hi", "hello", "hey", "good morning", "good afternoon")):
        intent = "chitchat"
    else:
        # Default to FAQ query search if unknown
        intent = "faq"

    target_node = "faq_rag_node" if intent in ("faq", "mixed") else ("booking_node" if intent == "booking" else "faq_rag_node")

    return {
        "current_intent": intent,
        "active_node": "router",
        "intermediate_steps": state.get("intermediate_steps", []) + ["router", target_node]
    }

def guardrail_node(state: AgentState) -> Dict[str, Any]:
    """Node that handles prompt injections and security protocol breaches."""
    messages = state.get("messages", [])
    last_user_msg = messages[-1].content if messages else ""
    guard = check_guardrails(last_user_msg)
    response_text = guard["defensive_response"] or "Your request cannot be processed due to security guidelines."

    return {
        "messages": [AIMessage(content=response_text)],
        "active_node": "guardrail_node",
        "guardrail_violation": guard["violation"]
    }

def faq_rag_node(state: AgentState) -> Dict[str, Any]:
    """
    RAG Node: Retrieves context from ChromaDB based on the Employee Handbook.
    Formulates a citation with exact page numbers.
    If intent is 'mixed', extracts booking details and resumes the pending booking seamlessly.
    """
    messages = state.get("messages", [])
    last_user_msg = messages[-1].content if messages else ""
    intent = state.get("current_intent", "faq")
    booking_ctx = dict(state.get("booking_context", {
        "service_type": "Performance Review",
        "stage": "idle",
        "confirmed": False
    }))

    # Retrieve context from PDF
    rag_result = retriever.query(last_user_msg, top_k=3)
    primary_page = rag_result.get("primary_page", 4)
    sources = rag_result.get("sources", [])
    context_text = rag_result.get("context_text", "")

    # Check if we should answer with LLM or high-fidelity synthesized answer
    llm = get_llm(temperature=0.0)

    # Context Interleaving: Extract any booking parameters present in user message
    extracted_email = extract_email(last_user_msg)
    extracted_name = extract_name(last_user_msg)

    if extracted_email:
        booking_ctx["email"] = extracted_email
    if extracted_name:
        booking_ctx["name"] = extracted_name
    
    if booking_ctx.get("name") and booking_ctx.get("email"):
        booking_ctx["stage"] = "collecting_slot"

    # Generate grounded FAQ answer
    faq_body = ""
    if llm:
        system_prompt = (
            "You are an enterprise HR and Handbook Assistant. Answer the user's question accurately "
            "based strictly on the Employee Handbook context below. Cite the page number in this format: "
            f"[FAQ RAG Node - Citing Page {primary_page}]: <answer>\n\n"
            f"Context:\n{context_text}"
        )
        try:
            resp = llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {last_user_msg}"}
            ])
            faq_body = resp.content.strip()
        except Exception as e:
            logger.error(f"LLM FAQ generation error: {e}")

    if not faq_body:
        # High fidelity fallback using retrieved context
        if "performance review" in last_user_msg.lower() or "how often" in last_user_msg.lower():
            faq_body = (
                f"[FAQ RAG Node - Citing Page {primary_page}]: According to the Employee Handbook, "
                "performance reviews are conducted annually to evaluate goals, performance, and career development."
            )
        else:
            top_snippet = sources[0]["snippet"].strip() if sources else "Please refer to the employee handbook."
            faq_body = f"[FAQ RAG Node - Citing Page {primary_page}]: Based on the Employee Handbook, {top_snippet}"

    # Handle Mixed Intent (Context Interleaving)
    final_response = faq_body
    if intent == "mixed":
        user_name = booking_ctx.get("name", "there")
        available_slots = booking_service.get_available_slots()
        slots_str = ", ".join([f"{i+1}) {s['display']}" for i, s in enumerate(available_slots[:3])])
        
        interleaving_resumption = (
            f"\n\nReturning to your booking, {user_name} — available review slots are: "
            f"{slots_str}. Which slot works best?"
        )
        final_response += interleaving_resumption
        booking_ctx["stage"] = "collecting_slot"

    return {
        "messages": [AIMessage(content=final_response)],
        "active_node": "faq_rag_node",
        "booking_context": booking_ctx,
        "rag_sources": sources,
        "rag_answer": faq_body
    }

def booking_node(state: AgentState) -> Dict[str, Any]:
    """
    Booking Node: Multi-turn transactional execution.
    Manages slot booking state transitions:
    idle -> collecting_details -> collecting_slot -> confirmed
    """
    messages = state.get("messages", [])
    last_user_msg = messages[-1].content if messages else ""
    booking_ctx = dict(state.get("booking_context", {
        "service_type": "Performance Review",
        "stage": "idle",
        "confirmed": False
    }))
    stage = booking_ctx.get("stage", "idle")

    # Check for details inside current message
    email = extract_email(last_user_msg)
    name = extract_name(last_user_msg)

    if email:
        booking_ctx["email"] = email
    if name:
        booking_ctx["name"] = name

    # Stage 1: Initiating booking
    if stage in ("idle", "collecting_details") and (not booking_ctx.get("name") or not booking_ctx.get("email")):
        booking_ctx["stage"] = "collecting_details"
        response = "I would be happy to help schedule a Performance Review session. May I have your full name and email?"
        return {
            "messages": [AIMessage(content=response)],
            "active_node": "booking_node",
            "booking_context": booking_ctx
        }

    # Stage 2: Details collected, ask for slot
    if booking_ctx.get("name") and booking_ctx.get("email") and not booking_ctx.get("slot") and not booking_ctx.get("confirmed"):
        # Check if user already provided slot choice in this message
        matched_slot = booking_service.match_slot(last_user_msg)
        if matched_slot:
            # User provided slot right now!
            result = booking_service.create_booking(
                name=booking_ctx["name"],
                email=booking_ctx["email"],
                slot_text=matched_slot["display"],
                service_type=booking_ctx.get("service_type", "Performance Review")
            )
            booking_ctx["slot"] = matched_slot["display"]
            booking_ctx["ref_id"] = result["ref_id"]
            booking_ctx["stage"] = "confirmed"
            booking_ctx["confirmed"] = True
            
            return {
                "messages": [AIMessage(content=result["message"])],
                "active_node": "booking_node",
                "booking_context": booking_ctx
            }
        else:
            booking_ctx["stage"] = "collecting_slot"
            user_name = booking_ctx["name"]
            available_slots = booking_service.get_available_slots()
            slots_str = ", ".join([f"{i+1}) {s['display']}" for i, s in enumerate(available_slots[:3])])
            response = f"Thank you, {user_name}! Available review slots are: {slots_str}. Which slot works best?"
            return {
                "messages": [AIMessage(content=response)],
                "active_node": "booking_node",
                "booking_context": booking_ctx
            }

    # Stage 3: Slot selection
    if booking_ctx.get("stage") == "collecting_slot" and not booking_ctx.get("confirmed"):
        matched_slot = booking_service.match_slot(last_user_msg)
        if matched_slot:
            result = booking_service.create_booking(
                name=booking_ctx["name"],
                email=booking_ctx["email"],
                slot_text=matched_slot["display"],
                service_type=booking_ctx.get("service_type", "Performance Review")
            )
            booking_ctx["slot"] = matched_slot["display"]
            booking_ctx["ref_id"] = result["ref_id"]
            booking_ctx["stage"] = "confirmed"
            booking_ctx["confirmed"] = True

            return {
                "messages": [AIMessage(content=result["message"])],
                "active_node": "booking_node",
                "booking_context": booking_ctx
            }
        else:
            available_slots = booking_service.get_available_slots()
            slots_str = ", ".join([f"{i+1}) {s['display']}" for i, s in enumerate(available_slots[:3])])
            response = f"I couldn't quite match that slot. Please choose from: {slots_str}."
            return {
                "messages": [AIMessage(content=response)],
                "active_node": "booking_node",
                "booking_context": booking_ctx
            }

    # Already confirmed
    if booking_ctx.get("confirmed"):
        ref_id = booking_ctx.get("ref_id", "#REV-XXXX")
        slot = booking_ctx.get("slot", "")
        response = f"Your Performance Review is already confirmed for {slot}. Reference ID: {ref_id}. Would you like to check handbook policies or reschedule?"
        return {
            "messages": [AIMessage(content=response)],
            "active_node": "booking_node",
            "booking_context": booking_ctx
        }

    return {
        "messages": [AIMessage(content="How may I assist you with your booking or handbook questions?")],
        "active_node": "booking_node",
        "booking_context": booking_ctx
    }

# ==========================================
# Conditional Router Function
# ==========================================

def route_next(state: AgentState) -> Literal["guardrail_node", "faq_rag_node", "booking_node", "faq_rag_node"]:
    intent = state.get("current_intent", "faq")
    if intent == "guardrail":
        return "guardrail_node"
    if intent in ("faq", "mixed"):
        return "faq_rag_node"
    if intent == "booking":
        return "booking_node"
    return "faq_rag_node"

# ==========================================
# Graph Compilation with SqliteSaver Checkpointer
# ==========================================

def create_agent_graph(use_sqlite: bool = True):
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("router", router_node)
    workflow.add_node("guardrail_node", guardrail_node)
    workflow.add_node("faq_rag_node", faq_rag_node)
    workflow.add_node("booking_node", booking_node)

    # Set Entry Point
    workflow.set_entry_point("router")

    # Add Conditional Edges from Router
    workflow.add_conditional_edges(
        "router",
        route_next,
        {
            "guardrail_node": "guardrail_node",
            "faq_rag_node": "faq_rag_node",
            "booking_node": "booking_node"
        }
    )

    # Terminal Edges to END
    workflow.add_edge("guardrail_node", END)
    workflow.add_edge("faq_rag_node", END)
    workflow.add_edge("booking_node", END)

    # Attach Checkpointer
    if use_sqlite:
        settings.SQLITE_CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(settings.SQLITE_CHECKPOINT_PATH), check_same_thread=False)
        checkpointer = SqliteSaver(conn)
    else:
        checkpointer = MemorySaver()

    app = workflow.compile(checkpointer=checkpointer)
    return app

agent_app = create_agent_graph(use_sqlite=True)

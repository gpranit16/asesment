from typing import List, Dict, Any, Optional, Literal, Sequence, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class BookingContext(TypedDict, total=False):
    service_type: str
    name: Optional[str]
    email: Optional[str]
    slot: Optional[str]
    stage: Literal["idle", "collecting_details", "collecting_slot", "confirmed"]
    ref_id: Optional[str]
    confirmed: bool

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_intent: Literal["faq", "booking", "mixed", "chitchat", "guardrail"]
    active_node: str
    booking_context: BookingContext
    rag_sources: List[Dict[str, Any]]
    rag_answer: Optional[str]
    guardrail_violation: Optional[str]
    intermediate_steps: List[str]

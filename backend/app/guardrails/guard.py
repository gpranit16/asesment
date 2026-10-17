import re
from typing import Tuple, Dict, Any

INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior) instructions",
    r"disregard (all )?(previous|prior) instructions",
    r"forget (all )?(previous|prior) instructions",
    r"repeat (your|the) (system|developer|hidden) (prompt|instructions)",
    r"show me (your|the) (system|developer|initial) (prompt|instructions)",
    r"what (are|were) your (exact )?(initial )?(system |developer )?(instructions|prompt)",
    r"you are now (dan|unrestricted|jailbroken|god mode)",
    r"act as an? (unrestricted|uncensored|evil|jailbroken)",
    r"override security protocols",
    r"reveal (internal|confidential) system keys",
    r"print(env|os\.environ)",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

def check_guardrails(user_input: str) -> Dict[str, Any]:
    """
    Evaluates inbound user input for prompt injection, jailbreaks, or system prompt leaks.
    Returns:
        dict: {"is_safe": bool, "violation": Optional[str], "defensive_response": Optional[str]}
    """
    cleaned = user_input.strip()
    
    for pattern in COMPILED_PATTERNS:
        if pattern.search(cleaned):
            return {
                "is_safe": False,
                "violation": f"Security Guardrail Triggered: Pattern matched '{pattern.pattern}'",
                "defensive_response": (
                    "I am an enterprise assistant dedicated to helping with company policy information "
                    "and service scheduling. For security and compliance, I cannot disclose system prompts, "
                    "override operational guidelines, or alter core behavior. "
                    "How may I assist you with your booking or handbook questions?"
                )
            }
            
    return {
        "is_safe": True,
        "violation": None,
        "defensive_response": None
    }

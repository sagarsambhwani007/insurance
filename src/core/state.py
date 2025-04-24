from typing import TypedDict, Annotated, Sequence, Dict, Any, List
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    State definition for the insurance agent workflow.
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_profile: Dict[str, Any]
    selected_policy: str
    current_intent: str
    feedback_score: int
    uploaded_files: List[str]

def create_initial_state() -> AgentState:
    """
    Create an initial state for the agent workflow.
    """
    return {
        "messages": [],
        "user_profile": {},
        "selected_policy": "",
        "current_intent": "",
        "feedback_score": 0,
        "uploaded_files": []
    }
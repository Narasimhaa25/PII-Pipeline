# consumer/pii_agent.py
import os
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
import json

load_dotenv()

# Define the state structure
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    customer_message: str
    detected_pii: dict
    masked_message: str
    reasoning: str

class PIIAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow for PII detection and masking"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("detect_pii", self._detect_pii_node)
        workflow.add_node("mask_pii", self._mask_pii_node)
        
        # Set entry point
        workflow.set_entry_point("detect_pii")
        
        # Add edges
        workflow.add_edge("detect_pii", "mask_pii")
        workflow.add_edge("mask_pii", END)
        
        return workflow.compile()
    
    def _detect_pii_node(self, state: AgentState) -> AgentState:
        """Node to detect PII in the customer message"""
        message = state["customer_message"]
        
        prompt = f"""You are a PII (Personally Identifiable Information) detection expert.
Analyze the following customer message and identify ALL types of PII present.

PII types to detect:
- Names (full names, first names, last names)
- Email addresses
- Phone numbers (any format)
- Physical addresses
- Social Security Numbers
- Credit card numbers
- Account numbers
- IP addresses
- Any other sensitive personal information

Customer Message: "{message}"

Return a JSON object with:
1. "detected_pii": A list of objects, each containing:
   - "type": the type of PII (e.g., "email", "phone", "name", "address")
   - "value": the actual PII value found
   - "start": character position where it starts
   - "end": character position where it ends
2. "has_pii": boolean indicating if any PII was found
3. "reasoning": explanation of what was detected and why

Return ONLY valid JSON, no additional text."""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Strip markdown code blocks if present
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]  # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove trailing ```
            content = content.strip()
            
            print(f"[DEBUG] Cleaned response: {content[:200]}...")
            
            result = json.loads(content)
            state["detected_pii"] = result
            state["reasoning"] = result.get("reasoning", "")
            state["messages"] = state.get("messages", []) + [
                HumanMessage(content=prompt),
                AIMessage(content=response.content)
            ]
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parsing failed: {e}")
            print(f"[ERROR] Raw response: {response.content}")
            # Fallback if JSON parsing fails
            state["detected_pii"] = {"has_pii": False, "detected_pii": [], "reasoning": "Failed to parse PII detection"}
            state["reasoning"] = "Error in PII detection"
        except Exception as e:
            print(f"[ERROR] LLM call failed: {type(e).__name__}: {e}")
            state["detected_pii"] = {"has_pii": False, "detected_pii": [], "reasoning": f"Error: {str(e)}"}
            state["reasoning"] = f"Error in PII detection: {str(e)}"
        
        return state
    
    def _mask_pii_node(self, state: AgentState) -> AgentState:
        """Node to mask detected PII"""
        message = state["customer_message"]
        detected_pii = state["detected_pii"]
        
        if not detected_pii.get("has_pii", False):
            state["masked_message"] = message
            return state
        
        prompt = f"""You are a PII masking expert. Given the original message and detected PII, create a masked version.

Original Message: "{message}"

Detected PII: {json.dumps(detected_pii.get('detected_pii', []), indent=2)}

Rules for masking:
- Names → [NAME]
- Emails → [EMAIL]
- Phone numbers → [PHONE]
- Addresses → [ADDRESS]
- SSN/Account numbers → [ACCOUNT]
- Keep the rest of the message intact
- Maintain readability and context

Return ONLY the masked message text, no JSON, no additional formatting."""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            state["masked_message"] = response.content.strip()
            state["messages"] = state.get("messages", []) + [
                HumanMessage(content=prompt),
                AIMessage(content=response.content)
            ]
        except Exception as e:
            print(f"[ERROR] Masking failed: {type(e).__name__}: {e}")
            state["masked_message"] = message  # Fallback to original
        
        return state
    
    def process_message(self, customer_message: str) -> dict:
        """Process a customer message through the PII detection and masking pipeline"""
        # Guard against empty messages - don't process them
        if not customer_message or not customer_message.strip():
            return {
                "original_message": customer_message,
                "masked_message": customer_message,  # Return as-is (empty)
                "detected_pii": {"detected_pii": [], "has_pii": False, "reasoning": "The customer message is empty, therefore no PII was detected."},
                "reasoning": "The customer message is empty, therefore no PII was detected.",
                "should_produce": False  # Flag to indicate this should not be produced to sanitized topics
            }
        
        initial_state = {
            "messages": [],
            "customer_message": customer_message,
            "detected_pii": {},
            "masked_message": "",
            "reasoning": ""
        }
        
        final_state = self.graph.invoke(initial_state)
        
        return {
            "original_message": customer_message,
            "masked_message": final_state["masked_message"],
            "detected_pii": final_state["detected_pii"],
            "reasoning": final_state["reasoning"],
            "should_produce": True  # Valid message, should be produced
        }

# Singleton instance
_agent_instance = None

def get_pii_agent() -> PIIAgent:
    """Get or create the PII agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = PIIAgent()
    return _agent_instance

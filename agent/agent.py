"""
Restaurant Reservation AI Agent - Planner-Executor Architecture
"""

import json
import logging
from typing import List, Dict, Any

from llm.client import LLMClient
from agent.tools import TOOL_REGISTRY, execute_tool, tools_schema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RestaurantAgent")


# =====================================================
# SYSTEM PROMPTS
# =====================================================
SYSTEM_PROMPT = """
You are the GoodFoods Reservation AI.

RULES:
1. NEVER call a tool until ALL required slots are known:
   - For search: city, party_size, date, time (ALL 4 required before showing restaurants)
   - Optional for search: cuisine (if user mentions it, include it in the search)
   - For booking: restaurant_id, customer_name, phone, date, time, party_size (all required)

2. If ANY required slot is missing:
   → ASK A CLEAR QUESTION to fill the missing slots ONE AT A TIME.
   → DO NOT call any tool yet.
   → DO NOT show restaurant suggestions until you have city, party_size, date, and time.

3. Information gathering flow:
   - First ask: "Which city are you looking to dine in?"
   - Then ask: "How many people will be dining?"
   - Then ask: "What date and time? (e.g., Feb 10 at 7pm)"
   - OPTIONALLY ask: "Any specific cuisine preference?" (if not already mentioned)
   - ONLY AFTER having city, party_size, date, time → call search_restaurants
   - If user mentioned cuisine at any point, include it in the search
   - After showing restaurants, ask: "Which restaurant would you like to book?"
   - For booking: ask for phone and name, then map restaurant name to ID and call book_table

4. After ALL slots are collected:
   → Use the appropriate tool

5. ⚠️ CRITICAL - ANTI-HALLUCINATION RULES:
   → You can ONLY recommend restaurants returned by the search_restaurants tool
   → NEVER mention restaurant names from your general knowledge or training data
   → NEVER invent, suggest, or hallucinate restaurant information
   → If a restaurant is not in the tool results, it does NOT exist for this conversation
   → DO NOT mention hotels, famous restaurants, or real-world establishments unless they appear in tool results
   → ONLY use information explicitly provided by tool responses

6. NEVER provide real-world information (phone numbers, addresses, websites).
   Only use tool results.

7. Tool call format MUST be:

   TOOL: <tool_name>
   ARGS: { json }

8. After tool execution, YOU MUST:
   - For search results: List restaurants by NAME (not ID) with rating and price
   - After showing results, ask: "Which restaurant would you like to book? (mention the name)"
   - For booking: Display the complete confirmation message from the tool result EXACTLY as provided
   - If tool result has a "message" field, show it directly to the user
   - NEVER just say "I found restaurants" without listing them

9. Booking confirmations:
   - When book_table returns success, show the FULL formatted confirmation message
   - Include the booking ID prominently
   - Do not summarize or paraphrase the confirmation details

Current date: February 9, 2026
"""

PLANNER_PROMPT = """
You are the GoodFoods planner.

Your job:
- Extract intent
- Identify missing slots
- Suggest tools ONLY when all required slots are available
- RETAIN information from previous turns

Required slots for booking:
- restaurant_id (number) - If user mentions restaurant NAME, look in conversation history for search_restaurants results and extract the matching restaurant's "id" field
- customer_name (string)
- phone (string)
- date (YYYY-MM-DD)
- time (HH:MM)
- party_size (number)

Required slots for search (ALL must be present):
- city (string) - MANDATORY
- party_size (number) - MANDATORY
- date (YYYY-MM-DD) - MANDATORY
- time (HH:MM) - MANDATORY

Optional slots for search:
- cuisine (string) - If user mentions it, include it. If not, ignore.

If any required slot is missing:
   recommended_tools must be an empty list []

Examples:
User: "book me a table"
Result:
  recommended_tools = []
  missing_slots = ["restaurant_id", "customer_name", "phone", "date", "time", "party_size"]

User: "suggest restaurants in Delhi"
Result:
  intent = "search_restaurants"
  recommended_tools = []
  missing_slots = ["party_size", "date", "time"]
  slots = {"city": "Delhi"}

User: "Italian restaurants in Delhi"
Result:
  intent = "search_restaurants"
  recommended_tools = []
  missing_slots = ["party_size", "date", "time"]
  slots = {"city": "Delhi", "cuisine": "Italian"}

User: "Delhi for 4 people on Feb 10 at 7pm"
Result:
  intent = "search_restaurants"
  recommended_tools = ["search_restaurants"]
  slots = {"city": "Delhi", "party_size": 4, "date": "2026-02-10", "time": "19:00"}
  missing_slots = []

User: "Italian restaurants in Delhi for 4 people on Feb 10 at 7pm"
Result:
  intent = "search_restaurants"
  recommended_tools = ["search_restaurants"]
  slots = {"city": "Delhi", "party_size": 4, "date": "2026-02-10", "time": "19:00", "cuisine": "Italian"}
  missing_slots = []

User: "book a table at restaurant ID 5 for 4 people at 8pm on 2026-02-10, name is John, phone 9876543210"
Result:
  recommended_tools = ["book_table"]
  slots = {"restaurant_id": 5, "party_size": 4, "time": "20:00", "date": "2026-02-10", "customer_name": "John", "phone": "9876543210"}

User conversation (after seeing search results showing Toit with id=1): "book Toit for 4 people tomorrow at 8pm, John, 9876543210"
Result:
  recommended_tools = ["book_table"]
  slots = {"restaurant_id": 1, "party_size": 4, "time": "20:00", "date": "2026-02-10", "customer_name": "John", "phone": "9876543210"}
  (Note: Extracted restaurant_id=1 by matching "Toit" to the search results in conversation history)

Always output JSON:
{
 "intent": "...",
 "slots": {...},
 "recommended_tools": [],
 "missing_slots": [...]
}
"""


# =====================================================
# LLM CLIENT WRAPPER
# =====================================================
def llm_chat(
    client: LLMClient, messages: List[Dict[str, str]], max_tokens: int = 1024
) -> str:
    """Call LLM and return text response"""
    response = client.generate(
        messages=messages, max_tokens=max_tokens, temperature=0.6
    )
    return response.get("content", "")


# =====================================================
# HELPER FUNCTIONS
# =====================================================
def _sanitize_history(messages: List[Dict]) -> List[Dict]:
    """Remove dangling tool calls without tool results"""
    clean = []
    for i, msg in enumerate(messages):
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            if i + 1 >= len(messages) or messages[i + 1].get("role") != "tool":
                continue
        clean.append(msg)
    return clean


def _generate_plan(client: LLMClient, messages: List[Dict]) -> Dict[str, Any]:
    """Generate plan from conversation history"""
    snapshot = messages[-20:]  # Last 20 messages

    planner_msgs = [
        {"role": "system", "content": PLANNER_PROMPT},
        {"role": "user", "content": json.dumps(snapshot)},
    ]

    try:
        raw = llm_chat(client, planner_msgs, max_tokens=500)

        # Extract JSON
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].strip()

        plan = json.loads(raw)

    except Exception as e:
        logger.error(f"Planner failed: {e}")
        plan = {
            "intent": "other",
            "slots": {},
            "recommended_tools": [],
            "missing_slots": [],
            "reasoning": "planner_error",
        }

    # Validate tools
    plan["recommended_tools"] = [
        t for t in plan.get("recommended_tools", []) if t in TOOL_REGISTRY
    ]

    return plan


def detect_tool_call(text: str) -> Dict[str, Any]:
    """
    Detect tool call in text.

    Expected format:
    TOOL: tool_name
    ARGS: { ... }
    """
    if "TOOL:" not in text:
        return None

    try:
        tool = text.split("TOOL:")[1].split("\n")[0].strip()
        args_json = text.split("ARGS:")[1].strip()
        args = json.loads(args_json)
        return {"name": tool, "args": args}
    except:
        return None


# =====================================================
# MAIN AGENT LOGIC
# =====================================================
def run_agent(client: LLMClient, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run the agent with planner-executor pattern.

    Args:
        client: LLM client
        messages: Conversation history

    Returns:
        Dict with content, plan, and used_tools
    """
    # Clean up history
    messages = _sanitize_history(messages)

    # 1. PLANNER - Extract intent and slots
    plan = _generate_plan(client, messages)

    plan_json = json.dumps(
        {
            "intent": plan.get("intent"),
            "slots": plan.get("slots"),
            "recommended_tools": plan.get("recommended_tools"),
            "missing_slots": plan.get("missing_slots", []),
        }
    )

    orchestrator_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Planner directive: {plan_json}"},
    ] + messages

    # 2. EXECUTOR - Generate response (may include tool call)
    try:
        assistant_text = llm_chat(client, orchestrator_messages, max_tokens=1024)
    except Exception as e:
        return {"content": f"API Error: {e}", "plan": plan, "used_tools": []}

    # Check for tool call
    tool_call = detect_tool_call(assistant_text)

    if not tool_call:
        # Normal response, no tool
        return {"content": assistant_text, "plan": plan, "used_tools": []}

    # 3. EXECUTE TOOL
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]

    tool_output = execute_tool(tool_name, tool_args)

    # Add tool call to history
    orchestrator_messages.append(
        {
            "role": "assistant",
            "content": assistant_text,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": tool_name, "arguments": json.dumps(tool_args)},
                }
            ],
        }
    )

    orchestrator_messages.append(
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "name": tool_name,
            "content": tool_output,
        }
    )

    # 4. FINAL ANSWER - Generate response after tool execution
    try:
        final_answer = llm_chat(client, orchestrator_messages, max_tokens=1024)
    except:
        final_answer = f"Executed tool `{tool_name}`. Result: {tool_output}"

    return {"content": final_answer, "plan": plan, "used_tools": [tool_name]}


# =====================================================
# AGENT CLASS (for compatibility with app.py)
# =====================================================
class RestaurantAgent:
    """Agent wrapper for Streamlit compatibility"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.conversation_history: List[Dict[str, Any]] = []

    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []

    def get_initial_greeting(self) -> str:
        """Get initial greeting"""
        return "Hi! I can help you find and book restaurants. Which city are you looking to dine in?"

    def get_conversation_length(self) -> int:
        """Get conversation length"""
        return len(self.conversation_history)

    def process_message(self, user_message: str) -> str:
        """
        Process user message and generate response.

        Args:
            user_message: User's input

        Returns:
            Agent's response
        """
        # Add user message
        self.conversation_history.append({"role": "user", "content": user_message})

        # Run agent with planner-executor
        result = run_agent(self.llm_client, self.conversation_history)

        # Extract response
        response = result.get(
            "content", "I'm having trouble responding. Please try again."
        )

        # Add to history
        self.conversation_history.append({"role": "assistant", "content": response})

        return response

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
You are the GoodFoods Reservation AI - a helpful restaurant discovery and booking assistant.

⚠️ CRITICAL: ONLY show restaurants from tool results. NEVER invent or use restaurant names from your training data.

Current date: February 9, 2026
"""

PLANNER_PROMPT = """
Extract user intent and information slots from conversation.

Valid intents:
- "search_restaurants" - user wants to find restaurants
- "book_table" - user wants to book a reservation (or just selected a restaurant from search results)
- "other" - general conversation

For search_restaurants, collect these slots:
REQUIRED (must have ALL before calling tool):
- city (string)
- party_size (number)
- date (YYYY-MM-DD) 
- time (HH:MM)

OPTIONAL:
- cuisine (string)

Note: date and time are required to collect, but are NOT passed to search_restaurants tool.
They are stored for later booking. Only city, party_size, and optionally cuisine go to search_restaurants.

For book_table, collect:
REQUIRED:
- restaurant_id (number) - ***CRITICAL***: When user mentions a restaurant name, look back in conversation history for the most recent search_restaurants tool result. Find the restaurant by name in the "restaurants" array and extract its "id" field. Set restaurant_id to that id.
- customer_name (string) - Extract from user message when they provide their name
- phone (string) - Extract phone number from user message
- date (YYYY-MM-DD) - Reuse from earlier conversation if available
- time (HH:MM) - Reuse from earlier conversation if available
- party_size (number) - Reuse from earlier conversation if available

***IMPORTANT***: 
1. If user just saw search results and mentions a restaurant name (e.g., "Toit" or "I want to book Toit"), set intent="book_table" and extract restaurant_id by looking up the name in the previous tool results.
2. When switching to book_table intent, carry forward date, time, and party_size from the earlier search slots.

Recommend tools ONLY when all REQUIRED slots are present.

Output JSON:
{
  "intent": "...",
  "slots": {...},
  "recommended_tools": [...],
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


def _build_step_instruction(plan: Dict[str, Any]) -> str:
    """
    Build step-by-step instruction for current conversation state.
    Guides LLM on exactly what to do next.
    """
    intent = plan.get("intent", "")
    slots = plan.get("slots", {})
    missing_slots = plan.get("missing_slots", [])
    recommended_tools = plan.get("recommended_tools", [])
    
    # Search restaurants flow
    if intent == "search_restaurants":
        city = slots.get("city")
        party_size = slots.get("party_size")
        date = slots.get("date")
        time = slots.get("time")
        cuisine = slots.get("cuisine")
        
        # All required info collected → call tool
        if city and party_size and date and time:
            tool_args = {"city": city, "party_size": party_size}
            if cuisine:
                tool_args["cuisine"] = cuisine
            
            return f"""
Current Step: Ready to search restaurants.

Collected Info:
- City: {city}
- Party Size: {party_size} people
- Date: {date}
- Time: {time}
{f'- Cuisine: {cuisine}' if cuisine else ''}

YOUR ACTION: Output ONLY this JSON:
TOOL: search_restaurants
ARGS: {json.dumps(tool_args)}
"""
        
        # Missing any required info - ask for ALL missing at once
        missing = []
        if not city:
            missing.append("city")
        if not party_size:
            missing.append("party size")
        if not date or not time:
            missing.append("date and time")
        
        if missing:
            questions = []
            if "city" in missing:
                questions.append("Which city would you like to dine in?")
            if "party size" in missing:
                questions.append("How many people will be dining?")
            if "date and time" in missing:
                questions.append("What date and time? (e.g., Feb 10 at 7pm)")
            
            combined_question = " ".join(questions)
            
            return f"""
Current Step: User wants to search restaurants. Missing: {', '.join(missing)}

YOUR ACTION: Ask ALL questions at once:
"{combined_question} You can also tell me your cuisine preference if you have one."

DO NOT call any tool.
"""
    
    # Booking flow
    if intent == "book_table":
        restaurant_id = slots.get("restaurant_id")
        customer_name = slots.get("customer_name")
        phone = slots.get("phone")
        date = slots.get("date")
        time = slots.get("time")
        party_size = slots.get("party_size")
        
        # All info collected → call tool
        if all([restaurant_id, customer_name, phone, date, time, party_size]):
            tool_args = {
                "restaurant_id": restaurant_id,
                "customer_name": customer_name,
                "phone": phone,
                "date": date,
                "time": time,
                "party_size": party_size
            }
            
            return f"""
Current Step: Ready to book table.

YOUR ACTION: Output ONLY this JSON:
TOOL: book_table
ARGS: {json.dumps(tool_args)}
"""
        
        # Build list of missing information
        missing = []
        if not restaurant_id:
            missing.append("restaurant name")
        if not customer_name:
            missing.append("your name")
        if not phone:
            missing.append("phone number")
        
        # Ask for ALL missing booking info at once
        if missing:
            if not restaurant_id:
                # After search results - ask for everything
                return """
Current Step: User saw restaurant list. Need to collect booking details.

YOUR ACTION: 
You MUST ask this EXACT question:
"Which restaurant would you like to book? Please also provide your name and phone number for the reservation."

DO NOT call any tool. DO NOT proceed without asking this question.
"""
            else:
                # Have restaurant but missing personal details
                questions_needed = []
                if not customer_name:
                    questions_needed.append("name")
                if not phone:
                    questions_needed.append("phone number")
                    
                return f"""
Current Step: User selected restaurant (ID: {restaurant_id}). Still need: {', '.join(questions_needed)}

YOUR ACTION:
You MUST ask this EXACT question:
"Great! What's your name and phone number for the reservation?"

DO NOT call any tool. DO NOT proceed without asking for name and phone.
"""
        
        # Have all personal details but missing date/time (shouldn't happen often)
        if not date or not time:
            return """
Current Step: Have restaurant and customer details, but need date/time confirmation.

YOUR ACTION: Ask:
"What date and time would you like to book? (e.g., Feb 10 at 7pm)"

DO NOT call any tool.
"""
    
    # Default: general conversation
    return """
Current Step: General conversation.

YOUR ACTION: Respond naturally and help the user get started.
Ask: "Hi! I can help you find and book restaurants. Please tell me: Which city would you like to dine in? How many people will be dining? And what date and time? (You can also mention your cuisine preference if you have one)"
"""


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
    
    print(f"\n🧠 PLANNER OUTPUT:")
    print(f"   Intent: {plan.get('intent')}")
    print(f"   Slots: {plan.get('slots')}")
    print(f"   Recommended Tools: {plan.get('recommended_tools')}")
    print(f"   Missing Slots: {plan.get('missing_slots')}\n")

    # 2. BUILD STEP-SPECIFIC INSTRUCTION
    step_instruction = _build_step_instruction(plan)
    
    print(f"\n📋 STEP INSTRUCTION:\n{step_instruction}\n")

    orchestrator_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": step_instruction},
    ] + messages

    # 3. EXECUTOR - Generate response (may include tool call)
    try:
        assistant_text = llm_chat(client, orchestrator_messages, max_tokens=1024)
        print(f"\n🤖 LLM Response:\n{assistant_text}\n")
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

    logger.info(f"🔧 Executing tool: {tool_name}")
    logger.info(f"📝 Tool arguments: {json.dumps(tool_args, indent=2)}")

    tool_output = execute_tool(tool_name, tool_args)

    logger.info(f"✅ Tool executed successfully")
    logger.info(f"📊 Tool output length: {len(tool_output)} chars")

    # Log first 500 chars of tool output for debugging
    try:
        parsed = json.loads(tool_output)
        if tool_name == "search_restaurants":
            total = parsed.get("total", 0)
            restaurants = parsed.get("restaurants", [])
            logger.info(
                f"🍽️  Found {total} restaurants, returning top {len(restaurants)}"
            )
            if restaurants:
                logger.info(
                    f"📋 First restaurant: {restaurants[0].get('name', 'Unknown')}"
                )
    except:
        logger.warning(f"⚠️  Could not parse tool output as JSON")
        logger.info(f"Raw output preview: {tool_output[:200]}...")

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
        tool_data = json.loads(tool_output)
        
        # For search_restaurants, format results directly from JSON
        if tool_name == "search_restaurants":
            if "error" in tool_data:
                final_answer = tool_data["error"]
            elif tool_data.get("total", 0) == 0:
                final_answer = "I couldn't find any restaurants matching your criteria. Try adjusting your preferences."
            else:
                # Format the EXACT restaurants from the tool results
                restaurants = tool_data.get("restaurants", [])
                final_answer = f"I found {tool_data['total']} restaurants for you:\n\n"
                
                for i, r in enumerate(restaurants, 1):
                    cuisines = ", ".join(r.get("cuisine", []))
                    final_answer += f"{i}. **{r['name']}** - {r['area']}\n"
                    final_answer += f"   📍 {r['city']} | 🍽️ {cuisines}\n"
                    final_answer += f"   ⭐ {r['rating']}/5 | 💰 ₹{r['price_per_person']}/person ({r['price_range']})\n\n"
                
                # COMPULSORY: Ask for ALL booking details at once
                final_answer += "Which restaurant would you like to book? Please also provide your name and phone number for the reservation."
        
        # For bookings, use the formatted message from tool
        elif tool_name == "book_table":
            final_answer = tool_data.get("message", tool_output)
        
        else:
            # Fallback for other tools
            final_answer = tool_output
            
    except Exception as e:
        # If parsing fails, use raw output
        logger.warning(f"Failed to parse tool output: {e}")
        final_answer = f"Executed {tool_name}. Result: {tool_output}"

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
        return "Hi! I can help you find and book restaurants. Please tell me: Which city would you like to dine in? How many people will be dining? And what date and time? (You can also mention your cuisine preference if you have one)"

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

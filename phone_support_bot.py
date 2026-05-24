import os
from typing import TypedDict, Annotated, List, Optional
from datetime import datetime
import operator
from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field
import json
from langchain_community.chat_models import ChatOllama

''' THE IMPORTS '''
# load environment variables
load_dotenv()

# initializing ChatGpt
'''llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.3,
    api_key=os.getenv("OPENAI_API_KEY")
)'''

# initialising local llm via Ollama
llm = ChatOllama(
    model="llama3.2:1b",
    temperature=0.3,
    base_url="http://localhost:11434"
)

# defining state structure
class AgentState(TypedDict):
    """state of the customer support agent"""
    messages: Annotated[List, operator.add] # conversation history
    user_query: str # current user query
    customer_name: Optional[str] # customer name if provided
    current_step: str # current step in conversation
    needs_human: bool # flag for human escalation
    collected_info: dict # information collected during conversation

print("Environment setup complete!")
print("LLM initialized with Ollama llama3.2:1b")

''' CREATING TOOL SCHEMAS '''
# define Pydantic models for our tools
class PhoneModelQuery(BaseModel):
    # query about models and specifications
    brand: Optional[str] = Field(None, description="Phone brand")
    model: Optional[str] = Field(None, description="Specific model name")
    feature: Optional[str] = Field(None, description="Specific feature to compare")

class RepairServiceQuery(BaseModel):
    # query about repair services
    phone_type: str = Field(..., description="Type of phone needing repair")
    issue: str = Field(..., description="Description of the problem")
    urgency: Optional[str] = Field("standard", description="Repair urgency: standard, urgent")

class StatusCheck(BaseModel):
    # checking repair or order status
    ticket_number: Optional[str] = Field(None, description="Repair ticket number")
    order_number: Optional[str] = Field(None, description="Order number")
    email: Optional[str] = Field(None, description="Customer email for lookup")

class AppointmentBooking(BaseModel):
    # book a repair appointment
    customer_name: str = Field(..., description="Customer's name")
    phone_type: str = Field(..., description="Type of phone to repair")
    issue: str = Field(..., description="Description of issue")
    preferred_date: str = Field(..., description="Preferred appointment date (YYYY-MM-DD)")
    preferred_time: str = Field(..., description="Preferred time slot")
    contact: str = Field(..., description="Contact phone or email")

''' IMPLEMENTING THE TOOL FUNCTIONS '''
# mock database for demonstration, in real life it will connect to actual databases
# Mock database for demonstration
# In real application, connect to actual databases
PHONE_INVENTORY = {
    "iPhone 15": {
        "price": "$799",
        "storage": ["128GB", "256GB", "512GB"],
        "colors": ["Black", "Blue", "Green", "Yellow", "Pink"],
        "specs": {
            "display": "6.1-inch Super Retina XDR",
            "camera": "48MP Main + 12MP Ultra Wide",
            "battery": "Up to 20 hours video playback"
        }
    },
    "Samsung Galaxy S23": {
        "price": "$799",
        "storage": ["128GB", "256GB"],
        "colors": ["Phantom Black", "Cream", "Green", "Lavender"],
        "specs": {
            "display": "6.1-inch Dynamic AMOLED 2X",
            "camera": "50MP Wide + 12MP Ultra Wide + 10MP Telephoto",
            "battery": "3900mAh"
        }
    }
}

REPAIR_JOBS = {
    "TICKET-001": {
        "status": "In Progress",
        "estimated_completion": "2024-01-15",
        "phone": "iPhone 14",
        "issue": "Screen Replacement"
    },
    "TICKET-002": {
        "status": "Completed",
        "completed_date": "2024-01-10",
        "phone": "Samsung S22",
        "issue": "Battery Replacement"
    }
}

# Tool 1: Get Phone Information
def get_phone_info(brand: str = None, model: str = None, feature: str = None) -> str:
    """Get information about phone models"""
    if model and model in PHONE_INVENTORY:
        phone = PHONE_INVENTORY[model]
        return f"""
        {model} Information:
        Price: {phone['price']}
        Available Storage: {', '.join(phone['storage'])}
        Colors: {', '.join(phone['colors'])}
        Specifications:
        - Display: {phone['specs']['display']}
        - Camera: {phone['specs']['camera']}
        - Battery: {phone['specs']['battery']}
        """
    elif brand:
        matching_models = [m for m in PHONE_INVENTORY.keys() if brand.lower() in m.lower()]
        if matching_models:
            return f"We have these {brand} models: {', '.join(matching_models)}. Ask about any specific model!"
        else:
            return f"Sorry, we don't have {brand} models in stock currently."
    else:
        return f"Available phones: {', '.join(PHONE_INVENTORY.keys())}"

# Tool 2: Get Repair Information
def get_repair_info(phone_type: str, issue: str, urgency: str = "standard") -> str:
    """Provide repair service information"""
    repair_prices = {
        "screen": {"iPhone": "$199", "Samsung": "$179", "Other": "$159"},
        "battery": {"iPhone": "$89", "Samsung": "$79", "Other": "$69"},
        "camera": {"iPhone": "$149", "Samsung": "$129", "Other": "$119"},
        "water_damage": {"iPhone": "$299", "Samsung": "$279", "Other": "$259"}
    }

    issue_lower = issue.lower()
    price_key = None
    for key in repair_prices:
        if key in issue_lower:
            price_key = key
            break

    if price_key:
        brand = "iPhone" if "iphone" in phone_type.lower() else "Samsung" if "samsung" in phone_type.lower() else "Other"
        price = repair_prices[price_key][brand]
        turnaround = "1-2 days" if urgency == "urgent" else "3-5 business days"
        return f"""
        Repair Estimate:
        Phone: {phone_type}
        Issue: {issue}
        Estimated Cost: {price}
        Turnaround Time: {turnaround}
        Warranty: 90 days on all repairs
        """
    return f"We can repair {phone_type} with {issue}. Please visit our store for exact pricing."

# Tool 3: Check Repair Status
def check_repair_status(ticket_number: str = None, order_number: str = None, email: str = None) -> str:
    """Check status of repair or order"""
    if ticket_number and ticket_number in REPAIR_JOBS:
        job = REPAIR_JOBS[ticket_number]
        if job['status'] == 'Completed':
            return f"Repair {ticket_number} was completed on {job.get('completed_date')}. Your {job['phone']} with {job['issue']} is ready for pickup!"
        else:
            return f"Repair {ticket_number} for {job['phone']} ({job['issue']}) is {job['status']}. Estimated completion: {job['estimated_completion']}."
    return "Please provide a valid ticket number. You can find it on your repair receipt."

# Tool 4: Book Appointment
def book_appointment(customer_name: str, phone_type: str, issue: str,
                    preferred_date: str, preferred_time: str, contact: str) -> str:
    """Book a repair appointment"""
    # Simple validation
    try:
        datetime.strptime(preferred_date, "%Y-%m-%d")
    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD."

    available_times = ["9:00 AM", "11:00 AM", "2:00 PM", "4:00 PM"]
    if preferred_time not in available_times:
        return f"Available times: {', '.join(available_times)}"

    appointment_id = f"APT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return f"""
    ✅ Appointment Booked Successfully!
    Appointment ID: {appointment_id}
    Customer: {customer_name}
    Phone: {phone_type}
    Issue: {issue}
    Date: {preferred_date}
    Time: {preferred_time}
    Contact: {contact}

    Please bring your phone and any accessories. Arrive 10 minutes early.
    """

# Tool 5: Basic Troubleshooting
def provide_troubleshooting(issue: str) -> str:
    """Provide basic troubleshooting steps"""
    troubleshooting = {
        "battery": [
            "1. Check for apps using excessive battery in Settings",
            "2. Enable battery saver mode",
            "3. Update to latest software version",
            "4. If problem persists, battery may need replacement"
        ],
        "screen": [
            "1. Clean screen with microfiber cloth",
            "2. Check for screen protector issues",
            "3. Restart your phone",
            "4. Check display settings"
        ],
        "slow": [
            "1. Close unused apps",
            "2. Clear cache and temporary files",
            "3. Check available storage space",
            "4. Update all apps and system"
        ],
        "wifi": [
            "1. Toggle airplane mode on/off",
            "2. Forget and reconnect to WiFi network",
            "3. Restart your router",
            "4. Reset network settings (Settings > General > Reset)"
        ]
    }

    issue_lower = issue.lower()
    for key, steps in troubleshooting.items():
        if key in issue_lower:
            return f"Troubleshooting steps for {issue}:\n" + "\n".join(steps)

    return f"For {issue}, try these general steps:\n1. Restart your phone\n2. Update software\n3. Check for specific error messages\n4. Visit our store for diagnosis"

print("✅ Tool functions defined successfully!")


''' Building the LangGraph Agent '''
''' creating the graph nodes '''

#defining intents for routing
INTENTS = [
    "product_info",
    "repair_info",
    "status_check",
    "appointment",
    "troubleshooting",
    "warranty_check",
    "contact_info",
    "human_escalation"
]

# memory conversation information
def update_memory(state: AgentState, query:str):
    """Extract and store some important conversation information"""
    
    memory = state.get("collected_info", {})
    
    extraction_prompt = f"""
    Extract useful customer informaion from this message.
    
    Message:
    "{query}"
    
    Return Only valid JSON format:
    
    Example:
    {{
        "phone_type": "...",
        "customer_name": "...",
    }}
    
    Do not generate schema.
    Do not explain.
    Do not add extra fields. 
    If information is missing, return empty fields.
    """
    
    try:
        response = llm.invoke(extraction_prompt)
        
        raw = response.content.strip()
        
        print(f"🧠 Raw memory respone: {raw}")
        
        start = raw.find("{")
        end = raw.rfind("}") + 1
        
        if start != -1 and end != -1:
            
            json_text = raw[start:end]
            data = json.loads(json_text)
            
            allowed_keys = ["phone_type", "customer_name"]
            
            for key in allowed_keys:
                value = data.get(key)
                
                # prevent: dict pollution, schema pollution and malformed memory objects
                if isinstance(value, str) and value.strip():
                    memory[key] = value.strip()
                    
    except Exception as e:
        print(f"Error in memory extraction: {e}")
    
    #conversational memory store    
    state["collected_info"] = memory 
    
# defining router function
def router(state: AgentState) -> str:        
    """Hybrid AI + rule-based intent router"""
    
    last_message = state["messages"][-1]
    
    if not isinstance(last_message, HumanMessage):
        return "general_chat"
    
    query = last_message.content.lower()
    
    # Update memory with any extracted information
    update_memory(state, query)
    
    # Strong repair keywords
    repair_keywords = ["repair", "fix", "broken", "damage", "screen", "battery", "camera", "water", "overheating", "not charging", "cracked", "unresponsive"]
    
    # Strong appointment keywords
    appointment_keywords = ["appointment", "schedule", "book", "meet", "visit", "come in", "reserve"]
    
    # Strong human escalation keywords
    human_keywords = ["human", "agent", "representative", "speak to", "talk to", "help me", "need help", "customer service"]
    
    # Strong status check keywords
    status_keywords = ["status", "track", "update", "progress", "repair status", "order status", "ticket"]
    
    # Hybrid rule checks
    if any(keyword in query for keyword in repair_keywords):
        intent = "repair_info"
    elif any(keyword in query for keyword in appointment_keywords):
        intent = "appointment"
    elif any(keyword in query for keyword in human_keywords):
        intent = "human_escalation"
    elif any(keyword in query for keyword in status_keywords):
        intent = "status_check"
    else:
        # fallback to LLM classification for more ambiguous queries
        routing_prompt = f"""
        You are an intent classifier for a phone repair business.

        Classify the user's message into EXACTLY ONE of these categories:

        - product_info
        - repair_info
        - status_check
        - appointment
        - human_escalation
        - general_chat

        User message:
        "{query}"

        Return ONLY the category name.
        """
    
        try:
            response = llm.invoke(routing_prompt)
        
            intent = response.content.strip().lower()
        
        except:
            intent = "general_chat"
            
    print(f"🔍 Detected intent: {intent}")
    return intent

# Define node functions
def product_info_node(state: AgentState) -> dict:
    """Handle product information queries"""
    query = state["messages"][-1].content
    response = get_phone_info(model=query)  # Simplified
    state["messages"].append(AIMessage(content=response))
    state["current_step"] = "product_info"
    return state

# Defines repair node functions
def repair_info_node(state: AgentState) -> dict:    
    '''Handle repair quries smarter'''
    
    query = state["messages"][-1].content
    
    # get conversation history
    memory = state.get("collected_info", {})
    
    # default fallback values
    phone_type = memory.get("phone_type", "Unknown Phone")
    issue = "general repair"
    
    query_lower = query.lower()
    
    # Rule-based issue detection (more reliable)
    if any(word in query_lower for word in ["screen", "display", "crack", "cracked"]):
        issue = "screen"
    elif any(word in query_lower for word in ["battery", "charge", "charging", "drains", "drain"]):
        issue = "battery"
    elif any(word in query_lower for word in ["camera", "photo", "picture", "video", "lens", "focus", "blurry"]):
        issue = "camera"
    elif any(word in query_lower for word in ["water", "liquid", "spill", "wet", "drowned", "submerged", "moisture", "humidity"]):
        issue = "water_damage"
    # optional AI enhancement    
    extraction_prompt = f"""
     Extract the phone type from this message.

    Message:
    "{query}"

    Return Only valid JSON format:
    
    Example
    {{
        "phone_type": "...",
    }}
    """
        
    try:
        llm_response = llm.invoke(extraction_prompt)
        
        raw_content = llm_response.content.strip()
        print(f"🔍 Debug extraction response: {raw_content}")
    
        # trying to extarct JSON safely
        start = raw_content.find("{")
        end = raw_content.rfind("}") + 1
    
        if start != -1 and end != -1:
            json_text = raw_content[start:end]
        
            data = json.loads(json_text)
            extracted_phone = data.get("phone_type")

            if isinstance(extracted_phone, str) and extracted_phone.strip() and extracted_phone.lower() != "null":
                phone_type = extracted_phone.strip()
                
    except Exception as e:
        print(f"Extraction error: {e}")

    repair_response = get_repair_info(
        phone_type=phone_type, issue=issue
        )
    state["messages"].append(
        AIMessage(content=repair_response)
        )
    state["current_step"] = "repair_info"
    return state

def status_check_node(state: AgentState) -> dict:
    """Handle status check queries"""
    query = state["messages"][-1].content
    # Extract ticket number (in real app, use regex)
    ticket_num = None
    if "TICKET" in query:
        import re
        match = re.search(r'TICKET-\d+', query)
        if match:
            ticket_num = match.group()

    response = check_repair_status(ticket_number=ticket_num)
    state["messages"].append(AIMessage(content=response))
    state["current_step"] = "status_check"
    return state

# Handled in steps to give direction
def appointment_node(state: AgentState) -> dict:
    """Handle appointment booking"""
    query = state["messages"][-1].content
    collected = state.get("collected_info", {})
    
    # start booking process
    if not collected:
        response = "Let's book your appointment! What's your name?"
        state["collected_info"] = {"step": "get_name"}
    
    elif collected("step") == "get_name":
        collected["customer_name"] = query
        collected["step"] = "phone_model"
        response = "What phone model do you need repaired?"
        
    elif collected("step") == "phone_model":
        collected["phone_type"] = query
        collected["step"] = "issue"
        response = "Please describe the issue with your phone."
        
    elif collected("step") == "issue":
        collected["issue"] = query
        collected["step"] = "date"
        response = "What date would you prefer? (YYYY-MM-DD)"
        
    elif collected("step") == "date":
        collected["date"] = query
        collected["step"] = "time"
        response = "What time would you prefer? (e.g., 2:00 PM)"
        
    elif collected("step") == "time":
        collected["time"] = query
        
        response = book_appointment(
            customer_name=collected["customer_name"],
            phone_type=collected["phone_model"],
            issue=collected["issue"],
            preferred_date=collected["date"],
            preferred_time=collected["time"],
            contact="Not Provided"
        )
        
        collected["step"] = "completed"
    else:
        response = "Your appointment is already booked. If you want to book another, please let me know!"

    state["collected_info"] = collected
    state["messages"].append(AIMessage(content=response))
    state["current_step"] = "appointment_booking"
    
    return state


def general_chat_node(state: AgentState) -> dict:
    """Handle general conversation using LLM"""
    # Get conversation history
    conversation = state["messages"]

    # Create system prompt
    system_prompt = """You are a helpful customer support agent for PhoneHub, a phone sales and repair store.
    You can help with:
    - Phone information and specifications
    - Repair services and pricing
    - Checking repair status
    - Booking appointments
    - Basic troubleshooting
    - Warranty information
    - Store locations and hours

    Be friendly, professional, and helpful. If you don't know something, offer to connect the customer with a human agent."""

    # Prepare messages for LLM
    messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation[-5:]:  # Last 5 messages for context
        if isinstance(msg, HumanMessage):
            messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            messages.append({"role": "assistant", "content": msg.content})

    # Get response from LLM
    response = llm.invoke(messages)

    state["messages"].append(AIMessage(content=response.content))
    state["current_step"] = "general_chat"
    return state

def human_escalation_node(state: AgentState) -> dict:
    """Escalate to human agent"""
    response = """I'm connecting you to a human agent now.

    In the meantime:
    - Call: +254748433574
    - Email: daggerone24@gmail.com
    - Live Chat: Available on our website

    Estimated wait time: 5 minutes.
    Please have your ticket/order number ready."""

    state["messages"].append(AIMessage(content=response))
    state["needs_human"] = True
    state["current_step"] = "human_escalation"
    return state

print("✅ Graph nodes defined successfully!")

''' building and compiling the graph '''
# build the graph
workflow = StateGraph(AgentState)

# adding nodes
workflow.add_node("product_info", product_info_node)
workflow.add_node("repair_info", repair_info_node)
workflow.add_node("status_check", status_check_node)
workflow.add_node("appointment", appointment_node)
workflow.add_node("general_chat", general_chat_node)
workflow.add_node("human_escalation", human_escalation_node)

# this block led to many AI calls for one message so it will be chopped off
''' 
# entry point
workflow.set_entry_point("general_chat")

# conditional edges
workflow.add_conditional_edges(
    "general_chat",
    router,
    {
        "product_info": "product_info",
        "repair_info": "repair_info",
        "status_check": "status_check",
        "appointment": "appointment",
        "human_escalation": "human_escalation",
        "general_chat": "general_chat"
    }
)

# adding edges from other nodes back to general_chat
for node in ["product_info", "repair_info", "status_check", "appointment"]:
    workflow.add_edge(node, "general_chat")

# human escalation ends conversation
workflow.add_edge("human_escalation", END)
'''

''' This is the replacement for the above block to avoid multiple LLM calls '''
# Router node
workflow.add_node("router", lambda state: (state))

# router as entry point
workflow.set_entry_point("router")

# router decides destination immediatley
workflow.add_conditional_edges(
    "router",
    router,
    {
        "product_info": "product_info",
        "repair_info": "repair_info",
        "status_check": "status_check",
        "appointment": "appointment",
        "human_escalation": "human_escalation",
        "general_chat": "general_chat"
    }
)

# End all nodes after response
workflow.add_edge("product_info", END)
workflow.add_edge("repair_info", END)
workflow.add_edge("status_check", END)
workflow.add_edge("appointment", END)
workflow.add_edge("general_chat", END)
workflow.add_edge("human_escalation", END)


# compile the graph
app = workflow.compile()

print("Graph built and compiled successfully!")
print("customer support bot is ready")

# test function
def test_bot():
    """Test the customer support bot"""
    print("\n" + "="*50)
    print("PHONEHUB CUSTOMER SUPPORT BOT")
    print("="*50)
    print("\nType 'quit' to exit, 'human' to speak with agent\n")

    # Initial state
    initial_state = AgentState(
        messages=[],
        user_query="",
        customer_name=None,
        current_step="start",
        needs_human=False,
        collected_info={}
    )

    while True:
        # Get user input
        user_input = input("\n👤 You: ").strip()
        if not user_input:
                print("⚠️ Please enter a message.")
                continue

        if user_input.lower() in ['quit', 'exit', 'bye', 'close']:
            print("Goodbye! 👋")
            break

        if user_input.lower() == 'human':
            user_input = "I want to speak with a human agent"

        # Add user message to state
        initial_state["messages"].append(HumanMessage(content=user_input))

        # Invoke the graph
        result = app.invoke(initial_state, {"recursion_limit":100})

        # Get the last AI response
        last_message = result["messages"][-1]

        print(f"\n🤖 Bot: {last_message.content}")

        # Update state
        initial_state = result
        
        #debug visibility
        print(f"\n🧠 Memory: {initial_state.get('collected_info')}")

        # Check if human escalation occurred
        if result.get("needs_human"):
            print("\n⚠️  Please wait while we connect you to a human agent...")
            break

# Run test if script is executed directly
if __name__ == "__main__":
    test_bot()
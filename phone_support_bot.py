import os
from typing import TypedDict, Annotated, List, Optional
from datetime import datetime
import operator
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field
import json

''' THE IMPORTS '''
# load environment variables
load_dotenv()

# initializing ChatGpt
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.3,
    api_key=os.getenv("OPENAI_API_KEY")
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
print("LLM initialized with gpt-4.1-mini")

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
# mock database for demonstration, in rea life it will connect to actual databases
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
# defining router function
def router(state: AgentState) -> str:
    """Route to appropriate node based on conversation state"""
    last_message = state["messages"][-1]

    if isinstance(last_message, HumanMessage):
        query = last_message.content.lower()

        # Check for specific intents
        if any(word in query for word in ["phone", "model", "spec", "price", "buy"]):
            return "product_info"
        elif any(word in query for word in ["repair", "fix", "broken", "damage"]):
            return "repair_info"
        elif any(word in query for word in ["status", "track", "check", "ticket"]):
            return "status_check"
        elif any(word in query for word in ["appointment", "schedule", "book", "meet"]):
            return "appointment"
        elif any(word in query for word in ["help", "trouble", "issue", "problem"]):
            return "troubleshooting"
        elif any(word in query for word in ["warranty", "guarantee", "cover"]):
            return "warranty_check"
        elif any(word in query for word in ["contact", "store", "location", "hours"]):
            return "contact_info"
        elif any(word in query for word in ["human", "agent", "speak to", "representative"]):
            return "human_escalation"
        else:
            return "general_chat"

    return "general_chat"

# Define node functions
def product_info_node(state: AgentState) -> dict:
    """Handle product information queries"""
    query = state["messages"][-1].content
    response = get_phone_info(model=query)  # Simplified
    state["messages"].append(AIMessage(content=response))
    state["current_step"] = "product_info"
    return state

def repair_info_node(state: AgentState) -> dict:
    """Handle repair service queries"""
    query = state["messages"][-1].content
    # Extract info from query (in real app, use NLP)
    if "screen" in query.lower():
        issue = "screen"
    elif "battery" in query.lower():
        issue = "battery"
    else:
        issue = "general repair"

    response = get_repair_info(phone_type="Phone", issue=issue)
    state["messages"].append(AIMessage(content=response))
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

def appointment_node(state: AgentState) -> dict:
    """Handle appointment booking"""
    query = state["messages"][-1].content

    # In full implementation, we'd collect information over multiple steps
    response = "To book an appointment, I'll need:\n1. Your name\n2. Phone model\n3. Issue description\n4. Preferred date & time\n5. Contact info\n\nPlease provide these details or say 'book appointment' to start the process."

    if "book appointment" in query.lower():
        # Start booking process
        response = "Let's book your appointment! What's your name?"
        state["collected_info"] = {"step": "get_name"}

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
    - Call: 1-800-PHONEHUB
    - Email: support@phonehub.com
    - Live Chat: Available on our website

    Estimated wait time: 5 minutes.
    Please have your ticket/order number ready."""

    state["messages"].append(AIMessage(content=response))
    state["needs_human"] = True
    state["current_step"] = "human_escalation"
    return state

print("✅ Graph nodes defined successfully!")
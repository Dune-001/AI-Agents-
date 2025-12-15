# advanced_features.py
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
import pandas as pd

# Advanced: Create proper LangChain tools
@tool
def phone_information_tool(brand: str, model: str = None) -> str:
    """Get detailed information about phone models"""
    return get_phone_info(brand=brand, model=model)

@tool
def repair_quote_tool(phone_model: str, issue: str) -> str:
    """Get a repair quote"""
    return get_repair_info(phone_type=phone_model, issue=issue)

@tool
def appointment_scheduler(name: str, date: str, time: str) -> str:
    """Schedule a repair appointment"""
    return book_appointment(
        customer_name=name,
        phone_type="To be specified",
        issue="Diagnosis needed",
        preferred_date=date,
        preferred_time=time,
        contact="Provided by customer"
    )

# Create a knowledge base for FAQs
def create_knowledge_base():
    """Create a simple knowledge base"""
    faqs = pd.DataFrame({
        'question': [
            'What are your store hours?',
            'Do you offer warranty?',
            'How long does repair take?',
            'Do you buy old phones?'
        ],
        'answer': [
            'Mon-Fri: 9AM-7PM, Sat: 10AM-6PM, Sun: 11AM-5PM',
            'Yes! 1 year warranty on all repairs, 2 years on new phones',
            'Standard repairs: 3-5 days. Express service: 24 hours available',
            'Yes! We offer trade-in values. Bring your phone for appraisal'
        ]
    })
    return faqs

# Memory management
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

print("✅ Advanced features ready!")
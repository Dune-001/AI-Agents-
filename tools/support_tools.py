from langchain.tools import tool
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

class PhoneInventory:
    """Mock phone inventory database"""

    def __init__(self):
        self.phones = {
            "iPhone 15 Pro": {
                "model": "iPhone 15 Pro",
                "price": 999.00,
                "stock": 15,
                "specs": {
                    "display": "6.1-inch Super Retina XDR",
                    "processor": "A17 Pro",
                    "storage": "128GB/256GB/512GB/1TB",
                    "camera": "48MP main + 12MP ultra-wide + 12MP telephoto",
                    "battery": "Up to 23 hours video playback"
                },
                "colors": ["Black Titanium", "White Titanium", "Blue Titanium", "Natural Titanium"]
            },
            "Samsung Galaxy S24": {
                "model": "Samsung Galaxy S24",
                "price": 799.99,
                "stock": 22,
                "specs": {
                    "display": "6.2-inch Dynamic AMOLED 2X",
                    "processor": "Snapdragon 8 Gen 3",
                    "storage": "128GB/256GB",
                    "camera": "50MP main + 12MP ultra-wide + 10MP telephoto",
                    "battery": "4000mAh"
                },
                "colors": ["Onyx Black", "Marble Gray", "Cobalt Violet", "Amber Yellow"]
            },
            "Google Pixel 8": {
                "model": "Google Pixel 8",
                "price": 699.00,
                "stock": 18,
                "specs": {
                    "display": "6.2-inch Actua display",
                    "processor": "Google Tensor G3",
                    "storage": "128GB/256GB",
                    "camera": "50MP main + 12MP ultra-wide",
                    "battery": "Up to 24 hours"
                },
                "colors": ["Obsidian", "Hazel", "Rose", "Mint"]
            }
        }

    def check_availability(self, model: str, color: Optional[str] = None) -> Dict[str, Any]:
        """Check if a phone model is in stock"""
        if model not in self.phones:
            return {"available": False, "message": f"Model '{model}' not found"}

        phone = self.phones[model]
        if color and color not in phone["colors"]:
            return {"available": False, "message": f"Color '{color}' not available for {model}"}

        return {
            "available": phone["stock"] > 0,
            "stock": phone["stock"],
            "colors": phone["colors"],
            "price": phone["price"]
        }

    def get_specs(self, model: str) -> Dict[str, Any]:
        """Get specifications for a phone model"""
        if model not in self.phones:
            return {"error": f"Model '{model}' not found"}

        return self.phones[model]["specs"]

    def compare_models(self, model1: str, model2: str) -> Dict[str, Any]:
        """Compare two phone models"""
        if model1 not in self.phones or model2 not in self.phones:
            return {"error": "One or both models not found"}

        return {
            "model1": self.phones[model1],
            "model2": self.phones[model2],
            "price_difference": abs(self.phones[model1]["price"] - self.phones[model2]["price"])
        }

class RepairServices:
    """Mock repair services database"""

    def __init__(self):
        self.repair_prices = {
            "screen_replacement": {
                "iPhone": 129.99,
                "Samsung": 119.99,
                "Google": 109.99,
                "Other": 139.99,
                "time": "1-2 hours"
            },
            "battery_replacement": {
                "iPhone": 89.99,
                "Samsung": 79.99,
                "Google": 69.99,
                "Other": 99.99,
                "time": "45-60 minutes"
            },
            "camera_repair": {
                "iPhone": 149.99,
                "Samsung": 139.99,
                "Google": 129.99,
                "Other": 159.99,
                "time": "1-3 hours"
            },
            "water_damage": {
                "iPhone": 199.99,
                "Samsung": 189.99,
                "Google": 179.99,
                "Other": 219.99,
                "time": "2-4 hours"
            },
            "charging_port": {
                "iPhone": 79.99,
                "Samsung": 69.99,
                "Google": 59.99,
                "Other": 89.99,
                "time": "30-45 minutes"
            }
        }

        self.warranty_info = {
            "new_phone": "1 year manufacturer warranty",
            "refurbished": "6 months store warranty",
            "repair": "90 days on parts and labor"
        }

    def estimate_repair_cost(self, phone_brand: str, issue: str) -> Dict[str, Any]:
        """Estimate repair cost for a specific issue"""
        if issue not in self.repair_prices:
            available_issues = list(self.repair_prices.keys())
            return {
                "error": f"Unknown issue '{issue}'. Available issues: {', '.join(available_issues)}"
            }

        price_info = self.repair_prices[issue]

        # Default to "Other" if brand not specified
        brand = phone_brand.capitalize() if phone_brand.capitalize() in ["Iphone", "Samsung", "Google"] else "Other"

        return {
            "issue": issue.replace("_", " ").title(),
            "brand": brand,
            "estimated_cost": price_info.get(brand, price_info["Other"]),
            "estimated_time": price_info["time"],
            "currency": "USD"
        }

    def check_warranty(self, product_type: str) -> str:
        """Check warranty information"""
        return self.warranty_info.get(product_type, "Please contact support for warranty information")

class AppointmentSystem:
    """Mock appointment booking system"""

    def __init__(self):
        self.appointments = {}
        self.next_id = 1
        self.working_hours = {
            "Monday": "9:00 AM - 6:00 PM",
            "Tuesday": "9:00 AM - 6:00 PM",
            "Wednesday": "9:00 AM - 6:00 PM",
            "Thursday": "9:00 AM - 6:00 PM",
            "Friday": "9:00 AM - 6:00 PM",
            "Saturday": "10:00 AM - 4:00 PM",
            "Sunday": "Closed"
        }

    def book_appointment(self, customer_name: str, service_type: str,
                        preferred_date: str, phone_model: str = "") -> Dict[str, Any]:
        """Book a repair appointment"""
        appointment_id = self.next_id
        self.next_id += 1

        appointment = {
            "id": appointment_id,
            "customer_name": customer_name,
            "service_type": service_type,
            "phone_model": phone_model,
            "date": preferred_date,
            "status": "Confirmed",
            "estimated_duration": "1 hour",
            "confirmation_code": f"REP{appointment_id:04d}"
        }

        self.appointments[appointment_id] = appointment

        return {
            "success": True,
            "appointment_id": appointment_id,
            "confirmation_code": appointment["confirmation_code"],
            "details": appointment
        }

    def check_appointment(self, appointment_id: int) -> Dict[str, Any]:
        """Check appointment status"""
        if appointment_id not in self.appointments:
            return {"error": f"Appointment ID {appointment_id} not found"}

        return self.appointments[appointment_id]

    def get_working_hours(self) -> Dict[str, str]:
        """Get store working hours"""
        return self.working_hours

class OrderTracking:
    """Mock order tracking system"""

    def __init__(self):
        self.orders = {
            "ORD001": {
                "order_id": "ORD001",
                "customer": "John Doe",
                "items": ["iPhone 15 Pro", "Case"],
                "status": "Shipped",
                "tracking_number": "UPS123456789",
                "estimated_delivery": "2024-01-15"
            },
            "ORD002": {
                "order_id": "ORD002",
                "customer": "Jane Smith",
                "items": ["Samsung Galaxy S24"],
                "status": "Processing",
                "tracking_number": None,
                "estimated_delivery": "2024-01-20"
            },
            "REP001": {
                "order_id": "REP001",
                "customer": "Bob Johnson",
                "items": ["Screen Replacement"],
                "status": "In Progress",
                "tracking_number": None,
                "estimated_completion": "2024-01-12"
            }
        }

    def track_order(self, order_id: str) -> Dict[str, Any]:
        """Track an order by ID"""
        if order_id not in self.orders:
            return {"error": f"Order ID {order_id} not found"}

        return self.orders[order_id]

    def check_repair_status(self, repair_id: str) -> Dict[str, Any]:
        """Check repair status"""
        # For simplicity, treat repair IDs same as order IDs
        return self.track_order(repair_id)

class PolicyFAQ:
    """Frequently Asked Questions about policies"""

    def __init__(self):
        self.faq = {
            "return_policy": {
                "question": "What is your return policy?",
                "answer": "We offer a 30-day return policy for unused devices in original packaging. Accessories can be returned within 14 days."
            },
            "shipping": {
                "question": "What are your shipping options?",
                "answer": "Standard shipping: 3-5 business days ($5.99), Express: 1-2 business days ($12.99), Overnight: Next day ($24.99)."
            },
            "warranty": {
                "question": "Do your repairs come with warranty?",
                "answer": "Yes, all repairs come with a 90-day warranty on both parts and labor."
            },
            "data_backup": {
                "question": "Should I backup my data before repair?",
                "answer": "Yes! We recommend backing up all data before any repair. We are not responsible for data loss during repair."
            },
            "payment_methods": {
                "question": "What payment methods do you accept?",
                "answer": "We accept Visa, MasterCard, American Express, PayPal, and Apple Pay."
            }
        }

    def get_answer(self, topic: str) -> Dict[str, str]:
        """Get FAQ answer for a topic"""
        if topic not in self.faq:
            available_topics = list(self.faq.keys())
            return {
                "error": f"Topic '{topic}' not found. Available topics: {', '.join(available_topics)}"
            }

        return self.faq[topic]

    def list_topics(self) -> List[str]:
        """List all available FAQ topics"""
        return list(self.faq.keys())

# Create global instances
inventory = PhoneInventory()
repair_services = RepairServices()
appointments = AppointmentSystem()
order_tracking = OrderTracking()
faq = PolicyFAQ()
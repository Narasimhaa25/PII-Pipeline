# producer/generate_synthetic_data.py
from faker import Faker
import random
import json
import os

fake = Faker()

QUERIES = [
    "I want to change my delivery address.",
    "Can I get a refund for my order?",
    "My credit card payment failed.",
    "Please cancel my subscription.",
    "I forgot my password and can't log in.",
    "Where is my package?",
    "Please update my phone number.",
    "Can I speak to a representative?",
    "I accidentally ordered twice, can I get a refund?",
    "Can you delete my account and data?",
    "Help me reset my account password",
    "I need to update my billing information",
    "Track my order status please",
    "Cancel my recent purchase",
    "Issue with my last payment"
]

def generate_message():
    """Generate a synthetic customer message with PII"""
    name = fake.name()
    email = fake.email()
    phone = fake.phone_number()
    address = fake.address().replace("\n", ", ")
    ssn = fake.ssn()
    credit_card = fake.credit_card_number()
    query = random.choice(QUERIES)
    
    # Create rich message with PII
    message = (
        f"Hi, my name is {name}. {query} "
        f"You can reach me at {email} or call {phone}. "
        f"My address is {address}. "
        f"SSN: {ssn}, Card: {credit_card}."
    )
    
    return {
        "customer_id": f"CUST{fake.random_int(1000, 9999)}",
        "message": message,
        "metadata": {
            "generated": True,
            "name": name,
            "email": email,
            "phone": phone
        }
    }

def generate_corpus(n=50):
    """Generate N synthetic customer messages"""
    print(f"🔧 Generating {n} synthetic customer messages with PII...")
    messages = [generate_message() for _ in range(n)]
    
    os.makedirs("data", exist_ok=True)
    output_file = "data/synthetic_corpus.json"
    
    with open(output_file, "w") as f:
        json.dump(messages, f, indent=2)
    
    print(f"✅ Generated {n} synthetic messages at {output_file}")
    print("\nSample message:")
    print(json.dumps(messages[0], indent=2))
    
    return messages

if __name__ == "__main__":
    generate_corpus(50)

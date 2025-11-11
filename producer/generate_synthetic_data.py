# producer/generate_synthetic_data.py
from faker import Faker
import random
import json
import os

fake = Faker()

def generate_message():
    """Generate a synthetic customer message with comprehensive PII for testing"""
    # Generate various PII types
    name = fake.name()
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = fake.email()
    phone = fake.phone_number()
    mobile = fake.phone_number()
    address = fake.address().replace("\n", ", ")
    street_address = fake.street_address()
    city = fake.city()
    state = fake.state()
    zipcode = fake.zipcode()
    country = fake.country()
    ssn = fake.ssn()
    # Generate valid credit card numbers for different types
    credit_card_types = ['visa', 'mastercard', 'amex', 'discover']
    card_type = random.choice(credit_card_types)
    credit_card = fake.credit_card_number(card_type=card_type)
    # Additional PII
    date_of_birth = fake.date_of_birth()
    passport = fake.passport_number()
    license_plate = fake.license_plate()
    bank_account = fake.iban()
    ip_address = fake.ipv4_public()
    url = fake.url()
    
    # Create varied message templates with different PII combinations
    templates = [
        f"Hi, my name is {name}. I need help with my account. You can reach me at {email} or call {phone}. My address is {address}. SSN: {ssn}, Card: {credit_card}.",
        f"Hello, I'm {first_name} {last_name}. My payment failed. Email: {email}, Phone: {phone}. Address: {street_address}, {city}, {state} {zipcode}. Credit card: {credit_card}.",
        f"Hi there, this is {name} from {country}. I forgot my password. Contact: {email} or {mobile}. DOB: {date_of_birth}. SSN: {ssn}. Card ending in {credit_card[-4:]}.",
        f"My name is {first_name}. I want to update my billing info. Email: {email}, Phone: {phone}. Address: {address}. Bank: {bank_account}. Card: {credit_card}.",
        f"Hello, I'm {name}. Track my order please. Email: {email}, Phone: {phone}. Shipping to: {street_address}, {city}, {state}. Card used: {credit_card}.",
        f"Hi, this is {first_name} {last_name}. Cancel my subscription. Contact info: {email}, {mobile}. Address: {address}. SSN: {ssn}. Payment card: {credit_card}.",
        f"My name is {name}. I need a refund. Email me at {email} or call {phone}. From {city}, {state}. Credit card {credit_card}. IP: {ip_address}.",
        f"Hello {name} here. Account security issue. Email: {email}, Phone: {phone}. Address: {address}. SSN: {ssn}. Card: {credit_card}. Passport: {passport}.",
        f"Hi, I'm {first_name}. Update my profile. Email: {email}, Mobile: {mobile}. Location: {street_address}, {city}, {zipcode}. Card: {credit_card}. License: {license_plate}.",
        f"This is {name} calling about my order. Email: {email}, Phone: {phone}. Shipping address: {address}. Payment: {credit_card}. DOB: {date_of_birth}.",
        f"Hello, my name is {first_name} {last_name}. I have a question about billing. Contact: {email} or {phone}. Address: {street_address}, {city}. Card: {credit_card}.",
        f"Hi there, this is {name}. My card was charged incorrectly. Email: {email}, Phone: {mobile}. From {country}. Card number: {credit_card}.",
        f"My name is {first_name}. Need to change delivery address. Email: {email}, Phone: {phone}. New address: {address}. Card: {credit_card}.",
        f"Hello, I'm {name}. Password reset issue. Email: {email}, Phone: {phone}. Location: {city}, {state}. SSN: {ssn}. Card: {credit_card}.",
        f"Hi, this is {first_name} {last_name}. Order status inquiry. Contact info: {email}, {mobile}. Address: {address}. Payment card: {credit_card}."
    ]
    
    message = random.choice(templates)
    
    return {
        "customer_id": f"CUST{fake.random_int(1000, 9999)}",
        "message": message,
        "metadata": {
            "generated": True,
            "pii_types": ["name", "email", "phone", "address", "ssn", "credit_card", "date_of_birth", "passport", "license_plate", "bank_account", "ip_address"],
            "card_type": card_type
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

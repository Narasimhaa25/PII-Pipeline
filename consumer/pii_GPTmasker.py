# consumer/pii_masker.py
import json
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from kafka import KafkaConsumer, KafkaProducer
from dotenv import load_dotenv
from consumer.pii_GPTagent import get_pii_agent

load_dotenv()
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")

consumer = KafkaConsumer(
    'input-events',
    bootstrap_servers=BOOTSTRAP,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='latest',  # Changed from 'earliest' to 'latest'
    enable_auto_commit=True,
    group_id='pii-masker-group-v2'  # Changed group ID to start fresh
)

producer = KafkaProducer(bootstrap_servers=BOOTSTRAP,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def run():
    print("PII masker with LangGraph agent started. Listening to input-events...")
    agent = get_pii_agent()
    
    for msg in consumer:
        event = msg.value
        customer_id = event.get("customer_id", "unknown")
        message = event.get("message", "")
        
        print(f"\n[{customer_id}] Processing message: {message[:50]}...")
        
        # Process message through LangGraph agent
        result = agent.process_message(message)
        
        # Send only masked message and customer_id
        minimal_message = {
            "customer_id": customer_id,
            "masked_message": result["masked_message"]
        }
        producer.send('sanitized-events', minimal_message)
        print(f"[{customer_id}] Masked: {result['masked_message']}")

if __name__ == "__main__":
    run()
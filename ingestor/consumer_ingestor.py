# ingestor/consumer_ingestor.py
"""
JSON-based ingestor that saves processed messages to JSON files.
No database required - all data stored in data/ directory.
"""
import asyncio
import json
import os
import time
from pathlib import Path
from datetime import datetime
from aiokafka import AIOKafkaConsumer
from dotenv import load_dotenv

load_dotenv()
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", os.getenv("KAFKA_BOOTSTRAP", "localhost:9092"))

# JSON file paths
DATA_DIR = Path(__file__).parent.parent / "data"
PROCESSED_FILE = DATA_DIR / "processed_messages.json"

def ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(exist_ok=True)

def load_processed_messages():
    """Load existing processed messages from JSON."""
    default = {"messages": [], "metadata": {"total": 0, "last_updated": None}}
    if PROCESSED_FILE.exists():
        try:
            with open(PROCESSED_FILE, 'r') as f:
                data = json.load(f)
            # If file is not a dict or missing 'messages', reset
            if not isinstance(data, dict) or "messages" not in data:
                return default
            return data
        except Exception:
            return default
    return default

def save_processed_message(event: dict):
    """Save a processed message to JSON file."""
    ensure_data_dir()
    
    # Load existing data
    data = load_processed_messages()
    
    # Create message record
    message_record = {
        "ticket_id": event.get("customer_id") or "unknown",
        "customer_id": event.get("customer_id") or "unknown",
        "original_message": event.get("original_message", ""),
        "masked_message": event.get("masked_message", ""),
        "detected_pii": event.get("detected_pii", {}),
        "agent_reasoning": event.get("reasoning", ""),
        "processor": event.get("meta", {}).get("processor", "langgraph-agent"),
        "processed_at": datetime.now().isoformat()
    }
    
    # Append new message
    data["messages"].append(message_record)
    data["metadata"]["total"] = len(data["messages"])
    data["metadata"]["last_updated"] = datetime.now().isoformat()
    
    # Save to file
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Saved message {message_record['ticket_id']} to {PROCESSED_FILE}")

async def handle_event(event: dict):
    """Handle incoming event from Kafka."""
    print(f"📥 Consumed message: {event}")
    save_processed_message(event)

async def consume_loop():
    """Consume messages from Kafka and save to JSON."""
    # Wait for Kafka to be fully ready
    print("⏳ Waiting 30 seconds for Kafka to be ready...")
    await asyncio.sleep(30)
    
    consumer = AIOKafkaConsumer(
        'sanitized-events',
        bootstrap_servers=BOOTSTRAP,
        group_id="ingestor-group",
        auto_offset_reset="earliest"
    )
    await consumer.start()
    
    print(f"📥 Ingestor started. Saving to {PROCESSED_FILE}")
    
    try:
        async for msg in consumer:
            event = json.loads(msg.value.decode('utf-8')) if isinstance(msg.value, (bytes, bytearray)) else msg.value
            await handle_event(event)
    finally:
        await consumer.stop()

async def main():
    """Main entry point."""
    ensure_data_dir()
    await consume_loop()

if __name__ == "__main__":
    asyncio.run(main())
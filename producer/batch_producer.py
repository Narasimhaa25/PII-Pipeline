import json
import asyncio
from pathlib import Path
from aiokafka import AIOKafkaProducer

async def send_synthetic_messages():
    """Read synthetic corpus and send all messages to Kafka."""
    
    # Initialize Kafka producer
    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    await producer.start()
    
    try:
        # Read synthetic corpus
        corpus_file = Path(__file__).parent.parent / 'data' / 'synthetic_corpus.json'
        
        if not corpus_file.exists():
            print(f"Error: {corpus_file} not found!")
            print("Please run: python producer/generate_synthetic_data.py")
            return
        
        with open(corpus_file, 'r') as f:
            messages = json.load(f)
        
        print(f"Loaded {len(messages)} messages from {corpus_file}")
        print(f"Sending messages to Kafka topic 'input-events'...\n")
        
        # Send each message to Kafka
        for idx, msg in enumerate(messages, 1):
            await producer.send_and_wait('input-events', msg)
            print(f"[{idx}/{len(messages)}] Sent message for customer {msg['customer_id']}")
            
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(0.1)
        
        print(f"\n✅ Successfully sent all {len(messages)} messages to Kafka!")
        print("Messages are being processed by the PII masking agent...")
        
    finally:
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(send_synthetic_messages())

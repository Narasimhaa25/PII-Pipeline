"""
Kafka Consumer for PII Masking using Presidio
Consumes messages from input-events topic, processes with Presidio agent,
and produces masked messages to sanitized-events topic.
"""

import asyncio
import json
import os
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from dotenv import load_dotenv
from pii_agent_presidio import PresidioPiiAgent

# Load environment variables
load_dotenv()

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
INPUT_TOPIC = os.getenv("INPUT_TOPIC", "input-events")
OUTPUT_TOPIC = os.getenv("OUTPUT_TOPIC", "sanitized-events")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "presidio-pii-masker-group")


async def consume_and_mask():
    """Main consumer loop using Presidio agent."""
    
    print("=" * 80)
    print("🔐 PRESIDIO PII MASKER - Starting...")
    print("=" * 80)
    print(f"Kafka Brokers: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Input Topic:   {INPUT_TOPIC}")
    print(f"Output Topic:  {OUTPUT_TOPIC}")
    print(f"Consumer Group: {CONSUMER_GROUP}")
    print("=" * 80)
    print()
    
    # Initialize Presidio agent
    print("Initializing Presidio PII Agent...")
    agent = PresidioPiiAgent()
    print("✓ Presidio agent ready")
    print()
    
    # Create Kafka consumer
    consumer = AIOKafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=CONSUMER_GROUP,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        enable_auto_commit=True
    )
    
    # Create Kafka producer
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda m: json.dumps(m).encode('utf-8')
    )
    
    try:
        # Start consumer and producer
        await consumer.start()
        await producer.start()
        print("✓ Connected to Kafka")
        print(f"🎧 Listening for messages on '{INPUT_TOPIC}'...")
        print()
        
        message_count = 0
        
        # Consume messages
        async for msg in consumer:
            try:
                message_count += 1
                data = msg.value
                
                customer_id = data.get("customer_id", "UNKNOWN")
                original_message = data.get("message", "")
                metadata = data.get("metadata", {})
                
                print(f"📨 [{message_count}] Processing message from customer: {customer_id}")
                
                # Process with Presidio agent
                result = agent.process_message(
                    customer_id=customer_id,
                    message=original_message,
                    metadata=metadata
                )
                
                # Send only masked message and customer_id
                minimal_message = {
                    "customer_id": result["customer_id"],
                    "masked_message": result["masked_message"]
                }
                await producer.send(OUTPUT_TOPIC, value=minimal_message)
                print(f"   ✓ Sent masked message to '{OUTPUT_TOPIC}' for {customer_id}")
                print()
                
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                print()
                continue
    
    except KeyboardInterrupt:
        print()
        print("=" * 80)
        print(f"🛑 Shutting down... Processed {message_count} messages")
        print("=" * 80)
    
    finally:
        # Clean up
        await consumer.stop()
        await producer.stop()
        print("✓ Disconnected from Kafka")


if __name__ == "__main__":
    asyncio.run(consume_and_mask())

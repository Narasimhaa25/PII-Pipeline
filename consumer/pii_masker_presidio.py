"""
Kafka Consumer for PII Masking using Presidio
Consumes messages from 'input-events' topic,
masks PII using Presidio agent, and produces masked
messages to 'sanitized-events' topic.
"""

import asyncio
import json
import os
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from dotenv import load_dotenv
from pii_agent_presidio import PresidioPiiAgent

load_dotenv()

# Auto-detect environment
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
INPUT_TOPIC = os.getenv("INPUT_TOPIC", "input-events")
OUTPUT_TOPIC = os.getenv("OUTPUT_TOPIC", "sanitized-events")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "presidio-pii-masker-group")


async def wait_for_kafka(bootstrap):
    """Retry connection until Kafka is reachable."""
    from aiokafka.errors import KafkaConnectionError
    for attempt in range(1, 11):
        try:
            producer = AIOKafkaProducer(bootstrap_servers=bootstrap)
            await producer.start()
            await producer.stop()
            print(f"✓ Kafka is reachable at {bootstrap}")
            return True
        except KafkaConnectionError:
            print(f"⏳ Waiting for Kafka... (attempt {attempt}/10)")
            await asyncio.sleep(5)
    print("❌ Kafka is not reachable after multiple attempts.")
    return False


async def consume_and_mask():
    print("=" * 80)
    print("🔐 PRESIDIO PII MASKER - Starting...")
    print("=" * 80)
    print(f"Kafka Brokers: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Input Topic:   {INPUT_TOPIC}")
    print(f"Output Topic:  {OUTPUT_TOPIC}")
    print(f"Consumer Group: {CONSUMER_GROUP}")
    print("=" * 80)
    print()

    # Wait until Kafka is ready
    if not await wait_for_kafka(KAFKA_BOOTSTRAP_SERVERS):
        return

    print("Initializing Presidio PII Agent...")
    agent = PresidioPiiAgent()
    print("✓ Presidio agent ready\n")

    consumer = AIOKafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=CONSUMER_GROUP,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda m: json.dumps(m).encode("utf-8"),
    )

    try:
        await consumer.start()
        await producer.start()
        print("✓ Connected to Kafka")
        print(f"🎧 Listening for messages on '{INPUT_TOPIC}'...\n")

        message_count = 0
        async for msg in consumer:
            try:
                message_count += 1
                data = msg.value
                customer_id = data.get("customer_id", "UNKNOWN")
                original_message = data.get("message", "")
                metadata = data.get("metadata", {})

                print(f"📨 [{message_count}] Processing message from customer: {customer_id}")

                result = agent.process_message(
                    customer_id=customer_id,
                    message=original_message,
                    metadata=metadata,
                )

                masked_payload = {
                    "customer_id": result["customer_id"],
                    "masked_message": result["masked_message"],
                }

                await producer.send(OUTPUT_TOPIC, value=masked_payload)
                print(f"   ✓ Sent masked message to '{OUTPUT_TOPIC}' for {customer_id}\n")

            except Exception as e:
                print(f"❌ Error processing message: {e}\n")
                continue

    except KeyboardInterrupt:
        print(f"\n🛑 Shutting down... Processed {message_count} messages\n")
    finally:
        await consumer.stop()
        await producer.stop()
        print("✓ Disconnected from Kafka\n")


if __name__ == "__main__":
    asyncio.run(consume_and_mask())
import json
import asyncio
import os
from pathlib import Path
from aiokafka import AIOKafkaProducer

async def send_synthetic_messages():
    """Read synthetic corpus and send all messages to Kafka."""

    # Auto-detect environment
    # If running inside Docker → use kafka:9092
    # If running locally → use localhost:9092
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9094")
    print(f"📡 Connecting to Kafka broker at {bootstrap}...")

    # Initialize Kafka producer
    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    await producer.start()

    try:
        corpus_file = Path(__file__).parent.parent / "data" / "synthetic_corpus.json"
        if not corpus_file.exists():
            print(f"❌ Error: {corpus_file} not found!")
            print("Please run: python src/generate_corpus.py")
            return

        with open(corpus_file, "r") as f:
            messages = json.load(f)

        print(f"✅ Loaded {len(messages)} synthetic messages")
        print(f"🚀 Sending messages to Kafka topic 'input-events'...\n")

        for idx, msg in enumerate(messages, 1):
            await producer.send_and_wait("input-events", msg)
            print(f"[{idx}/{len(messages)}] Sent message for customer {msg.get('customer_id', 'UNKNOWN')}")
            await asyncio.sleep(0.5)  # simulate real-time flow

        print(f"\n✅ Successfully sent all {len(messages)} messages to Kafka!")
        print("Messages are being processed by the PII masking agent...")

    finally:
        await producer.stop()
        print("🔌 Disconnected from Kafka.")

if __name__ == "__main__":
    asyncio.run(send_synthetic_messages())
import json
import asyncio
import os
from pathlib import Path
from aiokafka import AIOKafkaProducer


def detect_bootstrap():
    """Detect correct Kafka host automatically."""
    if os.path.exists("/.dockerenv"):
        return "kafka:9092"
    return "localhost:9094"


async def send_synthetic_messages():
    bootstrap = detect_bootstrap()
    print(f"📡 Connecting to Kafka at {bootstrap}...")

    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    await producer.start()

    try:
        corpus_file = Path(__file__).parent.parent / "data" / "synthetic_corpus.json"
        messages = json.load(open(corpus_file))

        print(f"🚀 Sending {len(messages)} synthetic messages...\n")

        for i, msg in enumerate(messages, 1):
            await producer.send_and_wait("input-events", msg)
            print(f"[{i}] Sent → {msg.get('customer_id')}, text='{msg.get('text', '')[:50]}...'")
            await asyncio.sleep(0.3)

        print("\n✅ All messages sent.")

    finally:
        await producer.stop()
        print("🔌 Disconnected.")


if __name__ == "__main__":
    asyncio.run(send_synthetic_messages())
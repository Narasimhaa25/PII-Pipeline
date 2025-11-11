"""
Dynamic producer that takes user input and sends messages to Kafka.
Allows interactive testing of the PII pipeline with custom messages.
"""

import asyncio
import json
import os
from faker import Faker
from aiokafka import AIOKafkaProducer

fake = Faker()

async def send_user_message():
    """Send user-provided messages to Kafka interactively."""

    # Detect environment automatically
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9094")
    print(f"📡 Connecting to Kafka broker at {bootstrap}...")

    # Initialize producer
    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    await producer.start()

    try:
        print("\n🎯 Dynamic PII Pipeline Producer")
        print("Enter your message (type 'quit' to exit):")
        print("Tip: Include PII like names, emails, phones, addresses, SSNs, credit cards")
        print("-" * 70)

        while True:
            user_input = input("\n📝 Your message: ").strip()
            if user_input.lower() in {"quit", "exit", "q"}:
                print("👋 Goodbye!")
                break
            if not user_input:
                print("⚠️  Please enter a non-empty message.")
                continue

            message_data = {
                "customer_id": f"CUST{fake.random_int(1000, 9999)}",
                "message": user_input,
                "metadata": {
                    "source": "dynamic_input",
                    "generated": False
                }
            }

            await producer.send_and_wait("input-events", message_data)

            print(f"✅ Sent message for customer {message_data['customer_id']}")
            print("📨 Message sent to PII processing pipeline!")
            print("   → Presidio consumer will mask PII")
            print("   → JSON ingestor will store results")

    except KeyboardInterrupt:
        print("\n👋 Interrupted by user. Exiting gracefully...")
    finally:
        await producer.stop()
        print("🔌 Disconnected from Kafka.")

if __name__ == "__main__":
    print("🚀 Starting dynamic producer...")
    print("Ensure Kafka and ambient services are running:")
    print("   docker compose -f docker-compose.kafka.yml up -d")
    print("-" * 70)
    asyncio.run(send_user_message())
import asyncio
import json
import os
from faker import Faker
from aiokafka import AIOKafkaProducer

fake = Faker()

def detect_bootstrap():
    """Detect correct Kafka host automatically."""
    if os.path.exists("/.dockerenv"):
        return "kafka:9092"
    return "localhost:9094"

async def send_user_message():
    bootstrap = detect_bootstrap()
    print(f"📡 Connecting to Kafka at {bootstrap}...")

    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    await producer.start()

    try:
        while True:
            msg = input("Message: ").strip()
            if msg.lower() in ("quit", "exit"):
                break

            data = {
                "message_id": f"msg-{fake.uuid4()}",
                "customer_id": f"CUST{fake.random_int(1000,9999)}",
                "text": msg
            }

            await producer.send_and_wait("input-events", data)
            print("Sent:", data)

    finally:
        await producer.stop()
        print("Disconnected")

if __name__ == "__main__":
    asyncio.run(send_user_message())
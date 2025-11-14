import asyncio, json, os
from pathlib import Path
from datetime import datetime
from aiokafka import AIOKafkaConsumer
from dotenv import load_dotenv

load_dotenv()

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")

DATA = Path(__file__).parent.parent / "data"
FILE = DATA / "processed_messages.json"

def ensure():
    DATA.mkdir(exist_ok=True)
    if not FILE.exists():
        with open(FILE, "w") as f:
            json.dump({"messages": [], "metadata": {}}, f)

def save(event):
    with open(FILE, "r") as f:
        data = json.load(f)

    rec = {
        "message_id": event.get("message_id", "unknown"),
        "customer_id": event["customer_id"],
        "masked_message": event["masked_message"],
        "has_pii": event.get("has_pii", False),
        "source_topic": event.get("source_topic", "unknown"),
        "ingested_at": datetime.utcnow().isoformat()
    }

    data["messages"].append(rec)
    data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
    data["metadata"]["total"] = len(data["messages"])

    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"💾 Saved → {rec['customer_id']} ({rec['message_id']})")

async def consume():
    ensure()
    consumer = AIOKafkaConsumer(
        bootstrap_servers=BOOTSTRAP,
        group_id="json-ingestor",
        auto_offset_reset="earliest"
    )

    # Subscribe to all sanitized-* topics
    consumer.subscribe(pattern="^sanitized-.*")

    await consumer.start()
    print("📥 JSON Ingestor running...")

    try:
        async for msg in consumer:
            event = json.loads(msg.value.decode("utf-8"))
            save(event)
    finally:
        await consumer.stop()

async def main():
    await consume()

if __name__ == "__main__":
    asyncio.run(main())
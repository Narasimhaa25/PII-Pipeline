import json
import os
import sys
import time
import requests
from pathlib import Path
from kafka import KafkaConsumer, KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic
from dotenv import load_dotenv

load_dotenv()

def detect_bootstrap():
    if os.path.exists("/.dockerenv"):
        return "kafka:9092"
    return "localhost:9094"

BOOTSTRAP = detect_bootstrap()
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm-service:8000/mask")
DLQ_TOPIC = "agent-errors"

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
AUDIT_FILE = DATA_DIR / "audit_log.json"

def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)

def append_to_audit(record):
    ensure_data_dir()
    try:
        if AUDIT_FILE.exists():
            with open(AUDIT_FILE, "r") as f:
                data = json.load(f)
        else:
            data = {"records": []}
        data["records"].append(record)
        with open(AUDIT_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"❌ Audit log write error: {e}")

def call_llm_service(message_id, customer_id, text, max_retries=3):
    payload = {"message_id": message_id, "customer_id": customer_id, "text": text}
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(LLM_SERVICE_URL, json=payload, timeout=25)
            r.raise_for_status()
            data = r.json()
            # Defensive: ensure required keys exist
            if not isinstance(data, dict) or "masked_text" not in data:
                raise ValueError("LLM returned malformed response (missing masked_text)")
            return data
        except Exception as e:
            print(f"❌ LLM call failed (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
            else:
                raise
def ensure_sanitized_topic(input_topic):
    """
    Create sanitized topic for the given input topic.
    Example:
        input-events -> sanitized-input-events
    """
    sanitized_topic = f"sanitized-{input_topic}"

    try:
        admin = KafkaAdminClient(bootstrap_servers=BOOTSTRAP)

        existing_topics = admin.list_topics()

        if sanitized_topic not in existing_topics:
            topic = NewTopic(
                name=sanitized_topic,
                num_partitions=1,
                replication_factor=1
            )
            admin.create_topics([topic])
            print(f"✅ Created sanitized topic: {sanitized_topic}")
        else:
            print(f"ℹ️ Sanitized topic already exists: {sanitized_topic}")

    except Exception as e:
        print(f"⚠️ Topic creation error for {sanitized_topic}: {e}")

    finally:
        try:
            admin.close()
        except:
            pass

    return sanitized_topic

def ambient_listener():
    print("🌿 Ambient PII Listener Started (auto-subscribing to input-*)")
    consumer = KafkaConsumer(
        bootstrap_servers=BOOTSTRAP,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="ambient-agent",
        enable_auto_commit=False
    )
    consumer.subscribe(pattern="^input-.*")
    print("✅ Listening for messages...\n")

    for msg in consumer:
        try:
            event = msg.value
            print(f"\n📥 Received (topic={msg.topic}, partition={msg.partition}, offset={msg.offset}): {event}")

            incoming_text = event.get("text") or event.get("message") or ""
            message_id = event.get("message_id") or f"msg-{int(time.time()*1000)}"
            customer_id = event.get("customer_id", "unknown")

            if incoming_text == "":
                print(f"⚠️ Empty incoming_text for message_id={message_id} — will still audit and proceed.")

            sanitized_topic = ensure_sanitized_topic(msg.topic)

            # CALL LLM
            try:
                llm = call_llm_service(message_id, customer_id, incoming_text)
            except Exception as e:
                print(f"❌ LLM permanent failure for {message_id}: {e}")
                dlq_payload = {"message_id": message_id, "error": str(e), "event": event}
                producer.send(DLQ_TOPIC, dlq_payload)
                producer.flush()
                consumer.commit()
                continue

            # LOG the raw LLM response for debugging
            print(f"ℹ️ LLM response for {message_id}: {json.dumps(llm)[:1000]}")

            masked_text = llm.get("masked_text", "")
            has_pii = llm.get("has_pii", False)
            detections = llm.get("detections", [])

            # Defensive: if masked_text empty but incoming_text non-empty, send DLQ for inspection
            if incoming_text and not masked_text:
                print(f"⚠️ LLM returned empty masked_text for non-empty input (id={message_id}). Sending to DLQ for inspection.")
                dlq_payload = {"message_id": message_id, "event": event, "llm_response": llm}
                producer.send(DLQ_TOPIC, dlq_payload)
                producer.flush()
                consumer.commit()
                continue

            sanitized_payload = {
                "message_id": message_id,
                "customer_id": customer_id,
                "original_message": incoming_text,
                "masked_message": masked_text,
                "has_pii": has_pii,
                "source_topic": msg.topic,
                "ts": time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }

            producer.send(sanitized_topic, sanitized_payload, key=message_id.encode())
            producer.flush()

            audit_entry = {
                "message_id": message_id,
                "customer_id": customer_id,
                "original_message": incoming_text,
                "masked_message": masked_text,
                "has_pii": has_pii,
                "detections": detections,
                "source_topic": msg.topic,
                "processed_at": time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            append_to_audit(audit_entry)

            consumer.commit()
            print(f"✔ Masked and produced to {sanitized_topic}: {masked_text[:200]}")

        except Exception as e:
            print(f"❌ Error processing message at offset {msg.offset}: {e}")
            try:
                dlq_payload = {"event": msg.value, "error": str(e), "topic": msg.topic, "offset": msg.offset}
                producer.send(DLQ_TOPIC, dlq_payload)
                producer.flush()
            except Exception as ex:
                print(f"❌ Failed to send DLQ: {ex}")
            consumer.commit()
            continue

if __name__ == "__main__":
    ambient_listener()
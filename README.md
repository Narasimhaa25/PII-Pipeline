# PII-Pipeline

<!--
Project: PII-Pipeline
Description: Enterprise-grade PII masking system using Kafka, LangGraph, and GPT-4o
Author: Narasimhaa25
Version: 1.0
Last Updated: November 2025
Repository: https://github.com/Narasimhaa25/PII-Pipeline
-->

## 📑 Table of Contents
1. Overview
2. Architecture
3. System Components
4. Message Lifecycle
5. Folder Structure
6. Setup Instructions
7. Running the Full Stack
8. Manual Testing Mode
9. LLM Service API Contract
10. PII Detection & Masking Logic
11. LangGraph Workflow
12. Reliability Model
13. Dead-Letter Queue (DLQ)
14. JSON Audit & Processed Storage
15. Supported PII Types
16. Troubleshooting
17. Future Enhancements
18. Configuration Options
19. Performance Considerations
20. Security Notes

---

## 1. Overview
The **PII-Pipeline** is an enterprise‑grade, zero‑touch data‑sanitization system designed for large-scale event workflows using **Kafka**, **LangGraph**, and **GPT‑4o/mini**.
Developers only publish messages → the ambient agent automatically detects, masks, and routes sanitized events.

<!-- Key Features:
- Zero-touch operation for developers
- Real-time PII detection and masking
- Scalable Kafka-based architecture
- Comprehensive audit logging
- Fault-tolerant with retry mechanisms
- Extensible LLM backend
-->


---

## 2. Architecture

```
┌────────────────┐       ┌───────────────────────┐       ┌──────────────────────────────────
│  Producer      │  ---> │  input-* Kafka Topics │ ----> │  Ambient Agent (PII)(Listener)   │
└────────────────┘       └───────────────────────┘       │  ^input-* subscription           │
                                                         │  Calls LLM Service               │
                                                         └─────────┬────────────────────────           ┘
                                                                   │
                                                                   ▼
                                                     ┌──────────────────────────┐
                                                     │  External LLM Service    │
                                                     │ (GPT‑4o-mini + LangGraph)│
                                                     └─────────┬────────────────┘
                                                               │
                                                               ▼
                                                      ┌──────────────────────────────┐
                                                      │ sanitized-<input-topic>      │
                                                      │ (Masked Kafka Events)        │
                                                      └─────────────┬────────────────┘
                                                                    │
                                                                    ▼
                                             ┌───────────────────────────────────────────┐
                                             │ JSON Storage: audit_log.json              │
                                             │                                           │
                                             └───────────────────────────────────────────┘
```

<!-- Architecture Notes:
- Producers are decoupled from processing
- Ambient agent acts as middleware
- LLM service is stateless and scalable
- JSON storage provides audit trail
- All components can be containerized
-->

---

## 3. System Components

### **1. Kafka Producer**
Publishes raw customer text in:
```
{ message_id, customer_id, text }
```

<!-- Producer Notes:
- message_id should be unique for deduplication
- customer_id helps with tenant isolation
- text can contain any customer message
-->

### **2. Ambient Agent**
A long‑running Kafka consumer that:
- auto-subscribes to all topics `^input-.*`
- calls LLM for each message
- produces sanitized output
- writes audit logs
- retries failures & writes DLQ

<!-- Ambient Agent Notes:
- Runs continuously in background
- Handles topic auto-discovery
- Implements circuit breaker pattern
- Maintains processing order per partition
-->

### **3. External LLM Service**
A FastAPI service calling LangGraph + GPT‑4o-mini:
- Detects PII
- Masks detected values
- Returns structured JSON

<!-- LLM Service Notes:
- Uses GPT-4o-mini for cost efficiency
- Structured output ensures consistency
- Timeout handling prevents hanging
- Can be scaled horizontally
-->

### **4. JSON Ingestor**
Listens to sanitized topics and stores:
- processed_messages.json

<!-- JSON Ingestor Notes:
- Provides secondary storage
- Enables downstream processing
- Maintains message history
- Can be replaced with database
-->  

---

## 4. Message Lifecycle
1. Producer publishes → input-events  
2. Ambient Agent consumes  
3. Sends text to LLM service  
4. LLM returns PII detections + masked text  
5. Sanitized message sent → sanitized-input-events  
6. JSON audit saved  
7. Offsets committed  

<!-- Lifecycle Notes:
- At-least-once delivery guaranteed
- Idempotent processing via message_id
- Audit trail maintained throughout
- Failures handled gracefully
-->

## 5. Folder Structure
```
pii_pipeline/
├── consumer/
│   ├── pii_GPTmasker.py      # Ambient agent implementation(listener)
│   └── pii_agent.py          # LangGraph PII detection logic
├── llm_service.py            # FastAPI LLM service
├── ingestor/
│   └── consumer_ingestor.py  # JSON storage consumer
├── producer/
│   ├── batch_producer.py     # Bulk message producer
│   ├── dynamic_producer.py   # Interactive producer
│   └── generate_synthetic_data.py  # Test data generator
├── data/
│   ├── audit_log.json        # Full processing audit
│   ├── processed_messages.json  # Sanitized messages
│   └── synthetic_corpus.json # Test data
├── docker-compose.kafka.yml  # Full stack deployment
├── Dockerfile                # Container definition
└── requirements.txt          # Python dependencies
```

<!-- Folder Structure Notes:
- Modular design for easy maintenance
- Clear separation of concerns
- Data directory for persistent storage
- Docker support for deployment
-->

## 6. Setup Instructions
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# source venv/Scripts/activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key-here"
# Optional: export KAFKA_BOOTSTRAP="localhost:9094"
```

<!-- Setup Notes:
- Python 3.10+ recommended
- OpenAI API key required for LLM
- Virtual environment prevents conflicts
- Kafka defaults to localhost if not set
-->

## 7. Running the Full Stack
```bash
# Start all services with Docker Compose
docker compose -f docker-compose.kafka.yml up -d --build

# Check logs
docker compose -f docker-compose.kafka.yml logs -f

# Stop services
docker compose -f docker-compose.kafka.yml down
```

<!-- Full Stack Notes:
- Builds containers automatically
- Services start in dependency order
- Use --build to rebuild after code changes
- Logs help with debugging
-->

## 8. Manual Testing Mode
Terminal 1:
```bash
python llm_service.py
```

Terminal 2:
```bash
python consumer/pii_GPTmasker.py
```

Terminal 3:
```bash
python producer/dynamic_producer.py
```

<!-- Manual Testing Notes:
- Useful for development and debugging
- Each component runs independently
- Allows step-by-step testing
- Monitor logs for issues
-->

## 9. LLM Service API Contract

### Request
```json
{
  "message_id": "msg-123",
  "customer_id": "CUST1111",
  "text": "my phone is 9876543210"
}
```

### Response
```json
{
  "has_pii": true,
  "masked_text": "my phone is [PHONE]",
  "detections": [
    { "type": "phone", "start": 12, "end": 22 }
  ]
}
```

<!-- API Contract Notes:
- Simple JSON-based interface
- Consistent request/response format
- detections array provides metadata
- has_pii flag enables conditional processing
-->

## 10. PII Detection & Masking Logic

### Masking Rules
| PII Type | Mask |
|----------|-------|
| Name | `[NAME]` |
| Email | `[EMAIL]` |
| Phone | `[PHONE]` |
| Address | `[ADDRESS]` |
| SSN/Account | `[ACCOUNT]` |
| Credit Card | `[CREDIT_CARD]` |

<!-- Masking Logic Notes:
- Standardized tokens for consistency
- Preserves message readability
- Easy to parse downstream
- Extensible for new PII types
-->

## 11. LangGraph Workflow

```
[detect_pii] → [mask_pii] → END
```

Nodes:
1. detect_pii
2. mask_pii

Each runs GPT‑4o-mini with deterministic prompting.

<!-- LangGraph Notes:
- Two-stage pipeline for clarity
- Deterministic prompts ensure consistency
- Can be extended with more nodes
- State management handles complex flows
-->

## 12. Reliability Model
- At-least-once delivery
- Idempotent via message_id key
- Retries with exponential backoff
- DLQ on failure

<!-- Reliability Notes:
- No message loss guaranteed
- Duplicate handling via deduplication
- Backoff prevents overwhelming LLM
- DLQ enables manual inspection
-->

## 13. Dead-Letter Queue (DLQ)
On repeated failure:
```
agent-errors topic
```

Payload contains:
- event
- error reason
- topic & offset

<!-- DLQ Notes:
- Captures unprocessable messages
- Includes error context
- Enables manual review
- Prevents processing loops
-->

## 14. JSON Audit & Processed Storage
Files:
- `data/audit_log.json` - Full processing details
- `data/processed_messages.json` - Sanitized messages

<!-- Storage Notes:
- JSON format for readability
- Audit trail for compliance
- Processed data for downstream use
- Can be replaced with databases
-->

## 15. Supported PII Types
- Names (full, first, last)
- Emails
- Phones (various formats)
- Addresses (street, city, state, zip)
- SSN (Social Security Numbers)
- Passport Numbers
- Credit Cards
- Account Numbers
- DOB (Dates of Birth)
- License Numbers
- IP addresses
- Bank accounts (IBAN)

<!-- PII Types Notes:
- Comprehensive coverage
- Context-aware detection
- Extensible via prompt engineering
- Covers common compliance requirements
-->

## 16. Troubleshooting

### LLM service not running
```bash
docker logs llm-service
# Check for API key issues or port conflicts
```

### Kafka topic missing
```bash
docker exec -it kafka kafka-topics.sh --list --bootstrap-server localhost:9092
# Topics auto-create, but verify connectivity
```

### Message not consumed
Reset consumer offsets:
```bash
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group ambient-agent --reset-offsets --to-earliest --execute --topic input-events
```

<!-- Troubleshooting Notes:
- Check logs first
- Verify network connectivity
- Reset offsets for testing
- Monitor resource usage
---

## 18. Configuration Options

### Environment Variables
```bash
OPENAI_API_KEY=sk-...          # Required for LLM
KAFKA_BOOTSTRAP=localhost:9094 # Kafka connection
LLM_SERVICE_URL=http://llm-service:8000/mask  # Service endpoint
DLQ_TOPIC=agent-errors         # Dead letter queue name
AUDIT_FILE=data/audit_log.json # Audit log location
```

<!-- Configuration Notes:
- Environment-based config
- Sensible defaults provided
- Easy to override for different environments
- Secrets management recommended
-->

---

## 19. Performance Considerations

- **Throughput**: ~10-50 messages/sec depending on LLM latency
- **Latency**: 2-10 seconds per message (LLM + network)
- **Scalability**: Horizontal scaling of LLM service
- **Cost**: Monitor OpenAI API usage
- **Storage**: JSON files grow over time, consider rotation

<!-- Performance Notes:
- LLM is the bottleneck
- Batch processing possible
- Monitor costs carefully
- Optimize for your use case
-->

---

## 20. Security Notes

- Store API keys securely (not in code)
- Use HTTPS in production
- Implement authentication if needed
- Audit logs contain sensitive data - secure storage
- VPC isolation recommended
- Regular security updates

<!-- Security Notes:
- Protect sensitive configuration
- Secure communication channels
- Compliance with data protection regulations
- Regular vulnerability assessments
-->

---


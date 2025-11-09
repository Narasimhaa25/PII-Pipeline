# PII Pipeline

A privacy-focused pipeline for detecting and masking PII using LangGraph agents (GPT-4o or Presidio), Kafka, and JSON storage.

## Features

- **Dual Agent Architecture**: Choose between GPT-4o (AI-powered context-aware detection) and Presidio (fast rule-based detection)
- **Event-Driven Processing**: Kafka-based streaming pipeline with separate input/output topics
- **Synthetic Data Generation**: Automated creation of realistic customer messages with embedded PII using Faker
- **Minimal Output Design**: Only essential data (customer_id, masked_message) sent to sanitized-events topic

## Architecture

```
Producer → Kafka (input-events) → Agent (GPT-4o/Presidio) → Kafka (sanitized-events) → JSON Ingestor
```

### Data Flow Explanation:
1. **Producer** generates synthetic customer messages with PII and sends them to `input-events` topic
2. **Agent Consumer** (GPT-4o or Presidio) reads from `input-events`, processes messages, and publishes masked results to `sanitized-events`
3. **JSON Ingestor** consumes from `sanitized-events` and appends results to `data/processed_messages.json`

### Topic Configuration:
- **input-events**: Raw messages with PII (5-minute retention)
- **sanitized-events**: Processed messages with PII masked (5-minute retention)
- **KRaft Mode**: Single-node Kafka setup for development/testing

## Project Structure
```
pii_pipeline/
├── .env                                    # Environment variables (Kafka, OpenAI API key)
├── AGENTS_COMPARISON.md                    # Detailed comparison of GPT-4o vs Presidio agents
├── README.md                               # This file
├── consumer/
│   ├── __pycache__/                        # Python compiled files
│   ├── pii_GPTagent.py                     # GPT-4o LangGraph agent (LLM-based)
│   ├── pii_agent_presidio.py               # Presidio LangGraph agent (rule-based)
│   ├── pii_GPTmasker.py                    # Kafka consumer for GPT-4o agent
│   └── pii_masker_presidio.py              # Kafka consumer for Presidio agent
├── data/
│   ├── processed_messages.json             # Output: masked messages (auto-created)
│   └── synthetic_corpus.json               # Input: synthetic test data
├── docker-compose.kafka.yml                # Kafka setup (KRaft mode, 5min retention)
├── ingestor/
│   └── consumer_ingestor.py                # Ingests sanitized-events to JSON
├── producer/
│   ├── batch_producer.py                   # Sends synthetic data to Kafka
│   └── generate_synthetic_data.py          # Generates synthetic PII data
├── requirements.txt                        # Python dependencies
├── setup_presidio.sh                       # Presidio setup script
└── venv/                                   # Python virtual environment
```

## Quickstart

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up environment
- Edit `.env` for Kafka bootstrap and OpenAI API key (if using GPT-4o).

### 3. Download spaCy model (Presidio only)
```bash
python -m spacy download en_core_web_lg
```

### 4. Start Kafka
```bash
docker-compose -f docker-compose.kafka.yml up -d
```

### 5. Generate synthetic data
```bash
python producer/generate_synthetic_data.py
```

### 6. Run the pipeline

There are two common ways to start the pipeline depending on your workflow:

- A) Start consumers first (recommended for continuous processing)
- B) Start producer first (useful for batch-load testing)

Before running any commands, start Kafka:
```bash
docker-compose -f docker-compose.kafka.yml up -d
```

A) Consumers first (recommended)

GPT-4o pipeline (consumers first):
```bash
# Terminal 1 - GPT-4o agent consumer
source venv/bin/activate
python consumer/pii_GPTmasker.py

# Terminal 2 - Ingestor (writes to data/processed_messages.json)
source venv/bin/activate
python ingestor/consumer_ingestor.py

# Terminal 3 - Producer (sends synthetic messages)
python producer/batch_producer.py
```

Presidio pipeline (consumers first):
```bash
# Terminal 1 - Presidio agent consumer
source venv/bin/activate
python consumer/pii_masker_presidio.py

# Terminal 2 - Ingestor
source venv/bin/activate
python ingestor/consumer_ingestor.py

# Terminal 3 - Producer
python producer/batch_producer.py
```

B) Producer first (batch load)

GPT-4o pipeline (producer first):
```bash
# Terminal 1 - Producer (send messages to input-events)
python producer/batch_producer.py

# Terminal 2 - GPT-4o agent consumer (process backlog)
source venv/bin/activate
python consumer/pii_GPTmasker.py

# Terminal 3 - Ingestor
source venv/bin/activate
python ingestor/consumer_ingestor.py
```

Presidio pipeline (producer first):
```bash
# Terminal 1 - Producer
python producer/batch_producer.py

# Terminal 2 - Presidio agent consumer
source venv/bin/activate
python consumer/pii_masker_presidio.py

# Terminal 3 - Ingestor
source venv/bin/activate
python ingestor/consumer_ingestor.py
```

Notes:
- You can run consumers in the background using `&` (e.g. `python consumer/pii_GPTmasker.py &`) or with a terminal multiplexer (tmux/screen).
- To run both agents side-by-side for comparison, start each consumer in a different consumer group (or different topic) so they both see the same input messages.
- If you run the producer multiple times, messages will be appended to the Kafka topic and processed according to topic retention and consumer offsets.

### 7. Ingest results

The ingestor consumes from `sanitized-events` and appends masked messages to `data/processed_messages.json`:
```bash
python ingestor/consumer_ingestor.py
```

## Output Format
```json
{
  "customer_id": "CUST1234",
  "masked_message": "Hi, my name is [NAME]. Card: [CREDIT_CARD]."
}
```


## References
- [Presidio](https://microsoft.github.io/presidio/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [OpenAI GPT-4o](https://platform.openai.com/docs/models/gpt-4o)

---

> For more details, see `AGENTS_COMPARISON.md`.
```

## 🚀 Setup

### 1. Start Kafka

```bash
docker compose -f docker-compose.kafka.yml up -d
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```properties
KAFKA_BOOTSTRAP=localhost:9092
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 5. Run the Pipeline

**Terminal 1 - Start PII Agent Consumer:**
```bash
source venv/bin/activate
python consumer/pii_GPTmasker.py
```

**Terminal 2 - Start Ingestor:**
```bash
source venv/bin/activate
python ingestor/consumer_ingestor.py
```

## 📤 Usage
### Generate Synthetic Data
```bash
python producer/generate_synthetic_data.py
```
### Process Messages Through Pipeline
```bash
python producer/batch_producer.py
```

This sends all 50 messages to Kafka for processing.

## 🔍 How It Works

1. **Synthetic Data Generation**: Creates realistic customer messages with PII
   
2. **LangGraph Agent Processing**:
   - **Detect Node**: GPT-4o-mini analyzes message and identifies PII with positions
   - **Mask Node**: Replaces each PII instance with standardized token
   
3. **Kafka Event Flow**:
   ```
   input-events → PII Agent → sanitized-events → JSON Storage
   ```

4. **JSON Storage**: Stores processed messages in JSON format

## 🗄️ Data Files

### Input
- `data/synthetic_corpus.json`: 50 original messages with PII

### Output
- `data/processed_messages.json`: Processed messages with PII masked

## 🎯 PII Detection Capabilities

The LangGraph agent can detect and mask:

- ✅ **Names**: Full names, first/last names
- ✅ **Emails**: Email addresses
- ✅ **Phones**: Various formats including international
- ✅ **Addresses**: Street addresses, cities, states, zip codes
- ✅ **SSN**: Social Security Numbers
- ✅ **Credit Cards**: Card numbers
- ✅ **Account Numbers**: Bank accounts, customer IDs

## ✨ Advantages Over Regex-Based Masking

✅ **Context-Aware**: Understands semantic meaning, not just patterns  
✅ **High Accuracy**: GPT-4o-mini reduces false positives/negatives  
✅ **Flexible**: Handles variations and edge cases  
✅ **Explainable**: Provides reasoning for each detection  
✅ **Extensible**: Easy to add new PII types via prompt engineering  
✅ **Complete Audit**: Full detection metadata stored  

## 🛠️ Technologies

- **LangGraph**: Agent workflow orchestration
- **LangChain**: LLM integration framework
- **OpenAI GPT-4o-mini**: Intelligent PII detection
- **Microsoft Presidio**: Rule-based PII detection
- **Apache Kafka**: Event streaming
- **Faker**: Synthetic data generation
- **spaCy**: NLP models for Presidio
- **Docker**: Kafka containerization

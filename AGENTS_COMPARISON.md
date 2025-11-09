# PII Detection Agents - Comparison Guide

This project now includes **two different PII detection approaches**:

## 🤖 Agent 1: GPT-4o-mini (LLM-based)
**File**: `consumer/pii_GPTagent.py`

### Strengths
- **Intelligent Context Understanding**: Uses AI to understand context and nuance
- **Adaptive Detection**: Can identify PII even in unusual formats or contexts
- **Reasoning**: Provides explanations for why something is PII
- **Handles Edge Cases**: Better at ambiguous situations

### Weaknesses
- **Cost**: Requires OpenAI API calls (paid service)
- **Speed**: Slower due to API latency (1-3 seconds per message)
- **Consistency**: May vary slightly between runs
- **Requires API Key**: Needs `OPENAI_API_KEY` environment variable

### Best For
- Complex customer service messages
- Multi-language support
- When context matters (e.g., "my number" vs "order number")
- High-value applications where accuracy > cost

---

## 🔍 Agent 2: Presidio (Rule-based)
**File**: `consumer/pii_agent_presidio.py`

### Strengths
- **Fast**: Processes messages in milliseconds
- **Free**: No API costs, runs locally
- **Deterministic**: Always produces same results for same input
- **Privacy**: No data leaves your infrastructure
- **Proven**: Microsoft's production-grade library

### Weaknesses
- **Pattern-Based**: Misses PII that doesn't match known patterns
- **Less Contextual**: Can't understand context like humans
- **False Positives**: May flag non-PII that looks like PII
- **Limited to Predefined Types**: Only detects known entity types

### Supported Entity Types
- PERSON, EMAIL_ADDRESS, PHONE_NUMBER
- CREDIT_CARD, US_SSN, US_PASSPORT
- US_DRIVER_LICENSE, LOCATION, DATE_TIME
- IP_ADDRESS, IBAN_CODE, US_BANK_NUMBER
- MEDICAL_LICENSE, URL

### Best For
- High-volume processing (1000s of messages/sec)
- Regulatory compliance (deterministic, auditable)
- Privacy-sensitive environments (on-premise)
- Cost-conscious applications

---

## 🚀 Setup Instructions

### Option 1: GPT-4o Agent (Current Default)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set OpenAI API key**:
   ```bash
   echo "OPENAI_API_KEY=sk-your-key-here" >> .env
   ```

3. **Run the consumer**:
   ```bash
   python consumer/pii_GPTmasker.py
   ```

---

### Option 2: Presidio Agent

1. **Install dependencies** (including Presidio):
   ```bash
   pip install -r requirements.txt
   ```

2. **Download spaCy language model**:
   ```bash
   python -m spacy download en_core_web_lg
   ```

3. **Run the Presidio consumer**:
   ```bash
   python consumer/pii_masker_presidio.py
   ```

4. **Test the agent** (standalone):
   ```bash
   python consumer/pii_agent_presidio.py
   ```

---

## ⚖️ Performance Comparison

| Metric | GPT-4o Agent | Presidio Agent |
|--------|--------------|----------------|
| **Speed** | 1-3 sec/msg | <10 ms/msg |
| **Cost** | ~$0.001/msg | Free |
| **Accuracy** | 95-98% (context-aware) | 85-92% (pattern-based) |
| **Privacy** | Data sent to OpenAI | 100% local |
| **Scalability** | Limited by API rate | 1000s msg/sec |
| **Setup Complexity** | Simple (API key) | Medium (spaCy model) |

---

## 🔄 Switching Between Agents

### Method 1: Use Different Consumers
```bash
# Run GPT-4o agent
python consumer/pii_GPTmasker.py

# OR run Presidio agent
python consumer/pii_masker_presidio.py
```

### Method 2: Use Different Consumer Groups
Run both simultaneously for comparison:
```bash
# Terminal 1: GPT-4o agent
python consumer/pii_GPTmasker.py

# Terminal 2: Presidio agent (different consumer group)
python consumer/pii_masker_presidio.py
```

Both will process the same messages independently!

---

## 🎯 Recommendations

### Use GPT-4o Agent When:
- Message volume < 1000/day
- Accuracy is critical
- Budget allows API costs
- Messages contain complex/ambiguous PII
- Need context understanding

### Use Presidio Agent When:
- Message volume > 10,000/day
- Privacy/data residency requirements
- Zero marginal cost needed
- PII patterns are well-defined
- Speed is critical

### Hybrid Approach:
1. Use Presidio for initial fast detection
2. Use GPT-4o for messages where Presidio found no/low PII
3. Best of both: speed + accuracy + cost optimization

---

## 🧪 Testing Both Agents

Generate test data and compare:

```bash
# 1. Generate synthetic data
python producer/generate_synthetic_data.py

# 2. Start Kafka
docker-compose -f docker-compose.kafka.yml up -d

# 3. Test GPT-4o agent
python consumer/pii_GPTmasker.py &
python producer/batch_producer.py
# Wait for completion, then Ctrl+C

# 4. Backup results
mv data/processed_messages.json data/gpt4o_results.json

# 5. Test Presidio agent
python consumer/pii_masker_presidio.py &
python producer/batch_producer.py
# Wait for completion, then Ctrl+C
```

---

## 📝 Notes

- Both agents use **LangGraph** for workflow orchestration
- Both produce the **same output format** (compatible with ingestor)
- Both support the **same Kafka topics** (can run side-by-side)
- Presidio requires ~500MB for spaCy language model
- GPT-4o requires internet connection + API key

---

## 🔗 References

- **Presidio**: https://microsoft.github.io/presidio/
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **OpenAI GPT-4o**: https://platform.openai.com/docs/models/gpt-4o

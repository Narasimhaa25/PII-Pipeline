


from typing import TypedDict
from langgraph.graph import StateGraph, END
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from dotenv import load_dotenv

load_dotenv()  # Load .env variables if present


# Initialize Presidio engines with ML-based recognizers
analyzer = AnalyzerEngine()

# Add spaCy ML-based recognizer for better entity detection
try:
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_analyzer.nlp_engine.spacy_nlp_engine import SpacyNlpEngine

    # Configure spaCy NLP engine
    spacy_config = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}]
    }

    # Create NLP engine
    nlp_engine = NlpEngineProvider(nlp_configuration=spacy_config).create_engine()

    # Add spaCy recognizer for ML-based NER
    from presidio_analyzer.recognizer_registry import RecognizerRegistry
    from presidio_analyzer.nlp_engine import SpacyNlpEngine

    # Create registry with spaCy support
    registry = RecognizerRegistry()
    registry.load_predefined_recognizers(nlp_engine=nlp_engine)

    # Create analyzer with ML support
    analyzer = AnalyzerEngine(registry=registry, nlp_engine=nlp_engine)

    print("✓ Using ML-based PII detection with spaCy")
    USE_ML = True

except ImportError:
    print("⚠️  spaCy not available, using rule-based detection")
    print("   Install with: pip install spacy && python -m spacy download en_core_web_lg")
    USE_ML = False

anonymizer = AnonymizerEngine()


# State definition for LangGraph
class PiiState(TypedDict):
    customer_id: str
    original_message: str
    detected_pii: dict
    masked_message: str
    metadata: dict



class PresidioPiiAgent:
    """LangGraph agent using Presidio for PII detection and masking."""

    def __init__(self):
        self.graph = self._build_graph()
        self.app = self.graph.compile()
        # Supported entity types in Presidio
        self.entity_types = [
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN",
            "US_PASSPORT", "US_DRIVER_LICENSE", "LOCATION", "DATE_TIME", "IP_ADDRESS",
            "IBAN_CODE", "NRP", "US_BANK_NUMBER", "MEDICAL_LICENSE", "URL"
        ]

        # --- Custom recognizer for long credit card numbers (16-19 digits) ---
        from presidio_analyzer import PatternRecognizer, Pattern
        custom_card_pattern = Pattern(name="Custom Credit Card", regex=r"\\b\\d{16,19}\\b", score=0.6)
        custom_card_recognizer = PatternRecognizer(supported_entity="CREDIT_CARD", patterns=[custom_card_pattern])
        analyzer.registry.add_recognizer(custom_card_recognizer)

    def _detect_pii_node(self, state: PiiState) -> PiiState:
        # Detect PII entities in the message using Presidio
        message = state["original_message"]
        results = analyzer.analyze(
            text=message,
            entities=self.entity_types,
            language='en'
        )
        detected_pii = [
            {
                "type": r.entity_type,
                "value": message[r.start:r.end]
            }
            for r in results
        ]

        # --- Custom detection logic placeholder ---
        # If you want to add custom PII detection, append to detected_pii here.
        # Example:
        # custom_entities = custom_pii_detection(message)
        # detected_pii.extend(custom_entities)
        state["detected_pii"] = {
            "detected_pii": detected_pii,
            "count": len(detected_pii),
            "method": "presidio"
        }
        print(f"✓ Presidio detected {len(detected_pii)} PII entities in message from {state['customer_id']}")
        return state

    def _mask_pii_node(self, state: PiiState) -> PiiState:
        # Mask detected PII entities using Presidio Anonymizer
        message = state["original_message"]
        detected_pii_list = state["detected_pii"].get("detected_pii", [])
        if not detected_pii_list:
            state["masked_message"] = message
            print(f"  → No masking needed for {state['customer_id']}")
            return state
        from presidio_analyzer import RecognizerResult
        # For masking, we need start/end, so reconstruct from Presidio results
        # If custom entities are added, ensure they have start/end for masking
        recognizer_results = []
        for r in analyzer.analyze(
            text=message,
            entities=self.entity_types,
            language='en'
        ):
            recognizer_results.append(
                RecognizerResult(
                    entity_type=r.entity_type,
                    start=r.start,
                    end=r.end,
                    score=r.score
                )
            )
        # If you add custom entities, append RecognizerResult for each
        # Define anonymization operators
        operators = {
            "DEFAULT": OperatorConfig("replace", {"new_value": "[PII]"}),
            "PERSON": OperatorConfig("replace", {"new_value": "[NAME]"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"}),
            "CREDIT_CARD": OperatorConfig("replace", {"new_value": "[CREDIT_CARD]"}),
            "US_SSN": OperatorConfig("replace", {"new_value": "[SSN]"}),
            "LOCATION": OperatorConfig("replace", {"new_value": "[ADDRESS]"}),
            "DATE_TIME": OperatorConfig("replace", {"new_value": "[DATE]"}),
            "US_DRIVER_LICENSE": OperatorConfig("replace", {"new_value": "[CREDIT_CARD]"}),
            "ACCOUNT_NUMBER": OperatorConfig("replace", {"new_value": "[CREDIT_CARD]"}),
            "IBAN_CODE": OperatorConfig("replace", {"new_value": "[CREDIT_CARD]"}),
        }
        anonymized_result = anonymizer.anonymize(
            text=message,
            analyzer_results=recognizer_results,
            operators=operators
        )
        state["masked_message"] = anonymized_result.text
        print(f"  → Masked {len(detected_pii_list)} PII entities for {state['customer_id']}")
        return state

    def _build_graph(self) -> StateGraph:
        # Build the LangGraph workflow
        workflow = StateGraph(PiiState)
        workflow.add_node("detect_pii", self._detect_pii_node)
        workflow.add_node("mask_pii", self._mask_pii_node)
        workflow.set_entry_point("detect_pii")
        workflow.add_edge("detect_pii", "mask_pii")
        workflow.add_edge("mask_pii", END)
        return workflow

    def process_message(self, customer_id: str, message: str, metadata: dict = None) -> dict:
        # Process a message through the Presidio workflow
        initial_state = {
            "customer_id": customer_id,
            "original_message": message,
            "detected_pii": {},
            "masked_message": "",
            "metadata": metadata or {}
        }
        final_state = self.app.invoke(initial_state)
        return {
            "customer_id": final_state["customer_id"],
            "original_message": final_state["original_message"],
            "detected_pii": final_state["detected_pii"],
            "masked_message": final_state["masked_message"],
            "metadata": final_state["metadata"]
        }



# Quick test for the agent
if __name__ == "__main__":
    agent = PresidioPiiAgent()
    test_messages = [
        {
            "customer_id": "TEST001",
            "message": "Hi, my name is John Smith and my email is john.smith@email.com. My phone is 555-123-4567.",
            "metadata": {"source": "test"}
        },
        {
            "customer_id": "TEST002",
            "message": "I need help with my account. My SSN is 123-45-6789 and I live at 123 Main St, New York.",
            "metadata": {"source": "test"}
        },
        {
            "customer_id": "TEST003",
            "message": "Please update my credit card ending in 4532 1234 5678 9010.",
            "metadata": {"source": "test"}
        }
    ]
    print("\n=== TESTING PRESIDIO PII AGENT ===\n")
    for test in test_messages:
        result = agent.process_message(test["customer_id"], test["message"], test["metadata"])
        print(f"Customer: {result['customer_id']}")
        print(f"Original:  {result['original_message']}")
        print(f"Masked:    {result['masked_message']}")
        print(f"Detected:  {len(result['detected_pii'].get('detected_pii', []))} PII entities")
        for pii in result['detected_pii'].get('detected_pii', []):
            print(f"  • {pii['type']:20s} : {pii['value']}")
        print("-" * 60)

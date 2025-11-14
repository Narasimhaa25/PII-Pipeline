# llm_service.py
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from consumer.pii_agent import get_pii_agent

app = FastAPI(title="LangGraph PII Masking Service")


# Input Model

class MaskRequest(BaseModel):
    message_id: str
    customer_id: str
    text: str



# Output Model

class Detection(BaseModel):
    type: str
    start: int
    end: int

class MaskResponse(BaseModel):
    has_pii: bool
    masked_text: str
    detections: list[Detection]



# Load LangGraph Agent

pii_agent = get_pii_agent()


@app.post("/mask", response_model=MaskResponse)
def mask_handler(req: MaskRequest):
    """
    Calls the LangGraph PIIAgent to detect + mask PII.
    """
    result = pii_agent.process_message(req.text)

    return MaskResponse(
        has_pii=result["detected_pii"].get("has_pii", False),
        masked_text=result["masked_message"],
        detections=[
            Detection(
                type=item.get("type"),
                start=item.get("start"),
                end=item.get("end")
            )
            for item in result["detected_pii"].get("detected_pii", [])
        ]
    )



# Start server
if __name__ == "__main__":
    print("🔥 LangGraph LLM Masking Service running at http://localhost:8000/mask")
    uvicorn.run(app, host="0.0.0.0", port=8000)
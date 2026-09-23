from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from rfq_cc.domain import CustomerIntent, OrderReference, QualificationInput, QuoteReference
from rfq_cc.gates import validate_kt38
from rfq_cc.policy import decide
from rfq_cc.qualification import next_best_question, qualify, resource_budget

app = FastAPI(
    title="RFQ Commercial Conversion Engine",
    version="0.1.0",
    description=(
        "Qualification, resource allocation, quote-response policy and KT37/KT38 gates."
    ),
)


@app.get("/health/live")
async def live() -> dict:
    return {"status": "ok"}


@app.get("/health/ready")
async def ready() -> dict:
    return {"status": "ready", "mode": "local"}


@app.post("/v1/qualification/evaluate")
async def qualification(payload: QualificationInput) -> dict:
    snapshot = qualify(payload)
    return {
        "qualification": snapshot.model_dump(mode="json"),
        "resource_budget": resource_budget(snapshot.classification).model_dump(mode="json"),
        "next_best_question": next_best_question(snapshot),
    }


@app.post("/v1/decision/evaluate")
async def decision(payload: CustomerIntent) -> dict:
    return decide(payload).model_dump(mode="json")


class KT38Request(BaseModel):
    quote: QuoteReference
    order: OrderReference


@app.post("/v1/kt38/validate")
async def kt38(payload: KT38Request) -> dict:
    return validate_kt38(
        quote=payload.quote,
        order=payload.order,
    ).model_dump(mode="json")

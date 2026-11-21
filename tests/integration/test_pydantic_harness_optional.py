"""Optional PydanticAI/Harness integration. No actual LLM or tools are used."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pydantic_ai_harness")
pytest.importorskip("pydantic_ai")

from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelResponse,
    ToolCallPart,
    models,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai_harness import (
    GuardrailResult,
    OutputBlocked,
    OutputGuardrail,
)

from electronics_rfq_agent.verified_extraction.audit import result_hash
from electronics_rfq_agent.verified_extraction.contracts import (
    EvidenceBlock,
    EvidenceBundle,
    ExtractedField,
    ExtractedLine,
    ExtractionResult,
    GateStatus,
    SourceLine,
    SourceSpan,
    verify,
)

models.ALLOW_MODEL_REQUESTS = False


def _sample() -> tuple[EvidenceBundle, ExtractionResult]:
    text = "ABB S203-C16 — 100 pcs"
    eid = "EV-1"

    def field(value: str) -> ExtractedField:
        start = text.index(value)
        return ExtractedField(
            value=value,
            span=SourceSpan(evidence_id=eid, start=start, end=start + len(value)),
        )

    bundle = EvidenceBundle(
        document_id="SYNTH-1",
        authorization_id="SYNTHETIC-ONLY",
        synthetic=True,
        evidence=[EvidenceBlock(evidence_id=eid, page=1, text=text)],
        source_lines=[
            SourceLine(
                source_line_id="L1",
                evidence_id=eid,
                original_text=text,
            )
        ],
    )
    result = ExtractionResult(
        document_id="SYNTH-1",
        lines=[
            ExtractedLine(
                source_line_id="L1",
                original_text=text,
                part_number=field("S203-C16"),
                quantity_raw=field("100"),
                unit_raw=field("pcs"),
            )
        ],
    )
    return bundle, result


def _agent(bundle: EvidenceBundle, canned: ExtractionResult) -> Agent[Any, Any]:
    def model_response(_messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        assert info.output_tools, "Structured output tool was not provided"
        return ModelResponse(
            parts=[
                ToolCallPart(info.output_tools[0].name, canned.model_dump(mode="json"))
            ]
        )

    def output_guard(output: object) -> GuardrailResult:
        if not isinstance(output, ExtractionResult):
            return GuardrailResult.block("Invalid typed result")
        report = verify(bundle, output, result_sha256=result_hash(output))
        if report.status == GateStatus.BLOCKED:
            return GuardrailResult.block("Invalid source evidence")
        return GuardrailResult.allow()

    return Agent(
        FunctionModel(model_response),
        output_type=ExtractionResult,
        instructions="Preserve each synthetic RFQ line and source span.",
        capabilities=[OutputGuardrail(guard=output_guard)],
    )


def test_function_model_accepts_verified_evidence_without_network() -> None:
    bundle, canned = _sample()
    output = _agent(bundle, canned).run_sync("synthetic RFQ only").output
    assert isinstance(output, ExtractionResult)
    assert output == canned
    report = verify(bundle, output, result_sha256=result_hash(output))
    assert report.status == GateStatus.REVIEW_REQUIRED


def test_guardrail_blocks_wrong_quantity_without_network() -> None:
    bundle, canned = _sample()
    wrong = canned.lines[0].quantity_raw.model_copy(update={"value": "1000"})
    bad_line = canned.lines[0].model_copy(update={"quantity_raw": wrong})
    bad = canned.model_copy(update={"lines": [bad_line]})
    with pytest.raises(OutputBlocked):
        _agent(bundle, bad).run_sync("synthetic RFQ only")

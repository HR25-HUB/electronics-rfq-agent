from fastapi.testclient import TestClient

from rfq_cc.api import app


client = TestClient(app)


def test_live_health() -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_qualification_endpoint() -> None:
    response = client.post(
        "/v1/qualification/evaluate",
        json={
            "line_id": "L1",
            "deal_id": "D1",
            "need_context": "PROJECT",
            "primary_criterion": "DELIVERY_DEADLINE",
            "decision_deadline_known": True,
            "decision_maker_known": True,
            "budget_process_known": True,
            "competitors_known": True,
            "explicit_project_or_need": True,
            "customer_engaged_in_dialogue": True,
            "agreed_success_condition": True
        },
    )
    assert response.status_code == 200
    assert response.json()["qualification"]["classification"] == "HOT"

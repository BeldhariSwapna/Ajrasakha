import unittest
from fastapi.testclient import TestClient
from api import app
from bot_handler import parse_feedback_input
from pipeline import run_flagging_pipeline
from digest import generate_weekly_digest

client = TestClient(app)


def test_health():
    """Verify health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_parse_feedback_input():
    """Verify WhatsApp input parsing for 1 and 2."""
    # Test positive responses
    is_fb, helpful, val = parse_feedback_input("1")
    assert is_fb is True and helpful is True and val == 1

    is_fb, helpful, val = parse_feedback_input("1. Yes")
    assert is_fb is True and helpful is True and val == 1

    is_fb, helpful, val = parse_feedback_input("అవును")
    assert is_fb is True and helpful is True and val == 1

    # Test negative responses
    is_fb, helpful, val = parse_feedback_input("2")
    assert is_fb is True and helpful is False and val == 2

    is_fb, helpful, val = parse_feedback_input("2 - No")
    assert is_fb is True and helpful is False and val == 2

    is_fb, helpful, val = parse_feedback_input("కాదు")
    assert is_fb is True and helpful is False and val == 2

    # Test non-feedback (regular question)
    is_fb, helpful, val = parse_feedback_input("మొక్కజొన్నలో ఎరువుల యాజమాన్యం ఎలా?")
    assert is_fb is False and helpful is None and val is None


def test_direct_feedback_submission():
    """Verify submitting direct feedback."""
    payload = {
        "gdb_id": "test_gdb_001",
        "farmer_phone": "+919999999999",
        "query": "What is the dose of neem oil for pest control?",
        "answer": "Mix 5ml neem oil per liter of water.",
        "is_helpful": True,
        "feedback_value": 1,
        "domain": "Plant Protection",
        "crop": "Paddy",
        "language": "en",
        "state": "Telangana",
    }
    response = client.post("/api/feedback/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "feedback_id" in data


def test_analytics_endpoints():
    """Verify all analytics endpoints respond successfully."""
    summary_res = client.get("/api/feedback/analytics/summary")
    assert summary_res.status_code == 200

    gdb_res = client.get("/api/feedback/analytics/by-gdb")
    assert gdb_res.status_code == 200

    domain_res = client.get("/api/feedback/analytics/by-domain")
    assert domain_res.status_code == 200

    lang_res = client.get("/api/feedback/analytics/by-language")
    assert lang_res.status_code == 200

    state_res = client.get("/api/feedback/analytics/by-state")
    assert state_res.status_code == 200


def test_weekly_digest_generation():
    """Verify weekly digest endpoint."""
    digest_res = client.get("/api/feedback/weekly-digest?days=7")
    assert digest_res.status_code == 200
    digest_data = digest_res.json()
    assert "overall_helpfulness" in digest_data
    assert "report_markdown" in digest_data
    assert len(digest_data["report_markdown"]) > 50


if __name__ == "__main__":
    print("Running automated tests...")
    test_health()
    test_parse_feedback_input()
    test_direct_feedback_submission()
    test_analytics_endpoints()
    test_weekly_digest_generation()
    print("[PASS] All tests passed successfully!")

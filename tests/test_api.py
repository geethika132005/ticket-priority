import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "online"
    assert "version" in data


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["models_loaded"] is True


def test_predict_endpoint_valid(client):
    payload = {"ticket": "Production Kubernetes cluster pod crashing urgently ASAP"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert "priority" in data
    assert "category" in data
    assert "department" in data
    assert "confidence" in data
    assert "requires_review" in data
    assert data["deadline_detected"] is not None
    assert "id" in data


def test_predict_endpoint_empty(client):
    response = client.post("/predict", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_list_tickets_endpoint(client):
    response = client.get("/tickets")
    assert response.status_code == 200
    data = response.get_json()
    assert "tickets" in data
    assert isinstance(data["tickets"], list)


def test_update_ticket_status(client):
    create_res = client.post("/predict", json={"ticket": "Test ticket for status update"})
    ticket_id = create_res.get_json()["id"]

    patch_res = client.patch(f"/tickets/{ticket_id}", json={"status": "Resolved"})
    assert patch_res.status_code == 200
    updated_data = patch_res.get_json()
    assert updated_data["status"] == "Resolved"


def test_analytics_endpoint(client):
    response = client.get("/analytics")
    assert response.status_code == 200
    data = response.get_json()
    assert "total" in data
    assert "open" in data
    assert "resolved" in data


def test_metrics_endpoint_with_confusion_matrix(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.get_json()
    assert "metrics" in data
    assert "priority" in data["metrics"]
    assert "accuracy" in data["metrics"]["priority"]
    assert "confusion_matrix" in data["metrics"]["priority"]
    assert "candidate_benchmark_cv" in data


def test_auth_register_and_login(client):
    import time
    username = f"testuser_{int(time.time() * 1000)}"
    reg_payload = {"username": username, "email": f"{username}@test.com", "password": "password123", "role": "customer"}
    reg_res = client.post("/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    assert "token" in reg_res.get_json()

    login_res = client.post("/auth/login", json={"username": username, "password": "password123"})
    assert login_res.status_code == 200
    assert "token" in login_res.get_json()
    assert login_res.get_json()["user"]["username"] == username


def test_priority_override_with_reason(client):
    create_res = client.post("/predict", json={"ticket": "Routine documentation request"})
    ticket_id = create_res.get_json()["id"]

    override_payload = {
        "priority": "High",
        "reason": "Executive requested expedited handling"
    }
    ov_res = client.post(f"/tickets/{ticket_id}/priority-override", json=override_payload)
    assert ov_res.status_code == 200
    ticket_data = ov_res.get_json()["ticket"]
    assert ticket_data["priority"] == "High"
    assert "Executive requested" in ticket_data["priority_override"]


def test_ticket_replies(client):
    create_res = client.post("/predict", json={"ticket": "VPN connection dropped"})
    ticket_id = create_res.get_json()["id"]

    reply_payload = {"message": "Please try resetting your VPN credentials.", "author_name": "agent_sarah"}
    rep_res = client.post(f"/tickets/{ticket_id}/replies", json=reply_payload)
    assert rep_res.status_code == 201
    assert rep_res.get_json()["reply"]["message"] == reply_payload["message"]


def test_assign_and_export_tickets(client):
    create_res = client.post("/predict", json={"ticket": "VPN dropping on gateway"})
    ticket_id = create_res.get_json()["id"]

    patch_res = client.patch(f"/tickets/{ticket_id}", json={"assigned_agent": "agent_sarah"})
    assert patch_res.status_code == 200
    assert patch_res.get_json()["assigned_agent"] == "agent_sarah"

    export_res = client.get("/export/tickets")
    assert export_res.status_code == 200
    assert b"ID,Ticket,Priority" in export_res.data

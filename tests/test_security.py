import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from auth import generate_jwt_token, decode_jwt_token


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_jwt_token_generation_and_decoding():
    user_payload = {"id": 10, "username": "test_agent", "email": "agent@test.com", "role": "agent"}
    token = generate_jwt_token(user_payload)
    assert isinstance(token, str)

    decoded = decode_jwt_token(token)
    assert decoded is not None
    assert decoded["sub"] == 10
    assert decoded["username"] == "test_agent"
    assert decoded["role"] == "agent"


def test_invalid_jwt_token_rejected():
    decoded = decode_jwt_token("invalid.bearer.token")
    assert decoded is None


def test_customer_cannot_delete_ticket(client):
    # Create ticket
    create_res = client.post("/predict", json={"ticket": "System failure test"})
    ticket_id = create_res.get_json()["id"]

    # Customer token
    cust_token = generate_jwt_token({"id": 50, "username": "customer_bob", "email": "bob@test.com", "role": "customer"})
    headers = {"Authorization": f"Bearer {cust_token}"}

    del_res = client.delete(f"/tickets/{ticket_id}", headers=headers)
    assert del_res.status_code == 403
    assert "Forbidden" in del_res.get_json()["error"]


def test_agent_can_delete_ticket(client):
    create_res = client.post("/predict", json={"ticket": "Delete test ticket"})
    ticket_id = create_res.get_json()["id"]

    agent_token = generate_jwt_token({"id": 1, "username": "admin", "email": "admin@nexusticket.com", "role": "admin"})
    headers = {"Authorization": f"Bearer {agent_token}"}

    del_res = client.delete(f"/tickets/{ticket_id}", headers=headers)
    assert del_res.status_code == 200

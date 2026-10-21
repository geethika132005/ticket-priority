"""
NEXUS AI - Enterprise Support Ticket Core REST API
Implements:
  - JWT Authentication & Role-Based Access Control (RBAC)
  - Real-time ML Inference with Calibrated Confidence & Review Flags
  - Separate ML Prediction Logging & Audit Event Sourcing
  - Thread-Safe Database Handlers & RFC-Compliant CSV Export
  - Model Diagnostics & Interactive Analytics
"""

import csv
import io
import json
import os
from typing import Optional

import joblib
import numpy as np
from flask import Flask, Response, jsonify, request

from auth import generate_jwt_token, get_authenticated_user, jwt_required, roles_required
from database import (
    add_ticket,
    add_ticket_reply,
    assign_ticket,
    create_user,
    delete_ticket,
    get_all_agents,
    get_all_tickets,
    get_sla_policies,
    get_ticket_analytics,
    get_ticket_by_id,
    get_ticket_events,
    get_ticket_replies,
    init_db,
    record_prediction,
    record_priority_override,
    update_ticket_priority,
    update_ticket_status,
    verify_user_login,
)
from deadline_parser import calculate_sla_target, extract_deadline
from preprocess import preprocess_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")
REPORT_PATH = os.path.join(MODEL_DIR, "evaluation_report.json")

app = Flask(__name__)

priority_model = None
category_model = None
department_model = None
vectorizer = None
model_version = "nexus-v2.1-calibrated"


def load_models() -> None:
    """Load serialized ML artifacts."""
    global priority_model, category_model, department_model, vectorizer, model_version

    priority_path = os.path.join(MODEL_DIR, "priority_model.pkl")
    category_path = os.path.join(MODEL_DIR, "category_model.pkl")
    department_path = os.path.join(MODEL_DIR, "department_model.pkl")
    vectorizer_path = os.path.join(MODEL_DIR, "vectorizer.pkl")

    for path in [priority_path, category_path, department_path, vectorizer_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file missing: {path}. Run 'python train_model.py' first.")

    vectorizer = joblib.load(vectorizer_path)
    priority_model = joblib.load(priority_path)
    category_model = joblib.load(category_path)
    department_model = joblib.load(department_path)


with app.app_context():
    init_db()
    load_models()


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC & HEALTH ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "service": "NEXUS AI Enterprise Support Intelligence API",
        "version": "2.2.0",
        "model_version": model_version,
        "endpoints": [
            "GET  /health",
            "POST /auth/register",
            "POST /auth/login",
            "GET  /auth/me",
            "POST /tickets (or /predict)",
            "GET  /tickets",
            "GET  /tickets/<id>",
            "PATCH /tickets/<id>",
            "POST /tickets/<id>/priority-override",
            "POST /tickets/<id>/assign",
            "POST /tickets/<id>/replies",
            "GET  /analytics/overview (or /analytics)",
            "GET  /analytics/model (or /metrics)",
            "GET  /export/tickets",
        ],
    })


@app.route("/health", methods=["GET"])
def health():
    models_loaded = all(m is not None for m in [priority_model, category_model, department_model, vectorizer])
    return jsonify({
        "status": "healthy" if models_loaded else "unhealthy",
        "models_loaded": models_loaded,
        "model_version": model_version,
        "database": "connected",
    }), (200 if models_loaded else 500)


# ─────────────────────────────────────────────────────────────────────────────
# AUTHENTICATION ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", "")).strip()
    role = str(data.get("role", "customer")).strip().lower()

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required."}), 400

    if role not in ["customer", "agent"]:
        return jsonify({"error": "Registration only allows 'customer' or 'agent' roles."}), 400

    user = create_user(username, email, password, role)
    if not user:
        return jsonify({"error": "Username or email already exists."}), 400

    token = generate_jwt_token(user)
    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "user": user,
    }), 201


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", "")).strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    user = verify_user_login(username, password)
    if not user:
        return jsonify({"error": "Invalid username or password."}), 401

    token = generate_jwt_token(user)
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user,
    }), 200


@app.route("/auth/me", methods=["GET"])
@jwt_required()
def get_me():
    user = request.current_user
    return jsonify({"user": user}), 200


# ─────────────────────────────────────────────────────────────────────────────
# TICKET CREATION & INFERENCE PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run_ml_inference(ticket_text: str):
    """Run preprocessing, vectorization, and multi-model inference with confidence scoring."""
    cleaned_text = preprocess_text(ticket_text)
    X = vectorizer.transform([cleaned_text])

    # Predict Priority and compute confidence
    pred_priority = str(priority_model.predict(X)[0])
    confidence = None
    if hasattr(priority_model, "predict_proba"):
        probs = priority_model.predict_proba(X)[0]
        confidence = round(float(np.max(probs)), 4)

    # Low-confidence threshold review indicator
    requires_review = bool(confidence is not None and confidence < 0.65)

    pred_category = str(category_model.predict(X)[0])
    pred_department = str(department_model.predict(X)[0])
    deadline = extract_deadline(ticket_text)
    sla_target = calculate_sla_target(pred_priority, ticket_text)

    return {
        "priority": pred_priority,
        "category": pred_category,
        "department": pred_department,
        "confidence": confidence,
        "requires_review": requires_review,
        "deadline_detected": deadline,
        "sla_deadline": sla_target,
    }


@app.route("/predict", methods=["POST"])
@app.route("/tickets", methods=["POST"])
def create_or_predict_ticket():
    data = request.get_json(silent=True) or {}
    ticket_text = str(data.get("ticket") or data.get("ticket_text") or "").strip()

    if not ticket_text:
        return jsonify({"error": "Please provide ticket text in the 'ticket' field."}), 400

    save_to_db = data.get("save", True)
    user_id = data.get("user_id")

    # If JWT provided, prefer authenticated user id
    auth_user = get_authenticated_user()
    if auth_user:
        user_id = auth_user.get("sub", user_id)

    assigned_agent = data.get("assigned_agent", "Unassigned")

    # Run AI inference
    inference = run_ml_inference(ticket_text)

    response = {
        "ticket": ticket_text,
        "priority": inference["priority"],
        "category": inference["category"],
        "department": inference["department"],
        "confidence": inference["confidence"],
        "requires_review": inference["requires_review"],
        "model_version": model_version,
        "deadline_detected": inference["deadline_detected"],
        "sla_deadline": inference["sla_deadline"],
    }

    if save_to_db:
        saved = add_ticket(
            ticket=ticket_text,
            priority=inference["priority"],
            category=inference["category"],
            department=inference["department"],
            deadline_detected=inference["deadline_detected"],
            status="Open",
            user_id=user_id,
            assigned_agent=assigned_agent,
            sla_deadline=inference["sla_deadline"],
        )
        ticket_id = saved["id"]
        response["id"] = ticket_id
        response["status"] = saved["status"]
        response["created_at"] = saved["created_at"]
        response["user_id"] = saved["user_id"]
        response["assigned_agent"] = saved["assigned_agent"]

        # Store initial prediction separately for audit/evaluation
        record_prediction(
            ticket_id=ticket_id,
            predicted_priority=inference["priority"],
            confidence=inference["confidence"],
            model_version=model_version,
            requires_review=inference["requires_review"],
        )

    return jsonify(response), 200


# ─────────────────────────────────────────────────────────────────────────────
# TICKET RETRIEVAL & MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/tickets", methods=["GET"])
def list_tickets():
    auth_user = get_authenticated_user()

    status_filter = request.args.get("status")
    priority_filter = request.args.get("priority")
    search_query = request.args.get("search")
    assigned_agent_arg = request.args.get("assigned_agent")
    user_id_arg = request.args.get("user_id")

    # Enforce Customer privacy: customers can ONLY see their own tickets
    user_id = None
    if auth_user and auth_user.get("role") == "customer":
        user_id = int(auth_user["sub"])
    elif user_id_arg and user_id_arg.isdigit():
        user_id = int(user_id_arg)

    tickets = get_all_tickets(
        status_filter=status_filter,
        priority_filter=priority_filter,
        search_query=search_query,
        user_id=user_id,
        assigned_agent=assigned_agent_arg,
    )
    return jsonify({"tickets": tickets, "count": len(tickets)}), 200


@app.route("/tickets/<int:ticket_id>", methods=["GET"])
def get_ticket_detail(ticket_id: int):
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": f"Ticket #{ticket_id} not found."}), 404

    # Privacy check for customers
    auth_user = get_authenticated_user()
    if auth_user and auth_user.get("role") == "customer":
        if ticket.get("user_id") != auth_user["sub"]:
            return jsonify({"error": "Forbidden: You cannot access other customers' tickets."}), 403

    replies = get_ticket_replies(ticket_id)
    timeline = get_ticket_events(ticket_id)
    return jsonify({
        "ticket": ticket,
        "replies": replies,
        "timeline": timeline,
    }), 200


@app.route("/tickets/<int:ticket_id>", methods=["PATCH"])
def update_ticket_route(ticket_id: int):
    data = request.get_json(silent=True) or {}
    updated = None

    auth_user = get_authenticated_user()
    author_name = auth_user["username"] if auth_user else "Agent"
    user_id = auth_user["sub"] if auth_user else None

    if "status" in data:
        new_status = str(data["status"]).strip()
        valid_statuses = ["Open", "In Progress", "Resolved", "Closed"]
        if new_status not in valid_statuses:
            return jsonify({"error": f"Invalid status. Must be one of {valid_statuses}."}), 400
        updated = update_ticket_status(ticket_id, new_status, author_name=author_name, user_id=user_id)

    if "assigned_agent" in data:
        agent_name = str(data["assigned_agent"]).strip()
        updated = assign_ticket(ticket_id, agent_name, author_name=author_name, user_id=user_id)

    if "priority" in data:
        new_priority = str(data["priority"]).strip()
        reason = str(data.get("reason", "Manual priority update")).strip()
        if new_priority in ["High", "Medium", "Low"]:
            updated = record_priority_override(
                ticket_id=ticket_id,
                new_priority=new_priority,
                reason=reason,
                author_name=author_name,
                user_id=user_id,
            )

    if not updated:
        return jsonify({"error": f"Ticket #{ticket_id} not found or no valid updates provided."}), 404

    return jsonify(updated), 200


@app.route("/tickets/<int:ticket_id>/priority-override", methods=["POST"])
def override_priority(ticket_id: int):
    data = request.get_json(silent=True) or {}
    new_priority = str(data.get("priority", "")).strip()
    reason = str(data.get("reason", "")).strip()

    if new_priority not in ["High", "Medium", "Low"]:
        return jsonify({"error": "Invalid priority. Must be 'High', 'Medium', or 'Low'."}), 400

    if not reason:
        return jsonify({"error": "A documented reason is required to override AI priority."}), 400

    auth_user = get_authenticated_user()
    author_name = auth_user["username"] if auth_user else "Support Agent"
    user_id = auth_user["sub"] if auth_user else None

    updated = record_priority_override(
        ticket_id=ticket_id,
        new_priority=new_priority,
        reason=reason,
        author_name=author_name,
        user_id=user_id,
    )
    if not updated:
        return jsonify({"error": f"Ticket #{ticket_id} not found."}), 404

    return jsonify({
        "message": "Priority override recorded successfully.",
        "ticket": updated,
    }), 200


@app.route("/tickets/<int:ticket_id>/assign", methods=["POST"])
def assign_ticket_route(ticket_id: int):
    data = request.get_json(silent=True) or {}
    agent_name = str(data.get("agent", "")).strip()
    if not agent_name:
        return jsonify({"error": "Agent name is required."}), 400

    auth_user = get_authenticated_user()
    author_name = auth_user["username"] if auth_user else "Dispatcher"
    user_id = auth_user["sub"] if auth_user else None

    updated = assign_ticket(ticket_id, agent_name, author_name=author_name, user_id=user_id)
    if not updated:
        return jsonify({"error": f"Ticket #{ticket_id} not found."}), 404

    return jsonify({"message": f"Assigned to {agent_name}", "ticket": updated}), 200


@app.route("/tickets/<int:ticket_id>/replies", methods=["POST"])
def add_reply(ticket_id: int):
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    if not message:
        return jsonify({"error": "Reply message cannot be empty."}), 400

    auth_user = get_authenticated_user()
    author_name = auth_user["username"] if auth_user else str(data.get("author_name", "User"))
    user_id = auth_user["sub"] if auth_user else data.get("user_id")

    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": f"Ticket #{ticket_id} not found."}), 404

    reply = add_ticket_reply(ticket_id, author_name, message, user_id)
    return jsonify({"message": "Reply added successfully", "reply": reply}), 201


@app.route("/tickets/<int:ticket_id>", methods=["DELETE"])
def delete_ticket_route(ticket_id: int):
    auth_user = get_authenticated_user()
    if auth_user and auth_user.get("role") not in ["agent", "admin"]:
        return jsonify({"error": "Forbidden: Only agents or admins can delete tickets."}), 403

    success = delete_ticket(ticket_id)
    if not success:
        return jsonify({"error": f"Ticket #{ticket_id} not found."}), 404
    return jsonify({"message": f"Ticket {ticket_id} deleted successfully."}), 200


@app.route("/agents", methods=["GET"])
def list_agents():
    agents = get_all_agents()
    return jsonify({"agents": agents}), 200


# ─────────────────────────────────────────────────────────────────────────────
# EXPORT, ANALYTICS & METRICS
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/export/tickets", methods=["GET"])
def export_tickets():
    tickets = get_all_tickets()
    if not tickets:
        return Response("No tickets found", mimetype="text/csv")

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    headers = [
        "ID", "Ticket", "Priority", "Category", "Department",
        "Confidence", "Requires Review", "Deadline", "Status",
        "Created At", "Assigned Agent", "SLA Deadline", "Priority Override"
    ]
    writer.writerow(headers)

    for t in tickets:
        writer.writerow([
            t.get("id", ""),
            t.get("ticket", ""),
            t.get("priority", ""),
            t.get("category", ""),
            t.get("department", ""),
            t.get("confidence", "N/A"),
            "Yes" if t.get("requires_review") else "No",
            t.get("deadline_detected") or "",
            t.get("status", ""),
            t.get("created_at", ""),
            t.get("assigned_agent") or "Unassigned",
            t.get("sla_deadline") or "",
            t.get("priority_override") or "None",
        ])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=nexus_tickets_export.csv"},
    )


@app.route("/analytics", methods=["GET"])
@app.route("/analytics/overview", methods=["GET"])
def analytics():
    stats = get_ticket_analytics()
    stats["sla_policies"] = get_sla_policies()
    return jsonify(stats), 200


@app.route("/metrics", methods=["GET"])
@app.route("/analytics/model", methods=["GET"])
def metrics():
    if not os.path.exists(REPORT_PATH):
        return jsonify({"error": "Model evaluation report not found. Run train_model.py."}), 404
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data), 200


if __name__ == "__main__":
    app.run(debug=False, use_reloader=False, host="0.0.0.0", port=5000)

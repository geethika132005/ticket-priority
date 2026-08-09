import os

import joblib
from flask import Flask, jsonify, request

from deadline_parser import extract_deadline
from preprocess import preprocess_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

app = Flask(__name__)

priority_model = None
category_model = None
department_model = None
vectorizer = None


def load_models() -> None:
    """Load trained ML models from the model folder."""
    global priority_model, category_model, department_model, vectorizer

    priority_path = os.path.join(MODEL_DIR, "priority_model.pkl")
    category_path = os.path.join(MODEL_DIR, "category_model.pkl")
    department_path = os.path.join(MODEL_DIR, "department_model.pkl")
    vectorizer_path = os.path.join(MODEL_DIR, "vectorizer.pkl")

    missing_files = [
        path
        for path in [priority_path, category_path, department_path, vectorizer_path]
        if not os.path.exists(path)
    ]

    if missing_files:
        raise FileNotFoundError(
            "Model files not found. Run 'python train_model.py' first."
        )

    vectorizer = joblib.load(vectorizer_path)
    priority_model = joblib.load(priority_path)
    category_model = joblib.load(category_path)
    department_model = joblib.load(department_path)


@app.route("/", methods=["GET"])
def home():
    return "Backend Running Successfully"


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)

    if not data or "ticket" not in data:
        return jsonify({"error": "Please provide JSON with a 'ticket' field."}), 400

    ticket_text = data["ticket"].strip()
    if not ticket_text:
        return jsonify({"error": "Ticket text cannot be empty."}), 400

    cleaned_text = preprocess_text(ticket_text)
    X = vectorizer.transform([cleaned_text])

    predicted_priority = priority_model.predict(X)[0]
    predicted_category = category_model.predict(X)[0]
    predicted_department = department_model.predict(X)[0]
    deadline = extract_deadline(ticket_text)

    response = {
        "ticket": ticket_text,
        "priority": predicted_priority,
        "category": predicted_category,
        "department": predicted_department,
        "deadline_detected": deadline,
    }

    return jsonify(response)


if __name__ == "__main__":
    load_models()
    app.run(debug=True, host="0.0.0.0", port=5000)

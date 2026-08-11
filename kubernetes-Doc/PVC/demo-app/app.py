from flask import Flask, jsonify, request
import json
import os

DATA_FILE = "/data/phonebook.json"
app = Flask(__name__)


def load_phonebook():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_phonebook(entries):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


@app.route("/")
def index():
    return jsonify({
        "message": "Phonebook demo app",
        "help": "GET /entries, POST /entries, DELETE /entries"
    })


@app.route("/entries", methods=["GET"])
def get_entries():
    return jsonify(load_phonebook())


@app.route("/entries", methods=["POST"])
def add_entry():
    data = request.get_json(silent=True)
    if not data or "name" not in data or "phone" not in data:
        return jsonify({"error": "Send JSON with name and phone"}), 400

    entries = load_phonebook()
    entries.append({"name": data["name"], "phone": data["phone"]})
    save_phonebook(entries)
    return jsonify(entries), 201


@app.route("/entries", methods=["DELETE"])
def clear_entries():
    save_phonebook([])
    return jsonify({"message": "Phonebook cleared"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

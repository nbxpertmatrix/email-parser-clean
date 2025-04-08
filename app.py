from flask import Flask, request, jsonify
from parse_and_store import parse_email_with_gpt, write_to_airtable

app = Flask(__name__)

@app.route("/parse-email", methods=["POST"])
def parse_email():
    data = request.json
    email_text = data.get("email_text")
    timestamp = data.get("timestamp")

    if not email_text:
        return jsonify({"error": "Missing 'email_text' in request"}), 400

    try:
        parsed = parse_email_with_gpt(email_text)
        write_to_airtable(parsed, timestamp=timestamp)
        return jsonify({"status": "success", "data": parsed})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # <-- this is the key change

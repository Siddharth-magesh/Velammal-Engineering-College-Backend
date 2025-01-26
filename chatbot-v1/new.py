from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer

app = Flask(__name__)

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

@app.route("/generate_embedding", methods=["POST"])
def generate_embedding():
    try:
        data = request.json
        text = data.get("text", "")

        if not text:
            return jsonify({"error": "Text is required for embedding"}), 400

        embedding = model.encode(text).tolist()

        return jsonify({"embedding": embedding})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Embedder Running")
    app.run(host="0.0.0.0", port=5000)

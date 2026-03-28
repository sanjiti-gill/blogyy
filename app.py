import json
import queue
import threading
import os
import traceback
from flask import Flask, render_template, request, Response, stream_with_context, jsonify
from engine import run_pipeline

app = Flask(__name__)

def sanitize_keyword(kw):
    if not kw:
        return "", True
    clean = kw.strip()
    return clean, False

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/health')
def health():
    return "OK", 200

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    keyword = data.get("keyword", "").strip()
    
    if not keyword:
        return jsonify({"error": "No keyword provided"}), 400

    clean_keyword, flagged = sanitize_keyword(keyword)
    
    if flagged:
        return jsonify({"error": "Invalid keyword"}), 400

    q = queue.Queue()

    def pipeline_thread():
        def progress(step, msg):
            q.put({"type": "progress", "step": step, "msg": msg})
        try:
            result = run_pipeline(clean_keyword, progress_callback=progress)
            q.put({"type": "done", "data": result})
        except Exception as e:
            print(f"PIPELINE ERROR: {traceback.format_exc()}")
            q.put({"type": "error", "msg": str(e)})

    threading.Thread(target=pipeline_thread, daemon=True).start()

    def stream():
        while True:
            try:
                item = q.get(timeout=110)
                yield f"data: {json.dumps(item)}\n\n"
                if item["type"] in ("done", "error"):
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'error', 'msg': 'Timeout'})}\n\n"
                break

    return Response(stream_with_context(stream()), mimetype="text/event-stream")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, threaded=True)

    
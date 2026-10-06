"""
Fruit Detection Server (Flask + YOLOv8)
รับภาพ -> ตรวจจับ/นับ apple, mango, orange -> ส่งจำนวนไป PHP API -> ตอบผลกลับ client

Endpoints
  GET  /health    ตรวจสถานะเซิร์ฟเวอร์/โมเดล
  POST /predict   form-data: file=<image>
                  query (ไม่บังคับ): conf=0.25  send=1|0  annotated=1|0
"""
import base64
import io
import logging
import os
import threading
import time

import requests
from flask import Flask, jsonify, request
from PIL import Image, ImageOps, UnidentifiedImageError
from requests.adapters import HTTPAdapter
from ultralytics import YOLO
from urllib3.util.retry import Retry

# ---------------------------------------------------------------- Config
MODEL_PATH = os.getenv("MODEL_PATH", "runs/detect/fruit_web_model/weights/best.pt")
API_URL = os.getenv("API_URL", "http://localhost:8080/smart_farm/api/store_inventory.php")
DEFAULT_CONF = float(os.getenv("CONF", "0.25"))
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "3"))
SEND_TO_API = os.getenv("SEND_TO_API", "1") == "1"   # ส่งไป PHP โดยปกติ
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
ALLOWED_EXT = {"jpg", "jpeg", "png", "bmp", "webp"}
CLASSES = ("apple", "mango", "orange")

# เลือกอุปกรณ์อัตโนมัติ: มี GPU ใช้ GPU ไม่มีใช้ CPU (override ด้วย DEVICE=cpu / 0)
def pick_device():
    env = os.getenv("DEVICE")
    if env:
        return int(env) if env.isdigit() else env
    try:
        import torch
        return 0 if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"

DEVICE = pick_device()

# ---------------------------------------------------------------- App setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("fruit-server")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

model = YOLO(MODEL_PATH)
model_lock = threading.Lock()   # YOLO predict ไม่ thread-safe ป้องกันคำขอชนกัน

# Session ใช้ connection ซ้ำ + retry เมื่อ network สะดุด (ลด latency และ overhead)
http = requests.Session()
http.mount("http://", HTTPAdapter(max_retries=Retry(
    total=2, backoff_factor=0.3,
    status_forcelist=(502, 503, 504), allowed_methods=frozenset(["POST"]))))

# warm-up ให้ request แรกไม่ช้า
try:
    model.predict(source=Image.new("RGB", (640, 640)), device=DEVICE, verbose=False)
    log.info("Model loaded (%s) on device=%s", MODEL_PATH, DEVICE)
except Exception as e:
    log.warning("Warm-up failed: %s", e)


# ---------------------------------------------------------------- Helpers
def allowed_file(name: str) -> bool:
    return "." in name and name.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def send_inventory(counts: dict) -> dict:
    """ส่งจำนวนไป PHP API ไม่ raise error เพื่อไม่ให้กระทบผลตรวจจับ"""
    t0 = time.perf_counter()
    try:
        res = http.post(API_URL, json=counts, timeout=API_TIMEOUT)
        body = res.json()
        ok = res.status_code == 200 and body.get("status") == "success"
        log.info("API %s: %s", res.status_code, body)
        return {"sent": ok, "http_status": res.status_code, "response": body,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 1)}
    except Exception as e:
        log.error("Send to API failed: %s", e)
        return {"sent": False, "error": str(e),
                "latency_ms": round((time.perf_counter() - t0) * 1000, 1)}


def to_base64_jpeg(bgr_array) -> str:
    rgb = bgr_array[..., ::-1]                       # BGR -> RGB
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------- Routes
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "model": os.path.basename(MODEL_PATH),
        "classes": list(model.names.values()),
        "device": str(DEVICE),
        "send_to_api": SEND_TO_API,
        "api_url": API_URL,
    }), 200


@app.route("/predict", methods=["POST"])
def predict():
    t_start = time.perf_counter()

    # ---- validate input
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded (use form-data key 'file')"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty file"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": f"Unsupported file type. Allowed: {sorted(ALLOWED_EXT)}"}), 415

    try:
        conf = float(request.args.get("conf", DEFAULT_CONF))
        if not 0.0 < conf <= 1.0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "conf must be a number in (0, 1]"}), 400

    do_send = request.args.get("send", "1" if SEND_TO_API else "0") == "1"
    want_image = request.args.get("annotated", "0") == "1"

    # ---- read image
    try:
        img = Image.open(io.BytesIO(file.read()))
        img = ImageOps.exif_transpose(img).convert("RGB")   # แก้ภาพมือถือที่หมุนผิด
    except (UnidentifiedImageError, OSError):
        return jsonify({"error": "File is not a valid image"}), 400

    # ---- inference
    try:
        t_inf = time.perf_counter()
        with model_lock:
            results = model.predict(source=img, device=DEVICE, conf=conf, verbose=False)
        inference_ms = round((time.perf_counter() - t_inf) * 1000, 1)
    except Exception as e:
        log.exception("Inference failed")
        return jsonify({"error": f"Inference failed: {e}"}), 500

    detections = []
    counts = {c: 0 for c in CLASSES}
    for r in results:
        for box in r.boxes:
            name = model.names[int(box.cls[0])]
            detections.append({
                "class": name,
                "confidence": round(float(box.conf[0]), 4),
                "bounding_box": [round(x, 2) for x in box.xyxy[0].tolist()],
            })
            if name in counts:
                counts[name] += 1

    # ---- forward to PHP API (แยก error ออกจากผลตรวจจับ)
    api_result = send_inventory(counts) if do_send else {"sent": False, "skipped": True}

    response = {
        "status": "success",
        "total": len(detections),
        "counts": counts,
        "api": api_result,
        "timing_ms": {"inference": inference_ms,
                      "total": round((time.perf_counter() - t_start) * 1000, 1)},
        "detections": detections,
    }
    if want_image and results:
        response["annotated_image_base64"] = to_base64_jpeg(results[0].plot())

    log.info("Detected %s (conf>=%.2f) in %.0f ms", counts, conf, inference_ms)
    return jsonify(response), 200


# ---------------------------------------------------------------- Errors
@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": f"File too large (max {MAX_UPLOAD_MB} MB)"}), 413


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(405)
def bad_method(_):
    return jsonify({"error": "Method not allowed"}), 405


if __name__ == "__main__":
    # threaded=True รองรับหลาย request; lock ด้านบนคุมการเรียกโมเดล
    app.run(host=HOST, port=PORT, threaded=True)

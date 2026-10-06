"""ทดสอบ server:  python test_client.py fruit.jpg [http://localhost:5000]"""
import sys
import requests

path = sys.argv[1]
base = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5000"

print(requests.get(f"{base}/health", timeout=5).json())
with open(path, "rb") as f:
    r = requests.post(f"{base}/predict", files={"file": f}, timeout=30)
data = r.json()
data.pop("annotated_image_base64", None)
print(r.status_code, data)

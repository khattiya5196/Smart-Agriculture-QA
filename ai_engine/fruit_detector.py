import time
import cv2
import requests
from ultralytics import YOLO

model = YOLO('runs/detect/fruit_web_model/weights/best.pt')
API_URL = "http://localhost:8080/smart_farm/api/store_inventory.php"
SEND_INTERVAL = 2.0  # วินาที: ไม่ส่งทุกเฟรมเพื่อไม่ให้ DB บวม

cap = cv2.VideoCapture(0)
last_sent = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, verbose=False)
    counts = {'apple': 0, 'mango': 0, 'orange': 0}

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            class_name = model.names[cls_id]
            if class_name in counts:
                counts[class_name] += 1

    # ส่ง JSON Payload ไปยัง API
    if time.time() - last_sent >= SEND_INTERVAL:
        try:
            t0 = time.time()
            res = requests.post(API_URL, json=counts, timeout=2)
            print("API Response:", res.json(), f"({(time.time()-t0)*1000:.0f} ms)")
        except Exception as e:
            print("Error sending inventory data:", e)
        last_sent = time.time()

    annotated = results[0].plot()
    cv2.putText(annotated, str(counts), (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.imshow("Fruit Detector (q = quit)", annotated)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

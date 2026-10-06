import cv2
from ultralytics import YOLO

MODEL_PATH = "runs/detect/fruit_web_model/weights/best.pt"   # ลอง "yolov8n.pt" เพื่อทดสอบ

model = YOLO(MODEL_PATH)
print("คลาสที่โมเดลรู้จัก:", model.names)

ok = False
for idx in (0, 1, 2):
    cap = cv2.VideoCapture(idx)
    ok, frame = cap.read()
    print(f"กล้อง index {idx}:", "เปิดได้" if ok else "เปิดไม่ได้")
    if ok:
        break
    cap.release()

if ok:
    results = model(frame, conf=0.10, verbose=False)   # conf ต่ำเพื่อดูว่ามีอะไรถูกตรวจเจอบ้าง
    for b in results[0].boxes:
        print(model.names[int(b.cls[0])], round(float(b.conf[0]), 2))
    print("จำนวนที่ตรวจเจอทั้งหมด:", len(results[0].boxes))
    cv2.imshow("debug (กดปุ่มใดก็ได้เพื่อปิด)", results[0].plot())
    cv2.waitKey(0)
    cap.release()
    cv2.destroyAllWindows()

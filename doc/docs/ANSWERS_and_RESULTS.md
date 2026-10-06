# ตารางบันทึกผล และคำตอบท้ายการทดลอง

## ตารางที่ 1: Integration Test Matrix
(ผล Pass/Fail และ Latency ต้องวัดจากเครื่องจริงของกลุ่มคุณ — ใช้คำสั่งใน README)

| ลำดับ | ต้นทาง | ปลายทาง | โปรโตคอล / Data Format | ผลทดสอบ | Latency (ms) |
|---|---|---|---|---|---|
| 1 | ESP32 | /store_telemetry.php | HTTP POST (x-www-form-urlencoded / JSON) | | |
| 2 | Python AI | /store_inventory.php | HTTP POST (form-data / JSON) | | |
| 3 | Postman | /get_latest.php | HTTP GET (application/json) | | |
| 4 | Flutter App | /get_latest.php | HTTP GET (JSON Fetch) | | |

## ตารางที่ 2: End-to-End Test

| สภาพแวดล้อม | อุณหภูมิที่อ่านได้ (°C) | จำนวนวัตถุจริง (ส้ม/แอปเปิล/มะม่วง) | AI ตรวจจับได้ | ค่าบน Flutter | เวลาอัปเดต (วินาที) |
|---|---|---|---|---|---|
| เคส 1 (ปกติ) | | | | | |
| เคส 2 (วางซ้อน) | | | | | |

## คำถามท้ายการทดลอง

**1) Concurrent Requests / Race Condition**
ESP32 เขียนตาราง `telemetry_data` ส่วน AI เขียน `warehouse_inventory` คนละตาราง และทุก request เป็น INSERT แถวใหม่ที่ใช้ AUTO_INCREMENT จึงไม่มี lost update และ InnoDB ใช้ row-level lock ทำให้ INSERT พร้อมกันปลอดภัย ปัญหาเกิดได้เมื่อหลายตัวส่งถี่มากจนเกิด connection เต็ม (max_connections) หรือเมื่อมีการอ่าน-แก้-เขียนแถวเดียวกัน
แนวทางระดับสถาปัตยกรรม: ใช้ Prepared Statement + InnoDB transaction, ตั้ง connection pooling / เพิ่ม max_connections, ใส่ Message Queue (RabbitMQ/Kafka/Redis) คั่นกลางให้ worker ตัวเดียวเขียน DB, ลดความถี่ส่งข้อมูล (AI ส่งเมื่อค่าเปลี่ยนหรือทุก N วินาที), ใส่ index บน created_at และจัดการ retry เมื่อเจอ deadlock (error 1213)

**2) HTTP REST เทียบกับ MQTT**
- Overhead: HTTP มี header ขนาดหลายร้อยไบต์ต่อ request และมักต้องเปิด TCP ใหม่ทุกครั้ง ส่วน MQTT เปิด connection ค้างไว้ header ขั้นต่ำเพียง 2 ไบต์
- Latency: MQTT ไม่ต้อง handshake ซ้ำ ส่งได้เร็วกว่า และเป็น push แบบ publish/subscribe (Flutter subscribe รับค่าทันทีแทนการ polling ทุก 3 วินาที)
- อื่น ๆ: รองรับ QoS 0/1/2, Last Will, retained message, ประหยัดพลังงานและแบนด์วิดท์บน ESP32 จึงเหมาะกับ IoT ที่มีอุปกรณ์จำนวนมาก
- ข้อแลกเปลี่ยน: ต้องมี Broker (Mosquitto/EMQX) และต้องมี subscriber บริการเขียนลง MySQL เพิ่ม

**3) Merge Conflict ในไฟล์ api/store.php**
1. `git fetch origin` แล้ว `git merge origin/main` (หรือ rebase) บน feature branch ของตนเอง
2. `git status` ดูไฟล์ที่ conflict แล้วเปิดไฟล์ดู marker `<<<<<<< HEAD`, `=======`, `>>>>>>>`
3. วิเคราะห์ว่าแต่ละฝั่งแก้อะไร (`git diff`, `git log -p`) และคุยกับเพื่อนเจ้าของการแก้ไขว่าต้องการเก็บส่วนใด
4. แก้ไฟล์ให้เป็นเวอร์ชันสุดท้ายที่ถูกต้อง (เก็บของฝั่งใดฝั่งหนึ่งหรือรวมกัน) แล้วลบ marker ทั้งหมด
5. ทดสอบ API ให้ทำงานได้
6. `git add api/store.php` -> `git commit` -> `git push` แล้วขอ Review ใน Pull Request ก่อน merge
การป้องกัน: แบ่งความรับผิดชอบไฟล์ให้ชัด, pull main บ่อย, commit ขนาดเล็ก

**4) แสงเปลี่ยนแล้ว AI ตรวจจับผิด — ใช้เซนเซอร์แสง (LDR/BH1750)**
- ติด BH1750 กับ ESP32 ส่งค่า lux ไป API ในตาราง telemetry (เพิ่มคอลัมน์ `lux`)
- ฝั่ง AI ดึงค่า lux ล่าสุดมาปรับก่อน/หลังตรวจจับ: ถ้า lux ต่ำให้ปรับ preprocessing (gamma correction / CLAHE / เพิ่ม exposure), หรือสลับใช้โมเดลที่เทรนกับภาพแสงน้อย
- ปรับ confidence threshold ตามช่วงแสง เช่น lux ต่ำให้เพิ่ม threshold ลดผลบวกลวง
- สั่งเปิด/ปิดไฟส่องสว่างผ่าน relay ให้แสงคงที่ (closed loop)
- ตั้ง flag "ข้อมูลไม่น่าเชื่อถือ" เมื่อ lux อยู่นอกช่วงที่โมเดลเทรนมา และเก็บ lux คู่กับผลนับเพื่อวิเคราะห์ย้อนหลังและเทรนโมเดลเพิ่ม (data augmentation ด้านความสว่าง)

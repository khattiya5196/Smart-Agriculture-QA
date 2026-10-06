CREATE DATABASE IF NOT EXISTS smart_farm_db CHARACTER SET utf8mb4;
USE smart_farm_db;

-- 1. ตารางเก็บข้อมูลสภาวะแวดล้อม (Telemetry)
CREATE TABLE IF NOT EXISTS telemetry_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    temperature FLOAT NOT NULL,
    humidity FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. ตารางเก็บข้อมูลคลังสินค้า/จำนวนผลไม้ (Warehouse Inventory)
CREATE TABLE IF NOT EXISTS warehouse_inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    apple_count INT DEFAULT 0,
    mango_count INT DEFAULT 0,
    orange_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json");
require_once '../db.php';

// ดึงข้อมูล Telemetry ล่าสุด
$r1 = $conn->query("SELECT * FROM telemetry_data ORDER BY id DESC LIMIT 1");
$telemetry_data = ($r1 && $r1->num_rows > 0) ? $r1->fetch_assoc() : null;

// ดึงข้อมูล Inventory ล่าสุด
$r2 = $conn->query("SELECT * FROM warehouse_inventory ORDER BY id DESC LIMIT 1");
$inventory_data = ($r2 && $r2->num_rows > 0) ? $r2->fetch_assoc() : null;

echo json_encode([
    "status" => "success",
    "telemetry" => $telemetry_data,
    "inventory" => $inventory_data
]);
?>

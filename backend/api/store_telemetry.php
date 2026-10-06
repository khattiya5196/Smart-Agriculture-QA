<?php
header("Content-Type: application/json");
require_once '../db.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $data = get_input();
    $temp = isset($data['temperature']) ? floatval($data['temperature']) : 0.0;
    $hum  = isset($data['humidity'])    ? floatval($data['humidity'])    : 0.0;

    $stmt = $conn->prepare("INSERT INTO telemetry_data (temperature, humidity) VALUES (?, ?)");
    $stmt->bind_param("dd", $temp, $hum);

    if ($stmt->execute()) {
        echo json_encode(["status" => "success", "message" => "Telemetry data saved"]);
    } else {
        echo json_encode(["status" => "error", "message" => $stmt->error]);
    }
    $stmt->close();
} else {
    http_response_code(405);
    echo json_encode(["status" => "error", "message" => "Use POST"]);
}
?>

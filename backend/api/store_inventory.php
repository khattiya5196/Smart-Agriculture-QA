<?php
header("Content-Type: application/json");
require_once '../db.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $data = get_input();
    $apple  = isset($data['apple'])  ? intval($data['apple'])  : 0;
    $mango  = isset($data['mango'])  ? intval($data['mango'])  : 0;
    $orange = isset($data['orange']) ? intval($data['orange']) : 0;

    $stmt = $conn->prepare("INSERT INTO warehouse_inventory (apple_count, mango_count, orange_count) VALUES (?, ?, ?)");
    $stmt->bind_param("iii", $apple, $mango, $orange);

    if ($stmt->execute()) {
        echo json_encode(["status" => "success", "message" => "Inventory data saved"]);
    } else {
        echo json_encode(["status" => "error", "message" => $stmt->error]);
    }
    $stmt->close();
} else {
    http_response_code(405);
    echo json_encode(["status" => "error", "message" => "Use POST"]);
}
?>

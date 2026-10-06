<?php
$host = "localhost";
$user = "root";
$pass = "";
$dbname = "smart_farm_db";

$conn = new mysqli($host, $user, $pass, $dbname);
if ($conn->connect_error) {
    die(json_encode(["status" => "error", "message" => "Database Connection Failed"]));
}
$conn->set_charset("utf8mb4");

// รองรับทั้ง JSON, x-www-form-urlencoded และ multipart/form-data
function get_input() {
    $raw = file_get_contents('php://input');
    $json = json_decode($raw, true);
    return is_array($json) ? $json : $_POST;
}
?>

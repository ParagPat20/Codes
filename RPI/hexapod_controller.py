import serial
import time
from typing import Dict, Any
from hexapod_config import HexapodConfig

class HexapodController:
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200):
        self.serial = serial.Serial(port, baudrate)
        self.config = HexapodConfig.load_default()
        time.sleep(2)  # Wait for ESP32 to initialize

    def send_command(self, command: str):
        self.serial.write(f"{command}\n".encode())
        time.sleep(0.05)  # Small delay between commands
        response = self.serial.readline().decode().strip()
        print(f"ESP32 response: {response}")

    def forward_command(self, command: str):
        print(f"Forwarding command to ESP32: {command}")
        self.send_command(command)

    def set_servo_positions(self, positions: Dict[str, float]):
        command_parts = []
        for servo_id, angle in positions.items():
            if servo_id in self.config.inverted_motors:
                if self.config.inverted_motors[servo_id]:
                    angle = 180 - angle
            angle = max(0, min(180, angle + self.config.offsets.get(servo_id, 0)))
            command_parts.append(f"{servo_id}:{angle}")
        
        command = ",".join(command_parts)
        self.send_command(command)

    def set_dc_motors(self, left_speed: int, right_speed: int):
        command = f"LDC:{left_speed},RDC:{right_speed}"
        self.send_command(command)

    def shutdown(self):
        self.serial.close() 
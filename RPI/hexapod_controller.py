import serial
import time
from typing import Dict, Any
from hexapod_config import HexapodConfig

class HexapodController:
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200):
        self.serial = serial.Serial(port, baudrate)
        self.config = HexapodConfig()
        time.sleep(2)  # Wait for ESP32 to initialize

    def send_command(self, command: str):
        self.serial.write(f"{command}\n".encode())
        time.sleep(0.05)  # Small delay between commands
        response = self.serial.readline().decode().strip()
        print(f"ESP32 response: {response}")

    def forward_command(self, command: str):
        print(f"Forwarding command to ESP32: {command}")
        self.send_command(command)
        
        # Update config if it's a servo command
        try:
            if ":" in command:
                parts = command.split(",")
                for part in parts:
                    servo_id, angle = part.split(":")
                    if not servo_id.endswith("DC"):  # Skip DC motor commands
                        self.config.update_servo(servo_id, float(angle))
        except Exception as e:
            print(f"Error updating config: {e}")

    def get_current_config(self):
        return self.config.get_current_config()

    def shutdown(self):
        self.serial.close() 
import serial
import time
from typing import Dict, Any
from hexapod_config import HexapodConfig

class HexapodController:
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200):
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=1.0  # Add timeout
        )
        self.config = HexapodConfig()
        time.sleep(2)  # Wait for ESP32 to initialize

    def send_command(self, command: str, wait_for_response=False):
        try:
            print(f"Sending command: {command}")
            self.serial.write(f"{command}\n".encode())
            self.serial.flush()  # Ensure command is sent
            
            if wait_for_response:
                # Wait for response with timeout
                response = self.serial.readline().decode().strip()
                print(f"ESP32 response: {response}")
                return response
            return None
        except serial.SerialTimeoutException:
            print(f"Timeout sending command: {command}")
        except Exception as e:
            print(f"Error sending command: {command}, Error: {e}")

    def forward_command(self, command: str):
        print(f"Forwarding command to ESP32: {command}")
        response = self.send_command(command, wait_for_response=True)
        
        # Update config if it's a servo command and we got a response
        if response and ":" in command:
            try:
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
        if self.serial.is_open:
            self.serial.close() 
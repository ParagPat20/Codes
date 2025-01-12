import serial
import time
from typing import Dict, Any
from hexapod_config import HexapodConfig

class HexapodController:
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200):
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=1.0
        )
        self.config = HexapodConfig()
        time.sleep(2)  # Wait for ESP32 to initialize
        self.current_mode = "standby"

    def send_command(self, command: str, wait_for_response=False):
        try:
            # Clean up command to ensure it's just in format "LFC:180"
            if ":" in command:
                parts = command.split(":")
                servo_id = parts[0].strip()
                angle = int(float(parts[1].strip()))
                command = f"{servo_id}:{angle}"
                
            print(f"Sending: {command}")
            self.serial.write(f"{command}\n".encode())
            self.serial.flush()
            
            if wait_for_response:
                time.sleep(0.05)  # Small delay to wait for response
                if self.serial.in_waiting:
                    response = self.serial.readline().decode().strip()
                    print(f"Response: {response}")
                    return response
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def forward_command(self, command: str):
        self.send_command(command, wait_for_response=False)

    def set_mode(self, mode: str):
        """Set the hexapod's motion mode"""
        if mode in ["standby", "forward", "backward", "turn_left", "turn_right"]:
            self.send_command(mode)
            self.current_mode = mode
        else:
            print(f"Invalid mode: {mode}")

    def move_to_standby(self):
        """Move all servos to their standby positions"""
        self.set_mode("standby")

    def start_forward(self):
        """Start forward walking motion"""
        self.set_mode("forward")

    def start_backward(self):
        """Start backward walking motion"""
        self.set_mode("backward")

    def turn_left(self):
        """Start turning left"""
        self.set_mode("turn_left")

    def turn_right(self):
        """Start turning right"""
        self.set_mode("turn_right")

    def stop(self):
        """Stop any motion and return to standby"""
        self.move_to_standby()

    def get_current_config(self):
        return self.config.get_current_config()

    def update_servo(self, servo_id: str, angle: float):
        """Update a single servo's position"""
        self.config.update_servo(servo_id, angle)
        self.send_command(f"{servo_id}:{angle}")

    def shutdown(self):
        """Safely shutdown the controller"""
        self.stop()  # Return to standby position
        time.sleep(1)  # Wait for motion to complete
        if self.serial.is_open:
            self.serial.close() 
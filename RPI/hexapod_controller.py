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

    def standup_sequence(self):
        print("Starting standup sequence...")
        
        # Step 1: Initialize all servos to safe positions
        initial_positions = {
            # Front legs
            "L1": 90, "L2": 90, "L3": 90,  # Left front
            "R16": 90, "R15": 90, "R14": 90,  # Right front
            
            # Middle legs
            "L8": 90, "L5": 90, "L6": 90, "L7": 90,  # Left middle
            "R8": 90, "R6": 90, "R10": 90, "R12": 90,  # Right middle
            
            # Back legs
            "L12": 90, "L9": 90, "L10": 90,  # Left back
            "R3": 90, "R2": 90, "R1": 90  # Right back
        }
        self.set_servo_positions(initial_positions)
        time.sleep(1)

        # Step 2: Use DC motors to help lift the body
        self.set_dc_motors(150, -150)  # Opposite directions to create twist
        time.sleep(0.5)
        
        # Step 3: Position legs for standing
        standing_positions = {
            # Front legs
            "L1": 45, "L2": 135, "L3": 90,  # Left front
            "R16": 135, "R15": 45, "R14": 90,  # Right front
            
            # Middle legs
            "L8": 90, "L5": 135, "L6": 90, "L7": 45,  # Left middle
            "R8": 90, "R6": 135, "R10": 90, "R12": 45,  # Right middle
            
            # Back legs
            "L12": 135, "L9": 135, "L10": 90,  # Left back
            "R3": 45, "R2": 45, "R1": 90  # Right back
        }
        self.set_servo_positions(standing_positions)
        time.sleep(1)

        # Step 4: Stop DC motors
        self.set_dc_motors(0, 0)
        print("Standup sequence completed")

    def shutdown(self):
        self.serial.close() 
from dataclasses import dataclass
from typing import Dict, Any
import json
from pathlib import Path

class HexapodConfig:
    def __init__(self):
        self.config_file = Path(__file__).parent / 'standing_position.json'
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                # We only need the servos part for the controller
                return data.get("servos", {
                    "LEFT": {"FRONT": {}, "MID": {}, "BACK": {}},
                    "RIGHT": {"FRONT": {}, "MID": {}, "BACK": {}}
                })
        except FileNotFoundError:
            print(f"Config file {self.config_file} not found")
            return {
                "LEFT": {"FRONT": {}, "MID": {}, "BACK": {}},
                "RIGHT": {"FRONT": {}, "MID": {}, "BACK": {}}
            }
        except json.JSONDecodeError:
            print(f"Error parsing {self.config_file}")
            return {
                "LEFT": {"FRONT": {}, "MID": {}, "BACK": {}},
                "RIGHT": {"FRONT": {}, "MID": {}, "BACK": {}}
            }

    def save_config(self):
        try:
            # Load existing config to preserve other settings
            with open(self.config_file, 'r') as f:
                full_config = json.load(f)
            
            # Update only the servos part
            full_config["servos"] = self.config
            
            with open(self.config_file, 'w') as f:
                json.dump(full_config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def update_servo(self, servo_id: str, angle: float):
        # Find and update the servo in the config
        for side in ["LEFT", "RIGHT"]:
            for section in ["FRONT", "MID", "BACK"]:
                if servo_id in self.config[side][section]:
                    self.config[side][section][servo_id]["angle"] = angle
                    return True
        return False

    def get_current_config(self):
        return {"servos": self.config}  # Match the expected structure 
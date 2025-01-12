from dataclasses import dataclass
from typing import Dict, Any
import json

class HexapodConfig:
    def __init__(self):
        self.config_file = 'standing_position.json'
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file {self.config_file} not found")
            return {}
        except json.JSONDecodeError:
            print(f"Error parsing {self.config_file}")
            return {}

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def update_servo(self, servo_id: str, angle: float):
        # Find and update the servo in the config
        for side in ["LEFT", "RIGHT"]:
            for section in ["FRONT", "MID", "BACK"]:
                if servo_id in self.config[side][section]:
                    self.config[side][section][servo_id]["angle"] = angle
                    return True
        return False

    def get_current_config(self):
        return self.config 
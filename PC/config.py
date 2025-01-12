import json
from pathlib import Path

class Config:
    def __init__(self):
        self.config_file = Path("servo_config.json")
        self.default_config = {
            "ip": "192.168.8.39",
            "port": 5000,
            "servos": {
                "LEFT": {
                    "FRONT": {
                        "L2": {"angle": 90, "inverted": False, "offset": 0},  # COXA
                        "L3": {"angle": 90, "inverted": False, "offset": 0},  # FEMUR
                        "L1": {"angle": 90, "inverted": False, "offset": 0}   # TIBIA
                    },
                    "MID": {
                        "L8": {"angle": 90, "inverted": False, "offset": 0},  # COXA
                        "L6": {"angle": 90, "inverted": False, "offset": 0},  # FEMUR1
                        "L7": {"angle": 90, "inverted": False, "offset": 0},  # FEMUR2
                        "L5": {"angle": 90, "inverted": False, "offset": 0}   # TIBIA
                    },
                    "BACK": {
                        "L11": {"angle": 90, "inverted": False, "offset": 0}, # COXA
                        "L10": {"angle": 90, "inverted": False, "offset": 0}, # FEMUR
                        "L9": {"angle": 90, "inverted": False, "offset": 0}   # TIBIA
                    }
                },
                "RIGHT": {
                    "FRONT": {
                        "R3": {"angle": 90, "inverted": False, "offset": 0},  # COXA
                        "R2": {"angle": 90, "inverted": False, "offset": 0},  # FEMUR
                        "R1": {"angle": 90, "inverted": False, "offset": 0}   # TIBIA
                    },
                    "MID": {
                        "R8": {"angle": 90, "inverted": False, "offset": 0},  # COXA
                        "R7": {"angle": 90, "inverted": False, "offset": 0},  # FEMUR1
                        "R6": {"angle": 90, "inverted": False, "offset": 0},  # FEMUR2
                        "R5": {"angle": 90, "inverted": False, "offset": 0}   # TIBIA
                    },
                    "BACK": {
                        "R9": {"angle": 90, "inverted": False, "offset": 0},  # COXA
                        "R11": {"angle": 90, "inverted": False, "offset": 0}, # FEMUR
                        "R10": {"angle": 90, "inverted": False, "offset": 0}  # TIBIA
                    }
                }
            }
        }
        self.config = self.load_config()

    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return self.default_config

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get_servo_config(self, side, section, servo_id):
        return self.config["servos"][side][section][servo_id]

    def update_servo(self, side, section, servo_id, angle=None, inverted=None, offset=None):
        if angle is not None:
            self.config["servos"][side][section][servo_id]["angle"] = angle
        if inverted is not None:
            self.config["servos"][side][section][servo_id]["inverted"] = inverted
        if offset is not None:
            self.config["servos"][side][section][servo_id]["offset"] = offset
        self.save_config() 
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
                        "LFC": {"angle": 0, "inverted": False, "offset": 0},   # COXA (L2)
                        "LFT": {"angle": 70, "inverted": False, "offset": 0},  # FEMUR (L3)
                        "LFB": {"angle": 180, "inverted": False, "offset": 0}  # TIBIA (L1)
                    },
                    "MID": {
                        "LMC": {"angle": 90, "inverted": False, "offset": 0},   # COXA (L8)
                        "LMT": {"angle": 160, "inverted": False, "offset": 0},  # FEMUR1 (L6)
                        "LMB": {"angle": 100, "inverted": False, "offset": 0},  # FEMUR2 (L7)
                        "LMF": {"angle": 0, "inverted": False, "offset": 33}    # TIBIA (L5)
                    },
                    "BACK": {
                        "LBC": {"angle": 0, "inverted": True, "offset": -20},   # COXA (L11)
                        "LBT": {"angle": 70, "inverted": True, "offset": 20},   # FEMUR (L10)
                        "LBB": {"angle": 180, "inverted": True, "offset": 0}    # TIBIA (L9)
                    }
                },
                "RIGHT": {
                    "FRONT": {
                        "RFC": {"angle": 0, "inverted": True, "offset": 0},    # COXA (R3)
                        "RFT": {"angle": 70, "inverted": False, "offset": 0},  # FEMUR (R2)
                        "RFB": {"angle": 180, "inverted": True, "offset": 0}   # TIBIA (R1)
                    },
                    "MID": {
                        "RMC": {"angle": 90, "inverted": False, "offset": 0},   # COXA (R8)
                        "RMT": {"angle": 160, "inverted": True, "offset": 0},   # FEMUR1 (R7)
                        "RMB": {"angle": 100, "inverted": False, "offset": 0},  # FEMUR2 (R6)
                        "RMF": {"angle": 0, "inverted": False, "offset": 0}     # TIBIA (R5)
                    },
                    "BACK": {
                        "RBC": {"angle": 0, "inverted": False, "offset": 0},    # COXA (R9)
                        "RBT": {"angle": 70, "inverted": False, "offset": 0},   # FEMUR (R11)
                        "RBB": {"angle": 180, "inverted": True, "offset": 0}    # TIBIA (R10)
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

    def get_all_servos(self):
        servos = []
        for side in ["LEFT", "RIGHT"]:
            for section in ["FRONT", "MID", "BACK"]:
                for servo_id in self.config["servos"][side][section]:
                    servos.append(servo_id)
        return servos 
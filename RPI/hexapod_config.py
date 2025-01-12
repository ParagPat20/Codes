from dataclasses import dataclass
from typing import Dict, Any
import json

@dataclass
class HexapodConfig:
    motor_groups: Dict[str, Dict[str, str]]
    servo_motors: Dict[str, float]
    dc_motors: Dict[str, int]
    offsets: Dict[str, int]
    inverted_motors: Dict[str, bool]

    @classmethod
    def load_default(cls):
        motor_groups = {
            'left_front': {
                "L2": "COXA",    # Front Leg
                "L3": "FRONT FEMUR",   # Front Mid
                "L1": "FRONT TIBIA"    # Front Lower
            },
            'left_center': {
                "L8": "MID COXA",      # Center Leg
                "L6": "MID FEMUR1",    # Center Upper
                "L7": "MID FEMUR2",     # Center Lower 2
                "L5": "MID TIBIA"      # Center Lower
            },
            'left_back': {
                "L11": "BACK COXA",   # Back Leg
                "L10": "BACK FEMUR",   # Back Mid
                "L9": "BACK TIBIA"   # Back Lower
            },
            'right_front': {
                "R3": "FRONT COXA",   # Front Leg
                "R2": "FRONT FEMUR",  # Front Mid
                "R1": "FRONT TIBIA"   # Front Lower
            },
            'right_center': {
                "R8": "MID COXA",     # Center Leg
                "R7": "MID FEMUR1",   # Center Upper
                "R6": "MID FEMUR2",   # Center Lower 2
                "R5": "MID TIBIA"    # Center Lower
            },
            'right_back': {
                "R9": "BACK COXA",    # Back Leg
                "R11": "BACK FEMUR",   # Back Mid
                "R10": "BACK FIBIA"   # Back Lower
            }
        }

        with open('config.json', 'r') as f:
            config = json.load(f)

        return cls(
            motor_groups=motor_groups,
            servo_motors=config['servo_motors'],
            dc_motors=config['dc_motors'],
            offsets=config['offsets'],
            inverted_motors=config['inverted_motors']
        ) 
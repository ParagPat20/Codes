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
                "L1": "Coxa",    # Front Leg
                "L2": "Femur",   # Front Mid
                "L3": "Tibia"    # Front Lower
            },
            'left_center': {
                "L8": "Coxa",      # Center Leg
                "L5": "Femur2",    # Center Upper
                "L6": "Femur",     # Center Lower 2
                "L7": "Tibia"      # Center Lower
            },
            'left_back': {
                "L12": "Coxa",   # Back Leg
                "L9": "Femur",   # Back Mid
                "L10": "Tibia"   # Back Lower
            },
            'right_front': {
                "R16": "Coxa",   # Front Leg
                "R15": "Femur",  # Front Mid
                "R14": "Tibia"   # Front Lower
            },
            'right_center': {
                "R8": "Coxa",     # Center Leg
                "R6": "Femur2",   # Center Upper
                "R10": "Femur",   # Center Lower 2
                "R12": "Tibia"    # Center Lower
            },
            'right_back': {
                "R3": "Coxa",    # Back Leg
                "R2": "Femur",   # Back Mid
                "R1": "Tibia"    # Back Lower
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
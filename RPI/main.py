from hexapod_controller import HexapodController
import zmq
import json
import time
import os
from pathlib import Path

# Get the directory where the script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

def load_standing_position():
    """Load standing position with proper error handling"""
    config_path = SCRIPT_DIR / 'standing_position.json'
    
    # If file doesn't exist, create it with default values
    if not config_path.exists():
        default_config = {
            "LEFT": {
                "FRONT": {
                    "L2": {"angle": 90, "inverted": False, "offset": 0},
                    "L3": {"angle": 90, "inverted": False, "offset": 0},
                    "L1": {"angle": 90, "inverted": False, "offset": 0}
                },
                "MID": {
                    "L8": {"angle": 90, "inverted": False, "offset": 0},
                    "L6": {"angle": 90, "inverted": False, "offset": 0},
                    "L7": {"angle": 90, "inverted": False, "offset": 0},
                    "L5": {"angle": 90, "inverted": False, "offset": 0}
                },
                "BACK": {
                    "L11": {"angle": 90, "inverted": False, "offset": 0},
                    "L10": {"angle": 90, "inverted": False, "offset": 0},
                    "L9": {"angle": 90, "inverted": False, "offset": 0}
                }
            },
            "RIGHT": {
                "FRONT": {
                    "R3": {"angle": 90, "inverted": False, "offset": 0},
                    "R2": {"angle": 90, "inverted": False, "offset": 0},
                    "R1": {"angle": 90, "inverted": False, "offset": 0}
                },
                "MID": {
                    "R8": {"angle": 90, "inverted": False, "offset": 0},
                    "R7": {"angle": 90, "inverted": False, "offset": 0},
                    "R6": {"angle": 90, "inverted": False, "offset": 0},
                    "R5": {"angle": 90, "inverted": False, "offset": 0}
                },
                "BACK": {
                    "R9": {"angle": 90, "inverted": False, "offset": 0},
                    "R11": {"angle": 90, "inverted": False, "offset": 0},
                    "R10": {"angle": 90, "inverted": False, "offset": 0}
                }
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        print(f"Created default standing_position.json at {config_path}")
        return default_config
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing standing_position.json: {e}")
        raise

def apply_leg_config(hexapod, config, side, section):
    """Apply configuration for a specific leg"""
    print(f"Configuring {side} {section} leg...")
    
    for servo_id, servo_config in config[side][section].items():
        try:
            angle = servo_config["angle"]
            if servo_config["inverted"]:
                angle = 180 - angle
            angle += servo_config["offset"]
            angle = max(0, min(180, angle))
            
            # Send simple command format
            command = f"{servo_id}:{angle}"
            hexapod.forward_command(command)
            time.sleep(0.1)  # Shorter delay between servos
        except Exception as e:
            print(f"Error configuring {servo_id}: {e}")
            return False
    
    time.sleep(0.2)  # Short delay after configuring all servos in a leg
    return True

def stand_sequence(hexapod, standing_position):
    """Execute standing sequence in specific order"""
    print("Starting stand sequence...")
    
    sequence = [
        ("LEFT", "FRONT"),
        ("RIGHT", "FRONT"),
        ("LEFT", "BACK"),
        ("RIGHT", "BACK"),
        ("LEFT", "MID"),
        ("RIGHT", "MID")
    ]
    
    for side, section in sequence:
        if not apply_leg_config(hexapod, standing_position, side, section):
            print(f"Error in {side} {section} leg configuration")
            return False
        time.sleep(0.05)  # Shorter delay between legs
    
    return True

def main():
    try:
        # Initialize the hexapod controller with the first available port
        available_ports = [f"/dev/ttyUSB{i}" for i in range(0, 4)] + [f"/dev/ttyACM{i}" for i in range(0, 4)]
        hexapod = None
        
        for port in available_ports:
            if os.path.exists(port):
                try:
                    hexapod = HexapodController(port=port)
                    print(f"Hexapod controller initialized on port {port}")
                    break
                except Exception as e:
                    print(f"Failed to initialize hexapod controller on port {port}: {e}")
                    continue
        
        if not hexapod:
            print("No valid port found for hexapod controller")
            return

        # ZMQ Server setup
        context = zmq.Context()
        
        # Socket for receiving commands (PULL)
        command_socket = context.socket(zmq.PULL)
        command_socket.bind("tcp://*:5000")
        
        # Socket for sending responses (PUSH)
        response_socket = context.socket(zmq.PUSH)
        response_socket.bind("tcp://*:5001")
        
        print("ZMQ server listening on ports 5000 (commands) and 5001 (responses)")
        
        # Load standing position
        standing_position = load_standing_position()
        
        # Stand sequence
        stand_sequence(hexapod, standing_position)
        

        while True:
            try:
                command_dict = command_socket.recv_json()  # Remove NOBLOCK flag
                print(f"Received command: {command_dict}")
                
                if isinstance(command_dict, dict):
                    if "command" in command_dict:
                        if command_dict["command"] == "get_values":
                            current_config = hexapod.get_current_config()
                            response_socket.send_json({"type": "current_values", "values": current_config})
                        elif command_dict["command"] == "stand":
                            print("Starting stand sequence...")
                            stand_sequence(hexapod, standing_position)
                            print("Stand sequence completed")
                    else:
                        # Handle regular servo commands
                        command_parts = [f"{motor}:{angle}" for motor, angle in command_dict.items()]
                        command = ",".join(command_parts)
                        hexapod.forward_command(command)
            except Exception as e:
                print(f"Error: {e}")
            
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nShutting down...")
        command_socket.close()
        response_socket.close()
        context.term()
        if hexapod:
            hexapod.shutdown()
    except Exception as e:
        print(f"Error: {e}")
        try:
            command_socket.close()
            response_socket.close()
            context.term()
            if hexapod:
                hexapod.shutdown()
        except:
            pass

if __name__ == "__main__":
    main() 
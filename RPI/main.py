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
            "ip": "192.168.8.39",
            "port": 5000,
            "servos": {
                "LEFT": {
                    "FRONT": {
                        "LFC": {"angle": 0, "inverted": False, "offset": 0, "old_id": "L2"},
                        "LFT": {"angle": 70, "inverted": False, "offset": 0, "old_id": "L3"},
                        "LFB": {"angle": 180, "inverted": False, "offset": 0, "old_id": "L1"}
                    },
                    "MID": {
                        "LMC": {"angle": 90, "inverted": False, "offset": 0, "old_id": "L8"},
                        "LMT": {"angle": 160, "inverted": False, "offset": 0, "old_id": "L6"},
                        "LMB": {"angle": 100, "inverted": False, "offset": 0, "old_id": "L7"},
                        "LMF": {"angle": 0, "inverted": False, "offset": 33, "old_id": "L5"}
                    },
                    "BACK": {
                        "LBC": {"angle": 0, "inverted": True, "offset": -20, "old_id": "L11"},
                        "LBT": {"angle": 70, "inverted": True, "offset": 20, "old_id": "L10"},
                        "LBB": {"angle": 180, "inverted": True, "offset": 0, "old_id": "L9"}
                    }
                },
                "RIGHT": {
                    "FRONT": {
                        "RFC": {"angle": 0, "inverted": True, "offset": 0, "old_id": "R3"},
                        "RFT": {"angle": 70, "inverted": False, "offset": 0, "old_id": "R2"},
                        "RFB": {"angle": 180, "inverted": True, "offset": 0, "old_id": "R1"}
                    },
                    "MID": {
                        "RMC": {"angle": 90, "inverted": False, "offset": 0, "old_id": "R8"},
                        "RMT": {"angle": 160, "inverted": True, "offset": 0, "old_id": "R7"},
                        "RMB": {"angle": 100, "inverted": False, "offset": 0, "old_id": "R6"},
                        "RMF": {"angle": 0, "inverted": False, "offset": 0, "old_id": "R5"}
                    },
                    "BACK": {
                        "RBC": {"angle": 0, "inverted": False, "offset": 0, "old_id": "R9"},
                        "RBT": {"angle": 70, "inverted": False, "offset": 0, "old_id": "R11"},
                        "RBB": {"angle": 180, "inverted": True, "offset": 0, "old_id": "R10"}
                    }
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
    
    try:
        servos = config["servos"][side][section]
        for servo_id, servo_config in servos.items():
            try:
                angle = servo_config["angle"]
                if servo_config["inverted"]:
                    angle = 180 - angle
                angle += servo_config["offset"]
                angle = max(0, min(180, angle))
                
                command = f"{servo_id}:{angle}"
                print(f"Sending command: {command}")
                hexapod.forward_command(command)
                time.sleep(0.1)
            except Exception as e:
                print(f"Error configuring {servo_id}: {e}")
                return False
        
        time.sleep(0.2)
        return True
    except Exception as e:
        print(f"Error in apply_leg_config: {e}")
        return False

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
        time.sleep(0.05)
    
    return True

def handle_motion_command(hexapod, command):
    """Handle motion commands from the GUI"""
    try:
        if command == "forward":
            hexapod.forward_command("forward")
        elif command == "backward":
            hexapod.forward_command("backward")
        elif command == "turn_left":
            hexapod.forward_command("turn_left")
        elif command == "turn_right":
            hexapod.forward_command("turn_right")
        elif command == "standby":
            hexapod.forward_command("standby")
        print(f"Sent motion command: {command}")
        return True
    except Exception as e:
        print(f"Error sending motion command: {e}")
        return False

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
        command_socket = context.socket(zmq.PULL)
        command_socket.bind("tcp://*:5000")
        response_socket = context.socket(zmq.PUSH)
        response_socket.bind("tcp://*:5001")
        
        print("ZMQ server listening on ports 5000 (commands) and 5001 (responses)")
        
        # Load standing position
        standing_position = load_standing_position()

        while True:
            try:
                command_dict = command_socket.recv_json()
                print(f"Received command: {command_dict}")
                
                if isinstance(command_dict, dict):
                    if "command" in command_dict:
                        command = command_dict["command"]
                        if command == "get_values":
                            current_config = hexapod.get_current_config()
                            response_socket.send_json({"type": "current_values", "values": current_config})
                        elif command == "stand":
                            print("Starting stand sequence...")
                            stand_sequence(hexapod, standing_position)
                            print("Stand sequence completed")
                        elif command in ["forward", "backward", "turn_left", "turn_right", "standby"]:
                            handle_motion_command(hexapod, command)
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
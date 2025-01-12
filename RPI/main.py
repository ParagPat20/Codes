from hexapod_controller import HexapodController
import zmq
import json
import time
import os

def load_standing_position():
    with open('standing_position.json', 'r') as f:
        return json.load(f)

def main():
    try:
        # Initialize the hexapod controller with the first available port
        available_ports = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0"]
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
        socket = context.socket(zmq.SUB)
        socket.bind("tcp://*:5000")
        socket.setsockopt_string(zmq.SUBSCRIBE, "")
        print("ZMQ server listening on port 5000")
        
        # Load standing position
        standing_position = load_standing_position()
        
        while True:
            try:
                command_dict = socket.recv_json()
                print(f"Received command: {command_dict}")
                
                if isinstance(command_dict, dict):
                    if "command" in command_dict:
                        if command_dict["command"] == "get_values":
                            # Send current configuration back to GUI
                            current_config = hexapod.get_current_config()
                            socket.send_json({"type": "current_values", "values": current_config})
                        elif command_dict["command"] == "stand":
                            # Apply standing position
                            for side in ["LEFT", "RIGHT"]:
                                for section in ["FRONT", "MID", "BACK"]:
                                    for servo_id, config in standing_position[side][section].items():
                                        angle = config["angle"]
                                        if config["inverted"]:
                                            angle = 180 - angle
                                        angle += config["offset"]
                                        angle = max(0, min(180, angle))
                                        hexapod.forward_command(f"{servo_id}:{angle}")
                                        time.sleep(0.1)  # Small delay between commands
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
        socket.close()
        context.term()
        if hexapod:
            hexapod.shutdown()
    except Exception as e:
        print(f"Error: {e}")
        try:
            socket.close()
            context.term()
            if hexapod:
                hexapod.shutdown()
        except:
            pass

if __name__ == "__main__":
    main() 
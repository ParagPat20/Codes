from hexapod_controller import HexapodController
import zmq
import json
import time
import os

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
        
        while True:
            try:
                command_dict = socket.recv_json()
                print(f"Received command: {command_dict}")
                
                # Convert dict to command string
                command_parts = [f"{motor}:{angle}" for motor, angle in command_dict.items()]
                command = ",".join(command_parts)
                
                # Forward to ESP32
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
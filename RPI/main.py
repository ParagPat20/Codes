from hexapod_controller import HexapodController
import socket
import json
import time

def main():
    try:
        # Initialize the hexapod controller
        hexapod = HexapodController()
        print("Hexapod controller initialized")

        # UDP Server setup
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(('0.0.0.0', 5000))  # Listen on all interfaces
        udp_socket.settimeout(0.1)  # Non-blocking socket
        print("UDP server listening on port 5000")

        # Execute standup sequence
        hexapod.standup_sequence()
        
        while True:
            try:
                # Check for UDP commands from PC
                data, addr = udp_socket.recvfrom(1024)
                if data:
                    command_dict = json.loads(data.decode())
                    print(f"Received command from {addr}: {command_dict}")
                    
                    # Convert dict to command string
                    command_parts = [f"{motor}:{angle}" for motor, angle in command_dict.items()]
                    command = ",".join(command_parts)
                    
                    # Forward to ESP32
                    hexapod.forward_command(command)
            except socket.timeout:
                # No UDP data received, continue loop
                pass
            except json.JSONDecodeError as e:
                print(f"Invalid JSON received: {e}")
            
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nShutting down...")
        udp_socket.close()
        hexapod.shutdown()
    except Exception as e:
        print(f"Error: {e}")
        try:
            udp_socket.close()
            hexapod.shutdown()
        except:
            pass

if __name__ == "__main__":
    main() 
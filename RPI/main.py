from hexapod_controller import HexapodController
import time

def main():
    try:
        # Initialize the hexapod controller
        hexapod = HexapodController()
        print("Hexapod controller initialized")

        # Execute standup sequence
        hexapod.standup_sequence()
        
        # Listen for commands from PC
        while True:
            if hexapod.serial.in_waiting > 0:
                command = hexapod.serial.readline().decode().strip()
                if command:
                    print(f"Received command from PC: {command}")
                    hexapod.forward_command(command)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nShutting down...")
        hexapod.shutdown()
    except Exception as e:
        print(f"Error: {e}")
        try:
            hexapod.shutdown()
        except:
            pass

if __name__ == "__main__":
    main() 
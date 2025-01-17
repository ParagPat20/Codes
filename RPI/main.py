import serial
import zmq
import time

# Serial setup
ser = None  # Initialize ser as None
ports = [f'ttyUSB{i}' for i in range(10)] + [f'ttyACM{i}' for i in range(10)] + [f'COM{i}' for i in range(1, 23) if i not in [4, 5]]
for port in ports:
    try:
        full_port = f"/dev/{port}" if port.startswith(('ttyUSB', 'ttyACM')) else port
        ser = serial.Serial(full_port, 115200, timeout=1, write_timeout=0)
        print(f"Connected to Arduino on port {full_port}")
        break
    except serial.SerialException:
        continue

if ser is None:
    print("Could not connect to any serial port")
    raise Exception("No serial connection available")

# ZMQ setup
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.bind("tcp://*:5556")
socket.subscribe("")  # Subscribe to all messages
print("ZMQ Subscriber started on port 5556")

while True:
    try:
        if ser is None:
            print("No serial connection")
            time.sleep(1)
            continue
            
        # Get command from PC (non-blocking)
        message = socket.recv_string(flags=zmq.NOBLOCK)
        # Send to Arduino
        ser.write(f"{message}\n".encode())
        print(f"Sent to Arduino: {message}")
    except zmq.Again:
        # No message available
        continue
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        ser = None  # Reset serial connection
        time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        continue 
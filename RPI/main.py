import serial
import time
import zmq

# Serial connection to Arduino
ports = [f'/dev/ttyUSB{i}' for i in range(0,10)] + [f'/dev/ttyACM{i}' for i in range(0,10)] + [f'COM{i}' for i in range(1,4)] + [f'COM{i}' for i in range(6,22)]
for port in ports:
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        print(f"Connected to {port}")
        break
    except serial.SerialException:
        pass
time.sleep(2)  # Wait for Arduino to reset

# ZMQ setup for receiving commands from PC
context = zmq.Context()
socket = zmq.Socket(context, zmq.REP)
socket.bind("tcp://*:5555")

def send_command(cmd):
    """Send command to Arduino and wait for acknowledgment"""
    ser.write(f"{cmd}\n".encode())
    ser.flush()
    print(f"Sent: {cmd}")
    # Wait for acknowledgment from Arduino
    response = ser.readline().decode().strip()
    return response

# Track last command to avoid duplicates
last_command = None

while True:
    try:
        # Wait for command from PC
        message = socket.recv_string()
        print(f"Received: {message}")
        
        # Only send if command is different from last one
        if message != last_command:
            # Forward command to Arduino
            response = send_command(message)
            last_command = message
            
            # Send acknowledgment back to PC
            if response == "OK":
                socket.send_string("OK")
            else:
                socket.send_string(f"ERROR: {response}")
        else:
            # Command is same as last one, just acknowledge without sending
            socket.send_string("OK")
        
    except Exception as e:
        print(f"Error: {e}")
        try:
            socket.send_string("ERROR")
        except:
            pass 
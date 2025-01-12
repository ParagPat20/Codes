import serial
import time
import zmq

# Serial connection to Arduino
ports = [f'/dev/ttyUSB{i}' for i in range(0,10)] + [f'/dev/ttyACM{i}' for i in range(0,10)]
for port in ports:
    try:
        ser = serial.Serial(port, 115200, timeout=1)
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

while True:
    try:
        # Wait for command from PC
        message = socket.recv_string()
        print(f"Received: {message}")
        
        # Forward command to Arduino
        send_command(message)
        
        # Send acknowledgment back to PC
        socket.send_string("OK")
        
    except Exception as e:
        print(f"Error: {e}")
        try:
            socket.send_string("ERROR")
        except:
            pass 
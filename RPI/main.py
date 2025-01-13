import serial
import time
import zmq
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hexapod.log'),
        logging.StreamHandler()
    ]
)

# Serial connection to Arduino
ports = [f'/dev/ttyUSB{i}' for i in range(0,10)] + [f'/dev/ttyACM{i}' for i in range(0,10)] + [f'COM{i}' for i in range(1,4)] + [f'COM{i}' for i in range(6,22)]
for port in ports:
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        logging.info(f"Connected to Arduino on {port}")
        break
    except serial.SerialException:
        logging.debug(f"Failed to connect to {port}")
        pass
time.sleep(2)  # Wait for Arduino to reset

# ZMQ setup for receiving commands from PC
context = zmq.Context()
socket = zmq.Socket(context, zmq.REP)
socket.bind("tcp://*:5555")
logging.info("ZMQ server started on port 5555")

def send_command(cmd):
    """Send command to Arduino and wait for acknowledgment"""
    try:
        logging.debug(f"Sending command to Arduino: {cmd}")
        ser.write(f"{cmd}\n".encode())
        ser.flush()
        
        # Wait for acknowledgment from Arduino
        raw_response = ser.readline()
        logging.debug(f"Raw response from Arduino: {raw_response}")
        
        try:
            response = raw_response.decode('utf-8', errors='ignore').strip()
            logging.debug(f"Decoded response: {response}")
        except UnicodeDecodeError:
            logging.warning(f"Failed to decode Arduino response: {raw_response}")
            response = "OK"  # Assume OK if can't decode response
        return response
    except Exception as e:
        logging.error(f"Serial communication error: {e}")
        return "ERROR"

# Track last command to avoid duplicates
last_command = None

while True:
    try:
        # Wait for command from PC
        message = socket.recv_string()
        logging.info(f"Received command from PC: {message}")
        
        # Only send if command is different from last one
        if message != last_command:
            logging.debug(f"New command detected (last: {last_command}, new: {message})")
            # Forward command to Arduino
            response = send_command(message)
            last_command = message
            
            # Send acknowledgment back to PC
            socket.send_string("OK")  # Always send OK to PC
            logging.debug("Sent OK to PC")
        else:
            logging.debug(f"Duplicate command ignored: {message}")
            # Command is same as last one, just acknowledge without sending
            socket.send_string("OK")
        
    except Exception as e:
        logging.error(f"Main loop error: {e}")
        try:
            socket.send_string("ERROR")
        except:
            logging.error("Failed to send error response to PC")
            pass 
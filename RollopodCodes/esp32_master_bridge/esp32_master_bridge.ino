/*
 * ESP32 Master Bridge (Serial to ESP-NOW)
 * 
 * This ESP32 connects to your PC via USB Serial and forwards commands
 * to the slave ESP32 on the robot via ESP-NOW wireless protocol.
 * 
 * Setup Instructions:
 * 1. Upload this sketch to ESP32 Master (connected to PC)
 * 2. Open Serial Monitor and send command: GET_MAC
 * 3. Note down the MAC address of the SLAVE ESP32
 * 4. Update SLAVE_MAC_ADDRESS array below with slave's MAC
 * 5. Re-upload this sketch
 * 
 * The Python GUI remains unchanged - it sends the same Serial commands.
 * This bridge transparently forwards them via ESP-NOW to the robot.
 * 
 * Requirements:
 * - ESP32 Arduino Core 2.0.0 or higher (3.0.0+ recommended)
 * - WiFi and ESP-NOW libraries (included in ESP32 core)
 * 
 * Based on ESP-NOW best practices from:
 * https://randomnerdtutorials.com/esp-now-esp32-arduino-ide/
 */

#include <esp_now.h>
#include <WiFi.h>
#include <esp_wifi.h>

// ============================================================
// IMPORTANT: Replace with your SLAVE ESP32's MAC Address
// Get it by uploading the slave sketch and checking Serial Monitor
// ============================================================
uint8_t SLAVE_MAC_ADDRESS[] = { 0x84, 0x1F, 0xE8, 0x2B, 0x52, 0x60 };
// Example: {0x24, 0x6F, 0x28, 0xAB, 0xCD, 0xEF}

// ESP-NOW peer info
esp_now_peer_info_t peerInfo;

// ============================================================
// Data Structures for ESP-NOW (Match exactly with slave)
// ============================================================

// Master -> Slave Command Structure
typedef struct cmd_struct {
  char command[16];
  int val1;
  int val2;
  float val3;
} cmd_struct;

// Slave -> Master Telemetry/Response Structure
typedef struct telemetry_struct {
  char type[10];
  char message[128];
  float pitch;
} telemetry_struct;

cmd_struct myCmd;
telemetry_struct myData;

// Command buffer for receiving Serial data
String serialBuffer = "";

// Status tracking
bool espnowInitialized = false;
bool peerAdded = false;
unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL = 5000;  // 5 seconds

// Function prototypes
void initESPNow();
void onDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status);
void onDataRecv(const esp_now_recv_info *recvInfo, const uint8_t *data, int len);
void sendCommandToSlave(String command);
void printMacAddress();
bool isMacAddressValid();

void setup() {
  // Initialize Serial communication with PC
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\n========================================");
  Serial.println("ESP32 Master Bridge - Serial to ESP-NOW");
  Serial.println("========================================");

  // Initialize ESP-NOW first so WiFi gets turned on
  initESPNow();

  // Print this device's MAC address
  Serial.print("\nMaster MAC Address: ");
  printMacAddress();

  // Check if slave MAC is configured
  if (!isMacAddressValid()) {
    Serial.println("\n*** WARNING: Slave MAC address not configured! ***");
    Serial.println("Please update SLAVE_MAC_ADDRESS in the code with your slave's MAC.");
    Serial.println("Upload slave sketch first and note its MAC address.");
  }

  Serial.println("\nBridge ready - waiting for Serial commands...");
  Serial.println("Type 'HELP' for available commands");
  Serial.println("Type 'GET_MAC' to see MAC addresses");
  Serial.println("==========================================\n");
}

void loop() {
  // Handle Serial input from PC
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      serialBuffer.trim();

      if (serialBuffer.length() > 0) {
        // Handle local bridge commands
        if (serialBuffer.equalsIgnoreCase("GET_MAC")) {
          Serial.print("Master MAC: ");
          printMacAddress();
          Serial.print("Slave MAC:  ");
          for (int i = 0; i < 6; i++) {
            Serial.printf("%02X", SLAVE_MAC_ADDRESS[i]);
            if (i < 5) Serial.print(":");
          }
          Serial.println();

          if (!isMacAddressValid()) {
            Serial.println("*** Slave MAC not configured! ***");
          }
        } else if (serialBuffer.equalsIgnoreCase("HELP")) {
          Serial.println("\n=== Bridge Commands ===");
          Serial.println("GET_MAC  - Show MAC addresses");
          Serial.println("HELP     - Show this help");
          Serial.println("\nAll other commands are forwarded to slave ESP32");
          Serial.println("See slave documentation for servo commands\n");
        } else if (serialBuffer.equalsIgnoreCase("PING")) {
          // Test connectivity
          Serial.println("Bridge OK - sending ping to slave...");
          sendCommandToSlave("INFO");
        } else {
          // Forward command to slave via ESP-NOW
          sendCommandToSlave(serialBuffer);
        }

        serialBuffer = "";
      }
    } else {
      serialBuffer += c;
    }
  }

  // Send periodic heartbeat to check connection
  if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
    lastHeartbeat = millis();
    // Could send a heartbeat ping here if needed
  }
}

// Initialize ESP-NOW
void initESPNow() {
  // Set device as a Wi-Fi Station
  WiFi.mode(WIFI_STA);
  
  // Disconnect from any AP first
  WiFi.disconnect();

  // Initialize ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("ERROR: ESP-NOW initialization failed!");
    return;
  }

  espnowInitialized = true;
  Serial.println("ESP-NOW initialized successfully");

  // Register callbacks (compatible with ESP32 Core 3.0.0+)
  esp_now_register_send_cb(onDataSent);
  esp_now_register_recv_cb(onDataRecv);

  // Add slave peer
  memset(&peerInfo, 0, sizeof(peerInfo));
  memcpy(peerInfo.peer_addr, SLAVE_MAC_ADDRESS, 6);
  peerInfo.channel = 0;      // Auto/default channel
  peerInfo.encrypt = false;  // No encryption for simplicity

  // Add peer
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("ERROR: Failed to add slave peer!");
    Serial.println("Make sure SLAVE_MAC_ADDRESS is correctly configured");
    return;
  }

  peerAdded = true;
  Serial.println("Slave peer added successfully");
}

// Callback when data is sent via ESP-NOW
void onDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status) {
  if (status != ESP_NOW_SEND_SUCCESS) {
    Serial.println("ERROR: ESP-NOW send failed!");
    Serial.println("Check if slave is powered on and in range");
  }
  // Don't print success message to avoid cluttering output
}

// Callback when data is received via ESP-NOW
void onDataRecv(const esp_now_recv_info *recvInfo, const uint8_t *incomingData, int len) {
  if (len == sizeof(telemetry_struct)) {
    memcpy(&myData, incomingData, sizeof(myData));
    
    // Forward to PC via Serial depending on message type
    if (strcmp(myData.type, "MPU") == 0) {
      Serial.printf("MPU_DATA %.2f\n", myData.pitch);
    } 
    else if (strcmp(myData.type, "OK") == 0 || strcmp(myData.type, "ERROR") == 0 || strcmp(myData.type, "INFO") == 0) {
      Serial.println(myData.message);
    }
  }
}

// Send command to slave ESP32 via ESP-NOW
void sendCommandToSlave(String command) {
  if (!espnowInitialized || !peerAdded) {
    Serial.println("ERROR: ESP-NOW not ready");
    return;
  }

  // Clear struct
  memset(&myCmd, 0, sizeof(myCmd));
  
  // Basic parsing
  command.trim();
  int spaceIndex1 = command.indexOf(' ');
  int spaceIndex2 = command.indexOf(' ', spaceIndex1 + 1);
  int spaceIndex3 = command.indexOf(' ', spaceIndex2 + 1);
  
  String cmd = "";
  if (spaceIndex1 != -1) {
    cmd = command.substring(0, spaceIndex1);
    
    // Parse arguments based on command type
    if (cmd == "MOTOR" || cmd == "TORQUE" || cmd == "FREQ" || cmd == "TELEMETRY" || cmd == "GET_CAL") {
      myCmd.val1 = command.substring(spaceIndex1 + 1).toInt();
    }
    else if (cmd == "ANGLE") {
      myCmd.val1 = command.substring(spaceIndex1 + 1, spaceIndex2).toInt();
      myCmd.val3 = command.substring(spaceIndex2 + 1).toFloat();
    }
    else if (cmd == "TICK") {
      myCmd.val1 = command.substring(spaceIndex1 + 1, spaceIndex2).toInt();
      myCmd.val2 = command.substring(spaceIndex2 + 1).toInt();
    }
    else if (cmd == "CAL_ALL") {
      myCmd.val1 = command.substring(spaceIndex1 + 1, spaceIndex2).toInt();
      myCmd.val3 = command.substring(spaceIndex2 + 1).toFloat();
    }
    else if (cmd == "CAL") {
      myCmd.val1 = command.substring(spaceIndex1 + 1, spaceIndex2).toInt();
      myCmd.val2 = command.substring(spaceIndex2 + 1, spaceIndex3).toInt();
      myCmd.val3 = command.substring(spaceIndex3 + 1).toFloat();
    }
  } else {
    cmd = command; // Single word command like "SLEEP", "WAKE", "GET_MPU"
  }
  
  // Copy command string safely
  strncpy(myCmd.command, cmd.c_str(), sizeof(myCmd.command) - 1);

  // Send structured data via ESP-NOW
  esp_err_t result = esp_now_send(SLAVE_MAC_ADDRESS, (uint8_t *) &myCmd, sizeof(myCmd));

  if (result != ESP_OK) {
    Serial.println("ERROR: Failed to send command to slave");
  }
}

// Print this device's MAC address
void printMacAddress() {
  uint8_t mac[6];
  WiFi.macAddress(mac);
  for (int i = 0; i < 6; i++) {
    Serial.printf("%02X", mac[i]);
    if (i < 5) Serial.print(":");
  }
  Serial.println();
}

// Check if slave MAC address has been configured (not default FF:FF:FF:FF:FF:FF)
bool isMacAddressValid() {
  for (int i = 0; i < 6; i++) {
    if (SLAVE_MAC_ADDRESS[i] != 0xFF) {
      return true;  // At least one byte is not FF, so it's configured
    }
  }
  return false;
}

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

#include <esp_idf_version.h>
#include <esp_now.h>
#include <WiFi.h>
#include <esp_wifi.h>

// Internal RF Antenna Setup for Seeed Studio XIAO ESP32-C6
void setupAntenna() {
#if defined(CONFIG_IDF_TARGET_ESP32C6) || defined(ARDUINO_SEEED_XIAO_ESP32C6) || defined(ESP32C6)
  pinMode(3, OUTPUT);
  digitalWrite(3, LOW); // Turn on antenna selection circuit
  delay(100);
  pinMode(14, OUTPUT);
  digitalWrite(14, LOW); // LOW = Built-in Internal PCB Antenna
  Serial.println("[ANTENNA] XIAO ESP32-C6: Internal PCB Antenna Configured (GPIO3=LOW, GPIO14=LOW)");
#else
  Serial.println("[ANTENNA] Standard ESP32 DevKit Board");
#endif
}

// ============================================================
// Target SLAVE ESP32 MAC Address (Updated to XIAO ESP32-C6)
// ============================================================
uint8_t SLAVE_MAC_ADDRESS[] = { 0x98, 0xA3, 0x16, 0x61, 0x1A, 0xC8 };
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
#ifndef LED_BUILTIN
#define LED_BUILTIN 15
#endif

// Non-blocking LED timing & mode control for Master
unsigned long lastMasterLedToggle = 0;
bool masterLedState = false;
int masterBurstToggles = 0;
unsigned long masterFailPauseEnd = 0;
unsigned long lastSlaveResponseTime = 0;
const unsigned long SLAVE_CONNECTED_TIMEOUT_MS = 3000;

void updateMasterLed() {
  unsigned long now = millis();

  // If in failed message pause, keep LED static OFF for the small pause period
  if (now < masterFailPauseEnd) {
    digitalWrite(LED_BUILTIN, LOW);
    return;
  }

  // 4 Fast Blinks on Confirm message sent (8 toggles @ 40ms)
  if (masterBurstToggles > 0) {
    if (now - lastMasterLedToggle >= 40) {
      lastMasterLedToggle = now;
      masterLedState = !masterLedState;
      digitalWrite(LED_BUILTIN, masterLedState ? HIGH : LOW);
      masterBurstToggles--;
    }
    return;
  }

  // Check if Slave is connected (received response/ACK within last 3 sec)
  bool isSlaveConnected = (now - lastSlaveResponseTime < SLAVE_CONNECTED_TIMEOUT_MS);

  if (!isSlaveConnected) {
    // Keep LED Solid ON if Slave is not connected
    digitalWrite(LED_BUILTIN, HIGH);
  } else {
    // Slow Blink (500ms ON / 500ms OFF) if Slave is connected
    if (now - lastMasterLedToggle >= 500) {
      lastMasterLedToggle = now;
      masterLedState = !masterLedState;
      digitalWrite(LED_BUILTIN, masterLedState ? HIGH : LOW);
    }
  }
}

// Function prototypes
void initESPNow();
void onDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status);
void onDataRecv(const esp_now_recv_info *recvInfo, const uint8_t *data, int len);
void sendCommandToSlave(String command);
void printMacAddress();
bool isMacAddressValid();

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // Initialize Serial communication with PC
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\n========================================");
#if defined(CONFIG_IDF_TARGET_ESP32C6) || defined(ARDUINO_SEEED_XIAO_ESP32C6) || defined(ESP32C6)
  Serial.println("ESP32-C6 Master Bridge - Serial to ESP-NOW");
  setupAntenna();
#else
  Serial.println("ESP32 DevKit Master Bridge - Serial to ESP-NOW");
  Serial.println("[ANTENNA] Standard ESP32 DevKit Board (Built-in PCB Antenna)");
#endif
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
          Serial.println("\n========================================================");
          Serial.println("         ROLLOPOD MASTER BRIDGE COMMAND REFERENCE        ");
          Serial.println("========================================================");
          Serial.println("SYSTEM & DIAGNOSTICS:");
          Serial.println("  PING                       - Test wireless connection link");
          Serial.println("  GET_MAC                    - Show Master & Slave MAC addresses");
          Serial.println("  INFO                       - Print current slave PCA9685 config");
          Serial.println("  TELEMETRY <1/0>            - Enable/Disable 10Hz pitch telemetry");
          Serial.println();
          Serial.println("POWER & MOTOR CONTROL:");
          Serial.println("  TORQUE <1/0>               - Enable (12V MOSFET ON) / Disable Servo power");
          Serial.println("  MOTOR <speed>              - Set DC Motor speed (-255 to +255)");
          Serial.println();
          Serial.println("SERVO CONTROL (PCA9685 16-CH):");
          Serial.println("  ANGLE <ch> <0.0-180.0>     - Set servo angle (0-15)");
          Serial.println("  TICK <ch> <102-512>        - Set raw PWM tick value (0-4095)");
          Serial.println();
          Serial.println("CALIBRATION & FREQUENCY:");
          Serial.println("  CAL <ch> <min> <max>       - Calibrate min/max ticks for channel");
          Serial.println("  CAL_ALL <min> <max>        - Calibrate min/max ticks for all channels");
          Serial.println("  GET_CAL <ch>               - Read channel calibration");
          Serial.println("  GET_ALL_CAL                - Read all channel calibrations");
          Serial.println("  FREQ <hz>                  - Set PWM frequency (Default: 50 Hz)");
          Serial.println();
          Serial.println("POWER MANAGEMENT:");
          Serial.println("  SLEEP / WAKE / RESET       - PCA9685 sleep/wake/reset");
          Serial.println("========================================================\n");
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

  // Send periodic 2Hz heartbeat to check if Slave is truly connected (every 500ms)
  static unsigned long last2HzHeartbeat = 0;
  if (millis() - last2HzHeartbeat >= 500) {
    last2HzHeartbeat = millis();
    if (espnowInitialized && peerAdded) {
      memset(&myCmd, 0, sizeof(myCmd));
      strncpy(myCmd.command, "PING", sizeof(myCmd.command) - 1);
      esp_now_send(SLAVE_MAC_ADDRESS, (uint8_t *)&myCmd, sizeof(myCmd));
    }
  }

  // Update Master LED state continuously
  updateMasterLed();
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
#if defined(ESP_IDF_VERSION_MAJOR) && (ESP_IDF_VERSION_MAJOR >= 5)
void onDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status) {
#else
void onDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
#endif
  if (status == ESP_NOW_SEND_SUCCESS) {
    lastSlaveResponseTime = millis();
    // Only trigger fast blink burst for actual user commands, not background 2Hz heartbeats
    if (strcmp(myCmd.command, "PING") != 0) {
      masterBurstToggles = 8; // 4 fast blinks = 8 toggles @ 40ms
    }
  } else {
    // Only trigger failure pause for actual user commands
    if (strcmp(myCmd.command, "PING") != 0) {
      masterFailPauseEnd = millis() + 350;
      Serial.println("[LINK FAIL] Delivery FAILED - Slave offline or out of range!");
    }
  }
}

// Callback when data is received via ESP-NOW
#if defined(ESP_IDF_VERSION_MAJOR) && (ESP_IDF_VERSION_MAJOR >= 5)
void onDataRecv(const esp_now_recv_info *recvInfo, const uint8_t *incomingData, int len) {
#else
void onDataRecv(const uint8_t *srcMac, const uint8_t *incomingData, int len) {
#endif
  lastSlaveResponseTime = millis();
  if (len == sizeof(telemetry_struct)) {
    memcpy(&myData, incomingData, sizeof(myData));
    
    // Ignore background PONG heartbeats so PC Serial Log stays clean
    if (strcmp(myData.message, "PONG") == 0) {
      return;
    }
    
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

// Print this device's MAC address directly from Wi-Fi hardware
void printMacAddress() {
  uint8_t baseMac[6];
  esp_err_t ret = esp_wifi_get_mac(WIFI_IF_STA, baseMac);
  if (ret == ESP_OK) {
    Serial.printf("%02X:%02X:%02X:%02X:%02X:%02X\n",
                  baseMac[0], baseMac[1], baseMac[2],
                  baseMac[3], baseMac[4], baseMac[5]);
  } else {
    Serial.println(WiFi.macAddress());
  }
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

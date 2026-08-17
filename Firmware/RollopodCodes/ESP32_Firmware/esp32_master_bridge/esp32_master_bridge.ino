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
// Target SLAVE ESP32 MAC Addresses (Left & Right Boards)
// ============================================================
uint8_t LEFT_SLAVE_MAC[]  = { 0x98, 0xA3, 0x16, 0x61, 0x15, 0x40 };
uint8_t RIGHT_SLAVE_MAC[] = { 0x98, 0xA3, 0x16, 0x61, 0x1A, 0xC8 };

// ESP-NOW peer info
esp_now_peer_info_t leftPeerInfo;
esp_now_peer_info_t rightPeerInfo;

// ============================================================
// Data Structures for ESP-NOW (Match exactly with slaves)
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
bool leftPeerAdded = false;
bool rightPeerAdded = false;

#ifndef LED_BUILTIN
#define LED_BUILTIN 15
#endif

// Non-blocking LED timing & mode control for Master
unsigned long lastMasterLedToggle = 0;
bool masterLedState = false;
int masterBurstToggles = 0;
unsigned long masterFailPauseEnd = 0;

unsigned long lastLeftResponseTime = 0;
unsigned long lastRightResponseTime = 0;
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

  // Check if at least one Slave is connected
  bool isAnySlaveConnected = (now - lastLeftResponseTime < SLAVE_CONNECTED_TIMEOUT_MS) ||
                             (now - lastRightResponseTime < SLAVE_CONNECTED_TIMEOUT_MS);

  if (!isAnySlaveConnected) {
    // Keep LED Solid ON if no Slave is connected
    digitalWrite(LED_BUILTIN, HIGH);
  } else {
    // Slow Blink (500ms ON / 500ms OFF) if at least one Slave is connected
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
void printMacAddress(const uint8_t *mac);
bool isMacValid(const uint8_t *mac);

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // Initialize Serial communication with PC
  Serial.begin(115200);
#if defined(ARDUINO_USB_CDC_ON_BOOT) && (ARDUINO_USB_CDC_ON_BOOT == 1)
  Serial.setTxTimeoutMs(0); // 0ms timeout: Prevent Serial.print blocking on USB-CDC hardware
#endif
  delay(500);

  Serial.println("\n\n========================================");
#if defined(CONFIG_IDF_TARGET_ESP32C6) || defined(ARDUINO_SEEED_XIAO_ESP32C6) || defined(ESP32C6)
  Serial.println("ESP32-C6 Dual Master Bridge (Left & Right Slaves)");
  setupAntenna();
#else
  Serial.println("ESP32 DevKit Dual Master Bridge (Left & Right Slaves)");
  Serial.println("[ANTENNA] Standard ESP32 DevKit Board (Built-in PCB Antenna)");
#endif
  Serial.println("========================================");

  // Initialize ESP-NOW first so WiFi gets turned on
  initESPNow();

  // Print device MAC addresses
  Serial.print("\nMaster MAC: ");
  printMacAddress(NULL);
  Serial.print("Left Slave MAC:  ");
  printMacAddress(LEFT_SLAVE_MAC);
  Serial.print("Right Slave MAC: ");
  printMacAddress(RIGHT_SLAVE_MAC);

  Serial.println("\nDual Bridge ready - waiting for Serial commands...");
  Serial.println("Commands can be prefixed with 'L ', 'R ', or 'B ' (e.g., 'L ANGLE 0 90')");
  Serial.println("Type 'HELP' for available commands");
  Serial.println("Type 'GET_MAC' to see MAC addresses & status");
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
          unsigned long now = millis();
          bool leftOnline = (now - lastLeftResponseTime < SLAVE_CONNECTED_TIMEOUT_MS);
          bool rightOnline = (now - lastRightResponseTime < SLAVE_CONNECTED_TIMEOUT_MS);

          Serial.print("Master MAC:      ");
          printMacAddress(NULL);
          Serial.print("Left Slave MAC:  ");
          printMacAddress(LEFT_SLAVE_MAC);
          Serial.printf("  -> Status: %s\n", leftOnline ? "ONLINE" : "OFFLINE");
          Serial.print("Right Slave MAC: ");
          printMacAddress(RIGHT_SLAVE_MAC);
          Serial.printf("  -> Status: %s\n", rightOnline ? "ONLINE" : "OFFLINE");
        } else if (serialBuffer.equalsIgnoreCase("HELP")) {
          Serial.println("\n========================================================");
          Serial.println("   ROLLOPOD DUAL MASTER BRIDGE COMMAND REFERENCE         ");
          Serial.println("========================================================");
          Serial.println("TARGET PREFIXES:");
          Serial.println("  L <cmd>                    - Send command to LEFT Slave");
          Serial.println("  R <cmd>                    - Send command to RIGHT Slave");
          Serial.println("  B <cmd> (or no prefix)     - Send command to BOTH Slaves");
          Serial.println();
          Serial.println("EXAMPLES:");
          Serial.println("  L ANGLE 2 90               - Set Left Slave CH 2 to 90 deg");
          Serial.println("  R ANGLE 1 180              - Set Right Slave CH 1 to 180 deg");
          Serial.println("  B TORQUE 1                 - Turn ON 12V Power on BOTH Slaves");
          Serial.println("  GET_MAC                    - Show MACs and Connection Status");
          Serial.println("========================================================\n");
        } else if (serialBuffer.equalsIgnoreCase("PING")) {
          Serial.println("Bridge OK - pinging both Left & Right slaves...");
          sendCommandToSlave("B INFO");
        } else {
          // Forward command to slave(s) via ESP-NOW
          sendCommandToSlave(serialBuffer);
        }

        serialBuffer = "";
      }
    } else {
      serialBuffer += c;
    }
  }

  // Send periodic 2Hz heartbeats to BOTH slaves (every 500ms)
  static unsigned long last2HzHeartbeat = 0;
  if (millis() - last2HzHeartbeat >= 500) {
    last2HzHeartbeat = millis();
    if (espnowInitialized) {
      memset(&myCmd, 0, sizeof(myCmd));
      strncpy(myCmd.command, "PING", sizeof(myCmd.command) - 1);
      if (leftPeerAdded) {
        esp_now_send(LEFT_SLAVE_MAC, (uint8_t *)&myCmd, sizeof(myCmd));
      }
      if (rightPeerAdded) {
        esp_now_send(RIGHT_SLAVE_MAC, (uint8_t *)&myCmd, sizeof(myCmd));
      }
    }
  }

  // Update Master LED state continuously
  updateMasterLed();
}

// Initialize ESP-NOW
void initESPNow() {
  // Set device as a Wi-Fi Station
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  // Initialize ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("ERROR: ESP-NOW initialization failed!");
    return;
  }

  espnowInitialized = true;
  Serial.println("ESP-NOW initialized successfully");

  // Register callbacks
  esp_now_register_send_cb(onDataSent);
  esp_now_register_recv_cb(onDataRecv);

  // 1. Add Left Slave peer
  memset(&leftPeerInfo, 0, sizeof(leftPeerInfo));
  memcpy(leftPeerInfo.peer_addr, LEFT_SLAVE_MAC, 6);
  leftPeerInfo.channel = 0;
  leftPeerInfo.encrypt = false;
  if (esp_now_add_peer(&leftPeerInfo) == ESP_OK) {
    leftPeerAdded = true;
    Serial.println("Left Slave peer added successfully");
  } else {
    Serial.println("WARNING: Failed to add Left Slave peer!");
  }

  // 2. Add Right Slave peer
  memset(&rightPeerInfo, 0, sizeof(rightPeerInfo));
  memcpy(rightPeerInfo.peer_addr, RIGHT_SLAVE_MAC, 6);
  rightPeerInfo.channel = 0;
  rightPeerInfo.encrypt = false;
  if (esp_now_add_peer(&rightPeerInfo) == ESP_OK) {
    rightPeerAdded = true;
    Serial.println("Right Slave peer added successfully");
  } else {
    Serial.println("WARNING: Failed to add Right Slave peer!");
  }
}

// Callback when data is sent via ESP-NOW
#if defined(ESP_IDF_VERSION_MAJOR) && (ESP_IDF_VERSION_MAJOR >= 5)
void onDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status) {
#else
void onDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
#endif
  if (status == ESP_NOW_SEND_SUCCESS) {
    if (strcmp(myCmd.command, "PING") != 0) {
      masterBurstToggles = 8;
    }
  } else {
    if (strcmp(myCmd.command, "PING") != 0) {
      masterFailPauseEnd = millis() + 350;
      Serial.println("[LINK FAIL] Delivery FAILED - Slave offline or out of range!");
    }
  }
}

// Callback when data is received via ESP-NOW
#if defined(ESP_IDF_VERSION_MAJOR) && (ESP_IDF_VERSION_MAJOR >= 5)
void onDataRecv(const esp_now_recv_info *recvInfo, const uint8_t *incomingData, int len) {
  const uint8_t *srcMac = recvInfo->src_addr;
#else
void onDataRecv(const uint8_t *srcMac, const uint8_t *incomingData, int len) {
#endif
  bool isLeft = (srcMac && memcmp(srcMac, LEFT_SLAVE_MAC, 6) == 0);
  bool isRight = (srcMac && memcmp(srcMac, RIGHT_SLAVE_MAC, 6) == 0);

  if (isLeft) {
    lastLeftResponseTime = millis();
  } else if (isRight) {
    lastRightResponseTime = millis();
  }

  if (len == sizeof(telemetry_struct)) {
    memcpy(&myData, incomingData, sizeof(myData));
    
    // Ignore background PONG heartbeats
    if (strcmp(myData.message, "PONG") == 0) {
      return;
    }

    const char *tag = isLeft ? "[LEFT]" : (isRight ? "[RIGHT]" : "[UNKNOWN]");
    
    // Forward to PC via Serial depending on message type
    if (strcmp(myData.type, "MPU") == 0) {
      Serial.printf("%s MPU_DATA %.2f\n", tag, myData.pitch);
    } 
    else if (strcmp(myData.type, "OK") == 0 || strcmp(myData.type, "ERROR") == 0 || strcmp(myData.type, "INFO") == 0) {
      Serial.printf("%s %s\n", tag, myData.message);
    }
  }
}

// Send command to slave ESP32 via ESP-NOW with target prefix handling
void sendCommandToSlave(String command) {
  if (!espnowInitialized) {
    Serial.println("ERROR: ESP-NOW not ready");
    return;
  }

  command.trim();
  char targetBoard = 'B'; // Default: Both Slaves

  // Parse board target prefix (e.g., "L ANGLE 0 90", "L_ANGLE 0 90", "R ANGLE...", "B TORQUE...")
  if (command.startsWith("L ") || command.startsWith("L_")) {
    targetBoard = 'L';
    command = command.substring(2);
  } else if (command.startsWith("R ") || command.startsWith("R_")) {
    targetBoard = 'R';
    command = command.substring(2);
  } else if (command.startsWith("B ") || command.startsWith("B_") || command.startsWith("ALL ")) {
    targetBoard = 'B';
    int sp = command.indexOf(' ');
    if (sp != -1) command = command.substring(sp + 1);
  }
  command.trim();

  // Clear struct
  memset(&myCmd, 0, sizeof(myCmd));
  
  int spaceIndex1 = command.indexOf(' ');
  int spaceIndex2 = command.indexOf(' ', spaceIndex1 + 1);
  int spaceIndex3 = command.indexOf(' ', spaceIndex2 + 1);
  
  String cmd = "";
  if (spaceIndex1 != -1) {
    cmd = command.substring(0, spaceIndex1);
    
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
    cmd = command;
  }
  
  strncpy(myCmd.command, cmd.c_str(), sizeof(myCmd.command) - 1);

  // Send packet to target board(s)
  if ((targetBoard == 'L' || targetBoard == 'B') && leftPeerAdded) {
    esp_now_send(LEFT_SLAVE_MAC, (uint8_t *) &myCmd, sizeof(myCmd));
  }
  if ((targetBoard == 'R' || targetBoard == 'B') && rightPeerAdded) {
    esp_now_send(RIGHT_SLAVE_MAC, (uint8_t *) &myCmd, sizeof(myCmd));
  }
}

// Print MAC address formatted
void printMacAddress(const uint8_t *mac) {
  if (mac == NULL) {
    uint8_t baseMac[6];
    esp_err_t ret = esp_wifi_get_mac(WIFI_IF_STA, baseMac);
    if (ret == ESP_OK) {
      Serial.printf("%02X:%02X:%02X:%02X:%02X:%02X\n",
                    baseMac[0], baseMac[1], baseMac[2],
                    baseMac[3], baseMac[4], baseMac[5]);
    } else {
      Serial.println(WiFi.macAddress());
    }
  } else {
    Serial.printf("%02X:%02X:%02X:%02X:%02X:%02X\n",
                  mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  }
}

bool isMacValid(const uint8_t *mac) {
  if (!mac) return false;
  for (int i = 0; i < 6; i++) {
    if (mac[i] != 0xFF) return true;
  }
  return false;
}


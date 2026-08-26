/*
 * M_ESP32_SUB_MASTER — Rollopod Onboard Sub-Master (Inside Robot)
 *
 * Sits INSIDE the robot body. Acts as the command relay hub:
 *   - Receives commands from Remote ESP32 via ESP-NOW
 *   - Also accepts commands directly from RPi5 via USB Serial (priority)
 *   - Forwards commands to Left and Right Slaves via ESP-NOW
 *   - Receives telemetry from L/R Slaves and relays back to Remote ESP32
 *
 * Board: Seeed Studio XIAO ESP32-C6
 *
 * MAC Address Setup:
 *   1. Flash this sketch
 *   2. Open Serial Monitor -> it prints SUB_MASTER MAC
 *   3. Copy that MAC into Remote ESP32 as SUB_MASTER_MAC
 *   4. L/R Slaves auto-register via existing REGISTER_MASTER handshake
 */

#include <esp_idf_version.h>
#include <esp_now.h>
#include <WiFi.h>
#include <esp_wifi.h>
#include <Adafruit_NeoPixel.h>

// ============================================================
// NEOPIXEL CONFIGURATION (D10 / GPIO 18)
// 10 LEDs for Backlight + 1 LED for Front Head = 11 Total
// ============================================================
#define NEOPIXEL_PIN        18   // D10 / GPIO18 on XIAO ESP32-C6
#define NUM_BACKLIGHT_LEDS  10   // 10 LEDs for Backlight (indices 0..9)
#define NUM_HEAD_LEDS       1    // 1 LED for Front Head (index 10)
#define TOTAL_NEOPIXELS     (NUM_BACKLIGHT_LEDS + NUM_HEAD_LEDS) // 11 LEDs

Adafruit_NeoPixel strip(TOTAL_NEOPIXELS, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

// Helper functions for NeoPixels
void setAllNeoPixels(uint8_t r, uint8_t g, uint8_t b) {
  for (int i = 0; i < TOTAL_NEOPIXELS; i++) {
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
  strip.show();
}

void setBacklightColor(uint8_t r, uint8_t g, uint8_t b) {
  for (int i = 0; i < NUM_BACKLIGHT_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
  strip.show();
}

void setHeadColor(uint8_t r, uint8_t g, uint8_t b) {
  strip.setPixelColor(NUM_BACKLIGHT_LEDS, strip.Color(r, g, b));
  strip.show();
}

bool parseColor(String str, uint8_t &r, uint8_t &g, uint8_t &b) {
  str.trim();
  str.toLowerCase();

  // Color name / single letter shortcuts
  if (str == "r" || str == "red")       { r = 255; g = 0;   b = 0;   return true; }
  if (str == "g" || str == "green")     { r = 0;   g = 255; b = 0;   return true; }
  if (str == "b" || str == "blue")      { r = 0;   g = 0;   b = 255; return true; }
  if (str == "w" || str == "white")     { r = 255; g = 255; b = 255; return true; }
  if (str == "y" || str == "yellow")    { r = 255; g = 200; b = 0;   return true; }
  if (str == "o" || str == "orange")    { r = 255; g = 80;  b = 0;   return true; }
  if (str == "p" || str == "purple")    { r = 180; g = 0;   b = 255; return true; }
  if (str == "c" || str == "cyan")      { r = 0;   g = 255; b = 255; return true; }
  if (str == "off" || str == "black")   { r = 0;   g = 0;   b = 0;   return true; }

  // Numeric "R G B" (e.g. "255 0 0")
  int ir = 0, ig = 0, ib = 0;
  if (sscanf(str.c_str(), "%d %d %d", &ir, &ig, &ib) == 3) {
    r = constrain(ir, 0, 255);
    g = constrain(ig, 0, 255);
    b = constrain(ib, 0, 255);
    return true;
  }
  return false;
}

void initNeoPixels() {
  strip.begin();
  strip.setBrightness(180); // 0-255 brightness
  // Set all 11 LEDs to RED on startup
  setAllNeoPixels(255, 0, 0);
  Serial.println("[NEOPIXEL] Initialized 11 LEDs on GPIO18 (D10) -> Set to RED (10 Backlight + 1 Head)");
}

// ============================================================
// XIAO ESP32-C6 Internal Antenna Setup
// ============================================================
void setupAntenna() {
#if defined(CONFIG_IDF_TARGET_ESP32C6) || defined(ARDUINO_SEEED_XIAO_ESP32C6) || defined(ESP32C6)
  pinMode(3, OUTPUT);
  digitalWrite(3, LOW);
  delay(100);
  pinMode(14, OUTPUT);
  digitalWrite(14, LOW);
  Serial.println("[ANTENNA] XIAO ESP32-C6: Internal PCB Antenna (GPIO3=LOW, GPIO14=LOW)");
#else
  Serial.println("[ANTENNA] Standard ESP32 DevKit Board");
#endif
}

// ============================================================
// PEER MAC ADDRESSES
// UPDATE REMOTE_ESP32_MAC after flashing Remote ESP32 and
// running GET_MAC on its Serial Monitor
// ============================================================
uint8_t REMOTE_ESP32_MAC[] = { 0x20, 0xE7, 0xC8, 0xAD, 0x8C, 0xBC }; // Remote ESP32 MAC
uint8_t LEFT_SLAVE_MAC[]   = { 0x10, 0xBD, 0xA3, 0xA0, 0xF1, 0x9C };
uint8_t RIGHT_SLAVE_MAC[]  = { 0x98, 0xA3, 0x16, 0x61, 0x1A, 0xC8 };

// ============================================================
// DATA STRUCTURES (must match Remote ESP32 and Slaves exactly)
// ============================================================
typedef struct cmd_struct {
  char text[128];
} cmd_struct;

typedef struct telemetry_struct {
  char type[10];
  char message[128];
  float pitch;
} telemetry_struct;

cmd_struct       outCmd;
telemetry_struct outTelemetry;

// ============================================================
// STATE
// ============================================================
bool espnowInitialized  = false;
bool remotePeerAdded    = false;
bool leftPeerAdded      = false;
bool rightPeerAdded     = false;

esp_now_peer_info_t remotePeerInfo;
esp_now_peer_info_t leftPeerInfo;
esp_now_peer_info_t rightPeerInfo;

String serialBuffer = "";

unsigned long lastLeftResponseTime   = 0;
unsigned long lastRightResponseTime  = 0;
unsigned long lastRemoteResponseTime = 0;
const unsigned long PEER_TIMEOUT_MS  = 3000;

#ifndef LED_BUILTIN
#define LED_BUILTIN 15
#endif

unsigned long lastLedToggle = 0;
bool ledState = false;
int burstToggles = 0;

// ============================================================
// LED STATUS
// Solid ON  = no peers connected
// Slow blink (700ms) = partial connection
// Fast blink (250ms) = all peers connected
// ============================================================
void updateLed() {
  unsigned long now = millis();
  if (burstToggles > 0) {
    if (now - lastLedToggle >= 40) {
      lastLedToggle = now;
      ledState = !ledState;
      digitalWrite(LED_BUILTIN, ledState ? HIGH : LOW);
      burstToggles--;
    }
    return;
  }

  bool anySlaveConnected = (now - lastLeftResponseTime  < PEER_TIMEOUT_MS) ||
                           (now - lastRightResponseTime < PEER_TIMEOUT_MS);
  bool remoteConnected   = (now - lastRemoteResponseTime < PEER_TIMEOUT_MS);

  if (!anySlaveConnected && !remoteConnected) {
    digitalWrite(LED_BUILTIN, HIGH); // Solid = isolated
  } else if (anySlaveConnected && remoteConnected) {
    if (now - lastLedToggle >= 250) { lastLedToggle = now; ledState = !ledState;
      digitalWrite(LED_BUILTIN, ledState ? HIGH : LOW); }
  } else {
    if (now - lastLedToggle >= 700) { lastLedToggle = now; ledState = !ledState;
      digitalWrite(LED_BUILTIN, ledState ? HIGH : LOW); }
  }
}

// ============================================================
// FORWARD DECLARATIONS
// ============================================================
void initESPNow();
void sendCommandToSlaves(String command);
void handleCommand(String command);
void printMacAddress(const uint8_t* mac);

// ============================================================
// ESP-NOW SEND CALLBACK
// ============================================================
#if defined(ESP_IDF_VERSION_MAJOR) && (ESP_IDF_VERSION_MAJOR >= 5)
void onDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status) {
#else
void onDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
#endif
  if (status == ESP_NOW_SEND_SUCCESS) {
    if (strcmp(outCmd.text, "PING") != 0) burstToggles = 6;
  } else {
    if (strcmp(outCmd.text, "PING") != 0)
      Serial.println("[LINK FAIL] Delivery FAILED!");
  }
}

// ============================================================
// ESP-NOW RECEIVE CALLBACK
// ============================================================
#if defined(ESP_IDF_VERSION_MAJOR) && (ESP_IDF_VERSION_MAJOR >= 5)
void onDataRecv(const esp_now_recv_info *recvInfo, const uint8_t *incomingData, int len) {
  const uint8_t *srcMac = recvInfo->src_addr;
#else
void onDataRecv(const uint8_t *srcMac, const uint8_t *incomingData, int len) {
#endif

  bool isLeft   = srcMac && (memcmp(srcMac, LEFT_SLAVE_MAC,   6) == 0);
  bool isRight  = srcMac && (memcmp(srcMac, RIGHT_SLAVE_MAC,  6) == 0);
  bool isRemote = srcMac && (memcmp(srcMac, REMOTE_ESP32_MAC, 6) == 0);

  if (isLeft)   lastLeftResponseTime   = millis();
  if (isRight)  lastRightResponseTime  = millis();
  if (isRemote) lastRemoteResponseTime = millis();

  // ---- From Remote ESP32 -> forward command to slaves ----
  if (isRemote && len == sizeof(cmd_struct)) {
    cmd_struct incoming;
    memcpy(&incoming, incomingData, sizeof(incoming));
    if (strcmp(incoming.text, "PING") == 0) return;
    sendCommandToSlaves(String(incoming.text));
    Serial.printf("[RELAY->SLAVE] %s\n", incoming.text);
    return;
  }

  // ---- From a Slave -> relay telemetry to Remote ESP32 ----
  if ((isLeft || isRight) && len == sizeof(telemetry_struct)) {
    telemetry_struct telem;
    memcpy(&telem, incomingData, sizeof(telem));
    if (strcmp(telem.message, "PONG") == 0) return;

    const char* tag = isLeft ? "[LEFT]" : "[RIGHT]";

    // Relay to Remote ESP32
    if (remotePeerAdded) {
      telemetry_struct fwd;
      memset(&fwd, 0, sizeof(fwd));
      strncpy(fwd.type, telem.type, sizeof(fwd.type) - 1);
      if (strcmp(telem.type, "MPU") == 0) {
        snprintf(fwd.message, sizeof(fwd.message), "%s MPU_DATA %.2f %s",
                 tag, telem.pitch, telem.message);
      } else {
        snprintf(fwd.message, sizeof(fwd.message), "%s %s", tag, telem.message);
      }
      fwd.pitch = telem.pitch;
      esp_now_send(REMOTE_ESP32_MAC, (uint8_t*)&fwd, sizeof(fwd));
    }

    // Also print to Serial for RPi5 monitoring
    if (strcmp(telem.type, "MPU") == 0) {
      Serial.printf("%s MPU_DATA %.2f %s\n", tag, telem.pitch, telem.message);
    } else {
      Serial.printf("%s %s\n", tag, telem.message);
    }
    return;
  }
}

// ============================================================
// SEND COMMAND TO SLAVE(S) — L / R / B prefix routing
// ============================================================
void sendCommandToSlaves(String command) {
  if (!espnowInitialized) return;
  command.trim();
  char target = 'B';

  if      (command.startsWith("L ") || command.startsWith("L_")) { target = 'L'; command = command.substring(2); }
  else if (command.startsWith("R ") || command.startsWith("R_")) { target = 'R'; command = command.substring(2); }
  else if (command.startsWith("B ") || command.startsWith("B_") || command.startsWith("ALL ")) {
    target = 'B'; int sp = command.indexOf(' '); if (sp != -1) command = command.substring(sp + 1);
  }
  command.trim();

  memset(&outCmd, 0, sizeof(outCmd));
  strncpy(outCmd.text, command.c_str(), sizeof(outCmd.text) - 1);

  if ((target == 'L' || target == 'B') && leftPeerAdded)
    esp_now_send(LEFT_SLAVE_MAC,  (uint8_t*)&outCmd, sizeof(outCmd));
  if ((target == 'R' || target == 'B') && rightPeerAdded)
    esp_now_send(RIGHT_SLAVE_MAC, (uint8_t*)&outCmd, sizeof(outCmd));
}

// ============================================================
// HANDLE COMMAND (from Serial/RPi5 or Remote ESP32)
// ============================================================
void handleCommand(String command) {
  command.trim();
  if (command.equalsIgnoreCase("GET_MAC")) {
    unsigned long now = millis();
    Serial.println("\n--- SUB-MASTER STATUS ---");
    Serial.print("SUB_MASTER MAC:   "); printMacAddress(NULL);
    Serial.print("Remote ESP32 MAC: "); printMacAddress(REMOTE_ESP32_MAC);
    Serial.printf("  -> %s\n", (now - lastRemoteResponseTime < PEER_TIMEOUT_MS) ? "ONLINE" : "OFFLINE");
    Serial.print("Left Slave MAC:   "); printMacAddress(LEFT_SLAVE_MAC);
    Serial.printf("  -> %s\n", (now - lastLeftResponseTime  < PEER_TIMEOUT_MS) ? "ONLINE" : "OFFLINE");
    Serial.print("Right Slave MAC:  "); printMacAddress(RIGHT_SLAVE_MAC);
    Serial.printf("  -> %s\n", (now - lastRightResponseTime < PEER_TIMEOUT_MS) ? "ONLINE" : "OFFLINE");
    Serial.println("------------------------\n");
    return;
  }
  if (command.equalsIgnoreCase("HELP")) {
    Serial.println("\n=== SUB-MASTER COMMANDS ===");
    Serial.println("  L <cmd>              Send to Left Slave");
    Serial.println("  R <cmd>              Send to Right Slave");
    Serial.println("  B <cmd>              Send to Both Slaves");
    Serial.println("  NEO <r> <g> <b>      Set all 11 NeoPixels (0-255)");
    Serial.println("  NEO_BACK <r> <g> <b> Set 10 Backlight NeoPixels");
    Serial.println("  NEO_HEAD <r> <g> <b> Set 1 Head NeoPixel");
    Serial.println("  NEO_OFF              Turn off all NeoPixels");
    Serial.println("  NEO_BRT <0-255>      Set NeoPixel Brightness");
    Serial.println("  GET_MAC              Show MACs & status");
    Serial.println("  PING                 Heartbeat both slaves");
    Serial.println("===========================\n");
    return;
  }
  if (command.equalsIgnoreCase("PING")) {
    Serial.println("[SUB-MASTER] PONG");
    sendCommandToSlaves("B PING");
    return;
  }

  // --- NEOPIXEL LOCAL COMMANDS ---
  if (command.startsWith("NEO ") || command.startsWith("NEO_ALL ")) {
    uint8_t r = 0, g = 0, b = 0;
    String arg = command.substring(command.indexOf(' ') + 1);
    arg.trim();
    if (parseColor(arg, r, g, b)) {
      setAllNeoPixels(r, g, b);
      Serial.printf("[NEOPIXEL] All 11 LEDs set to R:%d G:%d B:%d\n", r, g, b);
    }
    return;
  }
  if (command.startsWith("NEO_BACK ")) {
    uint8_t r = 0, g = 0, b = 0;
    String arg = command.substring(command.indexOf(' ') + 1);
    arg.trim();
    if (parseColor(arg, r, g, b)) {
      setBacklightColor(r, g, b);
      Serial.printf("[NEOPIXEL] Backlight 10 LEDs set to R:%d G:%d B:%d\n", r, g, b);
    }
    return;
  }
  if (command.startsWith("NEO_HEAD ")) {
    uint8_t r = 0, g = 0, b = 0;
    String arg = command.substring(command.indexOf(' ') + 1);
    arg.trim();
    if (parseColor(arg, r, g, b)) {
      setHeadColor(r, g, b);
      Serial.printf("[NEOPIXEL] Head LED set to R:%d G:%d B:%d\n", r, g, b);
    }
    return;
  }
  if (command.equalsIgnoreCase("NEO_OFF")) {
    setAllNeoPixels(0, 0, 0);
    Serial.println("[NEOPIXEL] All LEDs turned OFF");
    return;
  }
  if (command.startsWith("NEO_BRT ")) {
    int brt = 180;
    if (sscanf(command.c_str() + 8, "%d", &brt) == 1) {
      strip.setBrightness(constrain(brt, 0, 255));
      strip.show();
      Serial.printf("[NEOPIXEL] Brightness set to %d\n", brt);
    }
    return;
  }

  sendCommandToSlaves(command);
}

// ============================================================
// ESP-NOW INIT
// ============================================================
void initESPNow() {
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  if (esp_now_init() != ESP_OK) { Serial.println("ERROR: ESP-NOW init failed!"); return; }
  espnowInitialized = true;
  Serial.println("ESP-NOW initialized");
  esp_now_register_send_cb(onDataSent);
  esp_now_register_recv_cb(onDataRecv);

  // Add Remote ESP32 peer (if MAC is set)
  bool remoteIsSet = false;
  for (int i = 0; i < 6; i++) { if (REMOTE_ESP32_MAC[i] != 0xFF) { remoteIsSet = true; break; } }
  if (remoteIsSet) {
    memset(&remotePeerInfo, 0, sizeof(remotePeerInfo));
    memcpy(remotePeerInfo.peer_addr, REMOTE_ESP32_MAC, 6);
    remotePeerInfo.channel = 0;
    remotePeerInfo.encrypt = false;
    esp_err_t err = esp_now_add_peer(&remotePeerInfo);
    if (err == ESP_OK || err == ESP_ERR_ESPNOW_EXIST) {
      remotePeerAdded = true;
      Serial.println("Remote ESP32 peer added");
    } else {
      Serial.printf("WARNING: Failed to add Remote ESP32 peer (Error: 0x%X)\n", err);
    }
  } else {
    Serial.println("WARNING: REMOTE_ESP32_MAC not set - telemetry relay to Remote ESP32 disabled.");
  }

  // Add Left Slave
  memset(&leftPeerInfo, 0, sizeof(leftPeerInfo));
  memcpy(leftPeerInfo.peer_addr, LEFT_SLAVE_MAC, 6);
  leftPeerInfo.channel = 0;
  leftPeerInfo.encrypt = false;
  esp_err_t errL = esp_now_add_peer(&leftPeerInfo);
  if (errL == ESP_OK || errL == ESP_ERR_ESPNOW_EXIST) {
    leftPeerAdded = true;
    Serial.println("Left Slave peer added");
  } else {
    Serial.printf("WARNING: Failed to add Left Slave peer (Error: 0x%X)\n", errL);
  }

  // Add Right Slave
  memset(&rightPeerInfo, 0, sizeof(rightPeerInfo));
  memcpy(rightPeerInfo.peer_addr, RIGHT_SLAVE_MAC, 6);
  rightPeerInfo.channel = 0;
  rightPeerInfo.encrypt = false;
  esp_err_t errR = esp_now_add_peer(&rightPeerInfo);
  if (errR == ESP_OK || errR == ESP_ERR_ESPNOW_EXIST) {
    rightPeerAdded = true;
    Serial.println("Right Slave peer added");
  } else {
    Serial.printf("WARNING: Failed to add Right Slave peer (Error: 0x%X)\n", errR);
  }
}

// ============================================================
// SETUP
// ============================================================
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Serial.begin(115200);
#if defined(ARDUINO_USB_CDC_ON_BOOT) && (ARDUINO_USB_CDC_ON_BOOT == 1)
  Serial.setTxTimeoutMs(0);
#endif
  delay(500);

  Serial.println("\n\n========================================");
  Serial.println("  M_ESP32_SUB_MASTER - Rollopod Onboard ");
  Serial.println("========================================");
  setupAntenna();

  // Initialize 11 NeoPixels on D10 / GPIO 18 (Sets RED)
  initNeoPixels();

  initESPNow();

  Serial.print("\n*** SUB_MASTER MAC: ");
  printMacAddress(NULL);
  Serial.println("*** Copy this MAC into Remote ESP32 sketch as SUB_MASTER_MAC ***\n");
  Serial.println("Ready. Accepts commands from RPi5 Serial and Remote ESP32 (ESP-NOW).");
  Serial.println("Type HELP for command list.\n");
}

// ============================================================
// LOOP
// ============================================================
void loop() {
  // Serial input from RPi5 or PC
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      serialBuffer.trim();
      if (serialBuffer.length() > 0) {
        Serial.printf("[RPi5 CMD] %s\n", serialBuffer.c_str());
        handleCommand(serialBuffer);
        serialBuffer = "";
      }
    } else {
      serialBuffer += c;
    }
  }

  // 2Hz heartbeat to both slaves
  static unsigned long lastHeartbeat = 0;
  if (millis() - lastHeartbeat >= 500) {
    lastHeartbeat = millis();
    if (espnowInitialized) {
      memset(&outCmd, 0, sizeof(outCmd));
      strncpy(outCmd.text, "PING", sizeof(outCmd.text) - 1);
      if (leftPeerAdded)  esp_now_send(LEFT_SLAVE_MAC,  (uint8_t*)&outCmd, sizeof(outCmd));
      if (rightPeerAdded) esp_now_send(RIGHT_SLAVE_MAC, (uint8_t*)&outCmd, sizeof(outCmd));
    }
  }

  updateLed();
}

// ============================================================
// UTILITY
// ============================================================
void printMacAddress(const uint8_t* mac) {
  if (mac == NULL) {
    uint8_t baseMac[6];
    if (esp_wifi_get_mac(WIFI_IF_STA, baseMac) == ESP_OK) {
      Serial.printf("%02X:%02X:%02X:%02X:%02X:%02X\n",
                    baseMac[0], baseMac[1], baseMac[2],
                    baseMac[3], baseMac[4], baseMac[5]);
    }
  } else {
    Serial.printf("%02X:%02X:%02X:%02X:%02X:%02X\n",
                  mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  }
}

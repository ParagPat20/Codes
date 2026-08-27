/*
 * Remote ESP32 — Serial-to-ESP-NOW Bridge (stays near RPi5 or Laptop)
 *
 * NEW ARCHITECTURE (3-tier):
 *   Python GUI / RPi5
 *     ↕ USB Serial
 *   [ This board — Remote ESP32 ]
 *     ↕ ESP-NOW (wireless)
 *   [ M_ESP32_SUB_MASTER — inside robot ]
 *     ↕ ESP-NOW
 *   [ L_ESP32_SLAVE ]  [ R_ESP32_SLAVE ]
 *
 * This board is now a THIN RELAY — it only talks to SUB_MASTER.
 * All L/R slave routing is handled by SUB_MASTER.
 * The Python GUI is UNCHANGED — same Serial command format as before.
 *
 * Setup:
 *   1. Flash M_ESP32_SUB_MASTER first, get its MAC from Serial Monitor
 *   2. Set SUB_MASTER_MAC below to that MAC
 *   3. Flash this sketch to the Remote ESP32 (near laptop/RPi5)
 */

#include <esp_idf_version.h>
#include <esp_now.h>
#include <WiFi.h>
#include <esp_wifi.h>

void setupAntenna() {
#if defined(CONFIG_IDF_TARGET_ESP32C6) || defined(ARDUINO_SEEED_XIAO_ESP32C6) || defined(ESP32C6)
  pinMode(3, OUTPUT);  digitalWrite(3, LOW);  delay(100);
  pinMode(14, OUTPUT); digitalWrite(14, LOW);
  Serial.println("[ANTENNA] XIAO ESP32-C6: Internal PCB Antenna (GPIO3=LOW, GPIO14=LOW)");
#else
  Serial.println("[ANTENNA] Standard ESP32 DevKit Board");
#endif
}

// ============================================================
// SUB-MASTER MAC ADDRESS (M_ESP32_SUB_MASTER: 10:BD:A3:9E:E1:40)
// ============================================================
uint8_t SUB_MASTER_MAC[] = { 0x10, 0xBD, 0xA3, 0x9E, 0xE1, 0x40 };

// ============================================================
// DATA STRUCTURES (must match Sub-Master and Slaves exactly)
// ============================================================
typedef struct cmd_struct {
  char text[128];
} cmd_struct;

typedef struct telemetry_struct {
  char type[10];
  char message[128];
  float pitch;
} telemetry_struct;

cmd_struct       myCmd;
telemetry_struct myData;

String serialBuffer   = "";
bool espnowInitialized = false;
bool subMasterPeerAdded = false;
esp_now_peer_info_t subMasterPeerInfo;

unsigned long lastSubMasterResponseTime = 0;
const unsigned long PEER_TIMEOUT_MS = 3000;

#ifndef LED_BUILTIN
#define LED_BUILTIN 15
#endif

unsigned long lastLedToggle = 0;
bool ledState = false;
int burstToggles = 0;
unsigned long failPauseEnd = 0;

void updateLed() {
  unsigned long now = millis();
  if (now < failPauseEnd) { digitalWrite(LED_BUILTIN, LOW); return; }
  if (burstToggles > 0) {
    if (now - lastLedToggle >= 40) {
      lastLedToggle = now; ledState = !ledState;
      digitalWrite(LED_BUILTIN, ledState ? HIGH : LOW);
      burstToggles--;
    }
    return;
  }
  bool connected = (now - lastSubMasterResponseTime < PEER_TIMEOUT_MS);
  if (!connected) {
    digitalWrite(LED_BUILTIN, HIGH); // Solid = no Sub-Master
  } else {
    if (now - lastLedToggle >= 500) {
      lastLedToggle = now; ledState = !ledState;
      digitalWrite(LED_BUILTIN, ledState ? HIGH : LOW);
    }
  }
}

void initESPNow();
void printMacAddress(const uint8_t *mac);

#if defined(ESP_IDF_VERSION_MAJOR) && (ESP_IDF_VERSION_MAJOR >= 5)
void onDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status) {
#else
void onDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
#endif
  if (status == ESP_NOW_SEND_SUCCESS) {
    if (strcmp(myCmd.text, "PING") != 0) burstToggles = 8;
  } else {
    if (strcmp(myCmd.text, "PING") != 0) {
      failPauseEnd = millis() + 350;
      Serial.println("[LINK FAIL] Sub-Master not reachable!");
    }
  }
}

#if defined(ESP_IDF_VERSION_MAJOR) && (ESP_IDF_VERSION_MAJOR >= 5)
void onDataRecv(const esp_now_recv_info *recvInfo, const uint8_t *incomingData, int len) {
  const uint8_t *srcMac = recvInfo->src_addr;
#else
void onDataRecv(const uint8_t *srcMac, const uint8_t *incomingData, int len) {
#endif
  bool isSubMaster = srcMac && (memcmp(srcMac, SUB_MASTER_MAC, 6) == 0);
  if (isSubMaster) lastSubMasterResponseTime = millis();

  if (len == sizeof(telemetry_struct)) {
    memcpy(&myData, incomingData, sizeof(myData));
    if (strcmp(myData.message, "PONG") == 0) return;

    // Sub-Master pre-pends [LEFT]/[RIGHT] tag into message — just print it
    if (strcmp(myData.type, "MPU") == 0) {
      // message field already contains the full formatted string from Sub-Master
      Serial.printf("%s\n", myData.message);
    } else {
      Serial.printf("%s\n", myData.message);
    }
  }
}

void initESPNow() {
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  if (esp_now_init() != ESP_OK) { Serial.println("ERROR: ESP-NOW init failed!"); return; }
  espnowInitialized = true;
  Serial.println("ESP-NOW initialized");
  esp_now_register_send_cb(onDataSent);
  esp_now_register_recv_cb(onDataRecv);

  bool subMasterIsSet = false;
  for (int i = 0; i < 6; i++) { if (SUB_MASTER_MAC[i] != 0xFF) { subMasterIsSet = true; break; } }
  if (!subMasterIsSet) {
    Serial.println("WARNING: SUB_MASTER_MAC not set!");
    Serial.println("         Flash M_ESP32_SUB_MASTER first, run GET_MAC, then set MAC here.");
    return;
  }

  memset(&subMasterPeerInfo, 0, sizeof(subMasterPeerInfo));
  memcpy(subMasterPeerInfo.peer_addr, SUB_MASTER_MAC, 6);
  subMasterPeerInfo.encrypt = false;
  if (esp_now_add_peer(&subMasterPeerInfo) == ESP_OK) {
    subMasterPeerAdded = true;
    Serial.println("Sub-Master peer added");
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Serial.begin(115200);
#if defined(ARDUINO_USB_CDC_ON_BOOT) && (ARDUINO_USB_CDC_ON_BOOT == 1)
  Serial.setTxTimeoutMs(0);
#endif
  delay(500);

  Serial.println("\n\n========================================");
  Serial.println("  Remote ESP32 — Serial/ESP-NOW Relay   ");
  Serial.println("  (Talks to M_ESP32_SUB_MASTER only)    ");
  Serial.println("========================================");
  setupAntenna();
  initESPNow();

  Serial.print("\nRemote ESP32 MAC: "); printMacAddress(NULL);
  Serial.print("Sub-Master  MAC:  "); printMacAddress(SUB_MASTER_MAC);
  Serial.println("\nReady. Same commands as before — L/R/B prefix routing handled by Sub-Master.");
  Serial.println("Type GET_MAC for status, HELP for commands.\n");
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      serialBuffer.trim();
      if (serialBuffer.length() > 0) {
        if (serialBuffer.equalsIgnoreCase("GET_MAC")) {
          unsigned long now = millis();
          Serial.print("Remote ESP32 MAC: "); printMacAddress(NULL);
          Serial.print("Sub-Master  MAC:  "); printMacAddress(SUB_MASTER_MAC);
          Serial.printf("  -> %s\n", (now - lastSubMasterResponseTime < PEER_TIMEOUT_MS) ? "ONLINE" : "OFFLINE");
        } else if (serialBuffer.equalsIgnoreCase("HELP")) {
          Serial.println("\n=== REMOTE ESP32 RELAY COMMANDS ===");
          Serial.println("  L <cmd>   -> Sub-Master -> Left Slave");
          Serial.println("  R <cmd>   -> Sub-Master -> Right Slave");
          Serial.println("  B <cmd>   -> Sub-Master -> Both Slaves");
          Serial.println("  GET_MAC   Show status");
          Serial.println("  PING      Heartbeat");
          Serial.println("===================================\n");
        } else if (serialBuffer.equalsIgnoreCase("PING")) {
          Serial.println("Remote ESP32 OK — relaying PING to Sub-Master...");
          memset(&myCmd, 0, sizeof(myCmd));
          strncpy(myCmd.text, "B PING", sizeof(myCmd.text) - 1);
          if (subMasterPeerAdded) esp_now_send(SUB_MASTER_MAC, (uint8_t*)&myCmd, sizeof(myCmd));
        } else {
          // Forward command to Sub-Master as-is (it handles L/R/B routing)
          memset(&myCmd, 0, sizeof(myCmd));
          strncpy(myCmd.text, serialBuffer.c_str(), sizeof(myCmd.text) - 1);
          if (subMasterPeerAdded) {
            esp_now_send(SUB_MASTER_MAC, (uint8_t*)&myCmd, sizeof(myCmd));
          } else {
            Serial.println("ERROR: Sub-Master not configured. Set SUB_MASTER_MAC and reflash.");
          }
        }
        serialBuffer = "";
      }
    } else {
      serialBuffer += c;
    }
  }

  // 2Hz heartbeat PING to Sub-Master
  static unsigned long lastHeartbeat = 0;
  if (millis() - lastHeartbeat >= 500) {
    lastHeartbeat = millis();
    if (espnowInitialized && subMasterPeerAdded) {
      memset(&myCmd, 0, sizeof(myCmd));
      strncpy(myCmd.text, "PING", sizeof(myCmd.text) - 1);
      esp_now_send(SUB_MASTER_MAC, (uint8_t*)&myCmd, sizeof(myCmd));
    }
  }

  updateLed();
}

void printMacAddress(const uint8_t *mac) {
  if (mac == NULL) {
    uint8_t baseMac[6];
    if (esp_wifi_get_mac(WIFI_IF_STA, baseMac) == ESP_OK) {
      Serial.printf("%02X:%02X:%02X:%02X:%02X:%02X\n",
                    baseMac[0], baseMac[1], baseMac[2],
                    baseMac[3], baseMac[4], baseMac[5]);
    } else { Serial.println(WiFi.macAddress()); }
  } else {
    Serial.printf("%02X:%02X:%02X:%02X:%02X:%02X\n",
                  mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  }
}


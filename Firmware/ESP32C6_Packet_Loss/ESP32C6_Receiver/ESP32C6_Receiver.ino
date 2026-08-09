/*
  ===============================================================================
  ESP32-C6 ESP-NOW PACKET LOSS TRACER - RECEIVER (TARGET)
  Target Board: Seeed Studio XIAO ESP32-C6
  Environment: Arduino IDE (ESP32 Board Package v3.x+)
  ===============================================================================

  Antenna Control Notes (Seeed XIAO ESP32-C6):
  - GPIO 3: Enable control pin (Must be set LOW to activate RF antenna switching)
  - GPIO 14: Antenna Selection pin
      - LOW  = Built-in / Internal PCB Antenna (Default)
      - HIGH = External Antenna (U.FL connector)
  ===============================================================================
*/

#include <esp_idf_version.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>


// Antenna Selection: false = Internal Built-in Antenna, true = External Antenna
bool useExternalAntenna = false;

#define PAYLOAD_SIZE 180

// High-Stress Packet Structure with Wireless Relay Telemetry (233 bytes total)
typedef struct __attribute__((packed)) {
  uint32_t magic;             // Header signature (0x4553504E = 'ESPN')
  uint32_t sequence;          // Packet index
  uint32_t sendTimestamp;     // millis() at transmission time
  uint8_t  isEcho;            // 0 = Normal packet, 1 = Echo response
  char     senderMac[18];     // Sender MAC address
  uint16_t payloadLen;        // Length of heavy string payload
  uint32_t checksum;          // Payload integrity checksum

  // Wireless Telemetry Relay Fields (Receiver populates in Echo response)
  uint32_t rxPacketsReceived; // Receiver total received count
  uint32_t rxPacketsLost;     // Receiver total lost count
  float    rxLossRate;        // Receiver loss rate %
  uint32_t rxCorrupted;       // Receiver corrupted count

  char     payload[PAYLOAD_SIZE]; // 180-byte heavy test payload
} PacketData;

#define MAGIC_SIGNATURE 0x4553504E

// Checksum calculation for data integrity verification
uint32_t calculateChecksum(const char *data, uint16_t len) {
  uint32_t hash = 5381;
  for (uint16_t i = 0; i < len; i++) {
    hash = ((hash << 5) + hash) + (uint8_t)data[i];
  }
  return hash;
}

// Telemetry Statistics
struct Statistics {
  uint32_t packetsReceived = 0;
  uint32_t lastReceivedSeq = 0;
  uint32_t packetsLost = 0;
  uint32_t outOfOrder = 0;
  uint32_t corruptedPackets = 0;
  bool     firstPacketReceived = false;
  int      lastRssi = 0;
} stats;

uint32_t lastReportTime = 0;

// Antenna Setup (Auto-detects XIAO ESP32-C6 vs Standard ESP32 DevKit)
void setupAntenna(bool useExternal) {
#if defined(CONFIG_IDF_TARGET_ESP32C6) || defined(ARDUINO_SEEED_XIAO_ESP32C6) || defined(ESP32C6)
  pinMode(3, OUTPUT);
  digitalWrite(3, LOW); // Enable antenna selection circuit on XIAO C6
  delay(100);

  pinMode(14, OUTPUT);
  digitalWrite(14, useExternal ? HIGH : LOW); // LOW = Built-in, HIGH = External

  useExternalAntenna = useExternal;

  Serial.println("--------------------------------------------------");
  if (useExternal) {
    Serial.println("[ANTENNA] XIAO C6: EXTERNAL Antenna (GPIO3=LOW, GPIO14=HIGH)");
  } else {
    Serial.println("[ANTENNA] XIAO C6: BUILT-IN Internal Antenna (GPIO3=LOW, GPIO14=LOW)");
  }
  Serial.println("--------------------------------------------------");
#else
  Serial.println("--------------------------------------------------");
  Serial.println("[ANTENNA] Standard ESP32 DevKit Board (Built-in PCB Antenna)");
  Serial.println("--------------------------------------------------");
#endif
}

// ESP-NOW Receive Callback
#if defined(ESP_IDF_VERSION_MAJOR) && (ESP_IDF_VERSION_MAJOR >= 5)
void OnDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *incomingData, int len) {
  int currentRssi = recv_info->rx_ctrl->rssi;
  const uint8_t *srcMac = recv_info->src_addr;
#else
void OnDataRecv(const uint8_t *srcMac, const uint8_t *incomingData, int len) {
  int currentRssi = 0;
#endif

  if (len != sizeof(PacketData)) return;

  PacketData packet;
  memcpy(&packet, incomingData, sizeof(packet));

  if (packet.magic != MAGIC_SIGNATURE || packet.isEcho) return;

  stats.packetsReceived++;
  stats.lastRssi = currentRssi;

  // Packet loss gap calculation using sequence numbers
  if (!stats.firstPacketReceived) {
    stats.firstPacketReceived = true;
    stats.lastReceivedSeq = packet.sequence;
  } else {
    if (packet.sequence > stats.lastReceivedSeq + 1) {
      uint32_t gap = packet.sequence - (stats.lastReceivedSeq + 1);
      stats.packetsLost += gap;
    } else if (packet.sequence <= stats.lastReceivedSeq) {
      stats.outOfOrder++;
    }
    stats.lastReceivedSeq = packet.sequence;
  }

  // Verify payload string integrity via checksum
  uint32_t computedChecksum = calculateChecksum(packet.payload, packet.payloadLen);
  if (computedChecksum != packet.checksum) {
    stats.corruptedPackets++;
  }

  uint32_t totalExpected = stats.packetsReceived + stats.packetsLost;
  float lossRate = totalExpected ? ((float)stats.packetsLost / totalExpected) * 100.0 : 0.0;

  // High-speed stream output for Python UI (100Hz)
  Serial.printf("$DAT,RECV,%u,%d,%u,%u,%.2f,%u\n", 
                packet.sequence, currentRssi, stats.packetsReceived, stats.packetsLost, lossRate, stats.corruptedPackets);

  // Echo packet back to Sender so Sender can measure RTT latency, RSSI & Receiver stats
  packet.isEcho = 1;
  packet.rxPacketsReceived = stats.packetsReceived;
  packet.rxPacketsLost = stats.packetsLost;
  packet.rxLossRate = lossRate;
  packet.rxCorrupted = stats.corruptedPackets;

  // Auto-add sender as peer if not already in peer list
  if (!esp_now_is_peer_exist(srcMac)) {
    esp_now_peer_info_t peerInfo = {};
    memcpy(peerInfo.peer_addr, srcMac, 6);
    peerInfo.channel = 0;
    peerInfo.encrypt = false;
    esp_now_add_peer(&peerInfo);
  }

  esp_now_send(srcMac, (uint8_t *)&packet, sizeof(packet));
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  Serial.println("\n==================================================");
  Serial.println("    ESP32-C6 ESP-NOW PACKET LOSS TRACER (RECEIVER)");
  Serial.println("==================================================");

  // 1. Initialize Built-in Internal Antenna
  setupAntenna(useExternalAntenna);

  // 2. WiFi Station Mode
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  Serial.print("[WIFI] Receiver MAC Address: ");
  Serial.println(WiFi.macAddress());

  // Set maximum WiFi transmit power for reply echo (21dBm)
  esp_wifi_set_max_tx_power(84);

  // 3. Initialize ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("[ERROR] ESP-NOW Init Failed!");
    return;
  }
  Serial.println("[ESP-NOW] Initialized.");

  esp_now_register_recv_cb(OnDataRecv);

  printMenu();
}

void printDashboard() {
  Serial.println("\n----------------- [RECEIVER TELEMETRY REPORT] -----------------");
  Serial.print(" Total Received:  "); Serial.println(stats.packetsReceived);
  Serial.print(" Estimated Lost:  "); Serial.println(stats.packetsLost);
  
  uint32_t totalExpected = stats.packetsReceived + stats.packetsLost;
  float lossRate = totalExpected ? ((float)stats.packetsLost / totalExpected) * 100.0 : 0.0;
  
  Serial.print(" Packet Loss Rate: "); Serial.print(lossRate, 2); Serial.println(" %");
  Serial.print(" Out of Order/Dup: "); Serial.println(stats.outOfOrder);
  Serial.print(" Signal RSSI:     "); Serial.print(stats.lastRssi); Serial.println(" dBm");
  Serial.print(" Active Antenna:  "); Serial.println(useExternalAntenna ? "EXTERNAL (GPIO14=HIGH)" : "BUILT-IN / INTERNAL (GPIO14=LOW)");
  Serial.println("----------------------------------------------------------------");
}

void printMenu() {
  Serial.println("\n--- Receiver Remote Controls ---");
  Serial.println("  'x' : Reboot ESP32 Hardware");
  Serial.println("  'a' : Toggle Antenna (Built-in Internal <-> External)");
  Serial.println("  'r' : Reset Statistics");
  Serial.println("--------------------------------\n");
}

void handleSerialInput() {
  if (!Serial.available()) return;
  char c = Serial.read();
  switch (c) {
    case 'x': case 'X': 
      Serial.println("[STATE] REBOOTING_ESP32"); 
      delay(100); 
      ESP.restart(); 
      break;
    case 'a': case 'A': setupAntenna(!useExternalAntenna); break;
    case 'r': case 'R': memset(&stats, 0, sizeof(stats)); Serial.println("[INFO] Stats Reset."); break;
    case 'h': case 'H': printMenu(); break;
  }
}

void loop() {
  uint32_t currentMillis = millis();

  if (currentMillis - lastReportTime >= 1000) {
    lastReportTime = currentMillis;
    printDashboard();
  }

  handleSerialInput();
}

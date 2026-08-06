/*
  ===============================================================================
  ESP32-C6 ESP-NOW Packet Loss Tracer
  Target Board: Seeed Studio XIAO ESP32-C6 (or similar ESP32-C6 modules)
  Environment: Arduino IDE (ESP32 Board Package v3.x+)
  ===============================================================================

  Antenna Control Notes (Seeed XIAO ESP32-C6):
  - GPIO 3: Enable control pin (Must be set LOW to activate RF antenna switching)
  - GPIO 14: Antenna Selection pin
      - LOW  = Built-in / Internal PCB Antenna (Default)
      - HIGH = External Antenna (U.FL connector)

  Features:
  1. Internal / External Antenna Switching setup via GPIO3 & GPIO14.
  2. Dual Mode Support: Configurable as SENDER (Transmitter) or RECEIVER (Target).
  3. Real-time Packet Loss Tracking (Total Sent, Received, Lost, Loss %, RSSI, RTT).
  4. Sequence Number Gap Analysis for detecting dropped/out-of-order packets.
  5. Interactive Serial Console for toggling antenna mode, changing packet rates, and resetting stats.
  ===============================================================================
*/

#include <esp_idf_version.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

// ===============================================================================
// CONFIGURATION & MODES
// ===============================================================================
#define MODE_SENDER   1
#define MODE_RECEIVER 2

// Choose Device Mode here (MODE_SENDER or MODE_RECEIVER)
// Tip: Program one ESP32-C6 as MODE_SENDER and another as MODE_RECEIVER!
#ifndef DEVICE_MODE
#define DEVICE_MODE MODE_RECEIVER
#endif

// Antenna Selection: false = Internal Built-in Antenna, true = External Antenna
bool useExternalAntenna = false; 

// Packet Transmit Interval (ms) for Sender Mode
uint32_t sendIntervalMs = 100; // 10 packets per second by default

// Broadcast MAC Address (Sends to all listening devices)
uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

// ===============================================================================
// PACKET STRUCTURE
// ===============================================================================
#define PAYLOAD_SIZE 180

// High-Stress Packet Structure with Wireless Relay Telemetry (233 bytes total)
typedef struct __attribute__((packed)) {
  uint32_t magic;             // Header signature (0x4553504E = 'ESPN')
  uint32_t sequence;          // Incrementing packet index
  uint32_t sendTimestamp;     // millis() at transmission time
  uint8_t  isEcho;            // 0 = Normal packet, 1 = Echo/ACK response
  char     senderMac[18];     // Formatted String MAC of sender
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

// Generate a long dense string filled with sequential numbers & patterns
const char STRESS_PATTERN[] = "0123456789_ESP32C6_HIGH_STRESS_PACKET_LOSS_TRACER_PAYLOAD_890123456789_ABCDEFGHIJKLMNOPQRSTUVWXYZ_";

void generateLongStringPayload(char *buffer, uint16_t size, uint32_t seq) {
  int offset = snprintf(buffer, size, "PKT#%u-NUMS:0123456789876543210-DATA:", seq);
  if (offset < 0) offset = 0;
  
  while ((uint16_t)offset < size - 1) {
    uint16_t copyLen = sizeof(STRESS_PATTERN) - 1;
    if (offset + copyLen >= size - 1) {
      copyLen = (size - 1) - offset;
    }
    memcpy(buffer + offset, STRESS_PATTERN, copyLen);
    offset += copyLen;
  }
  buffer[size - 1] = '\0';
}

// ===============================================================================
// STATISTICS & TELEMETRY TRACKER
// ===============================================================================
struct Statistics {
  uint32_t packetsSent = 0;
  uint32_t sendSuccess = 0;
  uint32_t sendFail = 0;
  
  uint32_t packetsReceived = 0;
  uint32_t lastReceivedSeq = 0;
  uint32_t packetsLost = 0;
  uint32_t outOfOrder = 0;
  bool     firstPacketReceived = false;

  int      lastRssi = 0;
  uint32_t lastRttMs = 0;
  uint32_t avgRttMs = 0;
  uint32_t rttSampleCount = 0;
} stats;

uint32_t lastSendTime = 0;
uint32_t lastReportTime = 0;

// ===============================================================================
// HARDWARE INITIALIZATION: ANTENNA SELECTION
// ===============================================================================
void setupAntenna(bool useExternal) {
  // Step 1: Set GPIO3 LOW level to turn on antenna selection function
  pinMode(3, OUTPUT);
  digitalWrite(3, LOW); 
  delay(100);

  // Step 2: Set GPIO14 level to select antenna
  // LOW = Built-in Internal Antenna, HIGH = External Antenna
  pinMode(14, OUTPUT);
  digitalWrite(14, useExternal ? HIGH : LOW);

  useExternalAntenna = useExternal;

  Serial.println("--------------------------------------------------");
  if (useExternal) {
    Serial.println("[ANTENNA] Configured: EXTERNAL Antenna (GPIO3=LOW, GPIO14=HIGH)");
  } else {
    Serial.println("[ANTENNA] Configured: BUILT-IN Internal Antenna (GPIO3=LOW, GPIO14=LOW)");
  }
  Serial.println("--------------------------------------------------");
}

// ===============================================================================
// ESP-NOW CALLBACKS
// ===============================================================================

// Delivery Status Callback (Triggers when ESP-NOW packet is transmitted)
#if defined(ESP_IDF_VERSION_MAJOR) && (ESP_IDF_VERSION_MAJOR >= 5)
void OnDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
#else
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
#endif
  if (status == ESP_NOW_SEND_SUCCESS) {
    stats.sendSuccess++;
  } else {
    stats.sendFail++;
  }
}

// Data Receive Callback (Handles incoming ESP-NOW packets)
#if defined(ESP_IDF_VERSION_MAJOR) && ESP_IDF_VERSION_MAJOR >= 5
void OnDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *incomingData, int len) {
  int currentRssi = recv_info->rx_ctrl->rssi;
  const uint8_t *srcMac = recv_info->src_addr;
#else
void OnDataRecv(const uint8_t *srcMac, const uint8_t *incomingData, int len) {
  int currentRssi = 0; // Not available directly in older IDF callback struct
#endif

  if (len != sizeof(PacketData)) {
    return; // Ignore incompatible packets
  }

  PacketData packet;
  memcpy(&packet, incomingData, sizeof(packet));

  if (packet.magic != MAGIC_SIGNATURE) {
    return; // Invalid signature
  }

  uint32_t now = millis();

  // If this is an Echo/ACK reply received by SENDER
  if (packet.isEcho) {
    uint32_t rtt = now - packet.sendTimestamp;
    stats.lastRttMs = rtt;
    stats.rttSampleCount++;
    stats.avgRttMs = ((stats.avgRttMs * (stats.rttSampleCount - 1)) + rtt) / stats.rttSampleCount;
    stats.lastRssi = currentRssi;

    // Stream wireless Receiver telemetry received over ESP-NOW Echo response!
    Serial.printf("$DAT,RECV,%u,%d,%u,%u,%.2f,%u\n", 
                  packet.sequence, currentRssi, packet.rxPacketsReceived, packet.rxPacketsLost, packet.rxLossRate, packet.rxCorrupted);
    return;
  }

  // RECEIVER Mode Processing
  stats.packetsReceived++;
  stats.lastRssi = currentRssi;

  if (!stats.firstPacketReceived) {
    stats.firstPacketReceived = true;
    stats.lastReceivedSeq = packet.sequence;
  } else {
    if (packet.sequence > stats.lastReceivedSeq + 1) {
      // Missing sequence gap detected
      uint32_t gap = packet.sequence - (stats.lastReceivedSeq + 1);
      stats.packetsLost += gap;
    } else if (packet.sequence <= stats.lastReceivedSeq) {
      // Out of order or duplicate packet
      stats.outOfOrder++;
    }
    stats.lastReceivedSeq = packet.sequence;
  }

  uint32_t totalExpected = stats.packetsReceived + stats.packetsLost;
  float lossRate = totalExpected ? ((float)stats.packetsLost / totalExpected) * 100.0 : 0.0;

  // Echo packet back to sender with embedded Receiver telemetry
  packet.isEcho = 1;
  packet.rxPacketsReceived = stats.packetsReceived;
  packet.rxPacketsLost = stats.packetsLost;
  packet.rxLossRate = lossRate;
  packet.rxCorrupted = stats.corruptedPackets;
  
  // ESP-NOW requires the target MAC to be registered as a peer before sending
  if (!esp_now_is_peer_exist(srcMac)) {
    esp_now_peer_info_t peerInfo = {};
    memcpy(peerInfo.peer_addr, srcMac, 6);
    peerInfo.channel = 0;
    peerInfo.encrypt = false;
    esp_now_add_peer(&peerInfo);
  }
  
  esp_now_send(srcMac, (uint8_t *)&packet, sizeof(packet));
}

// ===============================================================================
// SETUP FUNCTION
// ===============================================================================
void setup() {
  Serial.begin(115200);
  delay(1500); // Allow time for Serial monitor connection

  Serial.println("\n==================================================");
  Serial.println("    ESP32-C6 ESP-NOW PACKET LOSS TRACER          ");
  Serial.println("==================================================");

  // 1. Initialize RF Antenna Switch (Internal RF by Default)
  setupAntenna(useExternalAntenna);

  // 2. Set WiFi to Station mode and get MAC address
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  Serial.print("[WIFI] Device MAC Address: ");
  Serial.println(WiFi.macAddress());

  // Set maximum WiFi transmit power for best range analysis
  esp_wifi_set_max_tx_power(84); // 84 = 21dBm (Max output power)

  // 3. Initialize ESP-NOW Protocol
  if (esp_now_init() != ESP_OK) {
    Serial.println("[ERROR] ESP-NOW Initialization Failed!");
    return;
  }
  Serial.println("[ESP-NOW] Initialized Successfully.");

  // 4. Register Callbacks
  esp_now_register_send_cb(OnDataSent);
  esp_now_register_recv_cb(OnDataRecv);

  // 5. Register Broadcast Peer
  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, broadcastAddress, 6);
  peerInfo.channel = 0; // Match current channel
  peerInfo.encrypt = false;

  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("[ESP-NOW] Warning: Failed to add broadcast peer.");
  } else {
    Serial.println("[ESP-NOW] Broadcast Peer Added Successfully.");
  }

  printMenu();
}

uint32_t sendIntervalMicros = 10000; // Default 100 Hz (10,000 us)
uint32_t currentFrequencyHz = 100;
uint32_t lastSendMicros = 0;
bool isTransmitting = true;

void setFrequencyHz(uint32_t hz) {
  if (hz == 0) return;
  currentFrequencyHz = hz;
  sendIntervalMicros = 1000000UL / hz;
  Serial.printf("[CONFIG] Frequency set to %u Hz (%u us interval)\n", hz, sendIntervalMicros);
}

// ===============================================================================
// LOOP FUNCTION
// ===============================================================================
void loop() {
  uint32_t currentMicros = micros();

#if (DEVICE_MODE == MODE_SENDER)
  if (isTransmitting && (currentMicros - lastSendMicros >= sendIntervalMicros)) {
    lastSendMicros = currentMicros;
    sendPacket();
  }
#endif

  uint32_t currentMillis = millis();
  if (currentMillis - lastReportTime >= 1000) {
    lastReportTime = currentMillis;
    printDashboard();
  }

  handleSerialInput();
}

// ===============================================================================
// HELPER FUNCTIONS
// ===============================================================================

void sendPacket() {
  PacketData packet;
  memset(&packet, 0, sizeof(packet));
  packet.magic = MAGIC_SIGNATURE;
  packet.sequence = ++stats.packetsSent;
  packet.sendTimestamp = millis();
  packet.isEcho = 0;
  
  String macStr = WiFi.macAddress();
  macStr.toCharArray(packet.senderMac, sizeof(packet.senderMac));

  generateLongStringPayload(packet.payload, PAYLOAD_SIZE, packet.sequence);
  packet.payloadLen = (uint16_t)strlen(packet.payload);
  packet.checksum = calculateChecksum(packet.payload, packet.payloadLen);

  esp_now_send(broadcastAddress, (uint8_t *)&packet, sizeof(packet));

  // High-speed stream output for Python UI (Emits on EVERY sent packet!)
  Serial.printf("$DAT,SENDER,%u,%d,%u,%u,%u,%u\n", 
                packet.sequence, stats.lastRssi, stats.lastRttMs, stats.packetsSent, stats.sendSuccess, stats.sendFail);
}

void printDashboard() {
  Serial.println("\n----------------- [PACKET LOSS TRACER REPORT] -----------------");

#if (DEVICE_MODE == MODE_SENDER)
  Serial.print(" Mode: SENDER (Transmitter) | Target Interval: ");
  Serial.print(sendIntervalMs);
  Serial.println(" ms");

  Serial.print(" Total Sent:      "); Serial.println(stats.packetsSent);
  Serial.print(" Send Success:    "); Serial.print(stats.sendSuccess);
  float sendLoss = stats.packetsSent ? ((float)(stats.packetsSent - stats.sendSuccess) / stats.packetsSent) * 100.0 : 0;
  Serial.print(" (MAC Ack Loss: "); Serial.print(sendLoss, 2); Serial.println("%)");

  Serial.print(" Send Failed:     "); Serial.println(stats.sendFail);
  Serial.print(" Last RTT:        "); Serial.print(stats.lastRttMs); Serial.println(" ms");
  Serial.print(" Average RTT:     "); Serial.print(stats.avgRttMs); Serial.println(" ms");
  Serial.print(" Target RSSI:     "); Serial.print(stats.lastRssi); Serial.println(" dBm");

#else
  Serial.println(" Mode: RECEIVER (Target)");

  Serial.print(" Total Received:  "); Serial.println(stats.packetsReceived);
  Serial.print(" Estimated Lost:  "); Serial.println(stats.packetsLost);
  
  uint32_t totalExpected = stats.packetsReceived + stats.packetsLost;
  float lossRate = totalExpected ? ((float)stats.packetsLost / totalExpected) * 100.0 : 0.0;
  
  Serial.print(" Packet Loss Rate: "); Serial.print(lossRate, 2); Serial.println(" %");
  Serial.print(" Out of Order/Dup: "); Serial.println(stats.outOfOrder);
  Serial.print(" Signal RSSI:     "); Serial.print(stats.lastRssi); Serial.println(" dBm");
#endif

  Serial.print(" Active Antenna:  ");
  Serial.println(useExternalAntenna ? "EXTERNAL (GPIO14=HIGH)" : "BUILT-IN / INTERNAL (GPIO14=LOW)");
  Serial.println("----------------------------------------------------------------");
}

void printMenu() {
  Serial.println("\n--- Interactive Serial Commands ---");
  Serial.println("  'a' : Toggle Antenna (Internal Built-in <-> External)");
  Serial.println("  'r' : Reset Telemetry Statistics");
  Serial.println("  '1' : Set Send Interval to 10ms (100 pkts/sec)");
  Serial.println("  '2' : Set Send Interval to 100ms (10 pkts/sec)");
  Serial.println("  '3' : Set Send Interval to 500ms (2 pkts/sec)");
  Serial.println("  'h' : Show Command Menu");
  Serial.println("------------------------------------\n");
}

void handleSerialInput() {
  while (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() == 0) continue;

    if (input.startsWith("$FREQ,")) {
      uint32_t hz = input.substring(6).toInt();
      if (hz > 0) setFrequencyHz(hz);
    } else {
      char c = input.charAt(0);
      switch (c) {
        case 's': case 'S': isTransmitting = true; Serial.println("[STATE] TRANSMISSION_STARTED"); break;
        case 'p': case 'P': isTransmitting = false; Serial.println("[STATE] TRANSMISSION_PAUSED"); break;
        case 'x': case 'X': Serial.println("[STATE] REBOOTING_ESP32"); delay(100); ESP.restart(); break;
        case 'a': case 'A': setupAntenna(!useExternalAntenna); break;
        case 'r': case 'R': memset(&stats, 0, sizeof(stats)); Serial.println("[INFO] Stats Reset."); break;
        case '1': setFrequencyHz(100); break;
        case '2': setFrequencyHz(10); break;
        case '3': setFrequencyHz(2); break;
        case '4': setFrequencyHz(1000); break; // 1 kHz
        case '5': setFrequencyHz(2000); break; // 2 kHz
        case 'h': case 'H': printMenu(); break;
      }
    }
  }
}
